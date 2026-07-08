"""Generate source-conditioned material maps for photoreal river environment review."""

from __future__ import annotations

from pathlib import Path

from raftsim.source_conditioned_material_maps import generate_source_conditioned_material_maps


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    generate_source_conditioned_material_maps(repo_root)
    print(repo_root / "unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/first_party_source_conditioned_material_map_manifest.json")


if __name__ == "__main__":
    main()
