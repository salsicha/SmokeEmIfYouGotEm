"""Generate Unreal-ready visual derivatives from calibrated C++ playback."""

from pathlib import Path

from raftsim.solver_visualization_fields import (
    MANIFEST_RELATIVE_PATH,
    generate_solver_visualization_fields,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    generate_solver_visualization_fields(repo_root)
    print(repo_root / MANIFEST_RELATIVE_PATH)


if __name__ == "__main__":
    main()
