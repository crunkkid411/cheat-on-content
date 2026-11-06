---
name: cheat-seed
description: Talk through content topics with the user — **one at a time by default**; the user offers a subject or an experience, and the AI digs into their input, distills an angle, and writes a draft. This is not the AI chasing the user with three open questions, nor dumping 5 candidates at once. Triggers: "找选题" / "我想做一条 X" / "最近有个想法" / "seed" / "启动种子". Optional batch mode: `/cheat-seed --batch 5` runs the old brainstorm-5-candidates + write-5-drafts flow.
argument-hint: "[— batch: N] [— sources: <comma-separated>]"
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-seed — topic conversation (default) / batch brainstorm (optional)

The core of cheat-seed is **discussing topics with the user**, not mechanically brainstorming. Good content comes from the user's real experience + observations + emotions — none of which an AI can brainstorm out of thin air. The AI's role is to **listen → help distill an angle → write one draft**, not dump 15 candidates for the user to pick from.

**Default mode**: conversational, one at a time.
**Batch mode** (`--batch N`): keeps the old brainstorm-N-candidates + write-N-drafts flow, for users who "have no ideas at all + want to initialize in bulk".

## Three modes (auto-detected)

```
Mode A — the user proactively gives a subject (**most common**):
  User: "/cheat-seed" + directly says "I want to make one about X"
       or: "/cheat-seed at the meeting recently my boss..."
  ↓
  AI **digs into** X / that event — which moment triggered it? What part made you most [emotional / annoyed / intrigued]?
  ↓
  Converge on one concrete angle → propose → user approves → write 1 draft → done
  ↓
  Ask "next one?" or the user says "that's it for today"

Mode B — the user gives a direction but not anything specific:
  User: "I've been wanting to do something about [workplace / relationships / AI / ...]"
  ↓
  AI: "[Scope] is too broad. What specific thing you encountered recently makes you want to do this direction?"
  ↓
  Converge into a concrete experience → Mode A

Mode C — the user has no idea at all (rare):
  User: "I don't know what to make" / "help me think of a topic"
  ↓
  AI: "OK, entering brainstorm mode — first grab trends + your previous interest areas, then give you 1 suggestion"
  ↓
  Run trend-sources to grab trends + read candidates.md / predictions/ to see the user's history
  ↓
  Propose 1 angle (not 5) → user approves → write draft

Batch Mode — the user explicitly asks for bulk (`/cheat-seed --batch 5`):
  Follows the old brainstorm flow: 3 questions → 15 candidates → user picks → write 5 drafts.
  For users who "want to settle the next 2 weeks of topics in one go today".
```

**Key corrections** (vs the old version):
- The AI **does not open with questions** — it waits for user input, then digs deeper
- One topic at a time, not 5
- Default is conversational + one at a time; batch is an escape hatch

## Constants

- **DEFAULT_TREND_SOURCES = ["manual-paste"]** — only used in Mode C / gray-area Mode A / Batch. Users can add aihot / trendradar-mcp in state
- **TREND_TOOL_ROUTING** — routes data sources by `content_form`; see [shared-references/data-source-routing.md](../../shared-references/data-source-routing.md)
- **MODE_B_MAX_REPROBE_TURNS = 2** — Mode B's "why" follow-up is capped at 2 rounds; beyond that, switch to Mode C
- **MAX_DEEP_DIVE_TURNS = 4** — Mode A's convergence stage is capped at 4 follow-up rounds, to avoid over-interrogating the user
- **WITH_DRAFT = yes** — by default, write the draft immediately after the angle is confirmed; the user can say "wait, I'll write it myself" to skip
- **DRAFT_LENGTH** — derived from `state.typical_duration_seconds`: 30s→100-200 words / 90s→250-500 / 240s→600-1000 / 450s→1100-2000 / 900s→2200+
- **HUMANIZE_DRAFT = on** (default) / off — after the draft is written, run it through the `humanizer` skill to remove AI writing tells (em-dash overuse / rule of three / inflated vocabulary / vague attributions etc.). When off, output the raw AI draft. **Only humanize the body; do not touch the header's "must rewrite" warning**

## Inputs

| Required | Source |
|---|---|
| `.cheat-state.json` | read calibration_samples / typical_duration / cadence |
| `rubric_notes.md` | read the current rubric (for rough scoring) |
| `script_patterns.md` | read existing patterns (pick a structure from the cheat sheet when writing a draft) |
| `predictions/*.md` (if any) | published history, used as context during brainstorming |
| `audience.md` (if any) | audience persona — the "who is watching" mirror when choosing topics / writing drafts (derived by `/cheat-persona`) |

