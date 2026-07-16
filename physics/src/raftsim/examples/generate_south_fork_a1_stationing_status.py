"""Generate the South Fork A1 stationing repair status artifact."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_stationing import (
    build_south_fork_a1_stationing_repair_status,
    write_south_fork_a1_stationing_repair_status,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_stationing_repair_status(repo_root)
    payload = build_south_fork_a1_stationing_repair_status(repo_root)
    print(f"status={payload['status']}")
    print(f"rapid_count={payload['catalog_stationing_scaffold']['rapid_count']}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
