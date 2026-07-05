"""Generate the Milestone 21 Unreal river-data round-trip validation manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import ROUND_TRIP_VALIDATION_PATH, write_round_trip_validation_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / ROUND_TRIP_VALIDATION_PATH,
        help="Output round-trip validation manifest path.",
    )
    args = parser.parse_args()

    generated = write_round_trip_validation_manifest(
        repo_root=repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"round_trip_cases={len(generated.manifest['round_trip_cases'])}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
