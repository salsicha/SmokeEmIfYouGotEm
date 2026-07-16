"""Generate the B2 source-binary storage decision packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_source_storage_decision import (
    build_b2_source_storage_decision,
    write_b2_source_storage_decision,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_source_storage_decision(args.repo_root)
    payload = build_b2_source_storage_decision()
    print(f"decision_packet={output_path}")
    print(f"schema={payload['schema']}")
    print(f"mode={payload['current_operating_mode']['mode']}")
    print(f"downloads_allowed_now={payload['current_operating_mode']['downloads_allowed_now']}")
    print(f"cc0_task_decision_count={len(payload['cc0_task_decision_requirements'])}")


if __name__ == "__main__":
    main()
