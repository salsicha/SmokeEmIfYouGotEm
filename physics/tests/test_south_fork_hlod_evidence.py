from pathlib import Path

import pytest

from raftsim.south_fork_hlod_evidence import (
    MAP_PACKAGE,
    parse_hlod_build_log,
    validate_south_fork_hlod_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _log(world_count: int = 22, built_count: int = 22) -> str:
    return "\n".join(
        (
            f"Command Line: {MAP_PACKAGE} -Builder=WorldPartitionHLODsBuilder",
            f"#### World contains {world_count} HLOD actors ####",
            *("HLOD Actor Cell was modified, saving" for _ in range(built_count)),
            f"#### Built {built_count} HLOD actors ####",
            "LogInit: Display: Success - 0 error(s), 1 warning(s)",
        )
    )


def test_hlod_log_parser_requires_positive_complete_zero_error_build():
    parsed = parse_hlod_build_log(_log())

    assert parsed["world_actor_count"] == 22
    assert parsed["built_actor_count"] == 22
    assert parsed["modified_and_saved_actor_count"] == 22
    assert parsed["zero_error_success"] is True


@pytest.mark.parametrize(
    "text",
    (
        _log(world_count=0, built_count=0),
        _log(world_count=22, built_count=21),
        _log() + "\nActor has an invalid HLOD layer",
        _log().replace("Success - 0 error(s)", "Success - 1 error(s)"),
    ),
)
def test_hlod_log_parser_rejects_false_completion(text: str):
    with pytest.raises(ValueError):
        parse_hlod_build_log(text)


def test_checked_in_hlod_evidence_matches_current_actor_packages():
    evidence = validate_south_fork_hlod_evidence(REPO_ROOT)

    assert evidence["commandlet_result"]["world_actor_count"] == 20
    assert evidence["acceptance"]["merged_atlas_parent_absent"] is True
