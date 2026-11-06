# Blind Prediction Protocol

Referenced by these sub-skills: `cheat-predict`, `cheat-retro`, and the main SKILL.md.

This is the full specification of project principle #1. Every sub-skill must execute this protocol before writing a prediction.

---

## Core definition

**Blind prediction**: a prediction completed **before** the predictor (human or model) sees any data about how the piece actually performed after publication.

Once a prediction is written into the `## Prediction` section of `predictions/*.md`, that section is **immutable** — you may only append a `## Retrospective` section at the end of the file; not a single character of the prediction section may change.

---

## The boundary of "having seen data" (critical, frequently violated)

If any of the following is true → the prediction is no longer blind, and **writing a prediction is forbidden**:

| Information | Breaks blindness? | Exception |
|---|---|---|
| Play count / read count for this piece on any platform | ✗ breaks it | None |
| Like / comment / repost counts for this piece | ✗ breaks it | None |
| The actual comment text on this piece | ✗ breaks it | None |
| Algorithmic recommendation slot / trending position for this piece | ✗ breaks it | None |
| Post-publish screenshots / backend analytics | ✗ breaks it | None |
| Performance of **other people's** pieces published in the same period | ○ does not break it | — |
| Performance of **historically similar topics** | ○ does not break it (this is exactly what anchor comparison is for) | — |
| The piece's **pre-publish** draft content | ○ does not break it | This is the prediction input |
| The user saying "I feel this one is decent" | △ caution | The user's subjective feeling is not "data", but note the bias in the prediction |

**Shortcut**: if the information **could only be obtained after publication**, it counts as "data".

---

## Situations the predictor must proactively disclose

Before starting `cheat-predict`, the sub-skill must self-check and **proactively disclose** to the user:

1. **The piece was published more than RETRO_WINDOW_DAYS days ago** (default 3 days) → must refuse to write a "prediction"; record it as a `**Reconstructed retrospective**` and clearly mark it as not a prediction
2. **The piece is published but < RETRO_WINDOW_DAYS days ago, and the user has not revealed any data** → blind prediction is allowed, but mark the file header with `published_before_prediction: true` + `blind_status: confirmed_no_data_seen`
3. **The user has already pasted any post-publication data into the conversation** → handle like #1, record as reconstructed

`BLIND_CHECK=strict` (default): if any breaking condition above is hit, **refuse to execute**.
`BLIND_CHECK=lenient`: warn and force a label, then allow continuation — only for offline tests or academic exercises, **not recommended for real calibration**.

---

## Engineering boundary of immutability

The immutability of the `## Prediction` section is a **user-experience promise**, enforced at the hook layer:

- `hooks/prediction-immutability.sh` checks files under `predictions/` on PreToolUse(Edit|Write)
- Any diff between `## Prediction` and the next H2 → exit 1, blocked
- Appending to `## Retrospective` → allowed

**Forbidden "workaround" patterns** (sub-skills must refuse):
- "Rewrite the prediction section to be a bit more accurate" → refuse. If there is a legitimate reason to redo it, create a new file `<original-name>_redo.md` and keep the original
- "My probability distribution was off by 0.5%, let me fix it" → refuse. Append to the retrospective: `Correction: original probability distribution X% should have been Y%, typo discovered on <date>`
- "I didn't consider SR=4 earlier, let me re-score it" → refuse. Same path as above

The only scenario where editing the prediction section is allowed: **pure markdown formatting errors** (wrong heading level, wrong list bullet format), and the user explicitly states it is a formatting fix. The hook will still block this case; the user needs an explicit bypass (set `CHEAT_BYPASS_IMMUTABILITY=1` for a single run) — the bypass should leave a trace in git history.

---

## Filename convention (**consistent in all three places**)

One piece of content uses three files, **all named with the same `<date>_<id>_<short>` group**:

```
scripts/<date>_<id>_<short>.md        ← pre-shoot draft (written by cheat-seed or the user)
predictions/<date>_<id>_<short>.md    ← immutable prediction (written by cheat-predict)
videos/<date>_<id>_<short>/           ← created only after shooting (by cheat-shoot)
  ├── script.md                       ← final shooting script supplied by the user
  └── report.md                       ← T+3d data (written by cheat-retro)
```

- `<date>`: **the date the draft was first written to disk** (i.e. `scripts/<id>.md` creation date), not the prediction / shoot / publish date. Reason: keep the ID stable — the draft can be heavily revised, its hash changes, but the files should remain traceable
- `<id>`: 12-character sha256 prefix, hashed from **the content of the draft when first written**. It **does not change** when the user edits the draft — this makes cross-file references stable
- `<short>`: 3-8 character short name (Chinese or English) for human recognition

Reconstructed redo: append `_redo` to `<short>` in all three places:
- `scripts/<date>_<id>_<short>_redo.md`
- `predictions/<date>_<id>_<short>_redo.md`
- `videos/<date>_<id>_<short>_redo/`

Keep the original files (do not delete them).

---

## Checklist every sub-skill must run

When `cheat-predict` starts:
1. Read the `BLIND_CHECK` constant
2. Ask the user for the piece's current publish status (not published / published < RETRO_WINDOW_DAYS / published ≥ RETRO_WINDOW_DAYS)
3. Ask whether any post-publication data about the piece has appeared in the conversation history (if unsure, check the conversation for keywords such as "plays / reads / likes / comments")
4. If #2 or #3 hits a breaking condition → handle according to the `BLIND_CHECK` mode
5. Only after passing may you write `predictions/*.md`

When `cheat-retro` starts:
1. Read the target prediction file
2. **Cache the `## Prediction` section in memory first** — every later write to that file must first verify that the section is unchanged
3. Fetch data → append the `## Retrospective` section
4. After writing, **verify again**: the post-write hash of the `## Prediction` section must equal the cache from step 2. If not → error out and roll back

Main SKILL.md:
- When the user says "rewrite the prediction" / "change the prediction section" / "you predicted wrong before, let me fix it for you", **refuse directly and explain**, and steer them to the `_redo.md` path

---

## Handling abnormal states

| Scenario | Handling |
|---|---|
| The prediction section was accidentally edited by hand | Do not auto-rollback (that causes more damage). The next `cheat-retro` detects the mismatch → append to the retrospective: `**Integrity warning**: the prediction section was externally modified at <ISO timestamp>; blindness cannot be guaranteed`. Downgrade the calibration value to "reference" and exclude it from the bump calibration pool |
| Prediction file lost / deleted | Recover from git log. If not found → record in `rubric_notes.md`: "<id> prediction file lost; the calibration pool is missing this sample" |
| The user started cold-start and midway wants to "backfill" a prediction for an already-published piece | Always record it as a `**Reconstructed retrospective**` and exclude it from the calibration pool — it is a backfill, not a prediction. It may be recorded as an "observation" in `rubric_notes.md` |

---

## Anti-patterns (requests that must be refused)

- "Predict this for me, but I'll tell you the play count first and you reverse-engineer it" → refuse. It directly breaks blindness
- "This has been live for 5 days and the data is out, but pretend you didn't see it and make a prediction to see if you'd be right" → refuse. Use the `_redo.md` reconstructed path instead
- "The last prediction was miscalculated, help me change the probability distribution" → refuse. Explain in the retrospective section
- "Can we skip the blind check? I have a special reason" → ask for the reason; only "formatting fix" is a legitimate bypass reason

---

## Why (why this is so strict)

Blind prediction is the **only signal source** for the entire cheat-on-content calibration loop. Once the prediction section is edited after the fact, every judgment about "which dimension was validated / refuted" loses its baseline — you no longer know whether the prediction was genuinely right, or edited into being right afterwards.

Calibration value = prediction accuracy × prediction credibility.
- Prediction accuracy can improve slowly through rubric bumps.
- Prediction credibility, once broken, cannot be restored — **that is why immutability is enforced at the hook layer, not left as a gentleman's agreement**.
