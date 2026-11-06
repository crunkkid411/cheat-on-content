---
name: cheat-bump
description: Propose and execute a rubric or bucket upgrade. Two modes: **full rubric bump** (the highest-risk action; 5 mandatory steps + cross-model audit) and **--bucket-only lightweight recalibration** (only swaps bucket boundaries, does not touch the rubric formula). **Phase 2 mandatorily re-scores the calibration pool through the cheat-score-blind sub-agent** — self-scored fallbacks are not accepted. Triggers: "升级 rubric" / "bump rubric" / "更新公式" / "我想加一个维度" / "调整权重" / "重校桶" / "recalibrate bucket".
argument-hint: --propose "<...>" | --bucket-only [--scheme ratio|absolute|percentile]
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, Skill, Task, mcp__llm-chat__chat
---

# /cheat-bump — Rubric / Bucket upgrade

Two modes:

| Mode | Trigger | What it does | Validation strength |
|---|---|---|---|
| **Full rubric bump** | `--propose "<new formula>"` | Change formula / dimensions / weights | 5 steps + cross-model audit (mandatory) |
| **bucket-only recalibration** | `--bucket-only` | Only re-derive bucket boundaries | Automatically derived from data, no audit |

A full rubric bump strictly follows the 5 steps in [shared-references/bump-validation-protocol.md](../../shared-references/bump-validation-protocol.md). bucket-only takes the lightweight path — see Phase B below.

## Overview

```
Entry: user triggers /cheat-bump
  ↓
[Phase A0: detect call mode]
  ↓
  ├─ --bucket-only  →  [Phase B: lightweight bucket recalibration]
  └─ --propose      →  [Phase 0~6: full rubric bump]
```

## Phase A0: Route by call mode (do this first)

Read the user arguments:
- Contains `--bucket-only` → go to **Phase B** (lightweight recalibration)
- Contains `--propose "<...>"` → go to **Phase 0~8** (full rubric bump)
- Neither → ask the user: "What do you want to do? 1) adjust the rubric formula / add or remove dimensions → --propose; 2) only re-derive bucket boundaries → --bucket-only"

If the user says "I think ER is too low, I want to adjust it" → that is the `--propose` path.
If the user says "my account has grown and the buckets are off" → that is the `--bucket-only` path.
**The two paths cannot be mixed** — one operation does one thing.

---

## Full rubric bump flow

```
[User: upgrade rubric --propose "ER×1.5→2.0, cut NA, add MS"]
  ↓
[Phase 0: prerequisite gate check]
  ↓
[Phase 1: write out the full new formula equation]
  ↓
[Phase 2: full re-score of the calibration pool]
  ↓
[Phase 3: compute rank consistency]
  ↓
[Phase 4: independent cross-model audit (mandatory)]
  ↓
[Phase 5: land + cleanup pass]
  ↓
[Phase 6: append a Re-scored line to the bottom of every calibration sample's prediction file]
```

## Constants

- **READINESS_HEURISTIC** —
  - **Default reference**: calibration pool ≥ 5 samples + at least 1 cross-sample observation supported by ≥3 samples
  - **But Claude may propose a bump** (even with few samples) if the signal is unusually strong:
    - N=3 but a strong counterexample completely refutes the current rubric hypothesis (composite 8.5 vs actual 50k, a ≥3x miss)
    - 1 piece shows a single-point but extremely strong phenomenon (e.g. one meme in the comments with ≥2000 likes)
  - **Claude may also refuse a bump** (even with enough samples) if the evidence is weak:
    - N=10 but the observations are all low-confidence fragments with no clear direction
    - The user's retros contain many casual "I just glanced at it" non-serious judgments
  - **When writing the prediction header or the cheat-bump output, always state**: whether this proposal is default-aligned or judgment-driven, so the user has a basis to review it
- **THRESHOLD = 0.8** — consistency threshold between the new ranking and the actual-performance ranking (4/5). This is **hardcoded** — the statistical rigidity of bump validation
- **CROSS_MODEL_AUDIT = true** — call an external LLM for independent audit. false only for offline use
- **REQUIRE_CONFIRM = true** — require the user to explicitly say "yes, bump" before landing

