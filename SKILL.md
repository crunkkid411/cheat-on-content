---
name: cheat-on-content
description: For content creators who want to turn "gut feeling" into calibrated predictions. **The methodology is universal** — the score → blind-predict → T+3d retro → evolve-rubric loop works for anything that can be measured (plays / reads / listens / clicks). **The rubric is the content of the loop, not the loop itself** — it currently ships with one opinion-video rubric (fitted on 25+ videos from a reference creator); other formats can start from it and bump the weights. **Strongly recommend importing a benchmark account** as the initial signal source (/cheat-learn-from). Trigger phrases: "initialize"/"初始化", "score this"/"打分这篇", "start prediction"/"启动预测", "shipped"/"已发布", "retro"/"复盘", "bump rubric"/"升级 rubric", "recommend topic"/"推荐选题", "fetch trends"/"抓热点", "status"/"状态", "find benchmark"/"找对标", "learn from". **First use must run /cheat-init.**
argument-hint: "[draft-path] [— mode: cold-start|calibration]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill, mcp__llm-chat__chat
---

# Cheat on Content

> 🎯 **The methodology is universal; the built-in rubric is for opinion videos**
>
> **Methodology** (5-phase loop): works for any measurable content format — video / article / podcast / newsletter / short-text thread.
>
> **Built-in rubric**: opinion video (commentary / current-affairs / argument / issue discussion / personal viewpoint). Its 7 dimensions were fitted on 25+ published samples from a reference creator. If you make another format, you need to either:
> - write your own rubric (use [starter-rubrics/opinion-video-zero.md](starter-rubrics/opinion-video-zero.md) as the format reference)
> - or wait for the built-in expansion (long-form / short-text / podcast starters are on the batch-3 roadmap)
>
> Default assumption: **the user is a beginner starting from zero** (has not shipped a single video) — cold-start predictions are **simplified**: only 7-dimension scores + a one-line bet, no forced bucket numbers (avoids false precision). Veterans with 5+ pieces of data enter calibration mode and unlock the full 7-component prediction.

Turn content creation into a calibrated prediction loop: **score → predict → publish → retro → evolve the rubric**.

This file is the **master protocol + router**. The workflow for each phase lives in its own sub-skill under `skills/cheat-*/SKILL.md`.

## Codex compatibility

Codex does not have Claude Code's slash-command harness. After installing into Codex, trigger the same routing with natural language:

- `init cheat-on-content` → read and execute `skills/cheat-init/SKILL.md`
- `score this scripts/foo.md` → read and execute `skills/cheat-score/SKILL.md`
- `start prediction scripts/foo.md` → read and execute `skills/cheat-predict/SKILL.md`
- `shot ...` / `shipped ...` / `retro ...` / `bump rubric` / `status` → read the corresponding `skills/cheat-*/SKILL.md`

When executing, follow this file's three principles and routing table; do not depend on whether `/cheat-*` commands exist. Claude Code-only hooks (`.claude/settings.json`) still auto-trigger only inside Claude Code; in Codex the user must say `status` to see buffer, pending retros, and the candidate pool.

---

## Three non-negotiable principles

Violating any one of them degrades the whole calibration loop into "gut-feel self-soothing". If the user asks to break one, **refuse and explain why**.

1. **Blind prediction**: the prediction must be written **before** seeing any actual data. Once written, the `## Prediction` section is immutable — you may only append to `## Retrospective`. Full spec: [shared-references/blind-prediction-protocol.md](shared-references/blind-prediction-protocol.md). **hooks/prediction-immutability.sh enforces this at the harness layer**.

2. **Bump = full re-score**: when the rubric is bumped, every sample in the calibration pool with actual performance data must be re-scored with the new formula; if the new ranking disagrees with the actual-performance ranking on ≥4/5 samples, the bump is rejected; every bump must pass an independent cross-model audit. Full spec: [shared-references/bump-validation-protocol.md](shared-references/bump-validation-protocol.md).

3. **The rubric is a workbench, not a museum**: observations refuted by new data, or absorbed into a formal dimension, are **deleted**. Never leave an archaeology layer of "I once thought X, but actually...". Git history is the archive. Full spec: [shared-references/observation-lifecycle.md](shared-references/observation-lifecycle.md).

