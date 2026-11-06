# Prediction Anatomy

Referenced by these sub-skills: `cheat-predict`, `cheat-retro`, `templates/prediction.template.md`.

**Every prediction uses the same format** — 7 required components + a retrospective section. The confidence level (derived from `calibration_samples`; see the confidence table in [state-management.md](state-management.md)) is annotated as a header field to tell the user how trustworthy this prediction is, **but it does not change the prediction format itself**.

> **Why there is no separate cold-start simplified version / complete version (a discarded old design)**:
> Splitting cold-start into a simplified version was based on the worry that bucket numbers in the first 5 pieces would be false precision. But the better solution is to **show the confidence level** — a weather forecast always reports a specific temperature and then labels its confidence; it does not withhold the number because the forecaster is inexperienced.
> Two-version switching also introduced a complexity jump at "the 5th piece suddenly unlocks the complete version" — a jarring user experience. A unified format plus progressive confidence labeling is smoother.

Reference real samples: the reference-creator project (private, includes 25+ calibrated videos) — both the tool's design inspiration and the rubric weights come from this real data.

---

## The 7 required components

### Component 1: File header

```markdown
# <title> — Prediction log

**Article ID**: <12-char hash>  (sha256 of scripts/<id>.md initial content, first 12 chars)
**Title**: <full title of the piece>
**Rubric Version**: **v0** | **v1** | **v2** | ...
**Predicted at**: 2026-05-04 (based on the final draft)
**Script Path**: scripts/2026-05-04_<id>_<short>.md
**Script Hash**: <sha256:12 of script content at predict time>
**Target Duration (s)**: 240  (derived from state.typical_duration_seconds)
**Actual Script Length**: 980 words  (read from the Script Path file)
**Calibration Samples (at predict time)**: 3
**Confidence**: 🟡 Low-ish (center ±40%, usable as one reference)
**Prediction Basis**: pre_shoot  ← or `post_shoot_pre_publish` (v2 section)
**Scored By**: claude  ← or `claude+user_override`
**BlindScored By**: subagent-v1  ← or `main-claude-self` / `mixed`
**BlindScore Disagreement**: <inline JSON — see below>
**User Override**: none  ← or list the overridden fields
**Data status at prediction time**: **blind** (no actual <platform> performance data seen)
```

The `BlindScore Disagreement` field is an inline JSON array, **one row per dimension**, and **delta=0 must be recorded too**:

```json
[
  {"dim": "ER",  "blind": 5, "self": 5, "delta": 0, "decided_as": 5},
  {"dim": "SR",  "blind": 3, "self": 4, "delta": 1, "decided_as": 3},
  {"dim": "AB",  "blind": 2, "self": 4, "delta": 2, "decided_as": 4, "user_decision": "b"},
  {"dim": "HP",  "blind": 5, "self": 5, "delta": 0, "decided_as": 5}
]
```

- `blind`: the score given by the sub-agent
- `self`: the main Claude's own estimate (the internal estimate at the end of Phase 2 that used to stay out of the file is now recorded — a necessary price of honesty)
- `delta`: |blind - self|
- `decided_as`: the final value used in the composite calculation
- `user_decision` (if any): the option chosen by the user in Phase 2.5, `a` / `b` / `c <number>` — only appears when delta ≥ DISAGREEMENT_THRESHOLD

Required-field rules:
- `Rubric Version` is required — when v3 arrives and we look back at v2 predictions, without a version number there is no fair comparison
- `Data status at prediction time` is required — explicitly declaring blind is the precondition of the immutability promise
- `Script Path` is required — points to `scripts/<id>.md` (the pre-shoot draft)
- `Script Hash` is required — cheat-shoot re-hashes `videos/<id>/script.md`; if it differs → add an integrity warning to the retrospective section
- `Calibration Samples` + `Confidence` are required — tell the reader how trustworthy this prediction is. **Confidence is derived automatically** from calibration_samples (see state-management.md)
- `Prediction Basis` is required — `pre_shoot` for a standard blind prediction; `post_shoot_pre_publish` for the v2 post-shoot draft revision (still no data seen, but soft-blind)
- `Scored By` is required — tell the reader whether the prediction was fully automatic or the user intervened:
  - `claude`: Claude proactively scored + bucketed + assigned probabilities, and the user replied "ok" after review
  - `claude+user_override`: the user challenged and changed some fields during review
