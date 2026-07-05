"""Generate the Milestone 21 reach-local authoring and streaming manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import REACH_LOCAL_STREAMING_PATH, write_reach_local_streaming_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / REACH_LOCAL_STREAMING_PATH,
        help="Output Unreal reach-local streaming manifest path.",
    )
    args = parser.parse_args()

    generated = write_reach_local_streaming_manifest(
        repo_root=repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"playable_windows={generated.manifest['playable_window_count']}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