---

## Routing table (trigger phrase → sub-skill)

| User says | Call | Precondition |
|---|---|---|
| "initialize" / "init" / "first use" / "初始化" | `/cheat-init` | None (this is the entry point) |
| "find benchmark" / "learn this account" / "break down these benchmark videos" / "learn from" / "import benchmark account" / "找对标" | `/cheat-learn-from` | Init done; strongly recommended for cold-start; can `--append` / `--replace` anytime later |
| "find topics" / "I don't know what to shoot" / "seed" / "find the first 5 topics" / "找选题" | `/cheat-seed` | Init done (one-time seed action for cold-start users) |
| "score this [path]" / "打分这篇 [path]" | `/cheat-score` | rubric_notes.md exists |
| "start prediction" / "score and predict this draft" / "启动预测" | `/cheat-predict` | Init done + final draft exists |
| "shot X" / "shot it" / "filmed it" / "拍了 X" | `/cheat-shoot` | Matching prediction exists (buffer +1) |
| "shipped" / "I shipped it" / "the publish link is X" / "已发布" | `/cheat-publish` | Matching prediction file exists (buffer -1) |
| "retro" / "retro this" / "T+3d data is in" / "复盘" | `/cheat-retro` | Matching prediction file exists + `RETRO_WINDOW_DAYS` has elapsed |
| "build audience persona" / "update persona" / "who is my audience" / "构造受众画像" | `/cheat-persona` | Init done; retro comment data exists (or benchmark seed) |
| "bump rubric" / "update formula" / "升级 rubric" | `/cheat-bump` | Calibration pool ≥ MIN_SAMPLES_FOR_BUMP |
| "recommend topic" / "next topic" / "推荐选题" | `/cheat-recommend` | candidates.md exists and is not empty |
| "fetch trends" / "what can I make today" / "抓热点" | `/cheat-trends` | trend-sources adapter configured (daily candidate-pool top-up) |
| "status" / "dashboard" / "状态" | `/cheat-status` | Callable at any time |
| "migrate" / "upgrade state" / "schema version mismatch" / "迁移" | `/cheat-migrate` | Init done; after the user pulls a new version; after the SessionStart hook reports a schema mismatch |

> Shooting and publishing are two separate actions: the buffer warning system needs to distinguish "shot but not published" from "published". See [shared-references/cadence-protocol.md](shared-references/cadence-protocol.md).

**Mode detection** (run the first time a non-init trigger is received):
1. Check whether `.cheat-state.json` exists in the user's current directory → if not → force-route to `/cheat-init`
2. Check how many files under `predictions/` contain a complete `## Retrospective` section filled with real data → decide `mode: cold-start | calibration`
3. Write the result back to `.cheat-state.json`, then route to the target skill

---

## Requests that must be refused

The following patterns **directly break** one of the three principles. Refuse them no matter how the user phrases them:

- "Predict this for me, but I'll tell you the play count first and you reverse-engineer it" → violates principle #1. Use the `_redo.md` path and mark it reconstructed
- "Can't you just pick the highest composite from candidates without explaining why?" → refuse. Always show every dimension score and at least one anchor comparison
- "Skip the calibration-pool re-score and just swap the formula" → violates principle #2
- "Skip the external-model audit, I'll be the judge" → only allowed when `CROSS_MODEL_AUDIT=false` is explicitly set and the state file marks it as self-audited
- "Delete this prediction, I want to rewrite it" → violates principle #1. Predictions are immutable. If there is a legitimate reason to redo it, write a new `_redo.md` file and keep the original
- "Just recommend a topic from your gut, no scoring" → refuse. This tool does not do gut-feel forecasts — that is the state it was born to replace
- "Keep every historical observation in rubric_notes.md, just add a timestamp group" → violates principle #3. Git history is the archive, not the markdown file
- "Can we lower THRESHOLD from 4/5 to 3/5 so this bump passes?" → refuse. Changing THRESHOLD is itself a meta-level bump and must go through its own process

