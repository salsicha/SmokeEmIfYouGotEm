"""Generate the Milestone 18 distinct pin/release fixture report."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_pin_release_fixture_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-id", default="midstream_wrap_pin_release")
    parser.add_argument("--obstruction-kind", default="midstream_wrap_rock")
    parser.add_argument("--station-m", type=float, default=42.0)
    parser.add_argument("--lateral-offset-m", type=float, default=0.85)
    parser.add_argument("--action-window-s", type=float, default=0.75)
    parser.add_argument("--feature-forcing-strength-scale", type=float, default=0.0)
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/pin_release_fixture.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/pin_release_fixture.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_pin_release_fixture_report(
        fixture_id=args.fixture_id,
        obstruction_kind=args.obstruction_kind,
        station_m=args.station_m,
        lateral_offset_m=args.lateral_offset_m,
        action_window_s=args.action_window_s,
        feature_forcing_strength_scale=args.feature_forcing_strength_scale,
        notes=tuple(args.note),
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"pin_release_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
