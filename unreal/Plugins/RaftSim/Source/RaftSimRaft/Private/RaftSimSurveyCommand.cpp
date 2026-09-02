// Review/survey console commands (never run unless explicitly invoked):
//
//   RaftSim.SurveyReach <startM> <endM> <stepM> <settleS> <label> [radiusM]
//     Walks the raft down the bound river corridor in sub-80 m hops, lets it
//     settle at every station, photographs it from a chase and a shore
//     camera, and logs one parseable "RaftSim survey station" line with raft
//     support, water and rock telemetry plus a 5 m water sweep around the
//     station. Exits after the last station.
//
//   RaftSim.CaptureRaftSeries <delay> <count> <interval> <label> <backM>
//                             <sideM> <upM> <aheadM> [paddle] [cmd=<crew cmd>]
//     Attaches a camera to the raft at the given offset and takes a burst of
//     frames, optionally with the crew paddling — the raft-relative stroke
//     review the fixed-camera CaptureSeries cannot give.
//
//   RaftSim.ManoeuvreCheck <label>
//     Runs a fixed crew-command timeline (forward, stop, back, turns) and
//     logs speed/heading once a second so accelerations and turn rates can
//     be checked against expectations.

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "Misc/Paths.h"
#include "RaftSimCameraPresentation.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "TimerManager.h"
#include "UnrealClient.h"

namespace RaftSimSurveyCommand
{

static ARaftSimRaftActor* FindRaft(UWorld* World)
{
    if (World == nullptr)
    {
        return nullptr;
    }
    for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It)
    {
        return *It;
    }
    return nullptr;
}

static URaftSimPhysicsBridgeSubsystem* FindBridge(UWorld* World)
{
    if (World == nullptr)
    {
        return nullptr;
    }
    if (const UGameInstance* GameInstance = World->GetGameInstance())
    {
        return GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    }
    return nullptr;
}

static URaftSimWaterRuntimeAdapter* FindWater(UWorld* World)
{
    URaftSimPhysicsBridgeSubsystem* Bridge = FindBridge(World);
    return Bridge ? Bridge->GetWaterRuntime() : nullptr;
}

static ACameraActor* PlaceCamera(
    UWorld* World, ACameraActor* Existing, const FVector& Location, const FRotator& Rotation)
{
    ACameraActor* Camera = Existing;
    if (Camera == nullptr)
    {
        Camera = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), Location, Rotation);
        if (Camera)
        {
            RaftSimCameraPresentation::Configure(Camera->GetCameraComponent());
        }
    }
    else
    {
        Camera->SetActorLocationAndRotation(Location, Rotation);
    }
    if (Camera)
    {
        if (APlayerController* PC = World->GetFirstPlayerController())
        {
            PC->SetViewTarget(Camera);
        }
    }
    return Camera;
}

static FString ScreenshotPath(const FString& Name)
{
    return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Name + TEXT(".png"));
}

static const TCHAR* CrewCommandName(ERaftSimCrewCommand Command)
{
    switch (Command)
    {
    case ERaftSimCrewCommand::Rest: return TEXT("Rest");
    case ERaftSimCrewCommand::AllForward: return TEXT("AllForward");
    case ERaftSimCrewCommand::AllBackward: return TEXT("AllBackward");
    case ERaftSimCrewCommand::TurnLeft: return TEXT("TurnLeft");
    case ERaftSimCrewCommand::TurnRight: return TEXT("TurnRight");
    case ERaftSimCrewCommand::Stop: return TEXT("Stop");
    case ERaftSimCrewCommand::GetDown: return TEXT("GetDown");
    case ERaftSimCrewCommand::HighSide: return TEXT("HighSide");
    }
    return TEXT("?");
}

static bool ParseCrewCommand(const FString& Name, ERaftSimCrewCommand& OutCommand)
{
    static const ERaftSimCrewCommand All[] = {
        ERaftSimCrewCommand::Rest, ERaftSimCrewCommand::AllForward,
        ERaftSimCrewCommand::AllBackward, ERaftSimCrewCommand::TurnLeft,
        ERaftSimCrewCommand::TurnRight, ERaftSimCrewCommand::Stop,
        ERaftSimCrewCommand::GetDown, ERaftSimCrewCommand::HighSide};
    for (ERaftSimCrewCommand Command : All)
    {
        if (Name.Equals(CrewCommandName(Command), ESearchCase::IgnoreCase))
        {
            OutCommand = Command;
            return true;
        }
    }
    return false;
}

// ---------------------------------------------------------------------------
// SurveyReach
// ---------------------------------------------------------------------------

struct FSurveyState
{
    enum class EPhase : uint8 { Hop, Settle, ChaseShot, ChaseShot2, SideShot, Telemetry, Done };

    TWeakObjectPtr<UWorld> World;
    FString Label;
    float StepM = 100.0f;
    float SettleSeconds = 4.0f;
    float RadiusM = 40.0f;
    TArray<float> Stations;
    int32 StationIndex = 0;
    EPhase Phase = EPhase::Hop;
    double PhaseStartSeconds = 0.0;
    int32 HopCount = 0;
    int32 StationHops = 0;
    int32 UnreachableCount = 0;
    float BestWorldErrorM = TNumericLimits<float>::Max();
    TWeakObjectPtr<ACameraActor> ChaseCamera;
    TWeakObjectPtr<ACameraActor> SideCamera;
    FTimerHandle Timer;
    int32 AnomalyTotal = 0;
    int32 StationsWithAnomalies = 0;
};

