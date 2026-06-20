import os
import json
import random
import smtplib
import urllib.request
import urllib.error
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _http_get(url, timeout=12):
    """Plain GET. Returns text or None on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 300:
                return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        pass
    return None


def _http_post_json(url, payload, headers, timeout=300):
    """POST JSON. Returns parsed JSON response."""
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("content-type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="ignore")
        print(f"API Error {e.code}: {err_text[:500]}")
        raise


def _http_post_stream_text(url, payload, headers, timeout=600):
    """POST JSON with stream=True, parse SSE stream, return accumulated text content.

    Used for long Anthropic responses where a single non-streaming read would time out.
    """
    payload = dict(payload)
    payload["stream"] = True
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("content-type", "application/json")
    h.setdefault("accept", "text/event-stream")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    full_text = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").rstrip("\r\n")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        full_text += delta.get("text", "")
                elif event.get("type") == "message_stop":
                    break
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="ignore")
        print(f"API Error {e.code}: {err_text[:500]}")
        raise
    return full_text

ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TO_EMAIL           = "gypsetsarita@gmail.com"
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

WESTERN_CHART = """
Sun in Libra, 19°55' — 10th House
Moon in Aquarius, ~3° — 3rd House
Ascendant in Scorpio, ~17° — 1st House
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

ALL_IMAGES = [
    "https://cdn.cosmos.so/001753d3-8bfb-4efc-bb07-52f60b976cd1",
    "https://cdn.cosmos.so/01239b25-375f-46da-b95f-c0928b7a1e26",
    "https://cdn.cosmos.so/02027bed-4a28-4e8d-b2f7-1d20cd8611b7",
    "https://cdn.cosmos.so/0a5c7a3b-9eff-494b-859c-4189cd994c9d",
    "https://cdn.cosmos.so/0b8c2141-539f-43f5-b719-52379baa8dba",
    "https://cdn.cosmos.so/13b7a990-bd23-431c-a5f9-0e20a51466ac",
    "https://cdn.cosmos.so/15d13356-9639-449a-85f8-42898ce5b9c7",
    "https://cdn.cosmos.so/1cd3618e-bbe3-4612-ba2a-df52272ebba9",
    "https://cdn.cosmos.so/22d08468-8111-495a-9392-fe7d808c7564",
    "https://cdn.cosmos.so/2b285c7e-2c0f-4927-b78e-0368ecd672dc",
    "https://cdn.cosmos.so/2daa93eb-8786-4065-a473-c3aadaa40aa1",
    "https://cdn.cosmos.so/30176961-5cc9-4e70-b932-7c0ef89f2f06",
    "https://cdn.cosmos.so/315e4302-7196-4106-a7f6-e658ca722efc",
    "https://cdn.cosmos.so/34ddc7b4-7b84-4324-999d-5d364e75570c",
    "https://cdn.cosmos.so/3f836eb1-638d-4262-9ca8-f06033246830",
    "https://cdn.cosmos.so/40af11e2-c61c-4ab8-8003-f95a83338057",
    "https://cdn.cosmos.so/42276b6e-6f10-45c0-b33e-755feb7d3078",
    "https://cdn.cosmos.so/46163520-d970-4d63-83f8-91b9fd034ca8",
    "https://cdn.cosmos.so/4a5c9622-9a83-45e0-aeb7-ed02f74bbc16",
    "https://cdn.cosmos.so/52dd2e11-5ee3-441a-a1ec-dc58450c6745",
    "https://cdn.cosmos.so/56a9e822-1b40-4024-9aef-4b664705a221",
    "https://cdn.cosmos.so/5bfa54d0-d45e-4e32-a3c3-9cb599330d5c",
    "https://cdn.cosmos.so/6287514b-a96c-4379-8e34-01b06633c7e6",
    "https://cdn.cosmos.so/63efaacb-3f23-443c-bcca-af9fbaa48f8a",
    "https://cdn.cosmos.so/693e858d-bd32-4a78-86c7-6c0c8e569992",
    "https://cdn.cosmos.so/6e394514-82e0-4196-b3b1-024d4dabacc1",
    "https://cdn.cosmos.so/6f86fc00-0347-4a85-92da-c192cca91883",
    "https://cdn.cosmos.so/71a87963-22b4-4186-8a5d-1f5c18dae7f0",
    "https://cdn.cosmos.so/75cd7de6-d42a-48bc-a3fc-ed7ea037ea15",
    "https://cdn.cosmos.so/7a85456d-1961-4e93-b7cc-b21169c91629",
    "https://cdn.cosmos.so/7e4757fe-6394-47ce-a766-f14891ba88a9",
    "https://cdn.cosmos.so/82305324-ef04-4700-9a99-a65a095c4ee9",
    "https://cdn.cosmos.so/84bfe989-7623-48a0-b97e-0dec327ab80c",
    "https://cdn.cosmos.so/8733eba1-eb24-4145-857c-4549c3f950f3",
    "https://cdn.cosmos.so/8dc51cfe-a819-4d2c-9a11-46e4b8fd323d",
    "https://cdn.cosmos.so/96172745-af89-4f02-82f6-b72bbabc4615",
    "https://cdn.cosmos.so/9d4471ec-89c1-4cef-96a2-ae2b60b4ad3e",
    "https://cdn.cosmos.so/a22716e5-1442-432c-b320-05b3ad24deec",
    "https://cdn.cosmos.so/a9b5647e-3b9a-4e3a-bcd1-aedf06fc669e",
    "https://cdn.cosmos.so/acbafe9e-45f3-4729-80cc-ac52fc63e765",
    "https://cdn.cosmos.so/b3174c8c-e566-481d-b257-21e3e9257006",
    "https://cdn.cosmos.so/b732f4ad-975b-4502-8731-c98677811206",
    "https://cdn.cosmos.so/bc3e7bac-ac66-4cbc-8cd2-708b2556779a",
    "https://cdn.cosmos.so/c82ba048-ce61-4866-b939-b9d8ddcde0c3",
    "https://cdn.cosmos.so/cbfc762c-11a7-4e9b-b155-7bef115610c6",
    "https://cdn.cosmos.so/d03b3254-696e-4f95-b636-7f44e880dda6",
    "https://cdn.cosmos.so/daf8e58c-79b4-4389-8a11-cc37b1e09185",
    "https://cdn.cosmos.so/e4243e3d-bc4c-46f1-ae96-106357e1dbb2",
    "https://cdn.cosmos.so/e629d9cb-f22a-453d-84ec-a9537ca999c1",
    "https://cdn.cosmos.so/e8f9ed23-db6a-42d6-9041-b0fab32b4b16",
    "https://cdn.cosmos.so/ef00255c-d360-42f3-9ea2-e0bd0c768c29",
    "https://cdn.cosmos.so/f0bdd073-9cd7-4e38-99fa-d39dd47c1801",
    "https://cdn.cosmos.so/f3f0fc30-5fa4-426b-82a0-859d1e674906",
    "https://cdn.cosmos.so/f608afaa-7cd5-4f9d-844a-2c5e4d2a6d4e",
    "https://cdn.cosmos.so/fba283e8-d582-409c-8f70-2b274446dbc6",
    "https://cdn.cosmos.so/fcfe557a-cea0-4787-898c-ec106fc8ddee",
    "https://cdn.cosmos.so/fdd572d5-a83b-4a6a-ad1a-eb2c05d3c944",
]


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





