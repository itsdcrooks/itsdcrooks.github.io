#!/usr/bin/env python3
"""
One-shot script to catalogue all URLs in the 'totem' pool from pools.json.

For each totem URL not already in cosmos_catalogue.json, calls Claude Haiku
vision to derive description, subjects, mood, and adds an entry to the
catalogue. The pools.json mapping handles slot assignment — entries here
just provide rich metadata so the daily horoscope's Today's Totem caption
can speak meaningfully to what's actually in the image.

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
COMMIT_EVERY = 25  # save + push progress every N entries

VALID_MOODS = [
    "contemplative", "sensual", "ethereal", "devotional", "tender",
    "raw", "cosmic", "abstract", "fierce", "architectural", "botanical",
]


def post_json(url, payload, headers, timeout=120):
    body = json.dumps(payload).encode("utf-8")
    h = dict(headers)
    h.setdefault("content-type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


TAG_PROMPT = f"""You are cataloguing this image for a horoscope's "Today's Totem" section, where one image per day is selected as a send-off ally. The horoscope's prompt will use the description and subjects you provide to write a 1-2 sentence reasoning caption.

Output ONLY a single JSON object. No prose, no markdown fences. Schema:

{{
  "description": "<3-4 sentence neutral description. Identify any specific animal, deity, saint, archangel, religious figure, or other recognizable subject by name. Note composition, mood, lighting, what's central to the frame.>",
  "mood": "<exactly one of: {', '.join(VALID_MOODS)}>",
  "subjects": ["<short noun phrase>", "<another>", "<another>"],
  "is_devotional": <true|false — true if sacred/ritual/religious imagery>,
  "is_botanical": <true|false>,
  "is_cosmic": <true|false>,
  "is_figure": <true|false — true if a human figure or body is present>
}}

Be specific about subjects. If it's a recognizable animal, name the species (e.g. "wolf", "stag", "owl"). If it's a deity or religious figure, name them (e.g. "Buddha", "Ganesha", "St. Francis", "Archangel Michael"). If a person but not a deity, describe them ("woman seated", "child running").
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
    if entry.get("mood") not in VALID_MOODS:
        entry["mood"] = "contemplative"
    entry["is_sensual"] = False  # totem pool is never sensual
    entry["suitable_for"] = ["closing"]  # used as send-off
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

    # Load totem URLs from pools.json
    if not POOLS_PATH.exists():
        print(f"No {POOLS_PATH.name} found. Aborting.")
        return
    with open(POOLS_PATH) as f:
        pools = json.load(f)
    totem_urls = [u.strip().rstrip(".") for u in pools.get("totem", []) if u.strip()]
    print(f"Totem pool has {len(totem_urls)} URLs")

    data = load_catalogue()
    catalogued_urls = {e.get("url") for e in data.get("catalogue", [])}
    failed_urls = {e.get("url") if isinstance(e, dict) else e for e in data.get("failed", [])}

    to_process = [u for u in totem_urls if u not in catalogued_urls and u not in failed_urls]
    print(f"Already catalogued: {len(totem_urls) - len(to_process)}")
    print(f"To process now:     {len(to_process)}\n")

    if not to_process:
        print("Nothing new to catalogue.")
        return

    added = 0
    failed = 0
    for i, url in enumerate(to_process, 1):
        prefix = f"[{i:3d}/{len(to_process)}]"
        try:
            entry = tag_image(api_key, url)
            data["catalogue"].append(entry)
            added += 1
            subjects = entry.get("subjects", [])[:3]
            print(f"{prefix} ✓ {url[-12:]} — {entry.get('mood'):14s} subjects={subjects}")
        except urllib.error.HTTPError as e:
            err = ""
            try:
                err = e.read().decode("utf-8", errors="ignore")[:200]
            except Exception:
                pass
            print(f"{prefix} ✗ HTTP {e.code}: {url}  {err}")
            data.setdefault("failed", []).append({"url": url, "reason": f"HTTP {e.code}", "ts": datetime.utcnow().isoformat()})
            failed += 1
            if e.code == 429:
                print("    (rate limited; sleeping 30s)")
                time.sleep(30)
        except Exception as e:
            print(f"{prefix} ✗ {url}: {type(e).__name__}: {e}")
            data.setdefault("failed", []).append({"url": url, "reason": str(e)[:200], "ts": datetime.utcnow().isoformat()})
            failed += 1

        # Periodic save + push for resumability
        if (i % COMMIT_EVERY) == 0:
            save_catalogue(data)
            git_commit_and_push(f"catalogue: totem progress +{added} ({i}/{len(to_process)})")

        time.sleep(0.4)

    save_catalogue(data)
    git_commit_and_push(f"catalogue: totem complete — +{added} entries, {failed} failed")

    print(f"\nDone. Added: {added}, Failed: {failed}")
    print(f"Final catalogue size: {len(data['catalogue'])}")


if __name__ == "__main__":
    main()
