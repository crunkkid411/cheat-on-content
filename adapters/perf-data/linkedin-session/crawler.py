"""LinkedIn single-post analytics crawler.

After logging in once, the cookie (including `li_at`) is persisted in .auth-linkedin/ and reused directly.
LinkedIn SSRs/inlines single-post analytics (/analytics/post-summary/) into the page, with no stable
voyager XHR to intercept, so we read the rendered DOM text and parse by known label anchors (see extract.py).
Like douyin-session: one crawl shares a single persistent Chromium session.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

from playwright.async_api import BrowserContext, Page, async_playwright

from paths import auth_dir, debug_dir
from extract import parse_post_meta, parse_post_summary

FEED = "https://www.linkedin.com/feed/"
POST_SUMMARY = "https://www.linkedin.com/analytics/post-summary/urn:li:activity:{activity_id}/"

_ACTIVITY_RE = re.compile(r"urn:li:activity:(\d+)|activity[:-](\d+)|/(\d{15,25})\b")


def extract_activity_id(raw: str) -> str:
    """Extract activity_id from a post URL or a bare id.

    Supports:
    - bare id: `7470493738918920193`
    - post link: `https://www.linkedin.com/feed/update/urn:li:activity:7470493738918920193/`
    - analytics link: `https://www.linkedin.com/analytics/post-summary/urn:li:activity:7470493738918920193/`
    Returns the input unchanged when extraction fails (the caller reports the error).
    """
    raw = raw.strip()
    if raw.isdigit():
        return raw
    m = _ACTIVITY_RE.search(raw)
    if m:
        return next(g for g in m.groups() if g)
    return raw


class Session:
    """Single browser session with a persistent login."""

    def __init__(self, ctx: BrowserContext, pw: Any) -> None:
        self.ctx = ctx
        self.pw = pw

    @classmethod
    async def open(cls, headless: bool = False) -> "Session":
        pw = await async_playwright().start()
        auth_path = auth_dir()
        auth_path.mkdir(parents=True, exist_ok=True)
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=str(auth_path),
            headless=headless,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        return cls(ctx, pw)

    async def close(self) -> None:
        try:
            await self.ctx.close()
        finally:
            await self.pw.stop()


async def _logged_in(ctx: BrowserContext) -> bool:
    cookies = await ctx.cookies("https://www.linkedin.com")
    return any(c["name"] == "li_at" for c in cookies)


async def ensure_login(timeout_s: int = 300) -> bool:
    """Open LinkedIn and wait for the user to log in; returns once the li_at cookie is detected."""
    sess = await Session.open()
    try:
        page = await sess.ctx.new_page()
        await page.goto(FEED)
        print(f"[login] Log in to LinkedIn in the Chromium window. Waiting up to {timeout_s} seconds...")
        for i in range(timeout_s):
            if await _logged_in(sess.ctx):
                print(f"[login] OK: li_at detected ({i}s). Cookie stored in .auth-linkedin/")
                await asyncio.sleep(1)
                return True
            await asyncio.sleep(1)
        print("[login] Timed out without detecting a login.")
        return False
    finally:
        await sess.close()


async def _scrape_post(page: Page, activity_id: str) -> dict:
    await page.goto(
        POST_SUMMARY.format(activity_id=activity_id),
        wait_until="domcontentloaded",
        timeout=60000,
    )
    await asyncio.sleep(7)
    if "post-summary" not in page.url:
        print(f"[post] WARNING: possibly logged out / redirected: {page.url}")
    txt = await page.inner_text("body")
    dbg = debug_dir()
    dbg.mkdir(parents=True, exist_ok=True)
    (dbg / f"post_{activity_id}.txt").write_text(txt, encoding="utf-8")

    result = parse_post_summary(txt)
    result["meta"] = parse_post_meta(txt)
    result["activity_id"] = activity_id
    if result["metrics"].get("impressions") is None:
        print(f"[post] WARNING: no impressions extracted for {activity_id} (layout may have changed; see {dbg}/post_{activity_id}.txt)")
    return result


async def fetch_post_summary(activity_id: str, headless: bool = True) -> dict:
    """Extract single-post analytics from the DOM (/analytics/post-summary/). Only **your own** posts are visible."""
    sess = await Session.open(headless=headless)
    try:
        if not await _logged_in(sess.ctx):
            print("[post] Not logged in. Run first: python review.py login")
            return {}
        page = await sess.ctx.new_page()
        return await _scrape_post(page, activity_id)
    finally:
        await sess.close()


async def fetch_all(activity_id: str, headless: bool = True) -> dict:
    """Fetch single-post analytics and return {'post': {...}} (aligned with review.py's render entry point)."""
    print(f"  -> Opening the single-post analytics page activity:{activity_id}")
    post = await fetch_post_summary(activity_id, headless=headless)
    if post:
        m = post.get("metrics", {})
        print(f"       impressions={m.get('impressions')} reactions={m.get('reactions')} comments={m.get('comments')}")
    return {"post": post}


if __name__ == "__main__":
    asyncio.run(ensure_login())
