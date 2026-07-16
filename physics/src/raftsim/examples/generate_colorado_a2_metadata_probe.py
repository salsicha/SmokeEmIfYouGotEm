"""Generate the Colorado A2 full-reach metadata probe report."""

from pathlib import Path

from raftsim.colorado_a2_metadata_probe import write_colorado_a2_metadata_probe


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    path = write_colorado_a2_metadata_probe(repo_root)
    print(path.relative_to(repo_root))
