---
name: cheat-publish
description: Register that a piece of content has been published; write the URL / platform ID / publish time into the corresponding prediction file header and the state file. This is a lightweight action — it only updates metadata and **does not change a single character of the prediction section**. Triggers: "已发布" / "I shipped" / "发布链接是 X" / "刚发完 [url]" / "publish registered".
argument-hint: <prediction-file-or-url> [— platform: youtube|bilibili|douyin|...]
allowed-tools: Bash(*), Read, Edit, Glob
---

# /cheat-publish — publish registration

Write the work's publish metadata (URL, publish time, platform) into the prediction file header and the state file. **Changing the prediction section is forbidden** — the hook will block it.

## Overview

```
[User: published https://...]
  ↓
[Phase 0: find the matching prediction file]   ← via in_progress_session or matching
  ↓
[Phase 1: parse the URL → platform / publish time]
  ↓
[Phase 2: update the prediction file header (metadata section only)]
  ↓
[Phase 3: update .cheat-state.json, clear in_progress_session]
```

## Constants

- **AUTO_DETECT_PLATFORM = true** — auto-detect the platform from the URL pattern
- **VERIFY_BLIND = true** — remind the user: from this moment on, seeing any subsequent data will damage the integrity of the blind-status claim

## Inputs

| Required | Source |
|---|---|
| `<prediction-file>` or URL | user argument; if missing, use `in_progress_session.file` from `.cheat-state.json` |
| `.cheat-state.json` | user project root |

## Workflow

### Phase 0: Find the matching prediction file

By priority:
1. The user explicitly gave a prediction file path → use it
2. The user gave only a URL → read `in_progress_session.file` from `.cheat-state.json`
3. Neither → list `predictions/*.md` files whose header has no `published_at` and let the user choose

**Warning path**: if the time gap between `in_progress_session.file` and the URL the user gave exceeds 14 days → prompt "this prediction was written a long time ago; are you sure it is this one?"

### Phase 1: Parse the platform

When `AUTO_DETECT_PLATFORM=true`, by URL pattern:

| URL pattern | Platform |
|---|---|
| `youtube.com/*` `youtu.be/*` | youtube |
| `bilibili.com/*` `b23.tv/*` | bilibili |
| `douyin.com/*` `iesdouyin.com/*` `v.douyin.com/*` | douyin |
| `xiaohongshu.com/*` `xhslink.com/*` | xhs |
| `mp.weixin.qq.com/*` | wechat |
| `substack.com/*` `*.substack.com/*` | substack |
| `medium.com/*` `*.medium.com/*` | medium |
| `twitter.com/*` `x.com/*` | twitter |
| Other | unknown — ask the user |

Publish time:
- Do not insist on auto-fetching — most platforms require a logged-in session
- Ask the user: "When was it published? (default: now)" → accept ISO 8601 or natural language ("today 14:30" / "20 minutes ago")
- Parse failure → use now()

### Phase 2: Update the prediction file header

**Never** touch the `## Prediction` section (legacy `## 预测`) or anything after it. Only modify the metadata block at the very top of the file.

Read the file and locate the metadata block (all lines before the first `##`). Check whether these fields already exist — if so, warn "already registered" and ask whether to overwrite; if not, append:

```markdown
**Published at**: 2026-05-04T14:32:00+08:00
**Platform**: douyin
**URL**: https://v.douyin.com/abc123
**Video Folder**: videos/2026-05-04_a3f2c1d4_stop-expecting/
**Aweme ID**: 7234567890123456789  (platform-specific ID needed by douyin / WeChat Channels etc.)
```

**About platform-specific IDs**:
- Douyin: resolve the short link and extract `aweme_id` (v.douyin.com → after redirect contains a modal_id or item_id parameter)
- Bilibili: BV id
- Xiaohongshu: note_id
- YouTube: video_id after the v= parameter

If the user gives a share short link (cannot be resolved immediately) → mark `Aweme ID: pending` and let the adapter resolve it at the next `/cheat-retro`.

