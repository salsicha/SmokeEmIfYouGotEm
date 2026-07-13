"""Generate the V10 three-source broad cypress spray maps."""

from pathlib import Path

from raftsim.futaleufu_cordillera_cypress_v10_assets import (
    generate_futaleufu_cordillera_cypress_v10_assets,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    manifest = generate_futaleufu_cordillera_cypress_v10_assets(repo_root)
    print(manifest["status"])
