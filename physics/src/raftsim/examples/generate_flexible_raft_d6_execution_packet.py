"""Generate the D6 external-engine execution packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d6_execution_packet import (
    build_flexible_raft_d6_execution_packet,
    write_flexible_raft_d6_execution_packet,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_flexible_raft_d6_execution_packet(args.repo_root)
    payload = build_flexible_raft_d6_execution_packet()
    print(f"execution_packet={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"execution_job_count={payload['summary']['execution_job_count']}")
    print(f"pending_external_job_count={payload['summary']['pending_external_job_count']}")
    print(f"d6_complete={payload['d6_complete']}")


if __name__ == "__main__":
    main()
