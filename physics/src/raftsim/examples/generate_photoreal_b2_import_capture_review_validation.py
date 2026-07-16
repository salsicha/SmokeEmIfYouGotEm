"""Generate the B2 import/capture/review validation report."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_import_capture_review import (
    build_b2_import_capture_review_validation_report,
    write_b2_import_capture_review_validation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_import_capture_review_validation_report(args.repo_root)
    payload = build_b2_import_capture_review_validation_report()
    print(f"validation_report={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"import_reviews_valid={payload['import_reviews_valid']}")
    print(f"validation_error_count={payload['validation_error_count']}")
    print(f"can_mark_any_source_reviewed={payload['promotion_gate']['can_mark_any_source_reviewed']}")


if __name__ == "__main__":
    main()
