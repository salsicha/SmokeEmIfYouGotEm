"""Generate Milestone 19 Unreal Chaos automation fixture artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone19 import write_chaos_automation_export


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json"),
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path("unreal/Content/RaftSim/Physics/chaos_automation_fixtures.json"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("physics/reports/milestone19/chaos"),
    )
    args = parser.parse_args(argv)

    export = write_chaos_automation_export(
        contract_path=args.contract,
        manifest_path=args.manifest_output,
        report_dir=args.report_dir,
    )
    print(f"manifest={args.manifest_output}")
    print(f"summary={args.report_dir / 'summary.json'}")
    print(f"replay_summaries={len(export.replays)}")
    print(f"decision={export.summary['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
