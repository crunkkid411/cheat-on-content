# Migration Protocol (schema evolution philosophy)

Referenced by the `cheat-migrate` skill / `cheat-init` / the SessionStart hook / maintainers. Defines how to safely evolve the `.cheat-state.json` schema without interrupting existing users.

---

## Core principles

1. **Every release must keep old users' state working** — either upgrade it through migrate, or stay compatible via `state.get(field, default)`
2. **MINOR change = add a field / loosen an enum**; the old state works without running migrate (missing fields fall back to defaults), and running it makes the state complete
3. **MAJOR change = delete a field / rename / change semantics**; the old state **must** run migrate, otherwise a skill reading inconsistent fields will break
4. **Skipping versions is not allowed**; a multi-version upgrade must apply each step in order. Every step is idempotent
5. **On failure, stop where you are**; do not roll back, let the user fix the breakpoint and continue
6. **schema_version is monotonically increasing**; downgrades are not allowed (if you need one, `cp` a historical git snapshot)

---

## When a change is MINOR vs MAJOR

### MINOR scope (old state still works without migrate)

- Adding a field (with a well-defined default; old skills neither read it nor break)
- Loosening an enum (e.g. `"strict" / "lenient"` gains a third `"adaptive"`; old values remain valid)
- Adding a new optional value to a field (e.g. a new element in a list field)
- Changing a default (without changing semantics)

### MAJOR scope (migrate is mandatory)

- **Deleting a field** — old skills still write it, new skills do not read it, which creates ambiguity
- **Renaming a field** — old/new skills cannot see what the other wrote
- **Changing field semantics** (e.g. `mode` from enum to integer; `baseline_plays` from int to list)
- **Changing enum values** (e.g. `"opinion-video"` becomes `"opinion_video"`; old values are no longer valid)
- **Splitting / merging fields**

> In ambiguous cases, **conservatively judge it MAJOR** — writing one extra migration file is better than breaking the user's state.

---

## Maintainer checklist: 4 things you must do when bumping the schema

Every time you prepare a release and have changed the state schema:

### 1. Change the hardcoded schema_version that cheat-init writes into a new state

```diff
- "schema_version": "1.1",
+ "schema_version": "1.2",
```

Location: the state-writing section of `skills/cheat-init/SKILL.md` Phase 3.

### 2. Change the LATEST_SCHEMA marker in migrations/registry.md

```diff
- LATEST_SCHEMA = "1.1"
+ LATEST_SCHEMA = "1.2"
```

And append a new row to the "version chain" table:

```
| 1.1 | 1.2 | NO/YES | [1.1-to-1.2.md](1.1-to-1.2.md) | One-line description |
```

### 3. Write migrations/<old>-to-<new>.md

4 required sections (see the `1.0-to-1.1.md` template):
- WHAT changed
- WHY
- HOW (Claude steps for /cheat-migrate)
- Manual fallback

> If you cannot write all 4 sections, the change is too complicated and not thought through — this schema bump should not ship.

### 4. Tag the version number + link in CHANGELOG.md

```markdown
## [0.2.0] — YYYY-MM-DD

### BREAKING / MINOR

- schema_version 1.1 → 1.2: <one-line description>. Migration guide: [migrations/1.1-to-1.2.md](migrations/1.1-to-1.2.md)
- ...
```

Use `### MINOR` for MINOR and `### BREAKING` for MAJOR, and make it prominent.

---

## How skills read state internally (defensive programming)

Every skill **must** use the `state.get(field, default)` pattern when reading state:

```python
# good
target_cadence = state.get("target_publish_cadence_days", None)
benchmark_status = state.get("benchmark_status", "none")
shoots = state.get("shoots", [])

# bad (KeyError when an old state lacks this field)
target_cadence = state["target_publish_cadence_days"]
```

Reasons:
- On a MINOR upgrade, the old state lacks new fields — the `get` pattern lets the skill fall back to defaults automatically
- The user hand-edited the state and deleted a field — same as above
- Reduces the hard dependency inside skills on "you must migrate before it runs"

**Exception**: core identity fields may be indexed directly (e.g. `state["schema_version"]`, `state["rubric_version"]`) — when these are missing, the state file is fundamentally invalid and should error explicitly.

---

## Role of the SessionStart hook

The hook checks at the start of every session:

```bash
state_schema=$(jq -r '.schema_version // "unknown"' "$STATE_FILE")
if [[ "$state_schema" != "$LATEST_SCHEMA" ]]; then
  echo "⚠️ schema version mismatch: state=$state_schema, skill expects=$LATEST_SCHEMA"
  echo "   recommended: run /cheat-migrate to upgrade (does not block further work)"
fi
```

**Non-blocking**: the user may choose to "keep working for now and run migrate later". With a MINOR mismatch most functionality still runs; with MAJOR some skills may error — running migrate then is still soon enough.

---

## For developers: practices that avoid frequent schema bumps

Not every change needs a schema bump. The philosophy:

- **Prefer MINOR**: add fields when you can; delete fields rarely. Deleting fields upsets existing users
- **Batch bumps**: accumulate 3-5 MINOR changes and release together instead of bumping on every small edit
- **Delay bumps**: if 90% of users will never use a MINOR field, **do not** rush the schema bump — let the field quietly work through `state.get(field, default)` and bump on the next release
- **Avoid MAJOR**: never use MAJOR when MINOR can solve it. E.g. instead of renaming a field, keep the old field + add a new one (mark the old one deprecated and delete it in the next MAJOR release)

---

## Backup retention policy

Before writing, `/cheat-migrate` backs up to `.cheat-state.json.backup-<timestamp>`.

How long backups are kept:
- When the user runs `/cheat-status`, if backups exist + the state has run stably for N days → suggest "you can clean up N old backups"
- `/cheat-init` cleans all old backups when re-initializing (since you are re-initializing, old backups have little value)
- The user manually running `rm .cheat-state.json.backup-*` is always OK

Not version-controlled: `.cheat-state.json.backup-*` should be in `.gitignore` (the `.cheat-state.json` wildcard rule already covers it).
