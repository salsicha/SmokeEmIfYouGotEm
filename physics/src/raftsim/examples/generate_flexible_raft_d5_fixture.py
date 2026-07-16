"""Generate the D5 flexible-raft telemetry/replay fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d5 import (
    build_flexible_raft_d5_fixture,
    write_flexible_raft_d5_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_flexible_raft_d5_fixture(args.repo_root)
    payload = build_flexible_raft_d5_fixture()
    print(f"fixture={output_path}")
    print(f"schema={payload['schema']}")
    print(f"frame_count={payload['frame_count']}")
    print(f"replay_sha256={payload['replay_sha256']}")


if __name__ == "__main__":
    main()
