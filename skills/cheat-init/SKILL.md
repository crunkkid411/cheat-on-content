---
name: cheat-init
description: First-time onboarding and scaffolding creator for cheat-on-content. Unified flow — every user goes through the same 5-phase loop; the only difference is that "people who have already published videos" get one extra step at init: pull their existing videos to build historical context (so later cheat-seed runs can suggest better-fitting topics and a more accurate baseline). Triggers: "初始化" / "init" / "首次使用" / "我是新用户" / "setup cheat-on-content". **Must run in the user's first session; other sub-skills automatically route here when .cheat-state.json does not exist.**
argument-hint: "[— form: opinion-video|long-essay|short-text|podcast]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-init — first-time onboarding

Take the user from zero to running their first prediction in ≤ 5 minutes (no publishing history) or ≤ 10 minutes (already published and wants to import history).

## Overview

```
[User says "init" for the first time]
  ↓
[Phase 0: Detect current state]
  ↓
[Phase 1: Opening copy — applicability + expectation management]
  ↓
[Phase 2: 6 questions (Q1-Q5 all asked; Q2 decides whether to run user-history import)]
  ↓
[Phase 2.5: Benchmark account — strongly recommended (mandatory for cold-start; optional for users with history)]
  ↓
[Phase 3: Create the scaffolding (including empty scripts/ + videos/ + samples/ dirs + template files including benchmark.md)]
  ↓
[Phase 3.5: user-history import flow (only Q2=has history + user agrees)]
  ↓
[Phase 4: Test whether the hook works]
  ↓
[Phase 5: Give the "what to say next" checklist]
```

## Constants

- **DEFAULT_RETRO_WINDOW_DAYS = 3**
- **INSTALL_HOOKS = ask** — ask by default; `auto` installs directly; `skip` does not install
- **TREND_DEFAULT_SOURCES = ["manual-paste"]**

## Inputs

None. All information is collected from 6 conversational questions.

## Workflow

### Phase 0: Detect current state

1. Read the user's current working directory (**the user's content project, not cheat-on-content itself**)
2. Check whether `.cheat-state.json` already exists:
   - Exists → say "this project seems to be initialized already (state file exists). Re-initializing will overwrite the existing config — confirm?" and wait for explicit confirmation
   - Does not exist → go to Phase 1
3. Check whether core files such as `rubric_notes.md` / `predictions/` already exist — they exist but the state file does not → this is a "half-initialized" state; tell the user and ask "should I infer state from the existing files, or reset?"

### Phase 1: Tell the user the expectations upfront (including applicability check)

Output to the user (verbatim, do not soften):

```
🎯 Cheat on Content — init

Your next piece of content is already rewriting the you of 3 months from now.
The pattern exists objectively; the difference is whether you **see** it or **don't**.
This tool lets you see it.

Over the next 5-10 minutes I'll ask 5-6 questions to understand what you make, what you have, and how you'll use it.
Two things upfront:

1. **Early predictions will be off** — the first 5 pieces are roughly ±50% accurate. That is a mathematical fact.
   The tool labels confidence with 🔴🟠🟡🟢🔵 instead of hiding the numbers —
   you decide whether to trust this one.

2. **Strongly recommended: import a benchmark account** — 5-10 benchmark videos and the tool immediately has anchors.
   Otherwise the first batch of predictions is basically astrology. Q5 will ask again later.

Ready to start?
```

If the user answers "continue" or a similar affirmative → Phase 2.
Do not refuse to proceed based on content_form — every form is allowed; only the `rubric_form_mismatch` field is set to true, and cheat-status keeps reminding the user that "your form needs a bump to adjust weights".

### Phase 2: 6 questions (one at a time; do **not** batch them)

**Q1: Content form**