# ---------- Pool-based image system ----------
POOLS_PATH = "pools.json"
USED_POOLS_PATH = "used_pools.json"

POOL_SLOT_COUNTS = {
    "hero": 1, "aura": 3, "eros": 3, "vedic": 3, "totem": 1,
}

# Mood-based fallback configuration if a pool is empty or too small
POOL_FALLBACK_MOODS = {
    "hero":  ["fierce", "cosmic", "ethereal"],
    "aura":  ["contemplative", "devotional", "cosmic", "ethereal"],
    "eros":  ["sensual", "tender", "ethereal"],
    "vedic": ["devotional", "contemplative", "cosmic"],
    "totem": ["contemplative", "ethereal", "devotional"],
}
POOL_FALLBACK_SLOT = {
    "hero": "hero", "aura": "devotional", "eros": "sensual",
    "vedic": "devotional", "totem": "closing",
}


def load_pools():
    if not os.path.exists(POOLS_PATH):
        return {}
    try:
        with open(POOLS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def load_used_pools():
    if not os.path.exists(USED_POOLS_PATH):
        return {}
    try:
        with open(USED_POOLS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_used_pools(used):
    with open(USED_POOLS_PATH, "w") as f:
        json.dump(used, f, indent=2)


def pick_images():
    rng = random.Random(datetime.now().strftime("%Y-%m-%d"))
    previously_used = load_used_images()
    today = datetime.now()
    all_urls = {i["url"] for i in CATALOGUE} if CATALOGUE else set(ALL_IMAGES)

    available = all_urls - previously_used
    if not available:
        print("Full image pool exhausted — resetting used images list.")
        previously_used = set()

    pools = load_pools()
    used_pools = load_used_pools()
    today_used = []

    def _add_query(u):
        return u if "?" in u else u + "?format=webp&w=800"

    def pick_from_pool_with_fallback(slot_name, n):
        pool_urls = pools.get(slot_name, [])
        used_in_pool = set(used_pools.get(slot_name, []))
        cross_excluded = set(today_used)

        # Try pool first
        if pool_urls:
            avail = [u for u in pool_urls if u not in used_in_pool and u not in cross_excluded]
            if len(avail) < n:
                # Reset within this pool — keep cross-slot dedup
                avail = [u for u in pool_urls if u not in cross_excluded]
                if len(avail) >= n:
                    print(f"  {slot_name}: pool history exhausted — resetting tracker for this pool")
                    used_pools[slot_name] = []
            if len(avail) >= n:
                rng.shuffle(avail)
                picks = avail[:n]
                used_pools.setdefault(slot_name, []).extend(picks)
                # Cap to prevent unbounded growth
                if len(used_pools[slot_name]) > 200:
                    used_pools[slot_name] = used_pools[slot_name][-200:]
                for p in picks:
                    today_used.append(p)
                return [_add_query(p) for p in picks]

        # Fallback to mood-based pick from existing catalogue
        print(f"  {slot_name}: pool insufficient ({len(pool_urls)} urls), falling back to mood-based catalogue pick")
        excluded = previously_used | set(today_used)
        moods = POOL_FALLBACK_MOODS.get(slot_name, [])
        slot = POOL_FALLBACK_SLOT.get(slot_name, "")
        if CATALOGUE:
            pool = [i for i in CATALOGUE
                    if i.get("mood") in moods
                    and slot in i.get("suitable_for", [])
                    and i["url"] not in excluded]
            if not pool:
                pool = [i for i in CATALOGUE if i.get("mood") in moods and i["url"] not in excluded]
            if not pool:
                pool = [i for i in CATALOGUE if i["url"] not in set(today_used)]
            rng.shuffle(pool)
            result = [i["url"] + "?format=webp&w=800" for i in pool[:n]]
        else:
            pool = [u for u in ALL_IMAGES if u not in excluded]
            if not pool:
                pool = list(ALL_IMAGES)
            rng.shuffle(pool)
            result = [u + "?format=webp&w=800" for u in pool[:n]]
        for url in result:
            today_used.append(url.split("?")[0])
        return result

    hero  = pick_from_pool_with_fallback("hero",  1)
    aura  = pick_from_pool_with_fallback("aura",  3)
    eros  = pick_from_pool_with_fallback("eros",  3)
    vedic_imgs = pick_from_pool_with_fallback("vedic", 3)
    totem = pick_from_pool_with_fallback("totem", 1)

    save_used_pools(used_pools)
    save_used_images(previously_used | {u.split("?")[0] for u in today_used})
    print(f"✓ Pools used: hero/aura/eros/vedic/totem - {len(today_used)} images picked today")

    # Build description lookup for selected images (catalogue may not have new pool URLs)
    url_to_entry = {i["url"]: i for i in CATALOGUE} if CATALOGUE else {}
    def get_desc(url):
        base = url.split("?")[0]
        item = url_to_entry.get(base, {})
        return {
            "url": url,
            "description": item.get("description", ""),
            "subjects": item.get("subjects", []),
            "mood": item.get("mood", ""),
        }

    return {
        "hero":       hero[0] if hero else ALL_IMAGES[0],
        "hero_desc":  get_desc(hero[0] if hero else ALL_IMAGES[0]),
        "aura":       aura,
        "aura_desc":  [get_desc(u) for u in aura],
        "eros":       eros,
        "eros_desc":  [get_desc(u) for u in eros],
        "vedic":      vedic_imgs,
        "vedic_desc": [get_desc(u) for u in vedic_imgs],
        "totem":      totem[0] if totem else ALL_IMAGES[0],
        "totem_desc": get_desc(totem[0] if totem else ALL_IMAGES[0]),
    }


def get_planet_positions():
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")
    day_name = today.strftime("%A")

    # Try multiple sources for current planetary data
    sources = [
        f"https://cafeastrology.com/events/{today.strftime('%B').lower()}-{today.day}-{today.year}/",
        "https://astro.com/swisseph/swepha_e.htm",
    ]

    for url in sources:
        try:
            text = _http_get(url, timeout=12)
            if text and len(text) > 500:
                # Return truncated text with date header
                return f"SOURCE DATE: {date_str} ({day_name})\n\n{text[:2500]}"
        except Exception:
            continue

    # Fallback — give the model the exact date and instruct it clearly
    return f"""Today is {date_str}, {day_name}.
Use your knowledge of current planetary positions for this exact date.
Be specific about which sign each planet is in, any retrogrades, and key aspects active today.
Do NOT use yesterday's or a generic date's positions — this reading is specifically for {date_str}."""


def generate_horoscope(planet_data, images, todays_quotes=None):
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
    aura_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['aura_desc'])])
    eros_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['eros_desc'])])
    totem_info = fmt_desc(images['totem_desc'])
    vedic_info = "\n".join([f"  Card {i+1}: {fmt_desc(d)}" for i, d in enumerate(images['vedic_desc'])])

    # Format pre-picked quotes for the prompt
    section_10_quote = fmt_quote(todays_quotes.get("section_10") if todays_quotes else None)
    section_11_quote = fmt_quote(todays_quotes.get("section_11") if todays_quotes else None)
    section_13_quote = fmt_quote(todays_quotes.get("section_13") if todays_quotes else None)
    section_24_quote = fmt_quote(todays_quotes.get("section_24") if todays_quotes else None)

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