## Inputs

| Required | Source |
|---|---|
| `--propose` text | user argument; ask if missing |
| `rubric_notes.md` | user project root |
| All `predictions/*.md` | calibration-pool data |
| `.cheat-state.json` | state |

## Workflow

### Phase 0: Prerequisite gate check

Following the "when it is forbidden" section of [bump-validation-protocol.md](../../shared-references/bump-validation-protocol.md), check each item:

| Check | Failure handling |
|---|---|
| Calibration-pool sample count vs observation strength | **Claude judges** — per READINESS_HEURISTIC: default ≥5 samples but exceptions allowed (strong counterexample / strong meme). If below the default, Claude must **explicitly explain** why it still proposes a bump ("although N=3, piece X shows composite Y vs actual Z, a W-fold miss"), so the user can review it |
| New calibrations since the last bump vs observation maturity | **Claude judges** — default recommends ≥3 new samples, but if 3 consecutive pieces all strongly point the same way → no need to wait |
| `in_progress_session == null` | Refuse: "You have an in-progress prediction. Finish that flow first or clear the state" |
| Trigger conditions hold (systematic deviation / cross-sample new observation / enough new-dimension evidence) | Warn but do not block — ask the user why they want to bump now |

Pass → go to Phase 1.

### Phase 1: Write out the full new formula equation

**Do not accept the user's short description alone**. Expand it into a full equation:

```
Current: v2  composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
Proposed: v2.1  composite = (ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0

Change summary:
- ER ×1.5 → ×2.0 (up)
- SR ×1.5 → ×1.0 (down)
- Added MS ×1.5 (Memetic Shareability)
- Added TS ×1.0 (Topic Shareability)
- Removed NA (overlaps with HP)
- Removed AB (replaced by TS)
- Normalization constant 8.5 → 9.0
- Total dimension count: 7 → 7 (net change 0)
```

If the user's proposal is vague (e.g. "raise the ER weight a bit") → ask for the specific number; **do not guess**.

### Phase 2: Full re-score of the calibration pool (**mandatorily through the blind sub-agent**)

Glob every `predictions/*.md` file with a complete retrospective section → the calibration pool.

**A bump is the tool's highest-risk action — all re-scoring must go through the [cheat-score-blind](../cheat-score-blind/SKILL.md) sub-agent**. Inline re-scoring = the main Claude has already seen the actual performance, and rank consistency becomes overfitting instead of a real signal.

#### Mandatory constraints

- **No self-scored fallback is accepted** — `/cheat-predict` has a `--skip-blind` flag, but `/cheat-bump` **does not**. If the Task tool is unavailable → **abort the bump** and report "resolve the Task tool before bumping"
- **"I'll only recompute the composite, not re-score the dims" is not accepted** — even if the new formula only adjusts weights and adds no dimensions, every dim of every prediction must be re-examined against the script by the sub-agent. Reason: the old dim scores themselves may be contaminated; a weight change does not guarantee the old dims still hold

#### For each prediction:

1. Parse the prediction file to get the matching `scripts/<id>.md` path (from the `Script Path` header field)
2. Validate that the script file exists + its hash matches the header `Script Hash`; mismatch → warn (the script has changed) but still spawn the sub-agent
3. **Spawn the cheat-score-blind sub-agent via the Task tool**:
   ```
   Spawn cheat-score-blind sub-agent.

   Input:
     script_path: <Script Path from the prediction header>
     rubric_notes_path: rubric_notes.md
     sidecar_path: .cheat-cache/bump-rescores/<prediction-id>.json

   Task: score the script according to the current formula in rubric_notes (already the new version vN+1).
   Return strict JSON. Write the sidecar file so the main bump flow can read it in bulk.

   Do not read the state file / predictions/ / videos/ or any other file.
   Do not ask the user anything — you have no user.
   Do not read this prediction file itself — you only look at the script + rubric.
   ```
