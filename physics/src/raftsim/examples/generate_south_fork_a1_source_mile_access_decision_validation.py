"""Generate the South Fork A1 source-mile/access decision validation report."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_decision_result import (
    build_south_fork_a1_source_mile_access_decision_validation_report,
    write_south_fork_a1_source_mile_access_decision_validation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_source_mile_access_decision_validation_report(
        args.repo_root
    )
    payload = build_south_fork_a1_source_mile_access_decision_validation_report(
        args.repo_root
    )
    print(f"validation_report={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"decision_valid={payload['decision_valid']}")
    print(f"validation_error_count={payload['validation_error_count']}")
    print(f"can_bind_solver_windows={payload['regeneration_permissions']['can_bind_solver_windows']}")


if __name__ == "__main__":
    main()
