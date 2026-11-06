# Adapter: whisper (video/audio transcription)

Invoked by `/cheat-learn-from` in Way b (the user provides video files and lets the tool transcribe).

> **Prefer Way a** (the user pastes script text directly — simple + accurate). Way b (whisper) is only for when the user **cannot find the script and has only the video**.

---

## What this adapter does

Turns media files such as mp4 / mov / mp3 into a text transcript, so Claude can read a benchmark account's scripts.

Most Douyin / Bilibili / YouTube videos **have no official subtitles** — getting the script is impossible without ASR (speech transcription). That is why this adapter exists.

---

## Installation (one-time)

### Option A: whisper-cpp (**recommended** — fast, light, pure C++)

On Mac M-series chips, a 3-minute video transcribes in 30-60 seconds.

```bash
# 1. Install whisper-cpp
brew install whisper-cpp

# 2. Install ffmpeg (a whisper-cpp dependency; extracts audio from video)
brew install ffmpeg

# 3. Download a model (for Chinese, medium or large-v3 is recommended — accurate enough + reasonably fast)
# whisper-cpp downloads automatically on first run, or manually:
mkdir -p ~/.whisper-cpp/models
cd ~/.whisper-cpp/models
# medium model (~1.5GB)
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
```

### Option B: openai-whisper (Python version; slower but has API compatibility)

```bash
pip install openai-whisper
brew install ffmpeg

# models download automatically
```

### Option C: use a cloud API (no local model needed)

`/cheat-learn-from` does not yet support cloud APIs directly — if you have an OpenAI / Azure / Alibaba Cloud ASR API key, you can edit `run.sh` yourself to use the cloud.

---

## Usage

cheat-learn-from calls it automatically; you do not need to run it by hand. But if you want to test manually:

```bash
# Transcribe a single video
bash run.sh <video_path> <output_dir>

# Example:
bash run.sh ~/Desktop/benchmark-account/some-video.mp4 ~/my-channel/samples/benchmark-account/abc123/
# → outputs ~/my-channel/samples/benchmark-account/abc123/transcript.md
```

## Output format

`transcript.md`:

```markdown
# Transcript: <video filename>

**Source**: <video file path>
**Transcribed at**: <ISO timestamp>
**Engine**: whisper-cpp medium / openai-whisper large / etc.
**Duration**: <video length>

---

[plain-text transcript, split into paragraphs (not subtitle format)]
```

> Note: whisper's subtitle output breaks lines by **sentence** (one line per sentence + a timestamp).
> run.sh strips the timestamps + merges short sentences into paragraphs, so Claude reads it like a script rather than a subtitle sheet.

## Failure modes

| Symptom | Cause | Handling |
|---|---|---|
| `whisper-cpp: command not found` | Not installed | Run `brew install whisper-cpp` |
| `ffmpeg: command not found` | ffmpeg not installed | Run `brew install ffmpeg` |
| Garbled transcript / many typos | The video is in English but a Chinese model was used, or vice versa | Change the `--language` argument in `run.sh` |
| Transcription is slow (>10 minutes) | Using the large model + no GPU/M-chip acceleration | Switch to the medium model |
| Disk full | Large model files (large-v3 ~3GB) | medium (~1.5GB) is enough |

## Stability level

★★★★ — whisper is the open-source standard for ASR and will not suddenly break. You can update models freely, and pinning a version is safe.

## Risk notes

- **TOS**: transcribing **benchmark videos you downloaded yourself** for personal study and reference is fair use; **do not** republish the transcripts
- **Privacy**: whisper runs entirely locally and sends no data to the cloud

## File list

```
adapters/script-extraction/whisper/
├── README.md           # this file
└── run.sh              # wrapper invoked by cheat-learn-from
```

## Relationship to the other adapters

- Like `adapters/perf-data/douyin-session/` and `adapters/trend-sources/*`, it is an optional cheat-on-content adapter
- Only invoked by `/cheat-learn-from --way b` — Way a (paste text) does not need it

## Notes on downloading videos yourself

The tool **does not scrape videos directly** — avoiding TOS risk + anti-scraping maintenance cost. Suggestions:

- **Douyin**: a third-party downloader / Douyin PC app → copy the video link → paste into the downloader
- **Bilibili**: [BBDown](https://github.com/nilaoda/BBDown) / [you-get](https://github.com/soimort/you-get)
- **YouTube**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (the most powerful)
- **Xiaohongshu**: [xhs-downloader](https://github.com/JoeanAmier/XHS-Downloader)

Once downloaded, drop them at `samples/<benchmark-name>/<video-id>/source.mp4` — cheat-learn-from will find them automatically.
