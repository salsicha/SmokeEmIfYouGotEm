"""Generate the South Fork A1 full-reach NHD named-flowline extract."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_nhd_extraction import (
    build_full_reach_nhd_named_flowline_extract,
    write_full_reach_nhd_named_flowline_extract,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-zip",
        type=Path,
        default=Path("/private/tmp/NHD_H_18020129_HU8_Shape.zip"),
        help="Path to the official USGS NHD HU8 18020129 shapefile zip.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    geojson_path, manifest_path = write_full_reach_nhd_named_flowline_extract(
        source_zip=args.source_zip,
        repo_root=repo_root,
    )
    geojson, _manifest = build_full_reach_nhd_named_flowline_extract(
        source_zip=args.source_zip,
        repo_root=repo_root,
    )
    print(f"feature_count={len(geojson['features'])}")
    print(f"length_km={geojson['selection']['selected_length_km_source_sum']}")
    print(geojson_path.relative_to(repo_root))
    print(manifest_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
