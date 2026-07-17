"""Generate the B2 source-acquisition execution plan."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_execution import (
    build_b2_source_acquisition_execution_plan,
    write_b2_source_acquisition_execution_plan,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_source_acquisition_execution_plan(args.repo_root)
    payload = build_b2_source_acquisition_execution_plan()
    print(f"artifact={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(
        "storage_decision_valid="
        f"{payload['storage_decision']['storage_decision_valid']}"
    )
    print(f"cc0_task_count={payload['summary']['cc0_task_count']}")
    print(f"executable_task_count={payload['summary']['executable_task_count']}")


if __name__ == "__main__":
    main()
