# Scoring calibration notes

> **This file is the vehicle for cheat-on-content's scoring-rule evolution**. After every retro comparing actual play data against predicted scores, write the reasoning and rules here explicitly; before scoring next time, `/cheat-score` `/cheat-predict` read this file first.
>
> **Core principle**: every rule must be traceable to specific samples. Do not write empty phrases like "emotional resonance matters" — write "XX's ER=5 was validated / refuted because the top 3 comments were all YY pattern".
>
> Full lifecycle protocol: [shared-references/observation-lifecycle.md](../cheat-on-content/shared-references/observation-lifecycle.md).
> Bump process: [shared-references/bump-validation-protocol.md](../cheat-on-content/shared-references/bump-validation-protocol.md).

---

## Rubric version log

_Only structural changes bump the version number; pure observation accumulation does not. After a version bump, every sample in the calibration pool must be re-scored with the new formula. Write a structured evidence memo for every bump (see the per-version sections below)._

**Current version**: `v0`

**Version quick-reference table**:

| Version | Effective date | Change type | Driving sample count | Driving article_ids |
|---|---|---|---|---|
| v0 | [YOUR-INIT-DATE] | Initial placeholder (cold-start) | 0 (prior) | — |

**Bump decision principles**:
- Pure weight tweak (e.g. SR×1.5 → ×1.8) → no bump; recompute the composite
- Dimension definition refinement (e.g. a stricter SR=5 threshold) → no bump, but note the new threshold in the retro
- Adding/removing dimensions, or a disruptive rewrite of a definition → bump the major version

**Migration trigger**: if an article scored under an old version enters the top during candidate selection → re-read and re-score it on the spot; do not re-score everything. **The calibration pool (with actual performance data) must be fully re-scored on every bump**.

---

## Current scoring dimensions (0-5)

> **Example: the table below is the measured v2 formula of the "video analysis" project (a Chinese opinion-video creator, 25+ published samples).
> Cold-start users should start with equal weights — see [opinion-video-zero.md](../cheat-on-content/starter-rubrics/opinion-video-zero.md).
> After calibrating 5 pieces, decide whether to replace this table with your own fitted version.**

| Dimension | Weight | Meaning | Typical signals |
|---|---|---|---|
| emotional_resonance (ER) | 1.5 | Emotional impact | Comments "teared up / broke down / me too" |
| social_resonance (SR) | 1.5 | Social-issue resonance | Social-phenomenon keywords in comments |
| hook_potential (HP) | 1.5 | Opening grab | Completion rate / first-3s retention |
| quotable_lines (QL) | 1.0 | Quotable-line density | Comments quoting the original |
| narrativity (NA) | 1.0 | Story quality | Repost / save rate |
| audience_breadth (AB) | 1.0 | Audience breadth | Non-follower share |
| satire_depth (SAT) | 1.0 | Satire / irony depth | Comments "savage / incisive / sharp" |

**Composite formula**:

```
composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
```

> Placeholder formula for cold-start users (equal weights):
> ```
> composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
> ```

---

## Observation log

> **Template** (append one entry after each retro):
>
> ```
> ### YYYY-MM-DD [short title] (id) — [one-line assessment, e.g. "ER dominance validated"]
> - Prediction: composite=X.XX, bucket=Y
> - Actual: plays / likes / comments / shares (with T+Nd label)
> - Top comment keywords: [brief excerpt + like count]
> - Judgment: which dimension was validated / refuted? Why?
> - Rubric adjustment: [if any, state "next time scoring XX type of article, change YY"]
> - See: [predictions/<file>.md]
> ```
>
> Deletion rules: [shared-references/observation-lifecycle.md](../cheat-on-content/shared-references/observation-lifecycle.md): absorbed as a dimension → delete; refuted → delete. Git history is the archive.

### Example entry (from the video-analysis project, for reference only; your project's real entries start accumulating after your first retro)

#### 2026-04-24 Stop expecting (ab61ed09) — emotional hit validated [T+7d data]
- Prediction: composite=8.24 (v2: ER5/HP5/QL5/NA3/AB5/SR2/SAT4), bucket=30-100w
- Actual: T+7d 711k (center 500k, **+42%**), share/play ratio **2.53%**
- Top comment keywords: "she's different" / "he's different" appears 12+ times in variants (highest 2,266 likes)
- Judgment: ER=5 dominance validated by strong evidence (vs the same-composite Who asked you at 117k, **6.07x traffic ratio**)
- Rubric adjustment: candidate for the next bump to raise ER from ×1.5 to ×2.0
- See: [predictions/2026-04-24_ab61ed09_stop-expecting.md]

> The above is an example. During cold-start, delete it and start accumulating real entries from your first retro.

---

## Major cross-video observations (≥2 samples support but need more validation)

> Single-sample observations stay in the "Observation log" section and do not come up here. Only the same pattern in ≥2 samples is promoted here.