**Video folder handling**: by the time it reaches cheat-publish, the matching `videos/<id>/` directory **should already have been created by cheat-shoot** (including script.md).

- If the video folder does not exist → warn "did you skip cheat-shoot? Suggest running cheat-shoot to register the shooting script in the video folder before publishing", and **ask the user whether to skip registration and publish directly**:
  - Yes → auto-create a video folder (fallback), but do not ask about script consistency, and mark `ad_hoc_publish: true`
  - No → have the user run cheat-shoot first, then come back to publish

Use the Edit tool (not Write to rewrite the whole file).

**Expected hook behavior**: because only the metadata section is touched (before `## Prediction`), the immutability hook should let it through. If the hook falsely blocks → report a bug; **do not bypass the hook**.

### Phase 3: Update the state file

```json
{
  "in_progress_session": null,
  "last_published_at": "<ISO timestamp>",
  "last_published_file": "predictions/<filename>",
  "last_published_video_folder": "videos/<...>/",
  "last_published_platform_id": "<aweme_id or BV id etc.>",
  "pending_retros": [
    "predictions/<filename>"
  ],
  "shoots": [
    // remove the item whose video_folder matches this publish; buffer -1
  ]
}
```

**`shoots` queue handling** (key to buffer tracking):
1. Read state.shoots[]
2. Find the item with `video_folder == this publish's video_folder` → remove it
3. If not found → warn "this video is not in the buffer queue. Did you publish directly without /cheat-shoot?" — do not block, but tell the user to use /cheat-shoot next time so buffer tracking stays accurate

`last_published_platform_id` is the input cheat-retro uses when calling an adapter — e.g. douyin-session needs aweme_id to fetch data directly.

`pending_retros` is the pending-retro list — `cheat-status` uses it + RETRO_WINDOW_DAYS to show "what to retro today".

### Phase 4: Reminder + next steps + buffer status

```
✅ Registration complete: predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md
   - Published at: 2026-05-04 14:32
   - Platform: douyin
   - URL: https://v.douyin.com/abc123

📦 Buffer: N pieces (color + meaning)
   At your cadence (X) = N×X days of buffer
   [if the color changed, prompt "time to shoot / pause shooting now"]

⚠️  From this moment on, any play/like/comment data you see about this work
    will damage the integrity of the blind-status claim. If you see it accidentally,
    tell me — I will append an integrity warning to the file.

📅 Planned retro: T+3d, around 2026-05-07
   When the time comes, say: "retro predictions/2026-05-04_..."
```

The buffer color is derived per [shared-references/cadence-protocol.md](../../shared-references/cadence-protocol.md). If this publish drops the buffer into red (gap risk) → highlight the warning "you must shoot ≥1 more today".

## Key Rules

1. **Do not touch the prediction section**. Even to fix a typo, editing the prediction section during publish is not allowed
2. **Do not fetch data**. publish is a registration action, not data collection (that is cheat-retro's job)
3. **State field names are fixed**. `pending_retros` / `last_published_at` are contracts other sub-skills (especially cheat-status / cheat-retro) depend on
4. **Do not force-report an unknown platform**. If it cannot be identified → ask the user; `platform: other` is allowed as a fallback
5. **Duplicate registration must be explicit**. If `published_at` already exists → ask "overwrite?"; never silently overwrite

## Refusals

- "Let me also tweak the prediction section while I'm here" → refuse. Use the `_redo.md` path
- "I'll add the URL later; just record the publish time now" → allowed: the URL field can be appended later; published_at + platform are required
- "Skip the metadata update and just clear in_progress_session" → refuse. Metadata is key context during retro (especially the platform, which decides which adapter to use for data collection)

## Integration

- Upstream: `/cheat-predict` (writes the prediction file and sets in_progress_session)
- Downstream: T+RETRO_WINDOW_DAYS later → `/cheat-retro`
- `cheat-status` uses the `pending_retros` field to compute "what to retro today"
- The platform field is used by `cheat-retro` to route to the matching perf-data adapter (manual-paste / youtube-data-api / etc.)
