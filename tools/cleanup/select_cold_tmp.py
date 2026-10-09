"""List tmp/ run folders that can leave the project drive.

A folder is cold when it was last modified more than --days ago and nothing
current refers to it: not the current section of docs/plans/remaining-work.md
(above "## Historical checkpoint log"), the other plan documents, the
project's scripts, or .claude/launch.json. Folders whose names suggest source
data (terrain, LiDAR, canopy, imagery, surveys...) are never selected, and of
the packaged game builds (folders holding .pak files) the newest is kept.

Prints one folder name per line, largest-first is not attempted (sizes are
left to the archiver); --summary adds counts to stderr.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIKE = re.compile(
    r"terrain|tile|landscape|import|dem|lidar|bathy|vegetation|foliage|canopy|laz|ept|naip|deps|source|survey|geospatial",
    re.IGNORECASE)
REFERENCE = re.compile(r"tmp[/\\]([A-Za-z0-9._-]+)")


def current_references():
    texts = []
    plan = ROOT / "docs" / "plans" / "remaining-work.md"
    if plan.exists():
        current = plan.read_text(encoding="utf-8", errors="replace").split("## Historical checkpoint log", 1)[0]
        texts.append(current)
    for path in (ROOT / "docs" / "plans").glob("*.md"):
        if path.name != "remaining-work.md":
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
    for folder, patterns in ((ROOT / "unreal" / "Scripts", ("*.py", "*.ps1")),
                             (ROOT / "physics" / "scripts", ("*.py", "*.ps1")),
                             (ROOT / "tools", ("*.py", "*.ps1"))):
        for pattern in patterns:
            for path in folder.rglob(pattern):
                texts.append(path.read_text(encoding="utf-8", errors="replace"))
    launch = ROOT / ".claude" / "launch.json"
    if launch.exists():
        texts.append(launch.read_text(encoding="utf-8", errors="replace"))
    return {match for text in texts for match in REFERENCE.findall(text)}


def holds_pak(folder, depth=6):
    for current, dirs, files in os.walk(folder):
        if any(name.endswith(".pak") for name in files):
            return True
        if Path(current).relative_to(folder).parts.__len__() >= depth:
            dirs[:] = []
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=float, default=7.0)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    tmp = ROOT / "tmp"
    referenced = current_references()
    cutoff = time.time() - args.days * 86400.0
    folders = [entry for entry in os.scandir(tmp) if entry.is_dir(follow_symlinks=False)]
    builds = sorted((entry for entry in folders if holds_pak(entry.path)), key=lambda e: e.stat().st_mtime)
    newest_build = builds[-1].name if builds else None
    selected = []
    for entry in folders:
        name = entry.name
        if name == newest_build or name in referenced or SOURCE_LIKE.search(name):
            continue
        if entry.stat().st_mtime >= cutoff:
            continue
        selected.append(name)
    for name in sorted(selected):
        print(name)
    if args.summary:
        print(f"{len(selected)} cold of {len(folders)} tmp folders; newest build kept: {newest_build}; "
              f"{len(referenced)} referenced names", file=sys.stderr)


if __name__ == "__main__":
    main()
