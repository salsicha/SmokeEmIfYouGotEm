// Diagnostic ride: carry the player raft down the wet centerline to the first
// substantial surface drop (the rapid), then release it to ride in naturally
// while logging the hull against BOTH water heights — the plain solver surface
// and the coupled raft-support surface. Separates "the hull left its surface"
// (physical submersion: center draft grows) from "the surface left the hull"
// (visual divergence: center draft stays flat while the rendered relief
// climbs). Transit uses centerline teleport hops because the moving water
// window only reveals downstream rapids as the raft travels, and a blind
// crew-forward order beaches on the first bend. Telemetry is AddInfo only;
// the only failure conditions are missing infrastructure.

#include "Camera/CameraActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterSurfaceActor.h"
#include "Tests/AutomationCommon.h"
#include "UnrealClient.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimTroublemakerApproachDraftTelemetryTest,
    "RaftSim.P4.TroublemakerApproachDraftTelemetry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkApproachDraftTelemetryTest,
    "RaftSim.P4.SouthForkApproachDraftTelemetry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetApproachTestWorld()
{
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() != nullptr &&
            (Context.WorldType == EWorldType::PIE ||
             Context.WorldType == EWorldType::Game))
        {
            return Context.World();
        }
    }
    return nullptr;
}

struct FRaftSimApproachTelemetryState
{
    enum class EPhase : uint8
    {
        Start,
        Transit,
        Ride,
    };

    // Skip transit straight to this station when >= 0 (named-rapid cruxes sit
    // kilometres downstream of the put-in; hop transit is for local reaches).
    float StartStationM = -1.0f;
    EPhase Phase = EPhase::Start;
    float ElapsedSeconds = 0.0f;
    float LastWorldTimeSeconds = -1.0f;
    float NextHopSeconds = 0.0f;
    int32 HopCount = 0;
    int32 ConsecutiveDryHolds = 0;
    float CurrentStationM = 0.0f;
    float RideStartElapsedSeconds = 0.0f;
    float NextSampleSeconds = 0.0f;
    FVector RideStartLocationCm = FVector::ZeroVector;
    float RideFacingYawDegrees = 0.0f;
    int32 ScreenshotsFired = 0;
    int32 SampleCount = 0;
    float MinCenterDraftCm = TNumericLimits<float>::Max();
    float MaxCenterDraftCm = -TNumericLimits<float>::Max();
    float MinFreeboardCm = TNumericLimits<float>::Max();
    float MaxReliefCm = -TNumericLimits<float>::Max();
    float MaxTravelCm = 0.0f;
};

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
    FRaftSimApproachDriftTelemetryCommand,
    FAutomationTestBase*, Test,
    TSharedPtr<FRaftSimApproachTelemetryState>, State);

