"""Generate D6 external measurement manifest and measured-results template."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    build_flexible_raft_d6_measurement_manifest,
    build_flexible_raft_d6_measured_results_template,
    write_flexible_raft_d6_measurement_manifest,
    write_flexible_raft_d6_measured_results_template,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    manifest_path = write_flexible_raft_d6_measurement_manifest(args.repo_root)
    template_path = write_flexible_raft_d6_measured_results_template(args.repo_root)
    manifest = build_flexible_raft_d6_measurement_manifest()
    template = build_flexible_raft_d6_measured_results_template()
    print(f"manifest={manifest_path}")
    print(f"template={template_path}")
    print(f"status={manifest['status']}")
    print(f"measurement_task_count={manifest['measurement_task_count']}")
    print(f"required_result_count={template['required_result_count']}")


if __name__ == "__main__":
    main()
