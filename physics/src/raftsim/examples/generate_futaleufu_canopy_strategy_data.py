from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.canopy_review_mining import build_canopy_review_report, render_canopy_review_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine the locked Futaleufu canopy review history.")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_canopy_review_report(repo_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_canopy_review_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
