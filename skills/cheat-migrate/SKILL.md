---
name: cheat-migrate
description: Upgrade a legacy user's .cheat-state.json to the current schema_version. Reads migrations/registry.md to compute the migration chain, then applies each migration file in order. Idempotent: running twice yields the same result. On failure it stops at the intermediate version without advancing. Triggers: "迁移" / "升级 state" / "migrate" / "我的 state 是老版本" / "schema 版本不对".
argument-hint: "[— from: <version>] [— to: <version>] [— dry-run]"
allowed-tools: Bash(*), Read, Write, Edit, Skill
---

# /cheat-migrate — Schema version migration

Upgrade the user's `.cheat-state.json` from an older `schema_version` to the `LATEST_SCHEMA` currently expected by cheat-on-content.

---

## Overview

```
[User: migrate / or the user runs it after a SessionStart prompt]
  ↓
[Phase 0: read .cheat-state.json + migrations/registry.md → determine the migration chain]
  ↓
[Phase 1: dry-run (default) shows the migration plan, waits for user confirmation]
  ↓
[Phase 2: back up .cheat-state.json → .cheat-state.json.backup-<timestamp>]
  ↓
[Phase 3: apply the HOW section of the matching migration file for each step in order]
  ↓
[Phase 4: verify the upgraded state file parses + schema_version is updated]
  ↓
[Phase 5: report + note that backups may need cleanup]
```

---

## Constants

- **REGISTRY_PATH = `${SKILL_DIR}/../../migrations/registry.md`** — single source of truth for the version chain
- **MIGRATIONS_DIR = `${SKILL_DIR}/../../migrations/`** — migration files directory
- **DRY_RUN_BY_DEFAULT = true** — the first run shows the plan and does not modify files directly
- **BACKUP_BEFORE_WRITE = true** — always back up before writing; backups are kept until the next successful init / manual user cleanup
- **STOP_ON_STEP_FAILURE = true** — any step failure → stop at the intermediate version, do not advance, do not roll back

> 💡 Override at call time: `/cheat-migrate — dry-run: false` executes directly / `/cheat-migrate — to: 1.2` upgrades only to the specified version

---

## Inputs

| Required | Source |
|---|---|
| `.cheat-state.json` | user project root |
| `migrations/registry.md` | LATEST_SCHEMA + version-chain table |
| `migrations/<from>-to-<to>.md` | concrete migration instructions per step |

---

## Workflow

### Phase 0: Determine the migration chain

