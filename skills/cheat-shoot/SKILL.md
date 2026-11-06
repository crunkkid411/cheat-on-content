---
name: cheat-shoot
description: Register that a video has been shot. **Create the video folder + ask whether the actual shooting script matches scripts/<id>.md + buffer +1**. Pairs with cheat-publish: shooting puts it in the queue, publishing takes it out. Triggers: "拍了" / "拍了 X" / "shot" / "shot it" / "已拍 X" / "录完了".
argument-hint: <scripts-path-or-id>
allowed-tools: Bash(*), Read, Write, Edit, Glob
---

# /cheat-shoot — register a finished shoot + create the video folder + (if the script changed) trigger a v2 prediction

Move a video from "prediction written, not shot" to "shot, not published". This step:
1. **Create the `videos/<same id>/` directory** (if it does not already exist)
2. **Ask the user**: "Is the script you actually shot with the same as `scripts/<id>.md`?"
3. Compute the diff — above V2_TRIGGER_THRESHOLD (default 30%) → **delegate to `/cheat-predict — mode: v2`** to append a `## Prediction v2` section to the original prediction file
4. Add the video folder to the state.shoots queue, buffer +1

cheat-shoot itself does **not** write prediction content — all prediction persistence logic lives in cheat-predict. cheat-shoot only detects script changes + dispatches.

