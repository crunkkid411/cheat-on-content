"""Run once after publishing a video: fetch Bilibili data/comments -> generate NotebookLM-friendly md.

Usage:
    python review.py login                          # Bilibili needs no login (kept for a consistent interface)
    python review.py video <BV number or video URL> [script.txt]   # specify the video directly
"""
from __future__ import annotations

import sys
from pathlib import Path

import crawler
import renderer
from paths import videos_dir


def run_with_id(bvid: str, script_path: str | None) -> None:
    active_videos_dir = videos_dir()
    active_videos_dir.mkdir(parents=True, exist_ok=True)

    script = ""
    if script_path:
        p = Path(script_path).expanduser()
        if p.is_file():
            script = p.read_text(encoding="utf-8", errors="ignore")
            print(f"Script: {p.name} ({len(script)} characters)")
        else:
            print(f"[warning] Cannot find script {p}")

    print(f"[fetch] Video {bvid}")
    result = crawler.fetch_all(bvid)
    video = result["video"]
    comments = result["comments"]

    out_dir = renderer.output_dir_for(video, active_videos_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if script:
        (out_dir / "script.txt").write_text(script, encoding="utf-8")
    md = renderer.render_report(video, script, comments)
    report = out_dir / "report.md"
    report.write_text(md, encoding="utf-8")
    print(f"\n✓ {report}")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        print("[Bilibili] Video data and comments are public APIs; no login needed — just run the retro.")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "video":
        if len(sys.argv) < 3:
            print("Usage: python review.py video <BV number or video URL> [script.txt]")
            sys.exit(3)
        bvid = sys.argv[2]
        script_path = sys.argv[3] if len(sys.argv) > 3 else None
        run_with_id(bvid, script_path)
        return
    print(__doc__)


if __name__ == "__main__":
    main()
