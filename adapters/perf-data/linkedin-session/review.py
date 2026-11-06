"""Run once after publishing a post: fetch LinkedIn single-post analytics -> generate NotebookLM-friendly md.

Usage:
    python review.py login                              # login only (first time, opens a browser)
    python review.py video <activity_id_or_url> [script.txt]   # fetch single-post analytics

The `video` subcommand name follows the douyin-session / bilibili-stat contract (/cheat-retro
uniformly calls `run.sh ... video ...`); for LinkedIn, "video" means one post.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import crawler
import renderer
from paths import videos_dir


def run_with_id(activity_raw: str, script_path: str | None) -> None:
    active_videos_dir = videos_dir()
    active_videos_dir.mkdir(parents=True, exist_ok=True)

    activity_id = crawler.extract_activity_id(activity_raw)

    script = ""
    if script_path:
        p = Path(script_path).expanduser()
        if p.is_file():
            script = p.read_text(encoding="utf-8", errors="ignore")
            print(f"Script: {p.name} ({len(script)} characters)")
        else:
            print(f"[warning] Cannot find script {p}")

    print(f"[fetch] Post activity:{activity_id}")
    result = asyncio.run(crawler.fetch_all(activity_id))
    post = result["post"]
    if not post:
        print("❌ No data fetched (most likely not logged in). Run first: python review.py login")
        sys.exit(3)

    out_dir = renderer.output_dir_for(post, active_videos_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if script:
        (out_dir / "script.txt").write_text(script, encoding="utf-8")
    md = renderer.render_report(post, script)
    report = out_dir / "report.md"
    report.write_text(md, encoding="utf-8")
    print(f"\n✓ {report}")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        asyncio.run(crawler.ensure_login())
        return
    if len(sys.argv) > 1 and sys.argv[1] == "video":
        if len(sys.argv) < 3:
            print("Usage: python review.py video <activity_id_or_url> [script.txt]")
            sys.exit(3)
        activity_raw = sys.argv[2]
        script_path = sys.argv[3] if len(sys.argv) > 3 else None
        run_with_id(activity_raw, script_path)
        return
    print(__doc__)


if __name__ == "__main__":
    main()