1. Read `.cheat-state.json` → parse `current_version = state.schema_version`
2. Read `migrations/registry.md` → parse the `LATEST_SCHEMA` field (line: `LATEST_SCHEMA = "X.Y"`)
3. Parse the `args.to` override (if any); otherwise target = LATEST_SCHEMA
4. Parse the `args.from` override (rare case: the user's state file has a broken schema field and the starting point must be forced)
5. **State decision**:
   - `current_version == target` → output "✅ state is already {target}; no migration needed" → exit
   - `current_version > target` (e.g. the user ran a dev build and switched back to release) → error "cannot downgrade; adjust manually or re-init"
   - `current_version < target` → continue; look up the migration chain in the registry
6. Compute `chain = [(from, to, file), ...]` from the registry's "version chain" table, linking current → target in order

If a step is missing from the registry (e.g. `current_version` is not in the table) → error and show "currently known versions: [1.0, 1.1, ...]" for the user to check.

### Phase 1: Dry-run

Output the migration plan:

```
📋 Migration plan

Current version: 1.0
Target version: 1.2
Will run 2 steps in order:

  [1/2] 1.0 → 1.1 (MINOR)
       Added fields: typical_duration_seconds, target_publish_cadence_days, ... (12 fields total)
       Removed fields: mode, prediction_complexity, bucket_scheme
       See: migrations/1.0-to-1.1.md

  [2/2] 1.1 → 1.2 (MINOR)
       Added fields: [...]
       See: migrations/1.1-to-1.2.md

⚠️ Backup location: .cheat-state.json.backup-<timestamp>

Continue? Reply yes to execute / no to exit / dry-run-detail to see exactly what each step changes.
```

If `args["dry-run"] == false` or the user replies yes → go to Phase 2.

### Phase 2: Backup

```bash
cp .cheat-state.json .cheat-state.json.backup-$(date +%s)
```

Output: "📦 Backed up to .cheat-state.json.backup-1714838400"

### Phase 3: Apply each step in order

For each (from, to, file) in the chain:

1. Output "→ [N/M] applying {file}..."
2. Read `migrations/<file>` → find the `## HOW (Claude steps for /cheat-migrate)` section
3. **Execute the natural-language steps in that section one by one** — this is the key: migrations are run by Claude reading markdown, not by a python script
4. After each step:
   - Update the in-memory state.schema_version = to
   - **Atomically write** to disk (write .tmp → rename)
5. If a step fails:
   - Output "❌ {file} step N failed: {error}"
   - Do not advance, do not roll back (state remains at the intermediate version where the previous step succeeded)
   - Prompt: "Stopped at schema_version: {last_success_version}. After fixing, rerunning /cheat-migrate will continue from here"
   - Exit

### Phase 4: Verify

After the upgrade:
1. Read `.cheat-state.json` → parse → should succeed
2. Check `schema_version == target`
3. Check that all "required fields" are present (see the full schema in [shared-references/state-management.md](../../shared-references/state-management.md))
4. Failure → error "migration completed but verification failed: {detail}. The state file may be inconsistent — restore from the backup"

### Phase 5: Report

```
✅ Migration complete

  From: 1.0
  To: 1.2
  Steps applied: 2

The state file now has X fields, all verified.

📦 Backup kept: .cheat-state.json.backup-1714838400
   (you may rm it manually once everything looks fine; the next successful /cheat-init also cleans up expired backups)

Next steps:
  - Run /cheat-status to confirm the dashboard is normal
  - If hooks need reinstalling, run bash <skill_repo>/install.sh --reinstall-hooks
```

---

## Key Rules

1. **Idempotent**: rerunning on an already-upgraded state should exit immediately with "no migration needed" and **must not** reapply steps. Implemented by comparing `current_version == target`
2. **Do not skip versions**: 1.0 → 1.3 must go 1.0→1.1→1.2→1.3 in order; each step is independently recoverable. A "combined migration that goes 1.0 → 1.3 directly" is not allowed
3. **No silent compatibility**: an unrecognized state-file schema_version → explicitly error "unknown version X, latest known version Y"; do not pretend to continue
4. **Failure stops in place**: when step N fails, schema_version stays at the last successfully applied version N-1 and does not roll back to pre-migration. A rerun continues from the breakpoint
5. **Backup is a hard constraint**: always back up before writing. Even if the user runs `--dry-run: false`, the backup still executes
6. **Do not touch predictions / rubric / videos**: only `.cheat-state.json` changes. Other user data is owned by its respective skill; the migration skill does not touch it
7. **MAJOR vs MINOR transparency**: dry-run output must label (MAJOR) / (MINOR). For MAJOR, additionally warn "old skills reading old fields will break; after migrating you cannot roll back to an old skill version"

---

## Refusals

- "Skip dry-run and overwrite my state now" → **allowed** (`--dry-run: false`), but the backup is still mandatory
- "My state is corrupted / the schema_version field is gone; can you guess a version and run?" → you may specify `--from: 1.0`, but warn "a guess-based migration may misalign fields"
- "Downgrade to an old version (current > target)" → refuse. Schema evolution is one-way. To downgrade, manually cp a historical git snapshot
- "Merge multiple migration steps into one atomic operation" → refuse. Independent recoverability per step is a core design principle
- "Run migrate in the middle of cheat-bump / cheat-predict" → refuse. Wait until the other skill finishes, to avoid corrupting in_progress_session state

---

## Integration

- Upstream: the SessionStart hook detects `state.schema_version != LATEST_SCHEMA` → outputs a red warning + suggests running `/cheat-migrate`
- Upstream (manual): after the user git pulls a new version and sees BREAKING in CHANGELOG → runs it proactively
- Downstream: after it runs, every other skill reading state gets the latest fields
- With `cheat-init`: init writes a new state directly at LATEST_SCHEMA and does not need migrate
- With `install.sh --reinstall-hooks`: migration does **not** reinstall hook scripts (hook scripts are skill-package code, not user state). The two are decoupled

---

## State field reads/writes

This skill **writes**:
- `schema_version` (updated after each successful step)

This skill **reads**:
- All existing fields (depending on the HOW steps in the specific migration file)

This skill **never** writes:
- Business state such as `calibration_samples` / `pending_retros` / `shoots` (those are other skills' responsibilities)
- Exception: a migration file explicitly says "deriving the value of a new field requires scanning predictions/ to compute baseline_plays" — that is initializing a new field, not changing an old one

---

## Examples

### Example 1: User upgrades from v0.1.0 to v0.2.0 (assume 0.2 introduced schema 1.2)

```
User: migrate
Claude: [runs cheat-migrate]
  Phase 0: current=1.1, target=1.2, chain=[(1.1, 1.2)]
  Phase 1: dry-run prints the plan
  User: yes
  Phase 2: backup
  Phase 3: apply 1.1-to-1.2.md (MINOR: adds platform_metrics_url and other fields)
  Phase 4: verification OK
  Phase 5: report ✅
```

### Example 2: User skipped multiple versions

```
User: I upgraded from v0.1.0 to v0.5.0, but state is still 1.0
Claude: [runs cheat-migrate]
  Phase 0: current=1.0, target=1.4 (LATEST), chain=[(1.0, 1.1), (1.1, 1.2), (1.2, 1.3), (1.3, 1.4)]
  Phase 1: dry-run prints a 4-step plan
  ...
```

### Example 3: Migration fails midway

```
Phase 3:
  → [1/4] applying 1.0-to-1.1.md ✓
  → [2/4] applying 1.1-to-1.2.md ✓
  → [3/4] applying 1.2-to-1.3.md... ❌ failed: user's baseline_plays field contains a non-numeric value and cannot be converted to int

state has stopped at schema_version: 1.2.
After fixing .cheat-state.json, rerunning /cheat-migrate will continue from 1.2 → 1.3.
```
