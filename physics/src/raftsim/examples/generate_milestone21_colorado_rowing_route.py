"""Generate the Milestone 21 Colorado River rowing/oar-rig route draft files."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import COLORADO_ROWING_ROUTE_PATH, write_colorado_rowing_route_draft_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / COLORADO_ROWING_ROUTE_PATH,
        help="Output Colorado rowing route draft manifest path.",
    )
    args = parser.parse_args()

    generated = write_colorado_rowing_route_draft_manifest(
        repo_root=repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"source_manifest={repo_root / generated.manifest['source_manifest']}")
    print(f"flow_presets={repo_root / generated.manifest['flow_presets']}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