> "Which of these is your content closest to?
> a) **Opinion video** (commentary / current events / argument / issue discussion / personal opinion) — directly matches the built-in rubric
> b) **Long essay** (WeChat Official Account / Substack / Medium) — can start from the opinion-video rubric and adjust weights at bump time
> c) **Short text / thread** (X / Weibo / Jike) — same as above
> d) **Podcast / long-form video** (YouTube long-form / podcast) — same as above
> e) **Tutorial / tool how-to / builder** (teaching people how to use tool X / build project Y) — same as above
> f) **Other** (gaming / food / makeup / news / drama) — the workflow is generic, but the rubric dimensions need adjusting
>      (ER / SR / HP may not predict well for your form; you'll need to derive dimensions that fit)
> g) **Mixed**"

Record into `content_form` + `rubric_form_mismatch`.

**Q1 → `content_form` enum mapping** (**must store the enum value, not the letter**):

| User answer | Value written to `content_form` |
|---|---|
| a | `"opinion-video"` |
| b | `"long-essay"` |
| c | `"short-text"` |
| d | `"podcast"` |
| e | `"tutorial-builder"` |
| f | `"other"` |
| g | `"mixed"` |

`rubric_form_mismatch` derivation:
- a → `false`
- b/c/d/e/f/g → `true`; cheat-status keeps reminding "your form may need a bump to adjust weights"
- **There is no longer a "severe mismatch" tier** — every form can run the workflow; some rubrics just need a more aggressive bump

**Q1.5: Typical duration** (only asked when Q1=a/d/f)

> "What is your typical video duration?
> a) 30 seconds-1 minute  b) 1-3 minutes  c) 3-5 minutes (recommended starting point)
> d) 5-10 minutes   e) Over 10 minutes"

Record into `typical_duration_seconds` (30 / 90 / 240 / 450 / 900).

**Q1.6: Publishing cadence**

> "How often do you plan to publish?
> a) Daily   b) Every other day   c) Weekly   d) Flexible / irregular (turn off buffer monitoring)"

Record into `target_publish_cadence_days` (1 / 2 / 7 / null).

**Q2: Have you published videos on this channel?**

> "a) Never — I'll brainstorm 5 candidates from your interests + trends and write 5 first drafts
>  b) Yes — whether 1 or 100, I'll pull your history so later brainstorms fit what you've already made"

If a → write `calibration_samples: 0` into state, **skip Phase 3.5**, go straight to Phase 4.
If b → go to **Q2.1**.

**Q2.1: Platform + fetch plan** (only Q2=b)

> "Which platform is your content mainly on?
> a) Douyin — install the douyin-session adapter (Playwright + QR login to Douyin Creator Center)
> b) Xiaohongshu — install the xhs-explore adapter (Playwright + QR login to Xiaohongshu Creator Center)
> c) YouTube — install the youtube-data-api adapter (requires an API key)
> d) Bilibili — bilibili-stat adapter
> e) LinkedIn — install the linkedin-session adapter (Playwright + log in to LinkedIn, analyze individual posts)
> f) WeChat Channels — install the wechat-channels adapter (Playwright + QR login to the Channels assistant; only pulls your own account's backend data)
> g) Other / multiple platforms — use manual paste mode"

If a/b/c/d/e/f → ask Q2.2; if g → skip to Q2.3 manual.

**Q2.2: Adapter install timing** (only Q2.1=a/b/c/d/e/f)

> "Install the adapter now for automatic fetching, or tell me manually first?
> - Install now — I'll guide you through Playwright + QR login → fetch your last N posts
> - Install later — start in manual mode, state marked 'pending_adapter_setup',
>            cheat-status keeps reminding you to install"

