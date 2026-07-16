"""Generate the Colorado A2 rapid-mile cross-check template."""

from pathlib import Path

from raftsim.colorado_a2_rapid_mile_crosscheck import (
    build_colorado_a2_rapid_mile_crosscheck_template,
    write_colorado_a2_rapid_mile_crosscheck_template,
)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[4]
    path = write_colorado_a2_rapid_mile_crosscheck_template(repo_root)
    payload = build_colorado_a2_rapid_mile_crosscheck_template(repo_root)
    print(path.relative_to(repo_root))
    print(payload["status"])
    print(f"rapid_count={payload['rapid_count']}")
