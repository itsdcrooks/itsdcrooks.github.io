#!/usr/bin/env python3
"""
Daily horoscope generator for Sara (artist name: Sarita).

Lives in the same repo as Daniel's generate.py. Reads the shared cosmos
catalogue. Writes to docs/sara/index.html. Maintains its own no-repeat
log in used_images_sara.json.

Required env vars (set as GitHub Secrets — most are already in the repo):
  ANTHROPIC_API_KEY      (existing)
  SMTP_HOST              (existing)
  SMTP_PORT              (existing)
  SMTP_USER              (existing)
  SMTP_PASS              (existing)
  SARA_EMAIL             (NEW — her email)
"""
import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe
from anthropic import Anthropic

# ---------- CONFIG ----------
ROOT = Path(__file__).parent.resolve()
COSMOS_PATH = ROOT / "cosmos_catalogue.json"
USED_IMAGES_PATH = ROOT / "used_images_sara.json"
OUTPUT_HTML = ROOT / "docs" / "sara" / "index.html"
LOCAL_TZ = ZoneInfo(os.environ.get("SARA_TZ", "America/Chicago"))
LEGAL_NAME = "Sara"         # used in email subject and as the primary name in readings
ARTIST_NAME = "Sarita"      # used when readings touch the artist self (music, painting, touring)
NO_REPEAT_DAYS = 70
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000

# ---------- HER NATAL CHART ----------
# Birth: October 13, 1993 — 8:28 AM — El Paso, TX (MDT, UTC-6)
# VERIFY these in Astro.com (tropical) and jhora.com (sidereal Lahiri) before going live.
NATAL = {
    "birth": "October 13, 1993 — 8:28 AM — El Paso, TX",
    "bio": (
        "A musician who travels the world, tends a farm, and paints. "
        "Three forms of alchemy: sound, soil, color. "
        "Mars conjunct ascendant. Pluto rising. The body is the instrument."
    ),
    "western_tropical_placidus": {
        "Sun": "Libra 19°55' — 10th house",
        "Moon": "Aquarius ~3° — 3rd/4th house (verify)",
        "Ascendant": "Scorpio ~17° (verify)",
        "Mercury": "Libra (late degrees) — 10th house",
        "Venus": "Virgo — 10th house",
        "Mars": "Scorpio — 1st house, conjunct ASC",
        "Jupiter": "Virgo — 10th house",
        "Saturn": "Aquarius — 3rd/4th house",
        "Uranus": "Capricorn — 2nd house",
        "Neptune": "Capricorn — 2nd house",
        "Pluto": "Scorpio — 1st house, conjunct ASC and Mars",
        "North Node": "Sagittarius",
    },
    "vedic_sidereal_lahiri": {
        "Ascendant": "Libra (Tula) — Vishakha nakshatra (Jupiter-ruled)",
        "Sun": "Virgo (Kanya) — Hasta nakshatra (Moon-ruled) — 12th house",
        "Moon": "Capricorn (Makara) — Uttara Ashadha (Sun-ruled) — 4th house",
        "Mars": "Libra (debilitated) — Vishakha — 1st house",
        "Mercury": "Libra — Vishakha — 1st house",
        "Jupiter": "Virgo — Hasta — 12th house",
        "Venus": "Leo — Purva Phalguni (Venus-ruled) — 11th house",
        "Saturn": "Capricorn (own sign) — 4th house",
        "Rahu": "Scorpio — 2nd house",
        "Ketu": "Taurus — 8th house",
    },
    "current_dasha": (
        "Likely Rahu Mahadasha (approx 2010 to 2028). "
        "Confirm antardasha in jhora.com and update this string."
    ),
}

