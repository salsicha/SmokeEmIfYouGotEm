"""Generate first-party close-range terrain detail textures."""

from pathlib import Path

from raftsim.production_detail_textures import generate_production_detail_textures


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    generate_production_detail_textures(repo_root)
    print(
        repo_root
        / "unreal/Content/RaftSim/Rendering/ProductionDetailTextures/first_party_production_detail_texture_manifest.json"
    )


if __name__ == "__main__":
    main()
