<h1 align="center">
  <img src="logo.svg" alt="Cheat on Content" width="720">
</h1>

<h2 align="center">Cheat on Content</h2>

<p align="center">
  <a href="../README.md"><strong>Main README</strong></a>
  &nbsp;·&nbsp;
  <strong>Chinese edition (translated into English)</strong>
</p>

<p align="center">
  <a href="https://watcha.cn/products/cheat-on-content">
    <img src="guancha-no1.svg" alt="Watcha Hot List · #1" width="328">
  </a>
</p>

<p align="center">
<a href="../CHANGELOG.md"><img src="https://img.shields.io/badge/version-v0.1.0-orange" alt="Version"></a>
&nbsp;
<a href="../LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
</p>

<p align="center">
Influencer cheat code: turn every piece of content into a calibratable experiment.
</p>

<p align="center">
You are reading this sentence, and this skill already predicted it.<br>
It turns every creator's "I have a feeling this one will blow up" into a calibratable experiment.<br>
I used it to gain 1,000,000 followers in one month. It said I would write this, so I did.<br>
You stopped to wonder "is this true?" That was in its prediction too.
</p>

---

## 🎬 What it really does

Most creators live inside the same gamble:

> Publish → the numbers come in → learn nothing → gamble again next time

A creator who has run 200 pieces is less than 10% ahead of one who has run a single piece, because they never **kept the books** after each bet.

**The influencer cheat** records every judgment, reviews it, and absorbs it into the next one:

📊 Score → 🎯 Blind prediction → 🚀 Publish → 📈 T+3 day retro → 🧬 Evolve your scoring formula

This is not motivation, it is **compounding**. Every piece you do not review erodes your ability to "see yourself."

Run it for one month = you own **a viral formula that belongs only to you**.
Run it for three months = you are 10 times better than when you started.

---

## 🌀 Origin

> I used to completely disbelieve in fate. Then this skill had me shoot a video, and it even predicted how much traffic that video would get.
>
> I tried to disprove it through collective observation. I told my audience about it, hoping a quantum collapse would change the trajectory.
>
> The numbers were accurate.
>
> I did not escape fate. I only jumped from the first order to the second.
>
> If even my awakening and my audience's observation were part of its presets,
> then as you read this right now: is it out of curiosity, or are you completing the algorithm's final placement?
>
> — The creator

---

## ⚖️ How it differs from other "creator tools"

| Others | This one |
|---|---|
| Give you "inspiration" | **Quantify your own inspiration** |
| AI writes for you | AI **judges** for you; the script stays yours |
| Post 10 versions at once to A/B test | Each post is a **bet**: write the judgment down, then reconcile it against the data |
| Static data dashboards | **A scoring formula that evolves**: three months from now your rubric is no longer the starting version |

In one line: other tools help you "produce more"; this one helps you "judge more accurately."

---

## 🤔 Can't ChatGPT / Doubao / DeepSeek do this too?

Those are **general assistants** that say the same thing to everyone. Ask "will this one blow up?" and the answer is fitted to the average experience of the whole internet. It has nothing to do with your account. Ask again tomorrow and you get the same answer, because **it doesn't remember you, and it certainly doesn't change because of you**.

This is **your own operations expert**, serving only your one account:

- The scoring formula is derived backward from **your** historical data, not a generic training distribution
- It updates its understanding of your account with every post; after three months its judgment is 10 times more accurate than at the start (**automatic evolution**)
- It knows your benchmark accounts, your publishing cadence, and why your last three posts flopped. ChatGPT forgets all that after its first sentence

General LLMs help everyone; this helps **your** account.

---

## 🛡️ How it makes the loop truly evolve

📝 **Every piece leaves a record**: score and write the prediction before publishing, all archived. Come back three days later and reconcile: where you were right and where you were off is **clear at a glance**, not a vague "I feel this one didn't do well."

🔁 **It gets more accurate with use**: after three consecutive deviations in the same direction, the tool automatically urges you to upgrade your scoring formula. **It nags even if you don't take the initiative.**

🛡️ **Upgrades have brakes**: a new formula must re-judge all historical samples and beat the old formula before it is allowed through, and it also needs an independent cross-model review, **so you can't fool yourself**.

🪒 **The rubric is a workbench, not a museum**: observations that get overturned are deleted, and so are those that get absorbed. It only ever holds what is most useful right now.

---

## 📦 Install

```bash
git clone https://github.com/XBuilderLAB/cheat-on-content.git
cd cheat-on-content
bash install.sh
```

> ⚠️ **Upgrading from v0.x?** After `git pull`, run `/cheat-migrate` in your content project. **1.3 → 1.4 is a BREAKING blind-channel integrity fix**: it splits `rubric_notes.md` so the blind sub-agent can't read actual results through the whitelist. If you skip the migration, blind scoring will keep flagging `non_blind_warning`. See the [CHANGELOG](../CHANGELOG.md) and [migrations/1.3-to-1.4.md](../migrations/1.3-to-1.4.md).

14 sub-skills are symlinked into your agent's skill directory. Install once and every content project can use them.

**Supported agents**: Claude Code (default) · Codex (`bash install.sh --codex`) · both (`bash install.sh --all`)

> Frozen version: `bash install.sh --copy` / `bash install.sh --codex --copy`
>
> Uninstall: `bash uninstall.sh` / `bash uninstall.sh --codex` (does not touch your content data)

---

## 🚀 First run

In your content project directory, open a skill-compatible agent and say:

```
initialize cheat-on-content
```

Five yes/no questions finish onboarding. **Importing a benchmark account is strongly recommended**: 5-10 samples give the tool an anchor right away. Otherwise your first 5 predictions are only accurate to ±50%.

---

## ⚡ Daily use

```
score this scripts/<...>.md            → score it
start prediction scripts/<...>.md      → blind prediction + decision log
shot scripts/<...>.md                  → create the video folder + buffer +1
shipped https://...                    → buffer -1
retro videos/<...>/                    → T+3d data collection + retro
status / fetch trends / find topics / bump rubric / find benchmark
```

Agents that support hooks automatically report buffer + pending retros + top candidates at the start of each session, so you don't have to ask. On other agents, just say `status`.

For the full workflow and sub-skill details, see [SKILL.md](../SKILL.md).

---

## 📈 Star History

<a href="https://star-history.com/#XBuilderLAB/cheat-on-content&Date">
  <img src="star-history.svg" alt="Star History Chart" width="720">
</a>

---

## 📜 License

MIT. Commercial use, modification, and closed-source integration are all fine.

---

*Is this cheating? So is a calculator. So is Google.*
*The future never rewards effort. It only rewards whoever sees the pattern first.*

*You read this line, and that was predicted too.*