- **`BlindScored By` is required** — who produced this round's dimension scores:
  - `subagent-v1`: blind scores obtained through the Task tool from the cheat-score-blind sub-agent (default, Phase 2 path)
  - `main-claude-self`: the user used `--skip-blind` or chose b in Phase 2.5 (trusting the main Claude's own estimate) — also sets `state.last_prediction_self_scored=true`
  - `mixed`: in Phase 2.5 the user chose c and overrode individual dimensions while the rest still came from the sub-agent
- **`BlindScore Disagreement` is required** — the JSON above. **Record every dimension** (even delta=0); do not record only the big differences. Reason: during retro, analyzing the delta distribution by dimension — "which kinds of dimensions systematically diverge between the sub-agent and the main Claude" — is an important signal for rubric evolution
- `User Override` is required (if there were overrides) — list which fields changed from X to Y, with the user's reason. During retro this field helps diagnose: if the user's override is validated by actual performance (the user's intuition was right) → the rubric may be missing something

---

### Component 2: Input snapshot

Record the draft state **at prediction time** — especially the user's final changes.

```markdown
## Input snapshot

**Scores (vN)**: ER5 / HP5 / QL5 / NA3 / AB5 / SR2 / SAT4 → composite=**8.24**

**User revision highlights vs Claude draft (if any)**:
- **Opening**: user cut the EWDM model name and the setup
- **Cut**: [specific paragraph / concept name / setup]
- **Kept**: [key quotable line / acknowledgment paragraph / main structure]
- **Pacing**: [tighter / looser] than the draft by about N%
```

> If the user wrote it from scratch (without cheat-seed), write "original user draft, no Claude draft to compare against".

---

### Component 3: Prediction body ⭐ immutable section

This is the core immutable section. `hooks/prediction-immutability.sh` intercepts every Edit from this heading to the next `##`.

```markdown
## Prediction v1

**Bucket**: `30-100w`

**Internal probability distribution**:
- `<5w` → 3%
- `5-30w` → 22%
- **`<headline bucket>` → 55%** (center ~50w)
- `>100w` → 17%
- `>150w` → 3%

**One-line reason**:
> ER=5 + AB=5 universal crush audience; IS directly locks in; 7.3 days + zero-signal reversal + MVP quotable line gives a complete emotional curve; SR=2 with no social issue underneath is the ceiling bottleneck; expected center 40-60w.
```

Hard requirements:
- **Bucket** must be one of the 5 predefined buckets
- **Probability distribution** must sum to 100% — this is the tool that forces you to be honest
- **Center** is the point estimate inside that bucket, making it easy to judge "high / low" during retro
- **One-line reason** is condensed for a DB field, making cross-sample retrieval easy

**About buckets during cold-start**: with few calibration_samples → the distribution **should be flatter** (e.g. 30/30/20/15/5 rather than 5/40/45/8/2). Low confidence does not mean skipping the bucket; it means the bucket deserves an appropriate amount of uncertainty.

---

### Component 4: Reasoning factors

Every factor driving the judgment + direction + confidence + explanation.

```markdown
## Reasoning factors

| Factor | Direction | Confidence | Explanation |
|---|---|---|---|
| ER=5 | strong + | high | "scrolling chat history at 3 a.m." is extremely concrete |
| IS hook | strong + | high | "only affects people who X" locks the audience in one line |
| SR=2 | strong - | high | no social issue underneath; pure personal emotion has a limited ceiling |
| Data + quotable-line route | medium ? | low | algorithmic friendliness is unverified |
```

**Confidence** has three levels: high (strong evidence + multiple anchors), medium (reasoned but few samples), low (intuition).
- During retro, if a "low-confidence" factor is validated → intuition is strong
- If a "high-confidence" factor is refuted → the rubric has a bug

---

### Component 5: Anchor comparison

Find 2-4 old samples with similar composite scores and list their actual performance.

```markdown
## Anchor comparison

| Comparison sample | composite | Actual | Similarities / differences |
|---|---|---|---|
| Hamster | 9.41 | ~1.5M | composite 1.17 lower, but the route differs a lot (analogy explainer vs data + quotable lines) |
| Housing prices | 9.41 | 2.59M | SR differs by 3 points (2 vs 5) |
| Who asked you | 8.24 | T+8d 117k | same composite but ER 5 vs 3, SR 2 vs 4 |
```

The value of anchors: catch mistakes the formula cannot catch.

**When there are not enough calibration samples** (< 2 published samples with composite within ±0.5):

```markdown
## Anchor comparison

The calibration pool has only N samples, with no composite ±0.5 neighbors. **Anchor comparison N/A** —
note that this prediction's confidence label is 🟡 Low-ish / 🔴 Very low; the bucket center is for reference only.
```

**Still write this section** — tell the reader why anchors are missing. Do not delete the section.

---

### Component 6: Counterfactual scenarios

For each possible bucket, write a paragraph on "if it lands here, what it means".

```markdown
## Counterfactual scenarios

**If it blows up to `>X w`** (X% expected):
- [which hypothesis is validated]
- [which hypothesis is refuted]
- [which new rubric dimension might be added]

**If it lands in `headline bucket`** (X% expected):
- [what the baseline validates]

**If it drops to `<X w`** (X% expected):
- [which core judgment is refuted]

**If `<<X w`** (X% expected):
- [possible explanation for the extreme scenario]
```

Why required: during retro, **which bucket it actually landed in** directly tells you which rubric hypothesis was tested. Without counterfactual scenarios, the retro degrades into "this time it was right / wrong" — no diagnostic value.

---

### Component 7: Critical calibration hypothesis

Optional but strongly recommended: treat this prediction as an experiment and write down explicitly "if X happens, it proves Y".

```markdown
## Critical calibration hypothesis (vs Who asked you)

Both pieces have the same composite=8.24. Differences:
- How to stop expecting: ER=5 / SR=2
- Who asked you: ER=3 / SR=4

**My bet: this piece > Who asked you (ratio 1.5-2x)**

If the opposite happens → SR weight in the rubric should go up, ER weight should go down
If the gap is < 1.3x → the rubric is basically OK; the difference is within noise
```

Calibration hypotheses are the seeds of rubric bumps — a single hypothesis validated by ≥3 samples → enters the bump candidates.

**When there are not enough calibration samples**: write "no comparable samples — but I will still write down my core bet for this one (even without an anchor)", then write one or two things you want to test this time. **Do not delete this section**.

---

### Component ∞: Retrospective — append only

Appended T+N days after publication during the retro. **Not a single character of the prediction section may change.**

```markdown
## Retrospective

**Retro at**: 2026-05-07 (T+3d after publish)
**Fetched at**: 2026-05-07 09:30
**Data source**: manual paste / adapter:douyin-session

### Actual performance
- Plays: 711k (landed in `30-100w`, on the high side, **+42%** vs the 500k center)
- Likes: 24k (like/play ratio 3.38%)
- Shares: 18k (share/play ratio 2.53%, strong)

### Top comment keywords
- "She's different" meme explosion: 2,266 likes, alone at the top; 12+ variants across the text

### Which predictions were validated / refuted
**Validated ✅**:
- The critical calibration hypothesis held completely: this piece 711k / Who asked you 117k = 6.07x
- ER=5 drove emotional spread → strong evidence for H1

**Refuted ❌**:
- The 500k center was exceeded by +42%
- My bet on SR was refuted in the opposite direction: SR should be lowered in emotionally driven scenarios

### New observations to write into rubric-memo.md
1. The true weight of ER in emotionally driven scenarios should be ≥ ×2.0
2. Issue-share impulse (TS) is a hidden dimension
```

---

## Full structure overview

```
file: predictions/YYYY-MM-DD_<id>_<short>.md

# Title — Prediction log          ← component 1: header (includes confidence + script_hash + Prediction Basis + BlindScored By + BlindScore Disagreement)
(metadata block)

## Input snapshot                  ← component 2
(scores + user revision highlights vs Claude draft)

## Prediction v1                  ← component 3 ⭐ IMMUTABLE start (based on pre-shoot draft)
(bucket + probabilities + center + one-line reason)

## Reasoning factors              ← component 4
(table with direction + confidence)

## Anchor comparison              ← component 5 (still write the "N/A section" when the calibration pool is insufficient)

## Counterfactual scenarios       ← component 6
(one "what it means" paragraph per bucket)

## Critical calibration hypothesis ← component 7
(the explicit bet of this prediction as an experiment)

## Prediction v2 (replaces v1)    ← (optional) triggered by cheat-shoot when the post-shoot draft changes ≥30%, appended not overwritten
(same 7-component structure + header includes a Diff vs v1 summary)

## Retrospective                  ← append only, IMMUTABLE boundary
(actuals + top comments + validated/refuted + new observations)
```

### v1 / v2 section conventions

- **New files**: cheat-predict writes `## Prediction v1` (no longer a bare `## Prediction` — reserves schema consistency for v2)
- **Legacy compatibility**: files written with `## Prediction` during v0.1.0 are left alone; both the hook and cheat-retro recognize them
- **v2 trigger condition**: cheat-shoot detects a line-diff ≥ 30% between the shooting script and `scripts/<id>.md` ([V2_TRIGGER_THRESHOLD](../skills/cheat-shoot/SKILL.md)), then calls `/cheat-predict — mode: v2 — prediction-file: <path>`
- **Append, not overwrite**: the v2 section is inserted before `## Retrospective`. The v1 section is **never** modified (physically enforced by the hook)
- **Which one calibration uses**: cheat-retro reads the last `## Prediction vN` to compute deviation; v1 is kept as historical archive
- **Diff learning**: the field differences between v1 and v2 (e.g. ER 4→5) are the scoring changes caused by the user's draft revision — evidence for rubric bumps

### Prediction Basis field

The prediction header must contain `Prediction Basis`:
- `pre_shoot` (v1 default, standard blind prediction)
- `post_shoot_pre_publish` (v2, soft-blind prediction — draft revised after shooting but re-judged before publishing)

cheat-retro uses this field to distinguish the two data lines during score-curve / bump calibration, avoiding mixed samples.

---

## Sub-skill acceptance criteria

After `cheat-predict` finishes a prediction, it must self-check that all 7 components are present:
- Components 5 / 7 must still write an "N/A section + explanation" when calibration samples are insufficient; **skipping them outright is not allowed**
- The header's `Calibration Samples` + `Confidence` are required — the reader sees at a glance how trustworthy the prediction is

When `cheat-retro` writes the retrospective section, it must first validate the file's 7 components:
- Missing component → warn "this prediction is non-conforming; its retro value is discounted"
- The retrospective format is **independent of** the confidence level — every stage uses the same retrospective format
- Diff `Script Hash` against the current `videos/<id>/script.md` hash → if different, add a `**Script changed between predict and shoot**` warning to the retrospective section

---

## Comparison with the old design (for v1 user migration)

| v0 design (abandoned) | v1 design (current) |
|---|---|
| `prediction_complexity = cold-start-simple` uses a 3-component simplified version | Field removed. Every prediction uses the unified 7-component version |
| `prediction_complexity = complete` uses 7 components | Same as above — it was always 7 components |
| The 5th retro "unlocks the complete prediction" | No unlocking needed — always complete. Confidence level rises automatically with calibration_samples |
| Cold-start skips bucket / anchor comparison / counterfactuals | **Do not skip** — if anchors are insufficient, explicitly mark "N/A"; still write the bucket (the distribution should be honestly flat) |
| Use the mode=cold-start field to branch the workflow | Field removed. Every skill follows the same workflow and progressively shows confidence based on calibration_samples |
