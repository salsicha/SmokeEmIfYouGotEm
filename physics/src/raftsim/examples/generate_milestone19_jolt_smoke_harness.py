"""Generate Milestone 19 native Jolt smoke harness artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone19 import write_jolt_smoke_harness_export


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
        default=Path("physics/cpp/tests/jolt_smoke_harness_manifest.json"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("physics/reports/milestone19/jolt"),
    )
    args = parser.parse_args(argv)

    export = write_jolt_smoke_harness_export(
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
