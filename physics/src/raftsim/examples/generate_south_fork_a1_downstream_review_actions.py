"""Generate South Fork A1 downstream-anchor reviewer action packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_downstream_review_actions import (
    build_south_fork_a1_downstream_anchor_review_actions,
    write_south_fork_a1_downstream_anchor_review_actions,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_downstream_anchor_review_actions(args.repo_root)
    payload = build_south_fork_a1_downstream_anchor_review_actions(args.repo_root)
    print(f"wrote={output_path}")
    print(f"status={payload['status']}")
    print(f"action_count={len(payload['action_sequence'])}")
    print(f"source_count={len(payload['evidence_bundle']['official_source_leads'])}")


if __name__ == "__main__":
    main()
