# Observation Lifecycle

Referenced by these sub-skills: `cheat-retro`, `cheat-bump`, and the main SKILL.md.

This is the full specification of project principle #3 — **the rubric is a workbench, not a museum**. Every addition or deletion of an observation entry in `rubric_notes.md` must follow this protocol.

---

## Three life stages

Every observation is in one of the following states:

```
[new]  →  [observation log]  →  [cross-video observation]  →  [settled rule] / [absorbed as a dimension] / [refuted]
                                                            ↘
                                                             [hypothesis to verify] (parking lot)
```

| Stage | Location in rubric_notes.md | Trigger |
|---|---|---|
| **Observation log** | `## Observation log` section | Written after a single retro. One entry per video retro |
| **Cross-video observation** | `## Major cross-video observations` section | The same pattern appears in ≥2 samples |
| **Settled rule** | `## Settled rules (high confidence)` section | Already supported by ≥2 samples **and has passed the bump validation process** (i.e. absorbed into a dimension or explicitly confirmed) |
| **Hypothesis to verify** | `## Hypotheses to verify` section | A single-sample observation parked until more samples arrive |

---

## Thresholds for advancing to the next stage (**Claude judges; the following are reference defaults**)

| From → To | Default reference threshold | Claude's signal-strength judgment (may soft-break) |
|---|---|---|
| Observation log → cross-video observation | Same pattern in ≥2 samples | 1 sample + strong meme evidence (≥2,000 likes in the comments) may also promote |
| Cross-video observation → hypothesis to verify | Single sample + strong signal but not yet reproduced | — |
| Cross-video observation → settled rule | ≥2 samples + no formula change needed | 1 sample + strong counterexample (≥3x miss) may also promote (label `**Single-sample, high-confidence**`) |
| Cross-video observation → dimension (no longer stands alone) | ≥3 samples + absorbed through the bump process | Same as cheat-bump's READINESS_HEURISTIC |
| Any → deleted | Refuted by new data / absorbed as a dimension / settled as a rule | `cheat-bump` cleanup pass, or a standalone operation |

**Core principle**: sample count is a **proxy for signal strength**, not the signal itself. 3 clear samples traceable to specific data points > 10 fragmentary, low-confidence samples.

**Discipline when Claude soft-breaks**:
- Label `**Promoted with N samples (default expects M)**: <why it still holds>` so the user can inspect it
- Do not soft-break repeatedly — if Claude soft-breaks 2+ times in the last 3 promotions, cheat-status warns "your observation-promotion judgment may be too aggressive; consider returning to the default thresholds for review"

### Sample size → permitted actions (detailed tiers)

The calibration pool's **total sample count** determines what changes are allowed — bigger structural changes need more evidence:

| Calibration pool size | Permitted actions | Notes |
|---|---|---|
| **1** | Record a "single observation" | A single point cannot trigger any rule change; it is only a seed |
| **2-4** | Extract "candidate rules" + promote to the "cross-video observations" section | Still cannot change the formula |
| **5-9** | Revise dimension definitions (**qualitative change** — e.g. make the SR=5 threshold stricter) | Do not touch weight values; only change judgment habits. **The first formal bump also happens in this tier** (the rubric takes shape for the first time) |
| **10-19** | Fine-tune weights by ±0.2 (**quantitative change**) | e.g. ER ×1.5 → ×1.7; adding / removing dimensions is still a "qualitative structural change" and needs more samples |
| **20+** | Back out weights with regression (**data-driven**) | Spearman correlation etc.; usable as bump evidence |

**Key discipline**:
- Do not use regression at N=5 — fitting a 7-dimension formula on 5 points will overfit
- Do not keep tuning weights by intuition at N=20 — there is already data signal
- The bump protocol's `MIN_SAMPLES_FOR_BUMP=5` is the minimum threshold for **the rubric taking shape for the first time**, not the threshold for "starting to be data-driven" — the latter requires N≥20

---

## Deletion rules (the part most often done wrong)

**Two kinds of entries must be deleted, never kept**:

### Type A: observations absorbed as dimensions

Example: during the v2.1 bump, "Observation E (the amount of remix on the acknowledgment section is the strongest external evidence for ER=5)" was absorbed as the new dimension **MS (Memetic Shareability)**.

→ After the bump lands, **delete** the "Observation E" log entry. The MS dimension is its new home.

**Reason**: keeping the observation means the same concept appears twice in the file (once as a dimension, once as an observation). The reader will be confused: is this history or a currently active rule?

### Type B: observations refuted by new data

Example: Observation X proposed "long videos have a low ceiling"; later 4 long-video samples all broke 500k → refuted.

→ **Delete** that observation.

**Reason**: keeping it means your future self or other readers will score based on a wrong rule.

---

## Entries that must be kept

The following entries are **not deleted**; leave them in place or migrate them to the appropriate section:

- **Unresolved observations** (neither absorbed nor refuted) → migrate to the new version's "hypotheses to verify" section on the next bump
- **Historical calibration events** (e.g. "v1 → v2 happened because Housing prices at 2.59M was severely underestimated") → keep in the "bump memo" section of the version log, **not** in the observation section
- **Rules still active in the current version** (already settled in "settled rules") → keep

---

## Disallowed anti-patterns (**must refuse**)

The following patterns are all "museum impulses" — treating rubric_notes.md as a historical archive:

