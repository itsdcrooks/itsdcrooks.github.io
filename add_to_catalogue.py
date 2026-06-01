#!/usr/bin/env python3
"""
One-shot script to catalogue new images.

Reads URLs from urls_to_catalogue.txt, calls Claude Haiku vision on each,
builds catalogue entries matching the existing schema, and appends to
cosmos_catalogue.json. Resumable: skips any URL already in the catalogue.

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
URLS_PATH = ROOT / "urls_to_catalogue.txt"
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
COMMIT_EVERY = 25  # Save and commit progress every N successful entries

VALID_MOODS = [
    "contemplative", "sensual", "ethereal", "devotional", "tender",
    "raw", "cosmic", "abstract", "fierce", "architectural", "botanical",
]
VALID_SLOTS = ["hero", "sensual", "devotional", "botanical", "transitional", "closing"]


# ---------- HTTP helpers (stdlib only) ----------
def post_json(url, payload, headers, timeout=120):
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("content-type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------- Prompt + parsing ----------
TAG_PROMPT = f"""You are cataloguing this image for a daily horoscope's image library.

Output ONLY a single JSON object. No prose, no markdown fences. Schema:

{{
  "description": "<2-3 sentence description of what is actually in the image — subjects, composition, lighting, mood. Write in the style of an art catalogue, neutral and precise.>",
  "mood": "<exactly one of: {', '.join(VALID_MOODS)}>",
  "subjects": ["<short noun phrase>", "<another>", "<another>", "<another (optional)>"],
  "is_sensual": <true|false — true if nudity, intimacy, or erotic charge>,
  "is_devotional": <true|false — true if sacred, ritual, religious, or spiritual imagery>,
  "is_botanical": <true|false — true if flowers, plants, or organic plant life is central>,
  "is_cosmic": <true|false — true if stars, planets, cosmos, or vast atmospheric phenomena>,
  "is_figure": <true|false — true if a human figure or body is present>,
  "suitable_for": [<one or more of: {', '.join(VALID_SLOTS)}>]
}}

Slot guidance:
- "hero": striking, atmospheric, can carry the top of a page
- "sensual": intimate, bodily, erotic charge
- "devotional": sacred, ritual, prayer-like
- "botanical": flowers, plants central
- "transitional": quieter image that can sit mid-page
- "closing": meditative, conclusive, often landscape or atmospheric

Many images fit 2-3 slots. Include all that fit.
"""


def tag_image(api_key: str, image_url: str) -> dict:
    """Call Claude vision on a URL, return parsed catalogue entry."""
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
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = post_json("https://api.anthropic.com/v1/messages", payload, headers)
    text = data["content"][0]["text"].strip()
    # Strip markdown fences if model added them despite instruction
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    entry = json.loads(text)
    # Validate vocab
    if entry.get("mood") not in VALID_MOODS:
        entry["mood"] = "contemplative"
    entry["suitable_for"] = [s for s in entry.get("suitable_for", []) if s in VALID_SLOTS] or ["transitional"]
    # Ensure URL is set
    entry["url"] = image_url
    return entry


# ---------- Catalogue I/O ----------
def load_catalogue():
    if not CATALOGUE_PATH.exists():
        return {"catalogue": [], "failed": [], "total": 0, "success": 0, "version": "1.0"}
    with open(CATALOGUE_PATH) as f:
        data = json.load(f)
    data.setdefault("catalogue", [])
    if isinstance(data.get("failed"), int):
        data["failed"] = []
    data.setdefault("failed", [])
    return data


def save_catalogue(data):
    data["total"] = len(data["catalogue"]) + len(data.get("failed", []))
    data["success"] = len(data["catalogue"])
    with open(CATALOGUE_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------- Git ----------
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


# ---------- Main ----------
def main():
    api_key = os.environ["ANTHROPIC_API_KEY"]

    if not URLS_PATH.exists():
        print(f"No {URLS_PATH.name} found. Nothing to do.")
        return

    with open(URLS_PATH) as f:
        urls = [line.strip().rstrip(".") for line in f if line.strip()]

    print(f"Loaded {len(urls)} URLs to consider.")
    data = load_catalogue()
    existing_urls = {e.get("url") for e in data["catalogue"]}
    failed_urls = {e.get("url") if isinstance(e, dict) else e for e in data.get("failed", [])}

    to_process = [u for u in urls if u not in existing_urls and u not in failed_urls]
    print(f"Already catalogued: {len(urls) - len(to_process)}")
    print(f"To process now:     {len(to_process)}\n")

    if not to_process:
        print("Nothing new to catalogue. Exiting.")
        return

    added_this_run = 0
    failed_this_run = 0

    for i, url in enumerate(to_process, 1):
        prefix = f"[{i:3d}/{len(to_process)}]"
        try:
            entry = tag_image(api_key, url)
            data["catalogue"].append(entry)
            added_this_run += 1
            print(f"{prefix} ✓ {url[-12:]} — {entry.get('mood'):14s} → {entry.get('suitable_for')}")
        except urllib.error.HTTPError as e:
            err_text = ""
            try:
                err_text = e.read().decode("utf-8", errors="ignore")[:200]
            except Exception:
                pass
            print(f"{prefix} ✗ HTTP {e.code}: {url} {err_text}")
            data["failed"].append({"url": url, "reason": f"HTTP {e.code}", "ts": datetime.utcnow().isoformat()})
            failed_this_run += 1
            if e.code == 429:  # Rate limited
                print("    (rate limited; sleeping 30s)")
                time.sleep(30)
        except Exception as e:
            print(f"{prefix} ✗ {url}: {type(e).__name__}: {e}")
            data["failed"].append({"url": url, "reason": str(e)[:200], "ts": datetime.utcnow().isoformat()})
            failed_this_run += 1

        # Periodic save + push for resumability
        if (i % COMMIT_EVERY) == 0:
            save_catalogue(data)
            git_commit_and_push(
                f"catalogue: +{added_this_run} entries (progress {i}/{len(to_process)})"
            )

        # Light rate-limit pacing
        time.sleep(0.4)

    save_catalogue(data)
    git_commit_and_push(
        f"catalogue: +{added_this_run} new entries, {failed_this_run} failed"
    )

    print(f"\nDone. Added: {added_this_run}, Failed: {failed_this_run}")
    print(f"Total catalogue size: {len(data['catalogue'])}")


if __name__ == "__main__":
    main()
