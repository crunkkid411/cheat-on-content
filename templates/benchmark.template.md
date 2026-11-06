# Benchmark account: [BENCHMARK-NAME]

> **This file is created and maintained by `/cheat-learn-from`.**
>
> The rubric / patterns / topic-direction sense of the early tool are **heavily** inferred from here — this is the anchor you have before you have your own historical data right after init.
>
> Once you accumulate N≥10 calibration samples of your own, the benchmark's influence **fades naturally** — your real data becomes the primary signal source. But the benchmark is not deleted; it is kept as a sanity check (to see whether your account really drifts away from the benchmark's direction).
>
> At any time you can:
> - **Append** benchmark videos: `/cheat-learn-from --append <new-videos>`
> - **Replace** the benchmark account: `/cheat-learn-from --replace <new-account>`

---

## Account info

- **Name**: [benchmark account name]
- **Platform**: [Douyin / Bilibili / YouTube / WeChat Official Account / ...]
- **URL**: [account homepage]
- **Follower tier**: [supplied by the user, for reference — e.g. "10k / 100k / 1M"]
- **Style / tone**: [user description — e.g. "knowledge explainer / academic parody" / "personal rant" / "technical tutorial"]
- **Imported at**: [YYYY-MM-DD]
- **Sample count**: N

---

## Imported samples

| # | Video title | Plays | Likes | Comments | Shares | Your impression | transcript |
|---|---|---|---|---|---|---|---|
| 1 | [example] How to stop expecting | 710k | 24k | 899 | 18k | high | samples/[BENCHMARK-NAME]/ab61ed09/transcript.md |
| 2 | [example] Boss nonsense | 390k | 12k | 567 | 7.9k | medium | samples/[BENCHMARK-NAME]/5fe5d869/transcript.md |
| 3 | [example] Who asked you | 110k | 3.8k | 198 | 2.7k | low | samples/[BENCHMARK-NAME]/8b5627e6/transcript.md |

> **Impression tier**: high / medium / low is your **subjective** judgment after watching the video of "is this a representative work of this account" — not data-driven, but intuition. This judgment tells Claude more about the style you want to make than the data does.

---

## Basic rubric derivation (one-off at init, **qualitative direction only**)

> Based on observations of N benchmark samples, Claude summarizes which dimensions appear related to "high performance" and which do not.
> **Do not give numeric weights directly** — fitting numbers on 5-10 samples easily overfits. Direction is enough; the user decides whether to adjust weights in rubric_notes.md.

### Dimensions shared by high-performing samples (look important)

- [example] **ER (emotional resonance) high**: 3/3 high-performing samples have a strong emotional anchor
- [example] **QL (quotable-line density) high**: 3/3 high-performing samples have ≥2 independently shareable quotable lines
- [example] **MS (memetic shareability) high**: 3/3 high-performing samples' comment sections contain reused sentence patterns

### Dimensions shared by low-performing samples (look less important)

- [example] **SR (social relevance) not significant**: in low-performing samples even SR=4 did not save them
- [example] **NA (narrative) not significant**: no obvious NA distribution difference between high and low samples

### Claude's initial suggestion

- [example] Your benchmark account looks like an **emotional resonance + quotable lines** driven account
- Suggestion: set initial rubric weights ×1.5 on ER / QL / MS (if enabled)
- **But wait until you have run 5+ calibrations yourself before a formal bump** — 5 benchmark samples are not enough to conclude

See the "benchmark-derived initial signals" section of [rubric_notes.md](rubric_notes.md).

---

## Basic pattern derivation

See the "Borrowed from benchmark [BENCHMARK-NAME]" section of [script_patterns.md](script_patterns.md).

Mark every pattern **Imported, untested on my channel** — it may not apply to your channel; after live validation (≥2 successful runs + retro confirmation) remove that label.

---

## Topic-direction sense

> cheat-seed reads this while brainstorming — it makes proposals based on the benchmark account's topic distribution.

[example] Topic types the benchmark account often makes:
- Crushes / emotional withdrawal (~40%)
- Academic-topic parody (~30%)
- Workplace observations (~20%)
- Social-issue commentary (~10%)

> You do not have to make exactly the same topics — this is only a reference frame.
> cheat-seed Mode A/B/C still centers on what you actually want to make.

---

## Maintenance history

| Date | Operation | Details |
|---|---|---|
| YYYY-MM-DD | First import | N=3 samples, method [way a paste text / way b whisper] |

---

## When it fades out later

- When `state.calibration_samples >= 10`, cheat-status tells the user "you have enough of your own data; the benchmark is now mainly a sanity check and no longer dominant"
- But benchmark.md **is not deleted** — it remains the reference frame for cheat-seed brainstorming
- If the benchmark account's style changes / you no longer want to benchmark against it → run `/cheat-learn-from --replace <none>` to detach (history is kept in the file, but cheat-seed stops reading it)
