"""Generate the project-owned South Fork live-oak branch texture maps."""

from pathlib import Path

from raftsim.south_fork_live_oak_branch_atlas import (
    generate_south_fork_live_oak_branch_atlas,
)

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    manifest = generate_south_fork_live_oak_branch_atlas(repo_root)
    print(
        "Generated "
        f"{len(manifest['maps'])} South Fork live-oak branch maps; "
        f"status={manifest['status']}"
    )
