"""Generate the D1 flexible-raft compliant-tube reference fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d1 import (
    build_compliant_tube_d1_fixture,
    write_compliant_tube_d1_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_compliant_tube_d1_fixture(args.repo_root)
    payload = build_compliant_tube_d1_fixture()
    print(f"fixture={output_path}")
    print(f"schema={payload['schema']}")
    print(f"case_count={len(payload['cases'])}")
    print(f"scoring_authority_enabled={payload['scoring_authority_enabled']}")


if __name__ == "__main__":
    main()
