#include "RaftSimRaftActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimCrewStateContracts.h"
#include "RaftSimFlexibleRaftModel.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimRiverWaterStreamingActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimRiverbedActor.h"
#include "RaftSimWaterVfxActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float kCmPerM = 100.0f;

bool IsFiniteVector(const FVector& Value)
{
    return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
}
}

ARaftSimRaftActor::ARaftSimRaftActor()
{
    PrimaryActorTick.bCanEverTick = true;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    // Collision/buoyancy footprint box — kept for the raft-body physics but
    // hidden; the visible raft is the procedural inflatable mesh below.
    HullMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HullMesh"));
    HullMesh->SetupAttachment(Root);
    HullMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (CubeMesh.Succeeded())
    {
        HullMesh->SetStaticMesh(CubeMesh.Object);
        // 14 ft paddle raft footprint: 4.3 m x 2.0 m x 0.56 m (engine cube is 1 m).
        HullMesh->SetRelativeScale3D(FVector(FootprintLengthM, FootprintWidthM, 0.56f));
        HullMesh->SetRelativeLocation(FVector(0.0f, 0.0f, 0.0f));
    }
    HullMesh->SetVisibility(false);

    // Photoreal inflatable-raft visual: swept tube loop + thwarts + floor. The
    // geometry is built in BeginPlay (BuildRaftVisual) to avoid work on the CDO.
    RaftVisual = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("RaftVisual"));
    RaftVisual->SetupAttachment(Root);
    RaftVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // Tube bottoms build at z=0; drop so the raft floats with the lower tube in
    // the water and the deck just above the surface.
    RaftVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -TubeRadiusM * 0.55f * kCmPerM));

    RescueLineVisual = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("RescueLineVisual"));
    RescueLineVisual->SetupAttachment(Root);
    RescueLineVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RescueLineVisual->SetVisibility(false);

    SternSeatAttachPoint = CreateDefaultSubobject<USceneComponent>(TEXT("SternSeatAttachPoint"));
    SternSeatAttachPoint->SetupAttachment(Root);
    // Guide sits on the stern tube, slightly above the deck.
    SternSeatAttachPoint->SetRelativeLocation(FVector(-165.0f, 0.0f, 55.0f));
}

void ARaftSimRaftActor::BeginPlay()
{
    Super::BeginPlay();

    // A-3 authoritative path: configure the bridge subsystem from this
    // actor's properties, then mirror the adapter's kinematic state.
    Bridge = nullptr;
    RaftAdapter = nullptr;
    const UGameInstance* GameInstance = GetGameInstance();
    if (GameInstance == nullptr)
    {
        return;
    }
    URaftSimPhysicsBridgeSubsystem* BridgeSubsystem =
        GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    if (BridgeSubsystem == nullptr)
    {
        return;
    }

    // Dev water config: the report gate governs river-water approval claims,
    // not the genuine-solver window, so the gate requirement is disabled.
    FRaftSimWaterRuntimeConfig WaterConfig;
    WaterConfig.bRequireAcceptedReportManifest = false;

    FRaftSimRaftBodyConfig BodyConfig;
    BodyConfig.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    BodyConfig.MassKg = MassKg;
    BodyConfig.TubeRadiusMeters = TubeRadiusM;
    BodyConfig.LengthMeters = FootprintLengthM;
    BodyConfig.WidthMeters = FootprintWidthM;
    // Yaw inertia of a flat raft: (1/12) m (L^2 + W^2); roll/pitch stiffer
    // response at 0.45x, matching the P1 integrator.
    const float YawInertia =
        MassKg * (FootprintLengthM * FootprintLengthM + FootprintWidthM * FootprintWidthM) / 12.0f;
    BodyConfig.InertiaTensorKgM2 =
        FVector(0.45f * YawInertia, 0.45f * YawInertia, YawInertia);
    BodyConfig.BuoyancyWeightMultiple = BuoyancyWeightMultiple;
    BodyConfig.LinearDragCoefficient = LinearDragCoefficient;
    BodyConfig.HeaveDampingNsPerM = HeaveDampingNsPerM;
    BodyConfig.AngularDampingPerSecond = AngularDampingPerSecond;

    FRaftSimWaterRaftCouplingPolicy CouplingPolicy;
    BridgeSubsystem->ConfigureBridge(
        WaterConfig, BodyConfig, CouplingPolicy,
        /*InWaterStepSeconds=*/1.0f / 60.0f,
        /*InChronoSubstepSeconds=*/FixedSubstepSeconds);

    // Live solver water: flat-tank FV window (surface Z=0, 3 m deep, 2 m
    // cells, 160x160 m) until the river window replaces it in the corridor
    // slice. Without the solver lib the bridge probe falls back to the same
    // flat Z=0 waterline.
    ARaftSimRiverWaterConfig* RiverConfig = nullptr;
    if (URaftSimWaterRuntimeAdapter* WaterAdapter = BridgeSubsystem->GetWaterRuntime())
    {
        // River map: load a cooked steady-state flow window if the level places
        // a config actor. Otherwise the dev flat tank.
        if (TActorIterator<ARaftSimRiverWaterConfig> It(GetWorld()); It)
        {
            RiverConfig = *It;
        }
        bool bRiverConfigured = false;
        if (RiverConfig != nullptr)
        {
            const bool bCoordinateMapReady = RiverConfig->CoordinateMapPath.IsEmpty() ||
                WaterAdapter->ConfigureRiverCoordinateMap(RiverConfig->CoordinateMapPath);
            if (bCoordinateMapReady && RiverConfig->bEnableMovingWindowStreaming)
            {
                bRiverConfigured = WaterAdapter->ConfigureMovingRiverWindow(
                    RiverConfig->CookedFieldsDir, RiverConfig->FlowBand.ToString(),
                    RiverConfig->WindowCenterM,
                    FVector2D(
                        RiverConfig->MovingWindowStationExtentM,
                        RiverConfig->MovingWindowLateralExtentM),
                    /*RoughnessManning=*/0.041f);
            }
            else if (bCoordinateMapReady)
            {
                bRiverConfigured = WaterAdapter->ConfigureRiverWindow(
                    RiverConfig->CookedFieldsDir, RiverConfig->FlowBand.ToString(),
                    RiverConfig->WindowCenterM,
                    FVector2D(RiverConfig->WindowExtentM, RiverConfig->WindowExtentM),
                    /*RoughnessManning=*/0.041f);
            }
        }
        if (!bRiverConfigured)
        {
            WaterAdapter->ConfigureDevTankWindow(
                FVector2D(-80.0, -80.0), 160.0f, 160.0f, 2.0f,
                /*SurfaceHeightM=*/0.0f, /*DepthM=*/3.0f);
        }
    }

    // Water-rendering v1: spawn a surface actor that displays the live solver
    // field. Skipped if one is already present (e.g. placed in a river map).
    if (UWorld* World = GetWorld())
    {
        bool bHasSurface = false;
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
        {
            bHasSurface = true;
        }
        if (!bHasSurface)
        {
            World->SpawnActor<ARaftSimWaterSurfaceActor>(
                ARaftSimWaterSurfaceActor::StaticClass(), FTransform::Identity);
        }

        bool bHasWaterVfx = false;
        if (TActorIterator<ARaftSimWaterVfxActor> It(World); It)
        {
            bHasWaterVfx = true;
        }
        if (!bHasWaterVfx)
        {
            World->SpawnActor<ARaftSimWaterVfxActor>(
                ARaftSimWaterVfxActor::StaticClass(), FTransform::Identity);
        }

        if (RiverConfig && RiverConfig->bEnableMovingWindowStreaming)
        {
            bool bHasStreamer = false;
            if (TActorIterator<ARaftSimRiverWaterStreamingActor> It(World); It)
            {
                bHasStreamer = true;
            }
            if (!bHasStreamer)
            {
                World->SpawnActor<ARaftSimRiverWaterStreamingActor>(
                    ARaftSimRiverWaterStreamingActor::StaticClass(), FTransform::Identity);
            }
        }

        // Photoreal terrain: spawn a riverbed actor that renders the cooked
        // window's DEM bed and banks. Skipped if one is already placed.
        bool bHasBed = RiverConfig && RiverConfig->bMapProvidesTerrain;
        if (TActorIterator<ARaftSimRiverbedActor> It(World); It)
        {
            bHasBed = true;
        }
        if (!bHasBed)
        {
            World->SpawnActor<ARaftSimRiverbedActor>(
                ARaftSimRiverbedActor::StaticClass(), FTransform::Identity);
        }
    }

    URaftSimChronoRuntimeAdapter* Adapter = BridgeSubsystem->GetRaftRuntime();
    if (Adapter == nullptr)
    {
        return;
    }

    // D1-D4 flexible-raft stack with the actual production crew load bound to
    // seats. Commands now move the same masses that the avatars depict.
    FRaftSimFlexParameters FlexParameters;
    FlexParameters.MassKg = MassKg;
    FlexParameters.LengthM = FootprintLengthM;
    FlexParameters.WidthM = FootprintWidthM;
    FlexParameters.TubeRadiusM = TubeRadiusM;
    FlexParameters.GuideMassKg = 85.0;
    FlexParameters.PassengerMassKg = 75.0;
    FlexParameters.PassengerCount = PaddlerCount;
    Adapter->ConfigureFlexibleRaftModel(
        FlexParameters, RaftSimFlex::BuildDefaultCrewSeats(FlexParameters));

    // Seed the adapter's kinematic state from the spawn transform.
    FRaftSimRaftKinematicState InitialState;
    InitialState.WorldTransform.SetTranslation(GetActorLocation());
    InitialState.WorldTransform.SetRotation(GetActorQuat());
    Adapter->SetKinematicState(InitialState);

    Bridge = BridgeSubsystem;
    RaftAdapter = Adapter;

    // Checkpoint = spawn pose; recovery/reset returns the raft here.
    CheckpointTransform = GetActorTransform();
    RaftMode = ERaftSimRaftMode::Upright;
    FlipRiskLatchSeconds = 0.0f;

    BuildRaftVisual();
    SpawnCrewVisuals();
}

