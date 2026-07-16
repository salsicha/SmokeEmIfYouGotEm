"""Generate South Fork A1 downstream access/publication source review."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_downstream_access_review import (
    build_south_fork_a1_downstream_access_publication_review,
    write_south_fork_a1_downstream_access_publication_review,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_downstream_access_publication_review(args.repo_root)
    payload = build_south_fork_a1_downstream_access_publication_review(args.repo_root)
    print(f"wrote={output_path}")
    print(f"status={payload['status']}")
    print(f"source_count={len(payload['sources_checked'])}")
    print(f"candidate_support_count={len(payload['candidate_support'])}")


if __name__ == "__main__":
    main()