static FString StationTag(const FSurveyState& State)
{
    return FString::Printf(TEXT("%s_%03d_%05.0fm"), *State.Label, State.StationIndex,
        State.Stations.IsValidIndex(State.StationIndex) ? State.Stations[State.StationIndex] : 0.0f);
}

static void LogSurveyStation(FSurveyState& State)
{
    UWorld* World = State.World.Get();
    ARaftSimRaftActor* Raft = FindRaft(World);
    URaftSimWaterRuntimeAdapter* Water = FindWater(World);
    URaftSimPhysicsBridgeSubsystem* Bridge = FindBridge(World);
    if (!World || !Raft || !Water)
    {
        return;
    }
    const FVector RaftLocation = Raft->GetActorLocation();
    const float StationM = State.Stations[State.StationIndex];
    TArray<FString> Anomalies;

    // Raft support / physics at rest.
    FRaftSimWaterSample Centre;
    const bool bCentreSampled = Water->SampleWaterAtWorldPosition(RaftLocation, Centre);
    FRaftSimWaterSample Support;
    const bool bSupportSampled =
        Water->SampleRaftSupportSurfaceAtWorldPosition(RaftLocation, Support) && Support.bWet;
    const float SupportZCm = bSupportSampled
        ? Support.SurfaceHeightMeters * 100.0f
        : (bCentreSampled ? Centre.SurfaceHeightMeters * 100.0f : 0.0f);
    float FloorZCm = 0.0f;
    const bool bHasFloor = Raft->GetRenderedFloorCenterWorldZCm(FloorZCm);
    const float FreeboardCm = bHasFloor ? FloorZCm - SupportZCm : 0.0f;
    const FVector Velocity = Raft->GetRaftVelocity();
    const float SpeedMps = Velocity.Size();
    const float WaterSpeedMps = (bCentreSampled && Centre.bWet)
        ? Centre.VelocityMetersPerSecond.Size2D() : 0.0f;
    const URaftSimChronoRuntimeAdapter* RaftRuntime = Bridge ? Bridge->GetRaftRuntime() : nullptr;
    const int32 DryPoints = RaftRuntime ? RaftRuntime->GetLastDrySupportPointCount() : -1;
    const int32 GroundPoints = RaftRuntime ? RaftRuntime->GetLastGroundedSupportPointCount() : -1;
    const float GroundPenetrationM =
        RaftRuntime ? RaftRuntime->GetLastMaximumGroundPenetrationMeters() : 0.0f;
    const FRotator Rotation = Raft->GetActorRotation();
    const FRaftSimRaftConditionState Condition = Raft->GetRaftCondition();

    FVector2D RiverPosition(StationM, 0.0f);
    FVector Tangent = FVector::ForwardVector;
    FVector LeftNormal = FVector::RightVector;
    Water->WorldToRiverCoordinates(RaftLocation, RiverPosition, Tangent, LeftNormal);
    const float HeadingDeg = Rotation.Yaw;
    const float TangentDeg = FMath::RadiansToDegrees(FMath::Atan2(Tangent.Y, Tangent.X));
    const float HeadingErrorDeg = FMath::FindDeltaAngleDegrees(TangentDeg, HeadingDeg);

    if (!bCentreSampled || !Centre.bWet)
    {
        Anomalies.Add(TEXT("raft_centre_dry"));
    }
    if (bHasFloor && (FreeboardCm < -5.0f || FreeboardCm > 60.0f))
    {
        Anomalies.Add(FString::Printf(TEXT("freeboard_%.0fcm"), FreeboardCm));
    }
    if (GroundPoints > 0)
    {
        Anomalies.Add(FString::Printf(TEXT("grounded_%d"), GroundPoints));
    }
    if (FMath::Abs(Rotation.Pitch) > 15.0f || FMath::Abs(Rotation.Roll) > 15.0f)
    {
        Anomalies.Add(FString::Printf(TEXT("attitude_p%.0f_r%.0f"), Rotation.Pitch, Rotation.Roll));
    }
    if (Condition.PressureFraction < 0.95f || Condition.FabricIntegrity < 0.95f)
    {
        Anomalies.Add(TEXT("raft_damaged"));
    }
    if (FMath::Abs(RiverPosition.Y) > 12.0f)
    {
        Anomalies.Add(FString::Printf(TEXT("off_centre_%.1fm"), RiverPosition.Y));
    }

    // Water sweep: 5 m along the corridor over +/- StepM/2 (capped) on the
    // centreline and 6 m to each side.
    const float HalfSpanM = FMath::Min(State.StepM * 0.5f, 60.0f);
    int32 SweepSamples = 0;
    int32 DryCentre = 0;
    int32 DrySides = 0;
    int32 Stagnant = 0;
    int32 Torrent = 0;
    float MaxStepDropM = 0.0f;
    float MaxStepRiseM = 0.0f;
    float MaxLateralTiltM = 0.0f;
    float MinVelocity = TNumericLimits<float>::Max();
    float MaxVelocity = 0.0f;
    float MinDepthM = TNumericLimits<float>::Max();
    float PreviousCentreZ = 0.0f;
    bool bHavePrevious = false;
    const float DatumM = Water->GetRiverVerticalDatumM();
    for (float Offset = -HalfSpanM; Offset <= HalfSpanM + 0.01f; Offset += 5.0f)
    {
        FVector CentreWorld;
        FVector LeftWorld;
        FVector RightWorld;
        if (!Water->RiverToWorldPosition(FVector2D(StationM + Offset, 0.0f), DatumM, CentreWorld) ||
            !Water->RiverToWorldPosition(FVector2D(StationM + Offset, 6.0f), DatumM, LeftWorld) ||
            !Water->RiverToWorldPosition(FVector2D(StationM + Offset, -6.0f), DatumM, RightWorld))
        {
            continue;
        }
        ++SweepSamples;
        FRaftSimWaterSample CentreSample;
        FRaftSimWaterSample LeftSample;
        FRaftSimWaterSample RightSample;
        const bool bCentreWet =
            Water->SampleWaterAtWorldPosition(CentreWorld, CentreSample) && CentreSample.bWet;
        const bool bLeftWet =
            Water->SampleWaterAtWorldPosition(LeftWorld, LeftSample) && LeftSample.bWet;
        const bool bRightWet =
            Water->SampleWaterAtWorldPosition(RightWorld, RightSample) && RightSample.bWet;
        if (!bCentreWet)
        {
            ++DryCentre;
            bHavePrevious = false;
            continue;
        }
        if (!bLeftWet)
        {
            ++DrySides;
        }
        if (!bRightWet)
        {
            ++DrySides;
        }
        const float Speed = CentreSample.VelocityMetersPerSecond.Size2D();
        MinVelocity = FMath::Min(MinVelocity, Speed);
        MaxVelocity = FMath::Max(MaxVelocity, Speed);
        MinDepthM = FMath::Min(MinDepthM, CentreSample.DepthMeters);
        if (Speed < 0.05f)
        {
            ++Stagnant;
        }
        if (Speed > 8.0f)
        {
            ++Torrent;
        }
        if (bHavePrevious)
        {
            const float Delta = CentreSample.SurfaceHeightMeters - PreviousCentreZ;
            MaxStepDropM = FMath::Max(MaxStepDropM, -Delta);
            MaxStepRiseM = FMath::Max(MaxStepRiseM, Delta);
        }
        PreviousCentreZ = CentreSample.SurfaceHeightMeters;
        bHavePrevious = true;
        if (bLeftWet && bRightWet)
        {
            MaxLateralTiltM = FMath::Max(
                MaxLateralTiltM,
                FMath::Abs(LeftSample.SurfaceHeightMeters - RightSample.SurfaceHeightMeters));
        }
    }
    if (SweepSamples == 0)
    {
        MinVelocity = 0.0f;
        MinDepthM = 0.0f;
    }
    if (DryCentre > 0)
    {
        Anomalies.Add(FString::Printf(TEXT("dry_centreline_%d"), DryCentre));
    }
    if (Stagnant > 0)
    {
        Anomalies.Add(FString::Printf(TEXT("stagnant_%d"), Stagnant));
    }
    if (Torrent > 0)
    {
        Anomalies.Add(FString::Printf(TEXT("torrent_%d"), Torrent));
    }
    if (MaxStepRiseM > 0.5f)
    {
        Anomalies.Add(FString::Printf(TEXT("surface_rises_%.2fm_per_5m"), MaxStepRiseM));
    }
    if (MaxStepDropM > 1.0f)
    {
        Anomalies.Add(FString::Printf(TEXT("surface_drop_%.2fm_per_5m"), MaxStepDropM));
    }
    if (MaxLateralTiltM > 0.6f)
    {
        Anomalies.Add(FString::Printf(TEXT("lateral_tilt_%.2fm_over_12m"), MaxLateralTiltM));
    }

    // Rocks: authoritative obstacle actors and dressing boulder instances
    // within RadiusM; obstacle actors are checked against the local surface.
    const float RadiusCm = State.RadiusM * 100.0f;
    int32 ObstacleCount = 0;
    int32 FloatingObstacles = 0;
    int32 DrownedObstacles = 0;
    for (TActorIterator<ARaftSimRockObstacleActor> It(World); It; ++It)
    {
        ARaftSimRockObstacleActor* Rock = *It;
        if (!Rock || FVector::Dist2D(Rock->GetActorLocation(), RaftLocation) > RadiusCm)
        {
            continue;
        }
        ++ObstacleCount;
        FVector Origin;
        FVector Extent;
        Rock->GetActorBounds(false, Origin, Extent);
        FRaftSimWaterSample RockSample;
        if (Water->SampleWaterAtWorldPosition(Rock->GetActorLocation(), RockSample) && RockSample.bWet)
        {
            const float SurfaceZ = RockSample.SurfaceHeightMeters * 100.0f;
            if (Origin.Z - Extent.Z > SurfaceZ + 100.0f)
            {
                ++FloatingObstacles;
            }
            else if (Origin.Z + Extent.Z < SurfaceZ - 100.0f)
            {
                ++DrownedObstacles;
            }
        }
    }
    int32 DressingRockInstances = 0;
    int32 DressingRockComponents = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->ActorHasTag(TEXT("RaftSimFullReachDressing")))
        {
            continue;
        }
        TInlineComponentArray<UHierarchicalInstancedStaticMeshComponent*> Components(Actor);
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (!Component || !Component->GetStaticMesh())
            {
                continue;
            }
            const FString MeshName = Component->GetStaticMesh()->GetName();
            const FString ComponentName = Component->GetName();
            if (!MeshName.Contains(TEXT("Boulder")) && !MeshName.Contains(TEXT("Rock")) &&
                !ComponentName.Contains(TEXT("Rock")) && !ComponentName.Contains(TEXT("Boulder")))
            {
                continue;
            }
            if (!Component->Bounds.GetBox().ExpandBy(RadiusCm).IsInsideXY(RaftLocation))
            {
                continue;
            }
            ++DressingRockComponents;
            const int32 InstanceCount = Component->GetInstanceCount();
            for (int32 Index = 0; Index < InstanceCount; ++Index)
            {
                FTransform InstanceTransform;
                if (Component->GetInstanceTransform(Index, InstanceTransform, true) &&
                    FVector::Dist2D(InstanceTransform.GetLocation(), RaftLocation) <= RadiusCm)
                {
                    ++DressingRockInstances;
                }
            }
        }
    }

    // Terrain under the corridor centreline at this station: a landscape
    // surface above the water surface means the channel is buried.
    float TerrainZCm = 0.0f;
    float TerrainClearanceCm = 0.0f;
    bool bTerrainHit = false;
    {
        FVector CentreWorld;
        if (Water->RiverToWorldPosition(FVector2D(StationM, 0.0f), DatumM, CentreWorld))
        {
            // Water tiles and dressing sit in the same channel, so take the
            // first hit that belongs to a terrain tile rather than the first
            // hit of any kind.
            TArray<FHitResult> Hits;
            FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimSurveyTerrain), true);
            Params.AddIgnoredActor(Raft);
            const FVector TraceStart(CentreWorld.X, CentreWorld.Y, RaftLocation.Z + 20000.0f);
            const FVector TraceEnd(CentreWorld.X, CentreWorld.Y, RaftLocation.Z - 20000.0f);
            World->LineTraceMultiByChannel(Hits, TraceStart, TraceEnd, ECC_WorldStatic, Params);
            for (const FHitResult& Hit : Hits)
            {
                if (Hit.GetActor() && Hit.GetActor()->ActorHasTag(TEXT("RaftSimFullReachTerrain")))
                {
                    bTerrainHit = true;
                    TerrainZCm = Hit.ImpactPoint.Z;
                    TerrainClearanceCm = SupportZCm - TerrainZCm;
                    if (bCentreSampled && Centre.bWet && TerrainClearanceCm < -20.0f)
                    {
                        Anomalies.Add(FString::Printf(TEXT("terrain_above_water_%.0fcm"), -TerrainClearanceCm));
                    }
                    break;
                }
            }
        }
    }
    if (Anomalies.Num() > 0)
    {
        ++State.StationsWithAnomalies;
        State.AnomalyTotal += Anomalies.Num();
    }
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim survey terrain: index=%d station_m=%.0f terrain_hit=%d terrain_z_cm=%.0f terrain_clearance_cm=%.0f"),
        State.StationIndex, StationM, bTerrainHit ? 1 : 0, TerrainZCm, TerrainClearanceCm);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim survey station: index=%d station_m=%.0f x_cm=%.0f y_cm=%.0f z_cm=%.0f ")
        TEXT("lateral_m=%.2f raft_speed_mps=%.2f water_speed_mps=%.2f heading_err_deg=%.1f ")
        TEXT("wet=%d depth_m=%.2f surface_z_cm=%.0f freeboard_cm=%.1f dry_points=%d ground_points=%d ")
        TEXT("ground_penetration_m=%.3f pitch_deg=%.1f roll_deg=%.1f pressure=%.2f integrity=%.2f ")
        TEXT("sweep_samples=%d sweep_dry_centre=%d sweep_dry_sides=%d sweep_stagnant=%d ")
        TEXT("sweep_v_min=%.2f sweep_v_max=%.2f sweep_depth_min=%.2f sweep_step_drop_m=%.2f ")
        TEXT("sweep_step_rise_m=%.2f sweep_lateral_tilt_m=%.2f obstacles=%d obstacles_floating=%d ")
        TEXT("obstacles_drowned=%d dressing_rock_components=%d dressing_rock_instances=%d ")
        TEXT("anomalies=%s"),
        State.StationIndex, StationM, RaftLocation.X, RaftLocation.Y, RaftLocation.Z,
        RiverPosition.Y, SpeedMps, WaterSpeedMps, HeadingErrorDeg,
        (bCentreSampled && Centre.bWet) ? 1 : 0,
        bCentreSampled ? Centre.DepthMeters : 0.0f,
        SupportZCm, FreeboardCm, DryPoints, GroundPoints,
        GroundPenetrationM, Rotation.Pitch, Rotation.Roll,
        Condition.PressureFraction, Condition.FabricIntegrity,
        SweepSamples, DryCentre, DrySides, Stagnant,
        MinVelocity, MaxVelocity, MinDepthM, MaxStepDropM,
        MaxStepRiseM, MaxLateralTiltM, ObstacleCount, FloatingObstacles,
        DrownedObstacles, DressingRockComponents, DressingRockInstances,
        Anomalies.Num() > 0 ? *FString::Join(Anomalies, TEXT(",")) : TEXT("none"));
}

