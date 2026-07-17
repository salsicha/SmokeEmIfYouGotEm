"""Generate the B2 source-acquisition execution plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from raftsim.photoreal_b2_source_acquisition_execution import (
    build_b2_source_acquisition_execution_plan,
    write_b2_source_acquisition_execution_plan,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--storage-decision-result",
        type=Path,
        default=None,
        help="Filled B2 source-binary storage decision result JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Execution-plan output path.",
    )
    args = parser.parse_args(argv)

    if args.storage_decision_result is not None:
        storage_result = _load_json_object(args.storage_decision_result)
        payload = build_b2_source_acquisition_execution_plan(storage_result)
        output_path = args.output or args.storage_decision_result.with_suffix(
            ".b2_source_acquisition_execution_plan.json"
        )
        _write_json(output_path, payload)
    elif args.output is not None:
        payload = build_b2_source_acquisition_execution_plan()
        output_path = args.output
        _write_json(output_path, payload)
    else:
        output_path = write_b2_source_acquisition_execution_plan(args.repo_root)
        payload = build_b2_source_acquisition_execution_plan()

    print(f"artifact={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(
        "storage_decision_valid="
        f"{payload['storage_decision']['storage_decision_valid']}"
    )
    print(f"cc0_task_count={payload['summary']['cc0_task_count']}")
    print(f"executable_task_count={payload['summary']['executable_task_count']}")
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
