"""Generate the photoreal river flow-variant capture plan."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_capture_quality import write_photoreal_flow_variant_capture_plan


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_photoreal_flow_variant_capture_plan(repo_root)
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
