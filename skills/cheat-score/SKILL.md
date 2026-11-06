---
name: cheat-score
description: Score a single draft against the rubric. **Console output only; writes no files, makes no prediction**. Triggers: "打分这篇 [path]" / "score this [path]" / "给这稿子打分" / "先打分看看". This is the lightweight exploration step before cheat-predict.
argument-hint: <draft-path>
allowed-tools: Read, Glob, Grep
---

# /cheat-score — single-draft scoring

Score but **do not predict**. The user uses it to quickly see a draft's composite and decide whether it is worth entering the formal prediction flow.

## Overview

```
[User: score this draft.md]
  ↓
[Read draft.md + rubric_notes.md]
  ↓
[Score each dimension 0-5 + write a one-line reason + compute composite]
  ↓
[Console output: scores + composite + recommended next step]
  ↓
[End — write no files]
```

## Constants

- **RUBRIC_PATH = rubric_notes.md** — source of the current rubric
- **OUTPUT_DETAIL = full** — full: includes a reason per dimension; compact: score table only

> 💡 Override at call time: `/cheat-score draft.md — OUTPUT_DETAIL: compact`

## Inputs

| Required | Source |
|---|---|
| `<draft-path>` | passed by the user as an argument; ask in the conversation if missing |
| `rubric_notes.md` | user project root |
| `.cheat-state.json` | user project root (to read the current `rubric_version` and mode) |

## Workflow

### Step 1: Pre-flight check

1. Read `.cheat-state.json` → if missing, tell the user to run `/cheat-init` first and stop
2. Read `<draft-path>` → if missing or empty → error and stop
3. Read `rubric_notes.md` and find the currently active formula section (usually under "Current scoring dimensions" or "Composite formula")

### Step 2: Identify the formula and dimensions

Parse from `rubric_notes.md`:
- The current rubric_version
- The dimension list and weights (e.g. `ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT`)
- The normalization constant (e.g. `/ 8.5 × 2.0`)
- The 0-5 meaning of each dimension (read from the "Current scoring dimensions" table)

If `rubric_notes.md`'s format does not match expectations (the user hand-edited the structure) → ask the user which line is the current formula; **do not guess**.

### Step 3: **Delegate to the blind sub-agent** (no more inline scoring)

The main conversation is already contaminated by the user conversation / published data / historical retro sections — inline scoring means scoring with hindsight.

Instead, **call the `/cheat-score-blind` sub-agent via the Task tool**; the main Claude only schedules + reviews. See [skills/cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md).

**Task prompt template** (**may only contain** the following):

```
Spawn cheat-score-blind sub-agent.

Input:
  script_path: <the draft path the user gave>
  rubric_notes_path: rubric_notes.md

Task: score the above script according to the current formula in rubric_notes. Return strict JSON (see the cheat-score-blind SKILL.md Phase 2 schema).
Do not read the state file / predictions/ / videos/ or any other file.
Do not ask the user anything — you have no user.
```

**Forbidden** in the Task prompt (see the "Main Claude call contract" section of [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md)):
- User conversation quotes / excerpts
- Any mention of play counts / 万 / w / k etc.
- Hints such as "the previous prediction was X" / "actual plays were Y"
- Any `predictions/*.md` path

Self-check with grep before calling: `echo "<prompt>" | grep -Ei '播放|阅读|点赞|评论数|实际|retro|复盘|实绩|w$|万$'` — on a hit → rewrite the prompt and resend.

### Step 4: Parse the sub-agent's JSON + review

The sub-agent returns strict JSON. The main Claude:

1. Parses the dimensions section (score + per-dim confidence + reason)
2. Checks `self_check.any_contamination_signal == false`; otherwise warn
3. Computes the composite per the rubric_notes formula (formula logic in the main, scores from the sub-agent)
4. **Does not modify the sub-agent's dimension scores** — the score is display only. If the user challenges it ("AB should be 3, not 4"), the main Claude records it under `User Override` but keeps the sub-agent's original score on file

