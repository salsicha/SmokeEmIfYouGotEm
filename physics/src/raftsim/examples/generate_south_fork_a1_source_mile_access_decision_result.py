"""Generate the South Fork A1 source-mile/access decision result template."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_decision_result import (
    build_south_fork_a1_source_mile_access_decision_result_template,
    write_south_fork_a1_source_mile_access_decision_result_template,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_source_mile_access_decision_result_template(
        args.repo_root
    )
    payload = build_south_fork_a1_source_mile_access_decision_result_template(
        args.repo_root
    )
    print(f"decision_result_template={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"allowed_option_count={len(payload['allowed_option_ids'])}")
    print(f"can_bind_solver_windows={payload['promotion_gate']['can_bind_solver_windows']}")


if __name__ == "__main__":
    main()
