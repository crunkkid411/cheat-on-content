"""Bilibili video data + comment crawler (public APIs; no login, no signature).

Unlike douyin-session / xhs-explore: Bilibili's video statistics and comments are both **public data** —
the `view` API needs no wbi signature, and comments use the older `x/v2/reply` API (sorted by popularity).
So this adapter is pure httpx, zero login, zero browser; clone it and it works.

APIs:
- Video data: https://api.bilibili.com/x/web-interface/view?bvid=<BV number>
- Comments:   https://api.bilibili.com/x/v2/reply?type=1&oid=<aid>&sort=2 (sort=2 = popularity)
"""
from __future__ import annotations

import re
import sys
import time

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA, "Referer": "https://www.bilibili.com"}
VIEW_API = "https://api.bilibili.com/x/web-interface/view"
REPLY_API = "https://api.bilibili.com/x/v2/reply"


def normalize_bvid(raw: str) -> str:
    """Extract the BV number from a BV number or a Bilibili video URL (including after a b23.tv short-link redirect)."""
    m = re.search(r"(BV[0-9A-Za-z]{10})", raw or "")
    return m.group(1) if m else (raw or "").strip()


def _client() -> httpx.Client:
    return httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True)


def fetch_video(client: httpx.Client, bvid: str) -> dict:
    """Fetch video info + statistics. Returns a normalized dict."""
    resp = client.get(VIEW_API, params={"bvid": bvid})
    resp.raise_for_status()
    j = resp.json()
    if j.get("code") != 0:
        raise RuntimeError(f"view API failed code={j.get('code')} msg={j.get('message')}")
    d = j.get("data") or {}
    stat = d.get("stat") or {}
    return {
        "bvid": d.get("bvid") or bvid,
        "aid": d.get("aid"),
        "title": d.get("title") or "",
        "desc": d.get("desc") or "",
        "owner": (d.get("owner") or {}).get("name") or "",
        "pubdate": d.get("pubdate") or 0,
        "duration_s": d.get("duration") or 0,
        "play_count": stat.get("view") or 0,
        "like_count": stat.get("like") or 0,
        "coin_count": stat.get("coin") or 0,
        "favorite_count": stat.get("favorite") or 0,
        "share_count": stat.get("share") or 0,
        "comment_count": stat.get("reply") or 0,
        "danmaku_count": stat.get("danmaku") or 0,
        "raw": d,
    }


def fetch_comments(client: httpx.Client, aid: int, max_count: int = 50) -> list[dict]:
    """Page through comments by popularity (sort=2), up to max_count."""
    out: list[dict] = []
    seen: set[str] = set()
    pn = 1
    for _ in range(60):  # pagination upper-bound guard
        if len(out) >= max_count:
            break
        try:
            j = client.get(
                REPLY_API,
                params={"type": 1, "oid": aid, "sort": 2, "pn": pn, "ps": 20},
            ).json()
        except Exception as exc:
            print(f"[warning] Comment request error (stopping): {exc}")
            break
        if j.get("code") != 0:
            print(f"[warning] Comment API code={j.get('code')} msg={j.get('message')} (stopping)")
            break
        reps = (j.get("data") or {}).get("replies") or []
        if not reps:
            break
        for c in reps:
            nc = _normalize_comment(c)
            if nc["cid"] in seen:
                continue
            seen.add(nc["cid"])
            out.append(nc)
        pn += 1
        time.sleep(0.4)
    out.sort(key=lambda x: x["digg_count"], reverse=True)
    return out[:max_count]


def _normalize_comment(c: dict) -> dict:
    member = c.get("member") or {}
    content = c.get("content") or {}
    loc = (c.get("reply_control") or {}).get("location") or ""
    return {
        "cid": str(c.get("rpid") or ""),
        "text": content.get("message") or "",
        "digg_count": c.get("like") or 0,
        "reply_comment_total": c.get("rcount") or 0,
        "create_time": c.get("ctime") or 0,
        "user_name": member.get("uname") or "",
        # Bilibili's IP-location field is prefixed with "IP属地：" / "IP属地:" in the API payload; strip the prefix.
        "ip_label": loc.replace("IP属地：", "").replace("IP属地:", "").strip() if loc else "",
    }


def fetch_all(bvid: str, max_comments: int = 50) -> dict:
    """Fetch video data + top comments in one go."""
    bvid = normalize_bvid(bvid)
    with _client() as client:
        print(f"  -> Fetching video data {bvid}")
        video = fetch_video(client, bvid)
        print(f"       OK {video['title'][:40]} (plays {video['play_count']})")
        print("  -> Fetching top comments")
        if video.get("aid") is None:
            print("[warning] Video data has no aid field; cannot fetch comments")
            comments = []
        else:
            comments = fetch_comments(client, video["aid"], max_count=max_comments)
        print(f"       OK {len(comments)} comments")
    return {"video": video, "comments": comments}


if __name__ == "__main__":
    # Keeps the same interface as douyin-session / xhs-explore; Bilibili public data needs no login.
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        print("[Bilibili] Video data and comments are public APIs; no login needed — just run /cheat-retro.")
