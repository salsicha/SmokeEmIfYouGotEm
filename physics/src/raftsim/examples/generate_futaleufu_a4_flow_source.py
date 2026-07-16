"""Generate Futaleufu A4 flow-source review artifacts."""

from pathlib import Path

from raftsim.futaleufu_a4_flow_source import (
    build_futaleufu_a4_flow_source_review_packet,
    write_futaleufu_a4_flow_source_result_template,
    write_futaleufu_a4_flow_source_review_packet,
    write_futaleufu_a4_flow_source_validation_report,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_futaleufu_a4_flow_source_review_packet(repo_root),
        write_futaleufu_a4_flow_source_result_template(repo_root),
        write_futaleufu_a4_flow_source_validation_report(repo_root),
    ]
    packet = build_futaleufu_a4_flow_source_review_packet(repo_root)
    for path in paths:
        print(path.relative_to(repo_root))
    print(packet["status"])
    print(f"flow_band_count={packet['flow_band_count']}")
