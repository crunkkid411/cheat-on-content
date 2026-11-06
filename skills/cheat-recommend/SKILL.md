---
name: cheat-recommend
description: Rank and recommend the top N topics from candidates.md under the current rubric, each with a composite + one-line rationale + anchor comparison. **When candidates does not exist, give guidance instead of an error**. Triggers: "推荐选题" / "next topic" / "下一篇做什么" / "recommend topics" / "挑一个选题".
argument-hint: "[— top: N] [— filter: tier1|all|safe|risky]"
allowed-tools: Read, Glob, Grep
---

# /cheat-recommend — candidate-pool ranking and recommendations

Read candidates.md → sort by composite → output the top N recommendations, each with score details + anchor comparison + reason for the recommendation.

## Overview

```
[User: recommend topics]
  ↓
[Phase 0: check whether candidates.md exists]   ← if not, guide; do not error
  ↓
[Phase 1: parse the candidates list]
  ↓
[Phase 2: filter (tier / safety / already published)]
  ↓
[Phase 3: sort by composite + find anchors]
  ↓
[Phase 4: output top N + a rationale for each + anchor comparison]
```

## Constants

- **TOP_N = 5** — recommend the top 5 by default
- **STRATEGY = stable+experimental** — when recommending ≥2, follow the "1 stable + 1 experimental" strategy in [cadence-protocol.md](../../shared-references/cadence-protocol.md); when recommending 1, recommend only the top stable pick
- **POOL_PATH = candidates.md** — candidate-pool path
- **EXCLUDE_PUBLISHED = true** — exclude already-published items (dedupe against `predictions/*.md`)
- **EXCLUDE_REJECTED = true** — exclude items the user actively skipped (`tier=skip`)
- **REQUIRE_SCORED = true** — only recommend already-scored items — avoid recommending material never read
- **DUPLICATE_CATEGORY_LOOKBACK** — derived from `state.target_publish_cadence_days`: do not recommend candidates in the same category published within max(3, cadence_days × 3) days (avoid aesthetic fatigue)

> 💡 Override at call time: `/cheat-recommend — top: 3 — filter: safe`

## Inputs

| Required | Source |
|---|---|
| `candidates.md` | user project root |
| `predictions/*.md` | for deduplication |
| `.cheat-state.json` | current rubric_version |

## Workflow

### Phase 0: Candidate-pool existence check

Read `candidates.md`:

| State | Handling |
|---|---|
| File does not exist | **Do not error**. Output guidance: see "No candidate pool guidance" below |
| File exists but is empty (< 1 entry) | Same as above |
| File exists and is non-empty | Go to Phase 1 |