| Anti-pattern | Why it is wrong |
|---|---|
| `~~ER weight 1.5~~` `**changed to 2.0**` (old value with strikethrough) | Use git history to see old values; do not pile them up in the file |
| "I once thought SR mattered, but actually..." | This kind of archaeology entry leaves the reader unsure what the current rule is after reading |
| "NA was key in the v1 era; after v2 we found it wasn't" | Same as above. Delete NA-related entries; leave the version memo to explain why NA was cut |
| "Keep this observation as a counterexample" | Counterexamples belong in the version memo's "refuted hypotheses" subsection, not the observation section |
| "I'll delete it in the next bump, leave it for now" | Refuse. Delete it cleanly in the same operation that lands the bump |

Git history is the real archive. `rubric_notes.md` is a snapshot of the currently active rules — a reader opening it should see **how to score today**, not the evolution history of the past few months.

---

## Blind channel leak guard (**every skill must follow this when writing rubric_notes.md**)

`rubric_notes.md` is the **whitelist** for the cheat-score-blind sub-agent (channel B) — when the sub-agent reads this file to score a script, the file content must not contain **actual-performance data from published pieces**, otherwise the sub-agent's "blindness" is broken.

**Patterns forbidden in rubric_notes.md**:

| Pattern | Example | Alternative location |
|---|---|---|
| Real video title + actual performance | "'Stop expecting' got 711k plays" | rubric-memo.md |
| Derived evidence with named anchors | "Derived evidence: 'She's different' MS=5 → actual 1.248M" | rubric-memo.md |
| Calibration-pool re-score table | The sample comparison table from a bump | rubric-memo.md |
| Cross-model audit quotes containing numbers | "audit: 'Boss nonsense' rank consistent ✓" | rubric-memo.md |
| Numbers matching `\d+w` / `\d+万` / `\d+M` / `\d+k` (**except bucket boundaries**) | "actual 137k" | rubric-memo.md |

**Allowed patterns** (generic language):

- Formula: `(ER×2.0 + HP×1.5 + ...) / N × M`
- Dimension definition: `ER (emotional resonance): 0 = no emotion / 3 = medium resonance / 5 = extreme resonance`
- **Abstracted** derived evidence: `Derived evidence: high-abstraction-density sample → CC=1 → low reach`
- Bucket boundaries (numbers belong to the rules, not to actual performance): `5-30w / 30-100w / 100-150w / >150w`
- Observation ID + one line: `Observation E: a question in the first 5 seconds → ER+` (no sample name / no actual performance)

**mandatory cheat-bump Phase 5 self-check**: after writing rubric_notes.md, run `grep -E '\\d+\\s*[wWmMkK万]|播放|实绩|实际|plays|actual'` → any hit → abort + roll back. This is a hard constraint. (The Chinese terms are kept so legacy Chinese notes are still caught.)

Historical context: when PR #11 introduced cheat-score-blind, this was missed — cheat-bump wrote the memo into rubric_notes.md, and the sub-agent read actual performance through the whitelist. PR #12 fixed it (split the file) and added this section to prevent a repeat.

---

## Mandatory timing of the cleanup pass

`cleanup pass` = deleting in one pass every observation that satisfies a "deletable" condition.

Mandatory triggers:
- **The last step of landing a bump** (see `bump-validation-protocol.md` Step 5)
- The user explicitly triggers a "cleanup" operation (rare)

Non-mandatory but recommended:
- Every 5 new calibration samples, proactively review the "observation log" section to see which entries can be promoted / deleted
- When the `cheat-status` dashboard detects that `rubric_notes.md` exceeds 500 lines, recommend a cleanup

---

## Line budget

Reference healthy size of `rubric_notes.md` (target):

| Calibration pool size | Healthy line count | Warning line count |
|---|---|---|
| 0-5 pieces | 100-200 | >300 |
| 5-20 pieces | 200-400 | >500 |
| 20-50 pieces | 300-500 | >700 |
| 50+ pieces | 400-600 | >800 |

Exceeding the warning line count → run a cleanup pass. This is not for looks; it is so **a reader can read the core rules in 60 seconds before scoring**.

---

## Alignment with the "observation log" template

The standard template for each observation entry (`rubric_notes.template.md` uses the same one):

```markdown
### YYYY-MM-DD [short title] (id) — [one-line assessment, e.g. "ER dominance validated"]
- Prediction: composite=X.XX, bucket=Y
- Actual: plays / likes / comments / shares (with T+Nd label)
- Top comment keywords: [brief excerpt + like count]
- Judgment: which dimension was validated / refuted? Why?
- Rubric adjustment: [if any, state "next time scoring XX type of piece, change YY"]
- See: [predictions/<file>.md]
```

Template for cross-video observations:

```markdown
### Observation X — [one-line rule]
**Evidence**:
- Sample 1 (composite, actual): key data
- Sample 2 (composite, actual): key data
- Sample 3 (composite, actual): key data

**Hypothesis**: [if the rule holds, what rubric adjustment it implies]

Sample count: N, [met / pending].
```

---

## Interface with the bump protocol

In Step 5 (cleanup pass), `cheat-bump` must process the observation sections in this order:

1. List every entry in `## Observation log`
2. Ask 3 questions of each entry:
   - Was it absorbed as a formal dimension by this bump? → delete
   - Was it refuted by this bump's new data? → delete
   - Is it still unresolved? → migrate to "hypotheses to verify"
3. List every entry in `## Major cross-video observations`
4. Ask the same 3 questions of each entry
5. Move rules that are "validated but do not require a formula change" → "settled rules"
6. Finally, **re-read** the whole `rubric_notes.md` to ensure a reader can understand the current scoring rules in 60 seconds
