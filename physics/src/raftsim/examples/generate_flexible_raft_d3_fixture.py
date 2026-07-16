"""Generate the D3 flexible-raft overwash/flip reference fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d3 import (
    build_overwash_flip_d3_fixture,
    write_overwash_flip_d3_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_overwash_flip_d3_fixture(args.repo_root)
    payload = build_overwash_flip_d3_fixture()
    print(f"fixture={output_path}")
    print(f"schema={payload['schema']}")
    print(f"case_count={len(payload['cases'])}")
    print(f"scoring_authority_enabled={payload['scoring_authority_enabled']}")


if __name__ == "__main__":
    main()
