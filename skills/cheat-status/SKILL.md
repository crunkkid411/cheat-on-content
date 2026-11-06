---
name: cheat-status
description: The cheat-on-content status dashboard. Shows the current mode / rubric version / calibration progress / pending retros / pool status / whether to upgrade to SQLite / whether to bump the rubric. **Callable at any time, no side effects**. Triggers: "状态" / "看板" / "status" / "我现在该做什么" / "进度怎么样".
allowed-tools: Bash(*), Read, Glob, Grep
---

# /cheat-status — status dashboard

Read the state file + scan the user's project → summarize current progress → output a "what to do today" list.

## Overview

```
[User: status]
  ↓
[Phase 1: read .cheat-state.json + scan the filesystem]
  ↓
[Phase 2: compute derived metrics]
  ↓
[Phase 3: detect recommendation triggers (upgrade / bump / cleanup)]
  ↓
[Phase 4: output the dashboard]
```

## Constants

- **SQLITE_UPGRADE_THRESHOLD = 30** — suggest upgrading to SQLite when calibration_samples reaches N
- **CLEANUP_LINE_THRESHOLD = 600** — suggest cleanup when rubric_notes.md exceeds N lines
- **STALE_PREDICTION_DAYS = 30** — prompt cleanup when an in_progress prediction has been unpublished for N days

## Inputs

| Source | Purpose |
|---|---|
| `.cheat-state.json` | Main state |
| `predictions/*.md` | Calibration sample count / pending retros |
| `candidates.md` | Candidate-pool size |
| `rubric_notes.md` | Line count / current version |
| `.cheat-cache/usage.jsonl` (if any) | meta-logging data, for "how many predictions since the last bump" |

## Workflow

### Phase 1: Read state

```python
state = read_json('.cheat-state.json')
if not state:
    return "You have not initialized yet. Run /cheat-init first."

predictions = glob('predictions/*.md')
candidates_count = parse_candidates_md_entries()
rubric_lines = wc -l rubric_notes.md
```

### Phase 2: Derived metrics

| Metric | Algorithm |
|---|---|
| **Buffer count** | `len(state.shoots)` |
| **Buffer color** | Derived per [cadence-protocol.md](../../shared-references/cadence-protocol.md): `buffer_days = buffer_count × target_publish_cadence_days`, `<1 red / 1-2 orange / 3-5 green / >5 blue`. If `target_publish_cadence_days=null` → color disabled |
| **Confidence level** | Derived per the [state-management.md confidence table](../../shared-references/state-management.md): emoji + label from the `calibration_samples` integer |
| **Days since the earliest shoot** | `now - state.shoots[0].shot_at`, used to warn "shot N days ago and not published" |
| Calibration sample count | Number of prediction files with a complete retrospective section (non-empty actual-performance data) |
| Pending retros | Entries in state.pending_retros past RETRO_WINDOW_DAYS |
| Pool size | Number of entries in candidates.md with tier!=skip |
| Predictions since the last bump | Number of predictions with published_at > state.last_bump_at |
| Same-direction error queue | state.consecutive_directional_errors |
| in_progress staleness | now - state.in_progress_session.started_at (if any) |

### Phase 3: Detect recommendation triggers

Check each item in priority order (high→low):

1. **Buffer color = 🔴 Red** → first line, high-priority alert: "buffer is at 0/1 pieces; the next publish day may have a gap — you must shoot ≥1 today. Say 'recommend topics' and I'll recommend only the top 1 stable pick (no experimental)"
2. **Buffer color = 🔵 Blue** → high-priority note: "buffer already has N pieces backed up. **Pause shooting**; publish inventory + retro first. Say 'published ...' and I'll dequeue it"
3. **Earliest shot_at in state.shoots > 14 days ago** → "you have a video shot N days ago and still unpublished — the topic's timeliness is decaying; publish it soon or drop it"
4. **in_progress stale** (>= STALE_PREDICTION_DAYS) → high-priority note "clean up or publish"
5. **Pending retros ≥ 1** → high priority "retro X pieces today"
6. **`pool_status=none` + `calibration_samples=0` + >24h since init** → "🌱 it has been N days since init and you still haven't shot — is it because you have no topic? Run /cheat-seed for 5 minutes to get 5 candidates + 5 drafts" high priority
7. **Claude judges a systematic deviation signal** (**not a rigid ≥3 same-direction rule**) → suggest "run /cheat-bump"
   - **Default reference**: ≥3 consecutive same-direction misses
   - **But Claude may act earlier**: 1 extreme miss (≥10x) or 2 same-direction + strong counter-evidence in the comments
   - **Or later**: 3 same-direction but each tiny (<25%) (may just be noise)
   - When prompting, label explicitly: "this is [default-aligned] / [judgment-driven]"
