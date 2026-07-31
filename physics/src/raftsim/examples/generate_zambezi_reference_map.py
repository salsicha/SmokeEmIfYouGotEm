"""Generate Zambezi user-reference terrain products and run scenario."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.zambezi_reference_map import generate_zambezi_reference_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    outputs = generate_zambezi_reference_bundle(args.repo_root)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
