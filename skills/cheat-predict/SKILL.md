---
name: cheat-predict
description: Write an immutable blind-prediction log for the final draft. This is the core action of the entire cheat-on-content calibration loop — once the prediction section is written it cannot be changed, enforced by the hook. **Auto-detection**: if the target file already has a `## Prediction` / `## Prediction v1` section (called by cheat-shoot in v2 mode), append `## Prediction v2` instead of overwriting. **Scoring is delegated to the `cheat-score-blind` sub-agent via the Task tool** (context-isolated channel B); the main Claude reviews and then persists. Triggers: "启动预测" / "start prediction" / "给这稿子打分并预测" / "写预测日志".
argument-hint: <script-path> [— mode: v1|v2] [— prediction-file: <path>] [— skip-blind]
allowed-tools: Bash(*), Read, Write, Edit, Glob, Task
---

# /cheat-predict — AI-led blind prediction + user review

**This tool is a "cheat device" — the AI makes the judgment for you**. So the core of cheat-predict is:
- **Claude itself** reads the draft + scores the 7 dimensions + gives the bucket + probability distribution + counterfactual scenarios
- The user **reviews** and replies "ok" to accept, or points out which dimension / judgment is wrong
- Default fast path: user says ok → persist
- Slow path: user challenges a dimension → Claude revises → review again → until confirmed

It is not the user writing everything from the 7 dimension scores to the probability distribution — that would leave Claude as only a "formatter", losing the tool's core value.

**Strictly follow [shared-references/blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md)** — if you have seen any subsequent data you cannot write a prediction, only a reconstructed one.
Full component checklist: [shared-references/prediction-anatomy.md](../../shared-references/prediction-anatomy.md).
Confidence derivation table: [shared-references/state-management.md](../../shared-references/state-management.md).

## Overview

```
[User: start prediction scripts/<id>.md]
  ↓
[Phase 0: blind check self-audit]                    ← refuse if violated
  ↓
[Phase 0.7: mode decision — v1 (new) or v2 (append)]
  ↓
[Phase 1: read script + rubric + state + derive confidence]
  ↓
[Phase 2: **delegate to the cheat-score-blind sub-agent** (Task tool) for N-dimensional blind scoring + per-dim confidence]
  ↓
[Phase 2.5: main Claude reviews the blind output — if any dimension |delta| ≥ 2 vs the self-estimate, ask the user to arbitrate]
  ↓
[Phase 3: **Claude itself** finds anchors and compares]
  ↓
[Phase 4: **Claude itself** gives bucket + probability distribution + center]   ← flatter distribution when confidence is low
  ↓
[Phase 5: **Claude itself** writes counterfactual scenarios + critical calibration hypothesis]
  ↓
[Phase 5.5: **user review** — show the complete draft, wait for "ok" or challenges]
  ↓
   ├─ "ok" → Phase 6 persist
   └─ "dimension X should be Y not Z" → Claude revises → review again → loop
  ↓
[Phase 6: persist — v1 writes a new file / v2 appends before the existing ## Retrospective]
  ↓
[Phase 7: update state.in_progress_session]
```

## Constants