If "install now" → run the adapter install guide (see each adapter's README) → verify fetching works → Q2.3.
If "later" → skip to Q2.3 manual.

**Q2.3: Fetch range / history size**

If the adapter is installed and verified:
> "How many recent posts can I fetch as a basis?
> (10-25 recommended; more samples means a more accurate baseline. Up to your account's actual count)"
→ user gives N; Phase 3.5 fetches N posts

If manual mode:
> "Roughly how many posts have you published? A range is fine (e.g. '5-10' / '20+'),
>  this is only used to estimate calibration_samples; it does not need to be exact."
→ user gives an estimate; Phase 3.5 skips fetching and writes the estimate into calibration_samples

**Q3: Data collection method**

> "How do you get data for the T+3 day retro?
>
> a) Manual paste — fallback. **You must paste the top 20+ comments (with like counts)**, not just play counts.
>    Comments are the real signal — a meme explosion like 'she's different' can only be seen in the comments;
>    play count will never tell you what content actually hit the audience.
> b) **[Recommended default]** adapter auto-fetch — comments + data all included.
>    If you haven't installed an adapter yet, that's fine; state is marked 'pending_adapter_setup',
>    install it before the first publish (cheat-status keeps reminding you).
>    Install instructions: adapters/perf-data/<platform>/README.md."

**Q3 → `data_collection` enum mapping**:

| User answer | Value written to `data_collection` |
|---|---|
| a | `"manual"` |
| b (default) | `"adapter"` |

Default recommendation is b — unless the user explicitly says "a, I want manual".

**Q4: Candidate topics**

> "Do you have a candidate-topic list right now? (e.g. maintained in external markdown / Notion)
> a) No (default) — I'll brainstorm with you in a moment, or use /cheat-trends day to day
> b) Yes, a markdown list
> c) Yes, Notion / something else"

**Q4 → `pool_status` enum mapping**:

| User answer | Value written to `pool_status` |
|---|---|
| a (default) | `"none"` |
| b | `"markdown"` |
| c | `"notion"` |

**Q5: Install a few hooks (installed by default; no decision needed from you)**

> "Q5: I'll install a few hooks along the way; reply 'yes' or 'enter' to install:
>
> 1. **Prediction lock** — after we finish a prediction together, the file is locked. Neither you nor I can change the prediction section.
>    A retro can only append to the lower half of the same file; it never contaminates the judgment in the upper half.
>    (Without this lock, seeing the data afterward and wanting to 'fix the old prediction' is almost inevitable — for you or for me)
>
> 2. **SessionStart auto-report** — every new session shows buffer / pending retros / top candidates at the top
>
> 3. **Silent usage log** — asynchronously records usage frequency, non-blocking, for future diagnosis
>
> All three install together. **You can also skip them** (reply 'no'), but you lose the prediction lock and the calibration value drops.
>
> Reply yes / no."

**Q5 → `hooks_installed` mapping**:

| User answer | Value written to `hooks_installed` |
|---|---|
| yes / enter / default | `true` (bool, **not the string `"yes"`**) |
| no | `false` |

Default is yes — unless the user explicitly says no.

### Phase 2.5: Benchmark account (**asked of every user**; strongly recommended for cold-start)

> The tool's most important early signal source is a **benchmark account** — right after init you have no data, and an equal-weight v0 rubric is basically astrology.
> But if you can find an account you want to become, and import 5-10 of its high / medium / low samples, the tool has anchors.

Ask:

```
🎯 Benchmark account

Can you find a benchmark account? At least 3 videos from that account.

  - You have **never published** (Q2=a) → **strongly recommended** — the rubric has no anchors and relies entirely on the benchmark.
    Without one you use the generic v0 equal-weight rubric, and the first 5 pieces are less accurate for longer
  - You **have publishing history** (Q2=b) → **optional** — you can also calibrate purely on your own history;
    but importing at least 1 benchmark as a sanity check is recommended (to see whether your account really drifts away from the benchmark's direction)

a) Find one now → go straight into /cheat-learn-from (5-15 minutes, depending on how ready your materials are)
b) Find one later → state marked `benchmark_status: pending`; cheat-status keeps reminding you
c) No benchmark → state marked `benchmark_status: none`; start with the generic v0

Reply a / b / c.
```

Behavior:
- a → after Phase 3 finishes creating the scaffolding, **automatically dispatch to /cheat-learn-from** (do not make the user run it manually — they are already in the init flow). When done, return to init Phase 4
- b → state marked `benchmark_status: pending` + `benchmark_name: null`
- c → state marked `benchmark_status: none`

