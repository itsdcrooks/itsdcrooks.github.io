# Add Sara's horoscope to your existing repo

Two files. They live alongside your existing setup. Nothing of yours gets touched.

---

## 1. Drop the files in

From the root of your existing horoscope repo (the one with `generate.py` and `cosmos_catalogue.json`):

```
generate_sara.py                          ← put at repo root
.github/workflows/sara.yml                ← put in workflows folder
```

That's it. Don't move or rename anything you already have.

---

## 2. Verify her chart in `generate_sara.py`

The `NATAL` dict near the top has values marked "verify."

- https://astro.com → run her chart (Oct 13 1993, 8:28 AM, El Paso TX) → confirm tropical degrees and house placements
- https://jhora.com → confirm sidereal Lahiri values and especially **current Mahadasha/Antardasha** → write the antardasha into `NATAL["current_dasha"]`

---

## 3. Add one new GitHub Secret

You already have `ANTHROPIC_API_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` in this repo. Sara's workflow reuses them.

Only one new secret:

| Name | Value |
|---|---|
| `SARA_EMAIL` | `gypsetsarita@gmail.com` |

Settings → Secrets and variables → Actions → New repository secret.

---

## 4. Commit and push

```bash
git add generate_sara.py .github/workflows/sara.yml
git commit -m "add sara daily horoscope"
git push
```

---

## 5. Test it

Actions tab → `daily-horoscope-sara` → Run workflow → Run.

If green:
- Sara gets the email
- `docs/sara/index.html` is created and committed
- `used_images_sara.json` is created and committed
- Live page: `https://itsdcrooks.github.io/sara/` (or wherever your Pages domain is)

If red: open the failed step. The most common issue is `SARA_EMAIL` typo or missing.

---

## What's shared, what's separate

| | Shared with yours | Separate |
|---|---|---|
| Cosmos catalogue | ✓ | |
| Anthropic API key, SMTP creds | ✓ | |
| GitHub Pages site | ✓ (different sub-path) | |
| Output HTML | | docs/sara/index.html |
| No-repeat image log | | used_images_sara.json |
| Workflow schedule | (same time, separate run) | |
| Recipient email | | SARA_EMAIL |
| Natal chart, prompt | | generate_sara.py |

Both workflows run at 13:00 UTC. The `concurrency` block in sara.yml makes sure git pushes don't collide if your workflow finishes first.

---

## Notes on naming

- Email subject and "to": **Sara**
- Default name inside the readings: **Sara**
- Shifts to **Sarita** only when the reading is specifically about her artist self — the music, the painting, the touring, the muse. Sara is the woman; Sarita is the art.

Both constants live at the top of `generate_sara.py` if you want to retune.