static void SurveyTick(TSharedRef<FSurveyState> State)
{
    UWorld* World = State->World.Get();
    ARaftSimRaftActor* Raft = FindRaft(World);
    URaftSimWaterRuntimeAdapter* Water = FindWater(World);
    if (!World || !Raft || !Water)
    {
        return;
    }
    const double Now = World->GetTimeSeconds();
    if (State->StationIndex >= State->Stations.Num())
    {
        State->Phase = FSurveyState::EPhase::Done;
    }
    switch (State->Phase)
    {
    case FSurveyState::EPhase::Hop:
    {
        const float TargetStationM = State->Stations[State->StationIndex];
        FVector2D RiverPosition;
        FVector Tangent;
        FVector LeftNormal;
        FVector TargetWorldCm;
        FVector TargetAheadCm;
        if (!Water->RiverToWorldPosition(FVector2D(TargetStationM, 0.0f), Water->GetRiverVerticalDatumM(), TargetWorldCm) ||
            !Water->RiverToWorldPosition(FVector2D(TargetStationM + 1.0f, 0.0f), Water->GetRiverVerticalDatumM(), TargetAheadCm))
        {
            UE_LOG(LogTemp, Warning,
                TEXT("RaftSim survey unreachable: index=%d station_m=%.0f reason=no_forward_map"),
                State->StationIndex, TargetStationM);
            ++State->UnreachableCount;
            ++State->StationIndex;
            State->StationHops = 0;
            return;
        }
        // Teleport height: never inside the landscape. Trace the terrain at
        // the destination and stand the raft a metre above it (or above the
        // water surface when the field is wet there); a hop that kept the
        // old Z buried the raft in a rising bank at 9300 m and the physics
        // ejected it 550 m off-corridor at 50 m/s.
        const auto SafeTeleportZ = [World, Raft, Water](const FVector& XYCm, float FallbackZCm)
        {
            // Prefer the local water surface; when the live window has not
            // reached the destination yet, stand the raft just above the
            // tagged riverbed instead of carrying the upstream Z along —
            // dropping onto the water from a few metres tumbled the raft
            // and tripped the capsize latch (dense 9200–9700 re-walk).
            float ZCm = FallbackZCm;
            bool bResolved = false;
            FRaftSimWaterSample Sample;
            if (Water->SampleWaterAtWorldPosition(FVector(XYCm.X, XYCm.Y, FallbackZCm), Sample) && Sample.bWet)
            {
                ZCm = Sample.SurfaceHeightMeters * 100.0f + 40.0f;
                bResolved = true;
            }
            // Only the tagged near-terrain tiles count: a coarse far-terrain
            // proxy spans the valley tens of metres above the river and is
            // collidable, and the first-hit version of this trace stood the
            // raft on it (2400 m, iso_base run).
            TArray<FHitResult> Hits;
            FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimSurveyHop), true);
            Params.AddIgnoredActor(Raft);
            World->LineTraceMultiByChannel(
                Hits,
                FVector(XYCm.X, XYCm.Y, FallbackZCm + 30000.0f),
                FVector(XYCm.X, XYCm.Y, FallbackZCm - 30000.0f),
                ECC_WorldStatic, Params);
            for (const FHitResult& Hit : Hits)
            {
                if (Hit.GetActor() && Hit.GetActor()->ActorHasTag(TEXT("RaftSimFullReachTerrain")))
                {
                    ZCm = bResolved
                        ? FMath::Max(ZCm, Hit.ImpactPoint.Z + 100.0f)
                        : Hit.ImpactPoint.Z + 150.0f;
                    break;
                }
            }
            return ZCm;
        };
        if (!Water->WorldToRiverCoordinates(Raft->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
        {
            // Off the corridor (ejected or lost): jump straight to the
            // target point and let the settle phase drop it onto the water.
            FVector Recovery = TargetWorldCm;
            Recovery.Z = SafeTeleportZ(TargetWorldCm, Raft->GetActorLocation().Z);
            Raft->TeleportForTesting(Recovery, (TargetAheadCm - TargetWorldCm).Rotation().Yaw, true);
            ++State->HopCount;
            ++State->StationHops;
            UE_LOG(LogTemp, Warning,
                TEXT("RaftSim survey recovery: index=%d station_m=%.0f raft was off-corridor; teleported to the station point"),
                State->StationIndex, TargetStationM);
            if (State->StationHops >= 10)
            {
                ++State->UnreachableCount;
                ++State->StationIndex;
                State->StationHops = 0;
                State->BestWorldErrorM = TNumericLimits<float>::Max();
            }
            return;
        }
        const float RemainingM = TargetStationM - RiverPosition.X;
        // Converge on WORLD distance to the target point: the corridor's
        // forward and inverse maps disagree by tens of metres around folds
        // (station ~7600 m), so a station-projection test never settles there.
        const float WorldErrorM = FVector::Dist2D(Raft->GetActorLocation(), TargetWorldCm) / 100.0f;
        if (WorldErrorM < 6.0f ||
            (FMath::Abs(RemainingM) < 3.0f && FMath::Abs(RiverPosition.Y) < 6.0f))
        {
            State->Phase = FSurveyState::EPhase::Settle;
            State->PhaseStartSeconds = Now;
            State->StationHops = 0;
            State->BestWorldErrorM = TNumericLimits<float>::Max();
            return;
        }
        // Only hops that fail to close the world distance count toward the
        // give-up bound: a long walk-in from the spawn needs ~90 hops.
        if (WorldErrorM < State->BestWorldErrorM - 1.0f)
        {
            State->BestWorldErrorM = WorldErrorM;
            State->StationHops = 0;
        }
        if (State->StationHops >= 10)
        {
            UE_LOG(LogTemp, Warning,
                TEXT("RaftSim survey unreachable: index=%d station_m=%.0f projected_station_m=%.1f lateral_m=%.1f world_error_m=%.1f hops=%d"),
                State->StationIndex, TargetStationM, RiverPosition.X, RiverPosition.Y,
                WorldErrorM, State->StationHops);
            ++State->UnreachableCount;
            ++State->StationIndex;
            State->StationHops = 0;
            State->BestWorldErrorM = TNumericLimits<float>::Max();
            return;
        }
        const float StepStationM = RiverPosition.X + FMath::Clamp(RemainingM, -79.0f, 79.0f);
        FVector StepWorldCm;
        FVector AheadWorldCm;
        if (!Water->RiverToWorldPosition(FVector2D(StepStationM, 0.0f), Water->GetRiverVerticalDatumM(), StepWorldCm) ||
            !Water->RiverToWorldPosition(FVector2D(StepStationM + 1.0f, 0.0f), Water->GetRiverVerticalDatumM(), AheadWorldCm))
        {
            ++State->StationHops;
            return;
        }
        // Hop by world distance when the projection is unreliable: never
        // teleport further than 79 m in the world either.
        FVector HopDelta = StepWorldCm - Raft->GetActorLocation();
        HopDelta.Z = 0.0f;
        if (HopDelta.Size() > 7900.0f)
        {
            StepWorldCm = Raft->GetActorLocation() + HopDelta.GetSafeNormal() * 7900.0f;
        }
        StepWorldCm.Z = SafeTeleportZ(StepWorldCm, Raft->GetActorLocation().Z);
        Raft->TeleportForTesting(StepWorldCm, (AheadWorldCm - StepWorldCm).Rotation().Yaw, true);
        ++State->HopCount;
        ++State->StationHops;
        return;
    }
    case FSurveyState::EPhase::Settle:
        if (Now - State->PhaseStartSeconds >= State->SettleSeconds)
        {
            State->Phase = FSurveyState::EPhase::ChaseShot;
        }
        return;
    case FSurveyState::EPhase::ChaseShot:
    case FSurveyState::EPhase::ChaseShot2:
    {
        const FVector RaftLocation = Raft->GetActorLocation();
        FVector Forward = Raft->GetActorForwardVector();
        Forward.Z = 0.0f;
        Forward = Forward.GetSafeNormal();
        if (Forward.IsNearlyZero())
        {
            Forward = FVector::ForwardVector;
        }
        const FVector CameraLocation = RaftLocation - Forward * 800.0f + FVector(0.0f, 0.0f, 350.0f);
        const FVector LookAt = RaftLocation + Forward * 1500.0f - FVector(0.0f, 0.0f, 120.0f);
        State->ChaseCamera = PlaceCamera(
            World, State->ChaseCamera.Get(), CameraLocation, (LookAt - CameraLocation).Rotation());
        const bool bSecond = State->Phase == FSurveyState::EPhase::ChaseShot2;
        FScreenshotRequest::RequestScreenshot(
            ScreenshotPath(StationTag(*State) + (bSecond ? TEXT("_chase2") : TEXT("_chase"))),
            false, false);
        State->Phase = bSecond ? FSurveyState::EPhase::SideShot : FSurveyState::EPhase::ChaseShot2;
        return;
    }
    case FSurveyState::EPhase::SideShot:
    {
        const FVector RaftLocation = Raft->GetActorLocation();
        FVector2D RiverPosition;
        FVector Tangent;
        FVector LeftNormal;
        FVector Side = -Raft->GetActorRightVector();
        if (Water->WorldToRiverCoordinates(RaftLocation, RiverPosition, Tangent, LeftNormal))
        {
            Side = LeftNormal.GetSafeNormal2D();
        }
        const FVector CameraLocation = RaftLocation + Side * 1200.0f + FVector(0.0f, 0.0f, 250.0f);
        const FVector LookAt = RaftLocation + FVector(0.0f, 0.0f, 40.0f);
        State->SideCamera = PlaceCamera(
            World, State->SideCamera.Get(), CameraLocation, (LookAt - CameraLocation).Rotation());
        FScreenshotRequest::RequestScreenshot(
            ScreenshotPath(StationTag(*State) + TEXT("_side")), false, false);
        State->Phase = FSurveyState::EPhase::Telemetry;
        return;
    }
    case FSurveyState::EPhase::Telemetry:
        LogSurveyStation(*State);
        ++State->StationIndex;
        State->Phase = FSurveyState::EPhase::Hop;
        return;
    case FSurveyState::EPhase::Done:
    {
        World->GetTimerManager().ClearTimer(State->Timer);
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim survey complete: stations=%d hops=%d unreachable=%d stations_with_anomalies=%d anomalies=%d"),
            State->Stations.Num(), State->HopCount, State->UnreachableCount,
            State->StationsWithAnomalies, State->AnomalyTotal);
        FTimerHandle ExitHandle;
        World->GetTimerManager().SetTimer(
            ExitHandle,
            FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
            3.0f, false);
        return;
    }
    }
}

