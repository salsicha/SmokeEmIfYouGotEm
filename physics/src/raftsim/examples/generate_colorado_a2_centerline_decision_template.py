"""Generate the Colorado A2 centerline/CRS decision template."""

from pathlib import Path

from raftsim.colorado_a2_centerline_decision import (
    build_colorado_a2_centerline_decision_template,
    write_colorado_a2_centerline_decision_template,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    path = write_colorado_a2_centerline_decision_template(repo_root)
    payload = build_colorado_a2_centerline_decision_template(repo_root)
    print(path.relative_to(repo_root))
    print(payload["status"])
