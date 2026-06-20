#!/usr/bin/env python3
"""
One-shot script to catalogue ALL remaining pool URLs from pools.json that
are not yet in cosmos_catalogue.json. Skips totem URLs already catalogued.

For each remaining URL, calls Claude Haiku vision to derive a concrete
description, mood, subjects, and flags. Computes suitable_for from which
pool(s) the URL appears in so the fallback mood-based picker can still find
it if needed.

Env vars required:
  ANTHROPIC_API_KEY
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
CATALOGUE_PATH = ROOT / "cosmos_catalogue.json"
POOLS_PATH = ROOT / "pools.json"
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
COMMIT_EVERY = 30

VALID_MOODS = [
    "contemplative", "sensual", "ethereal", "devotional", "tender",
    "raw", "cosmic", "abstract", "fierce", "architectural", "botanical",
]

# Map each pool to the slot label used by the fallback mood-based picker
POOL_TO_SLOT = {
    "hero":  "hero",
    "aura":  "devotional",
    "eros":  "sensual",
    "vedic": "devotional",
    "totem": "closing",
}


def post_json(url, payload, headers, timeout=120):
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("content-type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


TAG_PROMPT = f"""You are cataloguing this image for a daily horoscope's image carousels (Hero, Aura, Eros, Vedic, Totem). The horoscope prompt will use your description to write captions that describe what's visible and connect it to that day's astrology. Be visually concrete — captions will pull directly from this.

Output ONLY a single JSON object. No prose, no markdown fences. Schema:

{{
  "description": "<3-4 sentences. NAME THE SPECIFIC SUBJECT: if an animal, name the species. If a deity/saint/religious figure, name them. If human, describe pose, clothing, action, body language. Describe composition, lighting, palette, mood. Avoid abstract poetry — be concrete.>",
  "mood": "<exactly one of: {', '.join(VALID_MOODS)}>",
  "subjects": ["<short noun phrase>", "<another>", "<another>"],
  "is_devotional": <true|false — sacred, ritual, or religious imagery>,
  "is_botanical": <true|false — plants, flowers, gardens central>,
  "is_cosmic": <true|false — stars, geometry, celestial, yantras>,
  "is_figure": <true|false — a human or body is present>,
  "is_sensual": <true|false — intimate, erotic, or Venus-themed content>
}}

Lead with the concrete subject. Examples: "A snow leopard at rest on grey stone, head turned in profile…", "Two figures embracing under a draped white cloth, only their hands and shoulders visible…", "A yantra of intersecting golden lines on a deep indigo ground, eight-petaled mandala at center…"."""


def tag_image(api_key: str, image_url: str, pools_for_url: set) -> dict:
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "url", "url": image_url}},
                {"type": "text", "text": TAG_PROMPT},
            ],
        }],
    }
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    data = post_json("https://api.anthropic.com/v1/messages", payload, headers)
    text = data["content"][0]["text"].strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    entry = json.loads(text)
    if entry.get("mood") not in VALID_MOODS:
        entry["mood"] = "contemplative"
    # Compute suitable_for from which pools this URL belongs to
    entry["suitable_for"] = sorted({POOL_TO_SLOT[p] for p in pools_for_url if p in POOL_TO_SLOT})
    entry["url"] = image_url
    return entry


def load_catalogue():
    if not CATALOGUE_PATH.exists():
        return {"catalogue": [], "failed": [], "total": 0, "success": 0, "version": "1.0"}
    with open(CATALOGUE_PATH) as f:
        return json.load(f)


def save_catalogue(data):
    data["total"] = len(data["catalogue"]) + len(data.get("failed", []))
    data["success"] = len(data["catalogue"])
    with open(CATALOGUE_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def git_commit_and_push(message: str):
    try:
        subprocess.run(["git", "config", "user.name", "horoscope-bot"], check=False)
        subprocess.run(["git", "config", "user.email", "bot@horoscope"], check=False)
        subprocess.run(["git", "add", "cosmos_catalogue.json"], check=False)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", message], check=False)
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
            subprocess.run(["git", "push"], check=False)
            print(f"  ✓ Pushed: {message}")
    except Exception as e:
        print(f"  Git push failed (non-fatal): {e}")


def main():
    api_key = os.environ["ANTHROPIC_API_KEY"]

    if not POOLS_PATH.exists():
        print(f"No {POOLS_PATH.name} found. Aborting.")
        return
    with open(POOLS_PATH) as f:
        pools = json.load(f)

    # Build reverse map: url -> set of pools it belongs to
    url_to_pools: dict[str, set] = {}
    for pool_name, urls in pools.items():
        for u in urls:
            u = u.strip().rstrip(".")
            if not u:
                continue
            url_to_pools.setdefault(u, set()).add(pool_name)

    all_pool_urls = list(url_to_pools.keys())
    print(f"Total unique URLs across all pools: {len(all_pool_urls)}")

    data = load_catalogue()
    catalogued_urls = {e.get("url") for e in data.get("catalogue", [])}
    failed_urls = {(e.get("url") if isinstance(e, dict) else e) for e in data.get("failed", [])}

    to_process = [u for u in all_pool_urls if u not in catalogued_urls and u not in failed_urls]
    print(f"Already catalogued: {len(all_pool_urls) - len(to_process)}")
    print(f"To process now:     {len(to_process)}\n")

    if not to_process:
        print("Nothing new to catalogue.")
        return

    added = 0
    failed = 0
    for i, url in enumerate(to_process, 1):
        prefix = f"[{i:3d}/{len(to_process)}]"
        pool_membership = url_to_pools.get(url, set())
        pool_tag = "/".join(sorted(pool_membership))
        try:
            entry = tag_image(api_key, url, pool_membership)
            data["catalogue"].append(entry)
            added += 1
            subjects = entry.get("subjects", [])[:3]
            print(f"{prefix} \u2713 [{pool_tag:20s}] {url[-12:]} — {entry.get('mood'):14s} {subjects}")
        except urllib.error.HTTPError as e:
            err = ""
            try:
                err = e.read().decode("utf-8", errors="ignore")[:200]
            except Exception:
                pass
            print(f"{prefix} \u2717 HTTP {e.code}: {url}  {err}")
            data.setdefault("failed", []).append({"url": url, "reason": f"HTTP {e.code}", "ts": datetime.utcnow().isoformat()})
            failed += 1
            if e.code == 429:
                print("    (rate limited; sleeping 30s)")
                time.sleep(30)
        except Exception as e:
            print(f"{prefix} \u2717 {url}: {type(e).__name__}: {e}")
            data.setdefault("failed", []).append({"url": url, "reason": str(e)[:200], "ts": datetime.utcnow().isoformat()})
            failed += 1

        if (i % COMMIT_EVERY) == 0:
            save_catalogue(data)
            git_commit_and_push(f"catalogue: pools progress +{added} ({i}/{len(to_process)})")

        time.sleep(0.4)

    save_catalogue(data)
    git_commit_and_push(f"catalogue: pools complete — +{added} entries, {failed} failed")

    print(f"\nDone. Added: {added}, Failed: {failed}")
    print(f"Final catalogue size: {len(data['catalogue'])}")


if __name__ == "__main__":
    main()
