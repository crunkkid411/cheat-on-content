# Rubric Bump Validation Protocol

Referenced by these sub-skills: `cheat-bump`, and the main SKILL.md.

This is the full specification of project principle #2 — **a bump = a full re-score**. Every structural change to the rubric must go through this protocol.

---

## Definition of a "bump"

Any of the following changes triggers the full bump process:

- A change to a formula coefficient (ER×1.5 → ×2.0)
- Adding or removing a dimension (drop NA, add MS)
- A disruptive rewrite of a dimension definition ("QL = number of quotable lines" → "QL = reusable sentence patterns")
- A change to the normalization constant (divisor 8.5 → 9.0)

The following changes do **not** trigger a bump, but must be annotated in `rubric_notes.md`:
- Marginal refinement of a dimension definition (the threshold for QL=5 changes from "≥3 lines" to "≥3 lines distributed across different sections")
- A note that a single-dimension threshold has become stricter (no formula change, only the judgment habit at scoring time)
- Updating anchor samples (using a new sample as the 5-point benchmark)

---

## When a bump **may** be proposed (**Claude judges; the following are reference triggers**)

Any one is enough to propose — but **the final call is Claude's judgment of observation maturity + signal strength**; the list below is only a default heuristic:

1. A cross-sample observation shows a **clear support pattern traceable to specific data points** (default reference: ≥3 samples, but Claude may propose based on 1-2 **exceptionally strong** samples — e.g. a 6x traffic ratio / a single meme with ≥2,000 likes)
2. The current rubric has been **systematically biased in the same direction** in recent retros (default reference: ≥3 same-direction misses, but Claude may propose based on 1-2 **extreme deviations** — e.g. a 500k center vs 50k actual, a 10x miss)
3. A candidate dimension shows independent predictive power (reference sample count: ≥3 is solid, but 1-2 strong pieces of evidence also count)
4. The calibration pool crosses a milestone (5 / 10 / 20 / 50), triggering a routine review

**When Claude proposes a bump it must explicitly label** whether the proposal is default-aligned (meets the routine thresholds above) or judgment-driven (based on a strong signal but few samples). Let the user inspect the basis.

---

## When a bump is **forbidden**

The following are **hard constraints** — Claude cannot break them:

- A prediction is currently in progress (`state file in_progress_session != null`) — process discipline
- There have been no new calibration samples since the last bump — at least 1 new sample is required before another bump (avoid validating yourself in a loop)

The following are **soft recommendations** — Claude should normally avoid them, but may break them with a strong reason and explicit labeling:

- Do not normally bump when the calibration pool is < 5 samples (unless a strong counterexample appears)
- Do not normally bump when fewer than 3 new calibration samples have arrived since the last bump (unless the new samples contain a strong counterexample)

**When Claude breaks a soft rule, it must:**
1. Explicitly state in the proposal: "I know the default recommendation is to wait for N≥5 / ≥3 new samples, but this time the reason is [X strong signal]"
2. Still run the full 5-step validation process (including cross-model audit)
3. If the cross-model audit returns REJECT → the bump is rejected; **"I think the signal is strong" is not allowed to bypass it**

---

## Full bump process (mandatory 5 steps, no skipping)

### Step 1: Write the complete equation of the new formula

You cannot just say "increase the ER weight"; you must write the entire equation, all coefficients, and the normalization constant.

Example (compliant):
```
v2.0  composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
v2.1  composite = (ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0
```

Examples (non-compliant):
- "Raise the ER weight to 2.0" ← does not say whether the other weights change
- "Add an MS dimension" ← does not state the weight or normalization constant

### Step 2: **Locally** re-score the entire calibration pool

Calibration pool definition: every file under `predictions/*.md` that has a complete retrospective section (including `actual_*` data).

