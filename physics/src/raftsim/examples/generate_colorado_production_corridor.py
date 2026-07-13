"""Generate the source-scale Lees Ferry Unreal corridor package."""

from pathlib import Path

from raftsim.colorado_production_corridor import build_colorado_lees_ferry_production_corridor


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    result = build_colorado_lees_ferry_production_corridor(repo_root)
    print(result["manifest_path"])
