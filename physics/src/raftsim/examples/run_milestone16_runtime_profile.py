"""Profile promoted Milestone 16 C++ configs against runtime budgets."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone16 import run_milestone16_runtime_profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("regression_fixtures/milestone16/registry.json"))
    parser.add_argument("--cpp-solver", type=Path, required=True)
    parser.add_argument("--budget-config", type=Path, default=Path("config/runtime_budgets.json"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/m16profile"))
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/milestone16"))
    args = parser.parse_args(argv)

    report = run_milestone16_runtime_profile(
        args.registry,
        cpp_solver=args.cpp_solver,
        budget_config=args.budget_config,
        output_root=args.output_root,
        repetitions=args.repetitions,
    )
    json_path = report.write_json(args.report_dir / "runtime_profile.json")
    markdown_path = report.write_markdown(args.report_dir / "runtime_profile.md")
    print(f"report={json_path}")
    print(f"markdown={markdown_path}")
    print(f"runs={len(report.records)}")
    print(f"passed={report.passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