## Workflow

### Phase 0: Pre-flight check + load all context (**core: 3 context sources**)

1. Read `.cheat-state.json` → if missing, tell the user to run `/cheat-init` first
2. Read `rubric_notes.md` for the current formula (for rough scoring)
3. Read `script_patterns.md` — pick a structure from the cheat sheet when writing a draft
4. **Read existing prediction files** (including reconstructed ones imported at init) as **context source A** (the user's own history):
   - 0 → A is empty
   - ≥1 → A has content; extract (title / 7 dimensions / actual performance)
5. **Read `benchmark.md`** (if it exists) as **context source B** (benchmark account):
   - `state.benchmark_status = imported` → B has content; extract the benchmark's sample-topic distribution, tone, and patterns
   - `state.benchmark_status = none / pending` → B is empty
6. **Read `audience.md`** (if it exists and is not an empty skeleton) as the **audience mirror**:
   - Confidence 🟡 or above (derived from real retro data) → use it as the "would this persona care?" check when choosing topics / writing drafts
   - Confidence 🔴/🟠 (empty / benchmark-seeded only) → treat as a weak reference, not a hard constraint
   - **Does not feed into rough scoring** — audience.md is a creative lens; rough scoring still uses only the rubric. The persona affects "what to write / which angle", not the score
7. Check the user's input — whether it contains a concrete topic / experience, and decide Mode A/B/C/Batch

**Context priority during brainstorming** (**Claude judges** — the following is the reference default):

- **A dominates** (the user's own data): when Claude judges that the user's data can already drive direction (reference default: `calibration_samples ≥ 10`, but Claude may act earlier — e.g. N=5 but with ≥3 strong samples that clearly diverge from the benchmark)
- **B dominates** (benchmark): when the user has little data + the benchmark has content
- **B absent** (benchmark empty) + the user has little data: rely purely on user input + trend fetching; explicitly tell the user "no benchmark and not enough of your own data — I suggest running /cheat-learn-from before brainstorming again"

The basis for judgment is **not a rigid sample count**, but:
- Whether the user's last N samples' actual performance **matches the benchmark's high-performing sample types** — if so, the benchmark is still useful; if not, the user has gone their own way
- The user's sample **diversity** — 3 pieces of the same type is not mature; 3 pieces across different categories is more credible than 10 of the same type

### Phase 1: Mode routing

Read the user's input and identify:

**Contains a concrete noun + emotion / experience words** ("yesterday at the meeting..." / "I saw X and it made me..." / "I feel about Y...") → **Mode A** (dig deeper; if the topic is current events, Phase 2A.5 asks whether to pull external data)

**Contains a direction word but nothing concrete** ("want to do workplace" / "AI direction" / "relationships") → **Mode B** (ask only "why do you want to do this" — a window for the user's introspection; **do not call any trend tool**)

**Explicitly says they have no idea** ("don't know what to make" / "help me think" / "just give me something") → **Mode C** (call trend tools per [data-source-routing.md](../../shared-references/data-source-routing.md) + user picks + back to introspection; if all fails, fall back to the "talk about experiences" three options)

**Explicit `--batch N`** (user asks for bulk) → **Batch Mode**

**Bare `/cheat-seed` with nothing else** → **ask the entry question**:

```
What do you want to do today?

- Have a subject / experience in mind → just tell me ("I want to make one about X" / "recently I X...")
- Know the general direction → tell me ("want to do workplace" / "AI direction") → I'll ask you one question about why you want to do it
- No idea at all → say "help me think" → I'll use [aihot / trendradar] to pull today's trends for you
- Bulk → say "batch <N>"

(I won't chase you with a pile of open questions — give me one sentence and I'll start)
```

Note this is the **only open-ended question** — asked only when the user **barely triggers** `/cheat-seed`. If the user already provided content in the trigger phrase ("/cheat-seed I want to make..." or "find a topic, recently at the meeting..."), go straight to Mode A/B/C without asking this.

### Phase 2A: Mode A deep dive (the user gave a concrete topic / experience)

**Core principle**: dig into what the user gave you; **do not switch to a different subject**.

**Follow-up types (pick per situation)**:

- Trigger moment: "You said X — which specific moment first made you want to make this?" / "What made you feel this deserved a video?"
- Emotional anchor: "Which detail in this made you most [angry / find it absurd / find it interesting]?"
- Angle choice: "Do you want to say [angle a: critique the phenomenon] or [angle b: self-reflection] or [angle c: generalize to the universal]?"
- Audience imagination: "Who do you picture listening? How would they feel / would they share it?"
- Objection probing: "If someone objected with [opposing view X], how would you respond?" — forcing the user to think through their stance

**Follow-up discipline**:
- Ask only **1** question at a time (do not fire 3 in a row)
- Cap at `MAX_DEEP_DIVE_TURNS` rounds (default 4) — beyond that, converge proactively: "OK I think I have enough, let me propose an angle"
- If the user's reply contains emoji / is very short / sounds impatient → converge immediately; do not push

**Convergence output**:

```
I think this angle can work:

[One-sentence thesis: under 50 words]

Approach:
- Use [Pattern X structure] (from script_patterns.md)
- Hook: [specific scene / line]
- Body: [what the 3 observations are]
- Ending: [direction for the MVP line]

Rough score (v0 equal-weight 7 dimensions): ER=X HP=X QL=X NA=X AB=X SR=X SAT=X → composite ≈ X.X
Confidence: 🔴 Very low (you've only calibrated 0/N pieces)

Want me to write a draft first? (yes / change angle / I'll write it myself)
```

User says yes → Phase 4 writes the draft.
User says "change angle" → back to Phase 2A, dig deeper.
User says "I'll write it myself" → add the candidate to candidates.md marked tier1, end.

### Phase 2B: Mode B — ask only "why", triggering the user's introspection

The user gave a direction but nothing concrete ("want to do workplace" / "AI direction" / "relationships"). **Do not call any trend tool in this phase** — it is a window for the user's introspection; external information contaminates it.

Ask one question, **straight to the point**:

```
Why do you want to make this topic?
```

Do not offer "a/b/c three examples" — that dumps options for the user to pick and breaks introspection. Let the user form their own words.

**Route by the user's answer**:

| User answer | Classification | Behavior |
|---|---|---|
| Contains a concrete experience / personal sticking point ("I work overtime a lot myself" / "I saw X and it made me...") | **Real motive** | Switch to Mode A deep dive (Phase 2A) |
| Abstract popularity attribution ("this topic is hot lately" / "everyone is doing it" / "I heard it grows followers") | **Empty motive** | Ask back "then what angle on this topic do you personally feel most strongly about?" — force out a personal stake; still empty → switch to Mode C |
| "I don't know either" / "a friend said it makes money" / vague deflection | **Genuinely no idea** | Switch directly to Mode C |

**Follow-up discipline**: at most 2 rounds. If the 2nd round still yields no real motive → switch directly to Mode C; **do not dig forever**.

> Design intent: Mode B is a "filter", not a "factory". Users come here either to reveal their real motive (→ Mode A) or to reveal that they actually have no idea (→ Mode C). Both beat forcing a topic out of Mode B.

### Phase 2C: Mode C — external material + user picks + back to introspection

The user has no idea at all (said so explicitly / arrived from Mode B). **This is the only entry point that calls trend tools by default**.

Per the routing rules in [shared-references/data-source-routing.md](../../shared-references/data-source-routing.md):

1. **Pull external material** (pick a trend source by `content_form`):
   - `tutorial-builder` / AI-related → call the aihot skill
   - `opinion-video` / `long-essay` / `podcast` / `other` → call trendradar-mcp (if enabled)
   - `mixed` → call both
   - Neither available → manual-paste (ask the user: "what did you see today that could be filmed? Paste a few URLs/titles")

2. **Fall back to talking about experiences** (user refuses external material / is not interested in any of it):

   ```
   None of the external material resonates, so come back to yourself. Three openings — pick one and start talking:

   a) Something concrete you encountered recently? ("last week I saw my colleague X...")
   b) Something you read / saw recently that made you want to complain? ("there's an answer on Zhihu...")
   c) An unsolved confusion you've been chewing on? ("I've never understood why X...")

   Pick any one and start talking.
   ```

3. **After pulling external material**, rough-filter with the rubric + filter by content_form, keeping the 5 best fits:

   ```
   These 5 fit your form today:
   1. [Title A] (source: trendradar / Weibo hot search / hot_score: 8.5)
   2. [Title B] (source: aihot / model category / featured)
   3. ...

   Which one resonates most? If none, reply "none" and I'll ask from another direction.
   ```

4. **User picks one → back to introspection**:

   ```
   OK [Title X]. Why does this one resonate most with you?
   Is it [angle1] or [angle2] or something else?
   ```

   → user answers → switch to Mode A deep dive.

5. **User replies "none"** → go back to Mode C step 2's "talk about experiences" fallback.

**Key**: trends are not "dump 5 candidates for the user to pick", but "give material + force the question of the user's personal stake" — the AI does not decide for the user which one is worth making.

### Phase 2A.5: Mode A gray area — the user raised a current-events topic

Mode A deep-dives the user's experience by default. But if **what the user raised is itself a current-events topic** (a product name + time word / a person's name + event word), per the "current-events detection" rules in [data-source-routing.md](../../shared-references/data-source-routing.md), **ask** whether the user wants external data as reference:

```
💡 [Topic] is current events — I can pull today's public-opinion climate (sentiment across platforms + the main angles) as reference.

Want to see it? Reply "see it" and I'll fetch; reply "no need" and I'll dig straight into your angle.
```

User replies "see it" → call the matching trend source → inline the data into the deep-dive context;
User replies "no need" → standard Mode A deep dive, no external data.

**Never fetch proactively** — the user's angle takes priority over external data, to avoid external information **biasing** the user's perspective.

### Phase 2D: Batch Mode (user explicitly passes `--batch N`)

**Keeps the old brainstorm flow**:

1. Ask the 3 checklist questions (interests / tone / red lines) — only Batch mode asks these
2. Fetch trends + Claude brainstorms 15 candidates
3. User picks N
4. Write N drafts into scripts/ — **each one still goes through Phase 4's paragraph format + Phase 4.5 self-check** (line-format + humanizer); do not skip just because it is batch

See the commit history (the old cheat-seed Phases 1-3) for details. This is an escape hatch, not the default.

### Phase 3: Compute the candidate ID + write to the candidate pool

Whichever of Mode A/B/C the path took, after the angle is confirmed:

1. Compute the candidate id: `sha256("seed-" + thesis + trigger time)[:12]`
2. Write one entry line into `candidates.md` (per the [candidate-schema.md](../../shared-references/candidate-schema.md) format)
3. Mark `tier=tier1` + `read_status=deep_read` (already discussed, not skimmed)

### Phase 4: Write the draft

`WITH_DRAFT=yes` → write in sequence to `scripts/<YYYY-MM-DD>_<id>_<short-title>.md`:

**Read `script_patterns.md` before writing** — pick the right structure for the user's topic from the "structure selection cheat sheet". If the file is still an abstract skeleton (the user has filled in few patterns), use the generic framework from the starter rubric.

**Word count**: derived from `DRAFT_LENGTH` (based on `typical_duration_seconds`).

#### ⚠️ The body must be paragraphs, not subtitle format (**the most common generation drift**)

The model's training prior turns "video script" into teleprompter/subtitle short lines by default. **That is wrong** — cheat-seed's draft is a prose draft for the user to **rewrite**, not shooting subtitles. Subtitles are auto-broken by CapCut after shooting, not the form at writing time.

When generating the body, keep this contrast in view:

```
❌ Subtitle format (do not write like this):
Have you noticed
all reviewers are saying the same thing
your research is too old-fashioned
but look closely
everything they cite is a reaction from 5 years ago

✅ Paragraph version (you must write like this):
Have you noticed that all reviewers are saying the same thing — your research is too old-fashioned. But look closely: everything they cite is a reaction from 5 years ago. AI is not new; what's new is that this time everyone woke up at once.
```

Rules:
- **Each paragraph 100-300 words**, linked naturally with commas / periods / dashes, **no hard line breaks at sentence boundaries**
- A blank line between paragraphs (start a new paragraph only on a natural topic shift)
- A draft body is usually 3-6 paragraphs; **it should not have dozens of single-sentence lines**

#### Format:

```markdown
# [Thesis title]

> ⚠️ **Draft by Claude — you must rewrite it before shooting**
>
> This is scaffolding, not a finished piece. Your tone / rhythm / personal experience cannot be AI-generated.
> Rewrite process:
> 1. **Rewrite directly in this file** (same path: scripts/<...>.md)
>    - Add your tone, personal experience, real quotable lines
>    - Cut the setup, cut model abbreviations, cut academic packaging
> 2. When done, run `/cheat-predict scripts/<this file>.md`
> 3. After shooting, run `/cheat-shoot scripts/<this file>.md`

**Article ID**: <12-char hash>
**Tone**: [derived from the discussion, not from a checklist Q]
**Target duration**: <state.typical_duration_seconds converted> minutes
**Target word count**: <derived from duration>
**Structure choice**: [explicitly mark per the cheat sheet in script_patterns.md, e.g. "metaphor first" / "data-reversal opening"]
**Patterns used**: [number + short description]
**Discussion seed**: [one sentence recapping the core of the deep dive]

---

[draft body — **paragraph version**, 3-6 paragraphs, each 100-300 words, not single-sentence fragments]
```

`WITH_DRAFT=no` (user says "I'll write it myself") → skip Phase 4 + Phase 4.5.

### Phase 4.5: Draft self-check pass (layout + de-AI-ification)

After the draft is written and saved, **before showing it to the user**, run two self-checks. **Sequence is fixed: 4.5a fixes layout first, then 4.5b removes AI tells** — humanizer works on prose, and feeding it subtitle-format fragments makes a mess.

**Why it is safe** (does not contaminate calibration): cheat-seed's draft is not what gets predicted/published — after the user rewrites, cheat-predict scores **the user's final draft**. These two steps just give the user a cleaner starting point.

#### Phase 4.5a: line-format self-check (subtitle format → paragraph version)

Phase 4's prose instruction + ❌/✅ contrast already pushes the prior down during generation, but generation can still drift. This step is the **deterministic backstop**:

```bash
# Only look at the body section (after the --- divider)
body=$(awk '/^---$/{f=1;next} f' scripts/<id>.md)
line_count=$(printf '%s\n' "$body" | grep -c .)        # non-empty line count
char_count=$(printf '%s' "$body" | wc -m | tr -d ' ')
avg_chars_per_line=$(( char_count / (line_count > 0 ? line_count : 1) ))
```

Decision: **`avg_chars_per_line < 15` and `line_count >= 8`** → judged as subtitle format → **auto-reflow**:
- Merge hard line breaks at sentence boundaries back into natural paragraphs
- Split into 3-6 paragraphs by topic shifts, each 100-300 words
- Replace the body section with Edit (header untouched)
- Add a line to the Phase 5 output: "📐 Subtitle format detected; reflowed into paragraphs"

No hit → skip; the body is already paragraphs.

#### Phase 4.5b: humanizer de-AI-ification

`HUMANIZE_DRAFT=on` (default) — run it through the `humanizer` skill. Claude's own first drafts naturally carry AI tells (em-dash overuse / rule of three / "inflated" vocabulary / vague attributions / shallow -ing analysis); this step clears them.

Steps:

1. Check whether the `humanizer` skill is available (`~/.claude/skills/humanizer/` exists):
   - Unavailable → skip 4.5b and add a line to the Phase 5 output: "(humanizer not installed; the draft is the raw AI version — `git clone https://github.com/blader/humanizer` into ~/.claude/skills/ to enable automatic de-AI-ification)"
2. Available → invoke `humanizer` via the Skill tool, **passing only the draft body** (after the `---` divider, the paragraph version already reflowed by 4.5a), **never the header**:
   - The header's `⚠️ Draft by Claude — you must rewrite it before shooting` warning is an **intentional scaffolding marker**, not prose to humanize
   - **Voice calibration**: if the user has historical scripts (`videos/*/script.md`) or has filled in `script_patterns.md`, pass the latest 1-2 as voice reference samples to humanizer — so it leans toward "**this user's voice**", not "generic human voice"
3. humanizer returns the de-AI-ified body → use Edit to replace the draft file's body section (header untouched)
4. Record the "tells fixed" reported by humanizer (e.g. `em-dash overuse ×3 / rule of three ×2 / inflated vocabulary: "profound" "essentially"`), and show them in the Phase 5 output

**Discipline**:
- humanizer **removes AI tells**; it does not **rewrite for the user**. It makes the draft less machine-written, but **it is still not the user's voice** — the header's "must rewrite" warning still holds, and the Phase 5 output must restate it
- If humanizer changes a sentence so it drifts from the `Structure choice` / patterns used → the pattern wins; roll that sentence back (the pattern was agreed with the user; humanizer should not overturn it)
- humanizer **does not handle layout** — line-break issues were fixed in 4.5a; humanizer already receives the paragraph version

### Phase 5: Output "next steps" + ask whether to continue

```
✅ Draft written: scripts/2026-05-04_<id>_<short>.md
📐 Layout self-check: passed (paragraph version)  ← or "subtitle format detected; reflowed into paragraphs"
🧹 humanizer pass: fixed em-dash overuse ×3 / rule of three ×2 / inflated vocabulary ×2
   (the draft is less "machine-flavored" now — but it is still scaffolding, not your voice)

Next you can:
- Rewrite this draft (edit the file directly) — add your tone, experience, real quotable lines
- When done, run "score this scripts/<...>.md" to see the 7-dimension score
- Decide to shoot → "start prediction scripts/<...>.md"

What do you want to do next?
(Tell me a concrete experience / topic directly, or say "that's it for today" to finish)
```

> The humanizer line appears only when `HUMANIZE_DRAFT=on` and the skill is available. When not installed, replace it with a line explaining how to enable it.

User says "that's it for today" → end cheat-seed.
User gives a new topic → back to Phase 1 for routing.

## Key Rules

1. **The AI does not open with questions** — it asks the entry question once only when the user barely triggers `/cheat-seed`; otherwise **wait for user input, then dig deeper**
2. **One topic at a time** — Modes A/B/C all give 1 suggestion by default; go to Batch only when the user explicitly asks for bulk
3. **Follow-up discipline**: 1 question at a time, at most 4 rounds, converge immediately when the user is impatient
4. **Dig into the topic the user gave**; do not switch — if the user says "my boss yelled at me in a meeting", the AI should not ask "so have you recently felt AI makes everyone...", a parallel topic
5. **Read script_patterns.md before writing a draft** — pick a structure from the user's existing patterns
6. **The draft is scaffolding** — the header carries a prominent "must rewrite" warning
7. **humanizer only removes AI tells; it does not rewrite for the user** — Phase 4.5b makes the draft less machine-flavored, but it is still not the user's voice; the "must rewrite" warning does not expire because it passed through humanizer
8. **The body is paragraph version, not subtitle format** — watch the ❌/✅ contrast in Phase 4 while generating; Phase 4.5a uses `avg_chars_per_line < 15 and line count ≥ 8` as the deterministic backstop and reflows on a hit. Subtitles are auto-broken by CapCut after shooting, not the form at writing time

## Refusals

- "Skip the deep dive, just write the draft" → ask "Do you want to just give me the topic and have me write it? OK, but the draft quality may suffer — I don't know your angle. Give me a one-sentence thesis and I'll write"
- "AI decides the topic for me" → refuse. In Modes A/B/C the AI always only **presents external material** + **asks the user's angle**; it does not decide "which one to make" for the user
- "I can't be bothered to answer why in Mode B; just give me 5 candidates" → refuse. Mode B's "why" is a filter — if you cannot answer it, you should not use Mode B's direction. Either go to Mode A with a concrete experience, or go to Mode C and I'll help you find material
- "In Mode A, just pull trends without asking me" → refuse. In Mode A the user already has an angle; pulling external data without permission contaminates their perspective. See [data-source-routing.md](../../shared-references/data-source-routing.md)
- "Write 5 drafts at once" → not in the default flow. The user must explicitly pass `--batch 5`
- "I can't be bothered to rewrite; I'll shoot the AI draft directly" → warn "a directly AI-generated script tends to score low on ER and will contaminate your calibration data", but allow it if the user insists (mark `unmodified_ai_draft: true`)

## Integration

- Upstream: at the end of `/cheat-init` Phase 5, when `pool_status=none + calibration_samples=0`, it proactively asks "run /cheat-seed now?"
- Upstream: `/cheat-recommend` mentions `/cheat-seed` in its guidance copy when candidates is empty
- Upstream: `/cheat-status` prompts "haven't shot anything yet — run /cheat-seed?" when `pool_status=none + >24h since init`
- Downstream: the user's candidate → candidates.md (tier1, deep_read already done)
- Downstream: (default) draft → Phase 4.5 humanizer de-AI-ification → scripts/<id>.md → user rewrites → /cheat-predict
- Optional dependency: the [`humanizer`](https://github.com/blader/humanizer) skill (MIT, external project). When installed at `~/.claude/skills/humanizer/`, Phase 4.5 is enabled automatically; otherwise it is skipped gracefully. **Not bundled into cheat-on-content** — the user clones it themselves
- Difference from `/cheat-trends`: cheat-seed is **discussion + draft writing** (conversation-heavy); cheat-trends is **multi-adapter fetching + rough scoring** (fetch-heavy). Different purposes; they do not replace each other.