static void HandleSurveyReach(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr || Args.Num() < 5)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim.SurveyReach <startM> <endM> <stepM> <settleS> <label> [radiusM]"));
        return;
    }
    TSharedRef<FSurveyState> State = MakeShared<FSurveyState>();
    State->World = World;
    const float StartM = FCString::Atof(*Args[0]);
    const float EndM = FCString::Atof(*Args[1]);
    State->StepM = FMath::Max(FCString::Atof(*Args[2]), 5.0f);
    State->SettleSeconds = FMath::Max(FCString::Atof(*Args[3]), 0.5f);
    State->Label = Args[4];
    State->RadiusM = Args.Num() > 5 ? FMath::Max(FCString::Atof(*Args[5]), 5.0f) : 40.0f;
    TWeakObjectPtr<UWorld> WeakWorld(World);
    // Start after the raft and window exist; clamp the requested span to the
    // corridor the water adapter actually knows.
    FTimerHandle StartHandle;
    World->GetTimerManager().SetTimer(
        StartHandle,
        FTimerDelegate::CreateLambda([WeakWorld, State, StartM, EndM]()
        {
            UWorld* W = WeakWorld.Get();
            URaftSimWaterRuntimeAdapter* Water = FindWater(W);
            if (!W || !Water)
            {
                UE_LOG(LogTemp, Error, TEXT("RaftSim.SurveyReach: no world or water runtime"));
                return;
            }
            float MinStationM = 0.0f;
            float MaxStationM = 0.0f;
            if (!Water->GetRiverStationRangeM(MinStationM, MaxStationM))
            {
                UE_LOG(LogTemp, Error, TEXT("RaftSim.SurveyReach: no river coordinate map bound"));
                return;
            }
            const float FirstM = FMath::Clamp(StartM, MinStationM, MaxStationM);
            const float LastM = FMath::Clamp(EndM <= 0.0f ? MaxStationM : EndM, MinStationM, MaxStationM);
            for (float StationM = FirstM; StationM <= LastM + 0.01f; StationM += State->StepM)
            {
                State->Stations.Add(StationM);
            }
            UE_LOG(LogTemp, Display,
                TEXT("RaftSim.SurveyReach: corridor %.0f..%.0f m, surveying %d stations from %.0f to %.0f every %.0f m (settle %.1f s)"),
                MinStationM, MaxStationM, State->Stations.Num(), FirstM, LastM, State->StepM,
                State->SettleSeconds);
            W->GetTimerManager().SetTimer(
                State->Timer,
                FTimerDelegate::CreateLambda([State]() { SurveyTick(State); }),
                0.4f, true, 0.0f);
        }),
        4.0f, false);
}