int32 ARaftSimRaftActor::GetActiveWaterContactCount() const
{
    return RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry().ContactCount
        : 0;
}

float ARaftSimRaftActor::GetMaximumWaterContactIndentationM() const
{
    return RaftAdapter
        ? static_cast<float>(RaftAdapter->GetLastFlexibleStepTelemetry().MaxIndentationM)
        : 0.0f;
}

void ARaftSimRaftActor::BuildRaftVisual()
{
    if (RaftVisual == nullptr)
    {
        return;
    }
    RaftSimRaftMesh::FMeshData Tubes, Floor;
    RaftSimRaftMesh::BuildInflatableRaft(
        FootprintLengthM, FootprintWidthM, TubeRadiusM, Tubes, Floor, {},
        RaftSimRaftMesh::FRaftSimRaftVisualCondition{
            RaftCondition.PressureFraction,
            RaftCondition.FabricIntegrity,
            RaftCondition.PermanentCreaseAmplitudeM});
    const TArray<FLinearColor> NoColors;
    RaftVisual->CreateMeshSection_LinearColor(
        0, Tubes.Vertices, Tubes.Triangles, Tubes.Normals, Tubes.UVs, NoColors,
        Tubes.Tangents, /*bCreateCollision=*/false);
    RaftVisual->CreateMeshSection_LinearColor(
        1, Floor.Vertices, Floor.Triangles, Floor.Normals, Floor.UVs, NoColors,
        Floor.Tangents, /*bCreateCollision=*/false);
    if (UMaterialInterface* TubeMat = LoadObject<UMaterialInterface>(
            nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftTube.M_RaftSim_RaftTube")))
    {
        RaftVisual->SetMaterial(0, TubeMat);
    }
    if (UMaterialInterface* FloorMat = LoadObject<UMaterialInterface>(
            nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftFloor.M_RaftSim_RaftFloor")))
    {
        RaftVisual->SetMaterial(1, FloorMat);
    }
}

void ARaftSimRaftActor::UpdateFlexibleRaftVisual()
{
    if (RaftVisual == nullptr || RaftAdapter == nullptr)
    {
        return;
    }

    RaftSimRaftMesh::FMeshData Tubes, Floor;
    RaftSimRaftMesh::BuildInflatableRaft(
        FootprintLengthM,
        FootprintWidthM,
        TubeRadiusM,
        Tubes,
        Floor,
        RaftAdapter->GetFlexibleVisualSegments(),
        RaftSimRaftMesh::FRaftSimRaftVisualCondition{
            RaftCondition.PressureFraction,
            RaftCondition.FabricIntegrity,
            RaftCondition.PermanentCreaseAmplitudeM});
    const TArray<FLinearColor> NoColors;
    RaftVisual->UpdateMeshSection_LinearColor(
        0, Tubes.Vertices, Tubes.Normals, Tubes.UVs, NoColors, Tubes.Tangents);
    RaftVisual->UpdateMeshSection_LinearColor(
        1, Floor.Vertices, Floor.Normals, Floor.UVs, NoColors, Floor.Tangents);
}

void ARaftSimRaftActor::UpdateRockObstacles()
{
    if (RaftAdapter == nullptr || GetWorld() == nullptr)
    {
        return;
    }

    TArray<FRaftSimFlexRockObstacle> Obstacles;
    for (TActorIterator<ARaftSimRockObstacleActor> It(GetWorld()); It; ++It)
    {
        const ARaftSimRockObstacleActor* Rock = *It;
        if (Rock == nullptr)
        {
            continue;
        }
        // Broad-phase bound: D4 cannot contact a rock farther away than the
        // raft diagonal plus its radius. Keeping only local actors avoids a
        // full river's rock catalog entering every 120 Hz solve.
        const float ContactRangeCm =
            (0.6f * FMath::Sqrt(FootprintLengthM * FootprintLengthM +
                                FootprintWidthM * FootprintWidthM) +
             Rock->GetContactRadiusM()) * kCmPerM;
        if (FVector::DistSquared2D(GetActorLocation(), Rock->GetActorLocation()) >
            FMath::Square(ContactRangeCm))
        {
            continue;
        }

        FRaftSimFlexRockObstacle Obstacle;
        Obstacle.ObstacleId = Rock->GetName();
        Obstacle.LocalPosition =
            GetActorTransform().InverseTransformPosition(Rock->GetActorLocation()) / kCmPerM;
        Obstacle.RadiusM = Rock->GetContactRadiusM();
        Obstacle.FrictionCoefficient = Rock->GetContactFriction();
        Obstacles.Add(MoveTemp(Obstacle));
    }
    RaftAdapter->SetFlexibleRockObstacles(Obstacles);
}

void ARaftSimRaftActor::SpawnCrewVisuals()
{
    if (!GetWorld())
    {
        return;
    }
    for (ARaftSimCrewAvatarActor* Avatar : CrewAvatars)
    {
        if (Avatar)
        {
            Avatar->Destroy();
        }
    }
    CrewAvatars.Reset();
    for (int32 Index = 0; Index < PaddlerCount; ++Index)
    {
        FActorSpawnParameters Params;
        Params.Owner = this;
        ARaftSimCrewAvatarActor* Avatar = GetWorld()->SpawnActor<ARaftSimCrewAvatarActor>(
            ARaftSimCrewAvatarActor::StaticClass(), GetActorTransform(), Params);
        if (!Avatar)
        {
            continue;
        }
        const int32 Side = (Index % 2 == 0) ? -1 : 1;
        Avatar->ConfigureAppearance(Index, Side, false);
        CrewAvatars.Add(Avatar);
        AttachAvatarToSeat(Avatar, FName(*FString::Printf(TEXT("paddler_%d"), Index + 1)));
    }
    FActorSpawnParameters GuideParams;
    GuideParams.Owner = this;
    if (ARaftSimCrewAvatarActor* Guide = GetWorld()->SpawnActor<ARaftSimCrewAvatarActor>(
            ARaftSimCrewAvatarActor::StaticClass(), GetActorTransform(), GuideParams))
    {
        Guide->ConfigureAppearance(0, 1, true);
        CrewAvatars.Add(Guide);
        AttachAvatarToSeat(Guide, TEXT("guide"));
    }
}

ARaftSimCrewAvatarActor* ARaftSimRaftActor::FindAvatar(FName PassengerId) const
{
    if (PassengerId == TEXT("guide"))
    {
        return CrewAvatars.IsEmpty() ? nullptr : CrewAvatars.Last();
    }
    FString Id = PassengerId.ToString();
    if (!Id.RemoveFromStart(TEXT("paddler_")))
    {
        return nullptr;
    }
    const int32 Index = FCString::Atoi(*Id) - 1;
    return CrewAvatars.IsValidIndex(Index) ? CrewAvatars[Index] : nullptr;
}

void ARaftSimRaftActor::AttachAvatarToSeat(
    ARaftSimCrewAvatarActor* Avatar,
    FName PassengerId)
{
    if (!Avatar)
    {
        return;
    }
    FVector SeatCm(-175.0f, 0.0f, 38.0f);
    if (PassengerId != TEXT("guide"))
    {
        FString Id = PassengerId.ToString();
        Id.RemoveFromStart(TEXT("paddler_"));
        const int32 Index = FMath::Max(FCString::Atoi(*Id) - 1, 0);
        const float Side = (Index % 2 == 0) ? -1.0f : 1.0f;
        const float BowM = 1.15f - (Index / 2) * 1.05f;
        SeatCm = FVector(BowM * kCmPerM, Side * 62.0f, 30.0f);
    }
    Avatar->AttachToComponent(Root, FAttachmentTransformRules::KeepWorldTransform);
    Avatar->SetActorRelativeLocation(SeatCm);
    Avatar->SetActorRelativeRotation(FRotator::ZeroRotator);
    Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
}

void ARaftSimRaftActor::IssueCrewCommand(ERaftSimCrewCommand Command)
{
    if (Command != ActiveCrewCommand)
    {
        PendingCrewCommand = Command;
        CrewReactionRemaining = CrewReactionSeconds;
    }
}

void ARaftSimRaftActor::UpdateCrew(float DeltaSeconds)
{
    if (RaftAdapter == nullptr || RaftMode != ERaftSimRaftMode::Upright)
    {
        return;
    }

    // Crew react to a new command after a short latency.
    if (CrewReactionRemaining > 0.0f)
    {
        CrewReactionRemaining -= DeltaSeconds;
        if (CrewReactionRemaining <= 0.0f)
        {
            ActiveCrewCommand = PendingCrewCommand;
        }
    }

    // High-side / get-down couple to the D2 flexible crew actions (weight shift).
    TArray<FRaftSimFlexCrewAction> Actions;
    if (ActiveCrewCommand == ERaftSimCrewCommand::HighSide)
    {
        FRaftSimFlexCrewAction Action;
        Action.SeatId = TEXT("guide");
        Action.HighSideDirection = (GetActorRotation().Roll >= 0.0f) ? -1 : 1;
        Action.bBrace = true;
        Actions.Add(Action);
    }
    else if (ActiveCrewCommand == ERaftSimCrewCommand::GetDown)
    {
        FRaftSimFlexCrewAction Action;
        Action.SeatId = TEXT("guide");
        Action.LeanOffset = FVector(0.0f, 0.0f, -0.15f);
        Actions.Add(Action);
    }
    RaftAdapter->SetFlexibleCrewActions(Actions);

    ERaftSimCrewAvatarAction AvatarAction = ERaftSimCrewAvatarAction::SeatedIdle;
    switch (ActiveCrewCommand)
    {
        case ERaftSimCrewCommand::AllForward:
            AvatarAction = ERaftSimCrewAvatarAction::ForwardStroke;
            break;
        case ERaftSimCrewCommand::AllBackward:
            AvatarAction = ERaftSimCrewAvatarAction::BackStroke;
            break;
        case ERaftSimCrewCommand::TurnLeft:
            AvatarAction = ERaftSimCrewAvatarAction::TurnLeft;
            break;
        case ERaftSimCrewCommand::TurnRight:
            AvatarAction = ERaftSimCrewAvatarAction::TurnRight;
            break;
        case ERaftSimCrewCommand::Stop:
        case ERaftSimCrewCommand::GetDown:
            AvatarAction = ERaftSimCrewAvatarAction::Brace;
            break;
        case ERaftSimCrewCommand::HighSide:
            AvatarAction = GetActorRotation().Roll >= 0.0f
                ? ERaftSimCrewAvatarAction::HighSidePort
                : ERaftSimCrewAvatarAction::HighSideStarboard;
            break;
        case ERaftSimCrewCommand::Rest:
        default:
            break;
    }
    for (ARaftSimCrewAvatarActor* Avatar : CrewAvatars)
    {
        if (Avatar && Avatar->GetAttachParentActor() == this)
        {
            Avatar->SetAvatarAction(AvatarAction);
        }
    }

    // Paddle strokes on cadence for propulsion/turn commands.
    CrewStrokeTimer -= DeltaSeconds;
    if (CrewStrokeTimer > 0.0f)
    {
        return;
    }
    CrewStrokeTimer = CrewStrokeIntervalSeconds;

    const float PerPaddler = PaddleStrokeImpulseNs * 0.5f;
    const float Crew = static_cast<float>(FMath::Max(1, PaddlerCount));
    const FVector Forward = GetActorForwardVector();
    switch (ActiveCrewCommand)
    {
        case ERaftSimCrewCommand::AllForward:
            RaftAdapter->AddExternalImpulse(Forward * PerPaddler * Crew, FVector::ZeroVector);
            break;
        case ERaftSimCrewCommand::AllBackward:
            RaftAdapter->AddExternalImpulse(-Forward * PerPaddler * Crew, FVector::ZeroVector);
            break;
        case ERaftSimCrewCommand::TurnLeft:
            RaftAdapter->AddExternalImpulse(
                FVector::ZeroVector, FVector(0.0f, 0.0f, -PerPaddler * Crew * 1.1f));
            break;
        case ERaftSimCrewCommand::TurnRight:
            RaftAdapter->AddExternalImpulse(
                FVector::ZeroVector, FVector(0.0f, 0.0f, PerPaddler * Crew * 1.1f));
            break;
        case ERaftSimCrewCommand::Stop:
        {
            // Brace/back-paddle to shed speed.
            const FVector Vel = RaftAdapter->GetKinematicState().LinearVelocityMetersPerSecond;
            RaftAdapter->AddExternalImpulse(-Vel.GetSafeNormal() * PerPaddler * Crew, FVector::ZeroVector);
            break;
        }
        default:
            break;
    }
}

FVector ARaftSimRaftActor::GetRaftVelocity() const
{
    return RaftAdapter != nullptr
        ? RaftAdapter->GetKinematicState().LinearVelocityMetersPerSecond
        : FVector::ZeroVector;
}

void ARaftSimRaftActor::ApplyPaddleStroke(ERaftSimPaddleSide Side, float ForwardScale)
{
    if (RaftAdapter == nullptr)
    {
        return;
    }
    const float Scale = FMath::Clamp(ForwardScale, -1.0f, 1.0f);
    const FVector LinearImpulseNs = GetActorForwardVector() * (PaddleStrokeImpulseNs * Scale);

    // Off-center strokes also yaw the raft a little.
    FVector AngularImpulseNms = FVector::ZeroVector;
    if (Side != ERaftSimPaddleSide::Both)
    {
        const float LeverArmM = 0.9f;
        const float SideSign = (Side == ERaftSimPaddleSide::Port) ? -1.0f : 1.0f;
        AngularImpulseNms.Z = -SideSign * Scale * PaddleStrokeImpulseNs * LeverArmM * 0.35f;
    }
    RaftAdapter->AddExternalImpulse(LinearImpulseNs, AngularImpulseNms);
    ++PaddleStrokeCount;
}

void ARaftSimRaftActor::ApplyTurnStroke(float TurnScale)
{
    if (RaftAdapter == nullptr)
    {
        return;
    }
    const float Scale = FMath::Clamp(TurnScale, -1.0f, 1.0f);
    RaftAdapter->AddExternalImpulse(
        FVector::ZeroVector, FVector(0.0f, 0.0f, Scale * PaddleStrokeImpulseNs * 1.15f));
}

void ARaftSimRaftActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (Bridge == nullptr || RaftAdapter == nullptr)
    {
        return;
    }

    RockObstacleRefreshRemaining -= DeltaSeconds;
    if (RockObstacleRefreshRemaining <= 0.0f)
    {
        UpdateRockObstacles();
        RockObstacleRefreshRemaining = 0.05f;
    }

    FRaftSimPhysicsTickInput Input;
    Input.FrameDeltaSeconds = FMath::Min(DeltaSeconds, 0.25f);
    const FRaftSimPhysicsTickOutput Output = Bridge->TickBridge(Input);
    if (Output.CommittedPhysicsFrame > 0)
    {
        FVector Location = Output.RaftState.WorldTransform.GetTranslation();
        // Stability guard: a raft cannot leave the world. If the solver state
        // diverges (e.g. extreme forced overwash), clamp to a sane envelope and
        // shed the runaway velocity so rendering and gameplay stay valid.
        const float kMaxHorizM = 50000.0f * 100.0f; // 50 km
        const float kMaxDepthCm = 500.0f * 100.0f;  // 500 m
        if (Location.ContainsNaN() ||
            FMath::Abs(Location.X) > kMaxHorizM || FMath::Abs(Location.Y) > kMaxHorizM ||
            FMath::Abs(Location.Z) > kMaxDepthCm)
        {
            Location.X = FMath::Clamp(Location.ContainsNaN() ? 0.0f : Location.X, -kMaxHorizM, kMaxHorizM);
            Location.Y = FMath::Clamp(Location.ContainsNaN() ? 0.0f : Location.Y, -kMaxHorizM, kMaxHorizM);
            Location.Z = FMath::Clamp(Location.ContainsNaN() ? 0.0f : Location.Z, -kMaxDepthCm, kMaxDepthCm);
            FRaftSimRaftKinematicState Clamped = RaftAdapter->GetKinematicState();
            Clamped.WorldTransform.SetTranslation(Location);
            Clamped.LinearVelocityMetersPerSecond = FVector::ZeroVector;
            RaftAdapter->SetKinematicState(Clamped);
        }
        FQuat Rotation = Output.RaftState.WorldTransform.GetRotation().GetNormalized();
        if (Rotation.ContainsNaN() || !FMath::IsFinite(Rotation.SizeSquared()) ||
            Rotation.SizeSquared() < 1.0e-8)
        {
            Rotation = GetActorQuat();
            if (Rotation.ContainsNaN() || !FMath::IsFinite(Rotation.SizeSquared()) ||
                Rotation.SizeSquared() < 1.0e-8)
            {
                Rotation = FQuat::Identity;
            }
            FRaftSimRaftKinematicState Clamped = RaftAdapter->GetKinematicState();
            Clamped.WorldTransform.SetRotation(Rotation);
            Clamped.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
            RaftAdapter->SetKinematicState(Clamped);
        }
        SetActorLocationAndRotation(Location, Rotation);
    }

    UpdateCapsizeLoop(FMath::Min(DeltaSeconds, 0.25f));
    UpdateCrew(FMath::Min(DeltaSeconds, 0.25f));
    UpdateRescueInteraction(FMath::Min(DeltaSeconds, 0.25f));
    UpdateRaftCondition(FMath::Min(DeltaSeconds, 0.25f));
    UpdateRescueLineVisual();
    UpdateFlexibleRaftVisual();
}

void ARaftSimRaftActor::UpdateCapsizeLoop(float DeltaSeconds)
{
    const FRaftSimFlexStepTelemetry& Telemetry = RaftAdapter->GetLastFlexibleStepTelemetry();
    const float RollDegrees = FMath::Abs(GetActorRotation().Roll);

    if (RaftMode == ERaftSimRaftMode::Upright)
    {
        // Latch on a sustained negative flip margin (overwash roll moment beats
        // the tube's righting moment) or a hard roll-over.
        const bool bFlipRisk = Telemetry.bReferenceFlipRisk && Telemetry.ReferenceFlipMarginNm < 0.0;
        FlipRiskLatchSeconds = bFlipRisk
            ? FlipRiskLatchSeconds + DeltaSeconds
            : FMath::Max(0.0f, FlipRiskLatchSeconds - DeltaSeconds);

        if (FlipRiskLatchSeconds >= CapsizeLatchSeconds || RollDegrees >= CapsizeRollDegrees)
        {
            EnterCapsize();
        }
        if (Swimmers.IsEmpty())
        {
            return;
        }
    }

    // Capsized or Recovering: swimmers drift and can be reseated.
    DriftSwimmers(DeltaSeconds);

    if (RaftMode == ERaftSimRaftMode::Recovering)
    {
        TryReseatSwimmers();
        if (Swimmers.Num() == 0)
        {
            RaftMode = ERaftSimRaftMode::Upright;
            FlipRiskLatchSeconds = 0.0f;
        }
    }
}

void ARaftSimRaftActor::EnterCapsize()
{
    RaftMode = ERaftSimRaftMode::Capsized;
    FlipRiskLatchSeconds = 0.0f;
    // Right the boat here on re-flip. Guard against a diverged sink so the
    // recovery point stays near where the crew went overboard.
    CapsizeLocation = GetActorLocation();
    CapsizeLocation.Z = FMath::Clamp(CapsizeLocation.Z, -200.0f, 200.0f);

    // Roll the hull over so the flip is visible, and drain nothing yet — the
    // retained water keeps it inverted until the guide re-flips.
    AddActorLocalRotation(FRotator(0.0f, 0.0f, 160.0f));

    SpawnSwimmers(CrewSize, true);
}

void ARaftSimRaftActor::SpawnSwimmers(int32 Count, bool bIncludeGuide)
{
    Swimmers.Reset();
    RescueInteraction = FRaftSimRescueInteractionState{};
    SelectedSwimmerIndex = INDEX_NONE;
    const int32 Available = FMath::Clamp(Count, 0, PaddlerCount + (bIncludeGuide ? 1 : 0));
    const FVector RaftWorldCm = IsFiniteVector(GetActorLocation())
        ? GetActorLocation()
        : CheckpointTransform.GetLocation();
    const FVector RaftM = RaftWorldCm / kCmPerM;
    const FVector FlowMps = SampleWaterVelocityMps(RaftWorldCm);
    for (int32 Index = 0; Index < Available; ++Index)
    {
        FRaftSimSwimmerRescueFrame Swimmer;
        Swimmer.PassengerId = bIncludeGuide && Index == 0
            ? FName(TEXT("guide"))
            : FName(*FString::Printf(TEXT("paddler_%d"), Index + (bIncludeGuide ? 0 : 1)));
        const float Angle = (2.0f * PI * Index) / FMath::Max(1, Available);
        Swimmer.SwimmerWorldPositionMeters =
            RaftM + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * 1.5f;
        Swimmer.SwimmerDriftVelocityMetersPerSecond = FlowMps;
        Swimmer.RescueWindowSeconds = 22.0f;
        Swimmer.bThrowLineAvailable = true;
        Swimmers.Add(Swimmer);

        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId))
        {
            Avatar->DetachFromActor(FDetachmentTransformRules::KeepRelativeTransform);
            Avatar->SetActorTransform(FTransform(
                FQuat::Identity,
                Swimmer.SwimmerWorldPositionMeters * kCmPerM,
                FVector::OneVector));
            Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
        }
    }
    if (!Swimmers.IsEmpty())
    {
        SelectedSwimmerIndex = 0;
        RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Aiming;
        RescueInteraction.TargetPassengerId = Swimmers[0].PassengerId;
        RescueInteraction.DistanceMeters = FVector::Distance(
            Swimmers[0].SwimmerWorldPositionMeters,
            GetActorLocation() / kCmPerM);
        RescueInteraction.FeedbackCode = TEXT("rescue_target_selected");
    }
}

void ARaftSimRaftActor::DriftSwimmers(float DeltaSeconds)
{
    for (int32 Index = 0; Index < Swimmers.Num(); ++Index)
    {
        const FVector SwimmerCm = Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM;
        const FVector FlowMps = SampleWaterVelocityMps(SwimmerCm);
        Swimmers[Index] = URaftSimSwimmerRescueLibrary::IntegrateSwimmerDrift(
            Swimmers[Index], FlowMps, DeltaSeconds);
        if (!IsFiniteVector(Swimmers[Index].SwimmerWorldPositionMeters))
        {
            Swimmers[Index].SwimmerWorldPositionMeters =
                (IsFiniteVector(GetActorLocation())
                    ? GetActorLocation()
                    : CheckpointTransform.GetLocation()) / kCmPerM;
            Swimmers[Index].SwimmerDriftVelocityMetersPerSecond = FVector::ZeroVector;
        }
        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmers[Index].PassengerId))
        {
            Avatar->SetActorLocation(Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM);
            Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
        }
        if (Swimmers[Index].TimeInWaterSeconds > Swimmers[Index].RescueWindowSeconds &&
            Swimmers[Index].FailedRescueReason.IsNone())
        {
            Swimmers[Index].FailedRescueReason = TEXT("rescue_window_expired");
            RescueFailureResetRemaining = 4.0f;
        }
    }
    if (RescueFailureResetRemaining >= 0.0f)
    {
        RescueFailureResetRemaining -= DeltaSeconds;
        if (RescueFailureResetRemaining <= 0.0f)
        {
            ResetToCheckpoint();
        }
    }
}

