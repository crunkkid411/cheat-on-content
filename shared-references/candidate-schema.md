# Candidate Schema

Referenced by these sub-skills: `cheat-trends`, `cheat-recommend`, `cheat-init`, and every adapter under `adapters/`.

Any content material whose fate is "decide whether to make it" — whether it comes from a hand-pasted list / RSS / Notion / a platform trend scrape — must be normalized into this schema before entering the candidate pool. This is the output contract for `adapters/`.

The field design borrows from the reference-creator project's `articles` table schema (a private project; the tool's methodology was abstracted from it).

---

## Required fields

| Field | Type | Description |
|---|---|---|
| `id` | string (12 chars) | Stable hash: `sha256(source + normalized_title + url_path)[:12]`. The same material captured at different times → same id |
| `title` | string | Human-readable title of the candidate |
| `source` | string | Source identifier in the format `<adapter-type>:<source-name>`, e.g. `trend:hackernews`, `pool:notion-mybook`, `paste:manual` |
| `snapshot_text` | string | Full text or summary of the candidate — **this is the input to scoring**, not the url. The adapter must expand the url into readable text |
| `snapshot_at` | ISO 8601 | Time this item was captured / entered |

---

## Optional fields

| Field | Type | Description |
|---|---|---|
| `url` | string | Original link (for traceability) |
| `tier` | enum | `tier1` / `tier2` / `tier3` / `skip` / `risky` / `done`. Coarse classification, used for filtering |
| `read_status` | enum | `unread` / `skimmed` / `deep_read` / `done`. Processing state |
| `category` | string | Custom category tag (e.g. "society", "family", "academia") |
| `composite_score` | float | Composite score from the current rubric (if scored) |
| `dimension_scores` | object | Integer scores per dimension, keyed to the current rubric's dimensions (e.g. `{"ER": 5, "HP": 4, ...}`) |
| `scored_under_rubric_version` | string | Rubric version used at scoring time |
| `predicted_bucket` | string | Rough prediction bucket (e.g. `30-100w`). **Note: this is not a formal prediction** — it is a coarse estimate from the topic-selection stage, completely independent of the immutable prediction in `predictions/*.md` |
| `predicted_reason` | string | One-line reason |
| `note` | string | Free-text note, e.g. "wait for the right moment", "re-read later", "risky topic" |
| `rejected_at` / `rejected_reason` | ISO 8601 / string | Recorded when the user actively skips this candidate |

---

## JSON examples

### Markdown-list adapter output

```json
{
  "id": "a3f2c1d4e5b6",
  "title": "Why we all hate reaching out to friends first",
  "source": "pool:markdown-list",
  "snapshot_text": "[full text copied by the user from candidates.md]",
  "snapshot_at": "2026-05-04T08:30:00+08:00",
  "url": null,
  "tier": "tier1",
  "read_status": "skimmed",
  "category": "social",
  "composite_score": 7.4,
  "dimension_scores": {"ER": 4, "HP": 4, "QL": 5, "NA": 3, "AB": 5, "SR": 3, "SAT": 3},
  "scored_under_rubric_version": "v0",
  "predicted_bucket": "5-30w",
  "predicted_reason": "ER=4+QL=5 strong quotable feel, AB=5 universal, but SR=3 topic is not strong enough",
  "note": ""
}
```

### Trend adapter output (HN)

```json
{
  "id": "8c4d92e1f0b3",
  "title": "Show HN: I built a tool that predicts whether your video will go viral",
  "source": "trend:hackernews",
  "snapshot_text": "[full article + summary of top 5 comments]",
  "snapshot_at": "2026-05-04T09:15:00+08:00",
  "url": "https://news.ycombinator.com/item?id=12345678",
  "tier": null,
  "read_status": "unread",
  "category": "tech-meta",
  "composite_score": null,
  "dimension_scores": null,
  "scored_under_rubric_version": null
}
```

Before scoring, all score fields are null — that is expected. After `cheat-trends` fetches items, it calls `cheat-score` to compute a composite for each one.

---

## Markdown representation (the user-visible storage format)

The default storage for the candidate pool is `candidates.md` (human-readable), not JSON. Each item is an H3 entry:

```markdown
### [tier1] Why we all hate reaching out to friends first
- **id**: a3f2c1d4e5b6
- **source**: pool:markdown-list
- **snapshot_at**: 2026-05-04
- **category**: social
- **composite (v0)**: 7.4 — ER=4 HP=4 QL=5 NA=3 AB=5 SR=3 SAT=3
- **predicted bucket**: 5-30w
- **note**:

> [snapshot_text section, if any]
```

After upgrading to SQLite (see the upgrade trigger in `cheat-status`), the same fields are stored in the `articles` table, and the markdown view is rendered from the DB automatically.

---

## Key rules for ID stability

**The same material captured at different times by different adapters → must produce the same id**. This is the basis of deduplication.

Algorithm:
```python
import hashlib

def candidate_id(source: str, title: str, url: str = None) -> str:
    normalized_title = title.strip().lower().replace(" ", "")
    url_path = url.split("?")[0].rstrip("/") if url else ""
    raw = f"{source.split(':')[0]}|{normalized_title}|{url_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
```

Notes:
- `source` uses the adapter type before the colon (`trend:hackernews` → `trend`), not the specific source name — the same title captured by both HN and Reddit should be treated as one candidate (avoid double scoring)
- title is lowercased + spaces removed — so "Hello World" and "hello world" are not counted as different ids
- url drops the query string — `?utm_source=xxx` does not affect the content

---

## Deduplication protocol

Before writing to `candidates.md`, `cheat-trends` / `cheat-recommend` must run:

1. Compute the new item's id
2. Check whether `candidates.md` already contains this id → skip
3. Check whether `predictions/*.md` contains this id (already published) → skip
4. Check whether `.cheat-cache/trends-history.jsonl` contains this id with `rejected_at != null` → skip (the user already actively rejected it)
5. If it passes, write it

`.cheat-cache/trends-history.jsonl` is the dedup cache of fetch history; one JSON record per line, append-only. Candidates rejected by the user stay here for 6 months; afterwards they may reappear (perhaps the material will be evaluated differently under a new rubric).

---

## Semantics of tier

| Tier | Meaning | Corresponding action |
|---|---|---|
| `tier1` | Strong candidate, should recommend | Enters the `cheat-recommend` ranking pool |
| `tier2` | Medium, backup | Enters the ranking pool with lower weight |
| `tier3` | Weak candidate, keep but do not use | Not in the recommendation pool; kept as long tail |
| `skip` | User actively skipped | Never appears again |
| `risky` | Sensitive topic / platform moderation risk | Extra label when recommending; needs user confirmation |
| `done` | Published | Removed from the candidate pool; the prediction file takes over |

**During cold-start every item defaults to `unread` / `null tier`** — coarse classification is only possible after the user or `cheat-score` produces a composite. **Unscored items must not appear in `cheat-recommend` output** — avoid recommending material that has not been read.

---

## Adapter implementation contract

Any adapter under `adapters/` must:

1. Implement the `fetch() → List[Candidate]` interface (pseudo-signature; the actual protocol is described in markdown docs)
2. Output items conforming to this schema
3. Expand the url / short summary into readable `snapshot_text` itself — **an adapter must not output a "bare url"**
4. Degrade gracefully: if configuration is missing (API key, cookie), return an empty list + state the reason in stderr/log, **do not throw**

See `adapters/HOWTO.md` (to be written in batch 3).
