from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.editor_source_layout import (
    build_editor_source_inventory,
    render_editor_source_inventory_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory RaftSim editor C++ sources and command surfaces.")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    inventory = build_editor_source_inventory(args.repo_root.resolve())
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_editor_source_inventory_markdown(inventory), encoding="utf-8")


if __name__ == "__main__":
    main()
