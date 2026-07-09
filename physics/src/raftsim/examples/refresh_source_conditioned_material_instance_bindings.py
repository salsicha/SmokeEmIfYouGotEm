from __future__ import annotations

from pathlib import Path

from raftsim.source_conditioned_material_maps import (
    FIRST_PARTY_MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH,
    refresh_source_conditioned_material_instance_candidate_bindings,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    refresh_source_conditioned_material_instance_candidate_bindings(repo_root)
    print(repo_root / FIRST_PARTY_MATERIAL_INSTANCE_CANDIDATE_MANIFEST_RELATIVE_PATH)


if __name__ == "__main__":
    main()
