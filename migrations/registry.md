# Migrations Registry

The single source of truth for cheat-on-content's schema version evolution. `/cheat-migrate` reads this file to decide which migrations to run.

---

## Current schema_version

**`1.4`** — written by `cheat-init` Phase 3 into new state files.

The `LATEST_SCHEMA` marker below is referenced by the `cheat-migrate` skill and the SessionStart hook:

```
LATEST_SCHEMA = "1.4"
```

> Maintainer note: when bumping this value you **must** add the corresponding migration file + append a row to the "Version chain" below.

---

## Version chain

In chronological order, each row represents one schema upgrade. `/cheat-migrate` uses this table to compute which steps must run, in order, from the user's current version to LATEST_SCHEMA.

| from | to | breaking? | Migration file | Description |
|---|---|---|---|---|
| (none) | 1.0 | — | (built-in) | v1's first schema |
| 1.0 | 1.1 | NO | [1.0-to-1.1.md](1.0-to-1.1.md) | Remove the three enum fields `mode` / `prediction_complexity` / `bucket_scheme`; add `target_publish_cadence_days` / `baseline_plays` / `benchmark_*` / `shoots` etc. |
| 1.1 | 1.2 | NO | [1.1-to-1.2.md](1.1-to-1.2.md) | Extend `shoots[]` items with 5 fields (`scripts_path` / `script_consistency` / `script_diff_pct` / `v2_prediction_written` / `script_hash_at_shoot`) — supports the "post-shoot script change triggers v2 prediction re-judgment" workflow |
| 1.2 | 1.3 | NO | [1.2-to-1.3.md](1.2-to-1.3.md) | Add `last_prediction_self_scored: bool` + `last_self_scored_at` — supports the channel B isolated scoring introduced with the cheat-score-blind sub-agent. `true` means the last prediction used `--skip-blind`, and cheat-status keeps nagging |
| 1.3 | 1.4 | **BREAKING for blind channel** | [1.3-to-1.4.md](1.3-to-1.4.md) | Split the rubric file: `rubric_notes.md` → `rubric_notes.md` (blind whitelist, generic language) + `rubric-memo.md` (hard-forbidden for blind, contains real video names/actual performance). State fields unchanged; legacy users must run migrate to split their existing rubric_notes.md. If not → the blind sub-agent will keep marking non_blind_warning |

---

## Migration file naming convention

- Filename: `<from>-to-<to>.md` (e.g. `1.1-to-1.2.md`)
- Each must contain 4 sections:
  1. **WHAT changed** — field-level diff (added / removed / renamed)
  2. **WHY** — why this change
  3. **HOW (Claude steps)** — natural-language steps Claude executes in order when running `/cheat-migrate`
  4. **Manual fallback** — minimal instructions for hand-editing `.cheat-state.json` if the user does not want to run the skill

---

## Philosophy (see [shared-references/migration-protocol.md](../shared-references/migration-protocol.md))

- **MINOR bump** (e.g. 1.1 → 1.2): only adds fields or softens enum values. Old state reads defaults via `state.get(field, default)` and **may skip migrate** — but running it makes the state file complete
- **MAJOR bump** (e.g. 1.x → 2.0): removes fields / renames fields / changes field semantics. Old state **must** run migrate, otherwise skills read inconsistent fields
- **Version skipping is not allowed**: a 1.0 user upgrading to 1.3 must run 1.0→1.1, 1.1→1.2, 1.2→1.3 in order. Each step is idempotent
- **Failure stops in place**: if step N fails, state.schema_version remains N-1 (not the target version). After fixing, a rerun continues from the breakpoint

---

## For developers: adding a migration

When bumping the schema (in order):

1. Decide whether it is MINOR or MAJOR (see the philosophy section above)
2. Change the hardcoded `schema_version` in `cheat-init/SKILL.md` to the new value
3. Change the `LATEST_SCHEMA = "X.Y"` marker in this file
4. Append a row to this file's "Version chain" table
5. Create `migrations/<old>-to-<new>.md` with all 4 sections filled
6. Mark CHANGELOG.md as `BREAKING` (major) or `MINOR`, with a link to the migration file
7. Run it once: on a fixture old state, run `/cheat-migrate` and verify it upgrades to the new version with all state fields present

If you cannot be bothered to write the standard 4-section migration file, **defer** the schema bump until the next sizeable change — do not bump the schema first and write the docs later.
