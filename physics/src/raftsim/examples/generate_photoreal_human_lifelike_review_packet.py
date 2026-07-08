"""Generate the photoreal human lifelike Markdown review packet."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_capture_quality import write_human_lifelike_review_packet_markdown


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_human_lifelike_review_packet_markdown(repo_root)
    print(output_path)


if __name__ == "__main__":
    main()
