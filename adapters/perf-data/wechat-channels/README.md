# Adapter: wechat-channels (WeChat Channels assistant)

Used to fetch your own account's post performance data from the WeChat Channels assistant backend.

## How it works

- Playwright with a persistent Chromium login session
- Passively listens for JSON that the `channels.weixin.qq.com/platform/` page sends itself
- Does not reverse-engineer signatures and does not read WeChat client files
- The login session is stored in the content project's `.auth-wechat-channels/`

## Install and log in

```powershell
cd <content-project>
.\.venv\Scripts\python.exe -m pip install -r <adapter>\requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe <adapter>\review.py login
```

After scanning the QR code to log in, verify:

```powershell
.\.venv\Scripts\python.exe <adapter>\review.py list
```

## Fetch a single post

```powershell
.\.venv\Scripts\python.exe <adapter>\review.py post <post_id> [script.txt]
```

At runtime it only processes, in memory, the JSON the page sends itself. The adapter does not write raw responses, request bodies,
full backend URLs, backend page text, or screenshots to disk; diagnostics only print counts and error reasons to the terminal.

## Current limitations

- The first version prioritizes the post list and plays/likes/hearts/comments/shares data.
- It already supports automatically fetching comment text, like counts, and author replies from "Interaction Management → Comments" (互动管理 → 评论).
- By default it sorts by likes and time, and writes at most the Top 20 into the report; when the API paginates, it pages automatically.
- If the given post_id is not in the recent-post list, it exits with a non-zero status, to avoid generating a zero-value report.md that pollutes the retrospective.
- `run.sh` deletes any old `report.md` in the target directory before each fetch; a failed fetch will not misreport a stale report as success.

## TOS / risk boundaries

- Only for WeChat Channels assistant backend data visible after the user logs in themselves.
- Does not scrape other people's posts, does not bypass login, does not reverse-engineer signatures, does not auto-publish content.
- Does not persist raw responses, request bodies, signed media URLs, internal usernames/IDs, cookies, secrets, backend screenshots, or page text.
- `report.md` still contains the user's own operational data and comment text, so it should be kept in a private content project; review and redact before sharing externally.
- Trigger it manually at low frequency, for personal content retrospectives and NotebookLM/cheat-on-content analysis.

## Local verification

```bash
python -m unittest discover -s adapters/perf-data/wechat-channels -p 'test_*.py' -v
bash adapters/perf-data/wechat-channels/test_run_contract.sh
```