Why a separate skill:
- The buffer alert system needs a clear distinction between "shot" and "published". Videos can be shot in batches (5 in one day) and published spread out (1 per day)
- "Actual shooting script" ≠ "pre-shoot draft" is the norm. This step makes the diff explicit, triggers a v2 re-judgment, and captures "user revision pattern" signals
- The difference between the v2 and v1 predictions is itself evidence for a rubric upgrade — e.g. v1 gave ER=4 and v2 gave ER=5 (the user's revision raised the hook strength), telling the rubric "this user's ER threshold does not match my current formula"

## Overview

```
[User: shot scripts/2026-05-04_abc123_stop-expecting.md]
  ↓
[Phase 0: parse the path + verify the prediction exists]
  ↓
[Phase 1: check whether it is already registered (avoid duplicates)]
  ↓
[Phase 2: create videos/<id>/ + ask "does the actual shooting script match?"]
  ↓
[Phase 3: write videos/<id>/script.md]
  ↓
[Phase 4: append to state.shoots]
  ↓
[Phase 5: output the buffer status]
```

## Constants

- **REQUIRE_PREDICTION = true** — a v1 prediction file must exist before shooting
- **V2_TRIGGER_THRESHOLD = 0.30** — normalized char-level diff above 30% → recommend a v2 re-judgment by default; below 30%, ask the user whether they still want a v2
- **DIFF_METRIC = char_levenshtein_normalized** (**default**) — called through [`tools/diff_pct.py`](../../tools/diff_pct.py): first normalize (strip markdown headers / dividers / list markers / decorative punctuation / collapse all whitespace), then compute char-level Levenshtein / max(len_a, len_b). Preferred backend `rapidfuzz`, fallback `difflib.SequenceMatcher` (stdlib, always available). **The old line-level version produced severe false positives on colloquial transcripts** (long markdown-sentence drafts vs short whisper-transcribed lines; content almost unchanged but line-level computed ~200% diff) — fixed in PR #14
- **DIFF_METRIC=lines** — legacy fallback: when python3 is entirely unavailable or tools/diff_pct.py cannot be found, degrade to the `diff -u | grep '^[+-]' | wc -l` algorithm

## Inputs

| Required | Source |
|---|---|
| `<scripts-path-or-id>` | user argument; ask if missing |
| `.cheat-state.json` | state file |
| `scripts/*.md` | pre-shoot draft |
| `predictions/*.md` | verify the matching prediction exists |

## Workflow

### Phase 0: Parse + verify

1. Parse the path the user gives — several forms supported:
   - Full path `scripts/2026-05-04_abc123_stop-expecting.md`
   - Shorthand `2026-05-04_abc123_stop-expecting`
   - Id shorthand `abc123` → glob `scripts/*_abc123_*.md` for matches
2. Verify `scripts/<id>.md` exists: does not exist → error "cannot find the pre-shoot draft"
3. Verify the matching prediction `predictions/<same name>.md`:
   - Does not exist → **refuse to register**, prompt "run /cheat-predict first to write the prediction; otherwise you violate the blind-prediction principle — you cannot write a prediction after shooting, which is effectively writing it after seeing the footage"
   - Exists → pass

### Phase 1: Check for duplicates

Read `.cheat-state.json` and check whether `shoots[]` already contains this id:
- Already exists → warn "already registered (X days ago). Do you want to re-register, or publish with /cheat-publish?"
- Does not exist → go to Phase 2

### Phase 2: Create the video folder + ask about script consistency

1. Create the directory `videos/<id>_<short>/` (same naming as scripts/ + predictions/)
2. **Ask the user**:

```
When you shot "<title>", was the script you actually used the same as scripts/<id>.md?

a) Same — I shot from the draft
b) Changed some — can you show me the actual shooting script? I'll re-score it once (v2 prediction)
c) Major changes, basically a different piece → run the _redo flow:
   scripts/<id>_redo.md → cheat-predict again → cheat-shoot again (original prediction archived and detached)
```

### Phase 3: Write videos/<id>/script.md + (path b) trigger a v2 prediction

**Path a (same)**:
- `cp scripts/<id>.md → videos/<id>/script.md`
- `script_consistency = consistent`
- No re-judgment; go to Phase 4

**Path b (changed)**:
1. Ask the user for the actual shooting script — pasted text / file path / transcript file
2. If the user provides it → write to `videos/<id>/script.md`
3. If the user did not keep it (improvised) → mark `script_lost`, write a placeholder file + warn "v2 re-judgment skipped — next time keep the script (even a voice-memo transcript)"; go to Phase 4
4. If provided: compute the diff
   ```bash
   # Resolve the cheat-on-content source root (cheat-shoot is installed via symlink)
   SKILL_REAL="$(readlink -f ~/.claude/skills/cheat-shoot 2>/dev/null || readlink ~/.claude/skills/cheat-shoot 2>/dev/null)"
   if [[ -n "$SKILL_REAL" ]]; then
     REPO_ROOT="$(cd "$SKILL_REAL/../.." && pwd)"
     DIFF_TOOL="$REPO_ROOT/tools/diff_pct.py"
   fi

   if [[ -n "${DIFF_TOOL:-}" && -f "$DIFF_TOOL" ]] && command -v python3 >/dev/null 2>&1; then
     # default char-level Levenshtein on normalized text (rapidfuzz preferred, difflib fallback)
     diff_pct=$(python3 "$DIFF_TOOL" "scripts/<id>.md" "videos/<id>/script.md")
   else
     # legacy line-level fallback — only when python3 or diff_pct.py are unavailable
     added=$(diff -u scripts/<id>.md videos/<id>/script.md | grep -c '^+')
     removed=$(diff -u scripts/<id>.md videos/<id>/script.md | grep -c '^-')
     total_orig=$(wc -l < scripts/<id>.md)
     diff_pct=$(( (added + removed) * 100 / total_orig ))
     echo "⚠️  fallback to line-level diff — colloquial transcripts inflate diff_pct and may falsely trigger v2"
   fi
   ```

   **Why normalize + char-level**: line-level diff in creators' real workflows (draft is long markdown sentences, shooting script is colloquial short lines from whisper) computes ~200% difference while the content is almost unchanged. Normalized char-level Levenshtein stably reflects **content** differences rather than formatting differences. See [`tools/diff_pct.py`](../../tools/diff_pct.py) + `tools/diff_pct_test.sh` (3 fixtures pass on both backends).
5. **Decide the v2 trigger**:
   - `diff_pct >= 30` → recommend a v2 re-judgment by default, **proactively call** `/cheat-predict — mode: v2 — prediction-file: predictions/<id>.md`, passing `videos/<id>/script.md` as input. cheat-predict enters v2 mode and appends `## Prediction v2` (legacy `## 预测 v2` is also recognized)
   - `diff_pct < 30` → ask the user: "only N% of the content changed — re-judge? Default is no (the v1 prediction still stands)". If yes → same call; if no → skip v2 and continue to Phase 4
6. After cheat-predict finishes the v2 persist, control returns to cheat-shoot for Phase 4

**Path c (major changes)**:
- Do not write `videos/<id>/script.md`; prompt the `_redo` flow
- Exit cheat-shoot (do not go to Phase 4)

### Phase 4: State update

```json
{
  "shoots": [
    ...,
    {
      "video_folder": "videos/2026-05-04_abc123_stop-expecting/",
      "prediction_file": "predictions/2026-05-04_abc123_stop-expecting.md",
      "scripts_path": "scripts/2026-05-04_abc123_stop-expecting.md",
      "shot_at": "<ISO timestamp>",
      "script_consistency": "consistent" | "modified" | "lost",
      "script_diff_pct": <0-100 int or null>,
      "v2_prediction_written": <true/false>,
      "script_hash_at_shoot": "<sha256:12 of videos/<id>/script.md>"
    }
  ]
}
```

`v2_prediction_written: true` means the prediction file now has a `## Prediction v2` section, and cheat-retro should read v2 when computing the deviation; `false` means v1 still applies.

### Phase 5: Output the buffer status

After reading state, compute the buffer + color immediately (per the derivation rules in [cadence-protocol.md](../../shared-references/cadence-protocol.md)):

```
✅ Shoot registered: videos/2026-05-04_abc123_stop-expecting/
   Prediction file: predictions/2026-05-04_abc123_stop-expecting.md

📦 Current buffer: 3 pieces (🟢 Green, normal)
   At your cadence (every other day) = 6 days of buffer; the rhythm is stable.

Next: shoot other candidates / wait for the next publish day / do nothing
```

If the buffer color changes (e.g. green to blue) → highlight the alert:
```
📦 Current buffer: 6 pieces (🔵 Blue, **backlog**)
⚠️  Suggest pausing shooting and focusing on publishing inventory + retros.
   At your cadence (daily) = 6 days of reserve, above the healthy ceiling.
```

## Key Rules

1. **Do not write predictions** — shot ≠ published. The prediction is locked in /cheat-predict; shooting is just an event
2. **Do not touch video folder contents** — neither script.md nor draft-v0.md is modified
3. **A prediction must exist first** — otherwise it violates blind prediction (writing a prediction after shooting and seeing the footage = data leaking into judgment)
4. **Buffer is computed live** — recompute immediately after every shoot / publish; state.shoots is the source of truth
5. **Batch support**: the user can say "shot X / shot Y / shot Z" three times in a day and register them consecutively

## Refusals

- "I shot X, but I never ran cheat-predict" → refuse. The v1 prediction **must be written before shooting** — writing it after shooting lets the footage induce after-the-fact edits. Run /cheat-predict to write v1, then come back to /cheat-shoot. (A v2 re-judgment is different — it requires v1 to exist + a post-shoot script change)
- "I have no video folder; I shot it directly" → ask the user → help create the video folder + note that next time they should follow the full flow; mark `ad_hoc: true` when registering
- "I changed the script but just overwrite v1 and skip the v2 section" → refuse. v1 is the archive; v2 is the current judgment — append, do not overwrite. Keeping both sections is key evidence for rubric learning

## Integration

- Upstream: `/cheat-predict` finishes the prediction → user shoots → `/cheat-shoot` registers
- Downstream: `/cheat-publish` removes the corresponding item from state.shoots when publishing
- `/cheat-status`'s buffer number comes directly from `state.shoots.length`
- `/cheat-recommend` looks at the buffer color to adjust its recommendation strategy
- The SessionStart hook looks at the buffer color to decide the report's first line

## state.shoots data structure

```json
{
  "shoots": [
    {
      "video_folder": "videos/2026-05-04_abc123_stop-expecting/",
      "prediction_file": "predictions/2026-05-04_abc123_stop-expecting.md",
      "shot_at": "2026-05-04T18:30:00+08:00",
      "ad_hoc": false  // true if the user shot without going through the full flow
    }
  ]
}
```

Sorted by `shot_at` ascending — the earliest shoot comes first. `/cheat-status` shows a days-since-shoot warning for the earliest item (to avoid a video sitting unpublished for 30 days).
