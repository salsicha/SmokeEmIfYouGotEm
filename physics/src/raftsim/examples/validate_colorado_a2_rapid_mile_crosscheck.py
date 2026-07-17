"""Validate a filled Colorado A2 major-rapid mile cross-check payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.colorado_a2_rapid_mile_crosscheck import (
    build_colorado_a2_rapid_mile_crosscheck_validation_report,
    write_colorado_a2_rapid_mile_crosscheck_template,
    write_colorado_a2_rapid_mile_crosscheck_validation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--crosscheck",
        type=Path,
        default=None,
        help="Filled Colorado A2 major-rapid mile cross-check JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Accepted rapid-mile cross-check output path, written only when valid.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Validation report output path.",
    )
    args = parser.parse_args(argv)

    if args.crosscheck is None:
        template_path = write_colorado_a2_rapid_mile_crosscheck_template(args.repo_root)
        report_path = write_colorado_a2_rapid_mile_crosscheck_validation_report(
            args.repo_root
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"rapid_mile_crosscheck_template={template_path}")
        print(f"validation_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(f"crosscheck_valid={report['crosscheck_valid']}")
        print(f"validation_error_count={report['validation_error_count']}")
        return 0

    crosscheck_payload = _load_json_object(args.crosscheck)
    report = build_colorado_a2_rapid_mile_crosscheck_validation_report(
        args.repo_root,
        crosscheck_payload,
    )
    report_path = args.report or args.crosscheck.with_suffix(".validation_report.json")
    _write_json(report_path, report)

    print(f"validation_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"crosscheck_valid={report['crosscheck_valid']}")
    print(f"validation_error_count={report['validation_error_count']}")

    if not report["crosscheck_valid"]:
        return 1

    output_path = args.output or args.crosscheck.with_suffix(
        ".accepted_rapid_mile_crosscheck.json"
    )
    _write_json(output_path, crosscheck_payload)
    print(f"accepted_rapid_mile_crosscheck={output_path}")
    print(f"passing_rapid_count={report['passing_rapid_count']}")
    print(
        "can_restation_major_rapids="
        f"{report['promotion_permissions']['can_restation_major_rapids']}"
    )
    print(
        "can_bind_solver_windows="
        f"{report['promotion_permissions']['can_bind_solver_windows']}"
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
