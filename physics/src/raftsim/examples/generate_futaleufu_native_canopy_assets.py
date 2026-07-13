"""Generate the first-party Futaleufu native-canopy texture candidates."""

from pathlib import Path

from raftsim.futaleufu_native_canopy_assets import generate_futaleufu_native_canopy_assets


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    manifest = generate_futaleufu_native_canopy_assets(repo_root)
    print(
        f"Generated {len(manifest['maps'])} coigue texture maps; "
        f"status={manifest['status']}"
    )
