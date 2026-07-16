"""Generate the D6 external-engine fixture input package."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    build_flexible_raft_d6_fixture_input_package,
    write_flexible_raft_d6_fixture_input_package,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_flexible_raft_d6_fixture_input_package(args.repo_root)
    payload = build_flexible_raft_d6_fixture_input_package()
    print(f"fixture_inputs={output_path}")
    print(f"schema={payload['schema']}")
    print(f"fixture_count={payload['fixture_count']}")
    print(f"measurement_task_count={payload['measurement_task_count']}")
    print(f"d6_complete={payload['d6_complete']}")


if __name__ == "__main__":
    main()
