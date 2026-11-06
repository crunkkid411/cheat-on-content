"""Xiaohongshu creator center + frontend comment crawling.

After logging in once, the cookie is persisted in .auth-xhs/ and reused directly afterwards.
A single crawl shares one Chromium session, which is more stable than one process per step.

Design principles (same as douyin-session):
- Do not reverse-engineer the x-s / x-t signatures and do not forge requests — use a logged-in browser,
  let the page send its own signed requests, and only passively intercept the returned JSON.
- The creator's **own** note data goes through the galaxy API (no xsec_token needed) — the most stable main path.
- Comments go through the frontend web API (needs xsec_token) by letting the page navigate itself to trigger tokenized requests;
  when unavailable, degrade gracefully (report.md marks comments_unavailable and cheat-retro falls back to manually pasted comments).

New capabilities in this file (public-page parsing from xhs-analytics):
- fetch_public_note: parse the explore page's __INITIAL_STATE__ without login, for body / images / tags.
- fetch_public_comments: public-page fallback for top comments.
- download_image: download a note image locally.
"""
from __future__ import annotations

import asyncio
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from playwright.async_api import BrowserContext, Page, Response, async_playwright
from paths import auth_dir, debug_dir

CREATOR_HOME = "https://creator.xiaohongshu.com/new/home"
CREATOR_NOTE_MANAGER = "https://creator.xiaohongshu.com/new/note-manager"
# galaxy API path fragments — loose matching, the API occasionally changes its version number
GALAXY_NOTE_LIST_KEYS = (
    # Loose suffix match, compatible with /api/galaxy/creator/... and /api/galaxy/v2/creator/... (v2 in practice)
    "/creator/note/user/posted",
)
GALAXY_NOTE_STATS_KEYS = (
    "/api/galaxy/creator/data/note_stats",
    "/api/galaxy/creator/data/note_detail",
)
# Frontend web API
FEED_KEY = "/api/sns/web/v1/feed"
COMMENT_KEY = "/api/sns/web/v2/comment/page"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


