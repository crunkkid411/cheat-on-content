"""Run once after publishing a note: fetch data + comments -> generate report.md.

Usage:
    python review.py                       # interactive note picker
    python review.py login                 # login only (first QR-code scan)
    python review.py list                  # list recent notes (verify the login session)
    python review.py note <note_id> [script.txt]   # specify the note directly
    python review.py archive <notes.json> [output_root] [limit]   # bulk-archive body + images
    python review.py summarize [out_dir]   # account-level summary (based on the latest 50)

archive / summarize capabilities come from xhs-analytics' public-page parsing and can fetch body and images without login.
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import crawler
import renderer
from paths import runtime_project_root, videos_dir


LOG_FILE: io.TextIOWrapper | None = None


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except Exception:
        pass
    if LOG_FILE is not None:
        try:
            LOG_FILE.write(line + "\n")
            LOG_FILE.flush()
        except Exception:
            pass


def _parse_note_arg(arg: str) -> tuple[str, str | None]:
    """Accept a note_id or a full note URL (with xsec_token). Returns (note_id, note_url|None)."""
    arg = arg.strip().strip("'").strip('"')
    if arg.startswith("http"):
        m = re.search(r"/(?:explore|discovery/item)/([0-9a-zA-Z]+)", arg)
        note_id = m.group(1) if m else arg
        return note_id, arg
    return arg, None


def _prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except EOFError:
        return ""


def _pick_note(notes: list[dict]) -> dict | None:
    if not notes:
        print("Could not fetch the note list. Confirm the creator center is logged in, or the page structure changed and the crawler needs updating.")
        return None
    print("\nRecent notes:")
    for i, n in enumerate(notes):
        t = renderer._fmt_time(n.get("create_time", 0))
        title = (n.get("title") or "").replace("\n", " ")[:40]
        print(f"  [{i}] {t} | impressions {renderer._fmt_num(n.get('view_count'))} | {title}")
    choice = _prompt("\nPick an index (Enter to cancel): ")
    if not choice.isdigit():
        return None
    idx = int(choice)
    if 0 <= idx < len(notes):
        return notes[idx]
    return None


async def run() -> None:
    active_videos_dir = videos_dir()
    active_videos_dir.mkdir(parents=True, exist_ok=True)

    print("[pick note] Opening the creator center to pull the list...")
    sess = await crawler.Session.open()
    try:
        notes = await crawler.fetch_recent_notes(sess, limit=10)
    finally:
        await sess.close()
    note = _pick_note(notes)
    if not note:
        print("Cancelled.")
        return

    script_raw = _prompt("Drag the script txt here (or press Enter to skip): ")
    script_path: str | None = None
    if script_raw.strip():
        p = Path(script_raw.strip().strip("'").strip('"').replace("\\ ", " ")).expanduser()
        if p.is_file():
            script_path = str(p)
        else:
            print(f"[warning] Cannot find {p}; leaving the script empty.")

    await run_with_id(note["note_id"], script_path)


async def run_with_id(note_arg: str, script_path: str | None) -> None:
    active_videos_dir = videos_dir()
    active_videos_dir.mkdir(parents=True, exist_ok=True)

    note_id, note_url = _parse_note_arg(note_arg)

    script = ""
    if script_path:
        p = Path(script_path).expanduser()
        if p.is_file():
            script = p.read_text(encoding="utf-8", errors="ignore")
            print(f"Script: {p.name} ({len(script)} characters)")
        else:
            print(f"[warning] Cannot find script {p}")

    print(f"[fetch] Note {note_id}" + (" (tokenized URL)" if note_url else ""))
    result = await crawler.fetch_all(note_id, note_url=note_url)
    note = result["note"]
    comments = result["comments"]

    out_dir = renderer.output_dir_for(note, active_videos_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if script:
        (out_dir / "script.txt").write_text(script, encoding="utf-8")

    # Optional: download images locally (off by default; enable with the environment variable XHS_DOWNLOAD_IMAGES=1)
    if os.environ.get("XHS_DOWNLOAD_IMAGES", "").lower() in ("1", "true", "yes"):
        img_dir = out_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        for i, url in enumerate(note.get("images", []), 1):
            dest = img_dir / f"{i:02d}"
            if await crawler.download_image(url, dest):
                # download_image fixes the extension from Content-Type; recover the real filename here
                actual = next(dest.parent.glob(f"{dest.name}.*"), dest)
                paths.append(str(actual.relative_to(out_dir)).replace("\\", "/"))
        if paths:
            note["image_paths"] = paths

    md = renderer.render_report(note, script, comments)
    report = out_dir / "report.md"
    report.write_text(md, encoding="utf-8")
    print(f"\nOK {report}")


# ---------------------------------------------------------------------------
# archive: bulk-archive published notes' body, images, and tags (public-page parsing, no login)
# ---------------------------------------------------------------------------

async def run_archive(input_path: Path, output_root: Path, limit: int | None = None,
                      max_comments: int = 0) -> None:
    global LOG_FILE
    output_root.mkdir(parents=True, exist_ok=True)
    log_path = output_root / f"archive_{time.strftime('%Y%m%d_%H%M%S')}.log"
    LOG_FILE = open(log_path, "w", encoding="utf-8", errors="replace")
    try:
        _log(f"Starting archive: input={input_path}, output={output_root}")

        notes = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(notes, list):
            raise ValueError("input JSON must be a list of notes")

        notes = sorted(notes, key=lambda x: x.get("time", ""), reverse=True)
        if limit:
            notes = notes[:limit]

        results: list[dict] = []
        for i, note in enumerate(notes, 1):
            note_id = note.get("id") or note.get("note_id")
            xsec = note.get("xsecToken") or note.get("xsec_token", "")
            title = note.get("title", "")
            if not note_id or not xsec:
                results.append({
                    "success": False,
                    "note_id": note_id,
                    "error": "missing note_id or xsec_token",
                })
                continue

            out_dir = output_root / note_id
            _log(f"({i}/{len(notes)}) Archiving {note_id} {title[:30]}...")
            try:
                public = await asyncio.to_thread(crawler.fetch_public_note, note_id, xsec)
                if not public.get("success"):
                    err = public.get("error", "public-page parsing failed")
                    _log(f"  -> failed: {err}")
                    results.append({"success": False, "note_id": note_id, "error": err})
                    continue

                if max_comments > 0:
                    comments = await asyncio.to_thread(
                        crawler.fetch_public_comments, note_id, xsec, max_comments
                    )
                    public["comments"] = comments
                    public["comments_fetched"] = len(comments)

                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "note_detail.json").write_text(
                    json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8"
                )

                img_dir = out_dir / "images"
                img_dir.mkdir(parents=True, exist_ok=True)
                img_count = 0
                for idx, url in enumerate(public.get("images", []), 1):
                    if await crawler.download_image(url, img_dir / f"{idx:02d}"):
                        img_count += 1

                summary = {
                    "success": True,
                    "note_id": note_id,
                    "output_dir": str(out_dir),
                    "image_count": img_count,
                    "comment_count": public.get("comments_fetched", 0),
                }
                _log(f"  -> done: {img_count} images")
                results.append(summary)
            except Exception as e:
                _log(f"  -> exception: {e}")
                results.append({"success": False, "note_id": note_id, "error": str(e)})

            if i < len(notes):
                await asyncio.sleep(0.5)

        summary_path = output_root / f"archive_summary_{time.strftime('%Y%m%d_%H%M%S')}.json"
        summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        success = sum(1 for r in results if r.get("success"))
        _log(f"Done: {success} succeeded, {len(results) - success} failed, {len(results)} total")
        _log(f"Summary: {summary_path}")
    finally:
        if LOG_FILE is not None:
            LOG_FILE.close()
            LOG_FILE = None


# ---------------------------------------------------------------------------
# summarize: account-level summary (based on the creator center's latest notes + public-page tags)
# ---------------------------------------------------------------------------

def _series_of(note: dict) -> str:
    """Group notes into series by tag/title keyword; a simple fallback."""
    tags = note.get("tags") or []
    if tags:
        return tags[0]
    title = note.get("title", "")
    # Common series keywords (extendable)
    for kw in ("Agent", "RAG", "CS336", "Lec", "MCP", "LLM"):
        if kw.lower() in title.lower():
            return kw
    return "Other"


def _summarize(notes: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# xhs-explore account summary\n")
    lines.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Sample size: {len(notes)} notes\n")

    total_view = sum(n.get("view_count", 0) or 0 for n in notes)
    total_like = sum(n.get("like_count", 0) or 0 for n in notes)
    total_collect = sum(n.get("collect_count", 0) or 0 for n in notes)
    total_comment = sum(n.get("comment_count", 0) or 0 for n in notes)
    lines.append("## Overall data\n")
    lines.append(f"- Total views: {total_view:,}")
    lines.append(f"- Total likes: {total_like:,}")
    lines.append(f"- Total saves: {total_collect:,}")
    lines.append(f"- Total comments: {total_comment:,}")
    if total_view:
        lines.append(f"- Average like-to-view ratio: {total_like / total_view * 100:.2f}%")
        lines.append(f"- Average save-to-view ratio: {total_collect / total_view * 100:.2f}%")
    lines.append("")

    # Top 10 by views
    sorted_notes = sorted(notes, key=lambda x: x.get("view_count", 0) or 0, reverse=True)[:10]
    lines.append("## Views top 10\n")
    lines.append("| Rank | Title | Views | Likes | Saves | Comments |")
    lines.append("|------|------|------|------|------|------|")
    for idx, n in enumerate(sorted_notes, 1):
        title = (n.get("title") or "")[:30]
        lines.append(
            f"| {idx} | {title} | {n.get('view_count', 0):,} | "
            f"{n.get('like_count', 0)} | {n.get('collect_count', 0)} | {n.get('comment_count', 0)} |"
        )
    lines.append("")

    # Series summary
    series: dict[str, list[dict]] = defaultdict(list)
    for n in notes:
        series[_series_of(n)].append(n)
    lines.append("## Series summary (by first tag / title keyword)\n")
    lines.append("| Series | Notes | Total views | Avg views | Like rate | Save rate | Comment rate |")
    lines.append("|------|------|--------|--------|--------|--------|--------|")
    for name, items in sorted(series.items(), key=lambda x: sum(i.get("view_count", 0) or 0 for i in x[1]), reverse=True):
        views = sum(i.get("view_count", 0) or 0 for i in items)
        likes = sum(i.get("like_count", 0) or 0 for i in items)
        collects = sum(i.get("collect_count", 0) or 0 for i in items)
        comments = sum(i.get("comment_count", 0) or 0 for i in items)
        avg_view = views / len(items) if items else 0
        like_rate = likes / views * 100 if views else 0
        collect_rate = collects / views * 100 if views else 0
        comment_rate = comments / views * 100 if views else 0
        lines.append(
            f"| {name} | {len(items)} | {views:,} | {avg_view:.0f} | "
            f"{like_rate:.2f}% | {collect_rate:.2f}% | {comment_rate:.2f}% |"
        )
    lines.append("")

    lines.append(
        "> Tip: series assignment prefers the public-page tag; without a tag it falls back to title keywords."
        "Run `review.py archive` to bulk-archive, then calibrate manually.\n"
    )
    return "\n".join(lines)


async def run_summarize(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    print("[summarize] Pulling the creator center's latest 50 notes...")
    # summarize is a batch background command; use headless to avoid popup windows
    sess = await crawler.Session.open(headless=True)
    try:
        notes = await crawler.fetch_recent_notes(sess, limit=50)
    finally:
        await sess.close()

    # Fill in tags/body/images from the public page (a failure does not block)
    for n in notes:
        xsec = n.get("xsec_token") or ""
        if not xsec:
            continue
        try:
            public = await asyncio.to_thread(crawler.fetch_public_note, n["note_id"], xsec)
            crawler._merge_public_note(n, public)
        except Exception:
            pass

    md = _summarize(notes)
    out_path = out_dir / f"xhs_summary_{time.strftime('%Y%m%d_%H%M%S')}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"\nOK {out_path}")


def _usage() -> str:
    return """