Record into `benchmark_status` / `benchmark_name` (for a, cheat-learn-from writes it).

### Phase 3: Create the scaffolding (explain each item)

Create in order and **explain what each item is for**:

0. **`.gitignore` (safety — must be the first thing created)**
   ```
   "First create .gitignore, keeping account credentials out of version control — this is step one.
    .auth/ / .auth-xhs/ / .auth-linkedin/ / .auth-wechat-channels/ store platform login state (equivalent to account passwords),
    .cheat-secrets.json stores API keys / cookies — once committed or cloud-synced, that equals leaking the account.
    Note: predictions/ videos/ scripts/ are NOT ignored — principles #1/#3 rely on
    git history as the immutable archive of predictions, so they must be committed."
   ```
   - Copy `cheat-on-content/templates/gitignore.template` → `<user-repo>/.gitignore`
   - If `<user-repo>/.gitignore` **already exists** → do not overwrite; check line by line and **append missing lines**, at minimum ensuring
     `.auth/`, `.auth-xhs/`, `.auth-linkedin/`, `.auth-wechat-channels/`, `.cheat-secrets.json` all exist
   - Create it even if the user's project **is not a git repo yet** — it takes effect the moment the user runs `git init`
   - After creating it, remind the user: if the project has already been `git init`-ed and `.auth/` may have been added by mistake, run
     `git rm -r --cached .auth .auth-xhs .auth-linkedin .auth-wechat-channels .cheat-secrets.json` to remove the staged credentials

1. **`.cheat-state.json`**
   ```
   "Creating .cheat-state.json — where every sub-skill shares context.
    All the answers collected during this init are written here."
   ```
   Write (**every `<...>` placeholder must be looked up in the Q mapping tables above and replaced with a concrete enum value; never store the letter directly**):
   ```json
   {
     "schema_version": "1.4",
     "skill_version": "1.0.0",
     "rubric_version": "v0",
     "content_form": "<look up the Q1 mapping table and write the enum string, e.g. \"opinion-video\">",
     "typical_duration_seconds": <derived from Q1.5: 30/90/240/450/900>,
     "target_publish_cadence_days": <derived from Q1.6: 1/2/7/null>,
     "rubric_form_mismatch": <Q1=a→false; otherwise→true>,
     "benchmark_status": "<derived from Phase 2.5: a→\"imported\"/b→\"pending\"/c→\"none\">",
     "benchmark_name": <string name if imported, otherwise null>,
     "benchmark_sample_count": <number if imported, otherwise 0>,
     "baseline_plays": null,
     "calibration_samples": <Q2=a→0; Q2=b→backfilled from Phase 3.5 import or the Q2.3 estimate>,
     "data_collection": "<look up the Q3 mapping table and write \"manual\" or \"adapter\">",
     "pool_status": "<look up the Q4 mapping table and write \"none\"/\"markdown\"/\"notion\">",
     "data_layer": "markdown",
     "hooks_installed": <look up the Q5 mapping table and write bool true/false>,
     "enabled_trend_sources": ["manual-paste"],
     "enabled_perf_adapters": <Q2.1=a→[\"douyin-session\"]; b→[\"xhs-explore\"]; c→[\"youtube-data-api\"]; d→[\"bilibili-stat\"]; e→[\"linkedin-session\"]; f→[\"wechat-channels\"]; other→[]>,
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
     "initialized_at": "<local ISO 8601 with timezone, e.g. \"2026-05-05T20:11:13+08:00\", **do not use a UTC Z suffix**>"
   }
   ```

2. **`rubric_notes.md`**
   ```
   "Creating rubric_notes.md — the source of truth for your scoring dimensions.
    It uses the v0 placeholder rubric — 7 equal-weight dimensions (every dimension matters equally).
    
    Why it's called v0: v0 is the placeholder before calibration. Your account's real weights must be
    reverse-engineered from your data, not preset. After 5 pieces with data, the tool automatically proposes
    upgrading to 'calibrated v1' (your first truly calibrated rubric).

    ⚠️ rubric_notes.md is the whitelist file for the blind sub-agent (channel B) —
    it may only contain generic language (formula / dimension definitions / bucket boundaries), never real video names / actual performance.
    The memo written at every bump (with evidence data + derived evidence) goes into rubric-memo.md (created next)."
   ```
   - Copy `cheat-on-content/starter-rubrics/<form>-zero.md` (cold-start) or `<form>.md` (still available as a reference when you have data)

