"""Generate the B2 local source hash report template."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_source_hash_report import (
    build_b2_source_hash_report_template,
    write_b2_source_hash_report_template,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_source_hash_report_template(args.repo_root)
    payload = build_b2_source_hash_report_template()
    summary = payload["summary"]
    print(f"hash_report_template={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"required_hash_record_count={summary['required_hash_record_count']}")
    print(f"filled_hash_record_count={summary['filled_hash_record_count']}")
    print(f"can_promote_any_b2_asset_set={summary['can_promote_any_b2_asset_set']}")


if __name__ == "__main__":
    main()
