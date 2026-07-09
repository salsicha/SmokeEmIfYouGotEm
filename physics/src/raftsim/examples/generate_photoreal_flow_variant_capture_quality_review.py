"""Generate the photoreal flow-variant capture quality review manifest."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_capture_quality import write_flow_variant_capture_quality_review


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_flow_variant_capture_quality_review(repo_root)
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
