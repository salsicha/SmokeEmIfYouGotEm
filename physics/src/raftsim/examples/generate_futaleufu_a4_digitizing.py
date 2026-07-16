"""Generate Futaleufu A4 stationing digitizing artifacts."""

from pathlib import Path

from raftsim.futaleufu_a4_digitizing import (
    build_futaleufu_a4_digitizing_action_packet,
    write_futaleufu_a4_digitizing_action_packet,
    write_futaleufu_a4_digitizing_result_template,
    write_futaleufu_a4_digitizing_validation_report,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_futaleufu_a4_digitizing_action_packet(repo_root),
        write_futaleufu_a4_digitizing_result_template(repo_root),
        write_futaleufu_a4_digitizing_validation_report(repo_root),
    ]
    packet = build_futaleufu_a4_digitizing_action_packet(repo_root)
    for path in paths:
        print(path.relative_to(repo_root))
    print(packet["status"])
    print(f"rapid_count={packet['rapid_count']}")
