"""Generate the physical-scale Chili Bar production-corridor inputs."""

from __future__ import annotations

import json
from pathlib import Path

from raftsim.south_fork_production_corridor import (
    build_south_fork_chili_bar_production_corridor,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    result = build_south_fork_chili_bar_production_corridor(repo_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
