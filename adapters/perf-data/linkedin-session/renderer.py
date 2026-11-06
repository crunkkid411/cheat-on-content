"""Render the fetched LinkedIn single-post analytics into NotebookLM-friendly Markdown (same shape as douyin-session)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path


def _fmt_num(n: int | None) -> str:
    if n is None:
        return "-"
    return f"{n:,}"


def _ratio(num: int | None, den: int | None) -> str:
    """Derived ratio; shows '-' when the denominator is 0 / missing."""
    if not num or not den:
        return "-"
    return f"{num / den * 100:.2f}%"


def render_report(post: dict, script: str) -> str:
    metrics = post.get("metrics", {}) if post else {}
    meta = post.get("meta", {}) if post else {}
    activity_id = post.get("activity_id", "") if post else ""

    impressions = metrics.get("impressions")
    reactions = metrics.get("reactions")
    comments = metrics.get("comments")
    reposts = metrics.get("reposts")

    author = meta.get("author") or ""
    title = author and f"{author}'s LinkedIn post" or f"LinkedIn post {activity_id}"

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- Post activity_id: `{activity_id}`")
    if author:
        lines.append(f"- Author: {author}")
    if meta.get("age"):
        lines.append(f"- Published: {meta['age']} ago")
    lines.append(f"- Link: https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/")
    lines.append(f"- Fetched at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("## Data snapshot")
    lines.append("")
    lines.append(f"- Impressions: {_fmt_num(impressions)}")
    lines.append(f"- Members reached: {_fmt_num(metrics.get('reach'))}")
    lines.append(f"- Social engagements: {_fmt_num(metrics.get('social_engagement'))}")
    lines.append(f"- Reactions: {_fmt_num(reactions)}")
    lines.append(f"- Comments: {_fmt_num(comments)}")
    lines.append(f"- Reposts: {_fmt_num(reposts)}")
    lines.append(f"- Saves: {_fmt_num(metrics.get('saves'))}")
    lines.append(f"- Sends: {_fmt_num(metrics.get('sends'))}")
    lines.append(f"- Profile viewers from post: {_fmt_num(metrics.get('profile_views_from_post'))}")
    lines.append(f"- Followers from post: {_fmt_num(metrics.get('followers_from_post'))}")
    lines.append("")
    lines.append("Derived ratios (relative to impressions):")
    lines.append(f"- Reaction rate: {_ratio(reactions, impressions)}")
    lines.append(f"- Comment rate: {_ratio(comments, impressions)}")
    lines.append(f"- Repost rate: {_ratio(reposts, impressions)}")
    lines.append(f"- Social-engagement rate: {_ratio(metrics.get('social_engagement'), impressions)}")
    lines.append("")

    lines.append("## Post body")
    lines.append("")
    body = (meta.get("text") or "").strip()
    lines.append(body if body else "(body not captured — the single-post analytics page sometimes omits the full body; add it manually)")
    lines.append("")

    lines.append("## Original script")
    lines.append("")
    lines.append(script.strip() if script.strip() else "(not provided)")
    lines.append("")

    lines.append("## Comments")
    lines.append("")
    if comments:
        lines.append(
            f"The LinkedIn single-post analytics page gives only the comment **count** ({comments}), not comment text."
        )
        lines.append(
            "Comment text is the real signal — paste the top comments into this section manually for retrospective analysis."
        )
    else:
        lines.append("(No comments, or the comment count was not captured)")
    lines.append("")

    return "\n".join(lines)


def slugify(text: str, max_len: int = 30) -> str:
    """Generate a folder-friendly short title."""
    bad = '<>:"/\\|?*\n\r\t'
    out = "".join("_" if ch in bad else ch for ch in text).strip()
    return out[:max_len] or "untitled"


def output_dir_for(post: dict, root: Path) -> Path:
    activity_id = post.get("activity_id", "") if post else ""
    date = dt.datetime.now().strftime("%Y-%m-%d")
    author = (post.get("meta", {}) or {}).get("author") if post else ""
    slug = slugify(author or activity_id or "linkedin")
    return root / f"{date}_{activity_id}_{slug}".rstrip("_")
