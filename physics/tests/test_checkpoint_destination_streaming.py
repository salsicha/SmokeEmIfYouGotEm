"""Source-order contracts; native tests and first-frame captures verify behavior."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "unreal/Source/SmokeEmIfYouGotEm"
MANAGER = (ROOT / "RaftSimRunManager.cpp").read_text()
STREAMING = (ROOT / "RaftSimCheckpointStreaming.h").read_text()


def test_terrain_precedes_hydraulic_reseed_and_authoritative_raft_move():
    restore = MANAGER.split("void ARaftSimRunManager::TryRestoreSessionCheckpoint()", 1)[1].split(
        "void ARaftSimRunManager::StartRun()", 1)[0]
    ready = restore.index("RaftSimCheckpointStreaming::Prepare(GetWorld(),Checkpoint)")
    assert ready < restore.index("SeedCartesianCheckpointWater(Config,Water,Checkpoint)")
    assert ready < restore.index("Water->ConfigureRiverWindow(")
    assert ready < restore.index("Raft->SetCheckpointTransform(Checkpoint, true)")
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
