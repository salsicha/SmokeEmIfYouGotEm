#include "RaftSimRaftActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimFlexibleRaftModel.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/ConstructorHelpers.h"

ARaftSimRaftActor::ARaftSimRaftActor()
{
    PrimaryActorTick.bCanEverTick = true;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

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
        WaterAdapter->ConfigureDevTankWindow(
            FVector2D(-80.0, -80.0), 160.0f, 160.0f, 2.0f,
            /*SurfaceHeightM=*/0.0f, /*DepthM=*/3.0f);
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

    FRaftSimPhysicsTickInput Input;
    Input.FrameDeltaSeconds = FMath::Min(DeltaSeconds, 0.25f);
    const FRaftSimPhysicsTickOutput Output = Bridge->TickBridge(Input);
    if (Output.CommittedPhysicsFrame > 0)
    {
        const FTransform& RaftTransform = Output.RaftState.WorldTransform;
        SetActorLocationAndRotation(
            RaftTransform.GetTranslation(), RaftTransform.GetRotation().GetNormalized());
    }
}
