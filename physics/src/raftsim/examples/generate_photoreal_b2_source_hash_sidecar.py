"""Generate the B2 source-hash sidecar template and merge report."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_b2_source_hash_sidecar import (
    build_b2_source_hash_sidecar_merge_report,
    write_b2_source_hash_sidecar_merge_report,
    write_b2_source_hash_sidecar_template,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_b2_source_hash_sidecar_template(repo_root),
        write_b2_source_hash_sidecar_merge_report(repo_root),
    ]
    report = build_b2_source_hash_sidecar_merge_report()
    for path in paths:
        print(f"wrote={path.relative_to(repo_root)}")
    print(f"status={report['status']}")
    print(f"sidecar_record_count={report['sidecar_record_count']}")
    print(f"production_promoted={report['production_promoted']}")


if __name__ == "__main__":
    main()
