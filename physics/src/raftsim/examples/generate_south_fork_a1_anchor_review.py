"""Generate the South Fork A1 full-reach anchor review."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_anchor_review import (
    build_south_fork_a1_full_reach_anchor_review,
    write_south_fork_a1_full_reach_anchor_review,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_full_reach_anchor_review(repo_root)
    payload = build_south_fork_a1_full_reach_anchor_review(repo_root)
    coloma = {
        anchor["anchor_id"]: anchor for anchor in payload["anchor_reviews"]
    }["coloma_bridge_checkpoint"]
    validation = coloma["shortest_path_validation"]
    print(f"status={payload['status']}")
    print(
        "coloma_graph_minus_published_checkpoint_m="
        f"{validation['graph_minus_published_checkpoint_m']}"
    )
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
