# Rubric Memo — bump upgrade archive

> ⚠️ **This file is Channel A internal reference. Channel B (the cheat-score-blind sub-agent) NEVER reads this file** — the blind sub-agent's hard refusal list explicitly includes this file path.
>
> It accumulates the full memo of every rubric bump: triggering observations, evidence data tables (including real sample names + actual performance), diagnosis, cross-model audit conclusions, and known limitations.

---

## What this file is for

When cheat-bump Phase 5 lands, write the bump memo **here**, **not** into `rubric_notes.md`.

Historically cheat-bump wrote the full memo (including video names + actual performance + derived evidence) into `rubric_notes.md`. But `rubric_notes.md` is the blind sub-agent's whitelist file — the sub-agent leaked actual-performance data through it, turning blind scoring that should have been isolated into "post-hoc rationalization after seeing the results".

The fix:

| File | Content | Blind whitelist |
|---|---|---|
| `rubric_notes.md` | Formula / dimension definitions (**generic language**, no video names / actual performance) / bucket section / top metadata | ✅ YES |
| `rubric-memo.md` (this file) | Full bump memo (**including** real video names + real play counts + derived evidence) | ❌ NO (strictly forbidden) |

---

## Writing rules (cheat-bump Phase 5)

- **Append mode**: a new bump memo is **appended to the end of the file**; old memos are untouched. Reading in reverse chronological order shows the full rubric evolution
- **Every memo must contain 6 components** (per the [bump-validation-protocol.md](../shared-references/bump-validation-protocol.md) Step 5 template):
  1. Triggering observations (which observations accumulated to ≥3 same-direction misses)
  2. Evidence data (calibration-pool re-score table + ranking comparison — **including real video names + actual performance**)
  3. Diagnosis (which rubric hypothesis was refuted)
  4. New formula (changed weights / dimensions)
  5. Cross-model audit conclusion citation (channel C verdict + reason excerpt)
  6. Known limitations (what this bump did not solve)

- **The derived-evidence section** also goes **here**: named anchors such as "derived evidence: 'video X' CC=1 → actual 137k" are **absolutely not allowed** in `rubric_notes.md`; they all settle into this file

---

## Who reads this file

| Skill | Reads? | What it does |
|---|---|---|
| `cheat-bump` Phase 5 | ✅ writes | Append new memos |
| `cheat-retro` | ✅ reads | Looks back at historical memos during retro to find the rubric evolution trail |
| `cheat-status` | ✅ reads | Shows "what evidence the last bump used" on the dashboard |
| **`cheat-score-blind`** | ❌ **strictly forbidden** | refusal_code: `blocked_rubric_memo` |
| The main-Claude self-estimate part of `cheat-score` / `cheat-predict` | Does not proactively read | The main conversation is already contaminated; reading the memo again is just redundant |

---

## Memo section format (cheat-bump writes in this format)

Append one section per bump, in this format:

```markdown
---

## v<N> → v<N+1> Memo (bumped at <ISO 8601>)

### Triggering observations
(List the ≥3 same-direction miss observation IDs that accumulated to this bump + a one-line summary. Cite observation IDs from rubric_notes.md.)

### Evidence data
**Calibration-pool re-score table**:

| Sample | composite (vN) | composite (vN+1) | rank (vN+1) | Actual | rank (actual) | delta |
|---|---|---|---|---|---|---|
| "Real video name 1" | 9.41 | 9.55 | 1 | 1.248M | 1 | 0 |
| "Real video name 2" | 8.24 | 9.11 | 2 | 711k | 2 | 0 |
| ... | ... | ... | ... | ... | ... | ... |

**Derived evidence** (if any):
- "Video name X" CC=1 → actual Y validated the "high abstraction density → low reach" hypothesis
- ...

### Diagnosis
(Which hypothesis of rubric vN was refuted by the data; why the vN+1 formula explains the deviation)

### New formula
Old: `(ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0`
New: `(ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0`

Changes: removed NA / AB; added MS / TS; ER weight 1.5 → 2.0

### Cross-model audit (channel C)
- Audit model: qwen-max-2025-XX
- Verdict: PASS
- Reason excerpt: "..."
- Key risk: "..."

### Known limitations
(What this bump did not solve; directions still to watch at the next bump)

```

---

## Example: v0 → v1 (first bump)

(cheat-init creates this file empty; the first memo is appended here on the first bump)

<!-- subsequent bumps append here -->