void ARaftSimRaftActor::TryReseatSwimmers()
{
    const FVector RaftM = GetActorLocation() / kCmPerM;
    FRaftSimSwimmingSkillProfile Skill;
    for (int32 Index = Swimmers.Num() - 1; Index >= 0; --Index)
    {
        const float DistanceM =
            FVector::Dist(Swimmers[Index].SwimmerWorldPositionMeters, RaftM);
        FRaftSimRescueAttempt Attempt;
        // Reach-grab a swimmer at the tube; throw a line to one further out.
        Attempt.Method = (DistanceM <= 1.2f)
            ? ERaftSimRescueMethod::ReachGrab
            : ERaftSimRescueMethod::ThrowLine;
        Attempt.bThrowLineAvailable = Swimmers[Index].bThrowLineAvailable;
        Attempt.DistanceMeters = DistanceM;
        Attempt.TimeInWaterSeconds = Swimmers[Index].TimeInWaterSeconds;

        const FRaftSimSwimmerRescueFrame Result =
            URaftSimSwimmerRescueLibrary::EvaluateRescueAttempt(
                Swimmers[Index], Attempt, Skill);
        Swimmers[Index] = Result;

        // Reseated once the guide finishes pulling the swimmer in.
        if (Result.PullInProgress >= 1.0f)
        {
            RemoveSwimmerAt(Index);
        }
    }
}

