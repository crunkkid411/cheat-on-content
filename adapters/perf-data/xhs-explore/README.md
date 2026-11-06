# Adapter: xhs-explore (Xiaohongshu crawler)

Automatically invoked by `/cheat-retro` when `state.data_collection=adapter` + `platform=xhs`.

> **Origin**: copies the `douyin-session` adapter's architecture (Playwright persisted login session + passive XHR interception);
> API paths and fields reference NanmiCoder/MediaCrawler and ReaJason/xhs. Verified end-to-end on a real creator account (2026-05).
> In 2026-06 it merged the public-page parsing capability of [xhs-analytics](https://github.com/SingularGuyLeBorn/xhs-analytics):
> logged-out fetching of body / images / tags / top-comment fallback, plus bulk archive and account-summary commands.

---

## What this adapter does

Xiaohongshu's anti-scraping relies on `x-s`/`x-t`/`x-s-common` signatures + `xsec_token` — plain HTTP / requests gets no data.

xhs-explore uses **Playwright + a persistent Chromium context** to simulate a real browser, **without reverse-engineering signatures or forging requests**:
it lets the page send its own signed requests and only passively intercepts the returned JSON; it also uses the public page's `__INITIAL_STATE__` as a fallback for body/images/comments:

- Scan the QR code to log in to the creator center the first time; the cookie is stored in **your content project root** under `.auth-xhs/`
- Every later fetch reuses the cookie
- It fetches three data paths:
  1. **Creator-center galaxy API** (`/api/galaxy/v2/creator/note/user/posted`) — operational data for **your own** notes: views/likes/saves/comments/shares, **no xsec_token needed**, the most stable. Each list item carries its own `xsec_token`, so fetching your own notes needs no manual pasting of tokenized links
  2. **Frontend web API** (`/api/sns/web/v1/feed` + `/api/sns/web/v2/comment/page`) — confirmed like/save counts + comment text
  3. **Public-page fallback** (`window.__INITIAL_STATE__` on `www.xiaohongshu.com/explore/<note_id>`) — **no login needed** to fill in the body, image URLs, and tags; when the frontend API cannot get comments, use the public page's top comments as a fallback (usually ~10)

Output is written to **your content project's** `videos/<...>/report.md`.
Debug artifacts (URL dumps / screenshots / raw galaxy JSON) are written to `.cheat-cache/xhs-explore-debug/`.

## Field mapping (calibrated)

The real field names of galaxy `note/user/posted` have been confirmed on a real account and are hardcoded in `_normalize_note()` in `crawler.py`:
views `view_count`, likes `likes`, saves `collected_count`, comments `comments_count`, shares `shared_count`,
publish time `visible_time` (unix seconds) / `time` (local time string), per-note `xsec_token`.

If a Xiaohongshu redesign makes a field show 0: open the "galaxy raw fields" JSON at the end of `videos/<...>/report.md`
and add the new key to the corresponding `_first(v, ...)` candidate list in `_normalize_note()` (the multi-candidate fallback is retained).

## Installation (one-time)

```bash
# 1. Enter your content project root
cd ~/Documents/my-channel

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies (Playwright + Chromium + requests)
pip install -r "$ADAPTER/requirements.txt"
playwright install chromium

# 4. Log in to the Xiaohongshu creator center via QR code for the first time
ADAPTER=$(find ~/cheat-on-content -name "xhs-explore" -type d 2>/dev/null | head -1)
python "$ADAPTER/crawler.py" login
# → a Chromium window opens; scan the QR code with the Xiaohongshu app
# → the window closes automatically after login; the cookie is stored in the current directory/.auth-xhs/
```

> Windows note: the adapter lives at `~/cheat-on-content/adapters/perf-data/xhs-explore` (the cloned source),
> not in `~/.claude/skills` (install.sh only copies the 15 skills, not adapters).

## Usage

cheat-retro calls it automatically. Manual testing:

```bash
cd ~/Documents/my-channel
source .venv/bin/activate

# List recent notes (verify the login session has not expired)
python "$ADAPTER/review.py" list

# Fetch a specific note
python "$ADAPTER/review.py" note <note_id> [script.txt]

# Fetch a specific note and download images to videos/<...>/images/
XHS_DOWNLOAD_IMAGES=1 python "$ADAPTER/review.py" note <note_id>

# Bulk-archive the body + images of published notes (public-page parsing, no login)
python "$ADAPTER/review.py" archive my_notes.json data/raw/notes/archive 50

# Account-level summary (based on the creator center's latest 50 + public-page tags)
python "$ADAPTER/review.py" summarize reports
```

Output goes to current-directory/videos/<date>_<title>/report.md; archive output goes to `<output_root>/<note_id>/`.

## How to get the note_id

Xiaohongshu note URLs:
- `https://www.xiaohongshu.com/explore/66f1a2b3c4d5e6f700112233?xsec_token=...` → `note_id = 66f1a2b3c4d5e6f700112233`
- `https://xhslink.com/xxxxx` → short link; cheat-publish resolves it

When cheat-publish registers a publish it stores the note_id in the prediction header, and cheat-retro reads that field at startup.

## report.md output format

Generated by `renderer.py`:
- Note metadata (title, publish time, link, IP location)
- Data snapshot (impressions/views, likes, saves, comments, shares + derived ratios: like-to-impression / save-to-impression / comment-to-impression / share-to-impression + follower gain)
- Body + tags (only present when the public-page fallback is used)
- Images (local path preferred, otherwise URL)
- galaxy raw fields JSON (debug / for checking fields when the API changes)
- The original script (passed in by cheat-retro)
- Top comments (sorted by like count, including text + like count + IP)

## Failure modes (highest to lowest probability)

| Symptom | Cause | Handling |
|---|---|---|
| Impressions show 0 but the JSON has data | The galaxy field key is not in the candidate list | Check the galaxy JSON in report.md and add the real key to `_normalize_note` |
| `ensure_login` times out | Cookie expired | Rerun `python crawler.py login` |
| Note list is empty | The creator center changed the galaxy API path | Check `.cheat-cache/xhs-explore-debug/creator_urls.txt` and update `GALAXY_*_KEYS` |
| Comments not fetched | xsec_token missing / comments closed / login expired | Check `frontend_urls.txt` first; then fall back to public-page top comments; finally paste comments manually |
| Body/images/tags missing | The public page also failed to parse | Check the note_id and xsec_token; update `_extract_initial_state` when the page structure changes |
| Chromium crashes | Insufficient memory | Close other Chromium instances; `playwright install chromium --force` |

**Key reality**: Xiaohongshu's API paths (`/feed`, `/comment/page`, galaxy) are relatively stable, but the signature and xsec_token mechanisms change often.
This adapter avoids signature risk through passive interception + public-page fallback — the most fragile parts are the **galaxy creator API** and **comment replies**.

## Stability level

★★ — Playwright + a login session withstands far stronger anti-scraping than plain HTTP, but is still affected by Xiaohongshu frontend redesigns.
The comment path (dependent on xsec_token) is more fragile than the creator-data path; when necessary, degrade to manual or the public-page fallback.

## Risk notes

- **Cold-start users should install with care**: Playwright + Chromium ~500MB
- **TOS risk**: using your own cookie to fetch your own backend data is personal use; do not abuse it, do not run it at high frequency
- **Do not commit `.auth-xhs/` to git**: the cookie contains session credentials; a leak = someone else can log in to your Xiaohongshu account
- `.cheat-cache/xhs-explore-debug/` should also not be committed (it contains debug screenshots / API URLs / raw JSON)

## File list

```
adapters/perf-data/xhs-explore/
├── README.md           # this file
├── requirements.txt    # playwright>=1.44, requests>=2.28
├── crawler.py          # crawl core (galaxy / frontend API / public-page fallback / image download)
├── review.py           # CLI entry point (login / list / note / archive / summarize)
├── renderer.py         # renders the fetched JSON into report.md
├── paths.py            # project root / .auth-xhs / debug path resolution
└── run.sh              # wrapper invoked by cheat-retro
```

## Relationship to the other adapters

- `douyin-session` — Douyin; this adapter's architecture source
- `youtube-data-api` (pending) — YouTube official API, lighter
- `bilibili-stat` (pending) — Bilibili official stat API

If you make content across platforms, **install only the adapters you actually use**.