class Session:
    """Single browser session that runs multiple crawl steps in order."""

    def __init__(self, ctx: BrowserContext, pw: Any) -> None:
        self.ctx = ctx
        self.pw = pw

    @classmethod
    async def open(cls, headless: bool = False) -> "Session":
        pw = await async_playwright().start()
        auth_path = auth_dir()
        auth_path.mkdir(parents=True, exist_ok=True)
        common_kwargs = {
            "user_data_dir": str(auth_path),
            "headless": headless,
            "viewport": {"width": 1440, "height": 900},
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        try:
            ctx = await pw.chromium.launch_persistent_context(**common_kwargs)
        except Exception as exc:
            # Some environments only have system Chrome installed, not Playwright Chromium — fall back to channel=chrome
            try:
                ctx = await pw.chromium.launch_persistent_context(
                    **common_kwargs, channel="chrome"
                )
            except Exception:
                raise exc
        return cls(ctx, pw)

    async def close(self) -> None:
        try:
            await self.ctx.close()
        finally:
            await self.pw.stop()


# Creator-center login credentials — scanning the QR code at creator.xiaohongshu.com produces these (the galaxy main path only needs them).
# Note: logging in to the creator center does *not* produce web_session (that is the main site www frontend cookie). Early versions
# only recognized web_session, which was a bug: login succeeded but was never detected, and the tool waited until timeout for nothing.
CREATOR_LOGIN_COOKIES = (
    "access-token-creator.xiaohongshu.com",
    "galaxy_creator_session_id",
    "customer-sso-sid",
)
# Main-site frontend credentials — needed by the feed / comment web APIs; only issued after visiting www while logged in.
WEB_LOGIN_COOKIE = "web_session"


async def _cookie_map(ctx: BrowserContext, host: str) -> dict[str, str]:
    try:
        return {c["name"]: c.get("value", "") for c in await ctx.cookies(host)}
    except Exception:
        return {}


async def _creator_logged_in(ctx: BrowserContext) -> bool:
    names = await _cookie_map(ctx, "https://creator.xiaohongshu.com")
    return any(names.get(n) for n in CREATOR_LOGIN_COOKIES)


async def _has_web_session(ctx: BrowserContext) -> bool:
    for host in ("https://www.xiaohongshu.com", "https://creator.xiaohongshu.com"):
        if (await _cookie_map(ctx, host)).get(WEB_LOGIN_COOKIE):
            return True
    return False


async def _acquire_web_session(page: Page) -> None:
    """After creator-center login, visit the main site so SSO issues web_session (needed by frontend feed/comments). Best-effort."""
    try:
        await page.goto("https://www.xiaohongshu.com/explore",
                        wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        if await _has_web_session(page.context):
            print("[login] OK: acquired main-site web_session (frontend comments/interactions available)")
        else:
            print("[login] Note: no web_session obtained; frontend comments may need manual input; the galaxy main path is unaffected.")
    except Exception:
        pass


async def ensure_login(timeout_s: int = 180, max_refresh: int = 5) -> bool:
    """Scan the QR code to log in to the creator center; once the creator login is detected, exchange for web_session and close automatically.

    The QR code itself expires, so timeout_s is the per-attempt wait limit; after it, the page is refreshed to show a new code,
    up to max_refresh times. This gives the user plenty of time to scan.
    """
    sess = await Session.open()
    try:
        page = await sess.ctx.new_page()
        await page.goto(CREATOR_HOME)
        print(f"[login] Scan the QR code in the Chromium window to log in to the Xiaohongshu creator center. Each QR code is valid for about {timeout_s} seconds; it refreshes automatically on timeout.")

        for refresh in range(max_refresh + 1):
            for i in range(timeout_s):
                try:
                    if await _creator_logged_in(sess.ctx) and "login" not in page.url:
                        print(f"[login] OK: creator-center login confirmed (total {refresh * timeout_s + i}s)")
                        await _acquire_web_session(page)
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    pass

                # Remind every 30 seconds so the user does not think it is stuck
                if i > 0 and i % 30 == 0:
                    print(f"[login] Waited {i}s; please scan with the Xiaohongshu app (or wait for the QR code to refresh)...")

                await asyncio.sleep(1)

            if refresh < max_refresh:
                print(f"[login] QR code not scanned or expired; refreshing the page for a new code (refresh {refresh + 1}/{max_refresh})...")
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    await page.goto(CREATOR_HOME)

        print("[login] Maximum refreshes reached without detecting a login; stopped. Rerun this command to continue.")
        return False
    finally:
        await sess.close()


async def fetch_recent_notes(sess: Session, limit: int = 50) -> list[dict]:
    """Creator-center note manager page -> intercept the galaxy note list + per-note operational data (including impressions/views)."""
    captured: list[dict] = []
    all_urls: list[str] = []

    page = await sess.ctx.new_page()

    async def on_response(resp: Response) -> None:
        all_urls.append(resp.url)
        if any(k in resp.url for k in GALAXY_NOTE_LIST_KEYS + GALAXY_NOTE_STATS_KEYS):
            try:
                data = await resp.json()
                captured.append({"url": resp.url, "data": data})
                if len(captured) == 1 and isinstance(data, dict):
                    print(f"[diagnostic] galaxy API keys: {list(data.keys())[:8]}")
            except Exception:
                pass

    page.on("response", on_response)
    try:
        await page.goto(CREATOR_NOTE_MANAGER, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(8)
        # An expired cookie gets a 302 to the login page
        if "login" in page.url or "redirectReason=401" in page.url:
            print("[login] The creator center redirected to the login page; the cookie may have expired. Run: python crawler.py login")
            return []
        for _ in range(4):
            await page.evaluate("window.scrollBy(0, 1200)")
            await asyncio.sleep(1.5)
        notes = _parse_note_list(captured, limit)
        if not notes:
            _dump(all_urls, "creator_urls.txt", captured, "creator_captured.json")
            print(f"[diagnostic] Note list empty; {len(all_urls)} requests dumped to .cheat-cache/xhs-explore-debug/.")
        return notes
    finally:
        await page.close()


def _iter_candidates(data: Any) -> list:
    """Dig the "note array" out of any galaxy response. The structure varies; match loosely."""
    out: list = []
    if isinstance(data, dict):
        # Common wrappers: {data: {...}} / {data: [...]} / a top-level list field
        inner = data.get("data") if isinstance(data.get("data"), (dict, list)) else data
        targets = [inner] if not isinstance(inner, list) else []
        if isinstance(inner, list):
            out.extend(inner)
        for t in targets:
            if isinstance(t, dict):
                for key in ("notes", "note_list", "list", "items", "note_stats", "result"):
                    val = t.get(key)
                    if isinstance(val, list):
                        out.extend(val)
    return out


def _parse_note_list(captured: list[dict], limit: int) -> list[dict]:
    by_id: dict[str, dict] = {}
    for item in captured:
        for raw in _iter_candidates(item["data"]):
            if not isinstance(raw, dict):
                continue
            note = _normalize_note(raw)
            if not note["note_id"]:
                continue
            # The same note may appear once in the list API and once in the stats API — merge, preferring non-empty fields
            existing = by_id.get(note["note_id"])
            if existing:
                for k, v in note.items():
                    if v and not existing.get(k):
                        existing[k] = v
            else:
                by_id[note["note_id"]] = note
    return list(by_id.values())[:limit]


def _first(d: dict, *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None and d[k] != "":
            return d[k]
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return 0


def _normalize_note(v: dict) -> dict:
    note_id = v.get("note_id") or v.get("id") or v.get("noteId") or ""
    # Field names are calibrated against real responses (2026-05 /api/galaxy/v2/creator/note/user/posted):
    #   views view_count | likes likes | saves collected_count | comments comments_count
    #   shares shared_count | publish time visible_time (unix seconds) | per-note token xsec_token
    # Confirmed names come first; older candidates remain as fallbacks in case the API changes again.
    return {
        "note_id": str(note_id),
        "title": v.get("display_title") or v.get("title") or v.get("desc") or v.get("name") or "",
        "create_time": _to_int(_first(v, "visible_time", "create_time", "post_time", "publish_time")),
        "view_count": _to_int(_first(v, "view_count", "view", "imp", "impression", "read_count", "pv")),
        "like_count": _to_int(_first(v, "likes", "like_count", "liked_count", "like")),
        "collect_count": _to_int(_first(v, "collected_count", "collect_count", "collect", "fav_count")),
        "comment_count": _to_int(_first(v, "comments_count", "comment_count", "comment", "cmt_count")),
        "share_count": _to_int(_first(v, "shared_count", "share_count", "share")),
        "fans_inc": _to_int(_first(v, "fans", "fans_inc", "new_fans", "follow_count")),
        "post_time_str": v.get("time") or "",  # galaxy provides a local time string, saving timezone conversion from epoch
        "xsec_token": v.get("xsec_token") or "",
        "note_type": v.get("type") or "",
        "raw": v,
    }


def _to_int(x: Any) -> int:
    try:
        if isinstance(x, str):
            x = x.replace(",", "").strip()
        return int(float(x))
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Public-page parsing (core capability from xhs-analytics): body, images, tags, comment fallback without login
# ---------------------------------------------------------------------------

def _extract_initial_state(html: str) -> dict | None:
    """Parse window.__INITIAL_STATE__ out of the Xiaohongshu explore page HTML."""
    marker = "window.__INITIAL_STATE__="
    start = html.find(marker)
    if start == -1:
        return None
    script_start = html.rfind("<script", 0, start)
    script_end = html.find("</script>", start)
    if script_start == -1 or script_end == -1:
        return None
    script = html[script_start:script_end]
    assign_start = script.find(marker) + len(marker)
    json_str = script[assign_start:]
    json_str = re.sub(r":\s*undefined\s*([,}\]])", r":null\1", json_str)
    json_str = json_str.rstrip().rstrip(';').rstrip()
    try:
        return json.loads(json_str)
    except Exception:
        return None


def _image_url(img: dict) -> str:
    """Extract a usable image URL from an imageList element."""
    if not isinstance(img, dict):
        return ""
    for key in ("urlDefault", "url"):
        if img.get(key):
            return img[key]
    for info in img.get("infoList", []) or []:
        if isinstance(info, dict) and info.get("imageScene") == "WB_DFT" and info.get("url"):
            return info["url"]
    for info in img.get("infoList", []) or []:
        if isinstance(info, dict) and info.get("url"):
            return info["url"]
    return ""


def _xsec_token_from_url(url: str | None) -> str:
    """Pull xsec_token out of a note URL's query (preserving the original encoding)."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.unquote(urllib.parse.parse_qs(parsed.query).get("xsec_token", [""])[0])


def fetch_public_note(note_id: str, xsec_token: str) -> dict:
    """Fetch the public explore page without login and parse __INITIAL_STATE__.

    Returns a dict: success, note_id, title, desc/body, images, tags, time, counts, raw.
    """
    token = urllib.parse.unquote(xsec_token)
    url = (
        f"https://www.xiaohongshu.com/explore/{note_id}"
        f"?xsec_token={urllib.parse.quote(token)}"
        f"&xsec_source=pc_creatormng"
    )
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    state = _extract_initial_state(r.text)
    if not state:
        raise ValueError("could not parse the page's initial state")

    note_detail_map = state.get("note", {}).get("noteDetailMap", {})
    if note_id not in note_detail_map:
        raise ValueError("the page did not return data for this note")

    raw = note_detail_map[note_id]
    note = raw.get("note", {})
    interact = note.get("interactInfo", {})

    return {
        "success": True,
        "note_id": note_id,
        "title": note.get("title", ""),
        "desc": note.get("desc", ""),
        "body": note.get("desc", ""),
        "type": note.get("type", ""),
        "time": note.get("time", 0),
        "images": [_image_url(img) for img in note.get("imageList", [])],
        "tags": [tag.get("name", "") for tag in note.get("tagList", []) if tag.get("name")],
        "counts": {
            "liked": _to_int(interact.get("likedCount")),
            "collected": _to_int(interact.get("collectedCount")),
            "comment": _to_int(interact.get("commentCount")),
            "shared": _to_int(interact.get("shareCount")),
        },
        "raw": raw,
    }


def _normalize_public_comment(c: dict) -> dict:
    """Normalize comment fields from __INITIAL_STATE__ / the edith API into the adapter format."""
    user = c.get("user_info") or c.get("userInfo") or {}
    like_count = c.get("like_count") or c.get("likeCount") or 0
    sub_count = c.get("sub_comment_count") or c.get("subCommentCount") or 0
    return {
        "cid": str(c.get("id") or c.get("comment_id") or ""),
        "text": c.get("content") or "",
        "like_count": _to_int(like_count),
        "sub_comment_count": _to_int(sub_count),
        "create_time": c.get("create_time") or c.get("createTime") or 0,
        "user_name": user.get("nickname") or "",
        "ip_label": c.get("ip_location") or c.get("ipLocation") or "",
    }


def fetch_public_comments(note_id: str, xsec_token: str, max_comments: int = 20) -> list[dict]:
    """Public-page __INITIAL_STATE__ fallback for top comments (usually ~10)."""
    token = urllib.parse.unquote(xsec_token)
    url = (
        f"https://www.xiaohongshu.com/explore/{note_id}"
        f"?xsec_token={urllib.parse.quote(token)}"
        f"&xsec_source=pc_creatormng"
    )
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    state = _extract_initial_state(r.text)
    if not state:
        return []

    raw = state.get("note", {}).get("noteDetailMap", {}).get(note_id, {})
    comments = []
    # The comment path inside __INITIAL_STATE__ may be comments.list or commentsList
    for key in ("comments", "commentsList"):
        container = raw.get(key) if isinstance(raw, dict) else None
        if isinstance(container, dict):
            arr = container.get("list") or container.get("comments") or []
            if isinstance(arr, list):
                comments.extend([_normalize_public_comment(c) for c in arr])
        elif isinstance(container, list):
            comments.extend([_normalize_public_comment(c) for c in container])

    seen = set()
    dedup = []
    for c in comments:
        if not c["cid"] or c["cid"] in seen:
            continue
        seen.add(c["cid"])
        dedup.append(c)
    dedup.sort(key=lambda x: x["like_count"], reverse=True)
    return dedup[:max_comments]


async def download_image(url: str, dest: Path, timeout: int = 30) -> bool:
    """Download a single image to dest (fixing the extension from Content-Type). Async wrapper."""
    if not url:
        return False
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    def _download() -> bool:
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.xiaohongshu.com/",
        }
        r = requests.get(url, headers=headers, timeout=timeout, stream=True)
        r.raise_for_status()

        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path)
        ext = Path(path).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}:
            ct = r.headers.get("Content-Type", "").lower()
            if "webp" in ct:
                ext = ".webp"
            elif "png" in ct:
                ext = ".png"
            elif "gif" in ct:
                ext = ".gif"
            else:
                ext = ".jpg"
        dest_final = dest.with_suffix(ext)

        with open(dest_final, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True

    try:
        return await asyncio.to_thread(_download)
    except Exception as exc:
        print(f"[download image] Failed {url}: {exc}")
        return False


async def fetch_note_frontend(
    sess: Session,
    note_id: str,
    note_url: str | None = None,
    xsec_token: str | None = None,
) -> dict:
    """Open the frontend note page -> intercept feed (confirmed interact_info fields) + comment/page.

    The frontend needs xsec_token + a login session (web_session).
    - If note_url is passed (containing xsec_token, e.g. ?xsec_token=...&xsec_source=pc_creatormng copied from the creator backend)
      -> navigate with it directly; most stable.
    - Otherwise fall back to the bare explore URL (may only work for a logged-in account visiting its own note).
    Token missing / not logged in -> dump and degrade (comments left to manual).

    When comments cannot be intercepted, falls back to the top comments in the public page's __INITIAL_STATE__.
    """
    feed: dict = {}
    comments: list[dict] = []
    all_urls: list[str] = []

    page = await sess.ctx.new_page()

    async def on_response(resp: Response) -> None:
        all_urls.append(resp.url)
        if FEED_KEY in resp.url:
            try:
                data = await resp.json()
                ii = _extract_interact(data)
                if ii:
                    feed.update(ii)
            except Exception:
                pass
        elif COMMENT_KEY in resp.url:
            try:
                data = await resp.json()
                for c in _extract_comments(data):
                    comments.append(c)
            except Exception:
                pass

    page.on("response", on_response)
    try:
        url = note_url or f"https://www.xiaohongshu.com/explore/{note_id}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"[warning] Note page load error: {e}")
        await asyncio.sleep(5)
        if "website-login/error" in page.url or "登录" in (await page.title()):
            print("[warning] Hit a login wall (security restriction) — the cookie is not logged in or has expired. Run crawler.py login to scan the QR code.")

        # Scroll the comment area to trigger paginated lazy loading
        last = 0
        stagnant = 0
        for _ in range(40):
            await page.evaluate("window.scrollBy(0, 1400)")
            await asyncio.sleep(1.8)
            cur = len({c["cid"] for c in comments})
            if cur == last:
                stagnant += 1
                if stagnant >= 5:
                    break
            else:
                stagnant = 0
                last = cur

        # Fallback: top comments in the public page's __INITIAL_STATE__
        if not comments:
            xsec = xsec_token or _xsec_token_from_url(note_url)
            if xsec:
                try:
                    public_comments = await asyncio.to_thread(
                        fetch_public_comments, note_id, xsec, max_comments=20
                    )
                    if public_comments:
                        comments = public_comments
                        print(f"       public-page fallback: {len(comments)} comments")
                except Exception as exc:
                    print(f"[diagnostic] Public-page comment fallback failed: {exc}")

        if not comments:
            dbg = debug_dir()
            dbg.mkdir(parents=True, exist_ok=True)
            try:
                await page.screenshot(path=str(dbg / f"note_{note_id}.png"))
            except Exception:
                pass
            (dbg / "frontend_urls.txt").write_text("\n".join(all_urls), encoding="utf-8")
            print("[diagnostic] No comments intercepted on the frontend (xsec_token may be missing or comments closed); URLs dumped.")

        # Dedupe + sort by likes descending
        seen = set()
        dedup = []
        for c in comments:
            if c["cid"] in seen:
                continue
            seen.add(c["cid"])
            dedup.append(c)
        dedup.sort(key=lambda x: x["like_count"], reverse=True)
        print(f"       {len(dedup)} comments on the frontend in total")
        return {"interact": feed, "comments": dedup}
    finally:
        await page.close()


def _extract_interact(data: Any) -> dict:
    """Dig interact_info (confirmed fields) out of a feed response."""
    if not isinstance(data, dict):
        return {}
    items = []
    d = data.get("data", data)
    if isinstance(d, dict):
        items = d.get("items") or d.get("note_list") or []
    for it in items if isinstance(items, list) else []:
        node = it.get("note_card") or it.get("note") or it
        ii = node.get("interact_info") if isinstance(node, dict) else None
        if isinstance(ii, dict):
            return {
                "like_count": _to_int(ii.get("liked_count")),
                "collect_count": _to_int(ii.get("collected_count")),
                "comment_count": _to_int(ii.get("comment_count")),
                "share_count": _to_int(ii.get("share_count")),
                "ip_location": node.get("ip_location") or "",
            }
    return {}


def _extract_comments(data: Any) -> list[dict]:
    """comment/page response -> comment list (confirmed fields)."""
    out: list[dict] = []
    if not isinstance(data, dict):
        return out
    d = data.get("data", data)
    arr = d.get("comments") if isinstance(d, dict) else None
    for c in arr or []:
        if not isinstance(c, dict):
            continue
        user = c.get("user_info") or {}
        out.append({
            "cid": str(c.get("id") or c.get("comment_id") or ""),
            "text": c.get("content") or "",
            "like_count": _to_int(c.get("like_count")),
            "sub_comment_count": _to_int(c.get("sub_comment_count")),
            "create_time": c.get("create_time") or 0,
            "user_name": user.get("nickname") or "",
            "ip_label": c.get("ip_location") or "",
        })
    return out


def _dump(urls: list[str], url_file: str, captured: list[dict], cap_file: str) -> None:
    dbg = debug_dir()
    dbg.mkdir(parents=True, exist_ok=True)
    (dbg / url_file).write_text("\n".join(urls), encoding="utf-8")
    try:
        (dbg / cap_file).write_text(
            json.dumps([c["data"] for c in captured][:5], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _merge_public_note(note: dict, public: dict) -> None:
    """Fill in note with public-page data (without overwriting existing galaxy operational data)."""
    if not public.get("success"):
        return
    for key in ("title", "desc", "body", "type", "images", "tags"):
        if public.get(key) and not note.get(key):
            note[key] = public[key]
    if public.get("time") and not note.get("create_time"):
        note["create_time"] = _to_int(public["time"])
    counts = public.get("counts") or {}
    mapping = {
        "like_count": counts.get("liked"),
        "collect_count": counts.get("collected"),
        "comment_count": counts.get("comment"),
        "share_count": counts.get("shared"),
    }
    for k, v in mapping.items():
        if v and not note.get(k):
            note[k] = _to_int(v)


async def fetch_all(note_id: str, note_url: str | None = None) -> dict:
    """Run the whole flow in one session: note list (with galaxy metrics) + frontend interact + comments + public-page body/image fallback."""
    sess = await Session.open()
    try:
        print("  -> Opening the creator center, pulling the note list + operational data")
        notes = await fetch_recent_notes(sess, limit=50)
        note = next((n for n in notes if n["note_id"] == note_id), None)
        if not note:
            print(f"       {note_id} not found among the latest {len(notes)} notes; continuing with minimal metadata.")
            note = _normalize_note({"note_id": note_id})
        else:
            print(f"       OK {(note.get('title') or '')[:40]} (impressions {note.get('view_count')})")

        # When fetching your own notes, the galaxy list already carries each note's xsec_token — build the frontend URL automatically,
        # so there is no need to paste a tokenized link by hand
        front_url = note_url
        if not front_url and note.get("xsec_token"):
            front_url = (f"https://www.xiaohongshu.com/explore/{note_id}"
                         f"?xsec_token={note['xsec_token']}&xsec_source=pc_creatormng")

        xsec = _xsec_token_from_url(front_url) or note.get("xsec_token", "")

        # First fill body/images/tags from the public page (no login, low cost), without overwriting galaxy-confirmed counts
        if xsec:
            try:
                public = await asyncio.to_thread(fetch_public_note, note_id, xsec)
                _merge_public_note(note, public)
                print("       OK public-page body/images/tags filled in")
            except Exception as exc:
                print(f"[diagnostic] Public-page fallback failed: {exc}")

        print("  -> Opening the frontend note page to capture interact + comments")
        front = await fetch_note_frontend(sess, note_id, note_url=front_url, xsec_token=xsec)
        # Frontend interact fields are confirmed — use them to fill in / override counts that galaxy may be missing
        for k in ("like_count", "collect_count", "comment_count", "share_count"):
            if front["interact"].get(k):
                note[k] = front["interact"][k]
        if front["interact"].get("ip_location"):
            note["ip_location"] = front["interact"]["ip_location"]

        return {"note": note, "comments": front["comments"]}
    finally:
        await sess.close()


if __name__ == "__main__":
    asyncio.run(ensure_login())