int32 ARaftSimRaftActor::FindSwimmerIndex(FName PassengerId) const
{
    return Swimmers.IndexOfByPredicate(
        [PassengerId](const FRaftSimSwimmerRescueFrame& Swimmer)
        { return Swimmer.PassengerId == PassengerId; });
}

bool ARaftSimRaftActor::GetSwimmerWorldPosition(
    FName PassengerId,
    FVector& OutWorldPositionCm) const
{
    const int32 Index = FindSwimmerIndex(PassengerId);
    if (!Swimmers.IsValidIndex(Index))
    {
        return false;
    }
    OutWorldPositionCm = Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM;
    return true;
}

bool ARaftSimRaftActor::IsPassengerSwimming(FName PassengerId) const
{
    return FindSwimmerIndex(PassengerId) != INDEX_NONE;
}

void ARaftSimRaftActor::SelectRescueTarget(float Direction)
{
    if (Swimmers.IsEmpty())
    {
        SelectedSwimmerIndex = INDEX_NONE;
        RescueInteraction = FRaftSimRescueInteractionState{};
        return;
    }
    const int32 Step = Direction < 0.0f ? -1 : 1;
    SelectedSwimmerIndex = SelectedSwimmerIndex == INDEX_NONE
        ? 0
        : (SelectedSwimmerIndex + Step + Swimmers.Num()) % Swimmers.Num();
    RescueInteraction = FRaftSimRescueInteractionState{};
    RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Aiming;
    RescueInteraction.TargetPassengerId = Swimmers[SelectedSwimmerIndex].PassengerId;
    RescueInteraction.LineEndWorldMeters =
        Swimmers[SelectedSwimmerIndex].SwimmerWorldPositionMeters;
    RescueInteraction.DistanceMeters = FVector::Distance(
        Swimmers[SelectedSwimmerIndex].SwimmerWorldPositionMeters,
        GetActorLocation() / kCmPerM);
    RescueInteraction.FeedbackCode = TEXT("rescue_target_selected");
}

