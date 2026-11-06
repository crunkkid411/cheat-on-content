# Retrospective section template

> **This template is appended automatically by `/cheat-retro` into the `## Retrospective` section of the matching prediction file.**
> It is not a standalone file — it is only the format reference for the lower half of a prediction file.
>
> Example data comes from the video-analysis project's "Stop expecting" retrospective (the retrospective section of [predictions/2026-04-24_ab61ed09_stop-expecting.md]).
>
> Full spec: the "retrospective section" part of [shared-references/prediction-anatomy.md](../cheat-on-content/shared-references/prediction-anatomy.md).

---

## Retrospective

**Retro at**: `<YYYY-MM-DD>` (publish T+`<N>`d)
**Fetched at**: `<YYYY-MM-DD HH:MM>`
**Data source**: `manual paste` / `adapter:<platform>`

### Actual performance

- Plays: **`<X>`w** (landed in the \``<bucket>`\` bucket [high / low / center], **`<+X% / -X%>`** vs the `<X>`w center)
- Likes: `<X>`w (like/play ratio `<X.XX%>`)
- Comments: `<N>` (comment/play ratio `<X.XXX%>`)
- Saves: `<N>`
- Shares: **`<X>`w** (share/play ratio **`<X.XX%>`**, [strong / medium / weak])

> **Example** (Stop expecting, T+7d):
> - Plays: **711k** (landed in the `30-100w` bucket on the high side, **+42%** vs the 500k center)
> - Likes: 24k (like/play ratio 3.38%)
> - Comments: 899 (comment/play ratio 0.126%, **highest among videos from the same period**)
> - Saves: 5,251
> - Shares: **18k** (share/play ratio **2.53%**, strong)

> **Key derived ratios must be computed**: like/play, comment/play, share/play — they expose signals that raw play count cannot.
> For example, the video-analysis project found that "share/play ratio" is the strongest external proxy for the TS (issue-share impulse) dimension: job-hunting 0.96% vs Stop expecting 2.53% — same composite but a 2.6x difference in share/play ratio.

### Top comment keywords

> Split the N pasted comments into 3-5 categories (high-like meme / concept reference / off-topic noise / repost-exposure hint / @friend propagation, etc.),
> and list representative comments + like counts + proportions for each.

- **"[key meme / sentence pattern]"**: [like count] alone at the top / appears N times in variants ([short description of the pattern])
- **"[secondary meme]"**: [like count] [secondary pattern description]
- **Withdrawal / resonance / parody category**: [like count] [representative comment]
- **Extended references**: [other derivative patterns]
- **@friend propagation / self-deprecating complicity**: [whether the comments are doing this]

> **Example**:
> - **"She's different" / "He's different" meme explosion**: 2,266 likes alone at the top, and appears at least 12 times across the text (193, 5, 5, 5, 3, 4, 4, 2, 2, 2, 2, 1... repeated variants), with the audience **actively reusing the pattern to mock themselves** — this is a critical-tier meme
> - **"Joker / simp" secondary meme**: 412 likes "Schrödinger's Joker/Crush superposition", 74 likes "I want to spin in circles myself"
> - **Withdrawal methods seriously translated**: 27 likes "1. Think less 2. Don't believe in the good 3. Rebuild the filter" — the audience actively RTFs
> - **@friend propagation**: a large number of @ chains — the comment section is a social venue; the audience uses the video as a tool to "roast friends / self-deprecate in complicity"

### Which predictions were validated ✅ / refuted ❌

**Validated ✅**:
- [whether the critical calibration hypothesis held] [comparison with specific numbers]
- [which reasoning factors were validated]
- [which bucket in the counterfactual scenarios was hit]

**Refuted ❌**:
- [state it explicitly if the center was off by more than ±25%]
- [whether the Y in "if X means Y" actually happened]
- [items in the reasoning-factor table whose "high confidence" was refuted → rubric bug signal]

> **Example**:
> **Validated ✅**:
> - The critical calibration hypothesis **held completely**: this piece 711k / Who asked you 117k = **6.07x**, far above my 1.5-2x bet
> - ER=5 drove emotional spread → **strong evidence for H1**
> - HP=5 validated: share/play ratio 2.53%; the quotable line "intermittent hope" was quoted frequently
>
> **Refuted ❌**:
> - The 500k center was exceeded by +42%: I underestimated the viral-tier remixing of the "she's different" meme
> - The counterfactual reasoning "must be paired with a strong social issue to break 300k" was **completely wrong** — SR=2 broke 700k easily
> - My bet on SR ("H2: SR should be raised") was **refuted in the opposite direction**: SR contributes **almost nothing** in emotionally driven scenarios

> **Key discipline**: every validation / refutation must cite specific data ("share/play ratio 2.53%"); vague phrasing such as "basically consistent" is not allowed.

### New observations to write into rubric-memo.md

1. **[One-line rule title]**: [specific evidence, citing specific data points]
2. **[Second rule]**: [same as above]
3. **[Candidate dimension naming suggestion]**: [if a dimension the rubric does not capture is observed, propose a candidate dimension name + draft scoring definition]

> **Example**:
> 1. **The true weight of ER in emotionally driven scenarios should be ≥ ×2.0**: the 6x traffic ratio vs Who asked you is the strongest counterfactual evidence for the v2 rubric
> 2. **Issue-share impulse (TS) is a hidden dimension**: Joker / "she's different" / filter rebuilding provided a **safe self-deprecating identity** where reposting does not expose one's situation; a TS=5 sample
> 3. **HP × ER resonance effect**: ER=5 + HP=5 + a reusable meme sentence = viral tier; missing any one breaks it
> 4. **"Remixable sentence pattern" candidate dimension (Memetic Shareability, MS)**: can the audience form sentences with the author's pattern? Stop expecting = Y (endless "she's different" variants), Who asked you = N (only demand for information, quotable but not remixable)

> Every observation must be traceable to specific data points (do not write "emotion matters" — write "ER5/SR2 vs ER3/SR4 at the same composite differ 6x in traffic").
> These observations are written by `/cheat-retro` into the "Observation log" section of `rubric-memo.md`. `rubric_notes.md` is the blind whitelist and may only receive abstracted generic rules during a later `/cheat-bump`; sample names, actual performance, comments, or links must never be written into it.

### Bump trigger evaluation

- Miss direction: [high / low / on-target]
- Cumulative same-direction misses: [N times (including this one)]
- Does it trigger a bump proposal: [yes / no]

> If the cumulative same-direction misses are ≥3, `/cheat-retro` outputs a "consider running /cheat-bump" reminder at the end.
> The actual bump is done through `/cheat-bump`; this section only records the trigger.
