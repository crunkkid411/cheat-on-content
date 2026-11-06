# State Management (state-file read/write conventions)

Referenced by every sub-skill. `.cheat-state.json` is the **single source** of shared context across sub-skills — every piece of runtime state, cumulative metric, and mode marker is read from and written back to this file.

---

## File location

```
<user-content-project>/.cheat-state.json
```

**Never** put it in the global `~/.claude/` or inside cheat-on-content's own directory — one user may maintain multiple content projects, and each project has independent state.

---

## Complete schema

```json
{
  "schema_version": "1.4",
  "skill_version": "1.0.0",

  "rubric_version": "v0",
  "content_form": "opinion-video",
  "typical_duration_seconds": 240,
  "target_publish_cadence_days": 2,
  "rubric_form_mismatch": false,
  "benchmark_status": "none",
  "benchmark_name": null,
  "benchmark_sample_count": 0,
  "baseline_plays": null,

  "calibration_samples": 0,
  "calibration_samples_at_last_bump": 0,

  "data_collection": "manual",
  "pool_status": "none",
  "data_layer": "markdown",

  "hooks_installed": false,
  "enabled_trend_sources": ["manual-paste"],
  "enabled_perf_adapters": [],

  "last_bump_at": null,
  "last_bump_self_audited": false,
  "last_published_at": null,
  "last_published_file": null,
  "last_retro_at": null,
  "last_trends_run_at": null,
  "last_trends_added_count": 0,
  "last_prediction_self_scored": false,
  "last_self_scored_at": null,

  "consecutive_directional_errors": [],
  "pending_retros": [],
  "shoots": [],

  "in_progress_session": null,

  "initialized_at": "2026-05-04T15:00:00+08:00"
}
```

### Key changes (v1.4)

Compared with v1.3 (**MINOR but BREAKING for blind channel integrity** — existing users must run migrate):

- **Rubric file split**: `rubric_notes.md` → `rubric_notes.md` (formula + generic dimension definitions; the blind whitelist) + `rubric-memo.md` (bump memos with evidence + derived evidence; strictly forbidden reading for the blind channel)
- **State fields unchanged** — only `schema_version` is bumped to mark that existing users must run the migration that splits the current rubric_notes.md into two files
- Works with the `blocked_rubric_memo` refusal_code in [skills/cheat-score-blind/SKILL.md](../skills/cheat-score-blind/SKILL.md) + the cheat-bump Phase 5 leak-guard self-check
- **Consequence of not running migrate**: the blind sub-agent still reads actual performance from rubric_notes.md, and the sub-agent self-reports `non_blind_warning` and downgrades every confidence to medium — usable, but no longer "truly blind"
- See [migrations/1.3-to-1.4.md](../migrations/1.3-to-1.4.md)

### Key changes (v1.3)

Compared with v1.2 (MINOR, compatible):

