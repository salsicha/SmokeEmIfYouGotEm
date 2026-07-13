"""Record the rejected V1 Futaleufu cordilleran-cypress visual gate."""

from pathlib import Path

from raftsim.futaleufu_cordillera_cypress_review import (
    write_futaleufu_cordillera_cypress_v1_visual_review,
)


if __name__ == "__main__":
    write_futaleufu_cordillera_cypress_v1_visual_review(
        Path(__file__).resolve().parents[4]
    )
