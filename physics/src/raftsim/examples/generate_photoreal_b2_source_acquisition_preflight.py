"""Generate the B2 photoreal source-acquisition preflight queue."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_preflight import (
    build_b2_source_acquisition_preflight,
    write_b2_source_acquisition_preflight,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_source_acquisition_preflight(args.repo_root)
    payload = build_b2_source_acquisition_preflight()
    print(f"preflight={output_path}")
    print(f"schema={payload['schema']}")
    print(f"cc0_download_task_count={payload['cc0_download_task_count']}")
    print(f"fab_local_only_slot_count={payload['fab_local_only_slot_count']}")
    print(f"downloads_allowed_now={payload['execution_gate']['downloads_allowed_now']}")


if __name__ == "__main__":
    main()
