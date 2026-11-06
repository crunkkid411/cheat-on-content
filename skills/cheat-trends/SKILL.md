---
name: cheat-trends
description: Fetch today's trending topics from the configured trend sources (HN / Reddit / YouTube trending / Bilibili trending / etc.), dedupe + rough-score + write into candidates.md. **Most people have no candidate pool — this is the key that makes the "I have no material" problem disappear at onboarding step two**. Triggers: "抓热点" / "fetch trends" / "今天有什么可做的" / "trending now" / "找选题".
argument-hint: "[— sources: <comma-separated>] [— max-per: 20]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-trends — trend fetching

Multi-adapter mode: read each `trend-sources` adapter's output → dedupe → rough-score → write into `candidates.md`.

## Overview

```
[User: fetch trends]
  ↓
[Phase 0: read .cheat-state.json for enabled adapters]
  ↓
[Phase 1: call fetch on each adapter]
  ↓
[Phase 2: normalize to candidate-schema]
  ↓
[Phase 3: dedupe (vs candidates / predictions / trends-history)]
  ↓
[Phase 4: rough-score each new item (reusing cheat-score's inline logic)]
  ↓
[Phase 5: sort + ask the user which ones to add to candidates.md]
  ↓
[Phase 6: write + update the trends-history.jsonl cache]
```

## Constants

- **TREND_SOURCES = ["manual-paste"]** — enabled adapter list (default is manual-paste only, the most stable)
- **LOOKBACK_HOURS = 24** — fetch trends from the last N hours
- **MAX_PER_SOURCE = 20** — at most N items per adapter
- **DEDUPE = true** — dedupe switch
- **AUTO_SCORE = true** — automatically rough-score after fetching
- **MIN_COMPOSITE_TO_SUGGEST = 6.0** — items below this score are not recommended for the pool (still written to trends-history so they are not recommended again)

> 💡 Override at call time: `/cheat-trends — sources: manual-paste,aihot,weibo-hot — max-per: 10`

## Inputs

| Required | Source |
|---|---|
| `.cheat-state.json` | default sources |
| `adapters/trend-sources/<name>.md` | each adapter's implementation description |
| `candidates.md` | dedupe reference |
| `predictions/*.md` | dedupe reference (do not re-recommend published items) |
| `.cheat-cache/trends-history.jsonl` | historical fetch dedupe cache |

## Workflow

### Phase 0: Read enabled adapters

```python
# pseudocode
state = read('.cheat-state.json')
enabled_adapters = args.sources or state.get('enabled_trend_sources', ['manual-paste'])
```

If enabled_adapters is empty → output guidance:

```
You currently have no trend sources enabled.

Fastest setup:
- One-off run: /cheat-trends — sources: manual-paste,aihot
- Permanently enable: edit the enabled_trend_sources array in .cheat-state.json

Available adapters (see adapters/trend-sources/):
- manual-paste (default, always works)
- aihot (AI trend aggregator, no key needed)
- weibo-hot (Weibo hot search, no key needed)
- zhihu-hot (Zhihu hot list, no key needed)
- trendradar-mcp (TrendRadar MCP service, requires configuration)
```

### Phase 1-2: Call fetch + normalize for each adapter

For each adapter, read the fetch interface described in its `adapters/trend-sources/<name>.md` (in practice a Bash call to underlying Python / shell / WebFetch):

| Adapter | Implementation |
|---|---|
| `manual-paste` | Ask the user: "Paste your candidate URL/title list for today (one per line)" → parse each line, WebFetch URLs to expand a snippet |
| `aihot` | Read the fetch interface described in adapters/trend-sources/aihot.md |
| `weibo-hot` | Read the fetch interface described in adapters/trend-sources/weibo-hot.md |
| `zhihu-hot` | Read the fetch interface described in adapters/trend-sources/zhihu-hot.md |
| `trendradar-mcp` | Read the fetch interface described in adapters/trend-sources/trendradar-mcp.md |

Each adapter outputs items conforming to [candidate-schema.md](../../shared-references/candidate-schema.md).

**Graceful degradation**: a single adapter fails (missing API key / endpoint 503 / expired cookie) → skip that adapter, **do not throw**, and explain in the summary:
```
✅ aihot: fetched 18
✅ weibo-hot: fetched 15
✅ zhihu-hot: fetched 12
⚠️  trendradar-mcp: skipped (MCP service not configured — see adapters/trend-sources/trendradar-mcp.md)
```

### Phase 3: Dedupe

Per the "dedupe protocol" in [candidate-schema.md](../../shared-references/candidate-schema.md):

