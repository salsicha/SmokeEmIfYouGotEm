"""Generate Chilko A5 flow-window review artifacts."""

from __future__ import annotations

from pathlib import Path

from raftsim.chilko_a5_flow_source import (
    build_chilko_a5_flow_source_review_packet,
    write_chilko_a5_flow_source_result_template,
    write_chilko_a5_flow_source_review_packet,
    write_chilko_a5_flow_source_validation_report,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_chilko_a5_flow_source_review_packet(repo_root),
        write_chilko_a5_flow_source_result_template(repo_root),
        write_chilko_a5_flow_source_validation_report(repo_root),
    ]
    packet = build_chilko_a5_flow_source_review_packet(repo_root)
    for path in paths:
        print(f"wrote={path.relative_to(repo_root)}")
    print(f"flow_window_count={packet['flow_window_count']}")
    print(f"status={packet['status']}")
    print(f"production_promoted={packet['production_promoted']}")


if __name__ == "__main__":
    main()