Generate a complete self-contained HTML page.

PRE-SELECTED QUOTES FOR TODAY (use these EXACTLY — do not paraphrase, do not substitute, do not invent new ones):
  SECTION 10 (main sourced quote):
{section_10_quote}

  SECTION 11 (sensual section embedded quote):
{section_11_quote}

  SECTION 13 (second sourced quote):
{section_13_quote}

  SECTION 24 (vedic sourced quote):
{section_24_quote}

When you render each quote, format the body text exactly as given (italic) and the attribution on a new line in monospace 11px uppercase as: AUTHOR · SOURCE · YEAR.
 ALL CSS must be inline on each element (style="..."). NO <style> or <script> tags. Background #faf8f3 (warm white), body text #1f1d18 (rich dark warm), headings #0a0a0a (deep black), labels Courier New monospace. Max width 480px centered.

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

1. TOPBAR — date left, "☀ Libra · ↑ Scorpio" right. Monospace 11px #8a857d letter-spacing 0.18em. Border-bottom 1px solid #e0ddd5. Padding 26px 24px 14px.

2. HERO IMAGE — src="{images['hero']}" — width 100%, height 400px, object-fit cover, grayscale(100%) contrast(1.0), opacity 1.0. Subtle bottom gradient if needed.
   WHAT IS IN THIS IMAGE: {hero_info}
   Caption below: ↳ symbol + monospace 11px #8a857d — use the description above to write a caption explaining what you actually see in the image and why it was chosen for today's dominant Western transit.