4. Wait for the sub-agent to finish → read the sidecar JSON → the main flow computes the composite with the new formula
5. Write the "re-score table" to `.cheat-cache/bump-rescores.json` (summary). **Mark every entry `blind: true`** — during the Phase 5 cleanup, write this field along with the new score into the prediction file's `Re-scored under v<N+1>` line

#### Honest labeling of residual contamination

Even with the sub-agent, **two kinds of residual contamination must be honestly labeled in the bump report**:

| Type | Source | Label field |
|---|---|---|
| Model prior contamination | The sub-agent is still Claude; shared RLHF | `model_prior_warning: true` (default true, cannot be turned off) |
| The user's own rubric design bias | rubric_notes.md was written by the user and naturally fits their own content | `rubric_self_designed: true` (default true, cannot be turned off) |

These two remind the user that channel C (cross-model audit) cannot be skipped. The end of every bump report must print: "The rank consistency above is consistency within channel A. **The final decision must wait for channel C audit to pass**."

#### Failure modes

| Symptom | Handling |
|---|---|
| A prediction's script file is missing | The sub-agent skips that entry; the main flow's summary reports "N entries excluded due to missing scripts". If the remaining valid pool < MIN_SAMPLES → abort the bump |
| The sub-agent returns `refusal != null` | Resend the Task up to 3 times; still failing → mark that entry `rescore_failed: true` and exclude it from the calibration pool |
| The Task tool is entirely unavailable | Abort the bump and tell the user "the Task tool is a hard dependency of bump. If you are truly offline, run `/cheat-bump --bucket-only` for the lightweight branch" |
| The sub-agent output contains contamination_signal | Mark `suspicious: true` but do not exclude — list these suspicious entries at the end of the bump report for the user to review |

### Phase 3: Compute rank consistency

```
For each sample:
  new_composite_rank: rank when sorted by the new formula
  actual_plays_rank: rank when sorted by actual plays
  delta: |new_rank - actual_rank|

Output comparison table:
| Sample | composite (v2) | composite (v2.1) | rank (new) | actual | rank (actual) | delta |
|---|---|---|---|---|---|---|
| Hamster | 9.41 | 9.55 | 1 | 1.248M | 1 | 0 |
| Stop expecting | 8.24 | 9.11 | 2 | 711k | 2 | 0 |
| Boss nonsense | 7.65 | 8.11 | 4 | 396k | 3 | 1 |
| Job-hunting paradox | 8.47 | 7.56 | 5 | 168k | 4 | 1 |
| Who asked you | 8.24 | 7.00 | 6 | 117k | 5 | 1 |

Rank consistency: 4/5 within |delta| ≤ 1
Pairwise no-regression: every pair the old formula got right is not reversed under the new formula ✓
```

Decision:
- Rank consistency < THRESHOLD (default 0.8) → **local reject**; report the failure clearly before Phase 4
- Any pairwise regression → **local reject**

`THRESHOLD` is hardcoded in the protocol — it may not be lowered ad hoc (that itself is another meta-decision that needs a bump).

### Phase 4: Independent cross-model audit (**mandatory**, unless the escape hatch applies)

`CROSS_MODEL_AUDIT=true` (default):

Call `mcp__llm-chat__chat`:

```
prompt:
You are an independent reviewer. Below is a rubric formula a content creator is about to upgrade.
Independently judge two things:
1. Rank consistency: does the new formula's ordering of the samples really agree with the actual-performance ordering on ≥80% of samples?
2. Explanatory power: compared with the old formula, does the new formula explain the calibration pool's actual-performance distribution better?

Data:
Old formula: (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
New formula: (ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0

Calibration pool:
[complete JSON of the Phase 2 re-score table]

Rank comparison:
[complete JSON of the Phase 3 table]

Output format:
- Verdict: PASS or REJECT
- Reason: ≥100 words
- Key risk: [if any, list potential problems with the new formula]
```

Receive the external LLM reply → parse the verdict.

