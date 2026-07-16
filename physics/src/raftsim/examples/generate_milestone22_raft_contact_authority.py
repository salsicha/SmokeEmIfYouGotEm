"""Generate the Milestone 22 raft/contact authority integration manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone22 import write_raft_contact_authority_integration


def _default_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "TODO.md").exists():
            return candidate
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    args = parser.parse_args(argv)

    generated = write_raft_contact_authority_integration(args.repo_root)
    print(f"status={generated.manifest['status']}")
    print(
        "live_water_approved="
        f"{generated.manifest['custom_water_evidence']['live_water_approved']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
