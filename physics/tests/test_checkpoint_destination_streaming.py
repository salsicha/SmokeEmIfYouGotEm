"""Source-order contracts; native tests and first-frame captures verify behavior."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "unreal/Source/SmokeEmIfYouGotEm"
MANAGER = (ROOT / "RaftSimRunManager.cpp").read_text(encoding="utf-8")
STREAMING = (ROOT / "RaftSimCheckpointStreaming.h").read_text(encoding="utf-8")
RAFT = (ROOT.parents[1] / "Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftActor.cpp").read_text(encoding="utf-8")


def test_terrain_precedes_hydraulic_reseed_and_authoritative_raft_move():
    restore = MANAGER.split("void ARaftSimRunManager::TryRestoreSessionCheckpoint()", 1)[1].split(
        "void ARaftSimRunManager::StartRun()", 1)[0]
    ready = restore.index("RaftSimCheckpointStreaming::Prepare(GetWorld(),Checkpoint)")
    assert ready < restore.index("SeedCartesianCheckpointWater(Config,Water,Checkpoint)")
    assert ready < restore.index("Water->ConfigureRiverWindow(")
    assert ready < restore.index("Raft->TryRestoreCheckpoint(Checkpoint)")
    rejection = restore[ready:restore.index("bool bHydraulicRegionVerified")]
    assert "return;" in rejection and "water and raft not moved" in rejection


def test_scoped_provider_uses_player_policy_and_explicit_activation():
    assert "OutSources=PlayerSources;" in STREAMING
    assert "Source.TargetState=EStreamingSourceTargetState::Activated;" in STREAMING
    assert "RegisterStreamingSourceProvider(this)" in STREAMING
    assert "~FScopedDestination() { Subsystem->UnregisterStreamingSourceProvider(this); }" in STREAMING
    assert "World->BlockTillLevelStreamingCompleted();" in STREAMING
    assert "Partition->IsStreamingCompleted(&Source)" in STREAMING
    for forbidden in ("Shape.Radius=", "LoadingRangeScale=", "SetActorHiddenInGame",
                      "SetStreamingSourceEnabled", "RaftSimEphemeralProfile", "#if WITH_EDITOR"):
        assert forbidden not in STREAMING


def test_nonpartitioned_maps_keep_existing_behavior():
    assert "if (!World->GetWorldPartition()) return true;" in STREAMING
    assert "Player->GetStreamingSources(PlayerSources)" in STREAMING
    assert "!Destination.IsValid()" in STREAMING


def test_every_reset_prepares_before_mutating_raft_crew_or_checkpoint():
    reset = RAFT.split("bool ARaftSimRaftActor::TryRestoreCheckpoint(", 1)[1].split(
        "void ARaftSimRaftActor::SetCheckpointTransform(", 1)[0]
    prepare = reset.index("CheckpointPreparation.Execute(Prepared)")
    for mutation in ("CheckpointTransform=Prepared", "Swimmers.Reset()", "SetActorTransform(",
                     "ApplyCheckpointRepair(", "RaftAdapter->SetKinematicState(State)"):
        assert prepare < reset.index(mutation)
    rejection = reset[prepare:reset.index("CheckpointTransform=Prepared")]
    assert "return false;" in rejection
    assert "!CheckpointPreparation.IsBound()" in reset
    assert "bCheckpointResetInProgress" in reset and "TGuardValue<bool>" in reset
    setter = RAFT.split("void ARaftSimRaftActor::SetCheckpointTransform(", 1)[1].split(
        "void ARaftSimRaftActor::UpdateRaftCondition(", 1)[0]
    assert "TryRestoreCheckpoint(NewCheckpoint)" in setter
    assert "else CheckpointTransform = NewCheckpoint" in setter


def test_project_binds_weak_owner_and_prepares_cartesian_destination():
    begin = MANAGER.split("void ARaftSimRunManager::BeginPlay()", 1)[1].split(
        "void ARaftSimRunManager::ConfigureSession(", 1)[0]
    assert "SetCheckpointPreparation(FRaftSimCheckpointPreparation::CreateUObject(" in begin
    assert "this,&ARaftSimRunManager::PrepareCheckpointReset" in begin
    prepare = MANAGER.split("bool ARaftSimRunManager::PrepareCheckpointReset(", 1)[1].split(
        "bool ARaftSimRunManager::SeedCartesianCheckpointWater(", 1)[0]
    assert prepare.index("RaftSimCheckpointStreaming::Prepare") < prepare.index("SeedCartesianCheckpointWater")
    assert "HasCartesianWaterCoordinates()" in prepare
    assert "if (Config) return false;" in prepare
    assert "StartStationM" not in prepare


def test_failed_restart_keeps_score_and_progress_state():
    restart = MANAGER.split("void ARaftSimRunManager::RestartRun()", 1)[1].split(
        "void ARaftSimRunManager::FinishRun()", 1)[0]
    guard = restart.index("if (Raft != nullptr && !Raft->TryResetToCheckpoint()) return;")
    for mutation in ("LastProgressSample.bValid = false", "RunState =", "FinalScore =", "AwardedMedal ="):
        assert guard < restart.index(mutation)


def test_actual_play_probe_uses_checkpoint_apis_without_repairing_observed_water():
    probe = (ROOT / "Tests/RaftSimCheckpointPlayProbe.h").read_text(encoding="utf-8")
    assert "RaftSimEphemeralProfile" in probe
    assert "RaftSimCheckpointPlayReport=" in probe
    assert "Raft->TryRestoreCheckpoint(Destination)" in probe
    assert "Raft->TryResetToCheckpoint()" in probe
    assert "Frame->Validate()" in probe and "if(!Covered)" in probe
    assert "FreshFrames<100" in probe and "LastClock-FirstClock<3." in probe
    assert "Phase==2" in probe and "GetStreamingSourceProviders().Num()!=ProvidersBefore" in probe
    for forbidden in ("TeleportForTesting", "SetActorTransform", "Detail->Initialize",
                      "SetScalarParameterValue", "ConfigureAtWorldPosition", "TimeDilation"):
        assert forbidden not in probe


def test_checkpoint_runner_requires_report_and_preserves_existing_replay_gates():
    runner = (ROOT.parents[1] / "Scripts/profile_south_fork_current_map.ps1").read_text(encoding="utf-8")
    assert "[switch]$CheckpointResetReplay" in runner
    assert '"-RaftSimCheckpointPlayReport=$checkpointReplayFile"' in runner
    assert "'raftsim.checkpoint_actual_play.v1'" in runner
    assert "$checkpointReplay.passed -isnot [bool]" in runner
    assert "$CheckpointResetReplay -and -not $report.checkpoint_replay_passed" in runner
    assert "foreach ($phase in 0..2)" in runner and "foreach ($capture in 0..3)" in runner
    assert "$width -ne 1280 -or $height -ne 720" in runner
    assert "$report.checkpoint_frames = $frameEvidence" in runner
    assert "finally {" in runner and "NtResumeProcess($item.item.handle)" in runner
    detail = (ROOT / "Tests/RaftSimDetailStreamingPlayProbe.h").read_text(encoding="utf-8")
    assert "Elapsed>=120. && Handoffs-FirstHandoff>=8 && NewFrames>=100 && LastClock-FirstClock>=60." in detail