Decision logic:
- Local PASS + external PASS → pass, go to Phase 5
- Local PASS + external REJECT → **treat as REJECT**. A conflict means at least one side's reading is unstable
- Local REJECT → already terminated in Phase 3
- `mcp__llm-chat__chat` unavailable → degrade gracefully to `CROSS_MODEL_AUDIT=false`, state file marked `last_bump_self_audited: true`

`CROSS_MODEL_AUDIT=false`:
- Rely on local judgment only
- Keep the state file marked; cheat-status keeps telling the user "this bump was self-audited; configuring mcp__llm-chat__chat is recommended"

### Phase 5: Land + cleanup pass

After the audit passes, **REQUIRE_CONFIRM=true** → ask the user: "The new formula PASSED both local and external audit. Final confirmation: execute the bump? This will modify rubric_notes.md + rubric-memo.md and delete several absorbed observations. Answer 'yes, bump' to execute."

After the user confirms:

#### 5a. Update `rubric_notes.md` (**generic language only; no video names / actual performance**)

- Update the top metadata:
  - `**Current version**: vN+1`
  - `**Last bumped at**: <ISO 8601>`
  - `**Upgrade memos**: see [rubric-memo.md](rubric-memo.md)` (a pointer; do not copy memo content)
- Add a row to the version quick-reference table (version number + formula signature only, **not** evidence samples)
- Update the "Current scoring dimensions" section (remove NA / AB, add MS / TS)
- **Derived-evidence section** — if the new dimension needs an anchor explanation → **use generic language**:
  - ✅ Allowed: "Derived evidence: high-abstraction-density sample → CC=1 → low reach"
  - ❌ Forbidden: "Derived evidence: 'Stop expecting' CC=1 → actual 137k" (video name + actual-performance numbers)
  - If a forbidden pattern hits → move that passage into the "derived evidence" subsection of rubric-memo.md and replace it in place with generic language

#### 5b. Write the memo into `rubric-memo.md` (**append mode; do not overwrite history**)

Following [bump-validation-protocol.md](../../shared-references/bump-validation-protocol.md) Step 5 + the [templates/rubric-memo.template.md](../../templates/rubric-memo.template.md) format, append a memo section to the end of the file:

- Triggering observations (with real observation IDs)
- Evidence data (**calibration-pool re-score table + rank comparison, including real video names + actual performance**)
- Derived evidence (**including real sample names + actual performance**)
- Diagnosis
- New formula
- Cross-model audit conclusion citation (including model name + verdict + reason excerpt)
- Known limitations

**Never** overwrite existing content in rubric-memo.md — bump memos accumulate chronologically.

#### 5c. cleanup pass (per the "mandatory cleanup-pass timing" in [observation-lifecycle.md](../../shared-references/observation-lifecycle.md))

Execute inside `rubric_notes.md` (**do not** touch rubric-memo.md):

- Observations absorbed into a new dimension → delete (e.g. observation E absorbed as MS → delete observation E)
- Observations refuted by new data → delete
- Still-unresolved observations → move to the new version's "Hypotheses to verify" section
- Validated "rules" → move to the "Settled rules" section

#### 5d. Tidy + self-audit

- Re-read the full `rubric_notes.md` and make sure a reader can understand the current rules within 60 seconds — over 600 lines triggers an extra cleanup
- **Self-audit leak guard**: run `grep -E '\d+\s*[wWmMkK万]|播放|实绩|实际'` against `rubric_notes.md` → if anything hits → **abort the bump + roll back**, telling the user "rubric_notes.md contains forbidden content (actual performance / play counts)". Such content belongs in rubric-memo.md, not rubric_notes.md

### Phase 6: Batch-update calibration samples

For every calibration sample's prediction file, **append at the bottom** (do not touch the prediction section, do not touch the retrospective section):

```markdown

---
**Re-scored under v2.1 on 2026-05-04**: composite=8.24 → 9.11 (blind: true)
(recomputed in full at rubric bump time by the cheat-score-blind sub-agent independently; see the v2 → v2.1 upgrade memo in rubric-memo.md)
```

The `blind: true` field is **required** — it tells future readers of this record "this is channel B isolated scoring, not the main Claude's self-estimate". If a prediction was excluded in Phase 2 due to a sub-agent failure → it gets no Re-scored line (stays as-is).

