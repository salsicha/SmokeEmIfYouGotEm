"""Run the independent Project Chrono D6 compliant-fixture target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.flexible_raft_d6_project_chrono_runner import run_project_chrono_d6


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    sidecar_path, summary_path = run_project_chrono_d6(args.repo_root)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    print(f"project_chrono_sidecar={sidecar_path}")
    print(f"project_chrono_summary={summary_path}")
    print(f"engine_version={summary['engine_version']}")
    print(f"filled_fixture_count={summary['filled_fixture_count']}")
    print(f"can_merge_sidecar={summary['can_merge_sidecar']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
