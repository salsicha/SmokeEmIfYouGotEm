"""Generate the B2 import/capture/review ledger."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_import_capture_review import (
    build_b2_import_capture_review_ledger,
    write_b2_import_capture_review_ledger,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_import_capture_review_ledger(args.repo_root)
    payload = build_b2_import_capture_review_ledger()
    summary = payload["summary"]
    print(f"import_capture_review_ledger={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"import_review_record_count={summary['import_review_record_count']}")
    print(f"can_run_any_import_now={summary['can_run_any_import_now']}")


if __name__ == "__main__":
    main()