(None yet — they accumulate automatically once you start recording)

---

## Settled rules (high confidence, must read before scoring)

> Every rule needs ≥2 supporting samples + it has passed the bump validation process (i.e. absorbed as a dimension or explicitly confirmed).

(None yet — there will be content after 1-2 bumps)

---

## Benchmark-derived initial signals

> Derived from [benchmark.md](benchmark.md) (if any); indicates **which dimensions look important** across the benchmark account's high/medium/low samples.
>
> **Qualitative direction only; do not adopt them directly as numeric weights** — fitting on 5-10 samples easily overfits.
> Decide whether to adjust weights during the formal bump after you have N≥5 calibration samples of your own.
>
> Empty initially — `/cheat-learn-from` fills this in.

(To be filled by cheat-learn-from)

---

## Hypotheses to verify

> Single-sample observations + strong signals that have not yet reproduced go here.

- [ ] [example] Analogy-type pieces > direct-expression pieces (wait until the next analogy piece ships)
- [ ] [example] Around Spring Festival / Qingming and similar holidays, the AB of family-type pieces temporarily +1 (no samples)

---

## Rejected bump log

> Bumps that were proposed but failed validation are recorded here — so the same failed proposal is not repeated six months later.

(None yet)

---

## Bucket scheme (**current: ratio**)

> ⚠️ **Bucket boundaries are a property of the user's account, not a universal constant** — absolute-number buckets ("5w is the floor") only hold for veterans with a follower base; for a 0-follower newcomer, every video lands in "the bottom 99%" and buckets lose their ordering meaning.
>
> This tool switches between three bucket schemes by calibration stage. The active scheme is determined by the `bucket_scheme` field in `.cheat-state.json`.

### Stage 1: cold-start, ratio buckets (current stage)

`bucket_scheme = "ratio"`

**Piece 1**: use platform-generic defaults (actual play count)

| Bucket | Range (actual plays) | Meaning | Prior probability |
|---|---|---|---|
| Floor | < 100 | Almost buried by the algorithm | 30% |
| Base | 100 - 1,000 | Small recommendation supported by completion rate | 40% |
| Hit | 1,000 - 10,000 | The first signal of breaking out | 20% |
| Small hit | 10,000 - 100,000 | Extremely rare "zero-follower first hit" | 8% |
| Big hit | > 100,000 | Abnormal algorithmic weighting | 2% |

**From piece 2 on**: `baseline = the previous piece's actual plays` (or the median of the last 3)

| Bucket | Multiple range | Meaning |
|---|---|---|
| Regression | < 0.3 × baseline | Clearly worse than the previous piece |
| Flat | 0.3 - 1 × baseline | Same tier as the previous piece |
| Hit | 1 - 3 × baseline | Moderate breakthrough |
| Small hit | 3 - 10 × baseline | Significant breakout |
| Big hit | > 10 × baseline | Order-of-magnitude leap |

See the "ratio bucket scheme" section of [starter-rubrics/opinion-video-zero.md](../cheat-on-content/starter-rubrics/opinion-video-zero.md).

### Stage 2: switch to fixed absolute buckets after N=5 (with ratio as backup)

`bucket_scheme = "absolute_with_ratio"`

After 5 pieces, `/cheat-bump --bucket-only` derives automatically:
- `baseline = the median actual plays of the 5 pieces`
- Boundaries = baseline × {0.3 / 1 / 3 / 10 / 30}

`/cheat-bump --bucket-only` replaces this section's table when it lands.

### Stage 3: switch to percentile buckets after N≥10 (recommended long-term scheme)

`bucket_scheme = "percentile"`

Boundaries = percentiles of your historical samples:
- Floor = bottom 30%
- Base = 30-60%
- Hit = 60-85%
- Small hit = 85-95%
- Big hit = top 5%

`/cheat-status` proactively suggests switching at N=10. This scheme is always self-consistent — "top 5%" means the same thing no matter how big the account is.

---

> **The reference creator's absolute buckets** (fitted on 25+ videos, **only applicable to mature creators who already have a follower base** — do not copy them before you have calibrated):
>
> | Bucket | Range (ten-thousands of plays) | Prior probability |
> |---|---|---|
> | Floor | <50k | 5% |
> | Base | 50k-300k | 35% |
> | Hit | 300k-1M | 45% |
> | Breakout | 1M-1.5M | 12% |
> | Phenomenal | >1.5M | 3% |

---

## Default retrospective window

`RETRO_WINDOW_DAYS = 3`

Why 3 days: algorithmic distribution decisions are basically over within 72 hours; waiting longer only adds noise, not signal.

If your platform is special — remember to state the override reason here, e.g.:
> WeChat Official Account RETRO_WINDOW_DAYS = 7 (pushes finish within 24h, long tail is slower)
