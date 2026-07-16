"""Generate the pending D6 measured-result comparison report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    build_flexible_raft_d6_comparison_report,
    write_flexible_raft_d6_comparison_payload,
    write_flexible_raft_d6_comparison_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--measured-results",
        type=Path,
        default=None,
        help="Populated measured-results JSON or raw measured_results mapping.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output report path. Required only when the default measured-results sidecar is not desired.",
    )
    args = parser.parse_args(argv)

    if args.measured_results is None:
        output_path = args.output or write_flexible_raft_d6_comparison_report(
            args.repo_root
        )
        payload = build_flexible_raft_d6_comparison_report()
        if args.output is not None:
            output_path = write_flexible_raft_d6_comparison_payload(
                args.output,
                payload,
            )
    else:
        measured_results = _load_measured_results(args.measured_results)
        payload = build_flexible_raft_d6_comparison_report(measured_results)
        output_path = args.output or args.measured_results.with_suffix(
            ".comparison_report.json"
        )
        output_path = write_flexible_raft_d6_comparison_payload(output_path, payload)
    print(f"report={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"missing_target_count={payload['missing_target_count']}")
    print(f"d6_complete={payload['d6_complete']}")
    return 0


def _load_measured_results(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Measured-results payload must be a JSON object.")
    measured_results = payload.get("measured_results", payload)
    if not isinstance(measured_results, dict):
        raise ValueError("measured_results must be a JSON object.")
    return measured_results


if __name__ == "__main__":
    raise SystemExit(main())