2.5. **`rubric-memo.md`** (**new** — pairs with the cheat-score-blind isolation protocol)
   ```
   "Creating rubric-memo.md — the cumulative archive of bump memos.
    This is where cheat-bump Phase 5 writes the full memo (including real video names + actual performance + derived evidence).

    Why a separate file: the blind sub-agent's whitelist is rubric_notes.md;
    historically, writing bump memos into rubric_notes.md let the blind sub-agent
    read actual-performance data it should never have seen through the whitelist — this file is the isolation fix; the sub-agent is strictly forbidden from reading it.
    
    It is empty now; the first memo is appended after the first cheat-bump upgrade."
   ```
   - Copy `cheat-on-content/templates/rubric-memo.template.md` → `<user-repo>/rubric-memo.md`

3. **`script_patterns.md`**
   ```
   "Creating script_patterns.md — your writing-pattern library (decoupled from the rubric).
    rubric_notes.md teaches Claude how to score;
    script_patterns.md teaches Claude how to write."
   ```
   - Copy `cheat-on-content/templates/script_patterns.template.md`

4. **Four directories**: `scripts/` + `predictions/` + `videos/` + `samples/` (each gets a `.gitkeep`)
   ```
   "Creating four directories:
    
    scripts/      — pre-shoot drafts (written by cheat-seed or by you)
    predictions/  — immutable prediction logs (hook-protected)
    videos/       — post-shoot working directories (cheat-shoot creates subdirectories)
    samples/      — benchmark-account videos / transcripts (cheat-learn-from creates subdirectories)
    
    The first three use the same <date>_<id>_<short> naming group so they link to each other.
    samples/ is grouped by benchmark account name: samples/<account-name>/<video-id>/."
   ```

4.5. **`benchmark.md`** (only when Phase 2.5 chose a/b)
   ```
   "Copying the benchmark.md placeholder template (actual content is filled in by cheat-learn-from) —
    this is the central reference for your benchmark account.
    The tool's early rubric / patterns / topic-direction sense is largely inferred from here;
    later, after N≥10, its influence fades, but it is kept as a sanity check."
   ```
   - Copy `cheat-on-content/templates/benchmark.template.md` → `<user-repo>/benchmark.md`
   - **If Phase 2.5 chose c, do not create it** → benchmark.md does not exist, state marked `benchmark_status: none`

4.7. **`audience.md`**
   ```
   "Creating audience.md — your account's audience persona ('who is watching').
    
    It is an empty skeleton now. It is parallel to rubric_notes.md — the rubric teaches Claude how to score,
    the audience tells Claude who your viewers are. After enough retros, run /cheat-persona,
    and it clusters the comment data into a real persona; cheat-seed then has a mirror when choosing topics and writing drafts.
    
    Note: audience.md is derived from comments → contains actual-performance signals → the blind scoring sub-agent is strictly forbidden from reading it."
   ```
   - Copy `cheat-on-content/templates/audience.template.md` → `<user-repo>/audience.md`
   - If Phase 2.5 chose a/b (has a benchmark) → in the Phase 5 checklist mention "you can run `/cheat-persona — seed-from-benchmark` to seed an unverified persona first"

5. **`WORKFLOW.md`** + **`STATUS.md`**
   - Copy the corresponding files from templates/

6. **If Q5=yes → install hooks**
   - Read `.claude/settings.json` (create an empty `{}` if it does not exist)
   - Merge `hooks/prediction-immutability.json` into `hooks.PreToolUse`
   - Merge `hooks/session-start.json` into `hooks.SessionStart`
   - Merge `hooks/meta-logging.json` into hooks (if enabled at the same time)
   - Copy `prediction-immutability.sh` + `session-start.sh` + `log-event.sh` into `.cheat-hooks/`, chmod +x
   - Use `${CLAUDE_PROJECT_DIR}/.cheat-hooks/` for command paths in settings.json

