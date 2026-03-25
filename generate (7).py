import os
import json
import random
import smtplib
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TO_EMAIL           = "ddcrooks3@gmail.com"
GITHUB_PAGES_URL   = "https://itsdcrooks.github.io"

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
Sun in Cancer, 7°6' — 6th House
Moon in Pisces, 17°31' — 2nd House
Ascendant in Capricorn, 10°16' — 1st House
Mercury in Cancer, 1°35' — 6th House
Venus in Leo, 16°2' — 7th House
Mars in Taurus, 26°31' — 5th House
Jupiter in Scorpio, 4°46' — 10th House
Saturn in Pisces, 12°22' — 2nd House
Uranus in Capricorn, 25°3' — 1st House
Neptune in Capricorn, 22°22' — 1st House
Pluto in Scorpio, 25°38' — 11th House
"""

VEDIC_CHART = """
Ascendant: Sagittarius — ruled by Jupiter
Sun: Gemini, 12°55' — Ardra nakshatra (Rahu) — 7th House
Moon: Libra, 14°56' — Swati nakshatra (Rahu) — 11th House
Mars: Cancer — Ashlesha nakshatra — 8th House
Mercury: Gemini — Ardra nakshatra — 7th House
Jupiter: Aries — Bharani nakshatra — 5th House
Venus: Cancer — Ashlesha nakshatra — 8th House
Saturn (R): Aquarius — Shatabhisha nakshatra — 3rd House
Rahu (R): Aries — 5th House
Ketu (R): Libra — 11th House

Current Vimsottari Dasha: Rahu Mahadasha
Current Antardasha: Rahu-Venus (through approximately November 2026)
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


USED_IMAGES_FILE = "used_images.json"

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
    # Use date seed only for shuffling order within the available pool
    seed = today.year * 10000 + today.month * 100 + today.day
    rng = random.Random(seed)

    # Load previously used images — never repeat until pool is exhausted
    previously_used = load_used_images()

    # Get the full pool of available URLs
    all_urls = set(i['url'] for i in CATALOGUE) if CATALOGUE else set(ALL_IMAGES)

    # If we've used everything, reset and start fresh
    available = all_urls - previously_used
    if not available:
        print("Full image pool exhausted — resetting used images list.")
        previously_used = set()
        available = all_urls

    today_used = []  # track what we pick today

    def pick(moods=None, slot=None, exclude=[], n=1):
        # Exclude both today's picks and all previously used images
        excluded = set(exclude) | previously_used | set(today_used)
        if CATALOGUE:
            pool = CATALOGUE
            if moods:
                pool = [i for i in pool if i.get('mood') in moods]
            if slot:
                pool = [i for i in pool if slot in i.get('suitable_for', [])]
            pool = [i for i in pool if i['url'] not in excluded]
            # If filtered pool is empty, fall back to mood-only (ignore slot)
            if not pool and moods:
                pool = [i for i in CATALOGUE if i.get('mood') in moods and i['url'] not in excluded]
            # If still empty, use anything not used today
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

        # Record base URLs (without query params) as used
        for url in result:
            base = url.split('?')[0]
            today_used.append(base)
        return result

    hero      = pick(moods=['fierce','cosmic','ethereal'], slot='hero', n=1)
    atm       = pick(moods=['contemplative','devotional','cosmic','ethereal'], slot='devotional', n=4)
    sens      = pick(moods=['sensual','tender','ethereal'], slot='sensual', n=5)
    closing   = pick(moods=['contemplative','ethereal'], slot='closing', n=2)
    vedic_imgs = pick(moods=['devotional','contemplative','cosmic'], slot='devotional', n=3)

    # Save all today's picks as used
    save_used_images(previously_used | set(today_used))
    print(f"✓ Images picked: {len(today_used)} new, {len(previously_used)} previously used, {len(all_urls)} total pool")

    return {
        'hero':    hero[0] if hero else ALL_IMAGES[0],
        'atm':     atm,
        'sensual': sens,
        'closing': closing,
        'vedic':   vedic_imgs,
    }


