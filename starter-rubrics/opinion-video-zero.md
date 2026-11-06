# Starter Rubric: opinion video — v0 cold-start placeholder

**This is a placeholder rubric for new creators with absolutely no data.** It will score things wrong. **Prediction accuracy for the first 5 pieces is roughly ±50% — that is a mathematical fact of cold-start, not a rubric failure.**

After running 5 pieces (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you will have your first personal calibration data and can propose the first `/cheat-bump` to v1 (or directly adopt the v2 in [opinion-video.md](opinion-video.md) as a starting point and re-calibrate the weights).

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is an integer 0-5. The composite range is 0-10.

**Why equal weights instead of v2's differentiated weights**:
- You **have no data** supporting any particular weight
- Starting from v2's weights would make you think those weights are universal — they are not; they were fitted on the reference creator's account
- Equal weights let you give each dimension "neutral attention" before the data arrives
- After the 5th piece, your retro data will tell you which dimensions actually predict spread on your account

---

## The 7 dimensions

### ER — Emotional Resonance
*Can the draft make the audience feel a **concrete, nameable** emotion within the first 30 seconds?*

- **0** — Pure information transfer; no emotional hook
- **3** — Ordinary resonance
- **5** — Sharp, specific self-recognition that people are reluctant to admit

### HP — Hook Potential
*Can the first 3 seconds force the audience to keep watching for 30 seconds?*

- **0** — Generic opening ("hello everyone...")
- **3** — A concrete promise or counterintuitive assertion
- **5** — A concrete, vivid scene the audience cannot stop processing

### QL — Quotable Lines
*Are there at least 2-3 lines in the draft that can be screenshotted and spread as standalone text?*

- **0** — All narration
- **3** — One memorable line at the end
- **5** — Multiple independently usable lines, distributed across different parts of the draft

### NA — Narrativity
*Is there a recognizable arc, or is it flat exposition?*

- **0** — List-like
- **3** — A loose throughline
- **5** — A tight three-act structure

### AB — Audience Breadth
*How broad is the potential audience for this topic?*

- **0** — Very niche
- **3** — Medium
- **5** — Universal

### SR — Social Resonance
*Does the draft touch a current social pattern?*

- **0** — Purely personal / interpersonal
- **3** — Touches a recognized phenomenon but adds no new perspective
- **5** — Names a structural pattern the audience recognizes but has no language for

### SAT — Satire Depth
*Does the draft use multi-layered irony / parody format?*

- **0** — Sincere direct statement
- **3** — One layer of irony
- **5** — Nested or self-referential irony

If your channel takes a sincere route, give SAT 3 as a placeholder.

---

## Bucket prediction: unified format at every stage + progressive confidence labeling

> Poor prediction accuracy early on is a mathematical fact — **do not solve it by omitting buckets**; express uncertainty honestly through the **header's confidence level + a flatter probability distribution**. See [shared-references/prediction-anatomy.md](../shared-references/prediction-anatomy.md) and [the confidence table in state-management.md](../shared-references/state-management.md).
>
> When calibration_samples is small, the probability distribution **should be flatter** (e.g. 30/30/20/15/5 rather than 5/40/45/8/2) — **that is how you honestly express uncertainty**, not by skipping buckets.

## Ratio bucket scheme (applies at every stage)

> ⚠️ **A newcomer's buckets cannot use absolute numbers** — the reference creator's "50k is the floor" is a "phenomenal hit" for a 0-follower newcomer.
> If you copy absolute-number buckets, every one of your videos will land in "the bottom 99%", and buckets lose all ordering meaning.
>
> **Ratio buckets** split by "the multiple relative to your own previous piece". They always apply, no matter how big your account is.

### Piece 1: use platform-generic defaults (you have no "previous piece" yet)

The typical distribution for a 0-follower newcomer's first video on Douyin / Bilibili / TikTok / YouTube:

| Bucket | Range (**actual play count, not ten-thousands**) | Meaning | Prior probability |
|---|---|---|---|
| Floor | < 100 | Almost buried by the algorithm | 30% |
| Base | 100 - 1,000 | Small recommendation supported by completion rate | 40% |
| Hit | 1,000 - 10,000 | The first signal of breaking out | 20% |
| Small hit | 10,000 - 100,000 | Extremely rare "zero-follower first hit" | 8% |
| Big hit | > 100,000 | Abnormal algorithmic weighting | 2% |

> For WeChat Official Account / Substack, replace "plays" with "reads"; the magnitudes are similar (50-500 reads for a 0-follower account's first post is normal).

**When predicting piece 1**: pick a bucket + write the probability distribution. **It will very likely land in "Base"** — that is a mathematical fact, not your failure.

### From piece 2 on: use ratio buckets

Let `baseline = the previous piece's actual plays` (or the median of the last 3, if available).

| Bucket | Multiple range | Meaning |
|---|---|---|
| Regression | < 0.3 × baseline | Clearly worse than the previous piece |
| Flat | 0.3 - 1 × baseline | Same tier as the previous piece |
| Hit | 1 - 3 × baseline | Moderate breakthrough |
| Small hit | 3 - 10 × baseline | Significant breakout |
| Big hit | > 10 × baseline | Order-of-magnitude leap |

**Benefits of ratio buckets**:
- 100 → 1,000 plays (10x) and 50k → 500k plays (10x) are **the same achievement** — ratio buckets both mark them "Big hit"
- As your account grows from 0 to 100k followers, the bucket boundaries rise with it automatically
- No need to ask "should I flatter this number today" — the multiple is absolute

**Example**:
- Piece 1 got 480 plays (landed "Base") → baseline = 480
- Piece 2 predicted bucket = "Hit" (500-1,500), actual 1,200 → Hit
- Piece 3 baseline rolls forward = (480 + 1,200) / 2 = 840

### After piece 5: recommend fixed absolute buckets coexisting with ratio buckets

After 5 pieces, your baseline has stabilized from 5 data points. `/cheat-status` proactively suggests:

> You have calibrated 5 pieces; you can now fix absolute bucket boundaries based on your actual distribution.
> Run `/cheat-bump --bucket-only` to derive them automatically.

After fixing, absolute buckets are for "long-term trend identification" (is this piece better than last month's?), and ratio buckets are for "recent fluctuation" (is this piece better than the previous one?).

### After N≥10: you can switch to percentile buckets

When the calibration pool is ≥10, switch bucket boundaries to percentiles: your top 20% of videos are "breakouts", 10-20% are "hits", and 30-70% are "base". This scheme is always self-consistent — no matter how big the account, "top 20%" has a stable meaning.

---

**Important warnings**:
- The placeholder probabilities above are "priors when you know nothing" — your real distribution will emerge after the 5th piece
- In pieces 1-5 your judgment of your own bucket boundaries **will fluctuate heavily** — this is the normal cold-start state
- After the 5th piece you **must** run `/cheat-bump --bucket-only` to recalibrate

---

## Cold-start strategy (**required reading, the most overlooked section**)

A "prediction" during cold-start is not a prediction — it is **data collection**. Understanding this is the watershed for whether the tool is useful to you.

### What your predictions do in the first 5 pieces

1. **Build discipline**: write a blind judgment before seeing any data. That is the spine — not the numbers themselves
2. **Record 7-dimension scores**: after the retro each sample becomes a (score, actual) pair; by the 5th piece these pairs are the input to the rubric's first upgrade
3. **Record anchor hypotheses**: write hypotheses such as "I bet ER=5 gets more traffic than ER=3", validate them in retros → evidence for rubric upgrades

**What you should not do**: decide whether to publish a draft based on a cold-start composite. **Accuracy is ±50% — the decision is meaningless**. If you have already decided to publish, run the full loop; if you are still hesitating, use your own feel.

### Sampling strategy for the first 5 pieces: **actively pick the most divergent drafts**

If your first 5 pieces are all the same `ER=5 / SR=2 / HP=5` type, during retro **you cannot** tell which dimension actually predicted traffic — multicollinearity.

**Counterintuitive but correct approach**: during cold-start, actively pick samples with the most divergent dimension combinations:
- 1 ER-dominant piece (emotional, low SR)
- 1 SR-dominant piece (social-issue, low ER)
- 1 SAT-dominant piece (satirical)
- 1 QL-dominant piece (dense quotable lines)
- 1 medium all-round piece (all 3-4)

If you only have "safe same-type drafts", pick the 5 most divergent. **In the stable stage, pursue "publish only hits"; in cold-start, pursue "maximum information".**

### When to start trusting predictions

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Nothing. Buckets are placeholders |
| N=3-5 | Trust the direction of "which dimension may matter"; do not trust specific composite numbers |
| N=5-10 | Trust bucket ordering; do not trust the center point estimate |
| N=10-20 | The center is trustworthy to ±30%; usable as one decision reference |
| N≥20 | The rubric truly becomes a "cheat code" — but by then you have also developed your own content intuition |

**The real gift of cold-start is not prediction accuracy — it is the retro habit it forces you to build**. By the time that habit carries you to N=20, your content intuition itself will be much stronger.

---

## Retro discipline during cold-start (**stricter than the stable stage**)

Run the full loop for each of the first 5 pieces. **Skipping even one retro → the whole calibration fails**.

The minimum information to fill in for every retro:
- Actual plays / reads
- Actual like count (look at like/play ratio)
- Actual comment count (look at interaction)
- Top 3 comments + like counts (look at where the audience actually received it)
- My v0 prediction vs actual: which dimension was validated / refuted

After 5 pieces you will see at least one pattern — e.g. "my ER is always overestimated" or "my SR dimension does not predict anything" — that pattern is the evidence for your first bump.

---

## Upgrade options from piece 6

After 5 calibrations you have 3 paths:

### Path A: v0 → v1 (fit your own weights)
Run `/cheat-bump --propose "<your specific weight adjustments>"`. The system enforces a full re-score + cross-model audit.

### Path B: directly adopt v2 as a starting point
Copy the v2 formula from [opinion-video.md](opinion-video.md) into your `rubric_notes.md`, **then run `/cheat-bump`** — the bump process uses your 5 pieces of data to validate whether v2 really is better on your account.

### Path C: keep v0 equal-weight and run more samples
If 5 pieces still show no clear pattern, run 5 more. Equal-weight v0 is not embarrassing before 10-15 samples.

---

## What this rubric cannot do

- **It cannot tell you "whether it will blow up"** — cold-start prediction confidence is low; buckets should usually be given 30%-50%, not ≥80%
- **It cannot set bucket boundaries for you** — platform / account differences are too large
- **It cannot transfer across accounts** — the same v0 rubric fits different v1s on different people's accounts

---

## The most important sentence

**For the first 5 pieces you are not making decisions; you are collecting data.**

The biggest temptation during cold-start is "seeing composite 8.4 and thinking this one will blow up". **Do not believe it**. 8.4 is computed against a rubric that has not been calibrated yet — it means almost nothing for your account. Start trusting the numbers after the 5th piece.