Usage:
  python review.py                       interactive note picker
  python review.py login                 scan the QR code to log in
  python review.py list                  list recent notes
  python review.py note <note_id> [script.txt]
  python review.py archive <notes.json> [output_root] [limit]
  python review.py summarize [out_dir]
""".strip()


def main() -> None:
    # Windows Git Bash etc. default to a GBK console where emoji/Chinese print crashes; force UTF-8 output
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) > 1 and sys.argv[1] == "login":
        asyncio.run(crawler.ensure_login())
        return
    if len(sys.argv) > 1 and sys.argv[1] == "note":
        if len(sys.argv) < 3:
            print("Usage: python review.py note <note_id> [script.txt]")
            sys.exit(2)
        note_id = sys.argv[2]
        script_path = sys.argv[3] if len(sys.argv) > 3 else None
        asyncio.run(run_with_id(note_id, script_path))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        async def _list() -> None:
            sess = await crawler.Session.open()
            try:
                notes = await crawler.fetch_recent_notes(sess, limit=20)
            finally:
                await sess.close()
            for i, n in enumerate(notes):
                t = renderer._fmt_time(n.get("create_time", 0))
                title = (n.get("title") or "").replace("\n", " ")[:50]
                print(f"[{i}] {n['note_id']}  {t}  impressions {renderer._fmt_num(n.get('view_count'))}  {title}")
        asyncio.run(_list())
        return
    if len(sys.argv) > 1 and sys.argv[1] == "archive":
        if len(sys.argv) < 3:
            print(_usage())
            sys.exit(2)
        input_path = Path(sys.argv[2].strip('"').strip("'")).expanduser().resolve()
        output_root = Path(sys.argv[3]).expanduser().resolve() if len(sys.argv) > 3 else runtime_project_root() / "data" / "raw" / "notes" / "archive"
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
        asyncio.run(run_archive(input_path, output_root, limit=limit))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "summarize":
        out_dir = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else runtime_project_root() / "reports"
        asyncio.run(run_summarize(out_dir))
        return
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(_usage())
        return
    asyncio.run(run())


if __name__ == "__main__":
    main()
