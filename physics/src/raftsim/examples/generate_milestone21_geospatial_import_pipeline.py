"""Generate the Milestone 21 canonical geospatial import pipeline manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone21 import (
    GEOSPATIAL_IMPORT_PIPELINE_PATH,
    write_geospatial_import_pipeline_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root / GEOSPATIAL_IMPORT_PIPELINE_PATH,
        help="Output Unreal geospatial import pipeline manifest path.",
    )
    args = parser.parse_args()

    generated = write_geospatial_import_pipeline_manifest(
        repo_root=repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"import_stages={len(generated.manifest['import_stages'])}")
    print(f"status={generated.manifest['status']}")


if __name__ == "__main__":
    main()