static FAutoConsoleCommandWithWorldAndArgs GSurveyReachCommand(
    TEXT("RaftSim.SurveyReach"),
    TEXT("Walk the raft down the river corridor, photographing and logging every station. "
         "Usage: RaftSim.SurveyReach <startM> <endM> <stepM> <settleS> <label> [radiusM]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleSurveyReach));

// ---------------------------------------------------------------------------
// CaptureRaftSeries
// ---------------------------------------------------------------------------

static void HandleCaptureRaftSeries(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr || Args.Num() < 8)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim.CaptureRaftSeries <delay> <count> <interval> <label> <backM> <sideM> <upM> <aheadM> [paddle] [cmd=<crew cmd>]"));
        return;
    }
    const float Delay = FMath::Max(FCString::Atof(*Args[0]), 0.5f);
    const int32 Count = FMath::Clamp(FCString::Atoi(*Args[1]), 1, 200);
    const float Interval = FMath::Max(FCString::Atof(*Args[2]), 0.05f);
    const FString Label = Args[3];
    const FVector RelativeLocation(
        -FCString::Atof(*Args[4]) * 100.0f,
        FCString::Atof(*Args[5]) * 100.0f,
        FCString::Atof(*Args[6]) * 100.0f);
    const float AheadM = FCString::Atof(*Args[7]);
    bool bPaddle = false;
    ERaftSimCrewCommand Command = ERaftSimCrewCommand::AllForward;
    for (int32 Index = 8; Index < Args.Num(); ++Index)
    {
        if (Args[Index].Equals(TEXT("paddle"), ESearchCase::IgnoreCase))
        {
            bPaddle = true;
        }
        else if (Args[Index].StartsWith(TEXT("cmd="), ESearchCase::IgnoreCase))
        {
            bPaddle = ParseCrewCommand(Args[Index].RightChop(4), Command) || bPaddle;
        }
    }
    TWeakObjectPtr<UWorld> WeakWorld(World);
    if (bPaddle)
    {
        FTimerHandle PaddleHandle;
        World->GetTimerManager().SetTimer(
            PaddleHandle,
            FTimerDelegate::CreateLambda([WeakWorld, Command]()
            {
                if (ARaftSimRaftActor* Raft = FindRaft(WeakWorld.Get()))
                {
                    Raft->IssueCrewCommand(Command);
                }
            }),
            1.0f, false);
    }
    FTimerHandle StartHandle;
    World->GetTimerManager().SetTimer(
        StartHandle,
        FTimerDelegate::CreateLambda([WeakWorld, Count, Interval, Label, RelativeLocation, AheadM]()
        {
            UWorld* W = WeakWorld.Get();
            ARaftSimRaftActor* Raft = FindRaft(W);
            if (!W || !Raft)
            {
                return;
            }
            ACameraActor* Camera = W->SpawnActor<ACameraActor>(
                ACameraActor::StaticClass(), Raft->GetActorLocation(), FRotator::ZeroRotator);
            if (!Camera)
            {
                return;
            }
            RaftSimCameraPresentation::Configure(Camera->GetCameraComponent());
            Camera->AttachToActor(Raft, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
            const FVector LookAtRelative(AheadM * 100.0f, 0.0f, 60.0f);
            Camera->SetActorRelativeLocation(RelativeLocation);
            Camera->SetActorRelativeRotation((LookAtRelative - RelativeLocation).Rotation());
            if (APlayerController* PC = W->GetFirstPlayerController())
            {
                PC->SetViewTarget(Camera);
            }
            TSharedRef<int32> Taken = MakeShared<int32>(0);
            TSharedRef<FTimerHandle> LoopHandle = MakeShared<FTimerHandle>();
            W->GetTimerManager().SetTimer(
                *LoopHandle,
                FTimerDelegate::CreateLambda([WeakWorld, Taken, Count, Label, LoopHandle]()
                {
                    UWorld* W2 = WeakWorld.Get();
                    if (!W2)
                    {
                        return;
                    }
                    FScreenshotRequest::RequestScreenshot(
                        ScreenshotPath(FString::Printf(TEXT("%s_%03d"), *Label, *Taken)), false, false);
                    if (ARaftSimRaftActor* Raft2 = FindRaft(W2))
                    {
                        UE_LOG(LogTemp, Display,
                            TEXT("RaftSim.CaptureRaftSeries: frame %d speed=%.2f cmd=%s"),
                            *Taken, Raft2->GetRaftVelocity().Size(),
                            CrewCommandName(Raft2->GetActiveCrewCommand()));
                    }
                    ++(*Taken);
                    if (*Taken >= Count)
                    {
                        W2->GetTimerManager().ClearTimer(*LoopHandle);
                        FTimerHandle ExitHandle;
                        W2->GetTimerManager().SetTimer(
                            ExitHandle,
                            FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                            3.0f, false);
                    }
                }),
                Interval, true, 0.3f);
        }),
        Delay, false);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim.CaptureRaftSeries: %d frames every %.2fs from a raft-attached camera in %.1fs -> %s_NNN.png"),
        Count, Interval, Delay, *Label);
}