bool FRaftSimApproachDriftTelemetryCommand::Update()
{
    constexpr float HopEverySeconds = 0.5f;
    constexpr float HopAdvanceM = 8.0f;
    constexpr int32 MaxHops = 1200;
    constexpr float RapidLookaheadM = 120.0f;
    constexpr float RapidDropThresholdM = 0.45f;
    constexpr float RideReleaseUpstreamM = 40.0f;
    constexpr float RideSeconds = 60.0f;
    constexpr float SampleEverySeconds = 0.5f;
    constexpr float OverallBudgetSeconds = 900.0f;

    UWorld* World = GetApproachTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("Approach telemetry lost the PIE/game world"));
        return true;
    }

    const float WorldTime = World->GetTimeSeconds();
    if (State->LastWorldTimeSeconds >= 0.0f)
    {
        State->ElapsedSeconds +=
            FMath::Max(WorldTime - State->LastWorldTimeSeconds, 0.0f);
    }
    State->LastWorldTimeSeconds = WorldTime;

    ARaftSimRaftActor* Raft = nullptr;
    if (TActorIterator<ARaftSimRaftActor> It(World); It)
    {
        Raft = *It;
    }
    const UGameInstance* GI = World->GetGameInstance();
    URaftSimPhysicsBridgeSubsystem* Bridge =
        GI ? GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    URaftSimWaterRuntimeAdapter* Water =
        Bridge ? Bridge->GetWaterRuntime() : nullptr;
    if (Raft == nullptr || Water == nullptr)
    {
        Test->AddError(TEXT("Approach telemetry needs a raft and water runtime"));
        return true;
    }

    // Wet channel sample at a station. The wetted channel is rarely centred
    // on the river axis — entrance tongues hug a bank and several reaches
    // bend away from lateral zero (Troublemaker's own approach reads dry on
    // the centreline by station ~60 m) — so probe a small lateral fan
    // outward from the axis and adopt the first wet hit. Transit then
    // follows the channel instead of ending at the first off-axis reach.
    const auto SampleWetStation =
        [Water](float StationM, float& OutZCm, FVector& OutWorldCm) -> bool
    {
        constexpr float LateralProbesM[] = {
            0.0f, -4.0f, 4.0f, -8.0f, 8.0f, -12.0f, 12.0f, -16.0f, 16.0f};
        for (const float LateralM : LateralProbesM)
        {
            FRaftSimWaterSample Probe;
            if (Water->SampleWaterAtRiverCoordinates(
                    FVector2D(StationM, LateralM), Probe) &&
                Probe.bWet)
            {
                OutZCm = Probe.SurfaceHeightMeters * 100.0f;
                OutWorldCm = Probe.WorldPosition;
                return true;
            }
        }
        return false;
    };

    const auto TeleportToWorld =
        [Raft](const FVector& WorldCm, float FacingYaw)
    {
        Raft->TeleportForTesting(
            WorldCm + FVector(0.0f, 0.0f, 12.0f), FacingYaw, true);
        // The player pawn is the world-partition streaming source: named
        // cruxes sit kilometres from the put-in and their cells never load
        // unless the pawn travels too.
        if (UWorld* RaftWorld = Raft->GetWorld())
        {
            if (APlayerController* PlayerController =
                    RaftWorld->GetFirstPlayerController())
            {
                if (APawn* Pawn = PlayerController->GetPawn())
                {
                    Pawn->SetActorLocation(
                        WorldCm + FVector(0.0f, 0.0f, 400.0f),
                        false,
                        nullptr,
                        ETeleportType::TeleportPhysics);
                }
            }
        }
    };

    const auto TeleportToStation =
        [&SampleWetStation, &TeleportToWorld, Raft](float StationM) -> bool
    {
        float ZCm = 0.0f;
        float AheadZCm = 0.0f;
        FVector WorldCm = FVector::ZeroVector;
        FVector AheadWorldCm = FVector::ZeroVector;
        if (!SampleWetStation(StationM, ZCm, WorldCm))
        {
            return false;
        }
        float FacingYaw = Raft->GetActorRotation().Yaw;
        if (SampleWetStation(StationM + 5.0f, AheadZCm, AheadWorldCm))
        {
            const FVector Downstream =
                (AheadWorldCm - WorldCm).GetSafeNormal2D();
            if (!Downstream.IsNearlyZero())
            {
                FacingYaw = FMath::RadiansToDegrees(
                    FMath::Atan2(Downstream.Y, Downstream.X));
            }
        }
        TeleportToWorld(WorldCm, FacingYaw);
        return true;
    };

    if (State->Phase == FRaftSimApproachTelemetryState::EPhase::Start)
    {
        float FirstWetStationM = -1.0f;
        // Always probe from the reach start: the moving window boots around
        // the staged raft, so distant stations are dry until the raft (and
        // with it the window) actually travels there.
        for (float StationM = 0.0f;
             StationM <= 2000.0f;
             StationM += 5.0f)
        {
            float ZCm = 0.0f;
            FVector WorldCm = FVector::ZeroVector;
            if (SampleWetStation(StationM, ZCm, WorldCm))
            {
                FirstWetStationM = StationM;
                break;
            }
        }
        if (FirstWetStationM < 0.0f)
        {
            Test->AddError(
                TEXT("approach-telemetry found no wet centerline station; ")
                TEXT("river field is not live in this run"));
            return true;
        }
        State->CurrentStationM = FirstWetStationM + 10.0f;
        if (!TeleportToStation(State->CurrentStationM))
        {
            Test->AddError(TEXT("approach-telemetry failed initial placement"));
            return true;
        }
        Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
        State->Phase = FRaftSimApproachTelemetryState::EPhase::Transit;
        State->NextHopSeconds = State->ElapsedSeconds + HopEverySeconds;
        Test->AddInfo(FString::Printf(
            TEXT("approach-telemetry transit begins at station %.0f m ")
            TEXT("(support_enabled=%d)"),
            State->CurrentStationM,
            Water->IsRaftSupportSurfaceEnabled() ? 1 : 0));
        return false;
    }

    if (State->ElapsedSeconds > OverallBudgetSeconds)
    {
        Test->AddError(FString::Printf(
            TEXT("approach-telemetry exceeded budget in phase %d ")
            TEXT("(station %.0f m, %d hops)"),
            static_cast<int32>(State->Phase),
            State->CurrentStationM,
            State->HopCount));
        return true;
    }

    if (State->Phase == FRaftSimApproachTelemetryState::EPhase::Transit)
    {
        if (State->ElapsedSeconds < State->NextHopSeconds)
        {
            return false;
        }
        State->NextHopSeconds = State->ElapsedSeconds + HopEverySeconds;

        // Far from a requested crux, hop long (the 320 m window recentres
        // around the raft each hop) and skip drop-hunting entirely: the
        // reach between put-in and a named rapid is full of minor riffles
        // that would end transit kilometres early.
        const bool bSeekingDistantTarget = State->StartStationM > 0.0f &&
            State->CurrentStationM < State->StartStationM;
        if (bSeekingDistantTarget)
        {
            // Long hops can outrun the per-rapid source grids (each covers
            // ~400 m; the streaming handoff follows the RAFT, so a probe past
            // the active grid's edge reads dry until the raft crawls across).
            // Try a long hop, fall back to a short crawl, and only give up
            // after several consecutive fully-dry cycles.
            // Self-pacing: only advance when the moving window's leading
            // edge is confirmed well ahead. The adapter rejects
            // non-overlapping window handoffs, so a raft that outruns the
            // recentre cadence wedges the window permanently; gating each
            // hop on a lookahead probe makes that impossible.
            // Tiered lookahead: a per-rapid source grid ends mid-river, so a
            // long lookahead reads dry near every source boundary no matter
            // how healthy the window is (african_queen [3019,3419] deadlocked
            // the plain 120 m gate at 3370). Far lookahead wet -> full-speed
            // hop; only near lookahead wet -> creep across the boundary; both
            // dry -> hold for the window to catch up.
            float LookaheadZCm = 0.0f;
            FVector LookaheadWorldCm = FVector::ZeroVector;
            const bool bFarClear = SampleWetStation(
                State->CurrentStationM + 120.0f,
                LookaheadZCm,
                LookaheadWorldCm);
            const bool bNearClear = bFarClear || SampleWetStation(
                State->CurrentStationM + 32.0f,
                LookaheadZCm,
                LookaheadWorldCm);
            if (!bNearClear)
            {
                ++State->HopCount;
                ++State->ConsecutiveDryHolds;
                if (State->HopCount > MaxHops)
                {
                    Test->AddError(FString::Printf(
                        TEXT("approach-telemetry window never advanced past ")
                        TEXT("station %.0f m while seeking %.0f m"),
                        State->CurrentStationM,
                        State->StartStationM));
                    return true;
                }
                // Sustained dryness ahead means the hold can never release on
                // its own: at a low-overlap source-grid boundary the active
                // window's leading edge stops short of the next grid, and the
                // window follows the raft, which is exactly what a hold
                // prevents from moving. Since the adapter now reboots the
                // window cold on a non-overlapping handoff instead of
                // wedging, a blind creep along the coordinate map is safe:
                // project the next station geometrically, move the raft, and
                // let streaming bring the water up around it.
                if (State->ConsecutiveDryHolds >= 20)
                {
                    const float BlindStationM =
                        State->CurrentStationM + HopAdvanceM;
                    FVector BlindWorldCm = FVector::ZeroVector;
                    if (Water->RiverToWorldPosition(
                            FVector2D(BlindStationM, 0.0f),
                            Water->GetRiverVerticalDatumM(),
                            BlindWorldCm))
                    {
                        // Only the plan-view projection is trustworthy here
                        // (the surface is dry-unknown — that is why this is a
                        // blind creep). 8 m of river drops millimetres, so
                        // the hull's current height is the best local Z.
                        BlindWorldCm.Z = Raft->GetActorLocation().Z;
                        TeleportToWorld(
                            BlindWorldCm, Raft->GetActorRotation().Yaw);
                        State->CurrentStationM = BlindStationM;
                        State->ConsecutiveDryHolds = 0;
                        Test->AddInfo(FString::Printf(
                            TEXT("approach-telemetry blind creep across dry ")
                            TEXT("window boundary to station %.0f m"),
                            BlindStationM));
                    }
                }
                return false;
            }
            State->ConsecutiveDryHolds = 0;
            const float RemainingM =
                State->StartStationM - State->CurrentStationM;
            float NextStationM = State->CurrentStationM +
                (bFarClear && RemainingM > 200.0f ? 40.0f : HopAdvanceM);
            bool bMoved = TeleportToStation(NextStationM);
            if (!bMoved)
            {
                NextStationM = State->CurrentStationM + HopAdvanceM;
                bMoved = TeleportToStation(NextStationM);
            }
            if (!bMoved)
            {
                ++State->HopCount;
                if (State->HopCount > MaxHops)
                {
                    Test->AddError(FString::Printf(
                        TEXT("approach-telemetry stuck dry at station %.0f m ")
                        TEXT("while seeking station %.0f m"),
                        State->CurrentStationM,
                        State->StartStationM));
                    return true;
                }
                return false;
            }
            State->CurrentStationM = NextStationM;
            ++State->HopCount;
            if (State->HopCount > MaxHops)
            {
                Test->AddError(FString::Printf(
                    TEXT("approach-telemetry exceeded %d hops seeking station ")
                    TEXT("%.0f m (reached %.0f m)"),
                    MaxHops,
                    State->StartStationM,
                    State->CurrentStationM));
                return true;
            }
            if (State->HopCount % 10 == 0)
            {
                Test->AddInfo(FString::Printf(
                    TEXT("approach-telemetry seeking: station %.0f m of %.0f m"),
                    State->CurrentStationM,
                    State->StartStationM));
            }
            return false;
        }

        // Probe downstream of the current station for the first substantial
        // surface drop; the moving window only exposes what is near the raft.
        float HereZCm = 0.0f;
        FVector HereWorldCm = FVector::ZeroVector;
        const bool bHereWet =
            SampleWetStation(State->CurrentStationM, HereZCm, HereWorldCm);
        float MaxDropM = 0.0f;
        float DropStationM = -1.0f;
        if (bHereWet)
        {
            for (float AheadM = 5.0f; AheadM <= RapidLookaheadM; AheadM += 5.0f)
            {
                float AheadZCm = 0.0f;
                FVector AheadWorldCm = FVector::ZeroVector;
                if (!SampleWetStation(
                        State->CurrentStationM + AheadM, AheadZCm, AheadWorldCm))
                {
                    break;
                }
                const float DropM = (HereZCm - AheadZCm) / 100.0f;
                if (DropM > MaxDropM)
                {
                    MaxDropM = DropM;
                    DropStationM = State->CurrentStationM + AheadM;
                }
            }
        }

        if (MaxDropM >= RapidDropThresholdM)
        {
            const float ReleaseStationM = FMath::Max(
                State->CurrentStationM, DropStationM - RideReleaseUpstreamM);
            if (!TeleportToStation(ReleaseStationM))
            {
                Test->AddError(FString::Printf(
                    TEXT("approach-telemetry failed release placement at ")
                    TEXT("station %.0f m"),
                    ReleaseStationM));
                return true;
            }
            State->CurrentStationM = ReleaseStationM;
            State->Phase = FRaftSimApproachTelemetryState::EPhase::Ride;
            State->RideStartElapsedSeconds = State->ElapsedSeconds;
            State->NextSampleSeconds = State->ElapsedSeconds;
            State->RideStartLocationCm = Raft->GetActorLocation();
            State->RideFacingYawDegrees = Raft->GetActorRotation().Yaw;
            Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);

            // Fixed observation camera framed on the DETECTED DROP (not the
            // release point 40 m upstream): the whitewater, ledge, and wave
            // train all live at the drop, and a release-point camera reduces
            // them to distant pixels. Offset to the side so the tongue reads
            // in profile; rendered-frame evidence headless telemetry cannot
            // capture.
            float DropZCm = 0.0f;
            FVector DropWorldCm = State->RideStartLocationCm;
            float ApproachZCm = 0.0f;
            FVector ApproachWorldCm = State->RideStartLocationCm;
            const bool bFramedDrop =
                SampleWetStation(DropStationM + 10.0f, DropZCm, DropWorldCm) &&
                SampleWetStation(
                    DropStationM - 30.0f, ApproachZCm, ApproachWorldCm);
            const FVector Downstream =
                FRotator(0.0f, State->RideFacingYawDegrees, 0.0f).Vector();
            const FVector Side(-Downstream.Y, Downstream.X, 0.0f);
            const FVector CameraLocation = bFramedDrop
                ? ApproachWorldCm + Side * 1400.0f + FVector(0.0f, 0.0f, 650.0f)
                : State->RideStartLocationCm -
                    Downstream * 900.0f + FVector(0.0f, 0.0f, 520.0f);
            const FVector LookTarget = bFramedDrop
                ? DropWorldCm
                : State->RideStartLocationCm + Downstream * 4000.0f;
            const FRotator CameraFacing =
                (LookTarget - CameraLocation).Rotation();
            if (ACameraActor* Camera = World->SpawnActor<ACameraActor>(
                    ACameraActor::StaticClass(), CameraLocation, CameraFacing))
            {
                if (APlayerController* PlayerController =
                        World->GetFirstPlayerController())
                {
                    PlayerController->SetViewTarget(Camera);
                }
            }
            // One-shot render inventory at the rapid: the map is
            // world-partitioned, so this is the only context where the water
            // stack is actually streamed in. Names, materials, visibility,
            // and vertical placement of everything mesh-like near the raft —
            // the link between the (healthy) data and the (blank) screen.
            for (TActorIterator<AActor> ActorIt(World); ActorIt; ++ActorIt)
            {
                AActor* Actor = *ActorIt;
                if (!IsValid(Actor))
                {
                    continue;
                }
                FVector ActorOrigin;
                FVector ActorExtent;
                Actor->GetActorBounds(false, ActorOrigin, ActorExtent);
                const float PlanarDistanceCm = FVector::Dist2D(
                    ActorOrigin, State->RideStartLocationCm);
                if (PlanarDistanceCm - FMath::Max(ActorExtent.X, ActorExtent.Y) >
                    8000.0f)
                {
                    continue;
                }
                TArray<UMeshComponent*> MeshComponents;
                Actor->GetComponents<UMeshComponent>(MeshComponents);
                for (UMeshComponent* MeshComponent : MeshComponents)
                {
                    if (!MeshComponent)
                    {
                        continue;
                    }
                    FString Materials;
                    for (int32 Slot = 0; Slot < MeshComponent->GetNumMaterials();
                         ++Slot)
                    {
                        UMaterialInterface* Material =
                            MeshComponent->GetMaterial(Slot);
                        Materials += Material ? Material->GetName() : TEXT("NONE");
                        Materials += TEXT("|");
                    }
                    const FBoxSphereBounds MeshBounds = MeshComponent->Bounds;
                    Test->AddInfo(FString::Printf(
                        TEXT("rapid-inventory %s/%s :: %s vis=%d z=[%.0f..%.0f] ")
                        TEXT("mats=%s"),
                        *Actor->GetClass()->GetName(),
                        *Actor->GetName(),
                        *MeshComponent->GetName(),
                        MeshComponent->IsVisible() ? 1 : 0,
                        MeshBounds.Origin.Z - MeshBounds.BoxExtent.Z,
                        MeshBounds.Origin.Z + MeshBounds.BoxExtent.Z,
                        *Materials));
                }
            }

            Test->AddInfo(FString::Printf(
                TEXT("approach-telemetry ride begins: station %.0f m, drop ")
                TEXT("%.2f m at station %.0f m, raft=(%.0f, %.0f, %.0f)"),
                ReleaseStationM,
                MaxDropM,
                DropStationM,
                State->RideStartLocationCm.X,
                State->RideStartLocationCm.Y,
                State->RideStartLocationCm.Z));
            return false;
        }

        ++State->HopCount;
        if (State->HopCount > MaxHops)
        {
            Test->AddError(FString::Printf(
                TEXT("approach-telemetry found no %.2f m drop within %d hops ")
                TEXT("(reached station %.0f m)"),
                RapidDropThresholdM,
                MaxHops,
                State->CurrentStationM));
            return true;
        }
        const float NextStationM = State->CurrentStationM + HopAdvanceM;
        if (!TeleportToStation(NextStationM))
        {
            Test->AddInfo(FString::Printf(
                TEXT("approach-telemetry wet centerline ends near station ")
                TEXT("%.0f m without a qualifying drop; ending"),
                NextStationM));
            Test->TestTrue(
                TEXT("approach telemetry reached a rapid before the field ended"),
                false);
            return true;
        }
        State->CurrentStationM = NextStationM;
        if (State->HopCount % 10 == 0)
        {
            Test->AddInfo(FString::Printf(
                TEXT("approach-telemetry transit: station %.0f m after %d hops"),
                State->CurrentStationM,
                State->HopCount));
        }
        return false;
    }

    // Rendered-frame evidence: two shots 0.8 s apart early in the ride (a
    // pixel diff separates moving surface texture from static), one more in
    // the thick of the rapid for foam coverage.
    const float RideElapsed =
        State->ElapsedSeconds - State->RideStartElapsedSeconds;
    const float ShotTimes[3] = {8.0f, 8.8f, 20.0f};
    if (State->ScreenshotsFired < 3 &&
        RideElapsed >= ShotTimes[State->ScreenshotsFired])
    {
        const FString ShotPath = FPaths::Combine(
            FPaths::ProjectSavedDir(),
            TEXT("Screenshots"),
            FString::Printf(
                TEXT("rapid_evidence_%c.png"),
                TEXT('a') + State->ScreenshotsFired));
        FScreenshotRequest::RequestScreenshot(
            ShotPath, /*bShowUI=*/false, /*bAddFilenameSuffix=*/false);
        Test->AddInfo(FString::Printf(
            TEXT("approach-telemetry screenshot %d -> %s"),
            State->ScreenshotsFired,
            *ShotPath));
        ++State->ScreenshotsFired;
    }

    // Ride phase: natural physics, crew forward, telemetry at fixed cadence.
    if (State->ElapsedSeconds >= State->NextSampleSeconds)
    {
        State->NextSampleSeconds += SampleEverySeconds;
        const float RideT =
            State->ElapsedSeconds - State->RideStartElapsedSeconds;

        const FVector RaftCm = Raft->GetActorLocation();
        FRaftSimWaterSample PlainSample;
        FRaftSimWaterSample SupportSample;
        const bool bPlainWet =
            Water->SampleWaterAtWorldPosition(RaftCm, PlainSample) &&
            PlainSample.bWet;
        const bool bSupportWet =
            Water->SampleRaftSupportSurfaceAtWorldPosition(
                RaftCm, SupportSample) &&
            SupportSample.bWet;
        float FloorZCm = 0.0f;
        const bool bHasFloor = Raft->GetRenderedFloorCenterWorldZCm(FloorZCm);

        if (bPlainWet && bSupportWet)
        {
            const float PlainZCm = PlainSample.SurfaceHeightMeters * 100.0f;
            const float SupportZCm = SupportSample.SurfaceHeightMeters * 100.0f;
            const float CenterDraftCm = SupportZCm - RaftCm.Z;
            const float ReliefCm = SupportZCm - PlainZCm;
            const float RenderZCm = SupportZCm +
                ARaftSimWaterSurfaceActor::GetLiveSurfaceRenderLiftCm();
            const float FreeboardCm =
                bHasFloor ? FloorZCm - RenderZCm : TNumericLimits<float>::Max();
            const float TravelCm =
                FVector::Dist2D(RaftCm, State->RideStartLocationCm);
            const float SpeedMps =
                PlainSample.VelocityMetersPerSecond.Size2D();

            ++State->SampleCount;
            State->MinCenterDraftCm =
                FMath::Min(State->MinCenterDraftCm, CenterDraftCm);
            State->MaxCenterDraftCm =
                FMath::Max(State->MaxCenterDraftCm, CenterDraftCm);
            if (bHasFloor)
            {
                State->MinFreeboardCm =
                    FMath::Min(State->MinFreeboardCm, FreeboardCm);
            }
            State->MaxReliefCm = FMath::Max(State->MaxReliefCm, ReliefCm);
            State->MaxTravelCm = FMath::Max(State->MaxTravelCm, TravelCm);

            Test->AddInfo(FString::Printf(
                TEXT("approach-telemetry t=%6.2f travel=%6.1f m water=%4.2f mps ")
                TEXT("raft_z=%7.1f plain_z=%7.1f support_z=%7.1f ")
                TEXT("center_draft=%6.1f relief=%5.1f floor_freeboard=%s cm ")
                TEXT("x=%.0f y=%.0f"),
                RideT,
                TravelCm / 100.0f,
                SpeedMps,
                RaftCm.Z,
                PlainZCm,
                SupportZCm,
                CenterDraftCm,
                ReliefCm,
                bHasFloor
                    ? *FString::Printf(TEXT("%6.1f"), FreeboardCm)
                    : TEXT("   n/a"),
                RaftCm.X,
                RaftCm.Y));
        }
        else
        {
            Test->AddInfo(FString::Printf(
                TEXT("approach-telemetry t=%6.2f dry-or-missing sample ")
                TEXT("(plain_wet=%d support_wet=%d) x=%.0f y=%.0f"),
                RideT,
                bPlainWet ? 1 : 0,
                bSupportWet ? 1 : 0,
                Raft->GetActorLocation().X,
                Raft->GetActorLocation().Y));
        }
    }

    if (State->ElapsedSeconds - State->RideStartElapsedSeconds < RideSeconds)
    {
        return false;
    }

    Test->TestTrue(
        TEXT("approach telemetry collected samples"), State->SampleCount > 0);
    if (State->SampleCount > 0)
    {
        Test->AddInfo(FString::Printf(
            TEXT("approach-telemetry summary: samples=%d travel=%.1f m ")
            TEXT("center_draft=[%.1f, %.1f] cm draft_spread=%.1f cm ")
            TEXT("max_relief=%.1f cm min_floor_freeboard=%.1f cm"),
            State->SampleCount,
            State->MaxTravelCm / 100.0f,
            State->MinCenterDraftCm,
            State->MaxCenterDraftCm,
            State->MaxCenterDraftCm - State->MinCenterDraftCm,
            State->MaxReliefCm,
            State->MinFreeboardCm));
    }
    return true;
}

