"""Validate and merge a B2 import/capture review sidecar payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.photoreal_b2_import_capture_review import (
    build_b2_import_capture_review_validation_report,
)
from raftsim.photoreal_b2_import_capture_sidecar import (
    build_b2_import_capture_review_sidecar_merge_report,
    merge_b2_import_capture_review_sidecar,
    write_b2_import_capture_review_sidecar_merge_report,
    write_b2_import_capture_review_sidecar_template,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=None,
        help="Filled B2 import/capture review sidecar JSON to validate and merge.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Merged canonical import/capture ledger output path.",
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
        help="Canonical import/capture validation report output path for a valid merge.",
    )
    args = parser.parse_args(argv)

    if args.sidecar is None:
        template_path = write_b2_import_capture_review_sidecar_template(args.repo_root)
        report_path = write_b2_import_capture_review_sidecar_merge_report(args.repo_root)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"sidecar_template={template_path}")
        print(f"merge_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(
            "can_mark_any_source_reviewed="
            f"{report['promotion_permissions']['can_mark_any_source_reviewed']}"
        )
        print(
            "can_mark_any_b2_asset_set_promotion_ready="
            f"{report['promotion_permissions']['can_mark_any_b2_asset_set_promotion_ready']}"
        )
        return 0

    sidecar_payload = _load_json_object(args.sidecar)
    report = build_b2_import_capture_review_sidecar_merge_report(sidecar_payload)
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

    if report["status"] != "import_capture_review_sidecar_valid_manual_promotion_required":
        return 1

    merged = merge_b2_import_capture_review_sidecar(sidecar_payload)
    validation = build_b2_import_capture_review_validation_report(merged)
    output_path = args.output or args.sidecar.with_suffix(
        ".merged_import_capture_review_ledger.json"
    )
    validation_path = args.validation_report or args.sidecar.with_suffix(
        ".import_capture_review_validation_report.json"
    )
    _write_json(output_path, merged)
    _write_json(validation_path, validation)

    print(f"merged_import_capture_review_ledger={output_path}")
    print(f"import_capture_review_validation_report={validation_path}")
    print(f"import_reviews_valid={validation['import_reviews_valid']}")
    print(
        "approved_review_record_count="
        f"{validation['summary']['approved_review_record_count']}"
    )
    return 0


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
