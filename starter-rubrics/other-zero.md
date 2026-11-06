# Starter Rubric: generic / uncategorized content — v0 cold-start placeholder

> **⚠️ This is a generic catch-all rubric — use it when your content form is not any of opinion video, long essay, short text, podcast, or tutorial.**
>
> **Its dimension definitions were copied verbatim from "opinion video" and have not been adapted to your specific content form at all.** You should **heavily adjust the weights and dimension explanations** when using it — do not treat this rubric as "already customized for you".
>
> If your content form is already stable (e.g. you consistently make image-text reviews, Vlogs, knowledge maps, newsletters), it is strongly recommended to **redefine the dimensions** at the 5th-piece bump instead of only tuning weights.

**This is a placeholder rubric for new creators with absolutely no data.** It will score things wrong. **Prediction accuracy for the first 5 pieces is roughly ±50% — that is a mathematical fact of cold-start, not a rubric failure.**

After running 5 pieces (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you will have your first personal calibration data and can propose the first `/cheat-bump` to v1.

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is an integer 0-5. The composite range is 0-10.

**Why equal weights**: you have no data supporting any particular weight. Equal weights let you give each dimension "neutral attention" before the data arrives. After the 5th piece your retro data will tell you which dimensions actually predict spread on your account.

> **Special note for the generic rubric**: the equal-weight formula is almost certainly wrong for your content form — **but that is exactly the point of cold-start**. After 5 pieces you will know which dimensions simply do not apply to your form (you can drop or replace them at bump time).

---

## The 7 dimensions (**generic definitions; adjust your understanding to fit your content form**)

### ER — Emotional Resonance
*Can your content make the audience feel a **concrete, nameable** emotion?*

- **0** — Pure information transfer; no emotional hook
- **3** — Ordinary resonance
- **5** — Sharp, specific self-recognition that people are reluctant to admit

### HP — Hook Potential
*Can the opening force the audience to keep consuming?*

- **0** — Generic opening
- **3** — A concrete promise or counterintuitive assertion
- **5** — A concrete, vivid scene / image / question the audience cannot stop processing

### QL — Quotable Lines (spread density)
*Does the content contain at least 2-3 elements that can be clipped and spread as standalone fragments?*

- **0** — All narration / stream-of-consciousness content
- **3** — One fragment worth spreading
- **5** — Multiple independently spreadable fragments, distributed across different parts of the content

### NA — Narrativity (structure arc)
*Is there a recognizable arc, or flat exposition?*

- **0** — No structure / list-like
- **3** — A loose throughline
- **5** — A tight arc structure

### AB — Audience Breadth
*How broad is the potential audience for this issue / topic?*

- **0** — Very niche
- **3** — Medium
- **5** — Universal

### SR — Social Resonance
*Does the content touch a current social pattern?*

- **0** — Purely personal / purely technical
- **3** — Touches a recognized phenomenon but adds no new perspective
- **5** — Names a structural pattern the audience recognizes but has no language for

### SAT — Satire Depth (irony / style depth)
*How much "device" is there at the tone and form level?*

- **0** — Sincere direct statement
- **3** — One layer of irony / a deliberate style choice
- **5** — Nested irony / parody / self-reference

If SAT does not apply to your content form, give 2-3 as a placeholder and consider replacing it with a more relevant dimension at bump time.

---

## Bucket prediction: ratio bucket scheme

> ⚠️ **A newcomer's buckets cannot use absolute numbers** — baselines differ enormously across platforms and content forms.

### Piece 1: platform-generic defaults

Since the content form is unknown, use the most conservative generic prior:

| Bucket | Range (core metric count) | Prior probability |
|---|---|---|
| Floor | < platform new-account P25 | 30% |
| Base | P25 - P50 | 40% |
| Hit | P50 - P90 | 20% |
| Small hit | P90 - P99 | 8% |
| Big hit | > P99 | 2% |

> The "core metric" depends on the platform: plays, reads, interactions, downloads, saves... **decide which metric you use at piece 1**.

### From piece 2 on: use ratio buckets

`baseline = the previous piece's actual core metric` (or the median of the last 3).

| Bucket | Multiple range | Meaning |
|---|---|---|
| Regression | < 0.3 × baseline | Clear decline |
| Flat | 0.3 - 1 × baseline | Same tier |
| Hit | 1 - 3 × baseline | Moderate breakthrough |
| Small hit | 3 - 10 × baseline | Significant breakout |
| Big hit | > 10 × baseline | Order-of-magnitude leap |

After the 5th piece, run `/cheat-bump --bucket-only` to recalibrate the boundaries.

---

## Cold-start strategy (short version)

The "predictions" for the first 5 pieces are not predictions — they are **data collection**.

1. **Build discipline**: write a blind judgment before publishing
2. **Record 7-dimension scores**: after the retro each sample becomes a (score, actual) pair
3. **Sampling strategy**: actively pick content with the most divergent dimension combinations — make sure the 5 samples cover different dimension combinations

> **Extra advice for the generic rubric**: during the first 5 retros, besides recording the data, also record "what this dimension actually means for my content form". At bump time you may need to **redefine the dimensions**, not just tune the weights.

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Nothing |
| N=3-5 | Trust the direction of "which dimension may matter" |
| N=5-10 | Trust bucket ordering |
| N=10-20 | The center is trustworthy to ±30% |
| N≥20 | The rubric truly becomes a "cheat code" |

---

## Important warnings

- **This is a generic rubric** — the dimension definitions may seriously mismatch your content form. **Use it to collect data, not to make decisions**
- Cold-start composites have low confidence — **do not decide whether to publish a piece based on a v0 score**
- The first 5 pieces **must each complete the full loop** (predict → publish → retro); skipping any retro = the whole calibration fails
- After the 5th piece you **must** run `/cheat-bump` to upgrade — **the generic rubric especially needs a bump**, because the dimensions themselves may need replacing

---

## The most important sentence

**For the first 5 pieces you are not making decisions; you are collecting data.** The value of the generic rubric is not how accurate its dimension definitions are — it is that it forces you to build the predict-retro loop habit. At the 5th-piece bump, be bold about redefining the dimensions.