If the sub-agent returns `refusal != null`:
- `blocked_contaminated_input` → report that the Task prompt contained forbidden fields and have the main Claude resend
- `script_path_invalid` → check the path
- `rubric_unparseable` → tell the user rubric_notes.md is corrupted
- `non_blind_warning` → still accept the dimensions (but confidence all medium), and warn

### Step 5: Compute the composite + output

Compute the composite per the current formula. Console output (OUTPUT_DETAIL=full):

```
📊 [draft.md short title] — score (rubric: v2)

| Dimension | Score | Reason |
|---|---|---|
| ER (emotional resonance) | 5 | "scrolling chat history at 3am" — extremely concrete |
| HP (hook power)         | 5 | one IS line locks in the audience |
| QL (quotable-line density) | 5 | the MVP line "intermittent hope" stands alone and travels |
| NA (narrative)          | 3 | flat narration, weak arc |
| AB (audience breadth)   | 5 | crushes / exes are universal |
| SR (social-issue resonance) | 2 | purely personal emotion, no social backing |
| SAT (satire depth)      | 4 | the credits section is self-referential irony |

Formula: (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
composite = (5×1.5 + 2×1.5 + 5×1.5 + 5 + 3 + 5 + 4) / 8.5 × 2.0 = **8.24**

📍 Lands in the 30-100w bucket (based on the bucket boundaries in starter-rubrics)

Next:
- If this is the final draft and you're ready to publish → say "start prediction"
- If you want to revise → revise and score again (repeated scoring leaves no trace)
- If you want to see historical samples with a similar composite → say "find anchors with composite 8.0-8.5"
```

When OUTPUT_DETAIL=compact, output only the score table + composite, without the reason column.

### Step 6: Things to **never** do

- ❌ Write any file (including predictions/, rubric_notes.md, candidates.md)
- ❌ Give a bucket probability distribution (that is cheat-predict's job)
- ❌ Trigger "published" or "retro" logic
- ❌ Propose a rubric upgrade (even if scoring reveals an obvious anomaly, only mention it in the console; do not touch the rubric)

## Key Rules

1. **Scoring goes through the sub-agent**. The main Claude no longer scores inline. See the isolation protocol in [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md)
2. **Integer scores**. 4.5 and 3.7 are not allowed
3. **Blind scoring first**. The sub-agent sees only script + rubric; it is inherently blind — that is the entire reason it exists
4. **Reasons are diagnostic tools**. Each dimension's 1-30 word reason is not decoration — it is used during retro to find which dimension's judgment was wrong
5. **Do not write files**. This is the core difference between score and predict. score is exploration; predict is commitment
6. **Do not compute candidate composites**. The composite field in candidates.md is written by cheat-trends/cheat-recommend — score serves only "a specific draft that is already written"

## Refusals

- "Score it and predict while you're at it" → refuse. Use `/cheat-predict` instead. Reason: predict must run blind check + write an immutable log; score skips those
- "Write the score into the observation section of rubric_notes.md after scoring" → refuse. The observation lifecycle requires an "actual performance vs prediction" comparison; a score alone does not constitute an observation
- "Can you just tell me whether it will pop?" → refuse. A concrete composite + bucket judgment requires the predict flow; score only outputs the mechanical calculation under the current rubric
- "Skip the blind sub-agent and let the main Claude score directly" → cheat-score **does not accept** that escape hatch (unlike cheat-predict, which has `--skip-blind`). score is lightweight exploration; there is no reason to give up isolation. If the Task tool is truly unavailable → tell the user to configure it and retry

## Integration

- It is the exploratory step before `cheat-predict`: the user can score different draft versions repeatedly, settle on one, then predict
- score does not update `.cheat-state.json` — it is a side-effect-free operation
- If the user scores the same draft ≥3 times in a row → gently note in the console "repeated scoring causes decision fatigue; it is probably time to decide"