Use the Edit tool, matching the very end of each file.

### Phase 7: Update the state file

```json
{
  "rubric_version": "v2.1",
  "last_bump_at": "<ISO timestamp>",
  "last_bump_self_audited": false,
  "consecutive_directional_errors": [],
  "calibration_samples_at_last_bump": <current value>
}
```

Clear `consecutive_directional_errors` — the new rubric starts counting again.

### Phase 8: Console report

```
✅ Rubric upgraded v2 → v2.1

Changes:
- ER ×1.5 → ×2.0
- SR ×1.5 → ×1.0
- Added MS / TS
- Removed NA / AB

Calibration-pool re-score: 5/5 passed the rank check (4/5 consistent + 0 pairwise regressions)
Cross-model audit: ✅ PASS
Cleanup pass: deleted observations D and E (absorbed into the QL redefinition and the MS dimension)

The next prediction is scored under the v2.1 formula.
All historical prediction files have a Re-scored marker appended.
```

---

## Phase B: bucket-only recalibration (lightweight branch)

`/cheat-bump --bucket-only [--scheme ratio|absolute|percentile]`

**The essential difference from a full bump**: bucket boundaries are not part of the rules; they are a data-derived quantity. Re-deriving them **does not need a cross-model audit** — the derivation algorithm is deterministic and has no "judgment" component.

### B1: Choose the algorithm (auto-derived from the available sample count; **state does not store the scheme**)

| Algorithm | Applies | Boundary derivation |
|---|---|---|
| `ratio` (default N=1-4) | Small samples | Previous piece / median of the last 3 × {0.3 / 1 / 3 / 10 / 30} |
| `absolute` (default N=5-9) | Medium samples | Calibration-pool median × {0.3 / 1 / 3 / 10 / 30}, fixed boundaries |
| `percentile` (default N≥10) | Large samples | Calibration-pool actual-performance percentiles {30 / 60 / 85 / 95 / 100} |

The `--scheme` parameter lets the user **explicitly override the default**:
- `--scheme ratio` forces ratio (even when N≥5)
- `--scheme absolute` forces absolute
- `--scheme percentile` forces percentile (requires N≥3, otherwise error)

No `--scheme` specified → auto-derive per the table above.

> The old design had a `bucket_scheme` state field — removed in v1.1. Every skill derives the algorithm live from calibration_samples and does not need to persist "which one is current". This avoids the "forgot to sync after switching schemes" state-inconsistency problem.

### B2: Derive the new boundaries

Read every sample in `predictions/*.md` that has `actual_plays`.

**ratio mode**:
```
baseline = median(last 3 actual_plays)
buckets = {
  "Regression": (-inf, baseline * 0.3),
  "Flat": (baseline * 0.3, baseline * 1),
  "Hit": (baseline * 1, baseline * 3),
  "Small hit": (baseline * 3, baseline * 10),
  "Big hit": (baseline * 10, +inf),
}
```

**absolute mode**:
```
baseline = median(all calibration-pool actual_plays)
buckets = {
  "Floor": (-inf, baseline * 0.3),
  "Base": (baseline * 0.3, baseline * 1),
  "Hit": (baseline * 1, baseline * 3),
  "Breakout": (baseline * 3, baseline * 10),
  "Phenomenal": (baseline * 10, +inf),
}
```

**percentile mode**:
```
sorted_plays = sorted(all calibration-pool actual_plays)
buckets = {
  "Floor":   ≤ p30,
  "Base":    p30 - p60,
  "Hit":     p60 - p85,
  "Small hit":   p85 - p95,
  "Big hit":   ≥ p95,
}
```

### B3: Report the changes + user confirmation

```
Current bucket scheme: ratio
proposed scheme: absolute
baseline: 42k median (based on 5 calibration samples)

New boundaries:
- Floor:   < 13k
- Base:    13k - 42k
- Hit:     42k - 126k
- Breakout:   126k - 420k
- Phenomenal: > 420k

Derivation notes:
- 5 actuals: 15k / 38k / 42k / 56k / 180k
- Median 42k; new buckets derived by ×{0.3, 1, 3, 10}

Confirm apply? (yes / no)
```

