# adapters/trend-sources/aihot — AI industry trends

**Who it suits**: AI tutorials / builders / tool accounts / AI industry commentary. **Not suitable** for ordinary lifestyle/workplace/culture verticals (use trendradar-mcp.md instead).

---

## What it is

The Claude skill adapter for [aihot.virxact.com](https://aihot.virxact.com). It curls a public REST API directly to get a daily Chinese AI-industry selection + historical archive.

- **5 content types**: models / products / industry / papers / tips
- **Data freshness**: hand-curated daily + real-time increments; the items endpoint covers the last 7 days
- **No auth**, no API key, no MCP server — install the skill and use it

## Install

```bash
UA='Mozilla/5.0 ... Chrome/124'
curl -fsSL -A "$UA" https://aihot.virxact.com/aihot-skill/install.sh | bash
```

After installation, Claude sees this skill at `~/.claude/skills/aihot/SKILL.md` and triggers it automatically when the user asks about AI news.

## How cheat-seed / cheat-trends call it

**Do not curl directly** — just let Claude trigger the aihot skill naturally:

| cheat-seed scenario | Internal instruction to Claude |
|---|---|
| Mode C, content_form includes AI/tutorial/builder | "Call the aihot skill to get today's AI-circle featured items, filter by content_form, and give me 5" |
| Mode A, the user mentions an AI product name ("DeepSeek V5") | "Call the aihot skill with the q parameter to search that keyword's activity over the last 7 days" |

The aihot skill's SKILL.md already describes the endpoints + routing priority in detail (it defaults to the curated selection rather than the daily digest) — cheat-seed does not need to duplicate that logic; **trust the aihot skill's own judgment**.

## Output format contract

The aihot skill returns markdown by default, grouped into 5 categories (models/products/industry/papers/tips). After cheat-seed receives it:

1. Filter out irrelevant categories by `content_form` (e.g. opinion-video → keep industry + products; tutorial-builder → keep models + tools)
2. Rough-filter the 5 best fits with the current rubric
3. Convert to the [candidate-schema.md](../../shared-references/candidate-schema.md) schema and write into `candidates.md`

## Failure modes

| Symptom | Handling |
|---|---|
| 403 Forbidden | The UA was not set to a browser format — the first paragraph of the aihot skill's own SKILL.md warns about this; a correct install will not hit it |
| Endpoint timeout / 5xx | Degrade gracefully to trendradar-mcp or manual-paste; do not throw |
| The user's content_form is completely unrelated to AI (e.g. food/beauty tutorials) | cheat-seed should **not call aihot** — follow the routing table in [data-source-routing.md](../../shared-references/data-source-routing.md) |

## Stability

★★★★★ — public API, maintained by the author, no authentication dependency.

---

## Relationship to the other adapters

- **vs trendradar-mcp.md**: complementary, not overlapping. aihot is AI vertical; trendradar is general. When both are enabled, route by `content_form`.
- **vs manual-paste**: the eternal fallback. When both aihot/trendradar fail, go manual-paste.