Recompute the composite for each piece with the new formula. **Do not re-score the dimension scores** — dimension scores stay the same (v2's ER=5 is still ER=5 under v2.1); only the composite is recomputed.

Exception: if the new formula adds a dimension (e.g. new MS), you must **backfill an MS score** for every old sample. This step makes the cost of a bump rise linearly with the sample count — an intentional "bump damping".

### Step 3: Compute ranking consistency

The new composite ranking vs the ranking of samples by actual-performance bucket must satisfy:
- Agreement on ≥`THRESHOLD` proportion of samples (default 4/5 = 80%)
- No pair of samples that the old formula ordered correctly may be reversed (pairwise no-regression)

Algorithm for ranking consistency:
1. Rank all calibration samples by new composite
2. Rank all samples by actual_plays
3. Compute Spearman rank correlation; also check whether the relative order of every pair (i, j) is reversed
4. Output a comparison table: each sample's [new rank, actual rank, delta]

### Step 4: Independent cross-model audit (**mandatory**, unless the escape hatch is used)

When `CROSS_MODEL_AUDIT=true` (default):
1. Call `mcp__llm-chat__chat` with the following package sent to the external LLM:
   - The old formula + the new formula
   - For every calibration-pool sample: dimension scores, composite (new + old), actual_plays, actual_likes, actual_comments, actual_shares
   - The ranking comparison table from Step 3
2. The external LLM independently judges two things:
   - Is ranking consistency really ≥ THRESHOLD?
   - Does the new formula explain more than the old one?
3. The external LLM must output **PASS** / **REJECT** + a reason of ≥ 100 words
4. Both the local judgment and the external judgment must **pass** before Step 5

`CROSS_MODEL_AUDIT=false`: skip the external audit — **only for offline / no-network use**. The state file marks `last_bump_self_audited: true`, and `cheat-status` keeps reminding the user to configure an external audit.

### Step 5: Post-bump cleanup pass

The bump must land in one pass:

1. Update `**Current version**` at the top of `rubric_notes.md` and add a row to the **version quick-reference table**
2. Append a "vN → vN+1 bump memo" section to `rubric-memo.md` with the full memo (trigger observations + evidence data + diagnosis + new formula + known limitations). ⚠️ Do not write this into `rubric_notes.md` — that file is the blind sub-agent's whitelist, and including actual-performance data would contaminate the blind scoring channel
3. Delete every "observation log" entry that drove this bump and has now been absorbed into a formal dimension
4. Delete every "observation log" entry refuted during the bump
5. Any "observation log" entry still unresolved → move it to the new version's "hypotheses to verify" section (keep it)
6. Append one line to the **bottom** of every calibration sample's prediction file: `**Re-scored under <new-version> on YYYY-MM-DD**: composite=X.XX → Y.YY` (do not touch the prediction section or retrospective section; append only this line)

Cleanup is not optional. rubric_notes.md is a workbench, not a museum — see `observation-lifecycle.md`.

---

## Handling a rejected bump

If any step fails → the bump is rejected, handled as follows:

| Failure point | Handling |
|---|---|
| Step 3 local ranking inconsistency | The candidate formula goes back to the "to verify" area. Silently relaxing THRESHOLD (e.g. 4/5 → 3/5) is **not allowed** — that is honest self-deception. THRESHOLD is protocol rigidity; it differs from the sample-count threshold for "when a bump may be proposed" (the latter may be soft-broken) |
| Step 4 external audit REJECT | Record the external LLM's full reason in the "rejected bump log" section of `rubric-memo.md` |
| Step 4 external audit conflicts with the local judgment (one PASS one REJECT) | Treat as REJECT. A conflict means at least one side's reading of the data is unstable; do not bump |
| Step 5 cleanup cannot be completed (e.g. an observation can neither be deleted nor kept) | Roll the bump back to step 0. Note: this means the new formula still has uncaptured "unresolved observations"; the proposal is immature |

---

## Bump damping (why this protocol is intentionally hard)

Every additional sample in the calibration pool makes a bump linearly more expensive:
- Calibration pool 3-5 → almost zero cost
- Calibration pool 20-30 → noticeable cost
- Calibration pool 50+ → painful

This is **intentional design**. Frequent bumps = the rubric is chasing noise. A healthy rubric is characterized by: **bumps becoming rarer, and each bump becoming larger** — one bump explains multiple accumulated observations, rather than one observation per bump.

Reference video-analysis project: v1 → v2 took about 4 weeks (from first publish to first bump); the v2 → v2.1 candidate has been waiting 4 weeks and still has not shipped (waiting for joint validation on 6 samples). That is a healthy cadence.

---

## Anti-patterns (requests that must be refused)

- "Skip the calibration-pool re-score and just swap the formula" → refuse. Step 2 cannot be skipped
- "External LLM audit is too much hassle, skip it" → only allowed when `CROSS_MODEL_AUDIT=false` is explicitly set
- "This time I'm only tuning one weight, that doesn't count as a bump, right?" → any coefficient change counts. Step 1 must write the complete equation
- "It's just for my own use, I don't need the full process" → refuse. The value of this process is in **your future self looking back** — when you later ask "why wasn't v2.3 adopted?", you need the complete memo
- "Can we change THRESHOLD from 4/5 to 3/5 so this passes?" → refuse. Changing THRESHOLD is itself a meta-level bump and needs its own process
