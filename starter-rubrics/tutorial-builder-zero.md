# Starter Rubric: tutorial / how-to content — v0 cold-start placeholder

**This is a placeholder rubric for new creators with absolutely no data.** It will score things wrong. **Prediction accuracy for the first 5 pieces is roughly ±50% — that is a mathematical fact of cold-start, not a rubric failure.**

After running 5 pieces (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you will have your first personal calibration data and can propose the first `/cheat-bump` to v1.

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is an integer 0-5. The composite range is 0-10.

**Why equal weights**: you have no data supporting any particular weight. Equal weights let you give each dimension "neutral attention" before the data arrives. After the 5th piece your retro data will tell you which dimensions actually predict spread for your tutorials.

---

## The 7 dimensions

### ER — Emotional Resonance (the "aha" moment)
*After following the tutorial, can the reader / viewer have the **"it's this simple" or "I finally get it"** epiphany?*

A tutorial's emotional resonance is not tear-jerking — it is the satisfaction and sense of control that comes from a cognitive breakthrough.

- **0** — Pure step transfer; they followed it but never felt "I understand"
- **3** — Solves the problem, but in a bland way that lacks insight
- **5** — The tutorial itself reveals a deeper principle; the reader not only learns "how" but understands "why"

### HP — Hook Potential (problem-statement clarity)
*Can the opening make readers confirm within 10 seconds "this is the problem I want to solve"?*

A tutorial's hook = a precise problem description. When readers find your tutorial via search, the opening must make them confirm "I found the right one".

- **0** — Vague title ("Python study notes"); the opening introduces the history of the technology
- **3** — Clear problem description but lacks "pain-point resonance" ("This article explains how to...")
- **5** — The opening is the reader's specific pain-point scene ("It runs fine locally, but as soon as you deploy to the server it throws an error...")

### QL — Quotable Lines (copyable-content density)
*Does the tutorial contain code snippets, commands, configs, or step lists that can be **copy-pasted directly**?*

A tutorial's "quotable lines" are directly reusable content fragments — the core reason readers bookmark a tutorial.

- **0** — All conceptual explanation; nothing directly usable
- **3** — Code / steps are present but need heavy modification to use
- **5** — Multiple directly copyable code snippets / commands / config templates, with clear comments

### NA — Narrativity (tutorial progression)
*Does the tutorial have a clear easy-to-hard progression arc?*

- **0** — No logical relationship between steps; can be read in random order
- **3** — A linear order but lacks the explanation of "why this step is here"
- **5** — Explicit progression (get the minimal example running → add features step by step → handle edge cases); readers can feel their ability growing

### AB — Audience Breadth (problem universality)
*How many people encounter the problem this tutorial solves?*

- **0** — Very niche tool / very special scenario
- **3** — A common problem in a specific tech stack (e.g. deployment issues with a framework)
- **5** — A problem almost everyone in the same field encounters (e.g. Git merge conflicts, environment setup)

### SR — Social Resonance (tech-trend resonance)
*Is this tutorial's topic related to current tech trends / industry hot spots?*

- **0** — Outdated technology / purely classic content
- **3** — A routine tutorial for a stable tech stack
- **5** — A technology at the center of the moment (e.g. the current AI toolchain) — search volume is surging

### SAT — Satire Depth (teaching personality)
*To what extent does the tutorial "speak human" and show personality?*

A tutorial's "satire depth" is not satire — it is **teaching personality**: are you a warm human teaching, or a document outputting?

- **0** — Pure document style; no personality at all
- **3** — Natural colloquial expression / occasional rant ("this API design really is inhuman")
- **5** — A distinct teaching personality — humor, self-deprecation, real anger at pitfalls — readers follow you "because they like your style"

If your tutorials take a rigorous technical-documentation route, give SAT 2-3 as a placeholder.

---

## Bucket prediction: ratio bucket scheme

> ⚠️ **A newcomer's buckets cannot use absolute numbers** — a top tech blogger's "10k reads is normal" does not apply to a new account.

### Piece 1: platform-generic defaults

The typical distribution for a new account's first post on a tech blog / Juejin / CSDN / Dev.to / a YouTube tutorial channel:

| Bucket | Range (reads / plays) | Prior probability |
|---|---|---|
| Floor | < 50 | 25% |
| Base | 50 - 500 | 40% |
| Hit | 500 - 5,000 | 25% |
| Small hit | 5,000 - 50,000 | 8% |
| Big hit | > 50,000 | 2% |

> Tutorial content has a long tail — search traffic continues for 1-6 months after publishing. For bucket evaluation, do the first one 30 days after publishing.

### From piece 2 on: use ratio buckets

`baseline = the previous piece's actual reads 30 days after publishing` (or the median of the last 3).

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
3. **Sampling strategy**: actively pick tutorials with the most divergent dimension combinations — 1 deep principle piece (ER-dominant), 1 hot-tool quickstart (SR-dominant), 1 code-snippet collection (QL-dominant), 1 full project walkthrough (NA-dominant), 1 medium all-round

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Nothing |
| N=3-5 | Trust the direction of "which dimension may matter" |
| N=5-10 | Trust bucket ordering |
| N=10-20 | The center is trustworthy to ±30% |
| N≥20 | The rubric truly becomes a "cheat code" |

---

## Important warnings

- Cold-start composites have low confidence — **do not decide whether to publish a tutorial based on a v0 score**
- Tutorials have long-tail traffic — do the retro 30 days after publishing; do not conclude from Day 1 data
- The first 5 pieces **must each complete the full loop** (predict → publish → retro); skipping any retro = the whole calibration fails
- After the 5th piece you **must** run `/cheat-bump` to upgrade

---

## The most important sentence

**For the first 5 pieces you are not making decisions; you are collecting data.** The long-tail nature of tutorials means you need more patience — give each piece enough of a time window before the retro.
