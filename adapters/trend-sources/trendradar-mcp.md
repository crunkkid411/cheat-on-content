# adapters/trend-sources/trendradar-mcp — general social trends (MCP)

**Who it suits**: opinion videos / current-events commentary / culture verticals / food / workplace / social issues — **any non-AI vertical** content.

---

## What it is

[TrendRadar](https://github.com/sansan0/TrendRadar) is a 57k-star Chinese trend aggregation monitor (using the newsnow API to pull Weibo / Zhihu / Douyin / Bilibili / Toutiao and other platforms). It ships its own MCP server, `trendradar-mcp`, exposing 25+ tools.

cheat-on-content treats it as one of the trend-sources adapters — once the user configures the MCP server, cheat-seed / cheat-trends can call it naturally.

- **Multi-platform coverage**: Weibo / Zhihu / Douyin / Bilibili / Toutiao / 36kr / etc.
- **AI-enhanced tools**: `analyze_topic_trend` for breakout/decline judgment; `compare_periods` for week-over-week; `analyze_sentiment` for sentiment tendency
- **License**: TrendRadar itself is GPL-3.0, but we **only call their server through the MCP protocol**, which does not constitute linking — no GPL contagion

## Install

Refer to the [MCP configuration docs](https://github.com/sansan0/TrendRadar) in the TrendRadar repo. Once installed, the user's Claude Code `.claude/settings.json` contains the `mcp__trendradar__*` tool family.

cheat-on-content does not bundle TrendRadar — users install it themselves and manage the server resources themselves.

## Key tools called by cheat-seed / cheat-trends

| MCP tool | Purpose | Where it is called |
|---|---|---|
| `mcp__trendradar__get_latest_news` | Get the latest hot list (most direct) | cheat-seed Mode C primary / cheat-trends primary |
| `mcp__trendradar__get_trending_topics` | Automatically extract topic statistics | cheat-seed Mode C backup |
| `mcp__trendradar__analyze_topic_trend` | Single-topic trend analysis (breakout/decline) | cheat-seed Mode A gray-area enrichment (the user raised a concrete topic and agreed to pull data) |
| `mcp__trendradar__compare_periods` | Week-over-week / month-over-month | A weak signal for "has the user's domain changed" during cheat-bump rubric upgrades (rarely used) |
| `mcp__trendradar__search_news` | Keyword search | cheat-seed Mode A when the user gives a keyword |

## Output format contract

TrendRadar MCP returns JSON / markdown. After cheat-seed receives it:

1. Parse items (title / source / hot_score / snapshot_at / url)
2. Compute a stable id per [candidate-schema.md](../../shared-references/candidate-schema.md) (`sha256(source + normalized_title + url_path)[:12]`)
3. Dedupe (per cheat-trends' dedupe protocol)
4. Rough-filter with the current rubric
5. Write into `candidates.md`

## Failure modes

| Symptom | Handling |
|---|---|
| MCP server not installed / not started | cheat-seed automatically degrades to the next enabled source (e.g. aihot or manual-paste) without throwing |
| MCP call times out | Time out after 30 seconds; ask the user "trendradar is slow — wait or switch sources?" |
| The newsnow upstream API changed | TrendRadar's maintainers fix it; users upgrade along |

## Stability

★★★★ — depends on the TrendRadar project's activity (57k stars, active) + newsnow upstream stability.

---

## Relationship to the other adapters

- **vs aihot.md**: complementary, not overlapping. trendradar is general social; aihot is AI vertical. When both are enabled, route by `content_form` (see [data-source-routing.md](../../shared-references/data-source-routing.md))
- **vs manual-paste**: the eternal fallback. When both APIs fail, go manual-paste

## A note to the TrendRadar team

If you are a TrendRadar maintainer reading this adapter doc — thank you for turning multi-platform aggregation into an MCP server. cheat-on-content is your project's "content-production-side downstream" — users use TrendRadar to know what happened, and use cheat-on-content to turn it into a calibratable content-prediction loop. Complementary, not a replacement.

Cross-links welcome: [github.com/XBuilderLAB/cheat-on-content](https://github.com/XBuilderLAB/cheat-on-content).
