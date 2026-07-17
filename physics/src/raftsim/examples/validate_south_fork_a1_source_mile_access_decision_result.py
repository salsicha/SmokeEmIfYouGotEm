"""Validate a filled South Fork A1 source-mile/access decision result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.south_fork_a1_source_mile_access_decision_result import (
    build_south_fork_a1_source_mile_access_decision_validation_report,
    write_south_fork_a1_source_mile_access_decision_result_template,
    write_south_fork_a1_source_mile_access_decision_validation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--decision-result",
        type=Path,
        default=None,
        help="Filled South Fork A1 source-mile/access decision-result JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Accepted decision-result output path, written only when valid.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Validation report output path.",
    )
    args = parser.parse_args(argv)

    if args.decision_result is None:
        template_path = write_south_fork_a1_source_mile_access_decision_result_template(
            args.repo_root
        )
        report_path = write_south_fork_a1_source_mile_access_decision_validation_report(
            args.repo_root
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"decision_result_template={template_path}")
        print(f"validation_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(f"decision_valid={report['decision_valid']}")
        print(f"validation_error_count={report['validation_error_count']}")
        return 0

    decision_result_payload = _load_json_object(args.decision_result)
    report = build_south_fork_a1_source_mile_access_decision_validation_report(
        args.repo_root,
        decision_result_payload,
    )
    report_path = args.report or args.decision_result.with_suffix(
        ".validation_report.json"
    )
    _write_json(report_path, report)

    print(f"validation_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"decision_valid={report['decision_valid']}")
    print(f"validation_error_count={report['validation_error_count']}")

    if not report["decision_valid"]:
        return 1

    output_path = args.output or args.decision_result.with_suffix(
        ".accepted_decision_result.json"
    )
    _write_json(output_path, decision_result_payload)
    print(f"accepted_decision_result={output_path}")
    print(
        "can_regenerate_directed_route="
        f"{report['regeneration_permissions']['can_regenerate_directed_route']}"
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
