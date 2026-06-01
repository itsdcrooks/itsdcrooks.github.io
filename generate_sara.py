import os
import json
import random
import smtplib
import urllib.request
import urllib.error
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _http_get(url, timeout=12, user_agent="Mozilla/5.0"):
    """Plain GET. Returns (text, status) or (None, 0) on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore"), resp.status
    except Exception:
        return None, 0


def _http_post_json(url, payload, headers, timeout=300):
    """POST JSON. Returns (response_dict, status)."""
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="ignore")
        print(f"API Error {e.code}: {err_text[:500]}")
        raise

ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TO_EMAIL           = os.environ.get("SARA_EMAIL", "gypsetsarita@gmail.com")
GITHUB_PAGES_URL   = "https://itsdcrooks.github.io/sara/"

SACRED_FLAMES = {
    "Monday":    {"ray": "1st", "color": "Royal Blue",    "theme": "Divine Will, Protection, Faith",                "chohan": "Master El Morya",          "masters": "Archangel Michael & Faith, Master Adama",          "chakra": "Throat",       "wear": "deep blue or cobalt",           "symbol": "◉"},
    "Tuesday":   {"ray": "3rd", "color": "Rose Pink",     "theme": "Cosmic Love, Compassion, Brotherhood",          "chohan": "Master Paul the Venetian",  "masters": "Archangels Chamuel & Charity",                     "chakra": "Heart",        "wear": "rose, blush, or soft red",      "symbol": "◉"},
    "Wednesday": {"ray": "5th", "color": "Emerald Green", "theme": "Healing, Manifestation, Creation",              "chohan": "Master Hilarion",           "masters": "Archangel Raphael & Mother Mary",                  "chakra": "Third Eye",    "wear": "emerald, forest green, or jade","symbol": "◉"},
    "Thursday":  {"ray": "6th", "color": "Purple & Gold", "theme": "Resurrection, Christ Love, Selfless Service",   "chohan": "Lord Sananda",              "masters": "Lady Nada — Jeshua & Mary Magdalene",              "chakra": "Solar Plexus", "wear": "deep purple with gold accents", "symbol": "◉"},
    "Friday":    {"ray": "4th", "color": "White",         "theme": "Ascension, Purification, Christ Consciousness", "chohan": "Lord Serapis Bey",          "masters": "Archangels Gabriel & Hope",                        "chakra": "Root",         "wear": "white, ivory, or silver",       "symbol": "◉"},
    "Saturday":  {"ray": "7th", "color": "Violet",        "theme": "Transmutation, Freedom, True Alchemy",          "chohan": "Master Saint Germain",      "masters": "Archangels Zadkiel & Amethyst",                    "chakra": "Seat of Soul", "wear": "violet or deep lavender",       "symbol": "◉"},
    "Sunday":    {"ray": "2nd", "color": "Yellow",        "theme": "Illumination, Wisdom, Mind of God",             "chohan": "Lord Lanto",                "masters": "Gautama Buddha, Kuthumi, Sananda, Confucius",      "chakra": "Crown",        "wear": "gold, amber, or yellow",        "symbol": "◉"},
}

# Sara's natal data — VERIFY these in astro.com (tropical) and jhora.com (Lahiri sidereal)
# Birth: October 13, 1993 — 8:28 AM — El Paso, TX (MDT, UTC-6)

WESTERN_CHART = """
Sun in Libra, 19°55' — 10th House
Moon in Aquarius, ~3° — 3rd House (verify exact degree)
Ascendant in Scorpio, ~17° — 1st House (verify)
Mercury in Libra, late degrees — 10th House
Venus in Virgo — 10th House
Mars in Scorpio — 1st House (conjunct Ascendant)
Jupiter in Virgo — 10th House
Saturn in Aquarius — 3rd House
Uranus in Capricorn — 2nd House
Neptune in Capricorn — 2nd House
Pluto in Scorpio — 1st House (conjunct Ascendant and Mars)
North Node in Sagittarius
"""

VEDIC_CHART = """
Ascendant: Libra (Tula) — ruled by Venus — Vishakha nakshatra
Sun: Virgo (Kanya), ~26° — Hasta nakshatra (Moon-ruled) — 12th House
Moon: Capricorn (Makara), ~9° — Uttara Ashadha nakshatra (Sun-ruled) — 4th House
Mars: Libra (debilitated) — Vishakha nakshatra — 1st House (conjunct ASC)
Mercury: Libra — Vishakha nakshatra — 1st House
Jupiter: Virgo — Hasta nakshatra — 12th House
Venus: Leo — Purva Phalguni nakshatra (Venus-ruled) — 11th House
Saturn: Capricorn (own sign) — Uttara Ashadha nakshatra — 4th House
Rahu: Scorpio — 2nd House
Ketu: Taurus — 8th House

