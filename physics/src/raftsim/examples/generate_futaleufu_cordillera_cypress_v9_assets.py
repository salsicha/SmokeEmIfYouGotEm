"""Generate the V9 cordilleran-cypress high-fidelity branch-spray maps."""

from pathlib import Path

from raftsim.futaleufu_cordillera_cypress_v9_assets import (
    generate_futaleufu_cordillera_cypress_v9_assets,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    manifest = generate_futaleufu_cordillera_cypress_v9_assets(repo_root)
    print(manifest["status"])
