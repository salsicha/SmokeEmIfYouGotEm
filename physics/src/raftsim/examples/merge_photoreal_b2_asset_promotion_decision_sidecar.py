"""Validate and merge a B2 asset-promotion decision sidecar payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.photoreal_b2_asset_promotion_decision import (
    build_b2_asset_promotion_decision_validation_report,
)
from raftsim.photoreal_b2_asset_promotion_decision_sidecar import (
    B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS,
    build_b2_asset_promotion_decision_sidecar_merge_report,
    merge_b2_asset_promotion_decision_sidecar,
    write_b2_asset_promotion_decision_sidecar_merge_report,
    write_b2_asset_promotion_decision_sidecar_template,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=None,
        help="Filled B2 asset-promotion decision sidecar JSON to validate and merge.",
    )
    parser.add_argument(
        "--readiness",
        type=Path,
        default=None,
        help="Optional B2 asset-promotion readiness JSON to validate against.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Merged canonical B2 asset-promotion decision output path.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Sidecar validation/merge report output path.",
    )
    parser.add_argument(
        "--validation-report",
        type=Path,
        default=None,
        help="Canonical B2 asset-promotion decision validation output path.",
    )
    args = parser.parse_args(argv)

    if args.sidecar is None:
        template_path = write_b2_asset_promotion_decision_sidecar_template(
            args.repo_root
        )
        report_path = write_b2_asset_promotion_decision_sidecar_merge_report(
            args.repo_root
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"sidecar_template={template_path}")
        print(f"merge_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(
            "can_run_corridor_substitution="
            f"{report['promotion_permissions']['can_run_corridor_substitution']}"
        )
        return 0

    sidecar_payload = _load_json_object(args.sidecar)
    readiness_payload = _load_json_object(args.readiness) if args.readiness else None
    report = build_b2_asset_promotion_decision_sidecar_merge_report(
        sidecar_payload,
        readiness_payload,
    )
    report_path = args.report or args.sidecar.with_suffix(".merge_report.json")
    _write_json(report_path, report)

    print(f"merge_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"sidecar_error_count={report['sidecar_error_count']}")
    print(
        "merged_validation_error_count="
        f"{report['merged_validation']['validation_error_count']}"
    )

    if report["status"] != B2_ASSET_PROMOTION_DECISION_SIDECAR_VALID_STATUS:
        return 1

    merged = merge_b2_asset_promotion_decision_sidecar(sidecar_payload)
    validation = build_b2_asset_promotion_decision_validation_report(
        merged,
        readiness_payload,
    )
    output_path = args.output or args.sidecar.with_suffix(
        ".merged_asset_promotion_decision.json"
    )
    validation_path = args.validation_report or args.sidecar.with_suffix(
        ".asset_promotion_decision_validation_report.json"
    )
    _write_json(output_path, merged)
    _write_json(validation_path, validation)

    print(f"merged_asset_promotion_decision={output_path}")
    print(f"asset_promotion_decision_validation_report={validation_path}")
    print(f"decisions_valid={validation['decisions_valid']}")
    print(f"valid_decision_count={validation['summary']['valid_decision_count']}")
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
