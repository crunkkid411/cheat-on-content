# Starter Rubric: long essay (WeChat Official Account / Substack / Medium) — v0 cold-start placeholder

**This is a placeholder rubric for new writers with absolutely no data.** It will score things wrong. **Prediction accuracy for the first 5 pieces is roughly ±50% — that is a mathematical fact of cold-start, not a rubric failure.**

After running 5 pieces (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you will have your first personal calibration data and can propose the first `/cheat-bump` to v1 (or directly adopt a stable rubric of the same form as a starting point and re-calibrate the weights).

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is an integer 0-5. The composite range is 0-10.

**Why equal weights**: you have no data supporting any particular weight. Equal weights let you give each dimension "neutral attention" before the data arrives. After the 5th piece your retro data will tell you which dimensions actually predict spread on your account.

---

## The 7 dimensions

### ER — Emotional Resonance
*Can the article make the reader feel a **concrete, nameable** emotion in some passage?*

- **0** — Pure knowledge / information transfer; no emotional layer
- **3** — Resonates but stays at the level of "everyone says this"
- **5** — Sharp, specific, makes the reader screenshot it and post it with "this is me"

### HP — Hook Potential
*Can the title + first paragraph make someone stop in the feed, click, and finish the first three paragraphs?*

- **0** — Generic title ("Some thoughts on XX")
- **3** — A concrete promise or counterintuitive argument; the title sparks curiosity
- **5** — The title is itself ammunition for the argument, and the first paragraph delivers an unsettling concrete scene

### QL — Quotable Lines
*Are there at least 2-3 sentences in the article that can be screenshotted and stand alone outside the original?*

- **0** — All argumentation, no extractable single sentence
- **3** — One summary quotable line at the end
- **5** — Multiple independently spreadable sentences, scattered across different paragraphs

### NA — Narrativity
*Does the article have a recognizable structural arc, or a flat pile of arguments?*

- **0** — List / checklist style; the reader can close it at any point in the middle
- **3** — A loose throughline but the middle can be skimmed
- **5** — A tight arc (suspense → turn → landing) that the reader must finish

### AB — Audience Breadth
*How broad is the topic's potential readership?*

- **0** — Very niche industry / circle
- **3** — Medium — a specific group (e.g. office workers / parents / founders)
- **5** — Universal emotion / social issue that almost anyone can relate to

### SR — Social Resonance
*Does the article touch a current social pattern or collective mood?*

- **0** — Purely personal experience / technical detail
- **3** — Touches a recognized phenomenon but adds no new perspective
- **5** — Names a structural pattern readers recognize but lack language for

### SAT — Satire Depth (irony / style depth)
*How much "device" is there at the stylistic level — irony, parody, stylistic experiment?*

- **0** — Sincere direct statement (the normal state of most long essays)
- **3** — One layer of irony or a deliberate stylistic choice
- **5** — Nested irony / parody / self-reference

Long essays usually take a sincere route. If your writing style is direct, give SAT 2-3 as a placeholder.

---

## Bucket prediction: ratio bucket scheme

> ⚠️ **A newcomer's buckets cannot use absolute numbers** — the reference creator's "100k reads is the floor" is a "phenomenal hit" for a 0-follower new account.

### Piece 1: platform-generic defaults

The typical distribution for a new account's first post on WeChat Official Account / Substack / Medium:

| Bucket | Range (reads) | Prior probability |
|---|---|---|
| Floor | < 50 | 30% |
| Base | 50 - 500 | 40% |
| Hit | 500 - 5,000 | 20% |
| Small hit | 5,000 - 50,000 | 8% |
| Big hit | > 50,000 | 2% |

### From piece 2 on: use ratio buckets

`baseline = the previous piece's actual reads` (or the median of the last 3).

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
3. **Sampling strategy**: actively pick drafts with the most divergent dimension combinations — 1 ER-dominant, 1 SR-dominant, 1 QL-dominant, 1 narrative experiment, 1 medium all-round

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Nothing |
| N=3-5 | Trust the direction of "which dimension may matter" |
| N=5-10 | Trust bucket ordering |
| N=10-20 | The center is trustworthy to ±30% |
| N≥20 | The rubric truly becomes a "cheat code" |

---

## Important warnings

- Cold-start composites have low confidence — **do not decide whether to publish an article based on a v0 score**
- The first 5 pieces **must each complete the full loop** (predict → publish → retro); skipping any retro = the whole calibration fails
- After the 5th piece you **must** run `/cheat-bump` to upgrade

---

## The most important sentence

**For the first 5 pieces you are not making decisions; you are collecting data.** The biggest temptation during cold-start is seeing composite 8.4 and thinking this one will blow up — do not believe it.
