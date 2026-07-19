#include "RaftSimRaftActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimCrewStateContracts.h"
#include "RaftSimFlexibleRaftModel.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimRiverbedActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float kCmPerM = 100.0f;
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
    if (URaftSimWaterRuntimeAdapter* WaterAdapter = BridgeSubsystem->GetWaterRuntime())
    {
        // River map: load a cooked steady-state flow window if the level places
        // a config actor. Otherwise the dev flat tank.
        ARaftSimRiverWaterConfig* RiverConfig = nullptr;
        if (TActorIterator<ARaftSimRiverWaterConfig> It(GetWorld()); It)
        {
            RiverConfig = *It;
        }
        bool bRiverConfigured = false;
        if (RiverConfig != nullptr)
        {
            bRiverConfigured = WaterAdapter->ConfigureRiverWindow(
                RiverConfig->CookedFieldsDir, RiverConfig->FlowBand.ToString(),
                RiverConfig->WindowCenterM,
                FVector2D(RiverConfig->WindowExtentM, RiverConfig->WindowExtentM),
                /*RoughnessManning=*/0.041f);
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

        // Photoreal terrain: spawn a riverbed actor that renders the cooked
        // window's DEM bed and banks. Skipped if one is already placed.
        bool bHasBed = false;
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

    // D1-D4 flexible-raft stack behind the adapter: tube layout from this
    // hull, no crew seats yet (the crew slice binds them).
    FRaftSimFlexParameters FlexParameters;
    FlexParameters.MassKg = MassKg;
    FlexParameters.LengthM = FootprintLengthM;
    FlexParameters.WidthM = FootprintWidthM;
    FlexParameters.TubeRadiusM = TubeRadiusM;
    FlexParameters.GuideMassKg = 0.0;
    FlexParameters.PassengerMassKg = 0.0;
    FlexParameters.PassengerCount = 0;
    Adapter->ConfigureFlexibleRaftModel(FlexParameters, {});

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

void ARaftSimRaftActor::BuildRaftVisual()
{
    if (RaftVisual == nullptr)
    {
        return;
    }
    RaftSimRaftMesh::FMeshData Tubes, Floor;
    RaftSimRaftMesh::BuildInflatableRaft(
        FootprintLengthM, FootprintWidthM, TubeRadiusM, Tubes, Floor);
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
        RaftAdapter->GetFlexibleVisualSegments());
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
    UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    UStaticMesh* Cylinder = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto Mat = [](const TCHAR* Path)
    { return LoadObject<UMaterialInterface>(nullptr, Path); };
    UMaterialInterface* SkinMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Skin.M_RaftSim_Skin"));
    UMaterialInterface* HelmetMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"));
    UMaterialInterface* WetsuitMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"));
    UMaterialInterface* ShaftMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"));
    UMaterialInterface* BladeMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade"));
    UMaterialInterface* PFDMats[4] = {
        Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD")),
        Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Red.M_RaftSim_PFD_Red")),
        Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow")),
        Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Blue.M_RaftSim_PFD_Blue")),
    };

    auto AddPart = [this](UStaticMesh* MeshAsset, UMaterialInterface* Material,
                          const FVector& LocCm, const FRotator& Rot, const FVector& Scale)
    {
        if (MeshAsset == nullptr)
        {
            return;
        }
        UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
        C->SetupAttachment(Root);
        C->RegisterComponent();
        C->SetStaticMesh(MeshAsset);
        C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        if (Material != nullptr)
        {
            C->SetMaterial(0, Material);
        }
        C->SetRelativeLocationAndRotation(LocCm, Rot);
        C->SetRelativeScale3D(Scale);
        CrewMeshes.Add(C);
    };

    // Build one seated paddler (metres, paddler-local: +X downstream, +Z up),
    // offset to SeatCm on the raft. Engine primitives are 1 m (sphere r=0.5,
    // cylinder h=1/r=0.5), so a radius r maps to scale 2r and a bar of length L
    // to scale-Z L.
    auto Bar = [&](UStaticMesh* MeshAsset, UMaterialInterface* Material, const FVector& SeatCm,
                   const FVector& AMeters, const FVector& BMeters, float RadiusM)
    {
        const FVector A = SeatCm + AMeters * kCmPerM;
        const FVector B = SeatCm + BMeters * kCmPerM;
        const FVector D = B - A;
        const float LenM = FMath::Max(D.Size() / kCmPerM, 0.01f);
        const FRotator Rot = FRotationMatrix::MakeFromZ(D.GetSafeNormal()).Rotator();
        AddPart(MeshAsset, Material, (A + B) * 0.5f, Rot,
                FVector(2.0f * RadiusM, 2.0f * RadiusM, LenM));
    };
    auto Ball = [&](UStaticMesh* MeshAsset, UMaterialInterface* Material, const FVector& SeatCm,
                    const FVector& PosMeters, float RadiusM)
    {
        AddPart(MeshAsset, Material, SeatCm + PosMeters * kCmPerM, FRotator::ZeroRotator,
                FVector(2.0f * RadiusM));
    };

    auto BuildPaddler = [&](const FVector& SeatCm, UMaterialInterface* PFDMat)
    {
        // Torso + splash jacket.
        Bar(Cylinder, WetsuitMat, SeatCm, FVector(0.0f, 0.0f, 0.02f), FVector(0.05f, 0.0f, 0.52f), 0.15f);
        // Life jacket (PFD) over the chest.
        Bar(Cylinder, PFDMat, SeatCm, FVector(0.03f, 0.0f, 0.28f), FVector(0.05f, 0.0f, 0.50f), 0.20f);
        // Head + helmet.
        Ball(Sphere, SkinMat, SeatCm, FVector(0.08f, 0.0f, 0.66f), 0.11f);
        Ball(Sphere, HelmetMat, SeatCm, FVector(0.08f, 0.0f, 0.70f), 0.125f);
        // Paddle held diagonally across the body: shaft + blade.
        const FVector GripHigh(0.30f, 0.22f, 0.46f);
        const FVector BladeEnd(0.56f, -0.30f, -0.10f);
        Bar(Cylinder, ShaftMat, SeatCm, GripHigh, BladeEnd, 0.028f);
        const FVector D = (BladeEnd - GripHigh).GetSafeNormal();
        const FRotator BladeRot = FRotationMatrix::MakeFromZ(D).Rotator();
        AddPart(Cube, BladeMat, SeatCm + (BladeEnd + D * 0.14f) * kCmPerM, BladeRot,
                FVector(0.22f, 0.03f, 0.30f));
        // Arms reaching to the paddle grips.
        Bar(Cylinder, WetsuitMat, SeatCm, FVector(0.03f, 0.16f, 0.50f), GripHigh, 0.05f);
        Bar(Cylinder, WetsuitMat, SeatCm, FVector(0.03f, -0.16f, 0.50f), FVector(0.42f, -0.02f, 0.20f), 0.05f);
    };

    // Two rows of paddlers along the tubes plus a stern guide, all facing
    // downstream. Seats sit on the tube tops.
    const float SeatZ = 30.0f;
    for (int32 Index = 0; Index < PaddlerCount; ++Index)
    {
        const float Row = (Index % 2 == 0) ? -0.62f : 0.62f; // port / starboard
        const float Bow = 1.15f - (Index / 2) * 1.05f;        // fore to aft (m)
        BuildPaddler(FVector(Bow * kCmPerM, Row * kCmPerM, SeatZ), PFDMats[Index % 4]);
    }
    // Stern guide, centred.
    BuildPaddler(FVector(-1.75f * kCmPerM, 0.0f, SeatZ + 8.0f), PFDMats[0]);
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
        SetActorLocationAndRotation(
            Location, Output.RaftState.WorldTransform.GetRotation().GetNormalized());
    }

    UpdateCapsizeLoop(FMath::Min(DeltaSeconds, 0.25f));
    UpdateCrew(FMath::Min(DeltaSeconds, 0.25f));
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
        return;
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

    // Eject the crew as swimmers at the raft, drifting downstream.
    Swimmers.Reset();
    const FVector RaftM = CapsizeLocation / kCmPerM;
    const FVector FlowMps = SampleWaterVelocityMps(CapsizeLocation);
    for (int32 Index = 0; Index < CrewSize; ++Index)
    {
        FRaftSimSwimmerRescueFrame Swimmer;
        Swimmer.PassengerId = (Index == 0) ? FName(TEXT("guide")) : FName(*FString::Printf(TEXT("paddler_%d"), Index));
        // Scatter swimmers slightly around the flip point.
        const float Angle = (2.0f * PI * Index) / FMath::Max(1, CrewSize);
        Swimmer.SwimmerWorldPositionMeters =
            RaftM + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * 1.5f;
        Swimmer.SwimmerDriftVelocityMetersPerSecond = FlowMps;
        Swimmer.RescueWindowSeconds = 12.0f;
        Swimmer.bThrowLineAvailable = true;
        Swimmers.Add(Swimmer);
    }

    // Visual spheres for each swimmer.
    for (UStaticMeshComponent* Mesh : SwimmerMeshes)
    {
        if (Mesh != nullptr)
        {
            Mesh->DestroyComponent();
        }
    }
    SwimmerMeshes.Reset();
    UStaticMesh* SphereMesh =
        LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    UMaterialInterface* PFDMat = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"));
    UMaterialInterface* SkinMat = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Skin.M_RaftSim_Skin"));
    UMaterialInterface* HelmetMat = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"));
    for (int32 Index = 0; Index < Swimmers.Num(); ++Index)
    {
        // The tracked component (moved each frame) is the PFD torso; the head
        // and helmet ride along attached to it.
        UStaticMeshComponent* Torso = NewObject<UStaticMeshComponent>(this);
        Torso->SetupAttachment(nullptr);
        Torso->RegisterComponent();
        Torso->SetStaticMesh(SphereMesh);
        Torso->SetWorldScale3D(FVector(0.62f, 0.5f, 0.42f));
        Torso->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        if (PFDMat != nullptr)
        {
            Torso->SetMaterial(0, PFDMat);
        }
        Torso->SetWorldLocation(Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM);

        auto AttachBall = [this, Torso](UStaticMesh* MeshAsset, UMaterialInterface* Material,
                                        const FVector& OffsetCm, float Scale)
        {
            if (MeshAsset == nullptr)
            {
                return;
            }
            UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
            C->SetupAttachment(Torso);
            C->RegisterComponent();
            C->SetStaticMesh(MeshAsset);
            C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            if (Material != nullptr)
            {
                C->SetMaterial(0, Material);
            }
            C->SetWorldScale3D(FVector(Scale));
            C->SetRelativeLocation(OffsetCm);
        };
        AttachBall(SphereMesh, SkinMat, FVector(18.0f, 0.0f, 22.0f), 0.2f);
        AttachBall(SphereMesh, HelmetMat, FVector(18.0f, 0.0f, 26.0f), 0.23f);
        SwimmerMeshes.Add(Torso);
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
        if (SwimmerMeshes.IsValidIndex(Index) && SwimmerMeshes[Index] != nullptr)
        {
            SwimmerMeshes[Index]->SetWorldLocation(
                Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM);
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
            if (SwimmerMeshes.IsValidIndex(Index) && SwimmerMeshes[Index] != nullptr)
            {
                SwimmerMeshes[Index]->DestroyComponent();
            }
            SwimmerMeshes.RemoveAt(Index);
            Swimmers.RemoveAt(Index);
        }
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
