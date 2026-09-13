"""South Fork owns Troublemaker; the rapid is not a separate menu scenario."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimUI/Private/"
    "RaftSimVerticalSliceFrontend.cpp"
)


def test_troublemaker_is_not_a_standalone_scenario() -> None:
    source = FRONTEND_SOURCE.read_text(encoding="utf-8")
    assert 'TEXT("troublemaker_challenge")' not in source
    assert 'TEXT("/Game/RaftSim/Maps/L_SouthFork_Troublemaker")' not in source
    menu = FRONTEND_SOURCE.with_name('RaftSimMainMenuWidget.cpp').read_text()
    assert 'troublemaker_challenge' not in menu
    assert 'Troublemaker Rapid' not in menu
    scenario = source.split('TEXT("south_fork_full_descent")', 1)[1].split(
        'TEXT("hance_challenge")', 1
    )[0]
    assert 'TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach")' in scenario
    assert '120.0f, 48900.0f, false, true' in scenario


def test_retired_rapid_selection_does_not_reuse_local_checkpoint():
    source = FRONTEND_SOURCE.with_name('RaftSimSaveSubsystem.cpp').read_text()
    normalize = source.split('bool URaftSimSaveSubsystem::NormalizeSave(', 1)[1].split(
        'void URaftSimSaveSubsystem::RecalculateLicenseAndUnlocks(', 1)[0]
    assert 'Save->Selection.ScenarioId == TEXT("troublemaker_challenge")' in normalize
    assert 'Save->Selection.ScenarioId = TEXT("south_fork_full_descent")' in normalize
    checkpoint = source.split('bool URaftSimSaveSubsystem::FindBestCheckpoint(', 1)[1].split(
        'void URaftSimSaveSubsystem::RestoreDefaultSettings()', 1)[0]
    assert 'if (Progress.ScenarioId == TEXT("troublemaker_challenge")) continue;' in checkpoint


def test_playable_flow_preserves_geographic_and_hydraulic_authority():
    import hashlib
    import json
    directory = REPO_ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow'
    delivery = json.loads((directory / 'delivery.json').read_text())
    for name, expected in delivery['files'].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
    manifest = json.loads((directory / 'manifest.json').read_text())
    coordinates = json.loads((directory / 'coordinate_map.json').read_text())
    assert coordinates['world_y_sign'] == -1
    assert manifest['review']['source_bed_sampling'] == 'registered_triangles'
    assert manifest['review']['source_geometry_sha256'] == delivery['source_geometry_sha256']
    assert not delivery['underwater_bed_measured']
    assert not delivery['full_reconstruction_accepted']
    assert not manifest['all_bands_passed']  # integration is not acceptance
    route = json.loads((REPO_ROOT / 'docs/reconstruction-review-2026-09-07/guided-route-playable.json').read_text())
    assert route['cooked_fields_dir'] == directory.relative_to(REPO_ROOT).as_posix()
    assert route['source_geometry_sha256'] == delivery['source_geometry_sha256']
    assert route['depth_sha256'] == manifest['bands'][0]['arrays']['h']['sha256']


def test_negative_station_range_is_not_a_world_x_run():
    source = (REPO_ROOT / 'unreal/Source/SmokeEmIfYouGotEm/RaftSimRunManager.cpp').read_text()
    assert 'const bool bCrossedStart = FinishStationM > StartStationM && bHasStation' in source
    assert 'bool bFinished = FinishStationM > StartStationM && bHasStation' in source
    progress = source.split('float ARaftSimRunManager::GetProgressFraction()', 1)[1].split('bool ARaftSimRunManager::SampleRiverStation', 1)[0]
    assert 'StartStationM >= 0.0f' not in progress
    assert 'FinishStationM > StartStationM' in progress
    start, finish = -60., 110.
    assert (start-start)/(finish-start) == 0
    assert (finish-start)/(finish-start) == 1
    assert not -1 > -1  # unchanged unconfigured sentinel falls back to X


def test_playable_package_and_carrier_do_not_enable_particle_experiments():
    source = (REPO_ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    assert 'const bool bSurveyBreakingReview = bPlayableCapturedSouthFork ||' in source
    assert 'if (bPlayableCapturedSouthFork ||\n            WaterMaterial->GetPathName().Contains(TEXT("M_RaftSim_LiveRiverSurface")))' in source
    assert 'const bool bStatefulDetailReview = bRegisteredRockSurveyReview && bSurveyBreakingReview &&' in source
    assert 'TEXT("RaftSimStatefulDetailReview")' in source
    config = (REPO_ROOT / 'unreal/Config/DefaultGame.ini').read_text()
    assert '+MapsToCook=(FilePath="/Game/RaftSim/Maps/L_SouthFork_Troublemaker")' in config
    assert '+DirectoriesToNeverCook=(Path="/Game/RaftSim/Maps/Review")' in config
    build = (REPO_ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimWater/RaftSimWater.Build.cs').read_text()
    assert 'reconstruction_2026_09/troublemaker/playable_flow' in build


def test_ephemeral_gameplay_neither_loads_nor_writes_user_profile():
    source = (REPO_ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimUI/Private/RaftSimSaveSubsystem.cpp').read_text()
    assert 'const bool bExistingSlot = !bEphemeral && UGameplayStatics::DoesSaveGameExist' in source
    save = source.split('bool URaftSimSaveSubsystem::SaveCurrent()', 1)[1].split('void URaftSimSaveSubsystem::MarkScenarioCompleted', 1)[0]
    assert 'TEXT("RaftSimEphemeralProfile"))) return true;' in save
    assert save.index('TEXT("RaftSimEphemeralProfile")') < save.index('UGameplayStatics::SaveGameToSlot')
