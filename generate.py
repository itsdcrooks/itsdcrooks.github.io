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

CHART = """
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

# ── IMAGE CATALOGUE ──────────────────────────────────────────
# Load catalogue if available, otherwise use URL pool directly
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

def pick_images():
    today = datetime.now()
    seed = today.year * 10000 + today.month * 100 + today.day
    rng = random.Random(seed)

    def pick(moods=None, slot=None, exclude=[], n=1):
        if CATALOGUE:
            pool = CATALOGUE
            if moods:
                pool = [i for i in pool if i.get('mood') in moods]
            if slot:
                pool = [i for i in pool if slot in i.get('suitable_for', [])]
            pool = [i for i in pool if i['url'] not in exclude]
            rng.shuffle(pool)
            return [i['url'] + '?format=webp&w=800' for i in pool[:n]]
        else:
            pool = [u for u in ALL_IMAGES if u not in exclude]
            rng.shuffle(pool)
            return [u + '?format=webp&w=800' for u in pool[:n]]

    used = []
    hero = pick(moods=['fierce','cosmic','ethereal'], slot='hero', exclude=used)
    used += hero
    atm = pick(moods=['contemplative','devotional','cosmic','ethereal'], slot='devotional', exclude=used, n=4)
    used += atm
    sens = pick(moods=['sensual','tender','ethereal'], slot='sensual', exclude=used, n=5)
    used += sens
    closing = pick(moods=['contemplative','ethereal'], slot='closing', exclude=used, n=2)

    return {
        'hero': hero[0] if hero else ALL_IMAGES[0],
        'atm': atm,
        'sensual': sens,
        'closing': closing,
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
    except:
        pass
    return f"Date: {today.strftime('%B %d, %Y')}. Use your knowledge of current planetary positions."


def generate_horoscope(planet_data, images):
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    prompt = f"""You are generating a daily personal horoscope for Daniel (Sun Cancer 6H, Moon Pisces 2H, ASC Capricorn, Mercury Cancer 6H, Venus Leo 7H, Mars Taurus 5H, Jupiter Scorpio 10H, Saturn Pisces 2H, Uranus Capricorn 1H, Neptune Capricorn 1H, Pluto Scorpio 11H).

Today is {date_str}.

CURRENT PLANETARY DATA:
{planet_data}

Generate a complete self-contained HTML horoscope page. Use ONLY inline CSS (no <style> tags — email clients and some browsers strip them). Background #080808, body text #d6cfc4, headings #f2ede6, labels in Courier New monospace. Max width 480px centered.

REQUIRED SECTIONS IN ORDER:

1. TOPBAR — date left, sun sign + ascendant right. Monospace 11px, color #5a5550, letter-spacing 0.18em.

2. HERO IMAGE — use this exact src: {images['hero']}
   Full width, height 400px, object-fit cover, filter grayscale(100%) contrast(1.08), opacity 0.72.
   Below it: a caption line (↳ symbol + Courier New 11px #5a5550) explaining WHY this specific image was chosen for today — what you see in it and how it connects to today's dominant transit.

3. HEADLINE — large italic serif (clamp 36px to 52px), 2-5 words, poetic, tied to today's most important transit.

4. NATAL CHIPS — small monospace tags showing active placements. Highlight the ones most activated today with slightly brighter color (#aaa border #4a4a4a vs #5a5550 border #222).

5. MAIN READING — 3 paragraphs. Each paragraph grounded in a specific natal placement meeting a specific current transit. Precise, psychologically astute, Daniel's tone (LPC-A, entrepreneur, deep thinker).

6. ATMOSPHERE CAROUSEL — horizontal scrollable row of 4 image cards.
   Images: {images['atm'][0] if len(images['atm'])>0 else ''}, {images['atm'][1] if len(images['atm'])>1 else ''}, {images['atm'][2] if len(images['atm'])>2 else ''}, {images['atm'][3] if len(images['atm'])>3 else ''}
   Each card 280px wide, image 190px tall, object-fit cover, grayscale. Below each image: a card number/title in monospace 10px #333, then a caption in monospace 11px #5a5550 explaining what you see in that specific image and why it was chosen for that transit today.
   Use overflow-x: auto, display: flex, gap: 10px, scroll-snap-type: x mandatory on the container. Each card scroll-snap-align: start.

7. PLANET TABLE — every natal planet, what it's doing today. Format: symbol | name·house | colored status word + explanation.
   Status colors: active #a0c080, challenged #c08070, dormant #5a5550.
   Row borders #111, font-size 13px.

8. KEY ASPECTS BOX — dark background #0d0d0d, the 3-4 most important transits today shown as:
   [WHITE TAG: YOUR PLACEMENT] aspect-symbol [GHOST TAG: TRANSITING PLANET]
   Plus a one-line note in monospace 12px #5a5550 below.

9. CHECKLIST — "Right now [planet] is pushing you to..." then 4 items with ✓ marks. Specific and actionable.

10. SOURCED QUOTE — from a real canonical poet (Neruda, Rumi, Sappho, Rilke, Lorca, Anne Carson, Lucille Clifton, etc.) connected to today's transits. Attribute correctly. NEVER invent quotes.

11. SENSUAL SECTION — label "Venus in [sign] · [Moon situation]"
    Three paragraphs: astrologically grounded, embodied, sensual. Include one sourced quote from an erotic poet (Sappho, Neruda, Ovid, etc.) woven in naturally with em tags.
    
12. SENSUAL CAROUSEL — 5 portrait cards (200px wide, 320px tall images).
    Images: {images['sensual'][0] if len(images['sensual'])>0 else ''}, {images['sensual'][1] if len(images['sensual'])>1 else ''}, {images['sensual'][2] if len(images['sensual'])>2 else ''}, {images['sensual'][3] if len(images['sensual'])>3 else ''}, {images['sensual'][4] if len(images['sensual'])>4 else ''}
    Same carousel pattern. Each card: what you see in the image + why chosen for this specific transit/placement today.

13. SECOND SOURCED QUOTE — different poet, different register. Short, resonant.

14. THE LESSON — centered, large italic (21px), 2-3 sentences. The psychological/spiritual insight of the day, specific to Daniel's chart.

15. TRY THIS — two-column grid (1fr 1fr, gap 2px, background #111):
    LEFT "Consider" — a specific book, film, or idea connected to today's transits
    RIGHT "Listen" — a specific music recommendation for the day's energy

16. CLOSING CAROUSEL — 2 wide landscape cards (300px wide, 190px tall images).
    Images: {images['closing'][0] if len(images['closing'])>0 else ''}, {images['closing'][1] if len(images['closing'])>1 else ''}
    Label "Into the new season" or similar. Same caption format.

IMPORTANT:
- All CSS must be INLINE on each element (style="...")
- No <style> or <script> tags
- Carousels use CSS only: overflow-x:auto, display:flex, scroll-snap-type:x mandatory
- The page must be fully self-contained
- Output only the complete HTML, nothing else
"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 8000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
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
    body = f"""Your daily horoscope for {today} is ready.

Open it here: {url}

☽"""
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

    print("Generating with Claude...")
    html = generate_horoscope(planet_data, images)

    print("Saving index.html...")
    with open("index.html", "w") as f:
        f.write(html)

    print("Sending email...")
    send_email(GITHUB_PAGES_URL)

    print("✓ Done!")


if __name__ == "__main__":
    main()
