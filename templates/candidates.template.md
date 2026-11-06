# Candidate topic pool

> **This file is written by `/cheat-trends` with trend-fetch results, and read and ranked by `/cheat-recommend`.**
> **You can also edit it by hand — paste candidate titles as H3 entries.**
>
> Full schema spec: [shared-references/candidate-schema.md](../cheat-on-content/shared-references/candidate-schema.md).

---

## How to use this file (read this the first time you see it)

Each candidate is an H3 entry (`### [tier] title`) with metadata bullets below it. The minimal version only needs a title line — `/cheat-recommend` automatically calls `/cheat-score` to roughly score unscored entries.

### Field cheat sheet

- **id**: 12-char hash, used for cross-file deduplication. Leave empty when adding an entry by hand; `/cheat-trends` computes it automatically
- **source**: source identifier in the format `<adapter-type>:<source-name>`
- **snapshot_at**: capture / entry time (ISO 8601 or YYYY-MM-DD)
- **tier**: coarse classification `tier1` / `tier2` / `tier3` / `skip` / `risky` / `done`
- **read_status**: `unread` / `skimmed` / `deep_read` / `done`
- **composite (vN)**: composite score under the current rubric (rough scoring, **not a prediction**)
- **predicted bucket**: rough prediction bucket (coarse, used only for ordering)
- **note**: free-text note (e.g. "wait for the right moment", "re-read later", "risky topic")

### Minimal format for adding an entry by hand

```markdown
### Title
- snapshot_at: 2026-05-04
```

The remaining fields are filled in by `/cheat-recommend` on its next run (it calls `/cheat-score` automatically).

---

## Candidates

> Delete all the example entries below and start accumulating from your real candidates.
> The examples show real samples from the "video analysis" project's current candidate pool (anonymized).

### [tier1] The high-density "for your own good" family system

- **id**: e7c2f1a4d3b6
- **source**: pool:manual
- **snapshot_at**: 2026-05-01
- **tier**: tier1
- **read_status**: deep_read
- **composite (v2)**: 9.18 — ER=5 HP=5 QL=4 NA=4 AB=5 SR=5 SAT=4
- **predicted bucket**: 30-100w (center ~60w)
- **note**: heavy issue; not suitable for two consecutive pieces

> The three words "for your own good" are the highest-tier rhetoric of control Chinese families use on their children, backed by a whole cognitive system of "I know your needs better than you do".
> [snapshot_text section — close-reading notes after deep_read, optional]

---

### [tier1] The length of "haha"

- **id**: 229f5798b1d8
- **source**: pool:manual
- **snapshot_at**: 2026-05-03
- **tier**: tier1
- **read_status**: deep_read
- **composite (v2)**: 8.71 — ER=3 HP=5 QL=5 NA=4 AB=5 SR=4 SAT=5
- **predicted bucket**: 30-100w (center ~55w)
- **note**: v2.1 candidate dimensions MS+TS both 5 — the key A/B validation sample for the v2.1 bump

> A study of the nonlinear relationship between the length of "haha" in social media and willingness to communicate.
> Forms a perfect A/B control against Who asked you — same ER/HP/QL/SR/SAT, differing only by +3 each in MS and TS.

---

### [tier1] Freud's philosophy of sexual repression

- **id**: 8c4d92e1f0b3
- **source**: trend:manual-paste
- **snapshot_at**: 2026-04-28
- **tier**: tier1
- **read_status**: skimmed
- **composite (v2)**: 9.53 — ER=4 HP=5 QL=5 NA=4 AB=5 SR=5 SAT=5
- **predicted bucket**: 30-100w (center ~70w)
- **note**: **risky** (sexual topic); need to assess the account's risk tolerance

> Freud's core theory has been rejected by 21st-century psychology, but his description of "repression → symptom" still has explanatory power in intimate-relationship practice.

---

### [skip] [example - a skipped candidate]

- **id**: a1b2c3d4e5f6
- **source**: trend:hackernews
- **snapshot_at**: 2026-05-02
- **tier**: skip
- **rejected_at**: 2026-05-02
- **rejected_reason**: Does not fit this account's issues (pure tech news)

---

### [done] [example - a published candidate]

- **id**: ab61ed09f0a1
- **source**: pool:manual
- **snapshot_at**: 2026-04-22
- **tier**: done
- **read_status**: done
- **composite (v2)**: 8.24
- **published_at**: 2026-04-24
- **predictions_file**: predictions/2026-04-24_ab61ed09_stop-expecting.md

> Entries with tier done **do not appear in `/cheat-recommend` output** — published pieces are not recommended again.

---

## Maintenance suggestions

- **Keep < 100 active** (tier1+tier2+tier3, excluding skip/done). Above that, ranking becomes unstable
- **Clean up skips periodically**: skips older than 6 months can be automatically removed from `.cheat-cache/trends-history.jsonl` (they reappear if `/cheat-trends` captures them again)
- **Use the risky label seriously**: `/cheat-recommend` highlights risky items for a second confirmation; do not label everything "a bit controversial" as risky, or the label becomes meaningless
