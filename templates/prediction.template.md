# [Title of the piece] — Prediction log

> **This template is filled in automatically by `/cheat-predict`.**
> Every prediction uses the same format (7 components + a retrospective section) — the first 5 pieces and the mature stage are identical; the only difference is the confidence level in the header.
>
> Full spec: [shared-references/prediction-anatomy.md](../cheat-on-content/shared-references/prediction-anatomy.md).
>
> The example data in this template comes from the video-analysis project's "Stop expecting" ([predictions/2026-04-24_ab61ed09_stop-expecting.md]).

---

**Article ID**: `<12-char hash>`  ← e.g. ab61ed09f0a1 (sha256 of the first persisted content of `scripts/<id>.md`, first 12 chars)
**Title**: `<full title>`
**Rubric Version**: **`<v0/v1/v2/...>`**
**Predicted at**: `<YYYY-MM-DD>` (based on the final draft)
**Script Path**: `scripts/<YYYY-MM-DD>_<id>_<short>.md`
**Script Hash**: `sha256:<12 chars>` (hash the script content at predict time; cheat-shoot hashes it again and adds an integrity warning to the retrospective if it differs)
**Target Duration (s)**: `<state.typical_duration_seconds>`  ← e.g. 240 (3-5min)
**Actual Script Length**: `<actual word count of script.md>`  ← e.g. 980 words
**Calibration Samples (at predict time)**: `<state.calibration_samples>`  ← e.g. 3
**Confidence**: `<emoji + label>`  ← e.g. 🟡 Low-ish (center ±40%, usable as one reference). Derived from calibration_samples; see state-management.md
**Scored By**: `claude` | `claude+user_override`  ← Claude scored it itself; if the user challenged and changed fields during review, mark `+user_override`
**User Override**: `<if overridden, list which fields changed + old and new values>` | `none`
  ← e.g. `AB: claude=4 → user=3 (user thinks 'the one-person-company topic is less universal')` `Center: claude=60w → user=40w`
  ← During retro this field helps diagnose: on which dimension does the user's intuition systematically diverge from Claude's, and when actual performance validates it → the rubric may be missing something
**Data status at prediction time**: **blind** (no actual `<platform>` play data seen)
**Prediction Basis**: `pre_shoot`  ← or `post_shoot_pre_publish` (v2 section)
**BlindScored By**: `subagent-v1`  ← or `main-claude-self` / `mixed`
**BlindScore Disagreement**: `<inline JSON — one row per dimension, see prediction-anatomy.md>`

---

## Input snapshot

**Scores (vN)**: `<dim1=X / dim2=X / ...>` → composite=**`<X.XX>`**

> Example: ER5 / HP5 / QL5 / NA3 / AB5 / SR2 / SAT4 → composite=**8.24**

**User revision highlights vs Claude draft** (if any):
- **Opening**: [what the user cut / added]
- **Cut**: [specific paragraph / concept name / setup]
- **Kept**: [key quotable line / acknowledgment paragraph / main structure]
- **Pacing**: [tighter / looser] than the draft by about N%

> If the user wrote it from scratch without cheat-seed, write "original user draft, no Claude draft to compare against".

---

## Prediction v1

> ⚠️ **This section is immutable** — `hooks/prediction-immutability.sh` intercepts Edit calls that touch it.
> Once written it cannot be changed. To redo it, create `<this-filename>_redo.md` and keep the original.

**Bucket**: `<X-Yw>`  ← e.g. `30-100w`

**Internal probability distribution**:
- `<5w` → X%
- `5-30w` → X%
- **`<headline bucket>` → X%** (center ~Xw)
- `>100w` → X%
- `>150w` → X%

> Must sum to 100%.
> When confidence is low (few calibration_samples) it **should be flatter** (e.g. 30/30/20/15/5), not sharper (e.g. 5/40/45/8/2) — honestly reflect the uncertainty.

**One-line reason**:
> [core driver + strongest counterexample constraint + center prediction]

---

## Reasoning factors

| Factor | Direction | Confidence | Explanation |
|---|---|---|---|
| `<dim or feature>` | strong + / medium + / weak ? / strong - | high / medium / low | [≤30 words of reasoning] |

> Three confidence levels: high (strong evidence + multiple anchors), medium (reasoned but few samples), low (intuition). During retro, if a "low-confidence" factor is validated → intuition is strong; if a "high-confidence" factor is refuted → the rubric has a bug.

---

## Anchor comparison

| Comparison sample | composite | Actual | Similarities / differences |
|---|---|---|---|
| `<sample name>` | `<X.XX>` | `<Yw>` | [key differing dimensions] |

> **When the calibration pool is insufficient** (< 2 samples within composite ±0.5):
> write "the calibration pool has only N samples, with no composite neighbors. **Anchor comparison N/A** — note that this prediction's confidence is 🟡 Low-ish / 🔴 Very low; the bucket center is for reference only."
> **Do not simply delete this section** — telling the reader why anchors are missing is more honest than silently skipping it.

---

## Counterfactual scenarios (for the retro)

**If it blows up to `>X w`** (X% expected):
- [which hypothesis is validated]
- [which hypothesis is refuted]
- [which new rubric dimension might be added]

**If it lands in `headline bucket`** (X% expected):
- [what the baseline validates]

**If it drops to `<X w`** (X% expected):
- [which core judgment is refuted]

**If `<<X w`** (X% expected):
- [possible explanation for the extreme scenario]

> Which bucket it actually lands in → tells you which rubric hypothesis was tested. **Cannot be omitted**.

---

## Critical calibration hypothesis

[Treat this prediction as an experiment; explicitly write "if X happens, it proves Y"]

[Find a comparison sample (preferably the previous prediction)]

Both pieces [same composite / neighboring composite], differences:
- This piece: [key dimension comparison]
- Comparison: [key dimension comparison]

**My bet**: [this piece vs comparison = X times / higher by N w]

If the opposite happens → [which rubric hypothesis is refuted]
If the gap is < N → [the rubric is basically OK / within noise]

> **When the calibration pool has only 0-1 pieces**: write "no comparable samples — but I will still write down my core bet for this one (even without an anchor):" then write 1-2 things you want to test this time.

---

## Retrospective

> ⚠️ **The section below is appended by `/cheat-retro` at T+`RETRO_WINDOW_DAYS` days.**
> The hook allows appending to this section; it does not allow changing a single character of the prediction section.

(To be filled — run `/cheat-retro <matching video folder>` after RETRO_WINDOW_DAYS days)
