"""Render the fetched Bilibili data into NotebookLM-friendly Markdown (same format as douyin-session)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path


def _fmt_time(ts: int) -> str:
    if not ts:
        return "unknown"
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _fmt_num(n: int | None) -> str:
    if n is None:
        return "-"
    if n >= 10000:
        return f"{n / 1000:.1f}k"
    return str(n)


def _fmt_duration(s: int) -> str:
    if not s:
        return "-"
    return f"{s // 60}:{s % 60:02d}" if s >= 60 else f"{s}s"


def _ratio(num: int | None, den: int | None) -> str:
    if not num or not den:
        return "-"
    return f"{num / den * 100:.2f}%"


def render_report(video: dict, script: str, comments: list[dict]) -> str:
    lines: list[str] = []
    title = video.get("title") or "(untitled)"
    bvid = video["bvid"]
    play = video.get("play_count") or 0

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- BV number: `{bvid}`")
    lines.append(f"- Uploader: {video.get('owner') or '-'}")
    lines.append(f"- Published at: {_fmt_time(video.get('pubdate', 0))}")
    lines.append(f"- Duration: {_fmt_duration(video.get('duration_s', 0))}")
    lines.append(f"- Link: https://www.bilibili.com/video/{bvid}")
    lines.append(f"- Fetched at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("## Play data")
    lines.append("")
    lines.append(f"- Plays: {_fmt_num(play)}")
    lines.append(f"- Likes: {_fmt_num(video.get('like_count'))} (like-to-play {_ratio(video.get('like_count'), play)})")
    lines.append(f"- Coins: {_fmt_num(video.get('coin_count'))} (coin rate {_ratio(video.get('coin_count'), play)})")
    lines.append(f"- Saves: {_fmt_num(video.get('favorite_count'))} (save rate {_ratio(video.get('favorite_count'), play)})")
    lines.append(f"- Shares: {_fmt_num(video.get('share_count'))} (share-to-play {_ratio(video.get('share_count'), play)})")
    lines.append(f"- Comments: {_fmt_num(video.get('comment_count'))}")
    lines.append(f"- Danmaku: {_fmt_num(video.get('danmaku_count'))}")
    lines.append("")
    lines.append("> The derived ratios (like-to-play / coin rate / save rate / share-to-play) are signals that raw play count cannot show; "
                 "Bilibili's \"triple-combo rate\" (like + coin + save) especially reflects hardcore approval of the content.")
    lines.append("")

    lines.append("## Original script")
    lines.append("")
    lines.append(script.strip() if script.strip() else "(not provided)")
    lines.append("")

    lines.append(f"## Comments (sorted by likes descending; {len(comments)} total)")
    lines.append("")
    if not comments:
        lines.append("(No comments captured; the comment section may be closed or the video has no comments yet)")
    else:
        for c in comments:
            text = (c.get("text") or "").replace("\n", " ").strip()
            reply = f" 💬{c['reply_comment_total']}" if c.get("reply_comment_total") else ""
            loc = f" [{c['ip_label']}]" if c.get("ip_label") else ""
            lines.append(f"- [👍{c['digg_count']}{reply}]{loc} {text}")
    lines.append("")

    return "\n".join(lines)


def slugify(text: str, max_len: int = 30) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    out = "".join("_" if ch in bad else ch for ch in text).strip()
    return out[:max_len] or "untitled"


def output_dir_for(video: dict, root: Path) -> Path:
    date = _fmt_time(video.get("pubdate", 0))[:10].replace("unknown", "nodate")
    slug = slugify(video.get("title") or video["bvid"])
    return root / f"{date}_{slug}"