static FAutoConsoleCommandWithWorldAndArgs GCaptureRaftSeriesCommand(
    TEXT("RaftSim.CaptureRaftSeries"),
    TEXT("Burst of frames from a camera attached to the raft. Usage: RaftSim.CaptureRaftSeries "
         "<delay> <count> <interval> <label> <backM> <sideM> <upM> <aheadM> [paddle] [cmd=<crew cmd>]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleCaptureRaftSeries));

// ---------------------------------------------------------------------------
// ManoeuvreCheck
// ---------------------------------------------------------------------------

static void HandleManoeuvreCheck(const TArray<FString>& Args, UWorld* World)
{
    if (World == nullptr)
    {
        return;
    }
    const FString Label = Args.Num() > 0 ? Args[0] : TEXT("manoeuvre");
    struct FStep { float AtSeconds; ERaftSimCrewCommand Command; };
    static const FStep Timeline[] = {
        {2.0f, ERaftSimCrewCommand::AllForward},
        {14.0f, ERaftSimCrewCommand::Stop},
        {20.0f, ERaftSimCrewCommand::AllBackward},
        {30.0f, ERaftSimCrewCommand::Rest},
        {34.0f, ERaftSimCrewCommand::TurnLeft},
        {44.0f, ERaftSimCrewCommand::TurnRight},
        {54.0f, ERaftSimCrewCommand::Rest}};
    TWeakObjectPtr<UWorld> WeakWorld(World);
    for (const FStep& Step : Timeline)
    {
        FTimerHandle Handle;
        const ERaftSimCrewCommand Command = Step.Command;
        World->GetTimerManager().SetTimer(
            Handle,
            FTimerDelegate::CreateLambda([WeakWorld, Command]()
            {
                if (ARaftSimRaftActor* Raft = FindRaft(WeakWorld.Get()))
                {
                    Raft->IssueCrewCommand(Command);
                    UE_LOG(LogTemp, Display, TEXT("RaftSim manoeuvre: issued %s"), CrewCommandName(Command));
                }
            }),
            Step.AtSeconds, false);
    }
    TSharedRef<float> PreviousHeading = MakeShared<float>(0.0f);
    TSharedRef<bool> bHavePrevious = MakeShared<bool>(false);
    TSharedRef<FTimerHandle> LoopHandle = MakeShared<FTimerHandle>();
    World->GetTimerManager().SetTimer(
        *LoopHandle,
        FTimerDelegate::CreateLambda([WeakWorld, PreviousHeading, bHavePrevious, LoopHandle, Label]()
        {
            UWorld* W = WeakWorld.Get();
            ARaftSimRaftActor* Raft = FindRaft(W);
            if (!W || !Raft)
            {
                return;
            }
            const float Now = W->GetTimeSeconds();
            const float Heading = Raft->GetActorRotation().Yaw;
            const float YawRate = *bHavePrevious
                ? FMath::FindDeltaAngleDegrees(*PreviousHeading, Heading)
                : 0.0f;
            *PreviousHeading = Heading;
            *bHavePrevious = true;
            float WaterSpeed = 0.0f;
            float AlongWater = 0.0f;
            if (URaftSimWaterRuntimeAdapter* Water = FindWater(W))
            {
                FRaftSimWaterSample Sample;
                if (Water->SampleWaterAtWorldPosition(Raft->GetActorLocation(), Sample) && Sample.bWet)
                {
                    WaterSpeed = Sample.VelocityMetersPerSecond.Size2D();
                    const FVector Flow = Sample.VelocityMetersPerSecond.GetSafeNormal2D();
                    AlongWater = FVector::DotProduct(Raft->GetRaftVelocity(), Flow);
                }
            }
            UE_LOG(LogTemp, Display,
                TEXT("RaftSim manoeuvre: t=%.1f cmd=%s speed=%.2f along_flow=%.2f water=%.2f heading=%.1f yaw_rate_dps=%.1f"),
                Now, CrewCommandName(Raft->GetActiveCrewCommand()), Raft->GetRaftVelocity().Size(),
                AlongWater, WaterSpeed, Heading, YawRate);
            if (Now >= 58.0f)
            {
                W->GetTimerManager().ClearTimer(*LoopHandle);
                FScreenshotRequest::RequestScreenshot(ScreenshotPath(Label + TEXT("_end")), false, false);
                FTimerHandle ExitHandle;
                W->GetTimerManager().SetTimer(
                    ExitHandle,
                    FTimerDelegate::CreateLambda([]() { FPlatformMisc::RequestExit(false); }),
                    3.0f, false);
            }
        }),
        1.0f, true, 1.0f);
}

static FAutoConsoleCommandWithWorldAndArgs GManoeuvreCheckCommand(
    TEXT("RaftSim.ManoeuvreCheck"),
    TEXT("Run a fixed crew-command timeline and log speed/heading each second. "
         "Usage: RaftSim.ManoeuvreCheck [label]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleManoeuvreCheck));

} // namespace RaftSimSurveyCommand