**No candidate pool guidance** (core: do not let the user's first encounter with cheat-recommend drive them away):

```
You currently have no candidate pool (candidates.md does not exist or is empty).

Most people do not have one — that is completely normal. Four ways to build one; pick one:

1. 🌱 [Recommended] Run /cheat-seed
   A one-time seeding action: 3 questions (interests / tone / red lines) → pull public trends + Claude brainstorm
   → output 15 candidates for you to pick 5 → by default also writes 5 drafts. Done in 5 minutes.

   - Never published: pure brainstorm (interests × trends)
   - Published before (imported at init): the brainstorm recommends based on "what you have made before"

   Say: "find a topic" or "seed"

2. 🔥 [Daily top-up] Use /cheat-trends to fetch 20 scored candidates
   Say: "fetch trends" — pull N items each from weibo-hot / zhihu-hot / Bilibili trending / HN / your configured sources
   Good for users who have already run /cheat-seed and want to top up the pool day to day

3. ✍️  Build manually: paste candidate titles into candidates.md, one per line
   I will rough-score each one automatically

4. 📋 Import from Notion / RSS: run /cheat-init --mode add-pool to configure an adapter

You can also skip the candidate pool and give me a concrete draft directly, saying "start prediction".

> Difference between /cheat-seed and /cheat-trends:
> - seed is a seeding action (includes brainstorm + optional draft), good for "I'm starting from zero with no topic"
> - trends is daily multi-adapter fetching (no brainstorm, no draft), good for "topping up the pool day to day"
```

After the guidance → exit; do not continue to later phases.

### Phase 1: Parse candidates

Parse each H3 entry per the "Markdown representation" format in [candidate-schema.md](../../shared-references/candidate-schema.md):

```markdown
### [tier1] Title
- **id**: a3f2c1d4e5b6
- **composite (v2)**: 8.47 — ER=4 HP=4 QL=5 NA=3 AB=5 SR=3 SAT=3
- **predicted bucket**: 5-30w
...
```

Extract each entry's `id` / `title` / `tier` / `composite` / `dimension_scores` / `note`.

Tolerance: if `candidates.md` has been hand-edited by the user → ask the user about the schema; **do not silently ignore entries you do not recognize**.

### Phase 2: Filter

```
1. EXCLUDE_PUBLISHED=true → scan the headers of predictions/*.md, extract every id; filter them out of the pool
2. EXCLUDE_REJECTED=true → filter tier=skip
3. REQUIRE_SCORED=true → filter composite=null (do not recommend unscored items)
4. filter argument:
   - tier1: keep only tier=tier1
   - all: no filter (tier1+2+3)
   - safe: exclude tier=risky
   - risky: show only tier=risky (for "I want to publish a risky issue today")
```

### Phase 2.5: Buffer color override (**highest priority**)

Read `state.shoots` + `state.target_publish_cadence_days` to compute the buffer color ([cadence-protocol.md](../../shared-references/cadence-protocol.md)):

| Buffer color | Recommendation-strategy override |
|---|---|
| 🔴 Red | **Recommend only the top 1 stable pick** — no experimental. Reply: "your buffer is at 0/1 pieces; the next publish day is at high risk of a gap. You must shoot ≥1 stable piece today. Below is the top 1 stable pick (no experimental)" |
| 🟠 Orange | Standard 1 stable + 1 experimental, but note "recommend prioritizing the stable pick" |
| 🟢 Green | Standard 1+1 (default) |
| 🔵 Blue | **Refuse to recommend**. Reply: "your buffer already has N pieces; cadence-protocol says pause shooting when backed up. Publish inventory + retro first. To override manually, say 'I insist on shooting'" |
| Flexible mode (`target_publish_cadence_days=null`) | Do not apply the buffer override; standard strategy |

### Phase 3: Sort + pick 1 stable + 1 experimental (per STRATEGY)

#### Pick 1 (stable)

1. Sort by `composite` descending
2. Filter out `tier=risky` (the stable pick needs a safe topic)
3. Filter out `category` duplicates of what was published/recommended within the last `DUPLICATE_CATEGORY_LOOKBACK` days (avoid aesthetic fatigue)
4. Take the top 1

#### Pick 2 (experimental)

1. Find in candidates.md:
   - The dimension combination **most different** from recent published samples (adds calibration information), or
   - An explicit pattern/dimension hypothesis (e.g. "A/B comparison for MS=5"), or
   - tier=risky but the user is actively willing to try it (override with `--filter risky`)
2. composite need not be top — but it must have "information value"
3. If the pool has no suitable experimental candidate → reply: "no obvious experimental sample in the pool; here are 2 stable picks"

#### Remaining (TOP_N - 2)

Fill by composite descending, marked "(backup)".

#### Anchors

For each pick, find 1-2 **published** works with a close composite as anchors (read from `predictions/*.md`). Prefer **same-duration** anchors (within ±20% of `state.typical_duration_seconds`).

### Phase 4: Output

```
🎯 Candidate-pool recommendations (rubric: v2 / buffer: 🟢 Green / cadence: every other day)

📌 Pick 1 — **Stable** (recommend shooting immediately):
  **[tier1] [👍 9.18] "For Your Own Good" high-density system**
   - Dimensions: ER=5 HP=5 QL=4 NA=4 AB=5 SR=5 SAT=4
   - Rough prediction bucket: 30-100w (center ~60w)
   - rationale: ER+SR both 5, top spec; "high-density family issue" is universal and safe to share
   - Anchor: Hamster (composite 9.41, actual 1.24M) — same "theoretical framework + concrete sample" route
   - Risk: heavy issue; not suitable for two pieces in a row

🧪 Pick 2 — **Experimental** (tests a specific hypothesis):
  **[tier1] [👍 8.71] Haha Length**
   - Dimensions: ER=3 HP=5 QL=5 NA=4 AB=5 SR=4 SAT=5
   - Rough prediction bucket: 30-100w (center ~55w)
   - **Test goal**: v2.1 candidate dimensions MS+TS both 5 vs Who Asked You with the same ER/HP/QL/SR but MS+TS 3 lower
   - Information value: shooting this gives strong evidence / weak refutation for promoting v2.1
   - Anchor: Who Asked You (composite 8.24, actual 117k)

(Backup top 3):
  3. ...
  4. ...
  5. ...

Next:
- Pick 1 stable + 1 experimental → rewrite the script → "start prediction"
- Shoot only 1 → pick the stable one (the redder the buffer color, the more you should pick stable)
- Want more candidates → say "fetch trends"
- Not satisfied → say "filter all" to see other tiers, or "regen"
```

If the buffer color is 🔴:
```
🔴 Buffer alert: your buffer is at 0/1 pieces; **the next publish day may have a gap**.
   Per the cadence protocol, recommending only the top 1 stable pick (no experimental):

  **[tier1] [👍 9.18] "For Your Own Good" high-density system**
   - ... (same stable format as above)

You must shoot this one today. To pick 5 candidates → "fetch trends".
```

If the buffer color is 🔵:
```
🔵 Buffer backlog: your buffer already has N pieces; **recommendations paused**.
   Per the cadence protocol, publish inventory + retro first.
   - Shot but unpublished: N (the oldest was shot X days ago)
   - Awaiting retro: N
   Say "published ..." to dequeue, or "retro" to process pending retros.
   If you insist on shooting something new, reply "I insist on shooting" and I will recommend the top 1 stable pick.
```

Every entry must include: dimension scores (so the user can challenge the scoring) + anchors (so the user can calibrate the composite's credibility) + rationale (so the user understands the recommendation logic). **Outputting only a composite ranking with no explanation is not allowed** — that is a black box.

## Key Rules

1. **Do not error; guide**. A missing candidates file is the default state, not an error
2. **Do not recommend unscored items**. REQUIRE_SCORED=true is an honesty threshold — recommending material never read is astrology
3. **Anchors are mandatory**. A composite of 8.47 means different things on different accounts; anchors ground the abstract number in real samples
4. **Rationale is mandatory**. One sentence — why is this one stronger than the second?
5. **Dedupe published**. Do not recommend what has already been published (the user may explicitly override)

## Refusals

- "Just give me the highest composite, no need to explain" → refuse. Showing the score + anchors is the only chance to catch a "mis-score"
- "Re-score every entry in candidates.md" → route to `/cheat-score` for a single item; bulk re-scoring is part of `/cheat-bump` and outside recommend's scope
- "Sort by prediction bucket, not composite" → ask why. A bucket is a discretization of the composite; sorting by composite is sorting by bucket, with the difference inside buckets — if the user really wants to sort by "bet expected value", that requires multiplying by average plays, which is a separate scoring dimension

## Integration

- Upstream: `/cheat-trends` pulls external trends into candidates.md → recommend sees them automatically
- Downstream: after the user picks one and writes the script → `/cheat-predict` (the candidate's rough composite does not enter the prediction; the prediction re-scores)
- Coordinated with `/cheat-status`: status shows "candidates pool has N tier1 unpublished"; recommend provides concrete recommendations
