"""Generate Pacuare A3 stationing digitizing artifacts."""

from pathlib import Path

from raftsim.pacuare_a3_digitizing import (
    build_pacuare_a3_digitizing_action_packet,
    write_pacuare_a3_digitizing_action_packet,
    write_pacuare_a3_digitizing_result_template,
    write_pacuare_a3_digitizing_validation_report,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        write_pacuare_a3_digitizing_action_packet(repo_root),
        write_pacuare_a3_digitizing_result_template(repo_root),
        write_pacuare_a3_digitizing_validation_report(repo_root),
    ]
    packet = build_pacuare_a3_digitizing_action_packet(repo_root)
    for path in paths:
        print(path.relative_to(repo_root))
    print(packet["status"])
    print(f"rapid_count={packet['rapid_count']}")
