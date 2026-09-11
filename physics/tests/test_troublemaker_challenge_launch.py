"""Regression guard for the menu's named Troublemaker rapid launch."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimUI/Private/"
    "RaftSimVerticalSliceFrontend.cpp"
)


def test_troublemaker_challenge_starts_on_the_final_rapid_approach() -> None:
    source = FRONTEND_SOURCE.read_text(encoding="utf-8")
    scenario = source.split('TEXT("troublemaker_challenge")', 1)[1].split(
        'TEXT("hance_challenge")', 1
    )[0]

    assert 'TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach")' in scenario
    assert "ERaftSimLicenseTier::Trainee, 10, 8320.0f, 8525.0f" in scenario
    assert "7900.0f" not in scenario