void ARaftSimRaftActor::AimRescue(FVector WorldAimDirection)
{
    if (!WorldAimDirection.ContainsNaN() && !WorldAimDirection.IsNearlyZero())
    {
        RescueAimWorldDirection = WorldAimDirection.GetSafeNormal();
    }
}

bool ARaftSimRaftActor::BeginRescue(ERaftSimRescueMethod Method)
{
    if (!Swimmers.IsValidIndex(SelectedSwimmerIndex))
    {
        SelectRescueTarget(1.0f);
    }
    if (!Swimmers.IsValidIndex(SelectedSwimmerIndex))
    {
        return false;
    }
    const FRaftSimSwimmerRescueFrame& Swimmer = Swimmers[SelectedSwimmerIndex];
    FRaftSimSwimmingSkillProfile Skill =
        URaftSimSwimmingSkillLibrary::MakeSwimmingSkillProfile(
            ERaftSimSwimmingSkillLevel::AverageSwimmer);
    const FVector LineStartM =
        (GetActorLocation() + GetActorForwardVector() * 45.0f + FVector(0.0f, 0.0f, 65.0f)) /
        kCmPerM;
    RescueInteraction = URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
        Swimmer.PassengerId,
        Method,
        LineStartM,
        Swimmer.SwimmerWorldPositionMeters,
        RescueAimWorldDirection,
        Swimmer.bThrowLineAvailable,
        Swimmer.TimeInWaterSeconds,
        Skill);
    if (ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide")))
    {
        Guide->SetAvatarAction(
            Method == ERaftSimRescueMethod::ThrowLine
                ? ERaftSimCrewAvatarAction::ThrowLine
                : ERaftSimCrewAvatarAction::ReachRescue);
    }
    return RescueInteraction.Phase == ERaftSimRescueInteractionPhase::LineInFlight ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling;
}

