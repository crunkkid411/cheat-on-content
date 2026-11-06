---
name: cheat-persona
description: Derive / refresh the account's audience persona from retro comment data and write it into audience.md. This is the second derivative, parallel to the rubric — the rubric answers "how to score", the persona answers "who is watching". cheat-seed reads it when choosing topics / writing drafts. **audience.md contains actual-performance signals and is strictly off-limits to cheat-score-blind**. Triggers: "构造受众画像" / "更新 persona" / "我的观众是谁" / "build persona" / "刷新受众画像" / "看看我的受众画像".
argument-hint: "[— seed-from-benchmark] [— rebuild]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep
---

# /cheat-persona — audience persona derivation

Cluster the comment data from the retrospective sections of `predictions/*.md` into a real audience persona for the account, and write it into `audience.md`.

---

## Core positioning

The persona is the second derivative, **parallel to** the rubric, **not part of it**:

```
Retro data (comments + completion + follows)
   ├──→ rubric evolution (cheat-bump)          —— "how to score"
   └──→ audience persona (cheat-persona)       —— "who is watching"
Both feed cheat-seed, but for different purposes
```

- **rubric**: will this draft pop → feeds cheat-predict scoring
- **persona**: who will watch 3 more seconds / leave a comment / share because of this → feeds cheat-seed topic selection + draft writing

**Never mix them**: the persona does not enter the scoring formula. The rubric's AB dimension (audience breadth) may reference the persona, but that is cheat-bump's business, not this skill's.

## ⚠️ Contamination isolation (non-negotiable)

`audience.md` derives from retro comments = **it carries actual-performance signals from published work**. Therefore:

- `audience.md` is on [cheat-score-blind](../cheat-score-blind/SKILL.md)'s hard refusal list, refusal_code `blocked_audience`
- The persona influences cheat-seed's **what to write** (creative direction), not cheat-predict's **how to score** (the blind sub-agent never reads audience.md)
- This is clean: persona-shaped content goes into the final draft, and the blind sub-agent scores the draft itself — no leak. A leak would only happen if the sub-agent could read audience.md and reason "because this audience loves X, add points", and it cannot read it

## Overview

```
[User: build audience persona / update persona]
  ↓
[Phase 0: collect data — scan comment sections in predictions/*.md retros + benchmark.md]
  ↓
[Phase 1: judge data volume → derive Confidence level]
  ↓
[Phase 2: comment clustering — self-identification / emotional purpose / disagreement points / language]
  ↓
[Phase 3: persona × rubric cross-check]
  ↓
[Phase 4: write audience.md (full rebuild; header records version + last_rebuilt)]
  ↓
[Phase 5: console report + diff against the previous persona]
```

## Constants

- **AUDIENCE_PATH = audience.md** — where the audience persona is persisted
- **MIN_RETROS_FOR_DATA_GROUNDED = 3** — ≥3 retros counts as "data-grounded" (a soft judgment based on comment quality is allowed)
- **MIN_COMMENTS_PER_TRAIT = 3** — a "verified trait" needs at least 3 pieces of comment evidence; otherwise downgrade it to "hypothesized trait"
- **SEED_FROM_BENCHMARK = auto** — when there is no retro data of your own but a benchmark exists, seed an unverified persona

> 💡 Call overrides: `/cheat-persona — seed-from-benchmark` (force a benchmark seed) / `— rebuild` (rebuild even if the data has not changed)

## Inputs

| Source | Purpose |
|---|---|
| The `## Retrospective` section of `predictions/*.md` (legacy `## 复盘` is also accepted) | **Main data source** — top comments (with like counts). The persona's gold mine |
| `videos/*/report.md` | Completion / follow-conversion rates — thin signals for inferring "holds attention vs does not" |
| `benchmark.md` | Cold-start seed — "the benchmark's audience ≈ the audience you want" |
| `rubric_notes.md` | For the Phase 3 cross-check — persona appetite vs rubric-calibrated reality |
| `audience.md` (if it exists) | The previous persona, for the Phase 5 diff |

## Workflow

### Phase 0: Collect data

1. Glob `predictions/*.md`; for each file read the `## Retrospective` section (**read only the retrospective section — this is channel A, which is supposed to look at actual performance**)
2. Extract each piece's top comments (with like counts) + actual-performance bucket
3. Count: number of retros with comments `N_retros`, total comments `N_comments`
4. Read `benchmark.md` (if it exists)
5. Read `audience.md` (if it exists) → keep for the Phase 5 diff

### Phase 1: Data-volume judgment + Confidence

| Situation | Confidence | Behavior |
|---|---|---|
| `N_retros == 0` and no benchmark | 🔴 No data | **Do not fabricate** — tell the user "a persona needs retro data. Run a few cheat-retros first, or import a benchmark", and exit |
| `N_retros == 0` but a benchmark exists | 🟠 Benchmark-seeded, unverified | Seed an aspirational persona, **mark the whole file "unverified"** |
| `N_retros` 1-2 | 🟡 Early signal | Can produce output, but most traits land in the "hypotheses" section |
| `N_retros` 3-5 | 🟢 Data-grounded | Normal output |
| `N_retros` ≥6 | 🔵 Robust | Normal output + finer appetite segmentation possible |

Write the Confidence level into the audience.md header.

### Phase 2: Comment clustering

Cluster all collected comments along four dimensions:

