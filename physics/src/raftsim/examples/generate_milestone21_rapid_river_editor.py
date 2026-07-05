"""Generate the Milestone 21 Unreal rapid/river editor manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import RAPID_RIVER_EDITOR_MANIFEST_PATH, write_rapid_river_editor_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / RAPID_RIVER_EDITOR_MANIFEST_PATH,
        help="Output Unreal rapid/river editor manifest path.",
    )
    args = parser.parse_args()

    generated = write_rapid_river_editor_manifest(repo_root=repo_root, output_json=args.output_json)
    print(f"manifest={args.output_json}")
    print(f"seed_annotations={len(generated.manifest['seed_annotations'])}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