def get_planet_positions():
    today = datetime.now()
    try:
        r = requests.get(
            "https://astrolibrary.org/current-planets/",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.ok and len(r.text) > 500:
            return r.text[:3000]
    except Exception:
        pass
    return f"Date: {today.strftime('%B %d, %Y')}. Use your knowledge of current planetary positions."


def generate_horoscope(planet_data, images):
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")
    day_name = today.strftime("%A")
    flame = SACRED_FLAMES.get(day_name, SACRED_FLAMES["Sunday"])
    vedic_img_list = ", ".join(images.get('vedic', []))

    prompt = f"""You are generating a daily personal horoscope for Daniel — Licensed Professional Counselor Associate, entrepreneur, and integrative thinker. Today is {date_str}.

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

1. TOPBAR — date left, "☀ Cancer · ↑ Capricorn" right. Monospace 11px #5a5550 letter-spacing 0.18em. Border-bottom 1px solid #161616. Padding 26px 24px 14px.

2. HERO IMAGE — src="{images['hero']}" — width 100%, height 400px, object-fit cover, grayscale(100%) contrast(1.08), opacity 0.72. Gradient overlay at bottom. Caption below: ↳ symbol + monospace 11px #5a5550 describing what you see in the image and why chosen for today's dominant Western transit.

3. HEADLINE — font-size clamp(36px,9vw,52px), italic, font-weight 400, letter-spacing -0.01em. Tied to today's most important Western transit.

4. NATAL CHIPS — flex wrap, gap 7px. Active ones: border 1px solid #4a4a4a, color #aaa. Inactive: border 1px solid #222, color #5a5550. Monospace 10px letter-spacing 0.1em uppercase padding 4px 9px.

5. MAIN WESTERN READING — 3 paragraphs, font-size 17px, line-height 1.78, color #d6cfc4. Each grounded in specific natal placement + current transit.

6. ATMOSPHERE CAROUSEL — 4 cards, 280px wide each. Images:
   {images['atm'][0] if len(images['atm'])>0 else ''}, {images['atm'][1] if len(images['atm'])>1 else ''}, {images['atm'][2] if len(images['atm'])>2 else ''}, {images['atm'][3] if len(images['atm'])>3 else ''}
   Each image 190px tall, object-fit cover, grayscale. Below: card number monospace 10px #2a2a2a, caption monospace 11px #5a5550 — what you see + why chosen.

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
    Each card: number title + caption describing image + why chosen for this transit/placement.

13. SECOND SOURCED QUOTE — different poet, short, resonant.

14. THE LESSON — centered, font-size 21px italic #f2ede6, max-width 380px margin auto. 2-3 sentences specific to Daniel's Western chart.

15. TRY THIS — two-column grid (1fr 1fr, gap 2px, background #111). Each cell background #080808, padding 22px 18px. Label monospace 10px #5a5550 + text 14px #d6cfc4.

16. CLOSING CAROUSEL — 2 landscape cards, 300px wide, 190px tall. Images:
    {images['closing'][0] if len(images['closing'])>0 else ''}, {images['closing'][1] if len(images['closing'])>1 else ''}

═══ PART TWO: VEDIC READING ═══

Full-width divider: border-top 1px solid #2a2a2a. Then centered label "VEDIC READING" monospace 10px #5a5550 letter-spacing 0.3em, padding 28px 24px.

17. VEDIC HEADLINE — different from Western. Italic serif clamp(32px,8vw,46px). Tied to Rahu-Venus dasha or today's Vedic transit.

18. VEDIC CHIPS — Sag ASC · Gemini Sun · Libra Moon · Rahu Dasha · Venus Antardasha. Same chip style as Western.

19. VEDIC MAIN READING — 3 paragraphs. Ground in:
    - Rahu-Venus antardasha: Rahu in 5th (Aries), Venus in 8th (Cancer) — desire, transformation, creative ambition, the hidden becoming visible
    - Today's transiting planets in sidereal positions through Sagittarius ASC houses
    - Today's Moon nakshatra and its quality
    Vedic register: dharma, karma, the grahas as forces, the nodes as destiny shapers. More cosmic/cyclical than the Western psychological register.

20. VEDIC PLANET TABLE — same format as Western but using Vedic signs/houses. Include Rahu and Ketu.

21. VEDIC TRANSIT BOX — same dark box, 3-4 key Vedic transits/dasha influences today.

22. VEDIC IMAGE CAROUSEL — 3 wide cards, 280px wide, 190px tall. Images: {vedic_img_list}
    Captions: connect each image to a specific Vedic theme — a nakshatra quality, a graha's nature, or the Rahu-Venus dasha.

23. VEDIC LESSON — centered italic 21px #f2ede6, 2 sentences. Karmic/dharmic insight specific to Daniel's Vedic chart.

24. VEDIC SOURCED QUOTE — from Vedic/Sanskrit tradition, Bhagavad Gita, Upanishads, or a poet whose work resonates with Jyotish. Real quote, properly attributed.

Output ONLY the complete HTML document. Nothing else.
"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 12000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=180,
    )
    response.raise_for_status()
    html = response.json()["content"][0]["text"]
    html = html.replace("```html", "").replace("```", "").strip()
    return html


def send_email(url):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("No email credentials — skipping email.")
        return
    today = datetime.now().strftime("%B %d, %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"☽ Daily Reading · {today}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    body = f"Your daily horoscope for {today} is ready.\n\nOpen it here: {url}\n\n☽"
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())
    print(f"✓ Email sent to {TO_EMAIL}")


def main():
    print(f"Generating horoscope for {datetime.now().strftime('%B %d, %Y')}...")
    print("Picking images...")
    images = pick_images()
    print("Fetching planetary positions...")
    planet_data = get_planet_positions()
    print("Generating with Claude (Western + Vedic)...")
    html = generate_horoscope(planet_data, images)
    print("Saving index.html...")
    with open("index.html", "w") as f:
        f.write(html)
    print("Sending email...")
    send_email(GITHUB_PAGES_URL)
    print("✓ Done!")


if __name__ == "__main__":
    main()
