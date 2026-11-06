from __future__ import annotations

import datetime as dt
from pathlib import Path


def _fmt_time(value) -> str:
    if not value:
        return "unknown"
    try:
        ts = int(value)
        if ts > 1_000_000_000_000:
            ts //= 1000
        return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return str(value)


def _fmt_num(value) -> str:
    try:
        n = int(value or 0)
    except (TypeError, ValueError):
        return str(value)
    return f"{n / 1000:.1f}k" if n >= 10000 else str(n)


def _ratio(num, denom) -> str:
    try:
        a, b = int(num or 0), int(denom or 0)
        return "-" if b <= 0 else f"{a / b * 100:.2f}%"
    except (TypeError, ValueError):
        return "-"


def _percent(value) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "-"
    if n <= 1:
        n *= 100
    return f"{n:.2f}%"


def slugify(text: str, max_len: int = 30) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    return ("".join("_" if ch in bad else ch for ch in text).strip()[:max_len] or "untitled")


def output_dir_for(post: dict, root: Path) -> Path:
    date = _fmt_time(post.get("create_time"))[:10].replace("unknown", "nodate")
    return root / f"{date}_{slugify(post.get('title') or post['post_id'])}"


def render_report(post: dict, script: str, comments: list[dict]) -> str:
    title = post.get("title") or "(untitled)"
    views = post.get("view_count") or 0
    lines = [
        f"# {title}",
        "",
        f"- WeChat Channels post ID: `{post['post_id']}`",
        f"- Published at: {_fmt_time(post.get('create_time'))}",
        f"- Fetched at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Data snapshot",
        "",
        f"- Plays/views: {_fmt_num(views)}",
        f"- Likes: {_fmt_num(post.get('like_count'))} (like-to-play {_ratio(post.get('like_count'), views)})",
        f"- Hearts/saves: {_fmt_num(post.get('favorite_count'))} (save-to-play {_ratio(post.get('favorite_count'), views)})",
        f"- Comments: {_fmt_num(post.get('comment_count'))} (comment-to-play {_ratio(post.get('comment_count'), views)})",
        f"- Shares/forwards: {_fmt_num(post.get('share_count'))} (share-to-play {_ratio(post.get('share_count'), views)})",
    ]
    if post.get("full_play_rate") is not None:
        lines.append(f"- Full-play rate: {_percent(post.get('full_play_rate'))}")
    if post.get("avg_play_time_sec") is not None:
        lines.append(f"- Average play time: {float(post.get('avg_play_time_sec')):.1f} s")
    if post.get("fast_flip_rate") is not None:
        lines.append(f"- Fast-flip rate: {_percent(post.get('fast_flip_rate'))}")
    if post.get("follow_count"):
        lines.append(f"- Followers gained: {_fmt_num(post.get('follow_count'))}")
    if post.get("yesterday_view_count"):
        lines.append(f"- New plays yesterday: {_fmt_num(post.get('yesterday_view_count'))}")
    lines.append("")
    lines.extend(["## Original script", "", script.strip() or "(not provided)", "", "## Comments", ""])
    if comments:
        for comment in comments[:20]:
            if not isinstance(comment, dict):
                continue
            text = comment.get("text") or comment.get("content") or comment.get("comment") or ""
            likes = comment.get("like_count") or comment.get("likeCount") or 0
            reply = "(reply)" if comment.get("is_reply") else ""
            if text:
                lines.append(f"- [👍{likes}] {reply}{str(text).replace(chr(10), ' ').strip()}")
    else:
        lines.append("(The post-list API did not return comment text; further capture on the comment-management page is needed.)")
    lines.append("")
    return "\n".join(lines)
