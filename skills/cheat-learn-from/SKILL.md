---
name: cheat-learn-from
description: Import scripts + data from a benchmark account → break down patterns + derive base rubric signals → write to benchmark.md / script_patterns.md / rubric_notes.md. **This is the tool's earliest source of signal** — cold-start users with no history rely entirely on the benchmark, and users with publishing history should still import at least 1 benchmark as a sanity check. Triggers: "学这个账号" / "拆这几个对标视频" / "learn from" / "导入对标账号" / "找对标".
argument-hint: <account-name> [— way: a (default) | b] [— append | --replace]
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-learn-from — benchmark account import

The tool's most important early signal source is a **benchmark account** — after init you have no data, and an equal-weight v0 rubric is astrology. But if you can find an account you want to become, and import 5-10 of its high / medium / low samples, the tool has anchors.

Later, once your own calibration_samples ≥ 10, the benchmark's influence fades naturally — your real data becomes the main signal source. But benchmark.md is **not deleted**; it remains a reference frame for cheat-seed brainstorming.

## Overview

```
[User: learn from this account / start cheat-learn-from]
  ↓
[Phase 0: check benchmark status]
  ↓
[Phase 1: choose input method (Way a default)]
  ↓
[Phase 2: collect material]
  Way a: user pastes N script texts + data
  Way b: transcribe videos in the samples/ directory with whisper
  ↓
[Phase 3: ask for each sample's "impression judgment" (high/medium/low + why)]
  ↓
[Phase 4: Claude breaks down patterns + derives rubric signals]
  ↓
[Phase 5: user review → revise → persist]
  ↓
[Phase 6: write benchmark.md / script_patterns.md / rubric_notes.md]
  ↓
[Phase 7: update state.benchmark_status]
```

## Constants

- **MIN_SAMPLES = 3** — at least 3 samples (fewer yields no patterns)
- **RECOMMENDED_SAMPLES = 5-10** — recommended range, balancing signal volume against user effort
- **MAX_SAMPLES_PER_RUN = 15** — per-import cap; beyond that Claude's context runs out and the user gets tired
- **DEFAULT_WAY = a** — Way a is simple + accurate, and is the default

## Inputs

| Required | Source |
|---|---|
| `<account-name>` | user argument; ask if missing |
| `.cheat-state.json` | state file |
| Way a: user-pasted script text + data | conversation |
| Way b: `samples/<account-name>/*.mp4` and other video files | the user downloads them in advance |

## Workflow

### Phase 0: Check benchmark status

Read `benchmark_status` in `.cheat-state.json`:

| Status | Handling |
|---|---|
| `none` | First import — continue to Phase 1 |
| `pending` | The user previously said they would find one later — continue to Phase 1 |
| `imported` with an existing benchmark | Ask "you already have benchmark [current name] with N samples. What do you want to do?  a) append new videos to the current benchmark  b) replace it with a new benchmark  c) just look, don't change" |

Argument parsing:
- `--append` → append to the existing benchmark
- `--replace <new-name>` → replace with a new benchmark (archive the old one to benchmark.archived/)
- No flag + an existing benchmark → run the question above

### Phase 1: Choose the input method (**two independent dimensions**)

Each sample = **script** + **data**. How you get each is independent — you can mix and match.

#### Phase 1a: script source (how to get the script)

```
How do you want to get the script?

a) **Paste text (simplest, recommended)**
   - You've already organized it yourself / extracted it with a tool — paste it straight into the conversation
   - Tool recommendations (ordered by convenience):

     Douyin / Xiaohongshu:
     - The WeChat mini-program "Qingdou" (轻抖) — paste a video link → auto-extract the script + comments. Fastest
     - Similar tools: "Video Parsing Assistant" (视频解析助手) / "Short-video Script Extractor" (短视频文案提取) and other mini-programs
     - Usually has a free quota; heavy use is paid

     Bilibili / YouTube:
     - The video page has a "show subtitles/transcript" button (if the creator enabled it)
     - Third party: DownSub / SaveSubs / yt-dlp --write-auto-sub

     WeChat Official Account / Substack:
     - Copy the web page text directly

b) **Transcribe video files with whisper**
   - You downloaded the videos to samples/<account-name>/<video>/source.mp4
   - Requires whisper-cpp + ffmpeg (see adapters/script-extraction/whisper/README.md)
   - Transcriptions may have typos / dropped words / inaccurate punctuation — less accurate than a

c) **Skip the script, use metadata + impressions only**
   - You cannot get the script and cannot be bothered with tools
   - Consequence: patterns cannot be broken down deeply (only title / data / your impression), but rubric signals are still usable
   - Good for "set it up quickly now, fill it in later"

Reply a / b / c.
```

