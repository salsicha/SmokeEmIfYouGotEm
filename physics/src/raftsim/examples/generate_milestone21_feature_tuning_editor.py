"""Generate the Milestone 21 Unreal feature-tuning editor manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import FEATURE_TUNING_EDITOR_PATH, write_feature_tuning_editor_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / FEATURE_TUNING_EDITOR_PATH,
        help="Output Unreal feature-tuning editor manifest path.",
    )
    args = parser.parse_args()

    generated = write_feature_tuning_editor_manifest(
        repo_root=repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"feature_tuning_groups={len(generated.manifest['feature_tuning_groups'])}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
