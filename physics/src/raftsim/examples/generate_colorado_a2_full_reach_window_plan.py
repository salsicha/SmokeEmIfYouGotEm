"""Generate the Colorado A2 full-reach source-window plan."""

from pathlib import Path

from raftsim.colorado_a2_full_reach_window_plan import (
    write_colorado_a2_full_reach_window_plan,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    path = write_colorado_a2_full_reach_window_plan(repo_root)
    print(path.relative_to(repo_root))