void ARaftSimRaftActor::UpdateRescueInteraction(float DeltaSeconds)
{
    const int32 TargetIndex = FindSwimmerIndex(RescueInteraction.TargetPassengerId);
    if (!Swimmers.IsValidIndex(TargetIndex))
    {
        if (Swimmers.IsEmpty())
        {
            RescueInteraction = FRaftSimRescueInteractionState{};
            SelectedSwimmerIndex = INDEX_NONE;
        }
        return;
    }
    if (RescueInteraction.Phase != ERaftSimRescueInteractionPhase::LineInFlight &&
        RescueInteraction.Phase != ERaftSimRescueInteractionPhase::Pulling)
    {
        return;
    }

    const FVector StartM =
        (GetActorLocation() + GetActorForwardVector() * 45.0f + FVector(0.0f, 0.0f, 65.0f)) /
        kCmPerM;
    FRaftSimSwimmerRescueFrame& Swimmer = Swimmers[TargetIndex];
    RescueInteraction = URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
        RescueInteraction,
        StartM,
        Swimmer.SwimmerWorldPositionMeters,
        DeltaSeconds);

    if (RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry)
    {
        const FVector RaftM = GetActorLocation() / kCmPerM;
        FVector Away = (Swimmer.SwimmerWorldPositionMeters - RaftM).GetSafeNormal2D();
        if (Away.IsNearlyZero())
        {
            Away = FVector::RightVector;
        }
        const FVector TubeTarget = RaftM + Away * 0.9f;
        const float PullAlpha = 1.0f - FMath::Exp(-DeltaSeconds * 1.6f);
        Swimmer.SwimmerWorldPositionMeters = FMath::Lerp(
            Swimmer.SwimmerWorldPositionMeters, TubeTarget, PullAlpha);
        Swimmer.PullInProgress = RescueInteraction.PullProgress;
        Swimmer.RescueMethod = RescueInteraction.Method;
        if (RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry)
        {
            Swimmer.SwimmerWorldPositionMeters = TubeTarget;
            if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId))
            {
                Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
            }
        }
    }
}

