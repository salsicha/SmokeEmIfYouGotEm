from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_additional_canopy_branch_atlases import (
    generate_south_fork_additional_canopy_branch_atlases,
)

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    manifest = generate_south_fork_additional_canopy_branch_atlases(repo_root)
    print(
        f"Generated {len(manifest['profiles'])} additional South Fork branch "
        f"atlases; status={manifest['status']}"
    )