### B4: Land

After the user confirms:
1. Edit the "Bucket scheme" section of `rubric_notes.md` and replace it with the new table
2. Update the `baseline_plays` field in `.cheat-state.json` (the bucket scheme is not persisted — the next cheat-predict derives it live)
3. Append a change-log line at the top of the bucket section in `rubric_notes.md`: `v2 buckets recalibrated on YYYY-MM-DD: scheme=absolute, baseline=42k (based on N=10 samples)`
4. **Do not** modify any prediction file — historical predictions keep their original bucket labels (judgments made under the scheme in force when that sample was written)

### B5: Impact on future predictions

The next `/cheat-predict` derives under the new buckets. Bucket labels in historical prediction files are **not recomputed** — a bucket is a semantic judgment made at prediction time; rewriting it afterward destroys the blind property.

### What Phase B does not do

- Does not re-score composites (the formula did not change)
- Does not re-audit the observation section (the rubric did not change)
- Does not call a cross-model audit (deterministic derivation needs no judgment)
- Does not require a strict sample-count gate (Claude judges per READINESS_HEURISTIC; ratio mode runs at N=1)

---

## Key Rules

1. **The 5 steps cannot be skipped** (full rubric bump only). Any request to "simplify it first" is refused
2. **THRESHOLD is hardcoded** (full rubric bump only). Dynamic adjustment is not allowed
3. **Cross-model audit is the default** (full rubric bump only). Turning it off requires an explicit mark in the state file
4. **The cleanup pass is part of the bump** (full rubric bump only). Bumping without cleaning the observation section is not allowed
5. **REQUIRE_CONFIRM** (both modes). Before landing, the user must explicitly say "yes, bump" or "yes, recalibrate"
6. **bucket recalibration does not touch historical predictions**. A bucket is the semantics at prediction time; rewriting it afterward destroys the blind property

## Refusals

- "Skip the calibration-pool re-score and just swap the formula" → refuse. Principle #2
- "Skip the cheat-score-blind sub-agent; the main Claude can re-score directly" → refuse. bump **accepts no** self-scored fallback — sub-agent unavailable → abort the bump; "self-audit" is not accepted
- "Skip the external LLM audit" → only when `CROSS_MODEL_AUDIT=false` is explicitly set
- "Lower THRESHOLD to 3/5 this time so it passes" → refuse. Changing THRESHOLD is a meta-level bump
- "Keep all the old observations as history" → violates principle #3
- "Bump first, do the cleanup next time" → refuse. The cleanup is part of the bump
- "Only recompute the composite, do not re-score the dims" → refuse. New weights × old dims are still old contamination. Every dim is re-examined against the script by the sub-agent
- "Write the full memo into the top of rubric_notes.md so it's easier for me to read" → refuse. rubric_notes.md is the blind sub-agent's whitelist — containing video names / actual performance → leaks through the whitelist. The memo goes into rubric-memo.md (**outside** the whitelist); rubric_notes.md holds only the formula + generic-language dimension definitions + pointers
- "Keep real video names in the derived-evidence section so the rubric reads more concretely" → refuse. rubric_notes.md must use generic language ("high-abstraction-density sample"); derived evidence with video names goes into rubric-memo.md

## Integration

- Upstream: `/cheat-retro` detects ≥3 same-direction misses → proposes running `/cheat-bump`
- Dependencies: `mcp__llm-chat__chat` (if configured) + the Task tool (spawns cheat-score-blind)
- Modifies:
  - `rubric_notes.md` (structural update, **never** writes real video names / actual performance)
  - `rubric-memo.md` (**new** — appends the full memo, including evidence + derived evidence)
  - Every `predictions/*.md` (appends a Re-scored line; does not touch the prediction section)
  - `.cheat-state.json`
- Downstream: the next `/cheat-predict` automatically scores under the new rubric_version
