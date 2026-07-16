"""Generate Futaleufu A4 rapid digitizing work-window artifacts."""

from pathlib import Path

from raftsim.futaleufu_a4_digitizing_windows import (
    build_futaleufu_a4_digitizing_work_window_manifest,
    write_futaleufu_a4_digitizing_work_window_manifest,
    write_futaleufu_a4_digitizing_work_windows_geojson,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_futaleufu_a4_digitizing_work_windows_geojson(repo_root),
        write_futaleufu_a4_digitizing_work_window_manifest(repo_root),
    ]
    manifest = build_futaleufu_a4_digitizing_work_window_manifest(repo_root)
    for path in paths:
        print(path.relative_to(repo_root))
    print(manifest["status"])
    print(f"rapid_count={manifest['rapid_count']}")
