---
name: cheat-retro
description: T+N day data collection + retro + write actual-performance observations into rubric-memo.md. This is the feedback stage of the calibration loop — a prediction without a retro is astrology. Triggers: "复盘 [path]" / "retro this" / "T+3d 数据来了" / "抓数据 [path]" / "把这篇复盘了".
argument-hint: <prediction-file> [— window: 3|5|7] [— source: manual|adapter]
allowed-tools: Bash(*), Read, Edit, Write, Glob, Grep, Skill
---

# /cheat-retro — data collection and retro

Fetch T+N day actual performance → compare with the prediction → extract new observations → write them into rubric-memo.md. **Only append the `## Retrospective` section; never change the prediction section**. `rubric_notes.md` is the blind whitelist and may only hold generic formulas, dimension definitions, and abstract rules; it must never contain sample names, actual performance, comments, links, or play/read counts.

## Overview

```
[User: retro predictions/2026-05-04_...]
  ↓
[Phase 0: validate immutability + validate time window]
  ↓
[Phase 1: fetch data (manual paste or adapter)]
  ↓
[Phase 2: write the actual-performance section + top comment keywords]
  ↓
[Phase 3: validate / refute each prediction hypothesis]
  ↓
[Phase 4: extract new observations]
  ↓
[Phase 5: persist (append to the ## Retrospective section)]
  ↓
[Phase 6: write into the "observation log" section of rubric-memo.md]
  ↓
[Phase 7: detect whether a bump candidate is triggered → tell the user to run /cheat-bump]
```

## Constants

- **RETRO_WINDOW_DAYS = 3** — default T+3d. Fast short-video platforms can use 1; long essays can use 7
- **DATA_SOURCE = manual** — manual: the user pastes numbers; adapter: call the matching platform adapter (requires config)
- **AUTO_PROPOSE_BUMP = true** — Claude judges systematic deviation and automatically proposes /cheat-bump
  - **Default reference**: ≥3 consecutive same-direction misses (high/low) → propose
  - **But Claude may propose earlier**: 1 extreme miss (e.g. center 500k, actual 50k, ≥10x) triggers a proposal even without "consecutive"
  - **Or later**: 3 same-direction misses but each is tiny (<25%) may just be noise, not systematic
- **TOP_COMMENTS_N = 20** — fetch / paste the top N most-liked comments

> 💡 Override at call time: `/cheat-retro <file> — window: 7 — source: adapter`

## Inputs

| Required | Source |
|---|---|
| `<prediction-file>` or `<video-folder>` | user argument; if missing, use `pending_retros[0]` from `.cheat-state.json` |
| `rubric_notes.md` | user project root (read-only, for current-rule context; actual-performance observations must not be written into it) |
| `rubric-memo.md` | user project root (write retro observations, actual-performance evidence, sample names, and comment signals) |
| `.cheat-state.json` | state file |

### Argument parsing (accepts both forms, same as cheat-predict)

The user may give:
- **`predictions/2026-05-04_<id>_<short>.md`** → use this prediction file directly
- **`videos/2026-05-04_<id>_<short>/`** → find the matching prediction file (match by id) + write report.md into that video folder
- Empty → take the earliest from `pending_retros[0]`

## Workflow

### Phase 0: Validate

1. Read `<prediction-file>` and confirm it exists
2. **Identify the active prediction section**: scan every `## Prediction...` section (may include `## Prediction`, `## Prediction v1`, `## Prediction v2`, etc.):
   - Take the **last** `## Prediction vN` as the basis for this calibration (use v2 if it exists; otherwise v1; a legacy single `## Prediction` is used directly)
   - The matching `v2_prediction_written` in state.shoots should agree with "whether a v2 section exists" — if not, warn (state and file are out of sync)
3. **Validate immutability**: cache the content of every `## Prediction...` section in memory (for the check after Phase 5 — **all sections are immutable**, not only the active one)
4. Validate that the file header has `Published at` → an unregistered piece cannot be retro'd; tell the user to run `/cheat-publish` first
5. Validate the time window: today - published_at >= RETRO_WINDOW_DAYS. Not enough → say "X more days to go" and ask whether the user still wants to retro (mark `early_retro: true`)
6. Check whether the retrospective section is already filled — if so ask "supplement or correct?"
   - Supplement → append a new sub-section under the existing retrospective, marked with the date
   - Correct the prediction section (a user misconception) → refuse

### Phase 1: Fetch data

