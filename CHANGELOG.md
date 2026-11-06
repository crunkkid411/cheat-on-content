# Changelog

All notable changes to cheat-on-content will be documented here.

Format reference: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); version numbers follow [SemVer](https://semver.org/).

---

## [Unreleased]

### Added — xhs-explore adapter: public-page fallback, body/image archiving, account summary

- Merged the public-page parsing capability of [xhs-analytics](https://github.com/SingularGuyLeBorn/xhs-analytics):
  - `crawler.fetch_public_note()` parses `window.__INITIAL_STATE__` without login, filling in the body, image URLs, and tags.
  - `crawler.fetch_public_comments()` falls back to the public page's top comments when the frontend API cannot get comments (usually ~10).
  - `crawler.download_image()` downloads note images asynchronously.
- `review.py` gained new subcommands:
  - `archive <notes.json> [output_root] [limit]`: bulk-archive the body and images of published notes.
  - `summarize [out_dir]`: generate an account-level summary based on the creator center's latest 50 + public-page tags.
- `review.py note` supports the environment variable `XHS_DOWNLOAD_IMAGES=1` to download images to `videos/<...>/images/`.
- `renderer.py` adds "body + tags" and "images" blocks to `report.md`.
- `requirements.txt` adds `requests>=2.28`.
- `Session.open()` automatically falls back to system Chrome (`channel="chrome"`) when Playwright Chromium is not installed.

### Added — audience persona (cheat-persona skill + audience.md)

**Motivation**: when choosing topics / writing drafts, the user lacks a clear mirror of "who is watching". Added audience-persona functionality — clustering the account's real audience out of retrospective comment data.

**Design**: the persona is the second derivative, **parallel to** the rubric:

```
Retro data (comments + completion + follows)
   ├──→ rubric evolution (cheat-bump)          —— "how to score"
   └──→ audience persona (cheat-persona)       —— "who is watching"
```

- **New skill `/cheat-persona`** (the 15th sub-skill) — scans `predictions/*.md` retrospective comment sections, clusters along four dimensions ("self-identification / emotional purpose / disagreement points / language"), and writes `audience.md`
- **New file `audience.md`** + `templates/audience.template.md` — the audience-persona reference, peer to `benchmark.md`. Every "verified trait" must carry comment evidence + counts; verified / hypothesized / counter-persona three-way split; a mandatory "counter-persona" section prevents the persona from becoming a flattering fiction
- **⚠️ Contamination isolation**: `audience.md` derives from comments = contains actual-performance signals. `cheat-score-blind`'s hard refusal list gains `audience.md`, refusal_code `blocked_audience`. The persona affects cheat-seed's **what to write** (creative) and not cheat-predict's **how to score** (the blind sub-agent never reads audience.md)
- **cheat-seed wiring**: Phase 0 reads audience.md as the "would this persona care?" mirror (only Confidence 🟡 or above counts as a check lens; it does not enter rough scoring)
- **cheat-init wiring**: Phase 3 scaffolds an empty `audience.md`; users who imported a benchmark are told about `/cheat-persona — seed-from-benchmark`
- **Confidence levels**: 🔴 no data / 🟠 benchmark-seeded, unverified / 🟡 1-2 retros / 🟢 3-5 / 🔵 6+
- **Zero schema changes**: all persona metadata lives in the audience.md header (version / last_rebuilt / data basis / Confidence); `.cheat-state.json` is untouched

**Phase 1 scope** (this release): the above. **Phase 2 roadmap** (not done): cheat-recommend persona-fit ranking / cheat-status freshness nag / cheat-retro auto-flag.

**Known limitations** (written into cheat-persona/SKILL.md): comments ≠ the whole audience (skews toward the active minority who comment); comments can be polluted by trolls; the persona lags behind real audience change; it does not make the "wanted audience vs actual audience" strategy decision for the user.

### Fixed — cheat-seed writing drafts in subtitle format (one sentence per line)

**Problem**: users reported that the draft body cheat-seed wrote was in "one sentence per line" subtitle format rather than paragraph form. The root cause was not missing documentation — the "do not use subtitle format" instruction existed in 4 files, but **all of it was prose instruction**. At the moment of draft generation, the model's training prior that "video script = teleprompter short lines" overpowered one sentence buried in Phase 4 prose.

**Fix** (two hands):
- **A — suppress the prior during generation**: the Phase 4 draft template block adds a **concrete side-by-side ❌subtitle format / ✅paragraph version contrast**, right next to the body placeholder — at generation time the eyes are on the example and the prior is pinned by the anchor
- **B — deterministic backstop after persistence**: new Phase 4.5a line-format self-check — compute the body's `avg_chars_per_line`; `< 15 chars and line count ≥ 8` → judged subtitle format → automatically reflow into 3-6 paragraphs. Do not rely on model self-discipline; rely on `awk`
- Phase 4.5 order is fixed: **4.5a fixes layout first, then 4.5b humanizer** (humanizer works on prose; feeding it fragments makes a mess)
- Batch mode's N drafts also go through Phase 4 formatting + Phase 4.5 self-check

### Added — cheat-seed Phase 4.5: humanizer self-check pass (de-AI-ification)

**Problem**: Claude's own cheat-seed first drafts naturally carry AI writing tells — em-dash overuse, rule of three, inflated vocabulary, vague attributions, shallow -ing analysis. The starting point the user receives is heavily "machine-flavored".

**Change**: after the draft is written and saved, before showing it to the user, a new Phase 4.5 — run it through the [`humanizer`](https://github.com/blader/humanizer) skill (MIT, external project, 18k stars) to remove AI tells.
- Only humanize the **body**; do not touch the header's "must rewrite" warning (that is an intentional scaffolding marker)
- **Voice calibration**: when historical scripts / `script_patterns.md` exist, pass them as reference samples — lean toward "the user's voice", not "generic human voice"
- Report which tells were fixed, shown in the Phase 5 output
- `HUMANIZE_DRAFT = on` by default; if humanizer is not installed, skip gracefully + explain how to enable it
- **Does not contaminate calibration**: a cheat-seed draft is not what gets predicted/published — cheat-predict scores the user's final draft; humanizing the first draft just gives a cleaner starting point
- **Does not rewrite for the user**: humanizer removing AI flavor ≠ becoming the user's voice; the "must rewrite" warning still holds

humanizer is **not bundled** into cheat-on-content — users `git clone` it themselves into `~/.claude/skills/humanizer/`.

### Fixed — douyin-session runtime path privacy leak (@level5Ninja [#16](https://github.com/XBuilderLAB/cheat-on-content/pull/16))

**Problem**: the douyin-session adapter wrote `.auth/` (**containing the Douyin login cookie**), debug screenshots, and reports into the **skill source directory** instead of the user's content project — with a symlink install, the user's session credentials land inside the cheat-on-content repo with a risk of being committed. The meta-logging hook also stored the first 120 characters of every user prompt in `usage.jsonl`, over-collecting.

**Fix**:
- New `adapters/perf-data/douyin-session/paths.py` — runtime path helpers (`runtime_project_root` / `auth_dir` / `debug_dir` / `videos_dir`), using the `CHEAT_PROJECT_ROOT` env var + cwd fallback
- `.auth/` → user content project root; debug artifacts → `.cheat-cache/douyin-session-debug/`; report/script → the user project's `videos/` (no longer scattered in the skill source tree)
- `run.sh` exports `CHEAT_PROJECT_ROOT`
- The meta-logging hook no longer stores prompt summaries — it records only `prompt_present` (bool) + `prompt_chars` (length)
- Docs (adapter README + state-management.md) synced

### Fixed — cheat-shoot DIFF_METRIC false v2 triggers in colloquial scenarios (**BREAKING for v2-trigger-logic**)

**Problem**: cheat-shoot Phase 3b used a line-level unified diff to compute `diff_pct = (added + removed) * 100 / orig_lines`. But in **creators' real workflows** — the draft is long markdown sentences (~50 chars per line), the shooting script is colloquial short fragments from whisper transcription (~5-10 chars per line) — the same content inflates diff_pct to 100-200%, triggering a v2 re-judgment that should not happen.

**Reproduced in practice** (using the clone PR pre-fix):
- Draft markdown 63 lines / ~380 chars
- Shooting transcript 100 lines / the same ~380 chars
- Content almost entirely preserved (the reviewer's original sentences verbatim + the 5-years-ago reaction concept + every quotable line in the elevation passage)
- Only addition: 1 brand-anchoring sentence "fully embrace AI"
- **line-level diff_pct = 198%** ⚠️ v2 falsely triggered
- True semantic content diff ≈ 15-25%

**Fix**: split the metric.
- **DIFF_METRIC=char_levenshtein_normalized** (new default) — [tools/diff_pct.py](tools/diff_pct.py) first normalizes (strip markdown headers / dividers / list markers / decorative punctuation / collapse all whitespace), then computes char-level Levenshtein / max(len_a, len_b)
- Backend priority: `rapidfuzz` (C-backed, ~ms; requires `pip install rapidfuzz`) → `difflib.SequenceMatcher` (stdlib, always available, ~10ms)
- **V2_TRIGGER_THRESHOLD = 0.30** stays unchanged (the threshold is empirically reasonable)
- Legacy line-level is kept as the ultimate fallback (only degraded to when both python3 + tools/diff_pct.py are unreachable)

**Testing**: 3 fixtures × 2 backends = 6 cases, all passing:

| Case | Content | Expected range | difflib | rapidfuzz |
|---|---|---|---|---|
| 1 | markdown long sentences vs transcribed short fragments (same content) | < 30 | 7 | 12 |
| 2 | Completely different topics | ≥ 60 | 88 | 97 |
| 3 | Added 20% outro/CTA | 10-30 | 14 | 25 |

Run `bash tools/diff_pct_test.sh` to reproduce.

**Known limitations**:
- Historical v2 prediction files keep their line-level numbers as an audit trail — past predictions are not re-run
- normalizing is heuristic (Chinese punctuation) — other languages / atypical markdown may need regex adjustments

### Fixed — `rubric_notes.md` actual-performance leak (**BREAKING for blind channel integrity**)

**Problem**: the cheat-score-blind sub-agent introduced in PR #11 promised to read only `scripts/<id>.md` + `rubric_notes.md`. But cheat-bump Phase 5 wrote upgrade memos (including real video names + actual performance + derived evidence) into `rubric_notes.md` — the sub-agent read actual performance through the whitelist that it should never have seen, turning blind scoring into "post-hoc rationalization after seeing the actual performance". Reproduced in practice: of 5 published videos, 2 had the sub-agent automatically flag `any_contamination_signal: true` (refusal=`non_blind_warning`, all dimensions' confidence lowered to medium).

**Fix** (split the file):
- **New `rubric-memo.md`** — the cumulative archive of upgrade memos. cheat-bump Phase 5 writes **here**, **not** rubric_notes.md. Append mode accumulates multiple bumps
- **`rubric_notes.md` strictly narrowed** — only the formula + generic-language dimension definitions + bucket boundaries + top metadata pointing to rubric-memo.md. **Never** real video names / actual performance / derived evidence with naming anchors
- **`cheat-score-blind` hard-forbidden from reading `rubric-memo.md`** — refusal_code `blocked_rubric_memo`; plus a **backstop self-check** on whitelist files (grep hits an actual-performance pattern → mark `non_blind_warning`)
- **`cheat-bump` Phase 5 leak guard** — after writing rubric_notes.md, grep self-check; a forbidden pattern hit → abort + roll back
- **`shared-references/observation-lifecycle.md` gains a constraint** — no skill writing rubric_notes.md may contain actual-performance patterns (preventing recurrence)

**Existing users must run**: any v0.x project whose `rubric_notes.md` already contains bump memos **must** run `/cheat-migrate` after git pull to split rubric_notes.md into two files. If not → the blind sub-agent still leaks. See [migrations/1.3-to-1.4.md](migrations/1.3-to-1.4.md).

### Changed — schema 1.3 → 1.4 (MINOR but BREAKING for the blind channel)

- State fields **unchanged** — the `schema_version` bump only marks "existing users must run the file-layer split migration"
- [migrations/1.3-to-1.4.md](migrations/1.3-to-1.4.md) has a 7-step standard flow (backup → scan → extract → write rubric-memo.md → clean rubric_notes.md → self-check → bump schema)
- Synced in three places: cheat-init, the SessionStart hook's LATEST_SCHEMA, and registry.md

### Added — Blind scoring sub-agent (channel B isolation)

**Problem**: cheat-on-content's 7/9-dimension scoring originally ran inline in the main conversation — but the main Claude has already seen the user conversation, actual-performance data, and retrospective history, so scoring was contaminated. It is especially severe during the `/cheat-bump` Phase 2 calibration-pool re-score — rank consistency may be overfitting rather than a real signal.

**Change**: introduced [skills/cheat-score-blind](skills/cheat-score-blind/SKILL.md) as the **channel B** isolated scoring sub-agent. Three-channel model:
- **A** = main conversation: decisions / writing retros / interacting with the user
- **B** = blind sub-agent (new): receives only `script_path` + `rubric_notes_path`, hard-refuses to read the state file / predictions/ / videos/, outputs strict JSON 9-dimension scores + per-dim confidence
- **C** = cross-model audit (qwen-max via `mcp__llm-chat__chat`, existing): final bump sanity check

Concrete implementation:
- **`cheat-score` Step 3** changed to delegate to cheat-score-blind via the Task tool (no more inline scoring; cheat-score has no `--skip-blind` because it is lightweight exploration)
- **`cheat-predict` Phase 2** delegates by default; a new **Phase 2.5** does disagreement detection — blind vs the main Claude's self-estimate |delta| ≥ 2 prompts the user to arbitrate (choose a/b/c); the header gains `BlindScored By` + `BlindScore Disagreement` fields (**all dimensions must be recorded**, including delta=0, as retrospective analysis material)
- **`cheat-predict --skip-blind`** flag is the escape hatch: sets `state.last_prediction_self_scored=true` + a `last_self_scored_at` timestamp; cheat-status / the SessionStart hook keep nagging until the next normal call clears them
- **`cheat-bump` Phase 2** **mandatorily** uses the sub-agent and **accepts no fallback whatsoever** — Task tool unavailable → abort the bump; "self-audit" is not accepted; each prediction's `Re-scored under vN` line is additionally marked `blind: true`
- **SessionStart hook** detects `last_prediction_self_scored && days_since >= 7` and prints a red warning
- **install.sh / uninstall.sh** add `cheat-score-blind` to the SKILLS array (14 sub-skills)

### Changed — schema 1.2 → 1.3 (MINOR)

- Adds `last_prediction_self_scored: bool` (default false) + `last_self_scored_at: ISO 8601 / null`
- [migrations/1.2-to-1.3.md](migrations/1.2-to-1.3.md) contains the 4-section standard format (WHAT/WHY/HOW/Manual fallback)
- Old states upgrade via `/cheat-migrate`; not running it is also compatible (skills fall back with `state.get(field, default)`)

### Known limitations (written into cheat-score-blind/SKILL.md)

1. **A sub-agent ≠ truly independent** — the same Claude model, sharing RLHF priors; a fresh context does not equal another scoring system
2. **Does not solve rubric design bias** — a rubric written by the user naturally makes their own content look good. This layer of bias is handled by channel C cross-model audit and periodic bump validation
3. **Does not solve review-stage override** — after the main Claude receives the blind score, it may be swayed by actual performance at Phase 2.5 and override it. Disagreement detection + user arbitration mitigates but does not eliminate this

### Changed — README / cheat-init voice redesign (recursive fatalism)

- **README tagline changed to the recursive-fatalism version**: "You are reading this sentence — this skill already predicted it. ... You paused to wonder 'is this true?' — that is in its prediction too." Replaces the original "publishing on feeling is guessing; this lets you calculate" framing
- **New 🌀 origin section**: the essence of the creator's own video script (the awakening from first-order fatalism → second-order fatalism) as the README's mid-section narrative hook
- **Closing tagline gains a callback**: "You saw this line — that was predicted too" — bookending the reader inside the prediction loop
- **cheat-init Phase 1 first screen synced**: from "making content is essentially cheating" to "your next piece is already rewriting who you are 3 months from now. The patterns objectively exist; the difference is whether you see them. This lets you see."
- **GitHub repo description** synced to the recursive version

### Changed — multilingual README split

- `README.md` is now **English by default** — the first screen for international users
- `docs/README_CN.md` is Simplified Chinese (the original README content + the fatalism redesign)
- Both have a language switcher at the top (QuantDinger style)
- Logo paths + internal links adjusted to relative paths

### Added — Star History chart

Both READMEs end with a [star-history.com](https://star-history.com) chart, visualizing project popularity for the community.

### Changed — De-emphasizing Claude Code

The README install section changed from dual "### Claude Code" + "### Codex" headings to "default + supported agents list" — packaging the skill as a cross-agent workflow rather than Claude Code-exclusive. The daily-usage section also switched to the generic term "skill-compatible agent".

### Added — Terminal-style logo SVG

- `docs/logo.svg` (1.9KB native SVG, no image-asset dependency)
- Terminal window + traffic lights + `$ fatesnail` command line + 5-stage loop + `// cheat on content` comment
- Embedded centered in the README hero

### Added — cheat-seed mode restructure + dual trend-tool integration

**Problem**: the original Mode B gave "a/b/c three examples" for the user to recount experiences — but the same script treated **users with a direction but abstraction** ("want to do workplace") and **users with no idea at all** ("help me think") the same; the former actually has a real motive and does not need the AI to list options, while the latter needs external material, not a prompt.

**Change**:

- **Mode B changed to a single question, "why do you want to make this topic?"** — a window for the user's introspection, **calling no trend tool**. Three answer types: contains a concrete experience → switch to Mode A; empty motive → ask back at most 2 rounds; genuinely no idea → switch to Mode C
- **Mode C integrates external material**: route trend tools by `content_form` — AI-type forms call [aihot](adapters/trend-sources/aihot.md), culture/social forms call [trendradar-mcp](adapters/trend-sources/trendradar-mcp.md), mixed calls both; after the user picks one, **return to introspection** and ask "why does this one resonate most with you", then switch to Mode A deep dive
- **Mode A gray area** (the user gave a current-events topic): Phase 2A.5 asks "do you want to pull external data as reference" — **never calls proactively**, avoiding external information biasing the user's perspective
- **The three talk-about-experiences options moved to Mode C fallback**: presented only when the user refuses external material or finds none of it interesting

### Added — two first-class trend sources

- **[aihot](adapters/trend-sources/aihot.md)** (Claude skill): [aihot.virxact.com](https://aihot.virxact.com)'s daily Chinese AI-industry selection, 5 categories (models/products/industry/papers/tips). No auth, curl the public API, rate limit 600/min
- **[trendradar-mcp](adapters/trend-sources/trendradar-mcp.md)** (MCP server): [TrendRadar](https://github.com/sansan0/TrendRadar) (57k stars, GPL-3.0; calling it via MCP does not constitute linking). 25+ MCP tools — besides `get_latest_news`, there are `analyze_topic_trend` (breakout/decline judgment), `compare_periods` (week-over-week), `analyze_sentiment`

### Added — `shared-references/data-source-routing.md`

The trigger and routing protocol for trend tools — a single source recording: "when to call" (the trigger matrix for 5 entry points) + "which one to call" (the content_form → adapter routing table) + "what to do when not calling" (the failure-degradation chain) + token-cost awareness.

### Philosophy unchanged

> Trend tools are a "pre-material library", not a "main menu" — the AI provides material, the user decides the angle.

cheat-seed's core thesis "good content comes from the user's real experience; the AI does not brainstorm out of thin air" is fully retained. The new design only stops the "no idea at all" cold-cold-start path from deadlocking.

### Added — v2 prediction re-judgment system (post-shoot script change scenario)

- **append-only v2 prediction**: when cheat-shoot detects a line-level diff ≥ 30% between the shooting script and `scripts/<id>.md` (`V2_TRIGGER_THRESHOLD`) → automatically calls `/cheat-predict — mode: v2 — prediction-file: <path>` → appends a `## Prediction v2 (replaces v1)` section before the original prediction file's `## Retrospective` (legacy `## 复盘`). **The v1 section is never modified** (physically enforced by the hook); only v2 enters cheat-retro's deviation calculation
- **Immutability hook awk upgrade**: a single `## Prediction` (legacy `## 预测`) changed to recognizing multiple `## Prediction vN` sections (v1 / v2 / any vN locked together), while staying compatible with v0.1.0's legacy bare `## 预测` form. End-to-end 5-scenario validation passed (editing v1 / editing v2 / editing legacy all BLOCK; appending a new section, editing `## Retrospective` all ALLOW)
- **cheat-predict gains Phase 0.7 mode detection**: when the target prediction file already contains a `## Prediction...` section → automatically switch to v2 mode (Edit appends at the `## Retrospective` boundary; no Write overwrite)
- **cheat-retro upgraded**: recognizes multiple `## Prediction vN`, takes the last section as the calibration basis; prediction-section hash verification expands to "a merged hash of all v? sections"; if any one was modified, error and roll back
- **New prediction header field `Prediction Basis`**: `pre_shoot` (v1 default) / `post_shoot_pre_publish` (v2). score-curve and cheat-bump use it to separate the two data lines and avoid mixing samples
- **shoots[] item schema extended**: adds `scripts_path` / `script_consistency` / `script_diff_pct` / `v2_prediction_written` / `script_hash_at_shoot` (see [migrations/1.1-to-1.2.md](migrations/1.1-to-1.2.md))

### Changed — schema 1.1 → 1.2 (MINOR)

- Updated [migrations/registry.md](migrations/registry.md)'s `LATEST_SCHEMA` marker + version-chain table
- cheat-init writes `"schema_version": "1.2"` into new states
- SessionStart hook `LATEST_SCHEMA="1.2"` — an existing user git pulls + starts a session → the hook notes the schema mismatch → the user runs `/cheat-migrate` and upgrades in 5 seconds. MINOR compatibility; not mandatory (skills fall back with `state.get(field, default)`)

### Why now

The user's real workflow: finish a draft → **often improvise changes to the copy while shooting** → the draft and the actual broadcast version diverge. The original "predict before shooting, only register after shooting" strict blind prediction made "the draft that was predicted" and "the draft actually broadcast" different — calibration distortion.

The v2 system makes "post-shoot script change" a first-class citizen: v1 stays as an archive, v2 re-judges based on the actual shooting script, and diff(v1, v2) itself becomes strong evidence for rubric upgrades (the user's revision raised ER → the tool learns that this user's ER threshold does not match the current formula). The blind-prediction principle is retained: v2 is still completed before publishing, with no play data to "cheat" with.

### Added — Codex install compatibility (@songth1ef [#6](https://github.com/XBuilderLAB/cheat-on-content/pull/6))

- **`install.sh --codex`**: installs the root routing skill `cheat-on-content` and 13 sub-skills into `~/.codex/skills/`
- **`install.sh --all`**: installs both Claude Code and Codex skills
- **`uninstall.sh --codex` / `--all`**: symmetrically uninstalls Codex or the dual install
- **Codex routing note**: Codex triggers the same flow with natural language and does not depend on Claude Code's `/cheat-*` slash-command harness

### Added — Migration system (letting long-term iteration not disrupt existing users)

- **`/cheat-migrate` skill**: upgrades an existing user's `.cheat-state.json` from an old `schema_version` to the current `LATEST_SCHEMA`. Idempotent, no version skipping, failure stops at the breakpoint
- **`migrations/` directory**: single source of truth for version evolution
  - `registry.md`: the `LATEST_SCHEMA` marker + the full version-chain table
  - `<from>-to-<to>.md`: 4 sections per migration step (WHAT changed / WHY / HOW Claude steps / Manual fallback)
- **`shared-references/migration-protocol.md`**: evolution philosophy + maintainer checklist (the 4 things a schema bump must do)
- **SessionStart hook enhanced**: detects `state.schema_version != LATEST_SCHEMA` → prints a non-blocking warning suggesting `/cheat-migrate`
- **`install.sh --reinstall-hooks <project>`**: rewrite the scripts in the user project's `.cheat-hooks/` after git pull (without touching state / rubric / predictions)
- **state-management.md upgraded**: all schema-upgrade docs point to cheat-migrate; the MINOR / MAJOR boundary is made explicit

### Why now

v0.1.0 users' state is schema 1.1. If later changes alter field semantics, remove fields, rename, etc. → without a migration system, existing users would be stuck after git pull. This system makes "long-term iteration does not disrupt existing users" the norm.

### Fixed

- **cheat-init `content_form` stored as a letter bug**: the Phase 3 state JSON template used the abstract placeholder `<Q1>`, causing Claude to literally write `"a"` into the state file instead of the enum `"opinion-video"`. Fix: explicit letter→enum mapping tables for Q1/Q3/Q4/Q5 + a bold warning in the Phase 3 template. Also filled in 7 missing `last_*` init fields (previously backstopped by `state.get(field, default)`) + `enabled_perf_adapters` derivation + forced `initialized_at` to use the local `+08:00` timezone rather than UTC `Z`

### Changed — README rewrite (positioning adjustment after the v0.1.0 ship)

- Title: English `Cheat on Content`, subtitle `creator cheat code` (previously "creator cheater")
- Tagline confronts the "cheating" frame: "Making content is essentially cheating — whoever sees the patterns first takes the traffic"
- New section "But can't ChatGPT / Doubao / DeepSeek do this too?" — core positioning as "your own operations expert + automatic evolution"
- Removed the early-product warning section (the badge + this CHANGELOG already convey it; repeating it signals insecurity)
- Cut ARIS attribution (keeping the multi-adapter design idea, dropping external credit)
- README total length 330 lines → 90 lines
- cheat-init Phase 1 first-screen copy rewritten in sync: dropped methodology philosophy, kept 2 caveats (inaccurate early on + strongly recommend importing a benchmark)

### Remaining items

- Step B: soften more hardcoded rules
- A redacted snapshot of the full reference implementation

---

## [0.1.0] — 2026-05-05

> ⚠️ **Early product (v0.x) — the state schema may still break**
>
> Before v1.0, each upgrade may change the field structure of `.cheat-state.json`. **Back up your entire `<your-channel>/` directory before upgrading**. Major breaking changes are marked `BREAKING` in this CHANGELOG, with manual migration steps where possible.

### Added

- **Methodology + 12 sub-skills**: the full closed loop init → learn-from → seed → score → predict → shoot → publish → retro → bump, plus the status / recommend / trends helpers
- **3 non-negotiable principles**: blind prediction + upgrade = full re-score + the rubric is a workbench, not a museum (see `shared-references/`)
- **`/cheat-learn-from` benchmark account import**: derive base rubric signals + script patterns from 5-10 benchmark samples. Two input methods (paste text default / whisper transcription) + two data methods (manual entry / adapter auto-fetch)
- **Buffer alert system** (cadence-protocol): derive color thresholds from publish frequency, with gap warnings
- **Unified prediction format + confidence levels**: the same 7-component prediction at every stage; the header shows 🔴/🟠/🟡/🟢/🔵 confidence levels
- **prediction-immutability hook**: harness-level enforcement of principle #1 (end-to-end validation 5/5 passed)
- **SessionStart auto-report hook**: automatically render a status report on every session start
- **Cross-model bump audit** (mcp__llm-chat__chat): call an external LLM for an independent judgment during rubric upgrades
- **douyin-session adapter** (Playwright): auto-fetch Douyin video + comment data
- **whisper adapter**: transcribe video files into transcripts
- **9 templates** + **2 starter rubrics** (opinion-video v2 calibrated / opinion-video-zero v0 equal-weight)
- **score-curve.py**: a diagnostic tool for prediction-accuracy convergence curves

### Soft rules (Claude judgment first, not hard thresholds)

The rules below **have default reference values** but Claude may soft-violate them given strong signals:

- Bump trigger sample count (default ≥5; exceptions may be made for strong counterexamples)
- Same-direction deviation trigger (default ≥3 consecutive; exceptions may be made for 1 extreme deviation)
- Benchmark influence fade-out (default calibration_samples ≥10; exceptions may be made based on "the degree of divergence between user data and the benchmark")
- Observation promotion threshold (default ≥2 samples; exceptions may be made for strong signals)

When soft-violating, Claude must explicitly mark it `judgment-driven` for the user to review.

### Hard constraints (no soft violation)

- Bump validation `THRESHOLD = 4/5` (statistical rigidity)
- Prediction immutability hook (binary)
- `RETRO_WINDOW_DAYS = 3` by default (users may configure 1/7)
- ≥3 benchmark samples are required before patterns can be broken down
- ≥20 top comments are required to complete a manual-paste retrospective

### Known limitations

- **v0.x has no automatic migration**: if the state schema changed during an upgrade, existing users must manually wipe + re-init
- **Adapter fragility**: the Douyin / Xiaohongshu adapters rely on anti-scraping bypass and may break when the platforms redesign; they need continuous maintenance
- **whisper Chinese accuracy**: the medium model is good enough; long-form accuracy is average; key scripts should be manually reviewed

---

## Upgrade guide (pre-v1.0)

After every git pull:

1. **Symlink-mode install (recommended)**: takes effect immediately; no reinstall needed
2. **Copy-mode install**: rerun `bash install.sh --copy`
3. **If the CHANGELOG marks `BREAKING`**: follow the manual migration steps. When there are no steps, wiping + re-initializing is recommended
