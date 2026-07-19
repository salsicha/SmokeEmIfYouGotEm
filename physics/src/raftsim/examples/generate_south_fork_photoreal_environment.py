"""Generate the deterministic full-reach South Fork presentation products."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_photoreal_environment import (
    DEFAULT_SEED,
    build_south_fork_photoreal_environment_manifest,
    write_south_fork_photoreal_environment,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    output = write_south_fork_photoreal_environment(args.repo_root, args.seed)
    manifest = build_south_fork_photoreal_environment_manifest(args.repo_root)
    print(f"wrote={output}")
    print(f"status={manifest['status']}")
    print(f"far_field_patch_count={manifest['far_field']['patch_count']}")
    print(f"unreal_tile_count={len(manifest['unreal_import']['tiles'])}")


if __name__ == "__main__":
    main()
