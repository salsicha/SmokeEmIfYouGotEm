"""Normal-path source wiring; native tests exercise the directional arithmetic."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp'


def test_directional_onset_is_normal_south_fork_only():
    source = SOURCE.read_text()
    policy = source.split('bool bDirectionalFoamSource =', 1)[1].split('TArray<FVector4f> FoamSourceAudit', 1)[0]
    assert 'bCartesianFlow && bSingleLiveWaterSurfaceEnabled' in policy
    assert 'GetMapName().Contains(TEXT("L_SouthForkAmerican_FullReach"))' in policy
    assert '#if !UE_BUILD_SHIPPING' in policy
    assert 'RaftSimLegacyGenericFoamSource' in policy
    onset = source.split('const FVector2D WorkingGradient(', 1)[1].split('const float RoughnessGate', 1)[0]
    for component in ('BaseStationSlope', 'BaseLateralSlope', 'StandingWave.StationSlope',
                      'StandingWave.LateralSlope', 'ReliefStationSlope', 'ReliefLateralSlope',
                      'BoulderWakeStationSlope', 'BoulderWakeLateralSlope'):
        assert component in onset
    assert 'RaftSimFoamTransport::RisingSurfaceSlope(WorkingGradient,' in onset
    assert 'Sample.VelocityMetersPerSecond.X,Sample.VelocityMetersPerSecond.Y' in onset
    assert ': LegacyWorkingSlope;' in onset


def test_directional_onset_does_not_remove_other_foam_sources_or_transport():
    source = SOURCE.read_text()
    assert '0.015f, 0.06f, SurfaceWorkingSlope' in source
    assert 'FMath::Clamp((Froude - 0.78f) / 1.25f, 0.0f, 1.0f)' in source
    assert 'Foam = FMath::Max(Foam, 0.72f * HydraulicFeatureEnergy);' in source
    assert 'Foam = FMath::Max(Foam * BoulderCoreFade, WakeFoamAdd);' in source
    assert 'SourceFoam[VertexIndex] = FMath::Max(SourceFoam[VertexIndex], CrestFoam);' in source
    assert 'SourceFoam[VertexIndex], FMath::Max(PocketFoam, BoilFoam)' in source
    assert 'RaftSimFoamEvolution::Resolve(Advected,SourceFoam[Index],FoamAttackBlend,' in source
    assert 'FieldPosition - FieldVelocity * FoamDeltaSeconds' in source
