"""Validate and merge Unreal Chaos D6 measured results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    build_flexible_raft_d6_chaos_measured_results_merge_report,
    merge_flexible_raft_d6_chaos_measured_results_sidecar,
    write_flexible_raft_d6_chaos_measured_results_merge_payload,
    write_flexible_raft_d6_chaos_measured_results_merge_report,
    write_flexible_raft_d6_chaos_measured_results_sidecar_template,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--chaos-sidecar",
        type=Path,
        default=None,
        help="Unreal Chaos measured-results sidecar JSON to validate and merge.",
    )
    parser.add_argument(
        "--base-measured-results",
        type=Path,
        default=None,
        help="Optional standard measured-results payload to merge into.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Merged standard measured-results output path.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Validation/merge report output path.",
    )
    args = parser.parse_args(argv)

    if args.chaos_sidecar is None:
        template_path = write_flexible_raft_d6_chaos_measured_results_sidecar_template(
            args.repo_root
        )
        report_path = write_flexible_raft_d6_chaos_measured_results_merge_report(
            args.repo_root
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"sidecar_template={template_path}")
        print(f"merge_report={report_path}")
        print(f"schema={report['schema']}")
        print(f"status={report['status']}")
        print(f"can_merge={report['can_merge']}")
        print(f"d6_complete={report['d6_complete']}")
        return 0

    sidecar_payload = _load_json_object(args.chaos_sidecar)
    report = build_flexible_raft_d6_chaos_measured_results_merge_report(
        sidecar_payload
    )
    report_path = args.report or args.chaos_sidecar.with_suffix(".merge_report.json")
    write_flexible_raft_d6_chaos_measured_results_merge_payload(report_path, report)

    print(f"merge_report={report_path}")
    print(f"schema={report['schema']}")
    print(f"status={report['status']}")
    print(f"can_merge={report['can_merge']}")
    print(f"filled_fixture_count={report['filled_fixture_count']}")

    if not report["can_merge"]:
        return 1

    base_payload = (
        _load_json_object(args.base_measured_results)
        if args.base_measured_results is not None
        else None
    )
    merged = merge_flexible_raft_d6_chaos_measured_results_sidecar(
        sidecar_payload,
        base_measured_results_payload=base_payload,
    )
    output_path = args.output or args.chaos_sidecar.with_suffix(
        ".merged_measured_results.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(merged, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"merged_measured_results={output_path}")
    print(f"filled_result_count={merged['filled_result_count']}")
    print(f"d6_complete={merged['d6_complete']}")
    return 0


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