#### Phase 1b: data source (how to get plays/likes/comments)

```
How do you want to get the data (plays / likes / comments / shares)?

a) **Type the numbers in (simplest)**
   - Check the account backend or the video page and tell me the numbers
   - No tools needed

b) **Adapter auto-fetch (if configured)**
   - You already installed a perf-data adapter (e.g. douyin-session)
   - Give me the video URL and the tool fetches the data + top comments itself
   - Comment data is more complete (typing only gives me numbers; the adapter gets the actual comment text)

Reply a / b.
```

**Most common combinations**:
- Fully zero-dependency path: 1a + 1b (paste text + type numbers) — done in 5 minutes
- Comment quality first: 1a + 2b (paste text + adapter fetch) — use this if an adapter is installed
- Fallback when the script is unavailable: 1b + 1b (whisper + type numbers)

### Phase 2: Collect material

Follow the path matching the Phase 1a + 1b combination.

**General discipline**: every sample needs at least (script or transcript or an N/A marker) + data (4 basics: plays/likes/comments/shares).

#### Path A: paste text (Phase 1a=a)

```
OK. Let's go one at a time. At least 3, 5-10 recommended.

Sample 1's script — paste the whole thing below (paragraph version, not subtitle format):
```

Script received → compute video_id (sha256(script_content)[:12]) → go to Phase 2 data collection.

#### Path B: whisper transcription (Phase 1a=b)

```
First confirm whisper is installed:

[run `command -v whisper-cpp` or `command -v whisper` to detect]

If not installed:
  ❌ whisper is not installed. Three options:
  - brew install whisper-cpp (recommended — fast)
  - pip install openai-whisper (Python, slower)
  - Switch back to Path A and paste text yourself (the Qingdou mini-program and similar are recommended)

Once installed: put the video files at samples/<account-name>/<video-name>/source.mp4
(one subdirectory per video)

When they are in place, tell me "N files ready" and I'll transcribe.
```

After the user sets it up:
1. Glob `samples/<account-name>/*/source.*` for video files
2. For each video run `bash adapters/script-extraction/whisper/run.sh <video> samples/<account-name>/<id>/`
3. Report failures but continue with the rest
4. Go to Phase 2 data collection

#### Path C: skip the script (Phase 1a=c)

Go straight to Phase 2 data collection — tell the user "without a script, the patterns I can break down are limited to the title level / your impressions; rubric signals can still be derived normally".

#### Phase 2 data collection (Phase 1b=a typed / b adapter)

**If Phase 1b=a (typed)**:

```
Sample 1's data — tell me:
- Title
- Plays
- Likes
- Comment count (the number, not the comment text)
- Shares / reposts

Any format is fine; I can parse it. For example:
  "Title: how to stop expecting
   Plays: 710k / likes 24k / comments 899 / shares 18k"

If you can also paste the top 5-10 comments (with like counts), even better — that lets the pattern breakdown reach the meme level.
```

**If Phase 1b=b (adapter)**:

```
You said an adapter is installed (e.g. douyin-session). Give me each video's URL and
I'll run the adapter to auto-fetch data + top comments.

Sample 1 URL:
```

URL received → call the matching adapter → write data + comments to `samples/<account-name>/<id>/meta.md`.

**General**: keep asking for sample 2 / 3 / ... until the user says "enough" or MAX_SAMPLES_PER_RUN is reached, then go to Phase 3.

### Phase 3: Ask for the "impression judgment"

For every sample (whether Way a or b), after collecting the data **ask for the impression**:

```
Your impression after watching / listening to this video — relative to this account:
  a) High-performing sample (a representative work / the kind you want to make)
  b) Medium-performing sample (average level / neither here nor there)
  c) Low-performing sample (not representative of this account / you do not want to make this)

Why? (one sentence — this judgment tells me more about the style you want than the data does)
```

Record (impression_label, impression_reason) in memory.

> Note: the impression **may** conflict with the data — e.g. high data but the user feels it is "not representative". That conflict is itself a useful signal; record it.

### Phase 4: Claude breaks down patterns + derives rubric signals

Read all (script, data, impression) → analyze:

#### 4a. Script patterns

Break down per the cheat-sheet framework in script_patterns.md:
- Opening hook: distribution of the 3 types (scene immersion / IS parody / data reversal)
- Body structure: how many sections / how it cuts
- Sentence patterns / length / rhythm: short or long sentences, any signature constructions
- Emotional markers / dual-channel voice
- Credits section / ending
- High-frequency vocabulary / vocabulary style

Output N concrete patterns (each citing specific samples as evidence).

#### 4b. Rubric signals (**qualitative only, no numeric weights**)

Score each sample on the 7 dimensions (using the generic dimensions), then look at:
- Which dimensions are high across high-performing samples (by user impression)?
- Which dimensions are low across low-performing samples?
- Which dimensions show no difference between high/low samples (meaning they are not key dimensions)?

Output **qualitative directions** (not numeric weights):
- "ER looks important" (3/3 high samples have ER ≥4)
- "SR looks insignificant" (no difference in SR distribution between high and low samples)
- "Samples with high MS show obvious meme explosions in the comments"

### Phase 5: User review

Show all results to the user at once:

```
From the N benchmark videos you gave me, I broke out:

📝 N script patterns:
  1. **[Pattern 1 name]**: [one-sentence description] → evidence: [samples X / Y]
  2. ...

🎯 Rubric qualitative signals:
  - Dimensions that look important: ER / QL / MS (each supported by N high samples)
  - Dimensions that look insignificant: SR / NA
  - Initial suggestion: your benchmark account is [emotion + quotable-line driven] / [data driven] / [analogy-explainer] / ...
  - **No numeric weights given directly** — fitting on 5-10 samples overfits easily; use these as tier-2 signals first

🎨 Topic-direction sense:
  - Rough topic distribution: [topic A 40% / topic B 30% / ...]
  - Tone: [one sentence]

Reply "ok" and I'll persist,
or point out which patterns / signals you disagree with ("Pattern X looks off" / "Rubric signal Y is wrong").
```

User feedback loop:
- "ok" → Phase 6 persist
- User challenges → Claude revises → show again → until confirmed

### Phase 6: Persist

#### 6a. benchmark.md

Write to `<user-channel>/benchmark.md` in the [templates/benchmark.template.md] format:
- Account info (account name, URL, tone, follower scale — supplied by the user)
- Table of imported samples
- Base rubric derivation (qualitative only)
- Topic-direction sense

If `--append` → add new rows to the sample table in the existing benchmark.md + re-derive patterns; do not rewrite the whole file.
If `--replace` → move the existing benchmark.md to `benchmark.archived/<old-account-name>_<date>.md` and write the new one.

#### 6b. samples/<account-name>/

Create a subdirectory for each sample:
```
samples/<account-name>/<video-id>/
├── source.mp4 (Way b only; Way a has none)
├── transcript.md (written from pasted text / whisper output)
└── meta.md (title / data / impression / impression reason)
```

#### 6c. script_patterns.md

Add a new section to `<user-channel>/script_patterns.md`:

```markdown
## Borrowed from benchmark [account-name] (imported on YYYY-MM-DD, N samples)

> These patterns come from a benchmark account — **Imported, untested on my channel**.
> After live-shoot validation (≥2 runs + retro confirmation), remove this marker and promote them to formal patterns.

### Pattern A: [one-sentence name]
**From**: [sample X]
**Description**: [detail]

### Pattern B: ...
```

#### 6d. rubric_notes.md

Add / update the "benchmark-derived initial signals" section in `<user-channel>/rubric_notes.md`:

```markdown
## Benchmark-derived initial signals

> From benchmark account [account-name] in benchmark.md (N=N samples, imported on YYYY-MM-DD).
> **Qualitative direction only; not adopted as numeric weights directly** — fitting on 5-10 samples overfits easily.
> When you have N≥5 calibration samples of your own and do a formal bump, **decide then** whether to adjust weights.

- Dimensions that look important: ER / QL / ...
- Dimensions that look insignificant: SR / NA / ...
- Claude's initial suggestion: [one-sentence qualitative note]
```

### Phase 7: Update the state file

```json
{
  "benchmark_status": "imported",
  "benchmark_name": "<account-name>",
  "benchmark_sample_count": <N>
}
```

## Key Rules

1. **Way a is the default** — simple + accurate. Way b is only the fallback for "no script, video only"
2. **Impressions are mandatory** — breaking down patterns from the transcript alone tends to catch only the surface; adding the user's impression reaches the deeper layer
3. **Rubric signals are qualitative only** — no numeric weights directly. Fitting on 5-10 samples overfits
4. **Patterns are marked untested by default** — avoid contaminating the user's own pattern library
5. **Do not download videos yourself** — downloading is the user's job, avoiding TOS and anti-scraping issues
6. **Re-runnable** — `--append` adds new videos, `--replace` swaps accounts
7. **MIN_SAMPLES = 3**: fewer than 3 yields no patterns; refuse to continue

## Refusals

- "Skip the impression judgment, just break it down" → refuse. The impression is a key input
- "I can only give 1 sample" → refuse. At least 3
- "Just give me numeric weights" → refuse. Phase 4 produces qualitative signals only
- "Can we skip writing transcript files and just analyze in memory?" → no. Persisting transcripts is the basis for the later cheat-retro Phase 4b diff
- "Download the benchmark videos for me" → refuse. Guide the user to download them themselves with yt-dlp / BBDown or similar

## Integration

- Upstream: `/cheat-init` Phase 2.5 **strongly recommends** running `/cheat-learn-from` for cold-start users; **optional** for calibrated users
- Upstream: `/cheat-status` keeps reminding when `benchmark_status=pending` + >24h since init
- Downstream: `/cheat-seed` reads benchmark.md when brainstorming → knows the user's benchmark direction
- Downstream: `script_patterns.md` gains a new section; cheat-seed picks structures from those patterns when writing drafts
- Downstream: `rubric_notes.md` gains the benchmark-derived signals section, used as one reference at cheat-bump time
- N≥10 hint: when the user's calibration_samples ≥10, `cheat-status` says "you have enough of your own data; the benchmark's influence is fading (kept as a sanity check)"

## When the benchmark fades out

It is not a rigid sample count; it is **Claude judging whether the user's data signal has overtaken the benchmark**:

- **Default reference**: calibration_samples ≥ 10 → benchmark influence fades
- **May be earlier**: N=5 but the user's (score, actual performance) pairs include ≥3 that diverge from the benchmark patterns — meaning your account has already left the benchmark's path
- **May be later**: N=15 but the user's samples are all similar (all the same kind of content), so the benchmark still has signal value

Judgment conditions + defaults are implemented in cheat-status trigger #19 / cheat-seed Phase 0.

**After fade-out**:
- cheat-seed brainstorming still reads benchmark.md, but **at lower priority than the user's own predictions/**
- The benchmark signals section in rubric_notes is marked `**Status: superseded by user data**`; kept but no longer dominant
- benchmark.md is **not deleted** — kept as a sanity check (to see whether your account has really drifted too far from the benchmark's direction)

**At any time, on user request**: run `/cheat-learn-from --replace none` to fully remove the benchmark's influence

## Difference from other skills

| Skill | Purpose |
|---|---|
| `/cheat-learn-from` | Import patterns / rubric signals **from a benchmark account** (one-time / occasional appends) |
| `/cheat-seed` | Brainstorm topics + write drafts (reads benchmark.md as reference) |
| `/cheat-trends` | Fetch today's trends (unrelated to the benchmark) |
| `/cheat-bump` | Upgrade the rubric (after the user has N≥5 of their own samples, using real data; benchmark signals are not used directly) |