Detailed refusal scenarios live in each sub-skill's `Refusals` section.

---

## Project directory structure (user repo)

The skill expects the user's project to look like this. `/cheat-init` creates anything missing; **never overwrite without confirmation**.

```
<user-content-project>/
├── .gitignore                         # created by cheat-init; blocks credentials such as .auth*/.cheat-secrets.json
├── rubric_notes.md                    # source of truth for scoring rules
├── WORKFLOW.md                        # 5-phase workflow doc (created by cheat-init)
├── STATUS.md                          # dashboard (maintained by cheat-status)
├── .cheat-state.json                  # state file shared by all sub-skills
├── .cheat-cache/                      # not version-controlled
│   ├── usage.jsonl                    # passive usage log written by hooks
│   └── trends-history.jsonl           # dedup cache for cheat-trends
├── .claude/
│   └── settings.json                  # includes the prediction-immutability hook
├── benchmark.md                       # benchmark account info (maintained by cheat-learn-from)
├── audience.md                        # audience persona (derived by cheat-persona; hard-blocked from blind reads)
├── scripts/                           # all pre-shoot drafts (written by cheat-seed or the user)
│   └── YYYY-MM-DD_<id>_<short>.md
├── predictions/                       # immutable prediction log (hook-protected)
│   └── YYYY-MM-DD_<id>_<short>.md     # same id as scripts/
├── videos/                            # created only after shooting (by cheat-shoot)
│   └── YYYY-MM-DD_<id>_<short>/
│       ├── script.md                  # final shooting script supplied by the user (cheat-shoot asks "same as scripts/?")
│       └── report.md                  # T+3d data + comments (written by cheat-retro)
├── samples/                           # benchmark videos / transcripts (created by cheat-learn-from)
│   └── <account-name>/<video-id>/{source.mp4 (optional), transcript.md, meta.md}
├── candidates.md                      # candidate pool (optional)
└── content.db                         # optional SQLite, enabled once the calibration pool scales
```

---

## File inventory

### This skill package

