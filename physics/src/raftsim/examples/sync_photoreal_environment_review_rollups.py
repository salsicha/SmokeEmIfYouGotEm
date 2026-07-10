"""Synchronize current photoreal capture evidence into planning manifests."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_review_rollups import sync_photoreal_environment_review_rollups


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    for output_path in sync_photoreal_environment_review_rollups(repo_root):
        print(output_path)


if __name__ == "__main__":
    main()
