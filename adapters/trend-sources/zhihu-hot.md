# Adapter: zhihu-hot (Zhihu hot list)

Called by the following skills: `cheat-seed` Phase 2a, `cheat-trends`.

> **Current status**: schema only. The actual fetch implementation belongs to batch 3. During the stub period, /cheat-seed has Claude fetch directly via `WebFetch` (see "Interim implementation" below).

---

## When to use it

- **One of `cheat-seed`'s default sources** — a cold-start user's first topic seed
- **An optional `cheat-trends` source** — day-to-day candidate-pool top-up

Best fit: argumentative / issue-discussion / knowledge-explainer opinion videos. Zhihu topics are on average more "discussable" than Weibo — a single title already contains a question and a stance, saving half the brainstorming work.

## Dependencies

- Public endpoint, **no login required**
- Endpoint: `https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true` (JSON)
- Alternative: `https://www.zhihu.com/billboard` (HTML, usable as a fallback)

## Fetch interface

```
fetch(limit: int = 50) -> List[Candidate]
```

Returns a list of items conforming to [shared-references/candidate-schema.md](../../shared-references/candidate-schema.md).

Field mapping:
- `id`: `sha256("zhihu-hot|" + normalized_title + "|" + url_path)[:12]`
- `title`: the Zhihu question title
- `source`: `"trend:zhihu-hot"`
- `snapshot_text`: question title + a 200-character summary of the top answer (optional — if it cannot be fetched, use the title only)
- `snapshot_at`: fetch time in ISO 8601
- `url`: the Zhihu question URL (e.g. `https://www.zhihu.com/question/<id>`)
- Other fields: null

## Failure modes

| Symptom | Handling |
|---|---|
| API endpoint changed | Switch to the `/billboard` HTML fallback |
| API requires login (403) | Return an empty list + report |
| Network unreachable | Return an empty list + report |

**Graceful degradation**: failures never throw — the caller has other sources to fall back on.

## Stability level

★★★★ — the Zhihu API is more stable than Weibo's; the JSON endpoint changes less often than Weibo's HTML.

Suggested throttling: `/cheat-seed` defaults to ≤ 3 fetches per user per day.

## Interim implementation (stub)

Before batch 3 writes a dedicated adapter, `/cheat-seed` uses `WebFetch`:

```
WebFetch("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true",
         "parse each item in the JSON data array, extract target.title_area.text and target.url, up to 50 entries")
```

If the response structure cannot be recognized → switch to the `/billboard` HTML scraping fallback.

## Content characteristics (affects brainstorm quality)

Zhihu hot-list titles are usually **complete interrogative sentences** ("How should X be viewed", "Why Y", "What is the essence of X"), which are better suited than Weibo hot-search keywords for direct conversion into opinion-video topics.

But note:
- Some titles are too specific ("X company layoff event") → Claude should abstract in brainstorming from "case → universal"
- Some titles are too "Zhihu-flavored" (academic, long complex sentences) → Claude should translate in brainstorming from "Zhihu register → short-video hook"

## Risk notes

- The Zhihu hot list occasionally contains politically sensitive topics — the "red line" filter in /cheat-seed Phase 1 Q3 is necessary
- Some hot topics are already densely covered by Zhihu influencers, making differentiation hard when making videos — during rough scoring, suggest telling the user "this topic is saturated and needs a differentiated angle"

## Related adapters

- [weibo-hot.md](weibo-hot.md) — broader issues but more fragmented; better matched to current-events commentary
- bilibili-popular.md (pending) — direct video-content comparison reference
- thirdparty-paid.md (pending) — paid stable data sources
