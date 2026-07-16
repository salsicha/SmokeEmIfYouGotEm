"""Generate the Pacuare A3 stationing repair status artifact."""

from pathlib import Path

from raftsim.pacuare_a3_stationing import (
    build_pacuare_a3_stationing_repair_status,
    write_pacuare_a3_stationing_repair_status,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    path = write_pacuare_a3_stationing_repair_status(repo_root)
    payload = build_pacuare_a3_stationing_repair_status(repo_root)
    print(path.relative_to(repo_root))
    print(payload["status"])
    print(f"rapid_count={payload['catalog_stationing_scaffold']['rapid_count']}")
