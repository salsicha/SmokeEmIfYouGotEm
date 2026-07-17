"""Validate a filled Colorado A2 centerline/CRS decision payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.colorado_a2_centerline_decision import (
    build_colorado_a2_centerline_decision_validation_report,
    write_colorado_a2_centerline_decision_template,
    write_colorado_a2_centerline_decision_validation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--decision",
        type=Path,
        default=None,
        help="Filled Colorado A2 centerline/CRS decision JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Accepted decision output path, written only when valid.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Validation report output path.",
    )
    args = parser.parse_args(argv)

    if args.decision is None:
        template_path = write_colorado_a2_centerline_decision_template(args.repo_root)
        report_path = write_colorado_a2_centerline_decision_validation_report(
            args.repo_root
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"centerline_decision_template={template_path}")
        print(f"validation_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(f"decision_valid={report['decision_valid']}")
        print(f"validation_error_count={report['validation_error_count']}")
        return 0

    decision_payload = _load_json_object(args.decision)
    report = build_colorado_a2_centerline_decision_validation_report(
        args.repo_root,
        decision_payload,
    )
    report_path = args.report or args.decision.with_suffix(".validation_report.json")
    _write_json(report_path, report)

    print(f"validation_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"decision_valid={report['decision_valid']}")
    print(f"validation_error_count={report['validation_error_count']}")

    if not report["decision_valid"]:
        return 1

    output_path = args.output or args.decision.with_suffix(
        ".accepted_centerline_decision.json"
    )
    _write_json(output_path, decision_payload)
    print(f"accepted_centerline_decision={output_path}")
    print(
        "can_generate_source_window_bboxes="
        f"{report['regeneration_permissions']['can_generate_source_window_bboxes']}"
    )
    print(
        "can_bind_solver_windows="
        f"{report['regeneration_permissions']['can_bind_solver_windows']}"
    )
    return 0


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