8. **calibration_samples crosses into a new confidence level** (0→1, 2→3, 5→6, 10→11, 20→21) → "🎉 confidence upgraded: <old level> → <new level>. Bucket-center precision goes from ±X% to ±Y%". **Notification only; no user action required** — every skill already adjusts automatically based on calibration_samples
9. **calibration_samples crosses 5** → "your rubric shape can have its first formal bump. Review rubric_notes.md and see whether the observation log has a pattern supported by ≥3 samples → run /cheat-bump"
10. **calibration_samples crosses 10** → "you can run /cheat-bump --bucket-only --scheme percentile to switch bucket boundaries to percentile (always self-consistent)"
11. **calibration_samples crosses SQLITE_UPGRADE_THRESHOLD** and data_layer=markdown → "suggest running tools/md-to-sqlite.py" (planned — batch 3, not yet available)
12. **rubric_notes.md line count > CLEANUP_LINE_THRESHOLD** → "suggest cleaning up the observation section (manually or triggered by the next bump)"
13. **calibration_samples ≥ 5 + pool_status=none** → "you can start building a topic pool"
14. **calibration_samples ≥ 15 + pool_status=none** → "strongly recommend building a pool: /cheat-trends or manually create candidates.md"
15. **state.hooks_installed=false** → "your immutability is a gentleman's agreement; suggest running /cheat-init to install the hooks"
16. **state.last_bump_self_audited=true** → "the last bump was self-audited. Suggest configuring mcp__llm-chat__chat and using an external audit for the next bump"
17. **state.rubric_form_mismatch=true** → "your content_form is not opinion-video, but you are using the built-in opinion rubric. The first few predictions will be less accurate; at the next bump, adjust the weights for your form"
18. **state.benchmark_status=pending** → "🎯 at init you said you would find a benchmark account later, but you haven't. Run /cheat-learn-from to import ≥3 benchmark videos and the tool will have anchors"
19. **state.benchmark_status=imported + Claude judges the user's data signal has overtaken the benchmark** → "📊 your real data has become the main signal; the benchmark's influence is fading"
   - **Default reference**: calibration_samples ≥ 10
   - **But Claude may act earlier**: N=5 but the user's (score, actual performance) pairs include ≥3 that diverge from the benchmark patterns — meaning your account has already left the benchmark's path
   - **Or later**: N=15 but the user's samples are all similar with insufficient diversity → the benchmark still has signal value
   - The prompt is a **notification, not a gate** — benchmark.md is always kept as a sanity check, and cheat-seed can still read it

### Phase 4: Output the dashboard

```
🎛️ cheat-on-content status (updated 2026-05-04 15:00)

Content form: opinion-video / duration 3-5min / cadence: every other day
Current rubric: v2 (last bump: 2026-04-22)
Calibration samples: 18
Confidence: 🟢 Fairly high (center ±15%, rubric shape stable)
Baseline: 42k median

📦 Buffer: 3 pieces (🟢 Green)
   At your cadence (every other day) = 6 days of buffer; the rhythm is stable

📊 Progress bars
  [█████████████░░░░░] 18 / 30 → SQLite upgrade threshold
  [██████████░░░░░░░░] 18 / 10 → percentile buckets available (threshold exceeded)

🎬 To do (by urgency)
  🚨 Retro 1 piece (past T+3d)
     - predictions/2026-05-01_db063817_youre-not-in-the-relationship-anymore.md (T+3d reached)
  ⚠️  3 same-direction misses (high, high, high) → suggest /cheat-bump
  💤 in-progress prediction stale for 35 days
     - predictions/2026-04-01_xxx.md → published but forgotten, or dropped?

🔥 Candidate pool
  - candidates.md: 27 entries (tier1: 12, tier2: 9, tier3: 6)
  - 4 days since the last trend fetch — you can run /cheat-trends again

📈 Health
  - rubric_notes.md: 412 lines (healthy, <600 warning line)
  - hooks_installed: ✅
  - external audit configured: ❌ → suggest configuring mcp__llm-chat__chat

Next suggested steps (by recommended priority):
1. /cheat-retro predictions/2026-05-01_db063817_youre-not-in-the-relationship-anymore.md  ← most urgent
2. /cheat-bump  ← handle the 3 same-direction misses
3. Handle the stale in-progress (manually or reply "clean up in-progress")

The full command list is in the main SKILL.md.
```

Output style: **direct, concrete, clickable**. Every suggestion carries the exact command — the user should be able to copy-paste and run it.

## Key Rules

1. **No side effects**. Read many, write zero. Any state modification is another skill's job
2. **Do not pretend data is available**. If a state file field is missing → explicitly mark "unknown"; do not guess
3. **Suggestions carry priority**. Ten suggestions at once numb the user — rank by urgency
4. **Every suggestion carries a command**. Do not just say "time to bump" — give the exact entry point `/cheat-bump --propose "..."`

## Refusals

- "Also run a retro for me automatically" → refuse. status is read-only; retro is a separate action (avoid doing two things in one operation)
- "I don't want to see the rubric_notes line count; too trivial" → output still includes it but collapsed into the bottom "health" area — the presence of status information makes problems visible before they bite

## Integration

- Upstream: every other skill updates .cheat-state.json when it finishes; status is the visualization of those updates
- Downstream: every suggestion routes to a specific sub-skill
- meta-logging hook (if enabled) → writes usage.jsonl, which status uses to compute "how many since the last X"
