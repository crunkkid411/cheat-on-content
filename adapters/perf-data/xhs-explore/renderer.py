"""Render the fetched Xiaohongshu data into report.md (cheat-retro reads this file)."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def _fmt_time(ts) -> str:
    if not ts:
        return "unknown"
    try:
        ts = int(ts)
        # Some Xiaohongshu APIs use millisecond timestamps
        if ts > 1e12:
            ts //= 1000
        return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError, OSError):
        return str(ts)


def _fmt_num(n) -> str:
    if n is None:
        return "-"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 10000:
        return f"{n/1000:.1f}k"
    return str(n)


def _ratio(num, denom) -> str:
    try:
        num, denom = int(num), int(denom)
    except (ValueError, TypeError):
        return "-"
    if denom <= 0:
        return "-"
    return f"{num/denom*100:.2f}%"


def _escape_md(text: str) -> str:
    """Light escaping so a # in the body is not mistaken for a heading."""
    return text.replace("\n", "  \n").replace("#", "\\#")


def render_report(note: dict, script: str, comments: list[dict]) -> str:
    lines: list[str] = []
    title = note.get("title") or "(untitled)"
    note_id = note["note_id"]
    view = note.get("view_count") or 0

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- Note ID: `{note_id}`")
    lines.append(f"- Published at: {note.get('post_time_str') or _fmt_time(note.get('create_time', 0))}")
    lines.append(f"- Link: https://www.xiaohongshu.com/explore/{note_id}")
    lines.append(f"- Fetched at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if note.get("ip_location"):
        lines.append(f"- IP location: {note['ip_location']}")
    lines.append("")

    lines.append("## Data snapshot")
    lines.append("")
    lines.append(f"- Impressions/views: {_fmt_num(view)}")
    lines.append(f"- Likes: {_fmt_num(note.get('like_count'))} (like-to-impression {_ratio(note.get('like_count'), view)})")
    lines.append(f"- Saves: {_fmt_num(note.get('collect_count'))} (save-to-impression {_ratio(note.get('collect_count'), view)})")
    lines.append(f"- Comments: {_fmt_num(note.get('comment_count'))} (comment-to-impression {_ratio(note.get('comment_count'), view)})")
    lines.append(f"- Shares: {_fmt_num(note.get('share_count'))} (share-to-impression {_ratio(note.get('share_count'), view)})")
    if note.get("fans_inc"):
        lines.append(f"- Follower gain: {_fmt_num(note.get('fans_inc'))}")
    lines.append("")

    # Body + tags (present only when the public-page fallback ran)
    body = note.get("body") or note.get("desc") or ""
    tags = note.get("tags") or []
    if body or tags:
        lines.append("## Body")
        lines.append("")
        if tags:
            lines.append(" ".join(f"#{t}" for t in tags))
            lines.append("")
        lines.append(_escape_md(body) if body else "(none)")
        lines.append("")

    # Images (local path preferred, otherwise URL)
    image_paths = note.get("image_paths") or []
    image_urls = note.get("images") or []
    images = image_paths or image_urls
    if images:
        lines.append("## Images")
        lines.append("")
        for i, img in enumerate(images, 1):
            lines.append(f"![image {i}]({img})")
        lines.append("")

    # galaxy raw JSON — used on the first run to confirm the real key name for impressions
    raw = note.get("raw")
    if raw:
        lines.append("### galaxy raw fields (first-run calibration; ignore once the impressions key is confirmed)")
        lines.append("")
        lines.append("```json")
        full = json.dumps(raw, ensure_ascii=False, indent=2)
        truncated = full[:2500]
        if len(full) > 2500:
            truncated += "\n... (truncated)"
        lines.append(truncated)
        lines.append("```")
        lines.append("")

    lines.append("## Original script")
    lines.append("")
    lines.append(script.strip() if script.strip() else "(not provided)")
    lines.append("")

    lines.append(f"## Comments (sorted by likes descending; {len(comments)} total)")
    lines.append("")
    if not comments:
        lines.append("(No comments captured — xsec_token may be missing, comments may be closed, or manual paste may be needed)")
    else:
        for c in comments:
            reply = f" 💬{c['sub_comment_count']}" if c.get("sub_comment_count") else ""
            ip = f" [{c['ip_label']}]" if c.get("ip_label") else ""
            text = (c.get("text") or "").replace("\n", " ").strip()
            lines.append(f"- [👍{c['like_count']}{reply}]{ip} {text}")
    lines.append("")

    return "\n".join(lines)


def slugify(text: str, max_len: int = 30) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    out = "".join("_" if ch in bad else ch for ch in text).strip()
    return out[:max_len] or "untitled"


def output_dir_for(note: dict, root: Path) -> Path:
    date = (note.get("post_time_str") or _fmt_time(note.get("create_time", 0)))[:10].replace("unknown", "nodate")
    slug = slugify(note.get("title") or note["note_id"])
    return root / f"{date}_{slug}"
