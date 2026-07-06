"""Download and record review-gated production import pilot source tiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


PULL_MANIFEST_SCHEMA_VERSION = "raftsim.production_import_pilot_pull_manifest.v1"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_metadata(path: Path) -> tuple[list[int], str]:
    with Image.open(path) as image:
        return [int(image.width), int(image.height)], str(image.mode)


def _download_url(url: str, target_path: Path, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "RaftSim production import pilot downloader"})
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "unknown").split(";")[0].strip() or "unknown"
        with temp_path.open("wb") as output:
            shutil.copyfileobj(response, output)
    temp_path.replace(target_path)
    return content_type


def _expected_size(spec: dict[str, Any]) -> list[int] | None:
    size = spec.get("size_px")
    if isinstance(size, list) and len(size) == 2:
        return [int(size[0]), int(size[1])]
    return None


def pull_production_import_pilot(
    *,
    recipe_path: Path,
    river_root: Path,
    repo_root: Path,
    output_manifest_path: Path,
    timeout: float = 60.0,
    reuse_existing: bool = False,
) -> dict[str, Any]:
    """Download every tile download spec from a production import pilot recipe."""

    recipe = _read_json(recipe_path)
    downloads: list[dict[str, Any]] = []
    tiles = recipe.get("tile_grid", {}).get("tiles", [])
    for tile in tiles:
        tile_id = str(tile["tile_id"])
        download_specs = tile.get("download_specs", {})
        for download_kind, spec in download_specs.items():
            target_path = river_root / str(spec["target_artifact"])
            if reuse_existing and target_path.exists():
                content_type = "existing_file"
            else:
                content_type = _download_url(str(spec["url"]), target_path, timeout)
            actual_size, image_mode = _image_metadata(target_path)
            expected_size = _expected_size(spec)
            downloads.append(
                {
                    "tile_id": tile_id,
                    "download_kind": str(download_kind),
                    "provider": str(spec.get("provider", "unknown")),
                    "source_url": str(spec["url"]),
                    "path": _repo_relative(target_path, repo_root),
                    "status": "downloaded_review_pending",
                    "content_type": content_type,
                    "size_bytes": target_path.stat().st_size,
                    "sha256": _sha256(target_path),
                    "expected_size_px": expected_size,
                    "actual_size_px": actual_size,
                    "image_mode": image_mode,
                }
            )

    manifest = {
        "schema": PULL_MANIFEST_SCHEMA_VERSION,
        "status": "official_service_pilot_tiles_downloaded_review_pending",
        "generated_on": datetime.now(timezone.utc).date().isoformat(),
        "river_id": recipe["river_id"],
        "section_id": recipe["section_id"],
        "source_recipe": _repo_relative(recipe_path, repo_root),
        "download_count": len(downloads),
        "downloads": downloads,
        "review_gates": [
            "Verify provider metadata and acquisition dates for every imagery tile.",
            "Mosaic, clip, reproject, void-review, hydrologically condition, and channel-burn DEM tiles before Unreal Landscape promotion.",
            "Derive water, vegetation, wet-rock, sandbar, and release-band masks only after hydrography, river-edge, and bank alignment review.",
            "Do not treat downloaded reference tiles as final photoreal art until guide/oarsman and geospatial review passes.",
        ],
    }
    _write_json(output_manifest_path, manifest)
    return manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe", type=Path, help="Path to production_import_pilot.json")
    parser.add_argument("--river-root", type=Path, default=None, help="River data root; defaults to the recipe parent")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root for manifest-relative paths")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output pull manifest path; defaults to production_import_pilot_pull_manifest.json beside the recipe",
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-request timeout in seconds")
    parser.add_argument("--reuse-existing", action="store_true", help="Record existing target files without redownloading")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    recipe_path = args.recipe
    river_root = args.river_root or recipe_path.parent
    output_manifest_path = args.output or recipe_path.parent / "production_import_pilot_pull_manifest.json"
    manifest = pull_production_import_pilot(
        recipe_path=recipe_path,
        river_root=river_root,
        repo_root=args.repo_root,
        output_manifest_path=output_manifest_path,
        timeout=args.timeout,
        reuse_existing=args.reuse_existing,
    )
    print(f"wrote {output_manifest_path} with {manifest['download_count']} downloads")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
