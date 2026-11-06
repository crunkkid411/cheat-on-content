# Data Source Routing — trigger and routing protocol for trend tools

Referenced by cheat-seed / cheat-trends. Defines **when** to call a trend tool, **which one** to call, and **what to do when you don't call one**.

---

## Core philosophy

> **Trend tools are a "front-of-house material library", not the "main menu".**
>
> - The user is **introspecting** (telling their own experience / thinking through motivation) → **do not call**, avoid external-information contamination
> - The user is **looking for material** (no ideas / wants a batch / explicitly asks for trends) → **call**, routing the data source by content_form
> - The user is **confirming an angle** (has raised a current-events topic) → **do not proactively call**; let the user decide whether external data should inform it

Design goal: protect cheat-seed's core argument — "good content comes from the user's real experience; AI does not brainstorm out of thin air" — while not leaving a new creator with "zero ideas" stuck.

---

## Trigger matrix (referenced by cheat-seed Phase 1)

| cheat-seed Mode | Call by default? | Trigger condition |
|---|---|---|
| **Mode A** (user gave a specific experience/topic) | ❌ no by default | Only when the user's story is itself a current-events topic (contains a product name / person / event + a time word) + the user **explicitly agrees** |
| **Mode B** (direction is vague; ask "why") | ❌ **never** | At this stage the user is introspecting; external material is noise |
| **Mode C** (zero ideas) | ✅ yes by default | The core action of Mode C is to put external material on the table |
| `--batch N` | ✅ yes by default | Batch brainstorm needs an anchor |
| `/cheat-trends` explicit | ✅ call | Main entry point; no explanation needed |
| `/cheat-recommend` | ❌ no by default | A pool already exists; unless the pool has not been updated for >7 days → suggest trends first |

---

## Judging a current-events topic (for grey-area Mode A scenarios)

Let Claude judge; **do not write a regex whitelist**:

| Signal | Meaning |
|---|---|
| Contains a **proper noun** (person / product / event) | Strong signal — possibly current events |
| Contains a **time word** ("today" / "just now" / "recently" / "just happened") | Strong signal |
| Contains a **structural word** ("comparison" / "response" / "incident") | Weak signal |
| Only generic nouns + personal-experience words ("I" / "yesterday" / "my colleague") | Counter-signal — evergreen personal experience, **not current events** |

Result handling:
- **Strong signal** → ask the user "do you want me to pull the public conversation around this topic for reference?"
- **Weak signal / ambiguous** → do not ask; go straight into Mode A deep-dive
- **Counter-signal** → 100% do not call

This is consistent with the "soft rules, Claude judges" philosophy in [bump-validation-protocol.md](bump-validation-protocol.md).

---

## Data source routing (by content_form)

[adapters/trend-sources/](../adapters/trend-sources/) currently has two first-class citizens + one fallback:

| Adapter | Suitable content_form |
|---|---|
| [`aihot`](../adapters/trend-sources/aihot.md) | `tutorial-builder` / AI industry commentary / AI tutorials / AI product reviews |
| [`trendradar-mcp`](../adapters/trend-sources/trendradar-mcp.md) | `opinion-video` / `long-essay` / `short-text` / `podcast` / `other` (life/work/culture) |
| `manual-paste` | Permanent fallback — the user pastes a URL/title list |

### content_form → primary + secondary matrix

| content_form | Primary | Secondary | Do not call |
|---|---|---|---|
| `opinion-video` | trendradar-mcp | aihot (only when the topic is AI-industry related) | — |
| `long-essay` | trendradar-mcp | aihot (same as above) | — |
| `short-text` | trendradar-mcp | aihot (same as above) | — |
| `podcast` | trendradar-mcp | aihot (same as above) | — |
| `tutorial-builder` | **aihot** | trendradar-mcp (only when general tools/product launches are involved) | — |
| `mixed` | Call both | — | Claude decides which vertical each candidate belongs to |
| `other` (food/makeup/story/...) | trendradar-mcp | — | aihot (unrelated to AI) |

### User-level override

The `enabled_trend_sources` field in `.cheat-state.json` is an **explicit switch**:

```json
"enabled_trend_sources": ["aihot", "trendradar-mcp", "manual-paste"]
```

Only sources in the array are called. Empty array → manual-paste only.

An explicit cheat-trends call supports override: `/cheat-trends — sources: aihot` (use aihot for this run only).

---

## Failure fallback chain

```
[cheat-seed Mode C triggers a trend fetch]
  ↓
[pick primary by content_form]
  ↓
  ├─ Primary succeeds → take data → enter workflow
  ├─ Primary fails (API down / MCP not installed / timeout)
  │   ↓
  │   [pick secondary by content_form]
  │   ├─ Secondary succeeds → take data → tell the user "primary was unavailable, used secondary"
  │   └─ Secondary also fails → manual-paste fallback
  │       ↓
  │       [ask the user: "What did you see today that could be a piece? Paste a few URLs/titles"]
  └─ User has no source enabled → explain how to enable one + use manual-paste this time
```

**Key discipline**: no failure throws an exception. cheat-seed must always run — the only difference is whether external material is available.

---

## Token-cost awareness

Trend API calls **cost something** (aihot is tokens / trendradar-mcp is an MCP call + LLM context). Judgment principles:

| Scenario | Call frequency |
|---|---|
| Mode C trigger | At most once per session (cache the data in memory after fetching) |
| Mode A grey area | Only with user consent, once |
| `--batch N` | Once, fetching enough candidates |
| User repeatedly says "another batch" | Second time allowed; on the third, suggest "should we change the query angle?" |

Do not call the same endpoint repeatedly in one session — that is waste.

---

## Relationship with candidates.md

Data pulled by trend tools **ultimately lands in** `candidates.md`, as defined by [candidate-schema.md](candidate-schema.md):

```
[trend tool] → items
  → dedupe (vs candidates.md / predictions/ / .cheat-cache/trends-history.jsonl)
  → rough-score (cheat-seed inline rubric)
  → write to candidates.md (with a source field identifying the adapter)
```

After cheat-seed Mode C gets data it does **not** go straight into brainstorm; it first writes to candidates.md, then lets Claude choose from the pool. This keeps the data traceable and reusable by later cheat-recommend runs.

---

## Extension guide for maintainers

Adding a trend source:

1. Write `adapters/trend-sources/<name>.md`, following the format of aihot.md / trendradar-mcp.md
2. Add a row to this file's "Data source routing" section — state the content_form the adapter suits
3. No need to change cheat-seed internals — it auto-enables by `enabled_trend_sources`
4. Mark the CHANGELOG as MINOR

Do not hardcode "aihot"/"trendradar-mcp" into cheat-seed SKILL.md — keep the adapter model extensible.