3. HEADLINE — font-size clamp(36px,9vw,52px), italic, font-weight 400, letter-spacing -0.01em. Tied to today's most important Western transit.

4. NATAL CHIPS — flex wrap, gap 7px. Active ones: border 1px solid #7a7570, color #2a2a2a. Inactive: border 1px solid #d4d1ca, color #8a857d. Monospace 10px letter-spacing 0.1em uppercase padding 4px 9px.

5. MAIN WESTERN READING — 3 paragraphs, font-size 17px, line-height 1.78, color #1f1d18. Each grounded in specific natal placement + current transit.

6. AURA CAROUSEL — 3 cards, 280px wide each. Label this section "AURA" in the small monospace header. Images:
   {images['aura'][0] if len(images['aura'])>0 else ''}, {images['aura'][1] if len(images['aura'])>1 else ''}, {images['aura'][2] if len(images['aura'])>2 else ''}
   WHAT IS IN EACH IMAGE:
{aura_info}
   Each image 190px tall, object-fit cover, grayscale. Below: card number monospace 10px #c0bdb5, caption monospace 11px #8a857d.
   Caption FORMAT: "[Concrete visible content from the description above — name the subject, scene, gesture] — for [specific transit reason]." LEAD WITH WHAT'S VISIBLE; do not open with "a form", "a presence", "a figure".
   If no description is provided for an image, write the bare minimum: "card N · for [transit name]" — do not invent visual content you cannot verify.