1. **Self-identification** — "me too…" / "this is literally me" / "as a…" patterns. Count which identities recur ("big-tech worker" / "one-person company" / "grad-school candidate" / ...)
2. **Emotional purpose** — what emotion do viewers come to the comments for? Validation ("so true") / venting ("I'm exhausted too") / arguing ("I disagree") / asking for help ("so what should I do"). Report the proportions
3. **Disagreement points** — which views draw consistent opposition. These are the persona's boundaries
4. **Language** — how they speak. Meme density, sincere vs sarcastic, whether they copy your quotable lines

**Clustering discipline**:
- A "verified trait" needs at least `MIN_COMMENTS_PER_TRAIT` (3) pieces of comment evidence. Not enough → downgrade to the "hypothesized traits" section
- Every trait **must** cite specific comments + provenance (which prediction's retrospective section) + count
- If you find a "counter-persona" signal (the audience you assumed vs the people actually commenting are different) → write a "counter-persona" section

### Phase 3: persona × rubric cross-check

Read the current rubric in `rubric_notes.md` + calibration history. Check:

- The persona says "the audience loves topic type X" → does topic type X really over-perform in the rubric calibration pool?
- If inconsistent → **flag it** in the "persona × rubric cross-check" section of audience.md

Honesty requirement: when the two derivatives contradict, **do not** force reconciliation. Explicitly write "the persona says A, rubric calibration says B, to be clarified in the next retro" — the contradiction itself is a signal.

### Phase 4: Write audience.md

**Full rebuild** (not append) — the persona is a living document; every rebuild rewrites the whole file. But:

- The header's `Persona version` +1 (v0 → v1 → v2)
- The header records `Last rebuilt` date + `Data basis` (N retros / M comments) + `Confidence`
- The "version history" section at the bottom **appends one line**: `vN — based on M retros / K comments, main changes: ...` (this is the only retained history; no memo accumulation — the persona is a living document, not a formula)

Use the structure in [templates/audience.template.md](../../templates/audience.template.md).

⚠️ **No version memos / no cross-model audit** — the persona is not a high-risk irreversible action (if it is wrong, just rerun it); over-engineering is unnecessary.

### Phase 5: Report

```
✅ Audience persona updated: audience.md (v2, 🟢 data-grounded)

Data basis: 4 retros / 87 comments
Core persona: 25-35 year-old workers, here for emotional resonance, not information...

Main changes vs v1:
- Newly verified: the "scrolling at midnight" scene resonates strongly (v1 hypothesis; verified by 17 comments this time)
- New counter-persona: assumed "students" were the audience, but students are <5% of comments → moved to counter-persona
- ⚠️ Cross-check flag: the persona says the audience loves "workplace rants", but rubric calibration shows workplace pieces score low on composite — watch this in the next retro

Next:
- cheat-seed will reference this persona automatically when choosing topics / writing drafts
- After 3 more retros, run /cheat-persona again to refresh
```

## Key Rules

1. **Derived from data, not hand-written** — the persona must come from comment clustering. If the user wants to add a trait manually → allow it, but mark it `user-asserted` (not data-verified)
2. **Evidence is mandatory** — verified traits must carry comment counts + provenance. Evidence-free traits go in the "hypotheses" section
3. **Full rebuild** — every rebuild rewrites all of audience.md, appending only one line to the version history
4. **Never enters scoring** — the persona never feeds cheat-predict / cheat-score-blind. It is cheat-seed's creative lens
5. **Do not reconcile contradictions** — when persona × rubric conflict, flag it honestly; do not force a story
6. **Cold-start honesty** — if there is no data, say so; benchmark seeds are marked "unverified" throughout

## Refusals

- "I think my audience is X, just write it into audience.md" → you may write it, but mark it `user-asserted` and put it in the "hypothesized traits" section, not "verified traits". The persona's value lies in the gap between data and your fantasy
- "Let cheat-predict use the persona too, so scoring is more accurate" → refuse. The persona is an actual-performance derivative; feeding it into scoring = punching a hole through channel B's isolation. The persona serves cheat-seed only
- "Skip the comment clustering and draw one from your gut" → refuse. Drawing from the gut produces marketing copy, not a persona. If there is no comment data, honestly say "go do some retros first"
- "Put the persona into rubric_notes.md and save a file" → refuse. rubric_notes.md is the blind whitelist; putting a persona (an actual-performance derivative) into it = replaying the actual-performance leak hole (see the leak guard in observation-lifecycle.md)

## Integration

- Upstream: `cheat-retro` after each retro → flag "N retros accumulated; you can run /cheat-persona to refresh the persona"
- Upstream: `cheat-init` creates the empty audience.md skeleton; if a benchmark was imported → hint that `/cheat-persona — seed-from-benchmark` is available
- Downstream: `cheat-seed` Modes A/B/C read audience.md as the "would this persona care?" mirror
- Downstream (phase 2 roadmap): `cheat-recommend` persona-fit ranking; `cheat-status` persona-freshness nag
- **Isolation**: `cheat-score-blind` is strictly forbidden from reading audience.md (refusal_code `blocked_audience`)

## Known limitations

1. **Comments ≠ the whole audience** — commenters are the most active sliver of the audience (the silent majority is not in the data). The persona skews toward "people who comment", not "everyone who watches"
2. **Platform comments can be polluted** — trolls / flame-bait / off-topic comments enter the data. cheat-persona down-weights obvious outliers when clustering, but cannot filter them completely
3. **The persona lags behind real audience change** — the profile is based on the past N pieces' comments. When the audience structure changes, it takes new retros to reflect it
4. **Does not solve "the audience I want ≠ the audience I have"** — the persona only honestly reports "who is watching now". Shifting to a different audience is a topic-strategy question; cheat-persona only provides the gap between "current" and "target", and does not make strategy for you
