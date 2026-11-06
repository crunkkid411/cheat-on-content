"""Extract LinkedIn single-post analytics metrics from rendered DOM text.

LinkedIn SSRs/inlines single-post analytics (/analytics/post-summary/) rather than
serving an interceptable voyager XHR, so we read `inner_text` and parse by known label
anchors. Pure functions, independently testable (see test_extract.py).

LinkedIn **randomly switches its UI language between Japanese / English** (even within the
same session), so every metric stores multilingual aliases and both sets are tried.
"""
from __future__ import annotations

import re


def _to_int(s: str) -> int | None:
    """'34,057' -> 34057; '1.2K' -> 1200; '3M' -> 3000000; None if not extractable."""
    s = s.strip().replace(",", "")
    m = re.fullmatch(r"([\d.]+)\s*([KMB]?)", s)
    if not m:
        return None
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[m.group(2)]
    try:
        return int(float(m.group(1)) * mult)
    except ValueError:
        return None


# Single-post analytics page (/analytics/post-summary/). LinkedIn **randomly switches** language
# between Japanese/English, so every metric stores multilingual aliases. The layout has two parts:
#   top metrics — the value is one line above the label ("before")
#   engagement details — the value is one line below the label ("after")
# (labels, key, value_position)
POST_METRICS = [
    (("インプレッション数", "Impressions"), "impressions", "before"),
    (("リーチしたメンバー", "Members reached"), "reach", "before"),
    (("この投稿からのプロフィール閲覧ユーザー", "Profile viewers from this post"), "profile_views_from_post", "before"),
    (("この投稿で獲得したフォロワー", "Followers gained from this post"), "followers_from_post", "before"),
    (("ソーシャルエンゲージメント", "Social engagements"), "social_engagement", "before"),
    (("リアクション", "Reactions"), "reactions", "after"),
    (("コメント", "Comments"), "comments", "after"),
    (("再投稿", "Reposts"), "reposts", "after"),
    (("保存数", "Saves"), "saves", "after"),
    (("LinkedInでの送信数", "Sends on LinkedIn"), "sends", "after"),
]

_IMPRESSION_LABELS = ("インプレッション数", "Impressions")

# Language markers for the author byline ("…さんが投稿しました • 4日" / "… posted this • 6d").
_BYLINE_MARKERS = ("さんが投稿しました", "posted this")
# Small headings that appear before the top-metrics section ("Discovery" / "調査" etc.) — the boundary between body and metrics.
_BODY_END_MARKERS = ("調査", "Discovery", "ディスカバリー")


def parse_post_summary(text: str) -> dict:
    """Single-post analytics DOM text -> {'metrics': {...}}. Supports Japanese/English (LinkedIn switches randomly).

    Anchors after the first metric (Impressions) to avoid numbers in the body; each metric takes
    the line before / after according to value_position. Metrics that cannot be extracted are None
    (so an API/layout change does not crash the whole parse).
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    start = 0
    for i, l in enumerate(lines):
        if l in _IMPRESSION_LABELS:
            start = max(0, i - 1)
            break
    scan = lines[start:]
    out = {key: None for _, key, _ in POST_METRICS}
    for i, line in enumerate(scan):
        for labels, key, pos in POST_METRICS:
            if line not in labels or out[key] is not None:
                continue
            j = i - 1 if pos == "before" else i + 1
            if 0 <= j < len(scan):
                out[key] = _to_int(scan[j])
    return {"metrics": out}


def parse_post_meta(text: str) -> dict:
    """Extract the author byline + relative publish age + body from the single-post analytics DOM.

    Layout (reading order): byline ("…さんが投稿しました • 4日" / "… posted this • 6d")
    -> several body lines -> top-metrics small heading ("Discovery"/"調査") -> metrics section.
    Body is the lines between the byline and the small heading; when extraction fails every field
    is empty rather than raising. Returns {'author': str, 'age': str, 'text': str}.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    byline_idx = None
    for i, l in enumerate(lines):
        if any(m in l for m in _BYLINE_MARKERS):
            byline_idx = i
            break
    if byline_idx is None:
        return {"author": "", "age": "", "text": ""}

    byline = lines[byline_idx]
    author, age = "", ""
    if "•" in byline:
        head, _, tail = byline.partition("•")
        age = tail.strip()
        author = head.strip()
    else:
        author = byline.strip()
    for marker in _BYLINE_MARKERS:
        if marker in author:
            author = author.split(marker, 1)[0].strip()
            break

    body: list[str] = []
    for l in lines[byline_idx + 1:]:
        if l in _IMPRESSION_LABELS or l in _BODY_END_MARKERS:
            break
        body.append(l)
    return {"author": author, "age": age, "text": "\n".join(body).strip()}
