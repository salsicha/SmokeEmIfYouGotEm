"""Generate the photoreal flow-variant human lifelike review handoff."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_capture_quality import write_flow_variant_human_lifelike_review_handoff


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_flow_variant_human_lifelike_review_handoff(repo_root)
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