- **New `last_prediction_self_scored: bool`** — `true` only when the last `/cheat-predict` used the `--skip-blind` flag or the user chose b in Phase 2.5 (trusting the main Claude's own estimate). cheat-status / the SessionStart hook nag based on it: "the last prediction did not go through the blind sub-agent, N days ago"
- **New `last_self_scored_at: ISO 8601 / null`** — the timestamp when `last_prediction_self_scored` was triggered; cleared back to null when the sub-agent path is used
- Works with the channel B isolation protocol in [skills/cheat-score-blind](../skills/cheat-score-blind/SKILL.md) — upgrading contamination tracking from "relying on git history" to "relying on state fields"
- When an old state lacks these two fields → fall back to `false` / `null`, **MINOR compatible**

### Key changes (v1.2)

Compared with v1.1 (MINOR, compatible):

- **`shoots[]` item schema extended** — new `scripts_path`, `script_consistency`, `script_diff_pct`, `v2_prediction_written`, `script_hash_at_shoot` fields. See cheat-shoot Phase 4 for semantics. These fields record "whether a post-shoot draft revision triggered a v2 prediction re-judgment"; cheat-retro uses them to decide whether to read `## Prediction v1` or `## Prediction v2`
- When an old state lacks these fields → skills fall back via `state.get(field, default)` (`script_consistency` defaults to `"consistent"`, `v2_prediction_written` defaults to `false`, `script_diff_pct` defaults to `null`). **Running migrate is not mandatory** — but running it aligns the state fields with the schema doc

### Key changes (v1.1)

Compared with v1.0:

- **Removed `mode`** (the "cold-start" / "calibration" binary) → use the integer `calibration_samples` to determine state
- **Removed `prediction_complexity`** (the "cold-start-simple" / "complete" binary) → every prediction uses the unified complete 7-component structure, and **the confidence level is derived from calibration_samples**
- **Removed `bucket_scheme`** (the four tiers "ratio" / "absolute" / "absolute_with_ratio" / "percentile") → bucket boundaries are **derived automatically** by a single algorithm: with `baseline_plays` → by multiple; without → platform-generic defaults; samples ≥10 → recompute the baseline

Reason: hard mode switching was the designer's guess, not what the user experience should be. A unified flow + progressive confidence labeling better matches the fact that "a channel is a continuously evolving spectrum, not discrete stages".

---

## Field reference (semantics of each field + who writes, who reads)

### Metadata

| Field | Type | Writer | Reader | Description |
|---|---|---|---|---|
| `schema_version` | string | cheat-init / cheat-migrate | all skills | "1.1". Bumped when the schema is upgraded; existing users upgrade via [/cheat-migrate](../skills/cheat-migrate/SKILL.md). See [migration-protocol.md](migration-protocol.md) |
| `skill_version` | string | cheat-init | all skills | Current cheat-on-content version |
| `initialized_at` | ISO 8601 | cheat-init | cheat-status | First initialization time, never changes |

### Mode and configuration

| Field | Type | Values | Writer | Reader |
|---|---|---|---|---|
| `rubric_version` | string | "v0" / "v1" / "v2" / ... | cheat-init / cheat-bump | cheat-score / cheat-predict / cheat-retro |
| `content_form` | enum | "opinion-video" / "long-essay" / "short-text" / "podcast" / "other" / "mixed" | cheat-init | cheat-predict / cheat-recommend |
| `typical_duration_seconds` | int | The user's typical video duration. Determines the word count cheat-seed writes into a draft + cheat-predict's preference for anchors of the same duration | cheat-init | cheat-seed / cheat-predict |
| `target_publish_cadence_days` | int / null | The user's target publishing cadence (1 = daily / 2 = every other day / 7 = weekly / null = flexible). Determines the buffer warning color thresholds | cheat-init | cheat-status / cheat-recommend / cheat-shoot / cheat-publish / SessionStart hook |
| `rubric_form_mismatch` | bool | true means content_form ≠ opinion-video but the user still starts from the built-in opinion rubric — reminds the user to adjust weights at bump time | cheat-init | cheat-status (keeps reminding) |
| `benchmark_status` | enum | "none" / "imported" / "pending" (the user promised to find one later) | cheat-init / cheat-learn-from | cheat-seed (reads benchmark.md while brainstorming) / cheat-status (keeps reminding while pending) |
| `benchmark_name` | string / null | The benchmark account name (e.g. "Snail Senior Study Abroad"); null when none | cheat-learn-from | cheat-status / cheat-seed |
| `benchmark_sample_count` | int | Number of benchmark videos imported | cheat-learn-from (write / append) | cheat-status (suggests fading benchmark influence at N≥10) |
| `baseline_plays` | int / null | The user's baseline play count; at first init, the median if scrape history exists → otherwise null; later backfilled from the first cheat-retro with actual performance | cheat-init / cheat-retro / cheat-bump (--bucket-only) | cheat-predict (derives bucket boundaries) |
| `data_collection` | enum | "manual" / "adapter" | cheat-init | cheat-retro (determines the DATA_SOURCE default) |
| `pool_status` | enum | "none" / "markdown" / "notion" / "sqlite" | cheat-init / cheat-recommend | cheat-recommend / cheat-status |
| `data_layer` | enum | "markdown" / "sqlite" | cheat-init / md-to-sqlite.py | all skills that read predictions |
| `hooks_installed` | bool | true / false | cheat-init | cheat-status (keeps reminding) |
| `enabled_trend_sources` | array of string | List of trend-source adapter names (e.g. `["weibo-hot", "zhihu-hot"]`) | cheat-init / manual user edit | cheat-trends |
| `enabled_perf_adapters` | array of string | List of perf-data adapter names (e.g. `["douyin-session"]`). Empty → cheat-retro uses manual paste | cheat-init / manual user config | cheat-retro |

### Cumulative counters

| Field | Type | Writer | Purpose |
|---|---|---|---|
| `calibration_samples` | int | cheat-retro (+1 per successful retro) | cheat-status progress bar / cheat-bump threshold |
| `calibration_samples_at_last_bump` | int | cheat-bump | "How many new samples since the last bump" |

### Timestamps (last_X_at)

| Field | Type | Writer |
|---|---|---|
| `last_bump_at` | ISO 8601 / null | cheat-bump |
| `last_bump_self_audited` | bool | cheat-bump (true when CROSS_MODEL_AUDIT=false) |
| `last_published_at` | ISO 8601 / null | cheat-publish |
| `last_published_file` | string / null | cheat-publish |
| `last_retro_at` | ISO 8601 / null | cheat-retro |
| `last_trends_run_at` | ISO 8601 / null | cheat-trends |
| `last_trends_added_count` | int | cheat-trends |
| `last_prediction_self_scored` | bool | cheat-predict (true when `--skip-blind` or Phase 2.5 chose b; cleared back to false the next time the sub-agent path is used) |
| `last_self_scored_at` | ISO 8601 / null | cheat-predict (kept in sync with `last_prediction_self_scored`) |

### List queues

| Field | Type | Writer | Reader | Protocol |
|---|---|---|---|---|
| `consecutive_directional_errors` | array of "high"/"low" | cheat-retro (push) / cheat-bump (clear) | cheat-status / cheat-retro self-check | Direction of misses in the last N retros; 3 same-direction misses in a row trigger a bump proposal |
| `pending_retros` | array of file path | cheat-publish (push) / cheat-retro (remove) | cheat-status | Paths of prediction files awaiting retro |
| `shoots` | array of {video_folder, prediction_file, shot_at, ad_hoc, scripts_path, script_consistency, script_diff_pct, v2_prediction_written, script_hash_at_shoot} | cheat-shoot (push) / cheat-publish (remove) | cheat-status / cheat-recommend / SessionStart hook | Shot-but-unpublished queue. `len(shoots) = buffer count`; `buffer_days = buffer × target_publish_cadence_days` determines the color. See cheat-shoot Phase 4 for semantics of the v1.2 fields |

### Session state

| Field | Type | Writer | Reader | Protocol |
|---|---|---|---|---|
| `in_progress_session` | object / null | cheat-predict (create) / cheat-publish (clear) | cheat-publish / cheat-status | See "in_progress_session substructure" below |

#### `in_progress_session` substructure

```json
{
  "type": "prediction",
  "file": "predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md",
  "started_at": "2026-05-04T14:00:00+08:00",
  "rubric_version": "v2"
}
```

`type`: currently only `"prediction"`. In the future a `"bump"` value may be added to indicate a long-running bump is in progress.

---

## Read/write protocol

### Reading (any skill)

```python
# pseudocode
import json, os

state_path = os.path.join(os.getcwd(), ".cheat-state.json")
if not os.path.exists(state_path):
    # missing = the user has not initialized; route to /cheat-init
    raise NeedsInitError()

with open(state_path) as f:
    state = json.load(f)

# check schema_version compatibility
LATEST_SCHEMA = "1.1"  # see migrations/registry.md
if state.get("schema_version") != LATEST_SCHEMA:
    # do not raise directly — tell the user to run /cheat-migrate (non-blocking)
    log_warning(f"schema version mismatch: state={state.get('schema_version')}, expected={LATEST_SCHEMA}. Recommended: run /cheat-migrate")
    # a MINOR mismatch can usually continue; with MAJOR some field reads may KeyError → fall back with .get(field, default)
```

**Key discipline**:
- After reading, do not immediately care about missing fields — tolerate them with `state.get(field, default)`. When a new skill version introduces new fields, an old state file will lack them; default gracefully instead of crashing
- **Never** mutate state in memory and forget to write it back — downstream skills read the on-disk version

### Writing (any skill)

```python
# pseudocode — read-modify-write pattern
state = read_state()
state["calibration_samples"] += 1
state["last_retro_at"] = now_iso()
write_state(state)

def write_state(state):
    state_path = os.path.join(os.getcwd(), ".cheat-state.json")
    tmp_path = state_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, state_path)  # atomic rename
```

**Key discipline**:
- **Atomic write**: write to .tmp → rename. Avoids a half-written corrupted state file
- **Always indent=2**: human-readable, easy for the user to hand-edit and for git diff
- **ensure_ascii=False**: keep non-ASCII characters instead of escaping them as \uXXXX
- **Write before continuing**: avoids downstream skills reading stale values

### Concurrency model

Expected scenario: **single user + single Claude Code session**. No locking.

If two sessions operate on the same project in parallel (rare and not recommended): write overwrites may occur. **If this is ever needed**, add a file lock (`fcntl.flock`); do not add it now, to avoid complexity.

---

## Field write-ownership table (prevents ambiguity about "who should write this field")

| Field | Sole writer | When it writes |
|---|---|---|
| `rubric_version` | cheat-init / cheat-bump | init writes the initial value; bump advances the version |
| `baseline_plays` | cheat-init / cheat-retro / cheat-bump (--bucket-only) | at init, median if an adapter pulled history → otherwise null; the first retro with actual performance → backfill; bump --bucket-only → recompute |
| `calibration_samples` | cheat-retro | +1 each time a retro is successfully persisted |
| `pending_retros` | cheat-publish (push) / cheat-retro (remove) | publish pushes the current piece; retro removes it when done |
| `consecutive_directional_errors` | cheat-retro (push) / cheat-bump (clear) | retro pushes when it judges the miss direction; bump clears when it lands |
| `in_progress_session` | cheat-predict (create) / cheat-publish (clear) | predict creates it when the file is written; publish clears it on registration |
| `last_bump_at` | cheat-bump | when the bump lands |

**Multiple skills writing the same field is never allowed** — it shatters the semantics of the state. If a new field is needed in the future, first decide "who is the sole writer".

---

## Handling a corrupted / inconsistent state file

| Symptom | Handling |
|---|---|
| File does not exist | Show "not initialized, please run /cheat-init"; do **not** auto-create |
| JSON parse failure | Show "state file corrupted: path/to/.cheat-state.json"; recommend manual repair or backup + re-init |
| schema_version unrecognized | Show the version number + recommend running [/cheat-migrate](../skills/cheat-migrate/SKILL.md). The SessionStart hook detects and warns automatically |
| `pending_retros` contains a deleted file | cheat-status removes it quietly during its check; no error |
| `in_progress_session` file no longer exists | cheat-status detects it → asks the user whether to clean it up |
| `calibration_samples` disagrees with the actual retro count under `predictions/` | cheat-status reports the difference. A temporary hand-edit of state is fine; a persistent disagreement is a bug and a reconciliation step should be added to cheat-migrate in the next minor version |

---

## Relationship with git

`.cheat-state.json` **should** be version-controlled:
- ✅ It is a snapshot of project configuration + cumulative metrics
- ✅ git history provides a complete trace of state evolution
- ✅ Multi-device sync relies on git push/pull
- ❌ It does **not** contain sensitive information (cookies / API keys belong in `.env` or `.cheat-secrets.json`, gitignored separately)

The `.cheat-cache/` directory **should not** be version-controlled:
- It contains `usage.jsonl` (local logs from the meta-logging hook)
- It contains `trends-history.jsonl` (the dedup cache for trend fetches)
- It may also contain adapter debug files (e.g. `douyin-session-debug/`)
- These are device-local states; syncing them across devices is meaningless

`/cheat-init` should automatically append (not overwrite) to the user project root `.gitignore`:

```
.cheat-cache/
.cheat-secrets.json
```

---

## Upgrade path

For the complete philosophy and maintainer checklist, see [migration-protocol.md](migration-protocol.md). Short version:

When the schema changes in the future:
1. Bump `schema_version` (e.g. "1.1" → "1.2")
2. Write `migrations/<old>-to-<new>.md` (4 sections: WHAT/WHY/HOW/Manual fallback)
3. Update the `LATEST_SCHEMA` marker in `migrations/registry.md` + the version-chain table
4. The SessionStart hook automatically tells the user to run `/cheat-migrate` when it detects a mismatch
5. **Never** let a skill silently tolerate deleted or renamed fields from an old schema — that turns "which field means what under which version" into a mystery

Adding a field (MINOR, non-breaking):
- Read it with `state.get(field, default)`
- Old state files automatically get the default
- **Still bump schema_version + write a migrations file** — to guarantee the state file eventually converges; but the user may delay running migrate

Delete / rename / change semantics (MAJOR, breaking):
- Must bump schema_version + write a migration file
- Mark `BREAKING` in the CHANGELOG

---

## Boundaries of user hand-editing the state file

Fields that are allowed to be hand-edited:
- `enabled_trend_sources` (array; determines which sources cheat-trends uses)
- `data_collection` (switch manual ↔ adapter)

Fields **not** recommended for hand-editing (they break invariants):
- `calibration_samples` / `pending_retros` / `consecutive_directional_errors` (should be updated through the retro flow)
- `rubric_version` (should be updated through the bump flow)
- `in_progress_session` (should be updated through the predict/publish flow)

If the user really wants a reset: recommend **deleting the whole .cheat-state.json + re-running /cheat-init** — that is safer than hand-editing a single field.

---

## Confidence label derivation table (**single source of truth**)

Used jointly by cheat-predict / cheat-status / cheat-recommend / the SessionStart hook, etc. Derived from `calibration_samples`; every skill uses the same logic:

| `calibration_samples` | confidence emoji + label | Numerical meaning | How the user should use it |
|---|---|---|---|
| 0 | 🔴 Very low | "astrology tier, pure discipline training" | Do not decide whether to publish based on the composite; writing a prediction is for **collecting data**, not for **making decisions** |
| 1-2 | 🟠 Low | "center ±50%, directional sense beats absolute numbers" | Trust the direction "A beats B on traffic"; do not trust specific numbers |
| 3-5 | 🟡 Low-ish | "center ±40%, usable as one reference" | Bucket ordering is usable; the center point estimate is still a guess |
| 6-10 | 🟢 Medium | "center ±25%, can participate in decisions" | Can serve as one basis for "should I publish" |
| 11-20 | 🟢 Fairly high | "center ±15%, rubric shape is stable" | Trustworthy center estimates |
| 21+ | 🔵 High | "center ±10%, data-driven bumps possible" | Enters the data-driven stage — bumps use regression rather than intuition |

> The ±X% in the table above are **empirical values** (based on the reference creator's real calibration curve), not a mathematically strict guarantee. A new account's real ±X% can only be verified once it has produced its own score-curve.png.

**Do not use this table to gate any feature** — every skill runs the same flow at every calibration_samples level; the output only **displays** the current confidence level. This is the core principle of the new design.
