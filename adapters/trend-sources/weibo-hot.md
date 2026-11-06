# Adapter: weibo-hot (Weibo hot search)

Called by the following skills: `cheat-seed` Phase 2a, `cheat-trends`.

> **Current status**: schema only. The actual fetch implementation belongs to batch 3. During the stub period, /cheat-seed has Claude fetch + parse directly via `WebFetch` (see "Interim implementation" below).

---

## When to use it

- **One of `cheat-seed`'s default sources** — a cold-start user's first topic seed
- **An optional `cheat-trends` source** — day-to-day candidate-pool top-up

Best fit: current-events commentary, social issues, and hot-take opinion videos.

## Dependencies

- Public endpoint, **no cookie required**
- Endpoint: `https://s.weibo.com/top/summary?cate=realtimehot` (HTML page)
- Alternative: `https://weibo.com/ajax/side/hotSearch` (JSON; returns 401 during some periods, unstable)

## Fetch interface

```
fetch(limit: int = 50) -> List[Candidate]
```

Returns a list of items conforming to [shared-references/candidate-schema.md](../../shared-references/candidate-schema.md).

Field mapping:
- `id`: `sha256("weibo-hot|" + normalized_title + "|" + url_path)[:12]`
- `title`: the hot-search term
- `source`: `"trend:weibo-hot"`
- `snapshot_text`: hot-search term + (if any) official tag + a short summary (automatically fetch 1-2 sentences from the hot-search detail page)
- `snapshot_at`: fetch time in ISO 8601
- `url`: `https://s.weibo.com/weibo?q=<encoded_keyword>`
- Other fields: null (no scoring at fetch time; the caller cheat-score handles it)

## Failure modes

| Symptom | Handling |
|---|---|
| HTML structure changed, parsing fails | Return an empty list + write to stderr "weibo HTML structure changed; patch it yourself per adapters/trend-sources/weibo-hot.md" |
| Endpoint 503 / rate-limited | Return an empty list + report |
| Network unreachable | Return an empty list + report |

**Graceful degradation**: a single failure never throws — the caller (cheat-seed / cheat-trends) falls back to other sources.

## Stability level

★★★ — a public endpoint, but Weibo occasionally adjusts page structure + has anti-scraping (high-frequency fetching from the same IP in a short window gets rate-limited).

Suggested throttling: `/cheat-seed` defaults to ≤ 3 fetches per user per day — the cold-start stage does not need higher frequency.

## Interim implementation (stub)

Before batch 3 writes a dedicated adapter implementation, when `/cheat-seed` calls this source, Claude directly uses the `WebFetch` tool to fetch `https://s.weibo.com/top/summary?cate=realtimehot` and extract the top 50 hot-search titles from the HTML. cheat-seed's Phase 2a handles this:

```
WebFetch("https://s.weibo.com/top/summary?cate=realtimehot",
         "extract the top 50 hot-search titles, one per line, in descending popularity")
```

If the content returned by WebFetch yields ≥10 recognizable hot searches → treat as success; otherwise treat as failure and skip this source.

## Risk notes

- Weibo hot-search content **often includes politically sensitive / entertainment-gossip** topics — the "red line" filter in /cheat-seed Phase 1 Q3 is critical
- Some hot-search terms are too short (5-10 characters) and lack context — Claude needs to expand them during brainstorming
- A hot search's "popularity" score and its "suitability for an opinion video" are **not positively correlated** — do not feed popularity directly into the composite during rough scoring

## Related adapters

- [zhihu-hot.md](zhihu-hot.md) — deeper issues; better matched to argumentative content
- bilibili-popular.md (pending) — skews toward younger topics
- thirdparty-paid.md (pending) — Newrank / Feigua, paid but stable
