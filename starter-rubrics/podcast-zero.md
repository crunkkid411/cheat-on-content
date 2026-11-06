# Starter Rubric: podcast / long video — v0 cold-start placeholder

**This is a placeholder rubric for new hosts with absolutely no data.** It will score things wrong. **Prediction accuracy for the first 5 episodes is roughly ±50% — that is a mathematical fact of cold-start, not a rubric failure.**

After running 5 episodes (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you will have your first personal calibration data and can propose the first `/cheat-bump` to v1.

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is an integer 0-5. The composite range is 0-10.

**Why equal weights**: you have no data supporting any particular weight. Equal weights let you give each dimension "neutral attention" before the data arrives. After the 5th episode your retro data will tell you which dimensions actually predict spread for your show.

---

## The 7 dimensions

### ER — Emotional Resonance
*Can this episode make the listener feel a **concrete, nameable** emotion at some moment?*

Podcast emotional resonance usually comes from a real moment with the guest / host — a sudden silence, a change in voice, a truth said before it was ready.

- **0** — Information transfer throughout; sounds like reading a script
- **3** — Resonates but stays at "nice chat"
- **5** — At least one moment that makes people take off their headphones and pause

### HP — Hook Potential
*Can the first 60 seconds make the listener decide to finish this episode?*

A podcast's competitors are "skip to the next episode" / "open the music app". The first 60 seconds decide retention.

- **0** — "Hello everyone, welcome to episode N, today we'll talk about..."
- **3** — The opening gives a concrete promise or throws out a counterintuitive question
- **5** — The first 60 seconds go straight into a concrete, vivid scene or argument that makes people want to know what happens next

### QL — Quotable Lines (clippable quotables)
*Are there 2-3 segments worth making into clips / short videos?*

A podcast's secondary spread relies mainly on short-video clips and text excerpts. QL measures "the density of segments that can be cut out and spread independently".

- **0** — Chitchat throughout; no independently spreadable segment
- **3** — One highlight segment worth clipping
- **5** — Multiple clippable segments distributed across different parts of the episode; the text version also has screenshot-worthy sentences

### NA — Narrativity (episode arc)
*Does this episode have an overall arc that makes people want to listen to the end?*

- **0** — Topics jump randomly; quitting midway does not affect comprehension
- **3** — A loose throughline but the middle can be skipped
- **5** — A tight arc — suspense, a turn, a landing; quitting midway feels like "not finishing"

### AB — Audience Breadth
*How broad is the potential listener group for this episode's topic?*

- **0** — Very niche field / requires a lot of prior knowledge
- **3** — A specific group (founders / people in an industry / a hobby circle)
- **5** — Universal topic — anyone can relate (relationships, anxiety, choices, growth)

### SR — Social Resonance
*Does this episode touch the current social pattern or collective mood?*

- **0** — Purely personal experience / technical detail
- **3** — Touches a recognized phenomenon but adds no new perspective
- **5** — The conversation names a structural pattern listeners feel but have not heard anyone say

### SAT — Satire Depth (humor / irony depth)
*How many layers of humor and irony does this episode's conversation have?*

- **0** — Serious and straight; no humor
- **3** — Natural humor / one layer of banter
- **5** — Multi-layered irony, "bits" produced by guest chemistry, spreadable memes

Podcast humor usually emerges naturally rather than being designed. If your show takes a serious, in-depth route, give SAT 2-3 as a placeholder.

---

## Bucket prediction: ratio bucket scheme

> ⚠️ **A newcomer's buckets cannot use absolute numbers** — a top podcast's "50k plays is the floor" is dream data for a new show.

### Episode 1: platform-generic defaults

The typical distribution for a new podcast's first episode on Xiaoyuzhou / Apple Podcasts / Spotify / YouTube:

| Bucket | Range (plays / listens) | Prior probability |
|---|---|---|
| Floor | < 30 | 30% |
| Base | 30 - 300 | 40% |
| Hit | 300 - 3,000 | 20% |
| Small hit | 3,000 - 30,000 | 8% |
| Big hit | > 30,000 | 2% |

> YouTube long videos use plays; pure audio platforms use listens.

### From episode 2 on: use ratio buckets

`baseline = the previous episode's actual plays` (or the median of the last 3).

| Bucket | Multiple range | Meaning |
|---|---|---|
| Regression | < 0.3 × baseline | Clear decline |
| Flat | 0.3 - 1 × baseline | Same tier |
| Hit | 1 - 3 × baseline | Moderate breakthrough |
| Small hit | 3 - 10 × baseline | Significant breakout |
| Big hit | > 10 × baseline | Order-of-magnitude leap |

After the 5th episode, run `/cheat-bump --bucket-only` to recalibrate the boundaries.

---

## Cold-start strategy (short version)

The "predictions" for the first 5 episodes are not predictions — they are **data collection**.

1. **Build discipline**: write a blind judgment from the outline before recording (a podcast cannot fully predict where the conversation goes, but an outline-level assessment is still valuable)
2. **Record 7-dimension scores**: after the retro each episode sample becomes a (score, actual) pair
3. **Sampling strategy**: actively pick episodes with the most divergent dimension combinations — 1 deep interview (ER-dominant), 1 current-events commentary (SR-dominant), 1 light chat (SAT-dominant), 1 dense practical content (QL-dominant), 1 medium all-round

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Nothing |
| N=3-5 | Trust the direction of "which dimension may matter" |
| N=5-10 | Trust bucket ordering |
| N=10-20 | The center is trustworthy to ±30% |
| N≥20 | The rubric truly becomes a "cheat code" |

---

## Important warnings

- Cold-start composites have low confidence — **do not decide whether to record an episode based on a v0 score**
- Podcast production cycles are long — 5 calibrations may take 1-3 months, **stick with the full loop**
- The first 5 episodes **must each complete the full loop** (predict → publish → retro); skipping any retro = the whole calibration fails
- After the 5th episode you **must** run `/cheat-bump` to upgrade

---

## The most important sentence

**For the first 5 episodes you are not making decisions; you are collecting data.** Podcasts iterate slowly, so value each episode's calibration value even more — do not skip the retro.
