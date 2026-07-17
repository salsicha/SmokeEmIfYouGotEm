"""Validate a filled Futaleufu A4 rapid-stationing digitizing result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.futaleufu_a4_digitizing import (
    build_futaleufu_a4_digitizing_validation_report,
    write_futaleufu_a4_digitizing_action_packet,
    write_futaleufu_a4_digitizing_result_template,
    write_futaleufu_a4_digitizing_validation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--result",
        type=Path,
        default=None,
        help="Filled Futaleufu A4 rapid-stationing digitizing result JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Accepted digitizing result output path, written only when valid.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Validation report output path.",
    )
    args = parser.parse_args(argv)

    if args.result is None:
        packet_path = write_futaleufu_a4_digitizing_action_packet(args.repo_root)
        template_path = write_futaleufu_a4_digitizing_result_template(args.repo_root)
        report_path = write_futaleufu_a4_digitizing_validation_report(args.repo_root)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"digitizing_action_packet={packet_path}")
        print(f"digitizing_result_template={template_path}")
        print(f"validation_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(f"digitizing_valid={report['digitizing_valid']}")
        print(f"validation_error_count={report['validation_error_count']}")
        return 0

    result_payload = _load_json_object(args.result)
    report = build_futaleufu_a4_digitizing_validation_report(
        args.repo_root,
        result_payload,
    )
    report_path = args.report or args.result.with_suffix(".validation_report.json")
    _write_json(report_path, report)

    print(f"validation_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"digitizing_valid={report['digitizing_valid']}")
    print(f"validation_error_count={report['validation_error_count']}")

    if not report["digitizing_valid"]:
        return 1

    output_path = args.output or args.result.with_suffix(
        ".accepted_digitizing_result.json"
    )
    _write_json(output_path, result_payload)
    print(f"accepted_digitizing_result={output_path}")
    print(f"passing_rapid_count={report['passing_rapid_count']}")
    print(
        "can_regenerate_named_rapid_catalog="
        f"{report['promotion_permissions']['can_regenerate_named_rapid_catalog']}"
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
