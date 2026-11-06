# bilibili-stat — Bilibili perf-data adapter

Collects play data + top comments for **your own (or any) Bilibili video**, for `/cheat-retro` retrospectives.

Called by `/cheat-retro` when `state.data_collection=adapter` and `Platform: bilibili`.

## Why it is simpler than the Douyin / Xiaohongshu adapters

Bilibili's video statistics (`view`) and comments (`reply`) are both **public APIs**:

- No login needed (no `crawler.py login` step, no `.auth/`)
- No wbi signature needed (the `view` API needs no signature; comments use the older `x/v2/reply` API with `sort=2` by popularity)
- No browser needed (pure `httpx`, no playwright)

So **clone it and install `httpx` and it works**, with zero configuration.

## Installation

```bash
pip install -r requirements.txt
```

(If your content project root has a `.venv`, run.sh prefers it; otherwise it uses the system `python3`/`python`.)

## Usage

`/cheat-retro` calls it automatically per the contract below; you generally do not need to run it by hand:

```bash
bash run.sh <bvid_or_url> <video_folder> [<script_path>]
```

- `<bvid_or_url>`: `BV1cUoUY9Ecr`, or any link containing a BV number (e.g. `https://www.bilibili.com/video/BV1cUoUY9Ecr`)
- `<video_folder>`: output directory; `report.md` is written here
- `<script_path>`: optional original script, merged into report.md for the retrospective diff

You can also call the lower level directly:

```bash
python review.py video BV1cUoUY9Ecr           # fetch data → write videos/<auto>/report.md
python review.py login                        # Bilibili needs no login; just prints an explanation (API consistency)
```

## Output (report.md)

Same format as douyin-session, containing:

- Video metadata (title / uploader / publish time / duration / link)
- **Play data**: plays, likes, coins, saves, shares, comments, danmaku, plus derived ratios (like-to-play / coin rate / save rate / share-to-play) — Bilibili's "triple-combo rate" is especially indicative of hardcore approval
- The original script (if provided)
- **Top comments** (sorted by likes descending, with IP location)

## APIs

| Data | API |
|---|---|
| Video statistics | `GET https://api.bilibili.com/x/web-interface/view?bvid=<BV number>` |
| Comments | `GET https://api.bilibili.com/x/v2/reply?type=1&oid=<aid>&sort=2&pn=&ps=20` |

`oid` comes from the `aid` returned by the view API. Comments page by popularity (`sort=2`), taking the top 50 by default.

## Exit codes

`0` success · `2` missing dependency (httpx not installed) · `3` other failure (network / parsing / wrong BV number). On any failure, `/cheat-retro` degrades gracefully to manual mode.

## Maintaining fields across API redesigns

The `stat` field names of `view` (view/like/coin/favorite/share/reply/danmaku) and the comment fields `replies[].{like,content.message,member.uname,rcount,reply_control.location}` are calibrated against real 2026-06 responses. If a Bilibili redesign makes a field 0, adjust the keys in `fetch_video` / `_normalize_comment` in `crawler.py`.
