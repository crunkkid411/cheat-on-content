# Starter Rubric: short text (X / Weibo / Jike threads) — v0 cold-start placeholder

**This is a placeholder rubric for new writers with absolutely no data.** It will score things wrong. **Prediction accuracy for the first 5 posts is roughly ±50% — that is a mathematical fact of cold-start, not a rubric failure.**

After running 5 posts (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you will have your first personal calibration data and can propose the first `/cheat-bump` to v1.

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is an integer 0-5. The composite range is 0-10.

**Why equal weights**: you have no data supporting any particular weight. Equal weights let you give each dimension "neutral attention" before the data arrives. After the 5th post your retro data will tell you which dimensions actually predict spread on your account.

---

## The 7 dimensions

### ER — Emotional Resonance
*Can this post make someone feel a **concrete, nameable** emotion in the instant they scroll past?*

- **0** — Pure information / notification content
- **3** — Resonates but not sharply enough — "yeah, true" and then they scroll on
- **5** — Hits on the first try; after reading they cannot help reposting or screenshotting

### HP — Hook Potential
*Can the first line stop the thumb?*

A short post's hook is its first line — it must compete for attention with a hundred feed items.

- **0** — Generic opening ("today I want to talk about...")
- **3** — A counterintuitive assertion or a concrete number
- **5** — The first sentence is itself a complete, impossible-to-ignore opinion bomb

### QL — Quotable Lines (spread density)
*Can one sentence from this post be screenshotted and spread on its own?*

The whole short post is the vehicle for the "quotable line" — but real QL means: will the reader **screenshot just one sentence** and post it on another platform?

- **0** — The whole post is narration / a diary; no independently spreadable sentence
- **3** — The post as a unit is spreadable
- **5** — One sentence can detonate independently outside its context

### NA — Narrativity (thread arc)
*If it is a thread / consecutive Weibo posts, is there an arc that makes people want to scroll to the last one?*

- **0** — A single post with no arc (normal) / a thread where each post is an independent fragment
- **3** — The thread has a loose throughline
- **5** — The thread has "binge-watch feel" — you must see the last post

For a single post, NA is usually 1-2 — short-text spread relies mainly on ER/HP/QL.

### AB — Audience Breadth
*How broad is the potential audience for this topic?*

- **0** — Very niche circle meme
- **3** — A specific group (office workers / internet industry / parents)
- **5** — Universal — anyone who reads it feels something

### SR — Social Resonance
*Does this post touch the current collective mood or social pattern?*

- **0** — Purely personal / talking to yourself
- **3** — Rides a trend but adds no new perspective
- **5** — Names, in 280 characters, a structure everyone feels but nobody has said

### SAT — Satire Depth (irony / tone depth)
*How much "device" is in the tone — passive aggression, irony, parody?*

- **0** — Sincere direct statement
- **3** — One layer of passive aggression / irony
- **5** — Nested irony / self-reference — "a post satirizing satire"

On short-text platforms, satire / passive aggression is a spread weapon. If your style is sincere, give SAT 2-3 as a placeholder.

---

## Bucket prediction: ratio bucket scheme

> ⚠️ **A newcomer's buckets cannot use absolute numbers** — a big-V's "1,000 reposts means a fall from grace" is dream data for a new account.

### Post 1: platform-generic defaults

The typical distribution for a new account's first post on X / Weibo / Jike:

| Bucket | Range (impressions / interactions) | Prior probability |
|---|---|---|
| Floor | < 50 impressions | 30% |
| Base | 50 - 500 impressions | 40% |
| Hit | 500 - 5,000 impressions | 20% |
| Small hit | 5,000 - 50,000 impressions | 8% |
| Big hit | > 50,000 impressions | 2% |

> Jike uses interactions (likes + comments) as its main metric and impression data is opaque — use the interaction count instead.

### From post 2 on: use ratio buckets

`baseline = the previous post's actual impressions / interactions` (or the median of the last 3).

| Bucket | Multiple range | Meaning |
|---|---|---|
| Regression | < 0.3 × baseline | Clear decline |
| Flat | 0.3 - 1 × baseline | Same tier |
| Hit | 1 - 3 × baseline | Moderate breakthrough |
| Small hit | 3 - 10 × baseline | Significant breakout |
| Big hit | > 10 × baseline | Order-of-magnitude leap |

After the 5th post, run `/cheat-bump --bucket-only` to recalibrate the boundaries.

---

## Cold-start strategy (short version)

The "predictions" for the first 5 posts are not predictions — they are **data collection**.

1. **Build discipline**: write a blind judgment before publishing
2. **Record 7-dimension scores**: after the retro each sample becomes a (score, actual) pair
3. **Sampling strategy**: actively pick posts with the most divergent dimension combinations — 1 ER-dominant, 1 SR-dominant, 1 SAT-dominant (snarky), 1 with an extremely strong HP but ordinary content, 1 medium all-round

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Nothing |
| N=3-5 | Trust the direction of "which dimension may matter" |
| N=5-10 | Trust bucket ordering |
| N=10-20 | The center is trustworthy to ±30% |
| N≥20 | The rubric truly becomes a "cheat code" |

---

## Important warnings

- Cold-start composites have low confidence — **do not decide whether to publish a post based on a v0 score**
- Short-text publishing is frequent — 5 calibrations can be done in 1-2 weeks, **do not drag it out**
- The first 5 posts **must each complete the full loop** (predict → publish → retro); skipping any retro = the whole calibration fails
- After the 5th post you **must** run `/cheat-bump` to upgrade

---

## The most important sentence

**For the first 5 posts you are not making decisions; you are collecting data.** The advantage of short text is fast iteration — do not waste that advantage.
