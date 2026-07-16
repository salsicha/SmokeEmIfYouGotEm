"""Generate the D2 flexible-raft seat-load reference fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d2 import (
    build_seat_load_coupled_tube_d2_fixture,
    write_seat_load_coupled_tube_d2_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_seat_load_coupled_tube_d2_fixture(args.repo_root)
    payload = build_seat_load_coupled_tube_d2_fixture()
    print(f"fixture={output_path}")
    print(f"schema={payload['schema']}")
    print(f"case_count={len(payload['cases'])}")
    print(f"scoring_authority_enabled={payload['scoring_authority_enabled']}")


if __name__ == "__main__":
    main()