bool RunApproachTelemetryOnMap(
    FAutomationTestBase& Test,
    const FString& MapPath,
    float StartStationM = -1.0f)
{
    const FString FileName = FPackageName::LongPackageNameToFilename(
        MapPath, FPackageName::GetMapPackageExtension());
    if (!FPaths::FileExists(FileName))
    {
        Test.AddError(
            FString::Printf(TEXT("Map is missing: %s"), *MapPath));
        return false;
    }

    AutomationOpenMap(MapPath);
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.0f));
    TSharedPtr<FRaftSimApproachTelemetryState> State =
        MakeShared<FRaftSimApproachTelemetryState>();
    State->StartStationM = StartStationM;
    ADD_LATENT_AUTOMATION_COMMAND(
        FRaftSimApproachDriftTelemetryCommand(&Test, State));
    return true;
}

} // namespace

bool FRaftSimTroublemakerApproachDraftTelemetryTest::RunTest(const FString&)
{
    return RunApproachTelemetryOnMap(
        *this, TEXT("/Game/RaftSim/Maps/L_Troublemaker"));
}

bool FRaftSimSouthForkApproachDraftTelemetryTest::RunTest(const FString&)
{
    // Troublemaker proper: the named crux at station ~8169 m, where the
    // authored rapid features and the supercritical solve actually live.
    // The put-in reach the earlier rides sampled is a data-calm pool.
    return RunApproachTelemetryOnMap(
        *this,
        TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
        8050.0f);
}

#endif // WITH_AUTOMATION_TESTS