bool ARaftSimRaftActor::RequestSelectedReentry()
{
    const int32 TargetIndex = FindSwimmerIndex(RescueInteraction.TargetPassengerId);
    if (!Swimmers.IsValidIndex(TargetIndex))
    {
        return false;
    }
    const float DistanceM = FVector::Distance(
        Swimmers[TargetIndex].SwimmerWorldPositionMeters,
        GetActorLocation() / kCmPerM);
    RescueInteraction = URaftSimSwimmerRescueLibrary::CompleteReseat(
        RescueInteraction, DistanceM);
    if (RescueInteraction.Phase != ERaftSimRescueInteractionPhase::Completed)
    {
        return false;
    }
    ++CompletedRescueCount;
    RemoveSwimmerAt(TargetIndex);
    return true;
}

void ARaftSimRaftActor::RemoveSwimmerAt(int32 Index)
{
    if (!Swimmers.IsValidIndex(Index))
    {
        return;
    }
    const FName PassengerId = Swimmers[Index].PassengerId;
    if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(PassengerId))
    {
        AttachAvatarToSeat(Avatar, PassengerId);
    }
    Swimmers.RemoveAt(Index);
    if (Swimmers.IsEmpty())
    {
        SelectedSwimmerIndex = INDEX_NONE;
        RescueInteraction = FRaftSimRescueInteractionState{};
    }
    else
    {
        SelectedSwimmerIndex = FMath::Clamp(SelectedSwimmerIndex, 0, Swimmers.Num() - 1);
        RescueInteraction = FRaftSimRescueInteractionState{};
        RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Aiming;
        RescueInteraction.TargetPassengerId = Swimmers[SelectedSwimmerIndex].PassengerId;
        RescueInteraction.DistanceMeters = FVector::Distance(
            Swimmers[SelectedSwimmerIndex].SwimmerWorldPositionMeters,
            GetActorLocation() / kCmPerM);
        RescueInteraction.FeedbackCode = TEXT("rescue_target_selected");
    }
}

void ARaftSimRaftActor::ApplySwimmerStroke(
    FName PassengerId,
    FVector WorldDirection,
    float DistanceM)
{
    const int32 Index = FindSwimmerIndex(PassengerId);
    if (!Swimmers.IsValidIndex(Index) || WorldDirection.ContainsNaN())
    {
        return;
    }
    Swimmers[Index].SwimmerWorldPositionMeters +=
        WorldDirection.GetSafeNormal2D() * FMath::Clamp(DistanceM, 0.0f, 0.65f);
}

void ARaftSimRaftActor::ForceCrewOverboardForTesting(int32 Count)
{
    SpawnSwimmers(Count, false);
}

void ARaftSimRaftActor::ResetToCheckpoint()
{
    for (const FRaftSimSwimmerRescueFrame& Swimmer : Swimmers)
    {
        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId))
        {
            AttachAvatarToSeat(Avatar, Swimmer.PassengerId);
        }
    }
    Swimmers.Reset();
    RescueInteraction = FRaftSimRescueInteractionState{};
    SelectedSwimmerIndex = INDEX_NONE;
    RescueFailureResetRemaining = -1.0f;
    RaftMode = ERaftSimRaftMode::Upright;
    FlipRiskLatchSeconds = 0.0f;
    SetActorTransform(CheckpointTransform);
    RaftCondition = URaftSimRaftConditionLibrary::ApplyCheckpointRepair(RaftCondition);
    if (RaftAdapter)
    {
        RaftAdapter->ResetFlexiblePersistentState();
        FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
        State.WorldTransform = CheckpointTransform;
        State.LinearVelocityMetersPerSecond = FVector::ZeroVector;
        State.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
        RaftAdapter->SetKinematicState(State);
    }
}

void ARaftSimRaftActor::SetCheckpointTransform(
    FTransform NewCheckpoint, bool bRestoreImmediately)
{
    if (!NewCheckpoint.IsValid())
    {
        return;
    }
    CheckpointTransform = NewCheckpoint;
    if (bRestoreImmediately)
    {
        ResetToCheckpoint();
    }
}

void ARaftSimRaftActor::UpdateRaftCondition(float DeltaSeconds)
{
    if (!RaftAdapter)
    {
        return;
    }
    const FRaftSimFlexStepTelemetry& Telemetry = RaftAdapter->GetLastFlexibleStepTelemetry();
    FRaftSimRaftContactExposure Exposure;
    Exposure.DeltaSeconds = DeltaSeconds;
    Exposure.MaximumIndentationM = static_cast<float>(Telemetry.MaxIndentationM);
    Exposure.ContactCount = Telemetry.ContactCount;
    Exposure.WrappingContactCount = Telemetry.WrappingContactCount;
    Exposure.PinnedObstacleCount = Telemetry.PinnedObstacleCount;
    Exposure.RetainedWaterMassKg = static_cast<float>(Telemetry.TotalRetainedWaterMassKg);
    RaftCondition = URaftSimRaftConditionLibrary::AdvanceCondition(RaftCondition, Exposure);
    RaftAdapter->SetFlexibleConditionModifiers(
        RaftCondition.PressureFraction, RaftCondition.FabricIntegrity);
}

