"""Generate the Futaleufu A4 stationing and flow status artifact."""

from pathlib import Path

from raftsim.futaleufu_a4_status import (
    build_futaleufu_a4_stationing_flow_status,
    write_futaleufu_a4_stationing_flow_status,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    path = write_futaleufu_a4_stationing_flow_status(repo_root)
    payload = build_futaleufu_a4_stationing_flow_status(repo_root)
    print(path.relative_to(repo_root))
    print(payload["status"])
    print(f"rapid_count={payload['catalog_stationing_scaffold']['rapid_count']}")
