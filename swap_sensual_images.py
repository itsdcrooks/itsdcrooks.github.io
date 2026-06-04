#!/usr/bin/env python3
"""
One-shot: Replace all sensual/nude images in cosmos_catalogue.json
with the 90 new URLs in swap_sensual_urls.txt.

What this does:
  1. Backs up the existing catalogue to cosmos_catalogue.backup.json
  2. Removes every entry where is_sensual=true OR mood='sensual'
  3. Catalogues the 90 new URLs via Claude Haiku vision
  4. Forces is_sensual=true on each new entry and adds 'sensual' to suitable_for
  5. Commits and pushes the result

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
BACKUP_PATH = ROOT / "cosmos_catalogue.backup.json"
URLS_PATH = ROOT / "swap_sensual_urls.txt"
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
COMMIT_EVERY = 25

VALID_MOODS = [
    "contemplative", "sensual", "ethereal", "devotional", "tender",
    "raw", "cosmic", "abstract", "fierce", "architectural", "botanical",
]
VALID_SLOTS = ["hero", "sensual", "devotional", "botanical", "transitional", "closing"]


def post_json(url, payload, headers, timeout=120):
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("content-type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


TAG_PROMPT = f"""You are cataloguing this sensual/intimate image for a horoscope's image library.

Output ONLY a single JSON object. No prose, no markdown fences. Schema:

{{
  "description": "<2-3 sentence neutral description of subjects, composition, lighting, mood>",
  "mood": "<exactly one of: {', '.join(VALID_MOODS)}>",
  "subjects": ["<short noun phrase>", "<another>", "<another>"],
  "is_devotional": <true|false>,
  "is_botanical": <true|false>,
  "is_cosmic": <true|false>,
  "is_figure": <true|false — true if a human figure or body is present>,
  "suitable_for": [<one or more of: {', '.join(VALID_SLOTS)} — must include 'sensual'>]
}}
"""


def tag_image(api_key: str, image_url: str) -> dict:
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
    # Force the sensual flags regardless of what the model returned
    entry["is_sensual"] = True
    if entry.get("mood") not in VALID_MOODS:
        entry["mood"] = "sensual"
    slots = [s for s in entry.get("suitable_for", []) if s in VALID_SLOTS]
    if "sensual" not in slots:
        slots.insert(0, "sensual")
    entry["suitable_for"] = slots
    entry["url"] = image_url
    return entry


def git_commit_and_push(message: str):
    try:
        subprocess.run(["git", "config", "user.name", "horoscope-bot"], check=False)
        subprocess.run(["git", "config", "user.email", "bot@horoscope"], check=False)
        subprocess.run(["git", "add", "cosmos_catalogue.json", "cosmos_catalogue.backup.json"], check=False)
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

    # Step 1: Load + backup catalogue
    with open(CATALOGUE_PATH) as f:
        data = json.load(f)
    catalogue = data.get("catalogue", [])
    print(f"Existing catalogue: {len(catalogue)} entries")

    # Write backup before we change anything
    with open(BACKUP_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Backup written to {BACKUP_PATH.name}")

    # Step 2: Remove sensual entries
    def is_sensual_entry(e):
        return e.get("is_sensual") is True or e.get("mood") == "sensual"

    before = len(catalogue)
    new_catalogue = [e for e in catalogue if not is_sensual_entry(e)]
    removed = before - len(new_catalogue)
    print(f"Removed {removed} sensual entries (was {before}, now {len(new_catalogue)})")

    data["catalogue"] = new_catalogue

    # Step 3: Load new URLs
    if not URLS_PATH.exists():
        print(f"No {URLS_PATH.name} found. Exiting after removal.")
        # Save the removal so we don't lose it
        with open(CATALOGUE_PATH, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        git_commit_and_push(f"catalogue: removed {removed} sensual entries (no new URLs found)")
        return

    with open(URLS_PATH) as f:
        urls = [line.strip().rstrip(".") for line in f if line.strip()]
    print(f"Adding {len(urls)} new sensual URLs...\n")

    # Step 4: Catalogue each new URL
    added = 0
    failed = 0
    for i, url in enumerate(urls, 1):
        prefix = f"[{i:3d}/{len(urls)}]"
        try:
            entry = tag_image(api_key, url)
            data["catalogue"].append(entry)
            added += 1
            print(f"{prefix} ✓ {url[-12:]} — {entry.get('mood'):14s} → {entry.get('suitable_for')}")
        except urllib.error.HTTPError as e:
            err_text = ""
            try:
                err_text = e.read().decode("utf-8", errors="ignore")[:200]
            except Exception:
                pass
            print(f"{prefix} ✗ HTTP {e.code}: {url}  {err_text}")
            failed += 1
            if e.code == 429:
                print("    (rate limited; sleeping 30s)")
                time.sleep(30)
        except Exception as e:
            print(f"{prefix} ✗ {url}: {type(e).__name__}: {e}")
            failed += 1

        if (i % COMMIT_EVERY) == 0:
            data["total"] = len(data["catalogue"])
            data["success"] = len(data["catalogue"])
            with open(CATALOGUE_PATH, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            git_commit_and_push(f"catalogue: swap progress {i}/{len(urls)} (+{added} new, -{removed} old)")

        time.sleep(0.4)

    # Final save and push
    data["total"] = len(data["catalogue"])
    data["success"] = len(data["catalogue"])
    with open(CATALOGUE_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    git_commit_and_push(
        f"catalogue: sensual swap complete (-{removed} old, +{added} new, {failed} failed)"
    )

    print(f"\nDone. Removed: {removed}, Added: {added}, Failed: {failed}")
    print(f"Final catalogue size: {len(data['catalogue'])}")


if __name__ == "__main__":
    main()
