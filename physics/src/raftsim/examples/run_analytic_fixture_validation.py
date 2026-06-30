"""Generate Milestone 17 analytic fixture validation reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..analytic_validation import compare_analytic_fixture_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/validation/milestone17/analytic_fixtures/manifest.json"),
    )
    parser.add_argument("--candidate-kind", choices=("scenario", "cpp", "geoclaw", "reference"), default="scenario")
    parser.add_argument("--candidate-root", type=Path, default=None)
    parser.add_argument("--candidate-label", default=None)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=Path("reports/milestone17/analytic_fixture_validation.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/milestone17/analytic_fixture_validation.md"))
    args = parser.parse_args(argv)

    report = compare_analytic_fixture_manifest(
        args.manifest,
        candidate_kind=args.candidate_kind,
        candidate_root=args.candidate_root,
        candidate_label=args.candidate_label,
        frame_index=args.frame_index,
    )
    report.write_json(args.output_json)
    report.write_markdown(args.output_md)
    print(f"json={args.output_json}")
    print(f"markdown={args.output_md}")
    print(f"passed={report.passed}")
    print(f"fixtures={len(report.comparisons)}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
