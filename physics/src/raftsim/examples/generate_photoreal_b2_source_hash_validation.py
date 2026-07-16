"""Generate the B2 source hash validation report."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_source_hash_report import (
    build_b2_source_hash_validation_report,
    write_b2_source_hash_validation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_source_hash_validation_report(args.repo_root)
    payload = build_b2_source_hash_validation_report()
    print(f"validation_report={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"source_hashes_valid={payload['source_hashes_valid']}")
    print(f"validation_error_count={payload['validation_error_count']}")
    print(f"can_run_imports={payload['promotion_gate']['can_run_imports']}")


if __name__ == "__main__":
    main()
