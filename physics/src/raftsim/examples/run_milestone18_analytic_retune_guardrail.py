"""Run Milestone 17 analytic fixtures as a Milestone 18 retune guardrail."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import run_milestone18_analytic_retune_guardrail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/validation/milestone17/analytic_fixtures/manifest.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("reports/milestone18/analytic_retune_guardrails"))
    parser.add_argument("--retune-batch-id", default="baseline_scenario_guardrail")
    parser.add_argument("--preflight-candidate-kind", choices=("scenario", "cpp", "geoclaw", "reference"), default="scenario")
    parser.add_argument("--preflight-candidate-root", type=Path, default=None)
    parser.add_argument("--preflight-candidate-label", default=None)
    parser.add_argument("--preflight-frame-index", type=int, default=0)
    parser.add_argument("--postflight-candidate-kind", choices=("scenario", "cpp", "geoclaw", "reference"), default="scenario")
    parser.add_argument("--postflight-candidate-root", type=Path, default=None)
    parser.add_argument("--postflight-candidate-label", default=None)
    parser.add_argument("--postflight-frame-index", type=int, default=0)
    args = parser.parse_args(argv)

    report = run_milestone18_analytic_retune_guardrail(
        args.manifest,
        args.output_dir,
        retune_batch_id=args.retune_batch_id,
        preflight_candidate_kind=args.preflight_candidate_kind,
        preflight_candidate_root=args.preflight_candidate_root,
        preflight_candidate_label=args.preflight_candidate_label,
        preflight_frame_index=args.preflight_frame_index,
        postflight_candidate_kind=args.postflight_candidate_kind,
        postflight_candidate_root=args.postflight_candidate_root,
        postflight_candidate_label=args.postflight_candidate_label,
        postflight_frame_index=args.postflight_frame_index,
    )
    root = Path(report.output_dir)
    json_path = report.write_json(root / "analytic_retune_guardrail.json")
    markdown_path = report.write_markdown(root / "analytic_retune_guardrail.md")
    print(f"guardrail={json_path}")
    print(f"markdown={markdown_path}")
    print(f"decision={'PASS' if report.passed else 'BLOCKED'}")
    print(f"regressions={len(report.regressions)}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