void ARaftSimRaftActor::UpdateRescueLineVisual()
{
    if (!RescueLineVisual)
    {
        return;
    }
    if (!RescueInteraction.bLineVisible)
    {
        RescueLineVisual->SetVisibility(false);
        return;
    }
    RescueLineVisual->SetVisibility(true);
    constexpr int32 Rings = 13;
    constexpr int32 Sides = 6;
    constexpr float RadiusCm = 1.2f;
    const FVector Start = GetActorTransform().InverseTransformPosition(
        RescueInteraction.LineStartWorldMeters * kCmPerM);
    const FVector End = GetActorTransform().InverseTransformPosition(
        RescueInteraction.LineEndWorldMeters * kCmPerM);
    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    for (int32 Ring = 0; Ring < Rings; ++Ring)
    {
        const float T = static_cast<float>(Ring) / (Rings - 1);
        FVector Center = FMath::Lerp(Start, End, T);
        Center.Z -= 28.0f * 4.0f * T * (1.0f - T);
        const FVector Tangent = (End - Start + FVector(0.0f, 0.0f, -28.0f * 4.0f * (1.0f - 2.0f * T))).GetSafeNormal();
        FVector SideAxis = FVector::CrossProduct(Tangent, FVector::UpVector).GetSafeNormal();
        if (SideAxis.IsNearlyZero())
        {
            SideAxis = FVector::RightVector;
        }
        const FVector UpAxis = FVector::CrossProduct(SideAxis, Tangent).GetSafeNormal();
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const float A = 2.0f * PI * Side / Sides;
            const FVector Normal = FMath::Cos(A) * SideAxis + FMath::Sin(A) * UpAxis;
            Vertices.Add(Center + Normal * RadiusCm);
            Normals.Add(Normal);
            UVs.Add(FVector2D(T * 8.0f, static_cast<float>(Side) / Sides));
            Tangents.Add(FProcMeshTangent(Tangent, false));
        }
    }
    for (int32 Ring = 0; Ring < Rings - 1; ++Ring)
    {
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 NextSide = (Side + 1) % Sides;
            const int32 A = Ring * Sides + Side;
            const int32 B = (Ring + 1) * Sides + Side;
            const int32 C = Ring * Sides + NextSide;
            const int32 D = (Ring + 1) * Sides + NextSide;
            Triangles.Append({A, B, C, C, B, D});
        }
    }
    const TArray<FLinearColor> Colors;
    RescueLineVisual->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false);
    if (UMaterialInterface* RopeMat = LoadObject<UMaterialInterface>(
            nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow")))
    {
        RescueLineVisual->SetMaterial(0, RopeMat);
    }
}

FVector ARaftSimRaftActor::SampleWaterVelocityMps(const FVector& WorldLocationCm) const
{
    if (Bridge != nullptr)
    {
        if (const URaftSimWaterRuntimeAdapter* WaterAdapter = Bridge->GetWaterRuntime())
        {
            FRaftSimWaterSample Sample;
            if (WaterAdapter->SampleWaterAtWorldPosition(WorldLocationCm, Sample) && Sample.bWet)
            {
                // Cap to a physical big-water speed so a solver spike or a
                // non-finite sample can never teleport a swimmer.
                FVector Velocity = Sample.VelocityMetersPerSecond;
                if (!Velocity.ContainsNaN())
                {
                    return Velocity.GetClampedToMaxSize(12.0f);
                }
            }
        }
    }
    return FVector::ZeroVector;
}

void ARaftSimRaftActor::RequestReflip()
{
    if (RaftMode != ERaftSimRaftMode::Capsized)
    {
        return;
    }
    // Re-right the hull at the capsize location (the guide flips the boat
    // among the crew), drain retained water, and begin reseating swimmers.
    RaftMode = ERaftSimRaftMode::Recovering;
    SetActorLocationAndRotation(
        CapsizeLocation, FRotator(0.0f, GetActorRotation().Yaw, 0.0f));
    if (RaftAdapter != nullptr)
    {
        RaftAdapter->ResetFlexiblePersistentState();
        FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
        State.WorldTransform = GetActorTransform();
        // Guide has re-established the eddy: shed the residual drift the flip
        // imparted so the raft holds station over the swimmers to reseat them.
        State.LinearVelocityMetersPerSecond = FVector::ZeroVector;
        State.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
        RaftAdapter->SetKinematicState(State);
    }
}

void ARaftSimRaftActor::HandleHighSideResponse(int32 Direction)
{
    if (RaftAdapter == nullptr || Direction == 0)
    {
        return;
    }
    FRaftSimFlexCrewAction Action;
    Action.SeatId = TEXT("guide");
    Action.HighSideDirection = FMath::Clamp(Direction, -1, 1);
    Action.bBrace = true;
    RaftAdapter->SetFlexibleCrewActions({Action});
    ++HighSideResponseCount;
}

void ARaftSimRaftActor::ForceOverwashForTesting(float SurfaceHeightM, FVector FlowVelocityMps)
{
    if (RaftAdapter == nullptr)
    {
        return;
    }
    if (SurfaceHeightM < 0.0f)
    {
        RaftAdapter->SetFlexibleUniformWater(FRaftSimFlexUniformWater{}, false);
        return;
    }
    FRaftSimFlexUniformWater Water;
    Water.SurfaceHeightM = SurfaceHeightM;
    Water.VelocityMps = FlowVelocityMps;
    Water.bWet = true;
    RaftAdapter->SetFlexibleUniformWater(Water, true);
}

void ARaftSimRaftActor::ResetMotionForTesting()
{
    if (RaftAdapter == nullptr)
    {
        return;
    }
    FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
    State.LinearVelocityMetersPerSecond = FVector::ZeroVector;
    State.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
    RaftAdapter->SetKinematicState(State);
    ActiveCrewCommand = ERaftSimCrewCommand::Rest;
    PendingCrewCommand = ERaftSimCrewCommand::Rest;
    CrewReactionRemaining = 0.0f;
    CrewStrokeTimer = 0.0f;
}
