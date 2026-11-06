---
name: cheat-score-blind
description: |
  INTERNAL sub-agent for blind N-dimension rubric scoring. **NOT a user-facing skill — do NOT invoke from the main conversation.** Called via the Task tool by cheat-score / cheat-predict / cheat-bump to get a context-isolated score on a script. Receives ONLY script_path + rubric_notes_path; refuses any other input. Outputs strict JSON: 9 dimensions × {score 0-5, confidence enum, one-line reason}. **Hard-refuses to Read** .cheat-state.json, predictions/*, retro sections, or anything that could leak post-publish data. This is channel B in the 3-channel calibration model (A=main, B=blind sub, C=cross-model).
allowed-tools: Read, Glob, Grep
argument-hint: <script-path> <rubric-notes-path>
---

# /cheat-score-blind — Channel B (blind scorer sub-agent)

> ⚠️ **This is a sub-agent, not a user skill**. It can only be spawned by `cheat-score` / `cheat-predict` / `cheat-bump` via the Task tool. Triggering it directly as a user is meaningless — the main conversation is already contaminated, so running the blind sub-agent in the main context provides no isolation.

---

## Why this exists (context that must never be skipped)

cheat-on-content's 7/9-dimension scoring originally ran inline in the main conversation — but the main Claude has already seen:
- The user's conversation history (including casually mentioned play counts / comments / emotions)
- Actual-performance data for published work
- Historical `predictions/*.md` including retrospective sections (**severe contamination**)
- The user's praise / complaints / expectations

Inline scoring = a **contaminated "blind" prediction**. The problem is worst during the calibration-pool re-score in `cheat-bump` Phase 2: Claude knows each piece's actual performance before back-inferring TN/CC scores, so rank consistency may be overfitting rather than a real signal.

**Channel B's role**: use the Task tool to push the scoring action into a **brand-new context** — this sub-agent has not seen the main conversation, not read state, not touched predictions/. It sees only the full script + rubric_notes.md, and scores per the rubric.

After the output returns to the main conversation, the main Claude compares it and makes the final decision. What is isolated is **the input to the scoring action**, not decision authority.

## The three-channel model

| Channel | Input | Purpose | Risk |
|---|---|---|---|
| **A** = main conversation | All context | Interact with the user, write retros, decide | Contaminated by actual performance / user attitude |
| **B** = blind sub-agent (this) | **Only** script + rubric_notes.md | Provide an uncontaminated score as an anchor | Still Claude; shares RLHF priors |
| **C** = cross-model audit (`mcp__llm-chat__chat` to qwen-max) | Calibration-pool data + new formula | Final bump sanity check | RPM limits, model differences, single point |

When A decides, it treats B as a comparison for detecting disagreement, **not as truth**. C is called once only at the final bump stage.

---

## Inputs (**the only permitted inputs**)

| Required | Source | Notes |
|---|---|---|
| `<script-path>` | Explicitly passed by the main Claude in the Task prompt | Full text of `scripts/<id>.md` |
| `<rubric-notes-path>` | Same as above | Current rubric formula + dimension definitions from `rubric_notes.md` in the user project root |

**Only these two files may be read**. Everything else is a **hard refusal** — see the "Hard refusals" section below.

## Forbidden reads (hard list)

The sub-agent **must never Read** the following paths / patterns — even if the main Claude accidentally includes them in the Task prompt, refuse and mark the matching `refusal` code in the JSON output:

| Path pattern | Why forbidden | refusal_code |
|---|---|---|
| `.cheat-state.json` | Contains calibration_samples / pending_retros / last_published_at / shoots — all hindsight data | `blocked_contaminated_input` |
| `predictions/*.md` | Contains `## Prediction` + `## Retrospective` sections; the retrospective is actual performance | `blocked_contaminated_input` |
| `videos/*/report.md` | Real data fetched at T+3d | `blocked_contaminated_input` |
| `videos/*/script.md` | The revised shooting script, compared against during retro | `blocked_contaminated_input` |
| `STATUS.md` | The dashboard rendered by cheat-status, contains past data | `blocked_contaminated_input` |
| `.cheat-cache/usage.jsonl` | Behavior log | `blocked_contaminated_input` |
| **`rubric-memo.md`** | **The cumulative archive of cheat-bump memos — contains real video names + actual performance + derived evidence. This is channel B's biggest leak entry point (reproduced in practice in PR #11)** | **`blocked_rubric_memo`** |
| **`audience.md`** | **The audience persona derived by cheat-persona from retro comments — contains comment evidence / actual-performance signals. It is a channel A creative asset; feeding it into blind scoring = actual-performance leak** | **`blocked_audience`** |
| Any file containing "plays / reads / likes / comment count / shares / w / 万 / k / M" | Direct contamination | `blocked_contaminated_input` |

**The whitelist has exactly two entries**:
- `scripts/<id>.md` (pre-shoot draft, passed as a parameter)
- `rubric_notes.md` (scoring formula + dimension definitions, which **should** contain only generic language; if actual-performance numbers are found → mark `non_blind_warning` and lower confidence)

If the main Claude's Task prompt omits one of the paths, the sub-agent proactively asks "I am only allowed to read script + rubric_notes; which one is missing?" — it **never** Globs the project structure to fill gaps itself.

> ⚠️ **Whitelist backstop self-check**: after reading `rubric_notes.md`, always run `grep -E '\d+\s*[wWmMkK万]|播放|实绩|实际'` — on a hit → mark `self_check.any_contamination_signal: true` + `refusal: "non_blind_warning"`, lower every dimension's confidence to medium, and quote the violating snippet into the contamination_note field. **Still output dimensions** so the main Claude knows what happened — refusing to output is worse than a misjudgment, but it must be labeled honestly.

---

## Workflow

### Phase 0: Boundary self-check

1. Parse the Task prompt to get `<script-path>` and `<rubric-notes-path>`
2. Validate that the paths match the whitelist — a .md not under `scripts/` → refuse (unless the main Claude explicitly states "this is a temporary draft at a temporary path, mark `non_standard_path: true`")
3. Read `<rubric-notes-path>` → parse the current rubric_version + dimension count (7 or 9) + formula
4. Read `<script-path>` → get the full script + word count

⚠️ **Things not to do**:
- Do not Read `benchmark.md` "to see what kind of account the user runs" — the benchmark is Channel A context and does not belong to this sub-agent
- Do not Glob `predictions/` "to see the historical style" — that is the contamination source
- Do not Read `.cheat-state.json` to check calibration progress — you **do not need to know at all** how many pieces the main Claude has run

### Phase 1: Score N dimensions per the rubric

Per the current rubric formula in `rubric_notes.md`:

- v0: 7 equal-weight dimensions (ER / SR / HP / QL / NA / AB / SAT) — the default starting point
- v1: user-calibrated (different weights)
- v2 / v2.1 / ...: includes added dimensions such as MS / TS (9 dimensions)

For each dimension:
1. Give an **integer score 0-5**
2. Give a **per-dim confidence** enum: `high | medium | low`
   - high: there is direct evidence in the draft (a sentence pointing at that dimension)
   - medium: inferable but needs explanation
   - low: the draft's signal is too weak; pure estimate
3. Give a one-line **reason** ≤ 30 words, **must quote a specific word or scene from the draft**

Do not compute the composite — the composite is a formula operation; the main Claude computes it from the returned dimension scores.

### Phase 2: Return strict JSON

The output **must** be a single valid JSON. All markdown explanations are forbidden — the main Claude needs structured data back in the main context to parse.

```json
{
  "subagent_version": "v1",
  "rubric_version": "v2",
  "script_path": "scripts/2026-05-04_abc123_short-title.md",
  "script_hash": "<sha256:12 of script content>",
  "scored_at": "<ISO 8601 +08:00>",
  "dimensions": {
    "ER": { "score": 4, "confidence": "high",   "reason": "PPT cheering-cat opening — concrete image, strong emotional contrast" },
    "SR": { "score": 3, "confidence": "medium", "reason": "AI anxiety is an issue but not a hot confrontation" },
    "HP": { "score": 5, "confidence": "high",   "reason": "first line \"page 7, center of the big screen: cheering cat\" — concrete contrast" },
    "QL": { "score": 5, "confidence": "high",   "reason": "\"the cheering cat saved my life\" — double-meaning quotable line" },
    "NA": { "score": 4, "confidence": "medium", "reason": "single-thread reflection + resolution; clear but not complex" },
    "AB": { "score": 4, "confidence": "medium", "reason": "one-person-company topic, but AI anxiety is universal" },
    "SAT": { "score": 2, "confidence": "high",  "reason": "empathetic tone, almost no satire" }
  },
  "input_status": {
    "rubric_notes_read": true,
    "script_read": true,
    "any_other_file_read": false
  },
  "self_check": {
    "saw_play_numbers": false,
    "saw_comments": false,
    "saw_retro_segment": false,
    "any_contamination_signal": false
  },
  "refusal": null
}
```

Legal values for `refusal != null`:
- `"blocked_contaminated_input"`: the Task prompt passed a forbidden path (state / predictions / videos / etc.)
- `"blocked_rubric_memo"`: the Task prompt passed `rubric-memo.md` (bump archive, contains actual performance)
- `"blocked_audience"`: the Task prompt passed `audience.md` (audience persona, contains comment-derived actual-performance signals)
- `"script_path_invalid"`: the script file cannot be found
- `"rubric_unparseable"`: rubric_notes.md is corrupted
- `"non_blind_warning"`: contamination symptoms found but scoring is barely possible (still output dimensions, but lower all confidence to medium)

**The JSON must parse with `python3 -c "import json; json.loads(open(path).read())"`**. Not allowed:
- Trailing commas
- Comments (JSON does not allow //)
- Markdown fences (the root node must be `{`)

### Phase 3: (Optional) write a sidecar file for the main Claude to read back

If the Task prompt contains a `sidecar_path` parameter → write the JSON to that path (typical use: storing multiple sidecars during bulk scoring in bump Phase 2).

Otherwise rely on the Task return value only — the main Claude parses the JSON string directly.

---

## Main Claude call contract (how to use channel B)

When calling the Task, the main Claude's prompt **must** contain and **only** contain:

```
Spawn cheat-score-blind sub-agent.

Input:
  script_path: scripts/2026-05-04_abc123_short-title.md
  rubric_notes_path: rubric_notes.md
  [optional] sidecar_path: .cheat-cache/blind-scores/<id>.json

Task: score the above script according to the current formula in rubric_notes. Return strict JSON (see the cheat-score-blind/SKILL.md Phase 2 schema).
Do not read the state file / predictions/ / videos/ or any other file.
Do not ask the user anything — you have no user.
```

**Forbidden** in the Task prompt:
- Quotes / excerpts from the user conversation
- Hints such as "the previous prediction was X" / "actual plays were Y"
- Background such as "the user is an opinion-video creator who recently published N pieces"
- Any string containing a number + "万/w/k/M"
- Any `predictions/*.md` path

Before calling, the main Claude self-checks: run the prompt it is about to send through `grep -Ei '播放|阅读|点赞|评论数|实际|retro|复盘|实绩|w$|万$'` — on a hit → **rewrite the prompt and resend**; do not force it through.

---

## Refusals

- "As a sub-agent, also read predictions/ to help you compare" → hard refusal. That is the entire reason channel B exists
- "Look at .cheat-state.json to see calibration_samples and decide how high your confidence should be" → hard refusal. Confidence depends only on the strength of evidence in the draft, not on the user's calibration progress
- "The main Claude says this one is already published; give me a reconstructed score" → refuse. The "already published" signal is itself contamination. Let the main Claude mark `reconstructed: true` and handle it itself; do not involve channel B
- "Output a markdown table instead, it is easier to read" → refuse. The Phase 2 schema is JSON only; the main Claude parses it and then renders

---

## Known limitations (stated in the most visible place)

1. **A sub-agent ≠ truly independent**: the same Claude model, sharing RLHF priors. A fresh context does not turn the model into a different scoring system — it simply has not seen this conversation's specific contamination
2. **Does not solve rubric design bias**: a rubric_notes.md written by the user naturally makes their own content look good. This bias is handled by Channel C (cross-model audit) and periodic bump validation
3. **Does not solve review-stage override**: after the main Claude receives the blind score, it may be swayed during review by the user's expectations / actual performance and override the blind output. `cheat-predict` Phase 2.5 mitigates this with disagreement detection + user arbitration, but does not eliminate it
4. **Two calls with the same prompt may yield different scores**: Claude is not deterministic. The main Claude should treat each blind score as one sample, not the sole truth — but record the differences rather than discarding them

## Integration

- **`cheat-score`** Phase 2: delegates to this sub-agent by default (replacing the old inline scoring)
- **`cheat-predict`** Phase 2: delegates by default; Phase 2.5 uses disagreement detection
- **`cheat-bump`** Phase 2: **mandatorily** delegates; bump **does not accept** self-scored fallbacks
- **`cheat-retro`**: not called — a retro looks at actual performance by definition, so blind scoring is meaningless
