"""Generate project-owned Futaleufu Cordilleran cypress texture candidates."""

from pathlib import Path

from raftsim.futaleufu_cordillera_cypress_assets import (
    generate_futaleufu_cordillera_cypress_assets,
)


if __name__ == "__main__":
    generate_futaleufu_cordillera_cypress_assets(Path(__file__).resolve().parents[4])
