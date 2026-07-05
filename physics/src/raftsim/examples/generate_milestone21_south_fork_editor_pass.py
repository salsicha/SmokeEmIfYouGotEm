"""Generate the Milestone 21 South Fork first-river editor pass manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import SOUTH_FORK_EDITOR_PASS_PATH, write_south_fork_editor_pass_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / SOUTH_FORK_EDITOR_PASS_PATH,
        help="Output South Fork first-river editor pass manifest path.",
    )
    args = parser.parse_args()

    generated = write_south_fork_editor_pass_manifest(
        repo_root=repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"reviewed_rapid_count={generated.manifest['reviewed_rapid_count']}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
