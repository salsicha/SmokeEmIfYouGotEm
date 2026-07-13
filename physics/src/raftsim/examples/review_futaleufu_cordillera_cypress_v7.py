"""Write V7 compact-frond and authority-split cypress review evidence."""

from pathlib import Path

from raftsim.futaleufu_cordillera_cypress_review import (
    write_futaleufu_cordillera_cypress_v7_visual_review,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    review = write_futaleufu_cordillera_cypress_v7_visual_review(repo_root)
    print(review["status"])
