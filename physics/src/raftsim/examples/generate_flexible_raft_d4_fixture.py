"""Generate the D4 flexible-raft rock contact/wrap/pin reference fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d4 import (
    build_rock_contact_wrap_pin_d4_fixture,
    write_rock_contact_wrap_pin_d4_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_rock_contact_wrap_pin_d4_fixture(args.repo_root)
    payload = build_rock_contact_wrap_pin_d4_fixture()
    print(f"fixture={output_path}")
    print(f"schema={payload['schema']}")
    print(f"case_count={len(payload['cases'])}")
    print(f"scoring_authority_enabled={payload['scoring_authority_enabled']}")


if __name__ == "__main__":
    main()
