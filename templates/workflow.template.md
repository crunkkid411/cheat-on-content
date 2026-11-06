# Workflow cheat sheet (cheat-on-content)

> This is the quick-reference doc `/cheat-init` creates at your project root. The full spec lives in cheat-on-content's `SKILL.md` and `shared-references/`.
> Use this when "you forgot what to say next" — no need to read it from the top.

---

## One-line flow

```
Find a topic
  ├─ No publishing history → /cheat-seed brainstorm (interests × trends)
  └─ Has publishing history → /cheat-seed brainstorm (interests × trends × what you have made before)
                              (both run cheat-seed; the difference is the brainstorm has extra historical context)
  ↓
cheat-seed writes 5 drafts to → scripts/<date>_<id>_<short>.md
  ↓
User revises scripts/<date>_<id>_<short>.md (overwrite the same file)
  ↓
/cheat-score scripts/<date>_<id>_<short>.md → see the rubric score (exploration)
  ↓
/cheat-predict scripts/<date>_<id>_<short>.md → write the immutable prediction v1 to predictions/
  ↓
After shooting → /cheat-shoot scripts/<date>_<id>_<short>.md
   ├─ Create videos/<date>_<id>_<short>/ directory
   ├─ Ask the user: "Is the script you actually shot identical to scripts/<id>.md?"
   │   ├─ Yes → cp → videos/<id>/script.md, keep the v1 prediction
   │   ├─ Changed → request the final script → compute the diff
   │   │   ├─ diff ≥30% → automatically /cheat-predict — mode: v2 → append a `## Prediction v2` section to predictions/<id>.md
   │   │   └─ diff <30% → ask whether to do v2; default is to keep v1
   │   └─ Major rewrite → use the _redo flow (new scripts/<id>_redo.md + re-run cheat-predict)
   └─ buffer +1
  ↓
Publish → /cheat-publish + URL → buffer -1
  ↓
T+3 days → /cheat-retro videos/<date>_<id>_<short>/
   ├─ Fetch data / user pastes → write videos/<id>/report.md
   ├─ Append a ## Retrospective section to predictions/<id>.md
   ├─ Diff scripts/<id>.md vs videos/<id>/script.md → learn the user's revision patterns
   └─ Write new observations into rubric-memo.md / script_patterns.md (actual performance only goes into rubric-memo, never rubric_notes)
  ↓
≥3 same-direction misses accumulated → /cheat-bump (evolve the rubric)
```

---

## Trigger phrases for the five stages

### ① Topic selection

| What you want | Trigger phrase |
|---|---|
| See ranked recommendations from candidates.md | "recommend topic" / "what should I make next" |
| Fetch today's trends to expand candidates | "fetch trends" / "what can I make today" |
| See the current status | "status" |

> Having no candidates.md during cold-start is the default state — do not think the tool is broken because of it.

### ② Scoring + prediction

| What you want | Trigger phrase | Writes a file? |
|---|---|---|
| See a draft's rubric score (exploration) | "score this path/to/draft.md" | No |
| Write a formal immutable prediction log for the final draft | "start prediction" or "start a prediction for this draft path/to/draft.md" | Yes (`predictions/...md`) |

> **The core difference between score and predict**:
> - score is exploration, no side effects, can be run repeatedly
> - predict is a commitment; once the file is written, the `## Prediction v1` (or `## Prediction v2`) section is locked by the hook

> **v2 re-judgment trigger**: when cheat-shoot detects a line-diff ≥30% between the shooting script and the original scripts file, it automatically calls cheat-predict to write a `## Prediction v2` section (append, do not overwrite v1). See the v1/v2 section conventions in [shared-references/prediction-anatomy.md](../shared-references/prediction-anatomy.md).

### ③ Publish registration

Right after publishing:

```
"shipped https://..."
```

or:

```
"shipped predictions/2026-05-04_xxx.md, link is https://..."
```

This updates the prediction file header's `published_at` / `Platform` / `URL` and adds the file to the `pending_retros` queue.

### ④ Retro

T+3 days later (default):

```
"retro predictions/2026-05-04_xxx.md"
```

or simply:

```
"retro"
```

The latter takes the earliest entry from `pending_retros`.

> A retro needs data from you. The default is manual paste — paste "plays / likes / comments / shares" and the top 20 comments into the conversation.
> If you configured an adapter, cheat-retro can fetch automatically.

### ⑤ Rubric bump (rare)

