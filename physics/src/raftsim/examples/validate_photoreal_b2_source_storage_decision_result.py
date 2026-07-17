"""Validate a filled B2 source-binary storage decision result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.photoreal_b2_source_storage_decision import (
    build_b2_source_storage_decision_validation_report,
    write_b2_source_storage_decision_result_template,
    write_b2_source_storage_decision,
    write_b2_source_storage_decision_validation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--result",
        type=Path,
        default=None,
        help="Filled B2 source-binary storage decision result JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Accepted storage decision result output path, written only when valid.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Validation report output path.",
    )
    args = parser.parse_args(argv)

    if args.result is None:
        packet_path = write_b2_source_storage_decision(args.repo_root)
        template_path = write_b2_source_storage_decision_result_template(args.repo_root)
        report_path = write_b2_source_storage_decision_validation_report(args.repo_root)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"source_storage_decision_packet={packet_path}")
        print(f"source_storage_decision_result_template={template_path}")
        print(f"validation_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(f"storage_decision_valid={report['storage_decision_valid']}")
        print(f"validation_error_count={report['validation_error_count']}")
        return 0

    result_payload = _load_json_object(args.result)
    report = build_b2_source_storage_decision_validation_report(result_payload)
    report_path = args.report or args.result.with_suffix(".validation_report.json")
    _write_json(report_path, report)

    print(f"validation_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"storage_decision_valid={report['storage_decision_valid']}")
    print(f"validation_error_count={report['validation_error_count']}")

    if not report["storage_decision_valid"]:
        return 1

    output_path = args.output or args.result.with_suffix(
        ".accepted_storage_decision_result.json"
    )
    _write_json(output_path, result_payload)
    print(f"accepted_storage_decision_result={output_path}")
    print(f"chosen_option_id={report['chosen_option_id']}")
    print(
        "can_enable_local_cc0_downloads="
        f"{report['promotion_permissions']['can_enable_local_cc0_downloads']}"
    )
    print(
        "can_commit_cc0_source_binaries="
        f"{report['promotion_permissions']['can_commit_cc0_source_binaries']}"
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
