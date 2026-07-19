"""Generate deterministic full-reach South Fork environment products."""

from pathlib import Path

from raftsim.south_fork_photoreal_environment import (
    write_south_fork_photoreal_environment,
)

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    print(write_south_fork_photoreal_environment(repo_root))