Two paths according to the `state.data_collection` field — after fetching, **write the data into the video folder's `report.md`** (if the prediction is linked to a video folder), and also parse a summary inline into the prediction's retrospective section.

#### Path A: `DATA_SOURCE=manual` (fallback)

- Ask the user: "Paste this piece's current data: plays / likes / comments / shares / saves (order does not matter; I can parse it)"
- User pastes → parse and extract the numbers
- **Top comments are mandatory**: ask the user to paste TOP_COMMENTS_N comments from the platform backend or the comment section into the conversation (each with its like count)
  - User refuses / gives fewer than 5 → **refuse to continue**: "Comments are the real signal — a meme explosion like 'she's different' can only be seen in the comments.
    A retro without comments = judging an illness by a thermometer. Paste the top 20. If you truly cannot get them, tell me why (e.g. comments are turned off); I'll mark `comments_unavailable`, but this retro's value is discounted."
- Write the pasted raw data into `videos/<...>/report.md` (if there is a video folder)

#### Path B: `DATA_SOURCE=adapter`

Decide which one to call from the prediction header's `Platform` field + state's `enabled_perf_adapters`:

| Platform | Adapter | How to call |
|---|---|---|
| `douyin` | `adapters/perf-data/douyin-session/` | `bash <adapters-dir>/douyin-session/run.sh <aweme_id> <video_folder>` |
| `xhs` | `adapters/perf-data/xhs-explore/` | `bash <adapters-dir>/xhs-explore/run.sh <note_id> <video_folder>` |
| `linkedin` | `adapters/perf-data/linkedin-session/` | `bash <adapters-dir>/linkedin-session/run.sh <activity_id> <video_folder>` |
| `wechat_channels` | `adapters/perf-data/wechat-channels/` | `bash <adapters-dir>/wechat-channels/run.sh <post_id> <video_folder>` |
| `youtube` | `adapters/perf-data/youtube-data-api/` (planned — batch 3, not yet available) | call the YouTube Data API (requires an API key) |
| `bilibili` | `adapters/perf-data/bilibili-stat/` | `bash <adapters-dir>/bilibili-stat/run.sh <bvid> <video_folder>` |
| other | no adapter | degrade gracefully to Path A |

> `<adapters-dir>` = `cheat-on-content/adapters/perf-data/` at the cloned source location (install.sh does **not** copy adapters into ~/.claude/skills; it only copies the 15 skills). Locate it with: `find ~ -path '*/cheat-on-content/adapters/perf-data' -type d | head -1`.