7. **(Pool option c — Notion)** Only record `pool_status: notion` in the state file; cheat-trends handles it later when called

### Phase 3.5: Import flow (only Q2=b and the user agrees to fetch)

If Q2.2=install now → run the adapter install + login (see [adapters/perf-data/<platform>/README.md](../../adapters/perf-data/)).

After a successful fetch, for each published video:

1. **Create a video folder**: `videos/<date>_<id>_<short>/`
   - `<date>` = the video's actual publish date
   - `<id>` = 12-char hash: sha256 of (title + platform ID)
   - `<short>` = first 3-8 characters of the title
2. **Write report.md**: fill in the data fetched by the adapter (plays / likes / comments / shares / top comments)
3. **Ask the user for the original script**: "Did you keep the original script for the video "{title}"?"
   - Yes → the user provides it → save as `videos/<id>/script.md`
   - No → mark `script_lost` (still create the video folder; just script.md is missing)
4. **Write a reconstructed prediction**: `predictions/<date>_<id>_<short>.md`
   - Mark the header `**Reconstructed retrospective — NOT a blind prediction**`
   - Score the 7 dimensions **backwards** from the script + the actual performance in the retrospective section — make it explicit that this is not for calibration
   - Do not count it in calibration_samples (this is imported history, not accumulated calibration)

After the import:
- Derive `baseline_plays` = the median plays of the fetched videos → write into the state file
- Derive the confidence level → later cheat-predict uses it directly when writing predictions
- Output a summary: "Imported N historical posts. Most recent one X plays, median Y, created N video folders + reconstructed predictions"

### Phase 4: Test whether the hook works (only when Q5=yes)

Run a fake Edit-interception test:
1. Create a temp file `predictions/_test_hook.md` containing `## Prediction\n[test]\n## Retrospective\n`
2. Try to Edit the `## Prediction` section of this file
3. The hook should exit 1 and block → report "✅ immutability hook is working"
4. Delete the test file
5. SessionStart hook check: call `bash .cheat-hooks/session-start.sh` once → it should output a report (even an empty one is fine)

If the hook does not work → **do not pretend it succeeded**; tell the user clearly: "Hook installation failed; the .claude/settings.json config may not have taken effect. Check it manually or restart Claude Code."

### Phase 4.5: If Phase 2.5 chose a → dispatch to /cheat-learn-from

If the user chose a in Phase 2.5 (import a benchmark account now) → **automatically trigger /cheat-learn-from**:

```
✅ Scaffolding + hooks installed.

Going straight into /cheat-learn-from to import your benchmark account —
you chose "find one now" at init, so I won't make you open another session to run it.

[invoke /cheat-learn-from]
```

After cheat-learn-from finishes, return to init Phase 5.

If Phase 2.5 chose b/c → skip Phase 4.5 and go straight to Phase 5.

### Phase 5: Give the "what to say next" checklist

```
✅ Initialization complete (rubric: v0, calibration_samples: <N>, confidence: <emoji level>)

Next time you can say these directly:

📝 Finished a draft → "score this scripts/<...>.md"
🎯 Before publishing → "start prediction scripts/<...>.md"
🎬 Shot it       → "shot scripts/<...>.md" → create video folder + buffer +1
🚀 After publishing → "shipped https://..."
📊 T+3 days      → "retro videos/<...>/"
📈 Anytime       → "status" (see the full dashboard)

<If Q4=no candidate topics:>
🌱 Run /cheat-seed now to find topics?
   - Never published: pure brainstorm (interests × trends)
   - Published before (already imported): the brainstorm uses what you've made before to recommend
   Reply "yes, seed" to run it now, or "no" to think for yourself.

💡 Your confidence is <current level> — it rises automatically as you run more retros.
   Don't skip predictions just because confidence is low — the discipline of predicting is itself the core of the tool;
   the "value" of early predictions is data collection, not decision-making. After the 5th retro the rubric calibrates for the first time and
   confidence crosses into 🟡 Low-ish; after the 10th it becomes 🟢 Medium.
```