Current Vimsottari Dasha: Rahu Mahadasha (approximately 2010 to 2028)
Current Antardasha: VERIFY in jhora.com and update this string
"""

CATALOGUE = []
if os.path.exists("cosmos_catalogue.json"):
    with open("cosmos_catalogue.json") as f:
        data = json.load(f)
        CATALOGUE = data.get("catalogue", [])

ALL_IMAGES = [i['url'] for i in CATALOGUE[:60]] if CATALOGUE else []

USED_IMAGES_FILE = "used_images_sara.json"


def load_used_images():
    """Load the set of previously used image URLs from disk."""
    if os.path.exists(USED_IMAGES_FILE):
        with open(USED_IMAGES_FILE) as f:
            return set(json.load(f))
    return set()


def save_used_images(used_set):
    """Persist the updated set of used image URLs to disk."""
    with open(USED_IMAGES_FILE, "w") as f:
        json.dump(list(used_set), f)


def pick_images():
    today = datetime.now()
    seed = today.year * 10000 + today.month * 100 + today.day
    rng = random.Random(seed)

    previously_used = load_used_images()

    all_urls = set(i['url'] for i in CATALOGUE) if CATALOGUE else set(ALL_IMAGES)

    available = all_urls - previously_used
    if not available:
        print("Full image pool exhausted — resetting used images list.")
        previously_used = set()
        available = all_urls

    today_used = []

    def pick(moods=None, slot=None, exclude=[], n=1):
        excluded = set(exclude) | previously_used | set(today_used)
        if CATALOGUE:
            pool = CATALOGUE
            if moods:
                pool = [i for i in pool if i.get('mood') in moods]
            if slot:
                pool = [i for i in pool if slot in i.get('suitable_for', [])]
            pool = [i for i in pool if i['url'] not in excluded]
            if not pool and moods:
                pool = [i for i in CATALOGUE if i.get('mood') in moods and i['url'] not in excluded]
            if not pool:
                pool = [i for i in CATALOGUE if i['url'] not in set(today_used)]
            rng.shuffle(pool)
            result = [i['url'] + '?format=webp&w=800' for i in pool[:n]]
        else:
            pool = [u for u in ALL_IMAGES if u not in excluded]
            if not pool:
                pool = [u for u in ALL_IMAGES if u not in set(today_used)]
            rng.shuffle(pool)
            result = [u + '?format=webp&w=800' for u in pool[:n]]

        for url in result:
            base = url.split('?')[0]
            today_used.append(base)
        return result

    hero       = pick(moods=['fierce', 'cosmic', 'ethereal'], slot='hero', n=1)
    atm        = pick(moods=['contemplative', 'devotional', 'cosmic', 'ethereal'], slot='devotional', n=4)
    sens       = pick(moods=['sensual', 'tender', 'ethereal'], slot='sensual', n=5)
    closing    = pick(moods=['contemplative', 'ethereal'], slot='closing', n=2)
    vedic_imgs = pick(moods=['devotional', 'contemplative', 'cosmic'], slot='devotional', n=3)

    save_used_images(previously_used | set(today_used))
    print(f"✓ Images picked: {len(today_used)} new, {len(previously_used)} previously used, {len(all_urls)} total pool")

    url_to_desc = {i['url']: i for i in CATALOGUE} if CATALOGUE else {}

    def get_desc(url):
        base = url.split('?')[0]
        item = url_to_desc.get(base, {})
        return {
            'url': url,
            'description': item.get('description', ''),
            'subjects': item.get('subjects', []),
            'mood': item.get('mood', ''),
        }

    fallback = ALL_IMAGES[0] if ALL_IMAGES else (CATALOGUE[0]['url'] if CATALOGUE else '')
    return {
        'hero':       hero[0] if hero else fallback,
        'hero_desc':  get_desc(hero[0] if hero else fallback),
        'atm':        atm,
        'atm_desc':   [get_desc(u) for u in atm],
        'sensual':    sens,
        'sensual_desc': [get_desc(u) for u in sens],
        'closing':    closing,
        'closing_desc': [get_desc(u) for u in closing],
        'vedic':      vedic_imgs,
        'vedic_desc': [get_desc(u) for u in vedic_imgs],
    }


def get_planet_positions():
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")
    day_name = today.strftime("%A")

    sources = [
        f"https://cafeastrology.com/events/{today.strftime('%B').lower()}-{today.day}-{today.year}/",
        "https://astro.com/swisseph/swepha_e.htm",
    ]

    for url in sources:
        try:
            text, status = _http_get(url, timeout=12)
            if text and len(text) > 500:
                return f"SOURCE DATE: {date_str} ({day_name})\n\n{text[:2500]}"
        except Exception:
            continue

    return f"""Today is {date_str}, {day_name}.