**Only propose when the conditions are met**:
- Calibration pool ≥ 5 pieces
- ≥ 3 new calibrations since the last bump
- ≥ 3 consecutive same-direction misses detected

When met, run:

```
"bump rubric --propose 'ER weight 1.5→2.0, add MS dimension'"
```

A bump is a high-risk operation — it runs 5 validation steps (including an independent cross-model audit). See `cheat-on-content/shared-references/bump-validation-protocol.md`.

---

## Three non-negotiable principles

> Violating any one of them degrades the whole calibration loop into astrology.

1. **Blind prediction**: the prediction section is written before seeing any data, and cannot be changed once written. The hook enforces this at the harness layer.
2. **A bump = a full re-score**: a bump must re-score the entire calibration pool + pass an independent cross-model audit.
3. **The rubric is a workbench, not a museum**: observations that were absorbed / refuted are both deleted. Git history is the archive.

---

## Default configuration

Default values for a project created by `/cheat-init`:

| Setting | Default | When to change |
|---|---|---|
| `RETRO_WINDOW_DAYS` | 3 | Change to 7 for long-form / slow platforms |
| `BLIND_CHECK` | strict | Temporarily set to lenient for drills / tests |
| `MIN_SAMPLES_FOR_BUMP` | 5 | Do not lower |
| `CROSS_MODEL_AUDIT` | true (if mcp__llm-chat__chat is configured) | false only when offline |
| `TREND_SOURCES` | ["manual-paste"] | Add new sources via the `enabled_trend_sources` field |
| `POOL_PATH` | candidates.md | Change the field when using Notion |

---

## Dashboard (status command)

Say "status" at any time to output:
- Current mode / rubric version / calibration sample count
- To-dos (pending retros + same-direction miss warnings + stale in-progress)
- Candidate-pool size + days since the last trend fetch
- Health (rubric_notes.md line count / whether hooks are installed / whether cross-model audit is configured)
- Suggested next steps (in recommended priority order)

---

## File structure (your project root)

```
<your-content-project>/
├── rubric_notes.md          # Source of truth for scoring rules
├── script_patterns.md       # Writing pattern library
├── WORKFLOW.md              # This file
├── STATUS.md                # Dashboard (maintained by cheat-status)
├── candidates.md            # Candidate pool (optional; written by cheat-seed / cheat-trends)
├── .cheat-state.json        # State file (git-tracked)
├── .cheat-cache/            # Local cache (gitignored)
│   ├── usage.jsonl
│   └── trends-history.jsonl
├── .cheat-secrets.json      # API keys / cookies (gitignored)
├── .cheat-hooks/            # Copies of the hook scripts
│   ├── prediction-immutability.sh
│   ├── session-start.sh
│   └── log-event.sh
├── .claude/settings.json    # Contains the cheat-on-content hooks
│
├── scripts/                 # **All pre-shoot drafts**
│   └── YYYY-MM-DD_<id>_<short>.md   # Written by cheat-seed or the user
│
├── predictions/             # **Immutable prediction logs** (hook-protected)
│   └── YYYY-MM-DD_<id>_<short>.md   # Written by cheat-predict
│
└── videos/                  # **Created only after shooting** (by cheat-shoot)
    └── YYYY-MM-DD_<id>_<short>/
        ├── script.md        # The final shooting script you supplied
        └── report.md        # T+3d data (written by cheat-retro)
```

### How the three directories relate

| Directory | Stage | Content | Who writes |
|---|---|---|---|
| `scripts/` | Pre-shoot draft | Claude AI draft or user original | cheat-seed writes the first version; the user's revisions stay in the same file |
| `predictions/` | Prediction locked | 7-component immutable log | cheat-predict writes |
| `videos/<id>/` | Post-shoot artifact | Final shooting script + T+3d data | cheat-shoot creates the directory; cheat-retro writes report.md |

All three use the same `<date>_<id>_<short>` naming group; `<id>` is the first 12 chars of the sha256 of the first persisted content of `scripts/<id>.md`, and **does not change when the draft is revised**.

`/cheat-init` automatically creates the skeleton above (without overwriting anything that exists).

---

## Stuck?

- Read the "Requests that must be refused" section of `cheat-on-content/SKILL.md` — what you want to do may be exactly what the design refuses
- Read the corresponding sub-skill's `cheat-on-content/skills/cheat-X/SKILL.md`
- Run "status" to see cheat-status's "suggested next steps"