7. PLANET TABLE — 10 planets. Cols: symbol (14px monospace #8a857d, 28px wide) | name·house (10px monospace #555, 115px) | status word (active=#4a7a3a / challenged=#a05540 / dormant=#8a857d) + explanation (13px #1f1d18). Row border-bottom 1px solid #e8e5dd.

8. KEY ASPECTS BOX — background #f3f0e8 (cream panel), padding 20px, 3-4 transit rows. Each row: dark tag (background #0a0a0a, color #faf8f3, 10px monospace uppercase padding 3px 8px) + aspect symbol (12px #c0bdb5) + ghost tag (border 1px solid #d4d1ca, color #8a857d). Note below in monospace 12px #8a857d.

9. CHECKLIST — 4 items with ✓. Each item: display flex, gap 14px, padding 10px 0, border-bottom 1px solid #e8e5dd. Font-size 16px #1f1d18.

9b. SACRED FLAME SECTION — This is a standalone block between the checklist and the first quote.
    Outer container: padding 32px 24px, border-bottom 1px solid #e0ddd5, border-top 1px solid #e0ddd5.
    Header row: display flex, align-items center, gap 12px.
      - A small color swatch: width 10px, height 10px, border-radius 50%, background color matching the flame (Royal Blue=#3a5a8a, Rose Pink=#c97a8a, Emerald Green=#2d7a5a, Purple & Gold=#6a3a8a, White=#e8e4dc, Violet=#6a3a9a, Yellow=#c8a830). Add a 1px solid #d4d1ca border on the swatch so light colors (especially White) remain visible.
      - Label: "SACRED FLAME · {day_name.upper()}" monospace 10px #8a857d letter-spacing 0.2em uppercase
    Flame name: font-size 22px italic #0a0a0a margin-top 12px — e.g. "The {flame['color']} Flame"
    Ray line: monospace 11px #8a857d — "{flame['ray']} Ray · {flame['theme']}"
    Two-column detail row (display grid, grid-template-columns 1fr 1fr, gap 16px, margin-top 14px):
      Left: "CHOHAN" label (monospace 9px #8a857d uppercase letter-spacing 0.15em) + value (13px #1f1d18)
            "MASTERS" label + value (13px #1f1d18, line-height 1.5)
      Right: "CHAKRA" label + value (13px #1f1d18)
             "WEAR TODAY" label + value (13px #4a7a3a) — the color recommendation in darker forest green to stand out on white
    Invocation line: margin-top 16px, padding-top 14px, border-top 1px solid #e8e5dd. Font-size 15px italic #1f1d18, line-height 1.7.
      Write a 1-2 sentence invocation that connects today's flame to today's dominant astrological transit. Something like: "The [Flame] burns today — [theme]. With [specific transit], invoke [Chohan] to [specific intention tied to the day's sky]."

10. SOURCED QUOTE — font-size 20px italic #0a0a0a, line-height 1.72. Attribution monospace 11px #8a857d uppercase. USE THE SECTION 10 QUOTE provided above — do not pick your own.

11. SENSUAL SECTION — label "Venus in [sign] · [Moon situation]". 3 paragraphs, font-size 17px, line-height 1.82 #1f1d18. Embed the SECTION 11 QUOTE provided above inside the paragraphs as <em>...</em> (italic #0a0a0a) with full attribution. Do not substitute another quote.

12. EROS CAROUSEL — 3 portrait cards, 200px wide, 320px tall images, grayscale opacity 1.0. Label this section "EROS" in the small monospace header. Images:
    {images['eros'][0] if len(images['eros'])>0 else ''}, {images['eros'][1] if len(images['eros'])>1 else ''}, {images['eros'][2] if len(images['eros'])>2 else ''}
    WHAT IS IN EACH IMAGE:
{eros_info}
    Caption FORMAT: "[Concrete visible content from the description above — name the figure, gesture, body part, scene] — for [specific Venus / Moon / sensual current reason]." LEAD WITH WHAT'S VISIBLE; do not open with "a form", "a presence", "a body". Name the actual content.
    If no description is provided for an image, write the bare minimum: "card N · for [Venus placement]" — do not invent visual content you cannot verify.

13. SECOND SOURCED QUOTE — USE THE SECTION 13 QUOTE provided above. Format identical to section 10.

14. THE LESSON — centered, font-size 21px italic #0a0a0a, max-width 380px margin auto. 2-3 sentences specific to Sara's Western chart.

15. TRY THIS — two-column grid (1fr 1fr, gap 2px, background #d4d1ca). Each cell background #faf8f3, padding 22px 18px. Label monospace 10px #8a857d + text 14px #1f1d18.

16. TODAY'S TOTEM — A single centered send-off image acting as the day's ally. Outer container: padding 32px 24px, border-top 1px solid #e0ddd5, text-align center.
    Label "TODAY'S TOTEM" in monospace 10px #8a857d letter-spacing 0.2em uppercase, margin-bottom 18px.
    Image: src="{images['totem']}" — display block, margin 0 auto, max-width 400px, width 100%, height auto, grayscale(100%) contrast(1.0).
    Below the image: a reasoning caption in italic 14px #1f1d18, line-height 1.7, max-width 360px, margin auto, padding-top 14px.
    FORMAT: "[Concrete description — name the specific subject visible in the image: the animal, deity, figure, scene, or composition from the metadata below] — chosen as today's totem for [brief specific astrological reason: which transit, dasha, nakshatra, and what it asks]."
    LEAD WITH THE SUBJECT. Do NOT open with abstract phrases like "a presence", "a form", "a figure at the edge of". Name it directly: "a stylized tiger's face with a meditator seated at its center", "a stag in moonlit field", "Hekate at the threshold". Pull the visual specifics from the metadata description verbatim or close to it.
    Image metadata:
{totem_info}
    Only if metadata description is genuinely empty, write a minimal caption like "Today's totem — chosen for [specific transit]" rather than inventing visual details you cannot verify.

═══ PART TWO: VEDIC READING ═══

Full-width divider: border-top 1px solid #e0ddd5. Then centered label "VEDIC READING" monospace 10px #8a857d letter-spacing 0.3em, padding 28px 24px.

17. VEDIC HEADLINE — different from Western. Italic serif clamp(32px,8vw,46px). Tied to Rahu Mahadasha or today's Vedic transit through her Libra-rising chart.

18. VEDIC CHIPS — Libra ASC · Virgo Sun · Capricorn Moon · Rahu Dasha · Mars Conjunct Lagna. Same chip style as Western.

19. VEDIC MAIN READING — 3 paragraphs. Ground in:
    - Rahu Mahadasha through her chart: Rahu in 2nd (Scorpio), the house of voice, accumulated resources, the artist's livelihood
    - Mars debilitated in Libra conjunct her ASC — the body as instrument, force tempered by Venus, the warrior who paints
    - Today's transiting planets in sidereal positions through Libra-ASC houses
    - Today's Moon nakshatra and its quality
    Vedic register: dharma, karma, the grahas as forces, the nodes as destiny shapers. More cosmic/cyclical than the Western psychological register.

20. VEDIC PLANET TABLE — same format as Western but using Vedic signs/houses. Include Rahu and Ketu.

21. VEDIC TRANSIT BOX — same cream panel as Key Aspects (background #f3f0e8), 3-4 key Vedic transits/dasha influences today.

22. VEDIC IMAGE CAROUSEL — 3 wide cards, 280px wide, 190px tall. Images: {vedic_img_list}
    WHAT IS IN EACH IMAGE:
{vedic_info}
    Caption FORMAT: "[Concrete visible content — name the subject from the description above: figure, scene, composition, distinctive object] — chosen for [specific Vedic theme: active nakshatra, dasha lord, planetary house]."
    LEAD WITH WHAT'S VISIBLE. Do not begin with "a form", "a presence", "a figure". Name it: "the woman in a luminous mermaid gown beside her dark-clad companion", "a yantra of intersecting golden lines on dark ground", "a peacock with iridescent tail spread".
    If a description is empty for one of the images, write the bare minimum for that card: "card N · for [Vedic theme]" — do not invent visual content.

23. VEDIC LESSON — centered italic 21px #0a0a0a, 2 sentences. Karmic/dharmic insight specific to Sara's Vedic chart.

24. VEDIC SOURCED QUOTE — USE THE SECTION 24 QUOTE provided above. Format identical to section 10.

Output ONLY the complete HTML document. Nothing else.
"""

    import time as _time
    full_text = ""
    last_error = None
    for attempt in range(1, 4):
        if attempt > 1:
            wait = 10 * (attempt - 1)
            print(f"  Stream attempt {attempt}/3 — retrying after {wait}s...")
            _time.sleep(wait)
        try:
            full_text = _http_post_stream_text(
                "https://api.anthropic.com/v1/messages",
                payload={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 32000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                timeout=600,
            )
            if full_text and len(full_text) >= 5000:
                break
            print(f"  Got short response ({len(full_text)} chars); retrying.")
        except Exception as e:
            last_error = e
            print(f"  Attempt {attempt} failed: {type(e).__name__}: {str(e)[:200]}")
    else:
        if last_error:
            raise last_error
        raise RuntimeError(f"All 3 stream attempts returned too-short responses (last: {len(full_text)} chars)")

    html = full_text.replace("```html", "").replace("```", "").strip()
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



def _inject_no_cache_meta(html):
    """Inject cache-busting meta tags into <head> so browsers always fetch fresh."""
    import re as _re
    tags = (
        '<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">'
        '<meta http-equiv="Pragma" content="no-cache">'
        '<meta http-equiv="Expires" content="0">'
    )
    new, n = _re.subn(r'(<head[^>]*>)', r'\1' + tags, html, count=1, flags=_re.IGNORECASE)
    if n == 0:
        return tags + html
    return new



# ---------- Quote system ----------
QUOTES_PATH = "quotes.json"
QUOTE_REPEAT_DAYS = 60  # don't reuse a quote within this window

def load_quotes():
    if not os.path.exists(QUOTES_PATH):
        return []
    with open(QUOTES_PATH) as f:
        return json.load(f)

def load_used_quotes(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_used_quotes(path, used):
    with open(path, "w") as f:
        json.dump(used, f, indent=2, ensure_ascii=False)

def _pick_one(quotes, used_dict, today, registers, exclude_authors=None, exclude_ids=None):
    from datetime import timedelta
    exclude_authors = exclude_authors or set()
    exclude_ids = exclude_ids or set()
    cutoff = today.date() - timedelta(days=QUOTE_REPEAT_DAYS)
    candidates = [q for q in quotes
                  if q.get("register") in registers
                  and q.get("author") not in exclude_authors
                  and q.get("id") not in exclude_ids]
    available = []
    for q in candidates:
        last = used_dict.get(q.get("id"))
        if last:
            try:
                last_d = datetime.strptime(last, "%Y-%m-%d").date()
                if last_d >= cutoff:
                    continue
            except Exception:
                pass
        available.append(q)
    if not available:
        available = candidates
    return random.choice(available) if available else None

def pick_quotes_for_today(quotes, used_dict, today):
    """Returns dict with keys section_10, section_11, section_13, section_24.
    Each pick excludes IDs and authors already used in earlier picks for the same day.
    """
    picked_ids = set()
    picked_authors = set()
    def _track(q):
        if q:
            picked_ids.add(q.get("id"))
            picked_authors.add(q.get("author"))
        return q
    sec10 = _track(_pick_one(quotes, used_dict, today,
                             ["contemplative", "lyric", "devotional"],
                             exclude_ids=picked_ids))
    sec11 = _track(_pick_one(quotes, used_dict, today, ["sensual"],
                             exclude_authors=picked_authors,
                             exclude_ids=picked_ids))
    sec13 = _track(_pick_one(quotes, used_dict, today,
                             ["contemplative", "lyric", "devotional", "sensual"],
                             exclude_authors=picked_authors,
                             exclude_ids=picked_ids))
    sec24 = _track(_pick_one(quotes, used_dict, today, ["vedic", "devotional"],
                             exclude_authors=picked_authors,
                             exclude_ids=picked_ids))
    return {"section_10": sec10, "section_11": sec11, "section_13": sec13, "section_24": sec24}

def record_used_quotes(used_dict, picked, today):
    today_str = today.strftime("%Y-%m-%d")
    for q in picked.values():
        if q and q.get("id"):
            used_dict[q["id"]] = today_str
    return used_dict

def fmt_quote(q):
    if not q:
        return "(no quote available — pick any verified real-poet quote you know.)"
    src = q.get("source", "")
    year = q.get("year", "")
    return f'''TEXT: "{q.get("text", "")}"
ATTRIBUTION: {q.get("author", "")} — {src}{f" ({year})" if year else ""}'''


USED_QUOTES_PATH = "used_quotes_sara.json"


def main():
    print(f"Generating Sara's horoscope for {datetime.now().strftime('%B %d, %Y')}...")
    print("Picking images...")
    images = pick_images()
    print("Fetching planetary positions...")
    planet_data = get_planet_positions()
    print("Picking today's quotes (no-repeat tracking)...")
    today_dt = datetime.now()
    quotes = load_quotes()
    used_quotes = load_used_quotes(USED_QUOTES_PATH)
    todays_quotes = pick_quotes_for_today(quotes, used_quotes, today_dt)
    for slot, q in todays_quotes.items():
        print(f"  {slot}: {q.get('id') if q else '(none — fallback)'}")
    print("Generating with Claude (Western + Vedic)...")
    html = generate_horoscope(planet_data, images, todays_quotes)
    html = _inject_no_cache_meta(html)

    # Write to sara/ (where GitHub Pages serves Sara's page from)
    print("Saving sara/index.html...")
    os.makedirs("sara", exist_ok=True)
    with open("sara/index.html", "w") as f:
        f.write(html)

    # Also write to docs/sara/ so any older workflow that still references that
    # path doesn't fail on git add.
    print("Saving docs/sara/index.html (compatibility)...")
    os.makedirs("docs/sara", exist_ok=True)
    with open("docs/sara/index.html", "w") as f:
        f.write(html)

    # Commit and push from inside the script so we don't depend on the
    # workflow's commit step.
    print("Committing and pushing changes...")
    try:
        import subprocess
        subprocess.run(["git", "config", "user.name", "horoscope-bot"], check=False)
        subprocess.run(
            ["git", "config", "user.email", "bot@horoscope"],
            check=False,
        )
        subprocess.run(
            ["git", "add", "sara/index.html", "docs/sara/index.html"],
            check=False,
        )
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if diff.returncode != 0:
            today = datetime.now().strftime("%Y-%m-%d")
            subprocess.run(
                ["git", "commit", "-m", f"Daily horoscope Sara {today}"],
                check=False,
            )
            subprocess.run(["git", "push"], check=False)
            print("✓ Pushed.")
        else:
            print("Nothing new to commit.")
    except Exception as e:
        print(f"Git step failed (non-fatal): {e}")

    print("Recording quotes used today...")
    used_quotes = record_used_quotes(used_quotes, todays_quotes, today_dt)
    save_used_quotes(USED_QUOTES_PATH, used_quotes)
    print("Sending email...")
    send_email(f"{GITHUB_PAGES_URL}?v={datetime.now().strftime('%Y%m%d')}")
    print("✓ Done!")


if __name__ == "__main__":
    main()