Use your knowledge of current planetary positions for this exact date.
Be specific about which sign each planet is in, any retrogrades, and key aspects active today.
Do NOT use yesterday's or a generic date's positions — this reading is specifically for {date_str}."""


def generate_horoscope(planet_data, images):
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")
    day_name = today.strftime("%A")
    flame = SACRED_FLAMES.get(day_name, SACRED_FLAMES["Sunday"])
    vedic_img_list = ", ".join(images.get('vedic', []))

    def fmt_desc(d):
        subj = ', '.join(d['subjects'][:2]) if d['subjects'] else 'unknown'
        desc = d['description'][:80] if d['description'] else ''
        return f"{d['mood']} | {subj} | {desc}"

    hero_info = fmt_desc(images['hero_desc'])
    atm_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['atm_desc'])])
    sens_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['sensual_desc'])])
    closing_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['closing_desc'])])
    vedic_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['vedic_desc'])])

    prompt = f"""You are generating a daily personal horoscope for Sara — a musician who travels the world, tends a farm, and paints. Her artist name is Sarita. Today is {date_str} ({day_name}). THIS READING IS SPECIFICALLY FOR {date_str} — do not reuse content from any previous date.

NAMING RULE:
- Default to "Sara" when addressing her in the readings.
- Shift to "Sarita" only when the moment is specifically about her artist self — the musician on stage or on the road, the painter at the canvas, the muse, the part of her that creates and is witnessed. Sara is the woman; Sarita is the art.
- Use either name sparingly — no more than three total mentions across the page.
- Never use both names in the same sentence.

WESTERN NATAL CHART:
{WESTERN_CHART}

VEDIC NATAL CHART (Sidereal/Lahiri):
{VEDIC_CHART}

TODAY'S PLANETARY DATA:
{planet_data}

Generate a complete self-contained HTML page. ALL CSS must be inline on each element (style="..."). NO <style> or <script> tags. Background #080808, body text #d6cfc4, headings #f2ede6, labels Courier New monospace. Max width 480px centered.

Carousels: container has style="display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:0 24px;" — each card has style="flex-shrink:0;scroll-snap-align:start;"

TODAY'S SACRED FLAME (Telosian tradition):
Day: {day_name}
Ray: {flame['ray']} Ray — {flame['color']}
Theme: {flame['theme']}
Chohan: {flame['chohan']}
Masters: {flame['masters']}
Chakra: {flame['chakra']}
Recommended color to wear: {flame['wear']}

═══ PART ONE: WESTERN READING ═══

1. TOPBAR — date left, "☀ Libra · ↑ Scorpio" right. Monospace 11px #5a5550 letter-spacing 0.18em. Border-bottom 1px solid #161616. Padding 26px 24px 14px.

2. HERO IMAGE — src="{images['hero']}" — width 100%, height 400px, object-fit cover, grayscale(100%) contrast(1.08), opacity 0.72. Gradient overlay at bottom.
   WHAT IS IN THIS IMAGE: {hero_info}
   Caption below: ↳ symbol + monospace 11px #5a5550 — use the description above to write a caption explaining what you actually see in the image and why it was chosen for today's dominant Western transit.

3. HEADLINE — font-size clamp(36px,9vw,52px), italic, font-weight 400, letter-spacing -0.01em. Tied to today's most important Western transit.

4. NATAL CHIPS — flex wrap, gap 7px. Active ones: border 1px solid #4a4a4a, color #aaa. Inactive: border 1px solid #222, color #5a5550. Monospace 10px letter-spacing 0.1em uppercase padding 4px 9px.

