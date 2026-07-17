"""Generate Chilko A5 rapid-stationing digitizing work-window artifacts."""

from __future__ import annotations

from pathlib import Path

from raftsim.chilko_a5_digitizing_windows import (
    build_chilko_a5_digitizing_work_window_manifest,
    write_chilko_a5_digitizing_work_window_manifest,
    write_chilko_a5_digitizing_work_windows_geojson,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_chilko_a5_digitizing_work_windows_geojson(repo_root),
        write_chilko_a5_digitizing_work_window_manifest(repo_root),
    ]
    manifest = build_chilko_a5_digitizing_work_window_manifest(repo_root)
    for path in paths:
        print(f"wrote={path.relative_to(repo_root)}")
    print(f"rapid_count={manifest['rapid_count']}")
    print(f"status={manifest['status']}")
    print(f"production_promoted={manifest['production_promoted']}")


if __name__ == "__main__":
    main()