1. Compute each item's id (`sha256(source_type + normalized_title + url_path)[:12]`)
2. Check whether `candidates.md` already contains this id → skip
3. Check whether `predictions/*.md` already contains this id → skip
4. Check whether `.cheat-cache/trends-history.jsonl` already contains this id with `rejected_at != null` → skip

Write dedupe statistics into the summary report.

### Phase 4: Rough scoring

When `AUTO_SCORE=true`, for each new item:
1. Use the item's `snapshot_text` as input
2. Score the 7 dimensions per the current rubric (**do not** call the `/cheat-score` sub-skill with its IO; reuse the scoring logic inline)
3. Compute the composite
4. Give a one-sentence rationale

**Note**: rough scoring ≠ a formal prediction. A prediction must be based on the final draft (after the user's rewrite); scoring here is only a rough filter for "is this worth expanding into a draft".

When `AUTO_SCORE=false`, items are written into candidates.md with composite=null and need a manual `/cheat-score` later.

### Phase 5: Sort + ask

Sort by composite descending, filtering out composite < `MIN_COMPOSITE_TO_SUGGEST`:

```
🔥 Trend fetch complete. Per-source statistics:
- manual-paste: 5 (user input)
- aihot: 18
- weibo-hot: 15
Skipped trendradar-mcp (MCP service not configured)

After dedupe, 27 new items remain.
After rough scoring, 12 have composite ≥ 6.0:

| # | Title | source | composite | bucket | rationale |
|---|---|---|---|---|---|
| 1 | Why we all hate reaching out to friends first | aihot | 8.4 | 30-100w | ER+QL both 5, AB universal |
| 2 | The thousand variants of "she's different" | weibo-hot | 8.1 | 30-100w | MS candidate dimension high |
| 3 | ...... |

Which ones to add to candidates.md?
- All → reply "all"
- A few → reply "1, 3, 5"
- None → reply "none" (they are recorded in trends-history so they are not recommended again)
```

### Phase 6: Persist

After the user responds:
1. Selected items → append to `candidates.md` in the "Markdown representation" format from [candidate-schema.md](../../shared-references/candidate-schema.md)
2. All fetched items (selected or not) → append to `.cheat-cache/trends-history.jsonl`:
   ```jsonl
   {"id": "...", "title": "...", "source": "...", "snapshot_at": "...", "rejected_at": null|"<ISO>", "fetched_at": "<ISO>"}
   ```

### Phase 7: State update

```json
{
  "last_trends_run_at": "<ISO>",
  "last_trends_added_count": 5
}
```

## Key Rules

1. **Do not throw**. A single adapter failure → skip + report. All adapters failing → error "all sources failed" with troubleshooting guidance
2. **manual-paste is always available**. Even if every other adapter is broken, manual-paste must work — it is the fallback
3. **Dedupe is a hard constraint**. Do not re-recommend the same id; do not re-recommend items the user rejected for 6 months
4. **Rough scores must be labeled honestly**. Mark entries in candidates.md as `composite (rough, snapshot-based)` to avoid confusion with precise prediction scores
5. **Do not go straight into predictions/**. trends only produces candidates; predict is a separate action

## Refusals

- "Just scrape the Douyin trending feed without a cookie" → refuse. Douyin's anti-scraping is extremely strict; without a cookie it will fail. Point to the douyin-session adapter setup docs
- "Skip dedupe and write everything you fetched" → refuse. It pollutes the candidate pool and breaks ranking at the next recommend
- "Skip rough scoring and write raw titles" → allowed (`AUTO_SCORE=false`), but tell the user that `/cheat-score` is needed later before they can enter the recommend pool

## Integration

- Upstream: the user configures the `enabled_trend_sources` array in `.cheat-state.json`
- Downstream: `/cheat-recommend` reads `candidates.md` directly for ranking — once trends writes, recommend sees it immediately
- With `/cheat-init`: users who choose "no candidate pool" at onboarding Q4 are guided here
- With `/cheat-status`: the status dashboard shows "last trend fetch: X days ago / candidate pool awaiting cleanup: Y entries"

## Adapter implementation notes

Each `adapters/trend-sources/<name>.md` must document the following:
1. **Dependencies**: API key / cookie / package
2. **Fetch interface**: how to call it (python script path / shell command / API endpoint)
3. **Output schema**: must conform to candidate-schema.md
4. **Failure modes**: common errors + graceful-degradation behavior
5. **Stability level**: ★ 1-5 stars

See [adapters/HOWTO.md](../../adapters/HOWTO.md) (to be implemented in batch 3).