5. MAIN WESTERN READING — 3 paragraphs, font-size 17px, line-height 1.78, color #d6cfc4. Each grounded in specific natal placement + current transit. Reference her three crafts concretely (music, farm, paint) where the chart genuinely supports it — not as decoration.

6. ATMOSPHERE CAROUSEL — 4 cards, 280px wide each. Images:
   {images['atm'][0] if len(images['atm'])>0 else ''}, {images['atm'][1] if len(images['atm'])>1 else ''}, {images['atm'][2] if len(images['atm'])>2 else ''}, {images['atm'][3] if len(images['atm'])>3 else ''}
   WHAT IS IN EACH IMAGE:
{atm_info}
   Each image 190px tall, object-fit cover, grayscale. Below: card number monospace 10px #2a2a2a, caption monospace 11px #5a5550 — use the descriptions above to write what you see + why chosen for that transit.

7. PLANET TABLE — 10 planets. Cols: symbol (14px monospace #5a5550, 28px wide) | name·house (10px monospace #555, 115px) | status word (active=#a0c080 / challenged=#c08070 / dormant=#5a5550) + explanation (13px #d6cfc4). Row border-bottom 1px solid #111.

8. KEY ASPECTS BOX — background #0d0d0d, padding 20px, 3-4 transit rows. Each row: white tag (background #f2ede6, color #080808, 10px monospace uppercase padding 3px 8px) + aspect symbol (12px #2a2a2a) + ghost tag (border 1px solid #252525, color #5a5550). Note below in monospace 12px #5a5550.

9. CHECKLIST — 4 items with ✓. Each item: display flex, gap 14px, padding 10px 0, border-bottom 1px solid #111. Font-size 16px #d6cfc4.

9b. SACRED FLAME SECTION — This is a standalone block between the checklist and the first quote.
    Outer container: padding 32px 24px, border-bottom 1px solid #161616, border-top 1px solid #161616.
    Header row: display flex, align-items center, gap 12px.
      - A small color swatch: width 10px, height 10px, border-radius 50%, background color matching the flame (Royal Blue=#3a5a8a, Rose Pink=#c97a8a, Emerald Green=#2d7a5a, Purple & Gold=#6a3a8a, White=#e8e4dc, Violet=#6a3a9a, Yellow=#c8a830)
      - Label: "SACRED FLAME · {day_name.upper()}" monospace 10px #5a5550 letter-spacing 0.2em uppercase
    Flame name: font-size 22px italic #f2ede6 margin-top 12px — e.g. "The {flame['color']} Flame"
    Ray line: monospace 11px #5a5550 — "{flame['ray']} Ray · {flame['theme']}"
    Two-column detail row (display grid, grid-template-columns 1fr 1fr, gap 16px, margin-top 14px):
      Left: "CHOHAN" label (monospace 9px #3a3a3a uppercase letter-spacing 0.15em) + value (13px #d6cfc4)
            "MASTERS" label + value (13px #d6cfc4, line-height 1.5)
      Right: "CHAKRA" label + value (13px #d6cfc4)
             "WEAR TODAY" label + value (13px #a0c080) — the color recommendation in green to make it stand out
    Invocation line: margin-top 16px, padding-top 14px, border-top 1px solid #111. Font-size 15px italic #d6cfc4, line-height 1.7.
      Write a 1-2 sentence invocation that connects today's flame to today's dominant astrological transit. Something like: "The [Flame] burns today — [theme]. With [specific transit], invoke [Chohan] to [specific intention tied to the day's sky]."

10. SOURCED QUOTE — font-size 20px italic #f2ede6, line-height 1.72. Attribution monospace 11px #5a5550 uppercase. Real poet, never invented.

11. SENSUAL SECTION — label "Venus in [sign] · [Moon situation]". 3 paragraphs, font-size 17px, line-height 1.82 #d6cfc4. One sourced erotic poet quote in em tags (italic #f2ede6).

12. SENSUAL CAROUSEL — 5 portrait cards, 200px wide, 320px tall images, grayscale opacity 0.75. Images:
    {images['sensual'][0] if len(images['sensual'])>0 else ''}, {images['sensual'][1] if len(images['sensual'])>1 else ''}, {images['sensual'][2] if len(images['sensual'])>2 else ''}, {images['sensual'][3] if len(images['sensual'])>3 else ''}, {images['sensual'][4] if len(images['sensual'])>4 else ''}
    WHAT IS IN EACH IMAGE:
{sens_info}
    Each card: number title + caption using the descriptions above — what you actually see + why chosen for this transit/placement.

13. SECOND SOURCED QUOTE — different poet, short, resonant.

14. THE LESSON — centered, font-size 21px italic #f2ede6, max-width 380px margin auto. 2-3 sentences specific to Sara's Western chart.

15. TRY THIS — two-column grid (1fr 1fr, gap 2px, background #111). Each cell background #080808, padding 22px 18px. Label monospace 10px #5a5550 + text 14px #d6cfc4.

16. CLOSING CAROUSEL — 2 landscape cards, 300px wide, 190px tall. Images:
    {images['closing'][0] if len(images['closing'])>0 else ''}, {images['closing'][1] if len(images['closing'])>1 else ''}
    WHAT IS IN EACH IMAGE:
{closing_info}

═══ PART TWO: VEDIC READING ═══

Full-width divider: border-top 1px solid #2a2a2a. Then centered label "VEDIC READING" monospace 10px #5a5550 letter-spacing 0.3em, padding 28px 24px.

17. VEDIC HEADLINE — different from Western. Italic serif clamp(32px,8vw,46px). Tied to Rahu Mahadasha or today's Vedic transit through her Libra-rising chart.

18. VEDIC CHIPS — Libra ASC · Virgo Sun · Capricorn Moon · Rahu Dasha · Mars Conjunct Lagna. Same chip style as Western.

19. VEDIC MAIN READING — 3 paragraphs. Ground in:
    - Rahu Mahadasha through her chart: Rahu in 2nd (Scorpio), the second house of voice, value, accumulated resources, and the artist's livelihood
    - Mars debilitated in Libra conjunct her ASC — the body as instrument, force tempered by Venus, the warrior who paints
    - Today's transiting planets in sidereal positions through Libra-ASC houses
    - Today's Moon nakshatra and its quality
    Vedic register: dharma, karma, the grahas as forces, the nodes as destiny shapers. More cosmic/cyclical than the Western psychological register.

20. VEDIC PLANET TABLE — same format as Western but using Vedic signs/houses. Include Rahu and Ketu.

21. VEDIC TRANSIT BOX — same dark box, 3-4 key Vedic transits/dasha influences today.

22. VEDIC IMAGE CAROUSEL — 3 wide cards, 280px wide, 190px tall. Images: {vedic_img_list}
    WHAT IS IN EACH IMAGE:
{vedic_info}
    Captions: use the descriptions above — connect what you actually see in each image to a specific Vedic theme.

23. VEDIC LESSON — centered italic 21px #f2ede6, 2 sentences. Karmic/dharmic insight specific to Sara's Vedic chart.

24. VEDIC SOURCED QUOTE — from Vedic/Sanskrit tradition, Bhagavad Gita, Upanishads, or a poet whose work resonates with Jyotish. Real quote, properly attributed.

Output ONLY the complete HTML document. Nothing else.
"""

    data, status = _http_post_json(
        "https://api.anthropic.com/v1/messages",
        payload={
            "model": "claude-sonnet-4-6",
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": prompt}],
        },
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        timeout=300,
    )
    html = data["content"][0]["text"]
    html = html.replace("```html", "").replace("```", "").strip()
    return html


def send_email(url):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("No email credentials — skipping email.")
        return
    today = datetime.now().strftime("%B %d, %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"☽ Daily Reading for Sara · {today}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    body = f"Sara — your daily reading for {today} is ready.\n\nOpen it here: {url}\n\n☽"
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())
    print(f"✓ Email sent to {TO_EMAIL}")


def main():
    print(f"Generating Sara's horoscope for {datetime.now().strftime('%B %d, %Y')}...")
    print("Picking images...")
    images = pick_images()
    print("Fetching planetary positions...")
    planet_data = get_planet_positions()
    print("Generating with Claude (Western + Vedic)...")
    html = generate_horoscope(planet_data, images)
    print("Saving sara/index.html...")
    os.makedirs("sara", exist_ok=True)
    with open("sara/index.html", "w") as f:
        f.write(html)
    print("Sending email...")
    send_email(GITHUB_PAGES_URL)
    print("✓ Done!")


if __name__ == "__main__":
    main()