- **SCRIPTS_DIR = scripts/** — draft source directory
- **PREDICTION_DIR = predictions/** — persist directory
- **BLIND_CHECK = strict** — strict (default) / lenient (warn only, not recommended) — relates to the "have seen data" boundary in [blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md)
- **BLIND_SCORING = on** (default) / off — whether to use the [cheat-score-blind](../cheat-score-blind/SKILL.md) sub-agent. off is equivalent to the `--skip-blind` flag, marking `last_prediction_self_scored: true` to trigger a cheat-status warning
- **DISAGREEMENT_THRESHOLD = 2** — single-dimension difference between blind and the main Claude's self-estimate |Δ| ≥ this value → Phase 2.5 asks the user to arbitrate
- **BUCKET_PRESET = auto** — derived automatically: with baseline_plays → baseline × {0.3 / 1 / 3 / 10 / 30}; without baseline → platform-generic defaults
- **MIN_ANCHORS = 2** — anchor comparison expects 2; when there are not enough, explicitly write an "anchors N/A" section (do not delete the section, do not omit it)

> 💡 Override at call time: `/cheat-predict scripts/<id>.md — BLIND_CHECK: lenient` / `--skip-blind` (both not recommended)

## Inputs

| Required | Source |
|---|---|
| `<video-folder-path>` or `<script-path>` | user argument; ask if missing |
| `rubric_notes.md` | user project root |
| `.cheat-state.json` | state file |
| `predictions/*.md` (optional) | historical predictions, used as anchors |

### Argument parsing (Phase 0.5, before blind check)

The path the user gives **should** be `scripts/<date>_<id>_<short>.md`. If it is not under scripts/:

| Form | Handling |
|---|---|
| `scripts/<date>_<id>_<short>.md` | standard path, use directly |
| `<id>` or `<short>` shorthand | glob `scripts/*_<id>_*.md` or `scripts/*<short>*.md` to find matches |
| Any external .md file (e.g. `~/Desktop/my-draft.md`) | **warn + ask**: "It is recommended to put the draft at scripts/<date>_<id>_<short>.md so cheat-on-content can manage it. Want me to cp it over and compute the id?" If the user agrees → build the standard path and continue |
| `videos/<id>/` path (the user mistakenly thinks the video folder holds the script) | say "the video folder is created only after shooting — pre-shoot drafts live in scripts/. Which draft do you want to predict?" |

If scripts/<id>.md does not exist → error and ask "where is the draft you want to predict?"

## Workflow

### Phase 0: Blind check self-audit (**most critical**; stop immediately if violated)

Follow the "checklist every sub-skill must run" in [blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md):

1. Ask the user for the piece's current publishing status:
   - Not published → pass
   - Published < `RETRO_WINDOW_DAYS` days ago → ask "have you seen any subsequent data (plays / likes / comments)?"
     - User answers "no" → pass, mark `published_before_prediction: true` + `blind_status: confirmed_no_data_seen`
     - User answers vaguely → treat as "seen", handle under the next item
   - Published ≥ `RETRO_WINDOW_DAYS` days ago → **immediately refuse to write a "prediction"**; recommend the `_redo.md` path to record a reconstructed retrospective

2. Self-audit the conversation history for actual numbers alongside words such as plays / reads / likes / comments / shares → if found, treat as having seen data and handle under strict mode above

3. `BLIND_CHECK=lenient` mode: warn only + force-mark the file header `**Reconstructed retrospective — NOT a blind prediction**`, but still allow continuing

Pass → go to Phase 0.7.

### Phase 0.7: Mode decision (v1 vs v2)

Decide whether this is a new prediction (v1) or a v2 append to an existing prediction (the post-shoot script-revision scenario).

**Explicit parameters take priority**: the user/caller passes `— mode: v2` + `— prediction-file: <path>` → go directly to v2 mode.

**Auto-detection** (no explicit parameters):
1. Infer the target prediction path: `predictions/<same naming as scripts/<id>>.md`
2. Read that path:
   - Does not exist → **v1 mode**, go to Phase 1
   - Exists but only an empty `## Retrospective` (no `## Prediction...` section) → **v1 mode** (abnormal state; warn about overwrite + go to Phase 1)
   - Exists and contains `## Prediction` or `## Prediction v1` → **v2 mode**

**Extra actions in v2 mode**:
- Compare the input script (the final shooting draft) with the original `Script Hash` referenced in the `## Prediction` section
- If completely identical (same hash) → warn "the draft did not change; do you really want a v2?" — continue only after user confirmation; otherwise exit
- If different → compute a diff summary (lines / words / structural changes) → show it to the user during the Phase 5.5 review
- Mark `prediction_basis = "post_shoot_pre_publish"` (v1 defaults to `pre_shoot`)

### Phase 1: Read the final draft + rubric + state + derive confidence

1. Read the full text of `scripts/<id>.md` at the path resolved in Phase 0.5
2. Compute `script_hash` = sha256(script content)[:12] → for the header
3. Read `rubric_notes.md`, identify the current formula + dimensions (same as cheat-score Phase 2)
4. Read `.cheat-state.json` for `rubric_version`, `content_form`, `calibration_samples`, `typical_duration_seconds`, `baseline_plays`
5. **Derive the confidence level from `calibration_samples`** (per the [state-management.md confidence table](../../shared-references/state-management.md)) → write it into the prediction header later
6. Ask the user: "Is this the final draft you plan to actually shoot and publish, or will you revise it again?" — it must be the final draft
7. If the draft's word count badly mismatches the range derived from `typical_duration_seconds` (>50% off) → tell the user: "This draft is N words; given your typical duration (X minutes) it should be M-K words. Did you intentionally change the duration, or does the draft need cutting / padding?"

### Phase 2: Delegate to the cheat-score-blind sub-agent for blind scoring

**BLIND_SCORING=on** (default) — the main Claude no longer scores inline. Spawn `cheat-score-blind` via the Task tool so a context-isolated sub-agent sees only the script + rubric_notes.md and returns N-dimensional scores.

See the "main Claude call contract" section of [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md). **The task prompt must be minimal**:

```
Spawn cheat-score-blind sub-agent.

Input:
  script_path: <the scripts/<id>.md resolved in Phase 0.5>
  rubric_notes_path: rubric_notes.md

Task: score the above script according to the current formula in rubric_notes. Return strict JSON (see the cheat-score-blind SKILL.md Phase 2 schema).
Do not read the state file / predictions/ / videos/ or any other file.
Do not ask the user anything — you have no user.
```

**Self-audit before calling**: grep the task prompt with `grep -Ei '播放|阅读|点赞|评论数|实际|retro|复盘|实绩|w$|万$'` — if it hits, rewrite the prompt and resend.

**The main Claude also makes its own internal estimate** (not sent to the sub-agent) — purely for Phase 2.5 disagreement detection; **not persisted**, **does not replace the sub-agent output**. This estimate represents "what I would have scored without the sub-agent" and is an objective measure of contamination.

**Sandbox escape**: `BLIND_SCORING=off` or `--skip-blind` — the main Claude scores the 7 dimensions itself. State immediately marks `last_prediction_self_scored: true` + `last_self_scored_at: <ISO>`, and cheat-status keeps warning. Only for:
- Task tool unavailable (dev environment / offline)
- The user actively wants to audit the main Claude's inline scoring ability (very rare)

Compute the composite with the current formula — **using the dimension scores returned by the sub-agent**, not the main Claude's self-estimate.

### Phase 2.5: Blind output review + disagreement detection

After receiving the sub-agent JSON, the main Claude must:

1. **JSON validity check**: `python3 -c "import json; json.loads(...)"` should parse it; if not → resend the Task (up to 3 retries); still failing → abort and report to the user
2. **Contamination check**: `self_check.any_contamination_signal == true` → warn the user "the sub-agent self-reports possible contamination", but still accept the score (drop confidence one level)
3. **Refusal check**: `refusal != null` → follow the corresponding path in the handling table in [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md) Phase 2
4. **Disagreement detection** (core):
   - The main Claude internally estimates N dimension scores (the "self-estimate" at the end of Phase 2)
   - Compute `delta = |self-estimate - blind|` for every dimension
   - Any dimension with `delta >= DISAGREEMENT_THRESHOLD` (default 2) → **ask the user to arbitrate**

Arbitration UX:

```
⚠️  The blind sub-agent differs significantly from the main Claude on some dimensions:

| Dimension | blind (sub) | Main Claude self-estimate | delta | Sub-agent reason |
|---|---|---|---|---|
| ER | 5 | 3 | 2 | "PPT cheering-cat opening — concrete, strong visual" |
| AB | 2 | 4 | 2 | "one-person-company angle, narrow audience" |

Who is more accurate?
  a) Trust the sub-agent (isolated scoring, but same Claude model)
  b) Trust the main Claude self-estimate (more conversational context, possibly contaminated)
  c) I'll decide myself (you give the scores)

Reply a / b / c <your scores>
```

User choice:
- a → use the sub-agent's full score set in Phase 3
- b → use the main Claude's full self-estimate (treated as deliberately accepting contamination) → force `last_prediction_self_scored: true`
- c → the user's score overrides that dimension; other dimensions still use the sub-agent → record in `User Override`

**All deltas** — even if all < THRESHOLD — are recorded in the prediction header's `BlindScore Disagreement` field (see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 1). Record delta=0 too.

### Phase 3: Anchor comparison

**Run this phase at every stage** — when there are not enough anchors, explicitly mark N/A; do not delete the section.

1. Glob `predictions/*.md`, read each file's header (extract composite, actual-performance bucket, duration_seconds). **Be careful to exclude reconstructed predictions** (anything marked "Reconstructed" is not an anchor)
2. **Prefer** samples with the same duration (`Target Duration (s)` within ±20% of this one)
3. In the same-duration (or all) pool, find 2-4 samples whose composite is within ±0.5 of this prediction
4. **If the pool is too small** (same duration < 2 + all < 2) → output the "anchor comparison N/A section" (see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 5) — still write this section, telling the reader why anchors are missing
5. List the comparison table; if crossing durations, add an extra "duration vs this one" column per row
6. **Critical diagnosis**: if an anchor has almost the same composite but ≥3x difference in actual performance → the rubric is missing a key dimension. **Explicitly flag it in the file** as a seed for a new observation

> Why filter anchors by duration: 4-minute video at 50k plays vs 1-minute video at 50k plays are completely different things — a long video carries more attention loss per second. Cross-duration anchors easily lead to false conclusions.

### Phase 4: Bucket + probability distribution + center

**Write it at every stage** — when confidence is low the distribution is **flatter**, not omitted.

1. Read the default bucket boundaries from `starter-rubrics/<content_form>.md` (unless the user customized them in rubric_notes.md)
2. Choose the most likely bucket (headline call)
3. **Must** give the probability distribution over all buckets — summing to 100%
4. **Must** give a "center" point estimate inside that bucket

**Anti-honesty trap**: if you give a bucket 95% probability, then when the next prediction is wrong you cannot say "I wasn't really sure". **A real probability distribution usually puts 40-65% on the headline bucket**, with the remaining ≥35% spread across neighboring buckets.

### Phase 5: Counterfactual scenarios + critical calibration hypothesis

**Write it at every stage** — when the calibration pool is small the critical calibration hypothesis may have no suitable comparison sample; then write "no comparable samples — but I will still write down my core bet for this one" + 1-2 things you want to test this time.

**Counterfactual scenarios** (4 sections, each corresponding to a possible bucket; write "if it lands here, which rubric hypothesis is validated / refuted"): see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 6.

**Critical calibration hypothesis** (strongly recommended):
- Find a comparison sample (preferably the previous prediction)
- Explicitly write "I bet this piece vs the comparison = X times"
- Write "if the opposite happens / the gap is < N → which rubric hypothesis is refuted"

If `REQUIRE_HYPOTHESIS=required` → not allowed to persist without it.

### Phase 5.5: User review (**core — decides what goes into the file**)

After Phases 2-5 are all done in memory, **show the complete draft to the user in one go**:

```
My prediction draft (review before writing the file):

📊 7 dimension scores (v0 / v2 / whatever the current rubric is):
| Dimension | Score | Reason |
|---|---|---|
| ER | 5 | "PPT cheering cat + boss sees it + brain goes blank" — emotionally heavy |
| HP | 5 | Opening "page 7 of the PPT, center of the big screen: a cheering cat" — concrete, strong contrast |
| QL | 5 | "the cheering cat saved my life" — two quotable lines |
| NA | 4 | single timeline + reflection, clear but not complex |
| AB | 4 | one-person-company topic, but AI anxiety is universal |
| SR | 3 | AI anxiety is an issue but not a hot confrontation |
| SAT | 2 | empathetic tone, almost no satire |
→ composite ≈ 8.00

🎯 Betting bucket: 30-100w, center ~60w
   Probability distribution: <5w 5% / 5-30w 22% / **30-100w 50%** / 100-150w 18% / >150w 5%
   confidence: 🟢 Medium (based on 8 calibration samples, center ±25%)

🔍 Anchor comparison:
| Comparison | composite | Actual | Similarities / differences |
|---|---|---|---|
| ... | ... | ... | ... |

🤔 Counterfactuals:
   If >100w → validates and strengthens the ER-dominance hypothesis
   If 30-100w → baseline is OK
   If <30w → refutes "AI anxiety is universal"; AB was optimistic

🎲 Critical calibration hypothesis: this piece vs [comparison] bet 1.5x

——————————————————————————————

Reply "ok" and I'll persist it directly,
or point out which dimensions / judgments are wrong (e.g. "AB should be 3, too optimistic" / "the center should be 30w not 60w").
```

Three possible user responses:

1. **"ok"** / "fine" / "continue" → go directly to Phase 6 persist, header marked `Scored By: claude`
2. **"X is wrong, should be Y"** → Claude revises the corresponding field (not just the value — update the composite + probability distribution and other knock-on effects), shows it again → loop back to Phase 5.5
3. **"redo everything"** → rerun Phases 2-5 (rare; usually means Claude badly misread the draft's tone)

**Fields the user challenged** are recorded in the prediction header's `User Override` section (written in Phase 6):
- Which dimension / which number was overridden
- The AI's original value vs the user's revised value

During retro this field helps diagnose:
- The user says ok every time (consistent with Claude) → no user-bias contamination
- The user often overrides a particular dimension → Claude systematically diverges from the user's actual feel on that dimension
- The overridden dimension is validated by actual performance → the user's intuition is accurate → the rubric may be missing something

**Discipline for user challenges**:
- The user **may only change field values**; they cannot insert new reasoning during the review phase to make Claude rewrite a whole section — that turns Claude into a ghostwriter
- After a change, if the composite / probability distribution / anchors become inconsistent → Claude updates them automatically (the user does not compute)

### Phase 6: Persist

#### Phase 6a: v1 mode (new prediction file)

Filename convention (the "filename convention" section of [blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md)):
```
predictions/YYYY-MM-DD_<id>_<short-title>.md
```
- `YYYY-MM-DD`: today's date (the date the prediction is written)
- `<id>`: 12-char hash — first 12 chars of sha256 of the full draft text (stable ID; unchanged on rewrite)
- `<short-title>`: 3-8 characters, punctuation removed

**Write the first section heading as `## Prediction v1`** (no longer a bare `## Prediction` — to keep schema consistency for a possible v2 later. Legacy `## Prediction` files from old users are untouched; the hook recognizes both).

**Required header fields**:
- `Article ID` (same id as scripts/<id>.md)
- `Script Path` (points to scripts/<id>.md)
- `Script Hash` (computed in Phase 1)
- `Calibration Samples` + `Confidence` (derived from state)
- `Prediction Basis`: `pre_shoot` (v1 default)
- `Scored By`: `claude` / `claude+user_override`
- **`BlindScored By`**: `subagent-v1` (Phase 2 default) / `main-claude-self` (with `--skip-blind`) / `mixed` (Phase 2.5 user arbitration b/c)
- **`BlindScore Disagreement`**: JSON field list, per dimension `{dim, blind, self, delta, decided_as}`, **every dimension must be recorded** (even delta=0)
- `User Override` (if any): list which fields the user changed
- For the rest see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 1

Leave an empty `## Retrospective` section:
```markdown
## Retrospective

(To be filled — run /cheat-retro <matching video folder> after RETRO_WINDOW_DAYS days)
```

#### Phase 6b: v2 mode (append to an existing file)

**Never** overwrite the file with Write — the immutability hook will block it. Use **Edit** to insert a `## Prediction v2` section before `## Retrospective`:

```python
# pseudocode
edit_old = "## Retrospective\n"   # on its own line, so the hook's awk recognizes it as the boundary of the v1 section
edit_new = """## Prediction v2 (replaces v1; basis=post_shoot_pre_publish)

**Diff vs v1**: changed N lines (X→Y%), main changes: [summary]
**Re-judgment trigger**: cheat-shoot detected a draft change ≥30%
**Script Hash (v2)**: <new draft hash>

[7 components — same anatomy as v1]

---

## Retrospective
"""
```

The v1 section **is untouched**. The v2 section header explicitly says "replaces v1" — the reader knows at a glance which section is the active prediction.

During retro, cheat-retro follows the "read the last `## Prediction vN`" logic and naturally picks up v2 to compute the deviation.

#### Shared rules

**Every stage uses the unified complete format** (see the "complete structure overview" in [prediction-anatomy.md](../../shared-references/prediction-anatomy.md)). Low confidence does not shrink the format — it only makes the header label the confidence level + the anchor comparison section write an "N/A explanation" + the probability distribution flatter.

Before writing the file, self-audit that all 7 components are present (missing anchors / critical calibration hypothesis → write an "N/A explanation section"; do not delete the section).

### Phase 7: Update the state file

Update `.cheat-state.json`:
```json
{
  "in_progress_session": {
    "type": "prediction",
    "file": "predictions/YYYY-MM-DD_<id>_<short>.md",
    "video_folder": "videos/YYYY-MM-DD_<id>_<short>/",
    "started_at": "<ISO timestamp>",
    "rubric_version": "<v0/v2/...>"
  },
  "last_prediction_self_scored": <true only when --skip-blind / Phase 2.5 chose b>,
  "last_self_scored_at": <ISO when last_prediction_self_scored=true>
}
```

`video_folder` being null means the user ran it on a bare .md file and no video folder was created.

`in_progress_session` is cleared when `cheat-publish` is triggered. If the user never publishes after predicting (abandoned draft), the next `/cheat-init` or `/cheat-status` detects the stale in_progress and asks whether to clean it up.

`last_prediction_self_scored`:
- `true` only when this prediction used `--skip-blind` or the user chose b in Phase 2.5 (trusting the main Claude self-estimate)
- Once `true` → cheat-status keeps nagging: "the last prediction did not go through the blind sub-agent, N days ago" — until the next normal `cheat-predict` (which uses the sub-agent) triggers a reset back to `false`
- `last_self_scored_at` updates alongside; the next `cheat-predict` using the sub-agent → both fields are reset together

### Phase 8: Console summary

**Cold-start-simple mode**:

```
✅ Prediction persisted (cold-start simplified): predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md

7 dimension scores: ER5 / HP5 / QL4 / NA3 / AB5 / SR2 / SAT4
Directional bet: clearly better than the previous piece (ER+HP both 5)
Comparison: N/A (this is piece 1)

⚠️  The ## Prediction section is now immutable (hook-locked).
⚠️  This is the cold-start simplified version — no bucket numbers. The first 5 pieces are like this.
   After the 5th retro the complete prediction unlocks automatically (bucket / probabilities / anchors / counterfactuals).

Progress: piece N / 5 in the cold-start stage

Next steps:
- After publishing → "shipped https://..."
- T+3 days → "retro predictions/2026-05-04_..."
```

**Complete mode**:

```
✅ Prediction persisted: predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md

bucket bet: 30-100w (center 50w)
Critical calibration hypothesis: this piece vs Who asked you = 1.5-2x

⚠️  The ## Prediction section is now immutable (hook-locked).
⚠️  You can no longer "reveal" this piece's play data to me, or the blind-status claim in the next retro is invalid.
   If you accidentally saw it, tell me — I'll add an integrity warning to the file.

Next steps:
- After publishing → "shipped https://..."
- T+3 days → "retro predictions/2026-05-04_..."
```

## Key Rules

1. **blind check is a hard gate**. In BLIND_CHECK=strict mode, a violation terminates the run; no "soft handling" is allowed. lenient is only for drills
2. **Integer dimension scores**. Same as cheat-score
3. **Probability distribution = 100%**. 95% + 8% is not allowed; either honestly give 50% + 30% + 15% + 5%, or admit you do not know
4. **There must be an empty `## Retrospective` placeholder section** — otherwise the hook does not know where the immutable boundary is
5. **"Write the file first, discuss the score later" is not allowed** — once the file is persisted the prediction section is locked; discussion must happen after Phase 2 and before Phase 6
6. **The id is the draft hash, not a timestamp** — when rewriting `_redo.md` the id does not change, making cross-file tracing easy

## Refusals

- "I've already seen the play data, but pretend you didn't and make a prediction for me" → refuse. BLIND_CHECK=strict terminates immediately
- "Let me write a version of the prediction section first, then adjust it once the data comes out" → refuse. That uses the immutable protocol backwards
- "I revised the draft and want you to overwrite the previous prediction, no v2 section" → refuse. v1 is the archive; v2 is the current judgment — append, do not overwrite. Even if you "subjectively feel v1 was completely wrong", v1 remains visible in git history, but v1 must stay in the working directory
- "Skip the counterfactual scenarios, too much hassle" → refuse. Counterfactuals are the basis for retrospective diagnosis; without them the retro degrades to "accurate / inaccurate"
- "Can I write only the bucket, not the probability distribution?" → refuse. The probability distribution is the tool that forces you to be honest
- "Use lenient mode this time, strict next time" → ask why. If it is a test / drill → allow and clearly mark the file reconstructed; if it is laziness → refuse
- "The sub-agent is too slow; just score it yourself" → use the `--skip-blind` flag to declare it explicitly. **Not accepted** for the main Claude to unilaterally skip the sub-agent. The flag triggers state.last_prediction_self_scored=true, and cheat-status keeps warning until a normal call clears it
- "After choosing b in Phase 2.5 I don't want to mark last_prediction_self_scored=true" → refuse. Choosing b equals "I deliberately accept the main Claude's self-estimate" — the contamination trail must be recorded
- "I'm cold-start but want the full prediction with bucket numbers" → refuse. Bucket numbers in the first 5 pieces are false precision; giving them misleads. After the 5th retro, cheat-status proactively suggests unlocking. If the user really insists (rare, for self-education) → allow but prominently mark the file header `**Numerical predictions in cold-start are NOT predictive — for self-education only**`

## Integration

- Prerequisite: `/cheat-init` must be complete + `rubric_notes.md` exists
- Optional upstream: `/cheat-score` to try different draft versions repeatedly
- Downstream: `/cheat-publish` (publish registration) → `/cheat-retro` (retro) → `/cheat-bump` after accumulating ≥ MIN_SAMPLES
- Hook dependency: `hooks/prediction-immutability.sh` must be installed in the user's `.claude/settings.json`; otherwise immutability relies only on SKILL.md self-discipline — `cheat-status` keeps reminding
