# Cadence Protocol

Referenced by these sub-skills: `cheat-status`, `cheat-recommend`, `cheat-shoot`, `cheat-publish`, and the SessionStart hook.

Cement "what to do on which day" — so the user does not have to drive every step. Claude can answer "should I shoot / publish / retro now?" at the start of a session.

---

## Three layers of cadence

### Daily (every day / every session start)

1. The SessionStart hook automatically renders a 4-6 line report:
   - 📦 Buffer status (color + count)
   - ⏰ Retros that are due
   - 🎯 Candidate-pool top 3 (rough ranking)
   - 📅 Last trend fetch time
   - ⚠️ Key to-dos
2. Do not proactively start any action — wait for the user to decide

### Event-level (due at T+`RETRO_WINDOW_DAYS` days)

- Any published-but-not-retroed piece whose time has come → highlighted at the top of SessionStart
- The user supplies data (paste / URL) → `/cheat-retro` runs automatically

### Weekly (the user-chosen "batch day")

- Fetch trends (`/cheat-trends`) to refresh the candidate pool
- Check rubric bump triggers
- Check whether STATUS.md / rubric_notes.md need cleanup

---

## Buffer warning rules

**Buffer = the length of the `state.shoots` array** = the number of videos shot but not published.

`/cheat-shoot` adds a video to `state.shoots`; `/cheat-publish` removes it — separating the two events makes buffer tracking accurate.

### Color thresholds (derived from `target_publish_cadence_days`)

`buffer_days = buffer_count × target_publish_cadence_days`

| buffer_days | Color | Meaning | Action |
|---|---|---|---|
| < 1 | 🔴 **Red** | Warning — the next publish day may slip | **Must shoot today**, and only shoot a safe bet (top 1, no gambling) |
| 1-2 | 🟠 Orange | Low | Should shoot 1-2 pieces |
| 3-5 | 🟢 Green | Normal | Steady cadence; shoot or rest as you like |
| > 5 | 🔵 Blue | Backlog | **Pause shooting**; focus on publishing inventory + retros |

**Examples**:
- User cadence = 1 (daily), buffer count = 0 → buffer_days = 0 → 🔴
- User cadence = 7 (weekly), buffer count = 1 → buffer_days = 7 → 🔵 (one piece covers seven days)
- User cadence = 1, buffer count = 4 → buffer_days = 4 → 🟢

### Flexible cadence (target_publish_cadence_days = null)

If the user chose "flexible / no fixed schedule" in cheat-init → buffer monitoring is **off**. The SessionStart report only shows "shot but unpublished: N", with no color and no warning.

---

## Topic strategy (when `/cheat-recommend` proposes ≥ 2)

Every 2-topic recommendation follows the **1 safe bet + 1 experiment** principle:

### Piece 1 (safe bet)

- Ranking top 1-3
- Category does **not** repeat the last N published pieces (N = max(3, target_publish_cadence_days × 3), avoiding audience fatigue)
- High composite + topic safety (not risky)

### Piece 2 (experiment)

- A candidate-pool sample that can verify a **hypothesis to verify** (e.g. an A/B comparison for a new dimension)
- Or verify a **new pattern** (Pattern N in [script_patterns.md](script_patterns.md))
- Composite need not be top, but it must have "information value" — after the retro it should move the rubric / pattern library forward

### How buffer color overrides recommendations

| Buffer color | Recommendation override |
|---|---|
| 🔴 Red | **Only recommend the safe-bet top 1** — no experiment. "Whatever you can shoot today is fine" |
| 🟠 Orange | 1 safe + 1 experiment, but prioritize the safe bet |
| 🟢 Green | Standard 1+1 |
| 🔵 Blue | **Pause recommendations** — reply "your buffer is backlogged; publish inventory + retro first" |

**Key constraints** (apply at every color):
- No more than 2 consecutive pieces in the same category
- Do not recommend candidates already published (marked done)
- Do not recommend a candidate the user actively skipped (marked skip) for 6 months

---

## Cadence meta-rules

In priority order (high → low):