## Key Rules

1. **Never pretend it succeeded**: if any step fails → tell the user clearly which step failed. Never write "✅ Initialization complete" if it did not actually complete
2. **No batched questions**: ask the 5 questions one at a time
3. **No silent mkdir**: explain what every file you create is for
4. **Do not push SQLite**: give every user markdown; one line "it will suggest upgrading around 30 pieces" is enough
5. **Unified state fields**: remove enum fields such as mode / prediction_complexity / bucket_scheme — use the single integer calibration_samples + derived confidence
6. **Import failure must not block**: Q2=b but adapter install fails / fetch fails → degrade gracefully to "write an estimated calibration_samples, do not import historical video folders"

## Refusals

- "Skip Q1-Q5 and just create all the files for me" → refuse. The answers directly determine default config (content_form, cadence, hooks)
- "I already initialized elsewhere; sync that project's config over here" → be careful. Tell the user to `cp` the existing `.cheat-state.json` and `rubric_notes.md` manually; never sync across projects automatically
- "Don't install the hook but keep the immutability promise" → allowed; state marked `hooks_installed: false`; cheat-status keeps reminding "your immutability is a gentleman's agreement"

## Integration

- Once writing is done, the main SKILL.md routing unlocks every other sub-skill
- `cheat-status` reads the `calibration_samples` field in `.cheat-state.json` to decide which confidence level to display
- If Q2=b ran an import → historical reconstructed predictions go into `predictions/` and `videos/<...>/`, but are **not** counted in calibration_samples (they are not real calibration samples)
- `/cheat-seed` reads every historical reconstructed prediction in `predictions/` → during brainstorming it knows "what the user has made before"

## State field write checklist

| Field | Write timing | Source |
|---|---|---|
| `schema_version` | Phase 3 | hardcoded "1.4" |
| `skill_version` | Phase 3 | hardcoded "1.0.0" |
| `rubric_version` | Phase 3 | "v0" |
| `content_form` | Phase 3 | Q1 → look up the mapping table for the enum value (**not the letter**) |
| `typical_duration_seconds` | Phase 3 | derived from Q1.5 |
| `target_publish_cadence_days` | Phase 3 | derived from Q1.6 |
| `rubric_form_mismatch` | Phase 3 | Q1≠a → true |
| `benchmark_status` | Phase 3 / 2.5 | derived from the Q2.5 answer |
| `benchmark_name` | Phase 3 / 2.5 | supplied by the user at Q2.5 |
| `benchmark_sample_count` | Phase 3 / 2.5 | backfilled after the cheat-learn-from import |
| `baseline_plays` | Phase 3.5 (if the import succeeded) | median of the imported data; otherwise null |
| `calibration_samples` | Phase 3 / Phase 3.5 | Q2=a→0; Q2=b→the Q2.3 estimate or the import count |
| `data_collection` | Phase 3 | Q3 → look up the mapping table for the enum value |
| `pool_status` | Phase 3 | Q4 → look up the mapping table for the enum value |
| `enabled_perf_adapters` | Phase 3 | derived from Q2.1 (if Q2=a then `[]`) |
| `hooks_installed` | Phase 3-4 | Q5 → bool (not a string) |
| `last_bump_at` / `last_published_at` / `last_published_file` / `last_retro_at` / `last_trends_run_at` | Phase 3 | all `null` |
| `last_bump_self_audited` | Phase 3 | `false` |
| `last_trends_added_count` | Phase 3 | `0` |
| `last_prediction_self_scored` | Phase 3 | `false` |
| `last_self_scored_at` | Phase 3 | `null` |
| `initialized_at` | Phase 3 | now() local ISO 8601, with a `+08:00` timezone, **no UTC `Z`** |
