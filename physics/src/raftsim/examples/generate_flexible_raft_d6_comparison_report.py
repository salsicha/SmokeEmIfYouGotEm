"""Generate the pending D6 measured-result comparison report."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    build_flexible_raft_d6_comparison_report,
    write_flexible_raft_d6_comparison_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_flexible_raft_d6_comparison_report(args.repo_root)
    payload = build_flexible_raft_d6_comparison_report()
    print(f"report={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"missing_target_count={payload['missing_target_count']}")
    print(f"d6_complete={payload['d6_complete']}")


if __name__ == "__main__":
    main()
