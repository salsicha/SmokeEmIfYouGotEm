"""Promote a passing dual-solver run to the regression fixture registry."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..regression import promote_passing_dual_solver_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dual_solver_run", type=Path)
    parser.add_argument("--regression-root", type=Path, default=Path("regression_fixtures"))
    parser.add_argument("--registry", type=Path, default=None)
    args = parser.parse_args(argv)

    result = promote_passing_dual_solver_run(
        args.dual_solver_run,
        regression_root=args.regression_root,
        registry_path=args.registry,
    )
    print(f"scenario_id={result.scenario_id}")
    print(f"fixture_dir={result.fixture_dir}")
    print(f"registry={result.registry_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
