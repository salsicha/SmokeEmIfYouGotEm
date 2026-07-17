"""Generate the fail-closed D6 Unreal Chaos runner export bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.flexible_raft_d6_chaos_runner_export import (
    build_flexible_raft_d6_chaos_runner_sidecar,
    build_flexible_raft_d6_chaos_runner_summary,
    write_flexible_raft_d6_chaos_runner_export,
    write_flexible_raft_d6_chaos_runner_sidecar_payload,
    write_flexible_raft_d6_chaos_runner_summary_payload,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--sidecar-output", type=Path, default=None)
    parser.add_argument("--summary-output", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.sidecar_output is None and args.summary_output is None:
        sidecar_path, summary_path = write_flexible_raft_d6_chaos_runner_export(
            args.repo_root
        )
        sidecar = build_flexible_raft_d6_chaos_runner_sidecar()
        summary = build_flexible_raft_d6_chaos_runner_summary(sidecar)
    else:
        sidecar = build_flexible_raft_d6_chaos_runner_sidecar()
        summary = build_flexible_raft_d6_chaos_runner_summary(sidecar)
        sidecar_path = args.sidecar_output or (
            args.repo_root
            / "physics/reports/d6/chaos/flexible_raft_d6_chaos_measured_results.json"
        )
        summary_path = args.summary_output or (
            args.repo_root / "physics/reports/d6/chaos/summary.json"
        )
        write_flexible_raft_d6_chaos_runner_sidecar_payload(sidecar_path, sidecar)
        write_flexible_raft_d6_chaos_runner_summary_payload(summary_path, summary)

    print(f"chaos_runner_sidecar={sidecar_path}")
    print(f"chaos_runner_summary={summary_path}")
    print(f"schema={summary['schema']}")
    print(f"status={summary['status']}")
    print(f"fixture_count={summary['fixture_count']}")
    print(f"filled_fixture_count={summary['filled_fixture_count']}")
    print(f"can_merge_sidecar={summary['can_merge_sidecar']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