# ---------- SEVEN SACRED FLAMES ---------- (weekday: Mon=0 ... Sun=6)
SACRED_FLAMES = {
    0: ("Yellow Flame", "Lord Lanto", "wisdom, illumination, the second ray"),
    1: ("Pink Flame", "Paul the Venetian", "love, beauty, creativity, the third ray"),
    2: ("White Flame", "Serapis Bey", "purity, ascension, discipline, the fourth ray"),
    3: ("Green Flame", "Hilarion", "truth, healing, the soil and the science, the fifth ray"),
    4: ("Ruby-Gold Flame", "Lady Nada", "service, peace, ministration, the sixth ray"),
    5: ("Violet Flame", "Saint Germain", "transmutation, freedom, mercy, the seventh ray"),
    6: ("Blue Flame", "El Morya", "will, protection, faith, the first ray"),
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


# ---------- TRANSITS ----------
def _format(lon: float, speed: float) -> str:
    retro = " R" if speed < 0 else ""
    sign_idx = int(lon // 30) % 12
    deg = lon - sign_idx * 30
    d = int(deg)
    m = int(round((deg - d) * 60))
    if m == 60:
        d += 1
        m = 0
    return f"{SIGNS[sign_idx]} {d}\u00b0{m:02d}'{retro}"


def compute_transits(now_utc: datetime) -> dict:
    swe.set_ephe_path(None)
    jd = swe.julday(
        now_utc.year, now_utc.month, now_utc.day,
        now_utc.hour + now_utc.minute / 60 + now_utc.second / 3600,
    )
    bodies = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO, "True Node": swe.TRUE_NODE,
    }
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    tropical, sidereal = {}, {}
    for name, code in bodies.items():
        pos_t, _ = swe.calc_ut(jd, code)
        tropical[name] = _format(pos_t[0], pos_t[3])
        pos_s, _ = swe.calc_ut(jd, code, swe.FLG_SIDEREAL)
        sidereal[name] = _format(pos_s[0], pos_s[3])
    return {"tropical": tropical, "sidereal": sidereal}


# ---------- IMAGES ----------
def _image_id(img) -> str:
    """Get a stable identifier for an image dict, trying multiple field names."""
    if isinstance(img, dict):
        for key in ("id", "image_id", "filename", "file", "name", "url", "src", "path"):
            v = img.get(key)
            if v:
                return str(v)
        import hashlib
        return hashlib.md5(
            json.dumps(img, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]
    return str(img)


def _normalize_catalogue(raw):
    """Return a list of image dicts with an 'id' field, regardless of source shape."""
    if isinstance(raw, list):
        out = []
        for item in raw:
            if isinstance(item, dict):
                d = dict(item)
                d.setdefault("id", _image_id(d))
                out.append(d)
        return out
    if isinstance(raw, dict):
        for key in ("images", "catalogue", "catalog", "items", "data"):
            if key in raw:
                return _normalize_catalogue(raw[key])
        out = []
        for img_id, val in raw.items():
            if isinstance(val, dict):
                v = dict(val)
                v.setdefault("id", img_id)
                out.append(v)
        return out
    return []


def select_images(catalogue, used: dict, today: str) -> dict:
    images = _normalize_catalogue(catalogue)
    slots = ["hero", "sensual", "devotional", "botanical", "transitional", "closing"]
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    recent = set()
    for img_id, date_str in used.items():
        try:
            if (today_dt - datetime.strptime(date_str, "%Y-%m-%d")).days < NO_REPEAT_DAYS:
                recent.add(img_id)
        except Exception:
            continue
    selections = {}
    for slot in slots:
        pool = [
            img for img in images
            if slot in img.get("suitable_for", []) and img.get("id") not in recent
        ]
        if not pool:
            pool = [img for img in images if slot in img.get("suitable_for", [])]
        if not pool:
            continue
        choice = pool[abs(hash(today + slot)) % len(pool)]
        selections[slot] = choice
        used[choice.get("id") or _image_id(choice)] = today
    return selections

# ---------- PROMPT ----------
def build_prompt(local_now: datetime, transits: dict, flame: tuple, images: dict) -> str:
    flame_name, master, meaning = flame
    img_lines = "\n".join(
        f"- {slot}: id={img['id']} | mood={img.get('mood', '')} | {img.get('description', '')}"
        for slot, img in images.items()
    )
    return f"""You are writing a daily personalized astrology horoscope for {LEGAL_NAME} (artist name {ARTIST_NAME}).

NAMING RULE:
- Default to "{LEGAL_NAME}" when addressing her in the readings.
- Shift to "{ARTIST_NAME}" only when the moment is specifically about her artist self —
  the musician on stage or on the road, the painter at the canvas, the muse,
  the part of her that creates and is witnessed. Sara is the woman; Sarita is the art.
- Use either name sparingly — no more than three total mentions across the page.
- Never use both names in the same sentence.


DATE: {local_now.strftime('%A, %B %d, %Y')}

HER NATAL CHART:
{json.dumps(NATAL, indent=2)}

TRANSITS RIGHT NOW
TROPICAL (Western):
{json.dumps(transits['tropical'], indent=2)}

SIDEREAL (Vedic, Lahiri ayanamsa):
{json.dumps(transits['sidereal'], indent=2)}

TODAY'S SACRED FLAME (day-of-week mapping):
  Name: {flame_name}
  Master: {master}
  Meaning: {meaning}

IMAGE SLOTS — reference these by id in the HTML as <img data-id="ID" alt="...">:
{img_lines}

INSTRUCTIONS — output a single standalone HTML page in the Co-Star aesthetic:
  Background #080808, ivory text, EB Garamond + Courier Prime, tight luxe spacing.
  Sections in order:
    1. Date and one atmospheric opening sentence
    2. Western tropical reading — map today's transits to her natal houses
       (3 to 4 paragraphs, intimate, specific, no "you may find" hedging)
    3. Vedic sidereal reading — transits, nakshatras, dasha context
       (3 to 4 paragraphs)
    4. Today's Sacred Flame reflection (1 to 2 paragraphs, tied to her life)
    5. Planet table — tropical and sidereal positions side by side
    6. Atmosphere carousel — three short sensory lines
    7. Sensual carousel — three short erotic-but-tasteful lines
    8. A short erotic poem (4 to 8 lines, original, no cliche)
    9. A sourced quote — Mary Oliver, Rumi, Anais Nin, Hafiz, Rilke, Lorca,
       Audre Lorde, or similar. Attribute accurately. No fabrications.
    10. One closing line.

  Reference her concretely: musician on tour, the farm, the canvas, the strings.
  Follow the NAMING RULE above.
  No generic astrology cliches. No em dashes.
  Output ONLY the HTML — no markdown fences, no commentary.
"""


# ---------- API + EMAIL ----------
def call_anthropic(prompt: str) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def send_email(html: str, subject: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["SARA_EMAIL"]
    msg.attach(MIMEText(html, "html"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT") or "465"), context=ctx
    ) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


# ---------- MAIN ----------
def main() -> None:
    now_utc = datetime.now(timezone.utc)
    local_now = now_utc.astimezone(LOCAL_TZ)
    today_str = local_now.strftime("%Y-%m-%d")

    catalogue = json.loads(COSMOS_PATH.read_text())
    used = json.loads(USED_IMAGES_PATH.read_text()) if USED_IMAGES_PATH.exists() else {}

    transits = compute_transits(now_utc)
    flame = SACRED_FLAMES[local_now.weekday()]
    images = select_images(catalogue, used, today_str)
    prompt = build_prompt(local_now, transits, flame, images)
    html = call_anthropic(prompt)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html)
    USED_IMAGES_PATH.write_text(json.dumps(used, indent=2))

    subject = f"{local_now.strftime('%A')} — Daily Horoscope for {LEGAL_NAME}"
    send_email(html, subject)
    print(f"Sent {today_str} to {os.environ['SARA_EMAIL']}")


if __name__ == "__main__":
    main()