1. **Buffer beats scoring**: during a red warning, do not slip a publish date waiting for "a better topic" — shooting a composite 7.5 safe bet is safer than "waiting for tomorrow's 9.0"
2. **Retro beats new shooting**: on the day T+RETRO_WINDOW_DAYS comes due, **retro first, then consider shooting** — otherwise the data signal is lost and rubric calibration suffers
3. **Publishing beats backlog**: when the buffer is full (blue), stop shooting and publish what you have — the timeliness of already-shot topics decays
4. **At most 1 experiment per day**: when shooting 2 pieces in a day, at least 1 must be a safe bet. **Do not go all-experiment** — during cold-start the experiment failure rate is too high and damages the calibration cadence

---

## Standard "today's workflow" templates

### Case 1: buffer is sufficient + no T+3d retro due

```
SessionStart report → user decides whether to shoot
├─ Shoot → "recommend topic" → cheat-recommend proposes 2 →
│          user picks → /cheat-seed writes draft (cold-start) or user writes it →
│          user revises → script.md → user shoots → "shot videos/<...>/" → cheat-shoot
└─ Don't shoot → wait
```

### Case 2: buffer is sufficient + a T+3d retro is due

```
SessionStart report includes ⏰ retro reminder → user supplies video URL or pastes data →
cheat-retro runs automatically → writes retrospective section → checks bump triggers
├─ Triggered → propose /cheat-bump (not mandatory; user decides)
└─ Not triggered → wait for the next validation sample
```

### Case 3: buffer red warning

```
🔴 First line of SessionStart is a warning → user decides
├─ Shoot → cheat-recommend only proposes the current safe-bet top 1 → shoot immediately
└─ Accept the risk of slipping → user's call; cheat-status keeps reminding
```

### Case 4: buffer blue backlog

```
🔵 SessionStart report says "backlogged" → user decides
├─ Publish → "shipped https://..." → cheat-publish → buffer -1
├─ Retro → see Case 2
└─ Shoot new → cheat-recommend refuses: "your buffer already has N pieces; publish down to ≤3 first"
```

### Case 5: periodic batch day (user-triggered)

```
user says "fetch trends" → cheat-trends → candidate pool updated
+ user says "check whether the rubric should be bumped" → cheat-status checks cumulative same-direction bias
+ user says "check rubric_notes line count" → cheat-status health check
```

---

## Fallback: when the process drifts

If one day the cadence is violated (buffer=0 but the user refuses to shoot / backlog ≥10 but the user keeps shooting), the SessionStart report **explicitly labels it**:

```
❌ You have not published anything new for N days (last publish: YYYY-MM-DD),
   buffer = 0, your channel is currently in a state of "de facto hiatus"
```

or:

```
❌ Your buffer already has N pieces but you are still shooting new ones,
   N of the last N pieces have gone unpublished for more than X days — timeliness decay risk
```

**It will not automatically try to fix anything** — it only reports explicitly; the user decides how to get back on cadence.

---

## Sub-skill responsibility table

| Skill | Cadence responsibility |
|---|---|
| `/cheat-init` | Ask for cadence; write `target_publish_cadence_days`; install the SessionStart hook |
| `/cheat-shoot` | Add the video folder to state.shoots, buffer +1 |
| `/cheat-publish` | Remove the matching item from state.shoots, buffer -1 |
| `/cheat-status` | Compute buffer + color, output the report |
| `/cheat-recommend` | Recommend by buffer color + topic strategy |
| `/cheat-retro` | Update STATUS after the retro (auto-trigger /cheat-status) |
| SessionStart hook | Call /cheat-status to render a 4-6 line report and write it to STATUS.md |

---

## Key differences: cheat-on-content vs the video-analysis project

| Dimension | Video analysis | cheat-on-content |
|---|---|---|
| Cadence source | Defaults to daily (hardcoded in CADENCE.md) | User-supplied (cheat-init asks; 4 options: daily / every other day / weekly / flexible) |
| Buffer thresholds | 0/1/2/3-5/6+ (by "pieces") | 0/1-2/3-5/>5 (by "buffer_days" — derived from the user's cadence) |
| 2-topic strategy | 1 safe + 1 experiment | Same |
| SessionStart report | CLAUDE.md text constraint + Claude's self-discipline | Hook-enforced + Claude reads the hook output |