**douyin-session special handling**:
- Video URL (e.g. `https://v.douyin.com/abc123`) → resolve the short link → extract aweme_id
- Before calling, confirm the cookie file exists (the adapter looks in `.auth/`); if not, tell the user to run `python <adapter>/crawler.py login` first
- The adapter outputs to `<video_folder>/report.md` (the adapter's renderer.py already writes this format)
- cheat-retro reads this report.md, parses the key data → writes a summary into the prediction's retrospective section

**xhs-explore special handling**:
- Note URL (`https://www.xiaohongshu.com/explore/<note_id>?xsec_token=...` or `https://xhslink.com/xxx`) → extract note_id
- Before calling, confirm the cookie exists (the adapter looks in `.auth-xhs/`); if not, tell the user to run `python <adapter>/crawler.py login` first
- Fields are calibrated (views `view_count` etc. are hardcoded); if an API revision makes a field 0, look at the raw galaxy JSON at the end of report.md and add the new key to `_normalize_note` in `crawler.py`
- **Comments may be unavailable** (missing xsec_token / comments disabled) → report.md marks "comments not fetched" → then **degrade to asking the user to paste the top 20 comments manually** (comments are the real signal; they cannot be skipped)

**linkedin-session special handling**:
- Post URL (`https://www.linkedin.com/feed/update/urn:li:activity:<id>/`) or a bare activity_id → the adapter extracts activity_id automatically
- Before calling, confirm the cookie exists (the adapter looks in `.auth-linkedin/`); if not, tell the user to run `python <adapter>/crawler.py login` first
- **Only posts you wrote yourself can be fetched** (LinkedIn single-post analytics is author-only); the LinkedIn UI randomly switches between Japanese/English, and `extract.py`'s `POST_METRICS` already stores bilingual labels; if a field is None, look at `.cheat-cache/linkedin-session-debug/post_<id>.txt` and add the new label
- **Comments give only counts, not text** (analytics page limit) → report.md notes it → **degrade to asking the user to paste top comments manually** (comments are the real signal; they cannot be skipped)

**wechat-channels special handling**:
- Only fetches the Channels assistant backend data visible to the user after their own login; before calling, confirm the content project has `.auth-wechat-channels/`
- If no login state exists, tell the user to run `python <adapter>/review.py login` and scan the QR code; login state is stored only locally in the content project
- The adapter outputs `report.md`, but does not persist raw responses, request bodies, full backend URLs, backend screenshots, page text, commenter nicknames, or internal user IDs
- If the target piece cannot be found or the adapter fails, exit non-zero and degrade to manual; never treat an old report.md as this run's success

**bilibili-stat special handling**:
- Video URL (`https://www.bilibili.com/video/<BV id>` or a b23.tv short link) or a direct BV id → the adapter extracts the BV id automatically
- **No login needed**: Bilibili video stats (view) and comments (reply) are public APIs and need no wbi signing; the adapter is pure httpx, has no `crawler.py login` step, and never touches `.auth/`
- Requires httpx: first run `pip install -r <adapter>/requirements.txt`
- Comments are fetched by popularity (sort=2); Bilibili's old API may return few top-level comments — if too few, degrade to manual paste

**Any adapter failure** (expired cookie / API change / network) → **degrade gracefully to manual**, telling the user: "Adapter call failed, reason [X]. Switching to manual mode — paste the data below". **Do not block the flow**.

#### Common output

Whether Path A or B, in the end:
- `videos/<...>/report.md` contains the full raw data (numbers + top comments)
- The prediction file's retrospective section contains the **summary** (key ratios + comment-keyword clusters + validate/refute judgments)
- report.md is the data truth; the prediction retrospective section is the judgment truth

### Phase 2: Write the actual-performance section + top comment analysis

**Actual-performance data format** (see the retrospective section format in [prediction-anatomy.md](../../shared-references/prediction-anatomy.md)):

```markdown
### Actual performance
- Plays: 711k (landed in the `30-100w` bucket on the high side, **+42%** vs the 500k center)
- Likes: 24k (like/play ratio 3.38%)
- Comments: 899 (comment/play ratio 0.126%)
- Saves: 5,251
- Shares: 18k (share/play ratio 2.53%, strong)
```

The derived ratios between data points (like/play, comment/play, share/play) must be computed — they reveal signals raw play counts cannot.

**Top comment keyword clustering**:
- Split the N pasted comments into 3-5 categories (high-like meme / concept reference / off-topic noise / repost-exposure hint / @friend propagation, etc.)
- List representative comments per category (with like counts)
- Report proportions ("22% meme reuse, 35% concept reference, 5% off-topic")

### Phase 3: Validate / refute

Judge every item in the prediction file (reasoning-factor table, critical calibration hypothesis, counterfactual scenarios) one by one:

```markdown
### Which predictions were validated ✅ / refuted ❌

**Validated ✅**:
- The critical calibration hypothesis held completely: this piece 711k / Who asked you 117k = 6.07x, far above my 1.5-2x bet
- ER=5 drove emotional spread → strong evidence for H1
- HP=5 validated: share/play ratio 2.53% matches "the quotable line was quoted frequently"

**Refuted ❌**:
- The 500k center was exceeded by +42%
- The counterfactual reasoning "must be paired with a strong social issue to break 300k" was completely wrong
- The SR bet ("H2: SR should be raised") was refuted in the opposite direction: SR contributes almost nothing in emotionally driven scenarios
```

**Key discipline**:
- Every validation / refutation must cite specific data ("share/play ratio 2.53%"); vague phrasing such as "basically consistent" is not allowed
- The counterfactual's "what it means if it lands in bucket X" — the bucket it actually lands in directly tells you which rubric hypothesis was tested; state it explicitly

### Phase 4: Extract new observations (**two kinds, written to two files**)

#### 4a. Rubric observations (write to rubric-memo.md)

Observations about scoring dimensions / formula / bucket boundaries:

```markdown
### New observations to write into rubric-memo.md

1. **The true weight of ER in emotionally driven scenarios should be ≥ ×2.0**: the 6x traffic ratio vs Who asked you is the strongest counterfactual evidence for the v2 rubric
2. **Issue-share impulse (TS) is a hidden dimension**: Joker / "she's different" / filter rebuilding provided a safe self-deprecating identity; reposting does not expose one's situation. A TS=5 sample
3. ……
```

Every observation must be traceable to specific data points (do not write "emotion matters" — write "ER5/SR2 vs ER3/SR4 at the same composite differ 6x in traffic").

#### 4b. Writing-pattern observations (write to script_patterns.md)

Diff `scripts/<id>.md` (pre-shoot draft, possibly written by cheat-seed or the user) vs `videos/<id>/script.md` (the actual shooting script — the version the user supplied at cheat-shoot time), and find the parts that **changed and clearly affected traffic**:

| What the user did | Traffic effect | Propose appending a pattern? |
|---|---|---|
| Cut a section | Actual ≥ center → "cutting it did not hurt traffic" — validates that the section was redundant | Yes, add to the "Observed user draft revisions" table in script_patterns.md |
| Added a line / engagement hook | Actual above center → may be a new pattern | Yes, candidate Pattern N, marked ≥1 sample to verify |
| Changed the style (e.g. softened the opening) | Above similar samples → the style change worked | Yes, candidate Pattern N |
| Did not change structure / change unrelated to traffic | — | Do not append |

Output format:

```markdown
### New pattern candidates to write into script_patterns.md

1. **User revision pattern**: cut [section X] / added [Y]
   - Traffic effect: actual [N] vs center [M], [miss / on target]
   - Suggestion: append to the "Observed user draft revisions" table in script_patterns.md

2. **New pattern candidate N**: [one-line description]
   - Single-sample support
   - Trigger condition: [when to use it]
   - Suggestion: append to the "Newly discovered patterns" section at the end of script_patterns.md, marked ≥1 sample to verify
```

Ask the user: "Append these to script_patterns.md? (yes / no / which ones)". **Only append after user confirmation** — avoid writing a single-point observation directly as a formal pattern.

> **Rubric evolution ≠ writing evolution** — the two are decoupled:
> - rubric_notes.md learns "which dimensions really predict traffic"
> - script_patterns.md learns "which writing approaches really work"
> There may be overlap (e.g. the MS dimension and the "engagement hook" pattern), but they are recorded in two files because **their scope differs** — a rubric change affects all future scoring; a pattern change affects all future drafts.

If `videos/<id>/script.md` is **missing** (the user marked `script_lost` at cheat-shoot time) → skip 4b; no diff is possible.
If `script_consistency = "consistent"` (the user did not change the draft when shooting) → 4b is still meaningful (the diff may be empty), but you can skip the detailed review quickly.
If `script_consistency = "modified"` (the user changed it when shooting) → **4b is the core**; focus on learning this change → traffic effect.

### Phase 5: Persist into the ## Retrospective section

Use the Edit tool to **append only** to the existing `## Retrospective` section (delete the placeholder `(To be filled)` line first if present):

```markdown
## Retrospective

**Retro at**: 2026-05-07 (publish T+3d)
**Fetched at**: 2026-05-07 09:30
**Data source**: manual paste

### Actual performance
[Phase 2 content]

### Top comment keywords
[Phase 2 content]

### Which predictions were validated / refuted
[Phase 3 content]

### New observations to write into rubric-memo.md
[Phase 4 content]
```

**Validate once more after writing**: read the saved file and compare the combined hash of **all** `## Prediction...` sections (v1 / v2 / legacy) — it should equal the combined hash cached in Phase 0. **If any section changed → error and roll back**.

### Phase 6: Write into rubric-memo.md + script_patterns.md

#### 6a. rubric-memo.md (Phase 4a output)

Following the blind leak guard in [observation-lifecycle.md](../../shared-references/observation-lifecycle.md), append to the `## Observation log` section of `rubric-memo.md`. Here you may include real sample names, actual-performance data, comment keywords, and links; these contents must **never** go into `rubric_notes.md`:

```markdown
### YYYY-MM-DD [short title] (id) — [one-line assessment]
- Prediction: composite=X.XX, bucket=Y
- Actual: plays / likes / comments / shares (with T+Nd label)
- Top comment keywords: [brief excerpt + like count]
- Judgment: which dimension was validated/refuted? Why?
- Rubric adjustment: [if any, state "next time scoring XX type of article, change YY"]
- See: [predictions/<file>.md]
```

**Detect cross-sample patterns**: scan the existing "Observation log" in `rubric-memo.md` and see whether the new observation forms ≥2-sample support with an existing one. If so, promote it to the "Major cross-video observations" section in `rubric-memo.md`. Only when a later `/cheat-bump` lands should the validated rule be abstracted into generic language and written into `rubric_notes.md`.

#### 6b. script_patterns.md (Phase 4b output, **written only after user confirmation**)

If the user replied "yes" in Phase 4b or selectively confirmed some:
- "User revision pattern" → append to the "Observed user draft revisions" table in script_patterns.md
- "New pattern candidate N" → append to the "Newly discovered patterns" section at the end, **explicitly marked ≥1 sample to verify**

Format for a new pattern candidate (same as the Pattern 11/12 examples in [script_patterns.template.md](../../templates/script_patterns.template.md)):

```markdown
### Pattern N (from [short video name], single sample to verify)

**Phenomenon**: [Phase 4b description]

**Principle**: [why it works — a guess based on this one observation]

**Trigger condition**: [when to use it]

**To verify**: needs ≥2 supporting samples before promotion to a formal pattern.
```

Promoting a cross-sample pattern: scan the "Newly discovered patterns" section for ≥2 samples supporting the same phenomenon → promote to the core pattern library + delete the "to verify" mark.

If the user said no to everything in Phase 4b ("no") → skip 6b; rubric-memo.md is still written.

### Phase 7: Detect bump trigger

Read the `consecutive_directional_errors` field in `.cheat-state.json` and update it according to this retro's direction:
- This prediction overestimated (actual < center -25%) → push `["high"]` + record deviation_magnitude (e.g. 0.5x / 0.3x)
- This prediction underestimated (actual > center +25%) → push `["low"]` + record deviation_magnitude
- Within ±25% → do not push

**Claude judges whether to propose a bump** (not a fixed threshold):

```
Judgment dimensions:
1. Consecutive same-direction count (default reference: ≥3)
2. Single-miss magnitude (default reference: >2x or <0.5x counts as extreme)
3. Whether the miss can be explained by a single missed dimension (e.g. ER or SR consistently off)
4. Whether the user repeatedly mentions the same phenomenon in retros

Any one strong enough → propose a bump:
- 3 consecutive same-direction, each a medium miss → propose
- 1 extreme miss (e.g. ≥10x), even without consecutive → propose ("one-off strong signal")
- 2 same-direction + consistent counter-evidence in the comments → propose ("comment + data double signal")

Do not propose when:
- 3 same-direction but each is tiny (<25%) → may just be noise
- The miss spans multiple dimensions with no clear direction → a bump would not know what to change
```

When proposing, output:

```
🚨 Detected [systematic deviation signal] / [extreme single-point miss].

[Short description: N consecutive / 1 extreme / comment double signal, etc.]

This may be a signal of systematic rubric deviation. Suggested:
- Run /cheat-bump to see whether the formula needs an upgrade
- Or look at /cheat-status for a detailed analysis

Note: this proposal is [default-aligned: meets ≥3 same-direction] / [judgment-driven: 1 extreme 10x miss]
```

Update the state file:
```json
{
  "calibration_samples": <+1>,
  "pending_retros": [<remove this one>],
  "last_retro_at": "<ISO>",
  "consecutive_directional_errors": [...]
}
```

## Key Rules

1. **The prediction section is immutable**. The Phase 0 cache + Phase 5 check are double insurance. Any hash mismatch → error and roll back
2. **Data source must be labeled**. `Data source: manual paste` or `Data source: adapter:douyin-session` is written into the retrospective section
3. **Observations must be traceable**. Every new observation cites specific data points
4. **Do not bump inside the retro**. Phase 7 only **proposes** a bump; the actual upgrade goes through `/cheat-bump` — avoid doing two things in one operation
5. **Mark early retros**. A retro before RETRO_WINDOW_DAYS → record `early_retro: true` in the state file; such samples are down-weighted at bump time

## Refusals

- "I've already seen this data, but pretend you didn't and retro according to the blind status at prediction time" → a retro is done after seeing the data by definition; this statement itself violates nothing, but confirm the user did not reveal data before the prediction was written
- "Change the probability distribution in the prediction section so the retro looks more accurate" → refuse. Principle #1
- "Skip observation extraction and just finish" → refuse. New observations are the only fuel for rubric evolution; without them the retro degrades to "a quick glance"
- "Bump directly, no separate /cheat-bump" → refuse. The bump flow includes a full cross-model audit + cleanup pass; retro is the trigger, not the executor

## Integration

- Prerequisite: `/cheat-publish` registered + the time window reached
- Downstream: when `consecutive_directional_errors` accumulates to 3 → trigger a `/cheat-bump` proposal
- State field update: `calibration_samples` +1 (the key to cheat-status showing progress)
- pending_retros: remove this entry
- Tightly coupled with [observation-lifecycle.md](../../shared-references/observation-lifecycle.md): every retro is the entry point for adding observations