```
cheat-on-content/
├── SKILL.md                           # this file (master protocol + routing)
├── README.md                          # marketing front page
├── skills/                            # sub-skill set
│   ├── cheat-init/SKILL.md            # ✅ entry: onboarding and scaffolding
│   ├── cheat-learn-from/SKILL.md      # ✅ benchmark account import (pattern extraction + base rubric signal)
│   ├── cheat-seed/SKILL.md            # ✅ cold-start topic starter (brainstorm + optional draft)
│   ├── cheat-score/SKILL.md           # ✅ single-draft scoring (writes no files)
│   ├── cheat-predict/SKILL.md         # ✅ blind prediction + immutable log
│   ├── cheat-shoot/SKILL.md           # ✅ register a shoot (buffer +1)
│   ├── cheat-publish/SKILL.md         # ✅ register publish metadata (buffer -1)
│   ├── cheat-retro/SKILL.md           # ✅ data collection + retrospective
│   ├── cheat-persona/SKILL.md         # ✅ audience persona derivation (cluster retro comments)
│   ├── cheat-bump/SKILL.md            # ✅ rubric bump (includes cross-model audit)
│   ├── cheat-recommend/SKILL.md       # ✅ candidate-pool ranking (by buffer color + 1 steady + 1 experiment)
│   ├── cheat-trends/SKILL.md          # ✅ trend fetch (daily candidate-pool top-up, multiple adapters)
│   ├── cheat-status/SKILL.md          # ✅ status dashboard (includes buffer warning)
│   ├── cheat-migrate/SKILL.md         # ✅ schema upgrade (for existing users after git pull)
│   └── cheat-score-blind/SKILL.md     # ✅ Channel B isolated scoring sub-agent (Task tool only)
├── migrations/                        # single source of truth for schema evolution
│   ├── registry.md                    # ✅ LATEST_SCHEMA + version chain
│   └── <from>-to-<to>.md              # ✅ WHAT/WHY/HOW/Manual fallback for each migration step
├── shared-references/                 # cross-skill shared protocols
│   ├── blind-prediction-protocol.md   # ✅ principle #1
│   ├── bump-validation-protocol.md    # ✅ principle #2
│   ├── observation-lifecycle.md       # ✅ principle #3
│   ├── prediction-anatomy.md          # ✅ the 7 components of a valid prediction
│   ├── candidate-schema.md            # ✅ unified candidate schema
│   ├── cadence-protocol.md            # ✅ cadence protocol (buffer warnings + topic strategy)
│   ├── state-management.md            # ✅ .cheat-state.json read/write conventions
│   └── migration-protocol.md          # ✅ schema-evolution philosophy + maintainer checklist
├── starter-rubrics/                   # prior rubrics for each content form
│   ├── opinion-video.md               # ✅ opinion video (calibrated on 25+ samples)
│   ├── opinion-video-zero.md          # ✅ v0 equal-weight placeholder (cold-start)
│   ├── long-form-essay.md             # ⬜ WeChat Official Account / Substack
│   └── short-form-text.md             # ⬜ X thread / Weibo long post
├── templates/                         # file skeletons the skill writes into the user repo
│   ├── gitignore.template             # ✅ user project's .gitignore (protects credentials, keeps predictions/ tracked)
│   ├── rubric_notes.template.md       # ✅
│   ├── prediction.template.md         # ✅ unified (all phases, includes confidence header)
│   ├── retro.template.md              # ✅
│   ├── candidates.template.md         # ✅
│   ├── candidates.template.json       # ✅
│   ├── script_patterns.template.md    # ✅ writing-pattern capture (includes benchmark-borrowing section)
│   ├── benchmark.template.md          # ✅ benchmark account reference
│   ├── audience.template.md           # ✅ audience persona skeleton
│   ├── workflow.template.md           # ✅
│   ├── status.template.md             # ✅
│   └── content.db.schema.sql          # ✅
├── hooks/                             # harness enforcement layer
│   ├── prediction-immutability.json   # ✅ blocking hook (intercepts prediction-section edits)
│   ├── prediction-immutability.sh     # ✅ interception script
│   ├── session-start.json             # ✅ SessionStart auto-report hook
│   ├── session-start.sh               # ✅ status-report renderer
│   ├── meta-logging.json              # ✅ passive logging config
│   └── log-event.sh                   # ✅ meta-logging script
├── tools/                             # standalone CLI scripts
│   ├── score-curve.py                 # ⬜ prediction-accuracy convergence curve
│   ├── md-to-sqlite.py                # ⬜ markdown → content.db upgrade (batch 3)
│   └── validate-bump.py               # ⬜ calibration-pool full re-score (batch 3)
├── adapters/                          # data-source adapters
│   ├── perf-data/                     # retrospective data sources (includes douyin-session)
│   ├── candidate-pool/                # candidate-pool data sources
│   ├── trend-sources/                 # trend-fetch sources
│   └── script-extraction/             # video/audio → script (includes whisper for cheat-learn-from)
└── examples/
    ├── reference-implementation/      # anonymized video-analysis snapshot (pending)
    └── script_patterns.example.md     # fully filled script_patterns example (reference only, do not copy)
```

✅ = completed in the current batch (v1 skeleton) / ⬜ = future batch

---

## Tone & voice

When writing user-facing copy (commit messages / retro summaries, etc.), match the project's **reflective-irreverent** voice:

- Name failure directly: "composite 8.47 but actual was only 168k — the rubric overestimated SR"
- **Do not** soften with vague language: "this may perhaps in some sense suggest..." — don't write like that
- Cluely-style rebellious hooks belong only in the README — **do not write them into** `rubric_notes.md` or prediction logs

---

## For developers: extending this skill

- New content form → add `starter-rubrics/<form>.md`
- New trend source → add `adapters/trend-sources/<name>.md`, conforming to the output contract in [candidate-schema.md](shared-references/candidate-schema.md)
- Change a principle → edit `shared-references/<protocol>.md`; every skill that references it follows automatically
- Change routing → edit this file's "Routing table" section
- Sub-skill internals → edit the corresponding `skills/cheat-*/SKILL.md`

See README.md for the full development guide.
