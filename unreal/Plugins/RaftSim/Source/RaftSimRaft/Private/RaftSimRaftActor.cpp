#include "RaftSimRaftActor.h"
#include "ProfilingDebugging/CsvProfiler.h"
CSV_DEFINE_CATEGORY(RaftSimTickRaft,true);
#include "RaftSimCrewRoster.h"
#include "RaftSimCapsizePolicy.h"
#include "RaftSimWorldPositionGuard.h"
#include "RaftSimAccessoryMesh.h"

#include "Components/SceneComponent.h"
#include "RaftSimCrewBoarding.h"
#include "RaftSimSwimmerSurface.h"
#include "RaftSimSwimmerSubmersion.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Components/LightComponent.h"
#include "Engine/DirectionalLight.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimImmutableRestMesh.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimCrewStateContracts.h"
#include "RaftSimFlexibleRaftModel.h"
#include "RaftSimCrewSeatLayout.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimCartesianWaterRegions.h"
#include "RaftSimRiverWaterStreamingActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UnrealClient.h"
#include "RaftSimRiverbedActor.h"
#include "RaftSimWaterVfxActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "UObject/ConstructorHelpers.h"

// A commercial guide paddles from a stern quarter on their dominant side â€”
// a right-handed guide sits the right tube, a lefty the left ("if they are
// right handed they sit on the right side of the boat", player report
// 2026-08-31; the old seat was a centred coxswain perch no paddle guide
// uses). Normal physical loads share the authored horizontal anchors;
// independent Python/D6 reference fixtures keep their reference layout.
static TAutoConsoleVariable<int32> CVarRaftSimGuideLeftHanded(
    TEXT("raftsim.GuideLeftHanded"), 0,
    TEXT("0 = right-handed guide (sits the right stern quarter, paddles on ")
    TEXT("the right; default), 1 = left-handed (mirrored)."));

// Which boat the raft is rigged as, overriding the map (review captures and
// test tanks): -1 by map (default), 0 paddle crew, 1 Colorado oar rig,
// 2 Zambezi oar rig. Read at BeginPlay.
static TAutoConsoleVariable<int32> CVarRaftSimRaftRig(
    TEXT("raftsim.RaftRig"), -1,
    TEXT("-1 = by map (oar rigs on the Colorado and Zambezi maps; default), ")
    TEXT("0 = paddle crew, 1 = Colorado oar rig, 2 = Zambezi oar rig."));

namespace
{
constexpr float kCmPerM = 100.0f;
constexpr float kGuideMassKg = 85.0f;
constexpr float kPassengerMassKg = 75.0f;

bool IsFiniteVector(const FVector& Value)
{
    return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
}

bool IsPropulsiveCrewCommand(ERaftSimCrewCommand Command)
{
    return Command == ERaftSimCrewCommand::AllForward ||
        Command == ERaftSimCrewCommand::AllBackward ||
        Command == ERaftSimCrewCommand::TurnLeft ||
        Command == ERaftSimCrewCommand::TurnRight ||
        Command == ERaftSimCrewCommand::Stop;
}

bool FlexVisualStateMatches(
    const TArray<FRaftSimFlexVisualSegmentState>& Left,
    const TArray<FRaftSimFlexVisualSegmentState>& Right)
{
    if (Left.Num() != Right.Num())
    {
        return false;
    }
    constexpr double ShapeToleranceM = 1.0e-6;
    for (int32 Index = 0; Index < Left.Num(); ++Index)
    {
        const FRaftSimFlexVisualSegmentState& A = Left[Index];
        const FRaftSimFlexVisualSegmentState& B = Right[Index];
        if (A.SegmentId != B.SegmentId ||
            !A.LocalPositionM.Equals(B.LocalPositionM, ShapeToleranceM) ||
            !A.ContactNormalLocal.Equals(B.ContactNormalLocal, ShapeToleranceM) ||
            !FMath::IsNearlyEqual(A.CompressionM, B.CompressionM, ShapeToleranceM) ||
            !FMath::IsNearlyEqual(A.FreeboardLossM, B.FreeboardLossM, ShapeToleranceM) ||
            !FMath::IsNearlyEqual(A.IndentationM, B.IndentationM, ShapeToleranceM) ||
            A.bWrapping != B.bWrapping || A.bPinned != B.bPinned ||
            A.bRecovering != B.bRecovering)
        {
            return false;
        }
    }
    return true;
}
}

ARaftSimRaftActor::ARaftSimRaftActor()
{
    PrimaryActorTick.bCanEverTick = true;
    GuideStrokeAction = ERaftSimCrewAvatarAction::SeatedIdle;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    // Collision/buoyancy footprint box â€” kept for the raft-body physics but
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
    // Generated and production chamber centrelines live one radius above their
    // local origin. Align those centres with the rigid-body origin used by both
    // buoyancy and terrain contact; presentation must not carry a second
    // waterline datum.
    RaftVisual->SetRelativeLocation(
        FVector(0.0f, 0.0f, -TubeRadiusM * kCmPerM));

    RescueLineVisual = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("RescueLineVisual"));
    RescueLineVisual->SetupAttachment(Root);
    RescueLineVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RescueLineVisual->SetVisibility(false);
    ThrowBagVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ThrowBagVisual"));
    ThrowBagVisual->SetupAttachment(Root);
    ThrowBagVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ThrowBagVisual->SetVisibility(false);
    // The stowed bag's size: a rope-packed sack 14 cm across and about 30 cm
    // long, flying bottom first with the line paying out of its top.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> BagMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (BagMesh.Succeeded()) ThrowBagVisual->SetStaticMesh(BagMesh.Object);
    ThrowBagVisual->SetRelativeScale3D(FVector(.14, .14, .30));

    SternSeatAttachPoint = CreateDefaultSubobject<USceneComponent>(TEXT("SternSeatAttachPoint"));
    SternSeatAttachPoint->SetupAttachment(Root);
    // Guide sits on the stern tube, slightly above the deck.
    SternSeatAttachPoint->SetRelativeLocation(FVector(-165.0f, 0.0f, 55.0f));
}

ERaftSimRaftRig ARaftSimRaftActor::ResolveRaftRigForMap(const FString& MapName)
{
    FString Leaf = UWorld::RemovePIEPrefix(MapName);
    int32 Slash = INDEX_NONE;
    if (Leaf.FindLastChar(TEXT('/'), Slash))
    {
        Leaf = Leaf.Mid(Slash + 1);
    }
    int32 Dot = INDEX_NONE;
    if (Leaf.FindChar(TEXT('.'), Dot))
    {
        Leaf = Leaf.Left(Dot);
    }
    if (Leaf == TEXT("L_Hance"))
    {
        return ERaftSimRaftRig::ColoradoOarRig;
    }
    if (Leaf == TEXT("L_Zambezi") || Leaf == TEXT("L_ZambeziUpperGorge"))
    {
        return ERaftSimRaftRig::ZambeziOarRig;
    }
    return ERaftSimRaftRig::PaddleCrew;
}

void ARaftSimRaftActor::ResolveRaftRig()
{
    ERaftSimRaftRig Rig = RaftRig;
    const int32 Override = CVarRaftSimRaftRig.GetValueOnGameThread();
    if (Override >= 0 && Override <= 2)
    {
        Rig = static_cast<ERaftSimRaftRig>(Override + 1);
    }
    if (Rig == ERaftSimRaftRig::Auto)
    {
        Rig = ResolveRaftRigForMap(GetWorld() ? GetWorld()->GetMapName() : FString());
    }
    ResolvedRaftRig = Rig;
    if (IsSoloOarRig())
    {
        // One rower, seated on the frame: no paddlers, and a capsize puts
        // only the rower in the water.
        PaddlerCount = 0;
        CrewSize = 1;
    }
}

void ARaftSimRaftActor::SetRaftRigForValidation(ERaftSimRaftRig InRig)
{
    RaftRig = InRig;
    ResolveRaftRig();
}

void ARaftSimRaftActor::SetOarIntents(float Left, float Right)
{
    ManualOarIntents = FVector2D(FMath::Clamp(Left, -1.f, 1.f), FMath::Clamp(Right, -1.f, 1.f));
    RefreshOarCommandIntents();
}

FVector2D ARaftSimRaftActor::ResolveOarCommandIntents() const
{
    if (ActiveCrewCommand == ERaftSimCrewCommand::HighSide || ActiveCrewCommand == ERaftSimCrewCommand::GetDown)
        return FVector2D::ZeroVector;
    FVector2D Intents = FVector2D::ZeroVector;
    switch (ActiveCrewCommand)
    {
        case ERaftSimCrewCommand::AllForward: Intents = FVector2D(1, 1); break;
        case ERaftSimCrewCommand::AllBackward: Intents = FVector2D(-1, -1); break;
        case ERaftSimCrewCommand::TurnLeft: Intents = FVector2D(-1, 1); break;
        case ERaftSimCrewCommand::TurnRight: Intents = FVector2D(1, -1); break;
        case ERaftSimCrewCommand::Stop:
        {
            // Brake the boat's bow-axis way with the blades, never by resetting velocity.
            const float Speed = FVector::DotProduct(GetRaftVelocity(), GetActorForwardVector());
            const float Brake = FMath::Abs(Speed) > .05f ? -FMath::Clamp(Speed / .5f, -1.f, 1.f) : 0.f;
            Intents = FVector2D(Brake, Brake);
            break;
        }
        default: break;
    }
    if (TransientOarSeconds > 0.f) Intents = TransientOarIntents;
    if (!ManualOarIntents.IsNearlyZero()) Intents = ManualOarIntents;
    if (OarSteerSeconds > 0.f) Intents += FVector2D(OarSteerScale, -OarSteerScale);
    return FVector2D(FMath::Clamp(Intents.X, -1., 1.), FMath::Clamp(Intents.Y, -1., 1.));
}

void ARaftSimRaftActor::RefreshOarCommandIntents()
{
    if (OarRig && IsSoloOarRig())
    {
        const FVector2D Intents = ResolveOarCommandIntents();
        OarRig->SetOarIntents(Intents.X, Intents.Y);
    }
}

void ARaftSimRaftActor::PoseOarRigForValidation(float Phase, float LeftDirection, float RightDirection)
{
    if (OarRig && OarRig->IsBuilt())
    {
        OarRig->PoseForValidation(Phase, LeftDirection, RightDirection, FindAvatar(TEXT("guide")));
    }
}

void ARaftSimRaftActor::BeginPlay()
{
    Super::BeginPlay();
    ResolveRaftRig();

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
    // Deterministic stepping and replay hashes remain available, but gameplay
    // must not append a JSON line to disk on every fixed water tick. Validation
    // tools opt into capture explicitly when they need an audit artifact.
    WaterConfig.bEnableDeterministicCapture = false;

    // The rigid-body support stage integrates one combined body, so its mass
    // and inertia must include the occupied crew represented by D2. The flex
    // model below keeps MassKg as the dry raft mass and applies the same crew
    // masses to tube compression; using dry mass here made moving-water rafts
    // settle far below their loaded waterline and admit runaway deck water.
    // An oar rig adds its frame and load to the boat's own mass.
    const float DryMassKg = MassKg + URaftSimOarRigComponent::GetRigLoadKg(ResolvedRaftRig);
    const float LoadedBodyMassKg =
        DryMassKg + kGuideMassKg + kPassengerMassKg * static_cast<float>(PaddlerCount);
    FRaftSimRaftBodyConfig BodyConfig;
    BodyConfig.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    BodyConfig.MassKg = LoadedBodyMassKg;
    BodyConfig.TubeRadiusMeters = TubeRadiusM;
    BodyConfig.LengthMeters = FootprintLengthM;
    BodyConfig.WidthMeters = FootprintWidthM;
    // Yaw inertia of a flat raft: (1/12) m (L^2 + W^2); roll/pitch stiffer
    // response at 0.45x, matching the P1 integrator.
    const float YawInertia =
        LoadedBodyMassKg *
        (FootprintLengthM * FootprintLengthM + FootprintWidthM * FootprintWidthM) / 12.0f;
    BodyConfig.InertiaTensorKgM2 =
        FVector(0.45f * YawInertia, 0.45f * YawInertia, YawInertia);
    // Authored maps can retain the previous 2.6 instance value even after the
    // CDO default changes. A 5.2 reserve settles the support frame about 14 cm
    // below flat water instead of 21 cm, leaving the loaded 56 cm tubes and
    // self-bailing floor above routine approach flow before flex compression.
    constexpr float kMinimumLoadedBuoyancyReserve = 5.2f;
    BodyConfig.BuoyancyWeightMultiple =
        FMath::Max(BuoyancyWeightMultiple, kMinimumLoadedBuoyancyReserve);
    // Authored maps may retain the old 45/650 N coefficients. Even 650 left
    // the loaded production raft visibly slipping behind the foam/current for
    // several seconds after a local flow change. Preserve the authoring
    // control while enforcing a floor that captures passive drift promptly;
    // paddle impulses still create velocity relative to the water and decay
    // through this same physical hull resistance.
    // The named-rapid handoff can raise the sampled current from a calm
    // transit seed to nearly 3 m/s in one window update. At 1800 the loaded
    // raft still ran at only ~74% of local water speed ten seconds later, so
    // solver-advected froth visibly passed the boat. This floor gives the
    // broad immersed hull a prompt current-capture time without adding any
    // propulsion: the force remains strictly relative-water drag and falls to
    // zero when raft and current match.
    constexpr float kMinimumLoadedHullDrag = 9000.0f;
    BodyConfig.LinearDragCoefficient =
        FMath::Max(LinearDragCoefficient, kMinimumLoadedHullDrag);
    // No floor: this coefficient exists precisely to stay far below the
    // blunt one so bow-first paddle momentum coasts down physically.
    BodyConfig.ForwardSlicingDragCoefficient = ForwardSlicingDragCoefficient;
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
            if (bCoordinateMapReady && WaterAdapter->HasCartesianWaterCoordinates() &&
                RiverConfig->bEnableMovingWindowStreaming)
            {
                bRiverConfigured = FRaftSimCartesianWaterRegions::ConfigureAtWorldPosition(
                    WaterAdapter, RiverConfig->StreamingManifestPath,
                    RiverConfig->FlowBand.ToString(), GetActorLocation());
            }
            else if (bCoordinateMapReady && RiverConfig->bEnableMovingWindowStreaming)
            {
                const bool bSouthForkSingleSurface =
                    RiverConfig->CookedFieldsDir.Contains(
                        TEXT("south_fork_american_chili_bar/full_hydraulics"),
                        ESearchCase::IgnoreCase);
                const float MovingStationExtentM = bSouthForkSingleSurface
                    ? FMath::Max(
                          RiverConfig->MovingWindowStationExtentM,
                          ARaftSimWaterSurfaceActor::
                              GetSouthForkHydraulicWindowLengthMeters())
                    : RiverConfig->MovingWindowStationExtentM;
                FVector2D MovingWindowCenterM = RiverConfig->WindowCenterM;
                if (bSouthForkSingleSurface)
                {
                    MovingWindowCenterM.X += 0.30f * MovingStationExtentM;
                }
                float MinimumRiverStationM = 0.0f;
                float MaximumRiverStationM = 0.0f;
                if (bSouthForkSingleSurface &&
                    WaterAdapter->GetRiverStationRangeM(
                        MinimumRiverStationM, MaximumRiverStationM))
                {
                    const float HalfExtentM = 0.5f * MovingStationExtentM;
                    MovingWindowCenterM.X = FMath::Clamp(
                        MovingWindowCenterM.X,
                        MinimumRiverStationM + HalfExtentM,
                        MaximumRiverStationM - HalfExtentM);
                }
                bRiverConfigured = WaterAdapter->ConfigureMovingRiverWindow(
                    RiverConfig->CookedFieldsDir, RiverConfig->FlowBand.ToString(),
                    MovingWindowCenterM,
                    FVector2D(
                        MovingStationExtentM,
                        RiverConfig->MovingWindowLateralExtentM),
                    /*RoughnessManning=*/0.041f);
            }
            else if (bCoordinateMapReady)
            {
                bRiverConfigured = WaterAdapter->ConfigureRiverWindow(
                    RiverConfig->CookedFieldsDir, RiverConfig->FlowBand.ToString(),
                    RiverConfig->WindowCenterM,
                    FVector2D(RiverConfig->WindowExtentM, RiverConfig->WindowExtentM),
                    /*RoughnessManning=*/0.041f,
                    RiverConfig->bRecenterHydraulicCrux);
            }
        }
        if (!bRiverConfigured && RiverConfig)
        {
            // A broken authored river is not a flat tank. Leave the raft
            // stationary and report the missing data instead of disguising
            // integration failures with unrelated water or falling physics.
            UE_LOG(LogTemp, Error, TEXT("RaftSim authored river initialization failed: %s; raft disabled, no tank fallback"),
                *RiverConfig->StreamingManifestPath);
            SetActorTickEnabled(false);
            return;
        }
        if (!RiverConfig)
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
    FlexParameters.MassKg = DryMassKg;
    FlexParameters.LengthM = FootprintLengthM;
    FlexParameters.WidthM = FootprintWidthM;
    FlexParameters.TubeRadiusM = TubeRadiusM;
    FlexParameters.GuideMassKg = kGuideMassKg;
    FlexParameters.PassengerMassKg = kPassengerMassKg;
    FlexParameters.PassengerCount = PaddlerCount;
    Adapter->ConfigureFlexibleRaftModel(
        FlexParameters, IsSoloOarRig()
            ? RaftSimCrewSeatLayout::BuildOarRowerSeats(FlexParameters)
            : RaftSimCrewSeatLayout::BuildNormalSeats(FlexParameters,
                CVarRaftSimGuideLeftHanded.GetValueOnGameThread() != 0), 18000.0,
        /*bBodyMassIncludesAllSeats=*/true);

    // Seed the adapter in the local water frame. Starting a floating raft at
    // zero world velocity while the material immediately advects at the live
    // solver velocity guarantees that the foam visibly outruns the boat until
    // drag catches up. A passive raft already placed in the current should be
    // carried with that current from its first physics frame.
    FRaftSimRaftKinematicState InitialState;
    InitialState.WorldTransform.SetTranslation(GetActorLocation());
    InitialState.WorldTransform.SetRotation(GetActorQuat());
    if (const URaftSimWaterRuntimeAdapter* WaterAdapter =
            BridgeSubsystem->GetWaterRuntime())
    {
        FRaftSimWaterSample SpawnWater;
        if (WaterAdapter->SampleWaterAtWorldPosition(
                GetActorLocation(), SpawnWater) &&
            SpawnWater.bWet &&
            !SpawnWater.VelocityMetersPerSecond.ContainsNaN())
        {
            InitialState.LinearVelocityMetersPerSecond = FVector(
                SpawnWater.VelocityMetersPerSecond.X,
                SpawnWater.VelocityMetersPerSecond.Y,
                0.0f);
        }
    }
    Adapter->SetKinematicState(InitialState);

    Bridge = BridgeSubsystem;
    RaftAdapter = Adapter;
    const TWeakObjectPtr<ARaftSimRaftActor> WeakRaft(this);
    Adapter->SetCommittedStepObserver([WeakRaft](const FRaftSimRaftKinematicState& K)
    {
        auto* Self=WeakRaft.Get();
        if(Self && Self->RaftMode==ERaftSimRaftMode::Upright &&
            RaftSimCapsizePolicy::PhysicallyInverted(K.WorldTransform.GetRotation(),Self->CapsizeRollDegrees))
        {
            Self->SetActorTransform(K.WorldTransform);
            Self->EnterCapsize();
        }
    });

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

int32 ARaftSimRaftActor::GetWrappingRockContactCount() const
{
    return RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry().WrappingContactCount
        : 0;
}

int32 ARaftSimRaftActor::GetPinnedRockObstacleCount() const
{
    return RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry().PinnedObstacleCount
        : 0;
}

int32 ARaftSimRaftActor::GetRecoveringRockContactCount() const
{
    return RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry().RecoveringContactCount
        : 0;
}

bool ARaftSimRaftActor::IsUsingLiveD3WaterField() const
{
    return RaftAdapter &&
        RaftAdapter->GetLastFlexibleStepTelemetry().bUsedLiveWaterField;
}

int32 ARaftSimRaftActor::GetLiveD3WaterSampleCount() const
{
    return RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry().LiveWaterSampleCount
        : 0;
}

int32 ARaftSimRaftActor::GetLiveD3WetSampleCount() const
{
    return RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry().LiveWetSampleCount
        : 0;
}

float ARaftSimRaftActor::GetD3RetainedWaterMassKg() const
{
    return RaftAdapter
        ? static_cast<float>(
              RaftAdapter->GetLastFlexibleStepTelemetry().TotalRetainedWaterMassKg)
        : 0.0f;
}

bool ARaftSimRaftActor::GetDominantWaterContactPresentation(
    FVector& OutWorldPositionCm,
    FVector& OutWorldNormal,
    float& OutIndentationM) const
{
    OutWorldPositionCm = FVector::ZeroVector;
    OutWorldNormal = FVector::UpVector;
    OutIndentationM = 0.0f;
    if (!RaftAdapter)
    {
        return false;
    }

    const FRaftSimFlexVisualSegmentState* Dominant = nullptr;
    for (const FRaftSimFlexVisualSegmentState& Segment :
         RaftAdapter->GetFlexibleVisualSegments())
    {
        if (Segment.IndentationM > OutIndentationM)
        {
            Dominant = &Segment;
            OutIndentationM = static_cast<float>(Segment.IndentationM);
        }
    }
    if (!Dominant || OutIndentationM <= KINDA_SMALL_NUMBER)
    {
        return false;
    }

    OutWorldPositionCm = GetActorTransform().TransformPosition(
        Dominant->LocalPositionM * 100.0f);
    OutWorldNormal = GetActorTransform().TransformVectorNoScale(
        Dominant->ContactNormalLocal).GetSafeNormal();
    if (OutWorldNormal.IsNearlyZero())
    {
        OutWorldNormal = FVector::UpVector;
    }
    return true;
}

void ARaftSimRaftActor::BuildRaftVisual()
{
    if (RaftVisual == nullptr)
    {
        return;
    }
    // Constructor component transforms are based on CDO defaults. Re-resolve
    // the presentation origin from the live instance radius so an authored
    // override cannot silently move the visible tube centres away from the
    // rigid support points.
    RaftVisual->SetRelativeLocation(
        FVector(0.0f, 0.0f, -TubeRadiusM * kCmPerM));
    const TArray<FLinearColor> NoColors;
    ProductionRaftRestSections.Reset();
    ++CrewSupportGeometryRevision;
    ProductionRaftDeformedSections.Reset();
    ProductionRaftDeformationCache.Reset();
    LastRenderedFlexVisualSegments.Reset();
    bHasRenderedFlexibleRaftState = false;
    bUsingProductionRaftRestMesh = false;
    if (UStaticMesh* ProductionMesh = LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft."
                 "SM_RaftSim_ProductionPaddleRaft")))
    {
        TArray<RaftSimRaftMesh::FMeshData> ImportedRestSections;
        bUsingProductionRaftRestMesh =
            RaftSimRaftMesh::ExtractProductionRaftRestMesh(
                ProductionMesh, ImportedRestSections);
        if(bUsingProductionRaftRestMesh)
            ProductionRaftRestSections=MakeShared<const RaftSimRaftMesh::FImmutableProductionRestMesh>(ImportedRestSections);
    }

    TArray<RaftSimRaftMesh::FMeshData> FallbackSections;
    TArray<RaftSimRaftMesh::FMeshData>* Sections = &FallbackSections;
    if (bUsingProductionRaftRestMesh)
    {
        RaftSimRaftMesh::DeformProductionRaftRestMesh(
            ProductionRaftRestSections->GetSections(),
            TubeRadiusM,
            {},
            RaftSimRaftMesh::FRaftSimRaftVisualCondition{
                RaftCondition.PressureFraction,
                RaftCondition.FabricIntegrity,
                RaftCondition.PermanentCreaseAmplitudeM},
            ProductionRaftDeformedSections,
            &ProductionRaftDeformationCache);
        Sections = &ProductionRaftDeformedSections;
    }
    else
    {
        FallbackSections.SetNum(5);
        RaftSimRaftMesh::BuildInflatableRaft(
            FootprintLengthM, FootprintWidthM, TubeRadiusM,
            FallbackSections[0], FallbackSections[1], {},
            RaftSimRaftMesh::FRaftSimRaftVisualCondition{
                RaftCondition.PressureFraction,
                RaftCondition.FabricIntegrity,
                RaftCondition.PermanentCreaseAmplitudeM},
            &FallbackSections[2], &FallbackSections[3], &FallbackSections[4]);
    }
    for (int32 SectionIndex = 0; SectionIndex < Sections->Num(); ++SectionIndex)
    {
        const RaftSimRaftMesh::FMeshData& Section = (*Sections)[SectionIndex];
        RaftVisual->CreateMeshSection_LinearColor(
            SectionIndex,
            Section.Vertices,
            Section.Triangles,
            Section.Normals,
            Section.UVs,
            NoColors,
            Section.Tangents,
            /*bCreateCollision=*/false);
    }
    UMaterialInterface* TubeMat = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftTube.M_RaftSim_RaftTube"));
    if (TubeMat)
    {
        TubeMaterialInstance = UMaterialInstanceDynamic::Create(TubeMat, this);
        RaftVisual->SetMaterial(0, TubeMaterialInstance ? TubeMaterialInstance : TubeMat);
    }
    if (UMaterialInterface* FloorMat = LoadObject<UMaterialInterface>(
            nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftFloor.M_RaftSim_RaftFloor")))
    {
        // The former near-black floor became indistinguishable from opaque
        // water whenever the self-bailer sat below the waterline. Use the same
        // weathered rescue-orange coated fabric as the chambers, but retain a
        // separate instance and denser textile scale for the inflated floor.
        // The original floor material remains a fallback if the production
        // tube material is unavailable.
        UMaterialInterface* ReadableFloorMaterial = LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftFloorReadable."
                 "M_RaftSim_RaftFloorReadable"));
        UMaterialInterface* FloorPresentationMaterial = ReadableFloorMaterial
            ? ReadableFloorMaterial
            : (TubeMat ? TubeMat : FloorMat);
        FloorMaterialInstance = UMaterialInstanceDynamic::Create(
            FloorPresentationMaterial, this);
        if (FloorMaterialInstance)
        {
            FloorMaterialInstance->SetScalarParameterValue(
                TEXT("TextileTiling"), 7.5f);
            FloorMaterialInstance->SetScalarParameterValue(
                TEXT("TextileNormalStrength"), 0.42f);
            FloorMaterialInstance->SetScalarParameterValue(
                TEXT("FloorShadowFill"), 0.28f);
        }
        RaftVisual->SetMaterial(
            1,
            FloorMaterialInstance ? FloorMaterialInstance : FloorPresentationMaterial);
    }
    if (UMaterialInterface* RiggingMat = LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftRigging.M_RaftSim_RaftRigging")))
    {
        RaftVisual->SetMaterial(2, RiggingMat);
    }
    if (UMaterialInterface* FittingsMat = LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/M_RaftSim_GalvanizedSteel.M_RaftSim_GalvanizedSteel")))
    {
        RaftVisual->SetMaterial(3, FittingsMat);
    }
    if (UMaterialInterface* RubberMat = LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/M_RaftSim_BootRubber.M_RaftSim_BootRubber")))
    {
        RaftVisual->SetMaterial(4, RubberMat);
    }
    {
        // Hull extent for the rigged gear: the production mesh bounds (the
        // visual's local frame), or the fallback footprint.
        FBox HullBounds(ForceInit);
        if (bUsingProductionRaftRestMesh)
        {
            if (const UStaticMesh* ProductionMesh = LoadObject<UStaticMesh>(nullptr,
                    TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft")))
            {
                HullBounds = ProductionMesh->GetBoundingBox();
            }
        }
        if (!HullBounds.IsValid)
        {
            const FVector Half(0.5f * FootprintLengthM * kCmPerM, 0.5f * FootprintWidthM * kCmPerM, TubeRadiusM * kCmPerM);
            HullBounds = FBox(FVector(-Half.X, -Half.Y, 0.0f), FVector(Half.X, Half.Y, 2.0f * Half.Z));
        }
        BuildRaftGear(HullBounds);
        if (IsSoloOarRig())
        {
            if (!OarRig)
            {
                OarRig = NewObject<URaftSimOarRigComponent>(this, TEXT("OarRig"));
                OarRig->RegisterComponent();
            }
            OarRig->Build(ResolvedRaftRig, RaftVisual, HullBounds);
        }
    }
    if (IsSoloOarRig())
    {
        // Grand Canyon oar boats are commonly blue; Zambezi operators' boats
        // yellow (docs/oar-rig-reference.md). Floors match their tubes.
        const FLinearColor Tint = ResolvedRaftRig == ERaftSimRaftRig::ColoradoOarRig
            ? FLinearColor(0.012f, 0.045f, 0.16f)
            : FLinearColor(0.45f, 0.30f, 0.010f);
        if (TubeMaterialInstance)
        {
            TubeMaterialInstance->SetVectorParameterValue(TEXT("BaseTint"), Tint);
        }
        if (FloorMaterialInstance)
        {
            FloorMaterialInstance->SetVectorParameterValue(TEXT("BaseTint"), Tint * 0.8f);
        }
    }
    // The shared hull binds to the physics adapter; seating-only validation
    // (InitializeCrewSeatingForValidation) builds the visual without one.
    if (RaftAdapter != nullptr)
    {
        ConfigureSharedHullGeometryReview();
    }
}

void ARaftSimRaftActor::BuildRaftGear(const FBox& HullBoundsCm)
{
    using RaftSimAccessoryMesh::FAccessoryMesh;
    if (!RaftVisual)
    {
        return;
    }
    if (!RaftGear)
    {
        RaftGear = NewObject<UProceduralMeshComponent>(this, TEXT("RaftGear"));
        RaftGear->SetupAttachment(RaftVisual);
        RaftGear->RegisterComponent();
        RaftGear->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        RaftGear->SetCastShadow(true);
    }
    const float TubeCm = TubeRadiusM * kCmPerM;
    // Everything below is placed in RaftVisual's own frame, on the surfaces
    // it actually renders: the highest vertex of one section in a column.
    auto SurfaceTopZ = [this](int32 SectionIndex, float X, float Y, float HalfX, float HalfY, float Fallback)
    {
        const FProcMeshSection* Section = RaftVisual->GetProcMeshSection(SectionIndex);
        if (!Section)
        {
            return Fallback;
        }
        float Top = -BIG_NUMBER;
        for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
        {
            if (FMath::Abs(Vertex.Position.X - X) <= HalfX && FMath::Abs(Vertex.Position.Y - Y) <= HalfY)
            {
                Top = FMath::Max(Top, float(Vertex.Position.Z));
            }
        }
        return Top > -BIG_NUMBER ? Top : Fallback;
    };
    // Sections 0-2 are the stowed throw bag (hidden together while it is out
    // on the water); section 3 is the bow line.
    FAccessoryMesh Bag, BagTrim, BagRope, BowLine;

    // The guide's throw bag, after the common rescue bag (NRS Standard Rescue:
    // red Cordura, internal foam flotation, a mesh drain panel at the bottom,
    // a flared nylon top cinched by a barrel-lock drawstring, 75 ft of 3/8"
    // yellow floating line whose end comes out of the top on a figure-eight
    // loop). It stands on the floor beside the guide's hip, inboard of the
    // seat and aft of the feet, where the guide can reach it without moving
    // ("put it on the boat floor next to the guide", 2026-10-07).
    const float GuideSide = CVarRaftSimGuideLeftHanded.GetValueOnGameThread() != 0 ? -1.0f : 1.0f;
    const FTransform VisualToActor = RaftVisual->GetRelativeTransform();
    const FVector GuideSeat = VisualToActor.InverseTransformPosition(RaftSimCrewSeatLayout::AnchorCm(0, true, GuideSide < 0.0f));
    const FVector BagXY(GuideSeat.X + 5.0f, GuideSeat.Y - GuideSide * 36.0f, 0.0f);
    const FVector BagBase(BagXY.X, BagXY.Y,
        SurfaceTopZ(1, BagXY.X, BagXY.Y, 7.0f, 7.0f, HullBoundsCm.Min.Z + 0.4f * TubeCm) - 0.5f);
    const FVector Up = FVector::UpVector;
    // The rope end drapes over the rim toward the crew, where it shows.
    const FVector Drape = FVector(0.5f, -GuideSide * 0.85f, 0.0f).GetSafeNormal();
    const FVector Across = FVector::CrossProduct(Up, Drape);
    auto OnBag = [&](float Height, float Radius, const FVector& Direction)
    {
        return BagBase + Up * Height + Direction * Radius;
    };
    // Body: rope-packed and slightly barrel-sided, gathered at the neck.
    Bag.Lathe(BagBase, Up, {{0.0f, 0.0f}, {0.2f, 4.5f}, {0.6f, 6.3f}, {1.4f, 6.9f}, {4.0f, 7.0f}, {10.0f, 7.15f},
        {16.0f, 7.2f}, {22.0f, 7.05f}, {25.0f, 6.8f}, {26.6f, 5.8f}, {27.6f, 4.4f}}, 20);
    // Black mesh drain panel round the foot of the bag.
    BagTrim.Lathe(BagBase, Up, {{1.5f, 7.0f}, {1.9f, 7.15f}, {6.8f, 7.22f}, {7.2f, 7.05f}}, 20);
    // Flared nylon top, its inner wall turning back down into the bag.
    BagTrim.Lathe(BagBase, Up, {{27.2f, 4.6f}, {28.2f, 4.4f}, {29.6f, 5.0f}, {31.0f, 6.0f}, {32.0f, 6.6f},
        {32.4f, 6.55f}, {31.8f, 6.1f}, {30.6f, 4.9f}, {29.8f, 4.2f}}, 20);
    // Drawstring round the gathered neck and down to its barrel lock.
    {
        TArray<FVector> Neck;
        for (int32 Index = 0; Index < 18; ++Index)
        {
            const float Angle = UE_TWO_PI * Index / 18.0f;
            const FVector Out = Drape * FMath::Cos(Angle) + Across * FMath::Sin(Angle);
            Neck.Add(OnBag(27.5f + 0.15f * FMath::Sin(3.0f * Angle), 4.75f, Out));
        }
        BagTrim.Sweep(Neck, 0.28f, 5, true);
        const FVector LockSide = (Drape * 0.35f + Across).GetSafeNormal();
        for (const float Offset : {-0.45f, 0.45f})
        {
            const FVector Start = (LockSide + Drape * 0.1f * Offset).GetSafeNormal();
            BagTrim.Sweep({OnBag(27.5f, 4.9f, Start), OnBag(26.6f, 6.3f, LockSide),
                OnBag(25.4f, 7.55f, LockSide) + FVector::CrossProduct(Up, LockSide) * Offset},
                0.26f, 5);
            BagTrim.Sweep({OnBag(23.2f, 7.65f, LockSide) + FVector::CrossProduct(Up, LockSide) * Offset,
                OnBag(21.4f, 7.6f, LockSide) + FVector::CrossProduct(Up, LockSide) * (Offset * 1.6f)}, 0.26f, 5);
        }
        BagTrim.Lathe(OnBag(23.1f, 7.85f, LockSide), Up,
            {{0.0f, 0.0f}, {0.15f, 0.62f}, {0.5f, 0.78f}, {1.9f, 0.78f}, {2.25f, 0.62f}, {2.4f, 0.0f}}, 10);
    }
    // Sewn webbing grab handle near the foot, on the side away from the crew.
    {
        const FVector Out = -Drape;
        TArray<FVector> Strap;
        for (int32 Index = 0; Index <= 8; ++Index)
        {
            const float T = float(Index) / 8.0f;
            Strap.Add(OnBag(FMath::Lerp(2.5f, 11.0f, T), 7.25f + 1.6f * FMath::Sin(PI * T), Out));
        }
        for (int32 Index = 0; Index + 1 < Strap.Num(); ++Index)
        {
            const FVector Along = Strap[Index + 1] - Strap[Index];
            BagTrim.Box((Strap[Index] + Strap[Index + 1]) * 0.5f, Along, FVector::CrossProduct(Along, Out), Out,
                FVector(0.5f * float(Along.Size()) + 0.05f, 1.25f, 0.13f));
        }
    }
    // The rope end: out of the top, a figure-eight knot, and its loop laid
    // over the rim and down the side.
    {
        const float RopeR = 0.5f;
        BagRope.Sweep({OnBag(29.5f, 0.6f, Across), OnBag(32.0f, 0.4f, Across), OnBag(33.6f, 0.2f, Drape)}, RopeR, 6);
        BagRope.Lathe(OnBag(33.3f, 0.3f, Drape), (Up + Drape * 0.35f).GetSafeNormal(),
            {{0.0f, 0.0f}, {0.3f, 1.0f}, {1.2f, 1.35f}, {2.2f, 1.25f}, {2.9f, 0.8f}, {3.2f, 0.0f}}, 10);
        // (radius, height) along the loop's centre: off the knot, over the
        // rim, and hanging down the side against the bag.
        const TArray<FVector2f> Centre = {{0.6f, 36.0f}, {3.5f, 36.0f}, {6.0f, 34.6f}, {7.1f, 32.6f},
            {7.2f, 29.6f}, {7.35f, 26.6f}, {7.55f, 24.6f}};
        TArray<FVector> Eye, Back;
        constexpr int32 Steps = 22;
        for (int32 Step = 0; Step <= Steps; ++Step)
        {
            const float U = float(Step) / Steps * (Centre.Num() - 1);
            const int32 I = FMath::Min(int32(U), Centre.Num() - 2);
            const float F = U - I;
            const FVector2f P0 = Centre[FMath::Max(I - 1, 0)], P1 = Centre[I], P2 = Centre[I + 1],
                P3 = Centre[FMath::Min(I + 2, Centre.Num() - 1)];
            const FVector2f P = 0.5f * ((2.0f * P1) + (P2 - P0) * F + (2.0f * P0 - 5.0f * P1 + 4.0f * P2 - P3) * F * F +
                (3.0f * P1 - P0 - 3.0f * P2 + P3) * F * F * F);
            const float T = float(Step) / Steps;
            const float Half = 2.6f * FMath::Sqrt(FMath::Max(0.0f, 1.0f - FMath::Square(2.0f * T - 1.0f))) + 0.3f * (1.0f - T);
            const FVector Point = OnBag(P.Y, P.X, Drape);
            Eye.Add(Point + Across * Half);
            Back.Insert(Point - Across * Half, 0);
        }
        Eye.Append(Back);
        BagRope.Sweep(Eye, RopeR, 6, true);
    }

    // Bow line, tied off neatly: the standing end made fast round the bow
    // grab line with a round turn and two half hitches, the rest flaked into
    // a coil, collapsed into a hank, wrapped and laid along the top of the bow
    // tube between the carry handles — nothing loose to snag a swimmer.
    {
        float CrestX = HullBoundsCm.Max.X - TubeCm, CrestZ = HullBoundsCm.Max.Z, FrontX = HullBoundsCm.Max.X - 1.0f;
        if (const FProcMeshSection* Tube = RaftVisual->GetProcMeshSection(0))
        {
            float BestZ = -BIG_NUMBER, BestFront = -BIG_NUMBER;
            for (const FProcMeshVertex& Vertex : Tube->ProcVertexBuffer)
            {
                if (Vertex.Position.X < 0.0f || FMath::Abs(Vertex.Position.Y) > 4.0f)
                {
                    continue;
                }
                if (Vertex.Position.Z > BestZ)
                {
                    BestZ = float(Vertex.Position.Z);
                    CrestX = float(Vertex.Position.X);
                }
                BestFront = FMath::Max(BestFront, float(Vertex.Position.X));
            }
            if (BestZ > -BIG_NUMBER)
            {
                CrestZ = BestZ;
                FrontX = BestFront;
            }
        }
        const float BowR = FMath::Max(FrontX - CrestX, 10.0f);
        const FVector BowCentre(CrestX, 0.0f, CrestZ - BowR);
        // The grab line rounds the bow outboard of the skin and a little above
        // the tube's equator; find it among the rigging if it is there.
        FVector Grab = BowCentre + FVector(BowR + 1.5f, 0.0f, 5.8f);
        if (const FProcMeshSection* Rigging = RaftVisual->GetProcMeshSection(2))
        {
            FVector Sum = FVector::ZeroVector;
            int32 Count = 0;
            for (const FProcMeshVertex& Vertex : Rigging->ProcVertexBuffer)
            {
                if (FMath::Abs(Vertex.Position.Y) < 2.5f && Vertex.Position.X > CrestX + 0.6f * BowR)
                {
                    Sum += FVector(Vertex.Position);
                    ++Count;
                }
            }
            if (Count > 0)
            {
                Grab = Sum / Count;
            }
        }
        constexpr float LineR = 0.62f; // 1/2" line
        // A point on the bow tube's skin, Angle degrees forward of its crest.
        auto OnBow = [&](float Angle, float Y, float Lift)
        {
            const float Radians = FMath::DegreesToRadians(Angle);
            return BowCentre + FVector((BowR + Lift) * FMath::Sin(Radians), Y, (BowR + Lift) * FMath::Cos(Radians));
        };
        // The hank: loops collapsed side by side, each a long stadium, their
        // planes fanned round the hank's axis so the strands pack in a bundle.
        const FVector HankCentre = OnBow(-4.0f, 0.0f, 3.0f);
        constexpr int32 Loops = 7;
        constexpr float HankHalfLength = 17.0f;
        const float WrapCentreY = 9.0f, WrapHalfWidth = 2.6f;
        auto Pinch = [&](float Y)
        {
            return 1.0f - 0.5f * FMath::SmoothStep(0.0f, 1.0f, 1.0f - FMath::Clamp((FMath::Abs(Y - WrapCentreY) - WrapHalfWidth) / 4.0f, 0.0f, 1.0f));
        };
        for (int32 Loop = 0; Loop < Loops; ++Loop)
        {
            const float Fan = PI * (Loop + 0.5f) / Loops;
            const FVector Spread = FVector(FMath::Cos(Fan), 0.0f, FMath::Sin(Fan));
            const float Width = (Loop % 2 ? 1.55f : 2.25f);
            const float Length = HankHalfLength + 0.7f * FMath::Sin(2.3f * Loop);
            TArray<FVector> Points;
            for (int32 Step = 0; Step < 36; ++Step)
            {
                const float T = UE_TWO_PI * Step / 36.0f;
                const float C = FMath::Cos(T), S = FMath::Sin(T);
                const float Y = Length * FMath::Sign(C) * FMath::Pow(FMath::Abs(C), 0.35f);
                Points.Add(HankCentre + FVector(0.0f, Y, 0.0f) + Spread * (Width * S * Pinch(Y)));
            }
            BowLine.Sweep(Points, LineR, 6, true);
        }
        // Five tight wraps round the hank, the tail tucked back through.
        {
            TArray<FVector> Wraps;
            const float WrapR = 2.25f * 0.5f + 2.0f * LineR;
            constexpr int32 Turns = 5;
            for (int32 Step = 0; Step <= Turns * 12; ++Step)
            {
                const float T = float(Step) / (Turns * 12);
                const float Angle = UE_TWO_PI * Turns * T;
                Wraps.Add(HankCentre + FVector(WrapR * FMath::Cos(Angle), WrapCentreY - WrapHalfWidth + 2.0f * WrapHalfWidth * T,
                    WrapR * FMath::Sin(Angle)));
            }
            Wraps.Add(HankCentre + FVector(0.0f, WrapCentreY + WrapHalfWidth + 2.5f, 0.4f));
            Wraps.Add(HankCentre + FVector(-0.6f, HankHalfLength - 2.5f, 0.2f));
            BowLine.Sweep(Wraps, LineR, 6);
        }
        // Standing part: off the hank's near end, forward over the bow and
        // down its face to the grab line.
        const float KnotY = -3.0f;
        const float GrabAngle = FMath::RadiansToDegrees(FMath::Atan2(Grab.X - BowCentre.X, Grab.Z - BowCentre.Z));
        TArray<FVector> Standing = {HankCentre + FVector(0.8f, -HankHalfLength + 1.0f, -0.6f),
            HankCentre + FVector(3.0f, -HankHalfLength - 1.5f, -1.4f)};
        for (int32 Step = 1; Step <= 8; ++Step)
        {
            const float T = float(Step) / 8.0f;
            Standing.Add(OnBow(FMath::Lerp(10.0f, GrabAngle - 6.0f, T),
                FMath::Lerp(-HankHalfLength - 2.0f, KnotY - 1.0f, FMath::Min(T / 0.6f, 1.0f)), LineR + 0.1f));
        }
        Standing.Add(Grab + FVector(0.0f, KnotY - 1.0f, 1.2f + 2.0f * LineR));
        BowLine.Sweep(Standing, LineR, 6);
        // Round turn on the grab line (which runs athwartships at the bow).
        {
            TArray<FVector> Turn;
            const float TurnR = 1.2f + LineR;
            for (int32 Step = 0; Step <= 24; ++Step)
            {
                const float T = float(Step) / 24.0f;
                const float Angle = PI * 0.5f + UE_TWO_PI * 2.0f * T;
                Turn.Add(Grab + FVector(TurnR * FMath::Cos(Angle), KnotY - 0.8f + 2.6f * T, TurnR * FMath::Sin(Angle)));
            }
            // Out of the turn and up beside the standing part into the hitches.
            Turn.Add(Grab + FVector(-0.4f, KnotY + 2.4f, 3.4f));
            Turn.Add(OnBow(GrabAngle - 7.0f, KnotY + 0.4f, LineR + 0.9f));
            BowLine.Sweep(Turn, LineR, 6);
        }
        // Two half hitches round the standing part, snugged up to the turn.
        for (int32 Hitch = 0; Hitch < 2; ++Hitch)
        {
            const float Angle = GrabAngle - 10.0f - 3.5f * Hitch;
            const FVector Centre = OnBow(Angle, KnotY - 1.0f, LineR + 0.1f);
            const float Radians = FMath::DegreesToRadians(Angle);
            const FVector Axis(FMath::Cos(Radians), 0.0f, -FMath::Sin(Radians));
            const FVector U = FVector::CrossProduct(Axis, FVector::RightVector).GetSafeNormal();
            const FVector V = FVector::CrossProduct(Axis, U);
            TArray<FVector> Ring;
            for (int32 Step = 0; Step < 12; ++Step)
            {
                const float Turn = UE_TWO_PI * Step / 12.0f;
                Ring.Add(Centre + (U * FMath::Cos(Turn) + V * FMath::Sin(Turn)) * (2.0f * LineR + 0.15f) +
                    Axis * (0.5f * LineR * FMath::Sin(Turn)));
            }
            BowLine.Sweep(Ring, LineR, 6, true);
        }
    }
    Bag.Commit(RaftGear, 0);
    BagTrim.Commit(RaftGear, 1);
    BagRope.Commit(RaftGear, 2);
    BowLine.Commit(RaftGear, 3);
    auto Tinted = [this](const TCHAR* Path, const FLinearColor& Tint) -> UMaterialInterface*
    {
        UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, Path);
        if (!Base)
        {
            return nullptr;
        }
        UMaterialInstanceDynamic* Instance = UMaterialInstanceDynamic::Create(Base, this);
        Instance->SetVectorParameterValue(TEXT("BaseTint"), Tint);
        return Instance;
    };
    // Rescue-red bag with black trim and yellow floating throw line; a blue
    // bow line so it reads apart from the yellow perimeter line.
    RaftGear->SetMaterial(0, Tinted(TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"),
        FLinearColor(0.30f, 0.010f, 0.006f)));
    RaftGear->SetMaterial(1, LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing")));
    RaftGear->SetMaterial(2, Tinted(TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftRigging.M_RaftSim_RaftRigging"),
        FLinearColor(0.45f, 0.30f, 0.010f)));
    RaftGear->SetMaterial(3, Tinted(TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftRigging.M_RaftSim_RaftRigging"),
        FLinearColor(0.015f, 0.05f, 0.20f)));
}

bool ARaftSimRaftActor::GetRenderedFloorCenterWorldZCm(float& OutWorldZCm) const
{
    OutWorldZCm = 0.0f;
    if (RaftVisual == nullptr)
    {
        return false;
    }
    // Material section one is the inflated self-bailing floor in both the
    // production asset contract and the procedural fallback. Restrict the
    // sample to the centre so raised perimeter seams cannot hide a wet deck.
    const FProcMeshSection* FloorSection = RaftVisual->GetProcMeshSection(1);
    if (FloorSection == nullptr)
    {
        return false;
    }
    constexpr float CenterHalfExtentCm = 30.0f;
    bool bFound = false;
    const FTransform LocalToWorld = RaftVisual->GetComponentTransform();
    for (const FProcMeshVertex& Vertex : FloorSection->ProcVertexBuffer)
    {
        const FVector LocalCm(Vertex.Position);
        if (FMath::Abs(LocalCm.X) > CenterHalfExtentCm ||
            FMath::Abs(LocalCm.Y) > CenterHalfExtentCm)
        {
            continue;
        }
        const float WorldZCm =
            static_cast<float>(LocalToWorld.TransformPosition(LocalCm).Z);
        if (!bFound || WorldZCm > OutWorldZCm)
        {
            OutWorldZCm = WorldZCm;
            bFound = true;
        }
    }
    return bFound;
}

void ARaftSimRaftActor::UpdateFlexibleRaftVisual()
{
    if(bSharedHullGeometryReview && RaftVisual && RaftAdapter)
    {
        UpdateSharedHullVisual();
        return;
    }
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_UpdateFlexibleRaftVisual);
    if (RaftVisual == nullptr || RaftAdapter == nullptr)
    {
        return;
    }

    const TArray<FRaftSimFlexVisualSegmentState>& CurrentSegments =
        RaftAdapter->GetFlexibleVisualSegments();
    const RaftSimRaftMesh::FRaftSimRaftVisualCondition CurrentCondition{
        RaftCondition.PressureFraction,
        RaftCondition.FabricIntegrity,
        RaftCondition.PermanentCreaseAmplitudeM};
    constexpr float ConditionTolerance = 1.0e-6f;
    const float CurrentEffectiveCreaseM = CurrentCondition.CreaseAmplitudeM *
        (1.0f - CurrentCondition.Integrity);
    const float LastEffectiveCreaseM = LastRenderedRaftVisualCondition.CreaseAmplitudeM *
        (1.0f - LastRenderedRaftVisualCondition.Integrity);
    const bool bConditionMatches = bHasRenderedFlexibleRaftState &&
        FMath::IsNearlyEqual(
            CurrentCondition.PressureFraction,
            LastRenderedRaftVisualCondition.PressureFraction,
            ConditionTolerance) &&
        FMath::IsNearlyEqual(
            CurrentEffectiveCreaseM,
            LastEffectiveCreaseM,
            ConditionTolerance);
    if (bConditionMatches &&
        FlexVisualStateMatches(CurrentSegments, LastRenderedFlexVisualSegments))
    {
        return;
    }

    TArray<RaftSimRaftMesh::FMeshData> FallbackSections;
    TArray<RaftSimRaftMesh::FMeshData>* Sections = &FallbackSections;
    if (bUsingProductionRaftRestMesh)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_DeformProductionRaftMesh);
        RaftSimRaftMesh::DeformProductionRaftRestMesh(
            ProductionRaftRestSections->GetSections(),
            TubeRadiusM,
            CurrentSegments,
            CurrentCondition,
            ProductionRaftDeformedSections,
            &ProductionRaftDeformationCache);
        Sections = &ProductionRaftDeformedSections;
    }
    else
    {
        FallbackSections.SetNum(5);
        RaftSimRaftMesh::BuildInflatableRaft(
            FootprintLengthM,
            FootprintWidthM,
            TubeRadiusM,
            FallbackSections[0],
            FallbackSections[1],
            CurrentSegments,
            CurrentCondition,
            &FallbackSections[2],
            &FallbackSections[3],
            &FallbackSections[4]);
    }
    const TArray<FLinearColor> NoColors;
    const TArray<FVector2D> NoUVs;
    ++CrewSupportGeometryRevision;
    for (int32 SectionIndex = 0; SectionIndex < Sections->Num(); ++SectionIndex)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_UploadProceduralMeshSection);
        const RaftSimRaftMesh::FMeshData& Section = (*Sections)[SectionIndex];
        RaftVisual->UpdateMeshSection_LinearColor(
            SectionIndex,
            Section.Vertices,
            Section.Normals,
            NoUVs,
            NoColors,
            Section.Tangents);
    }
    LastRenderedFlexVisualSegments = CurrentSegments;
    LastRenderedRaftVisualCondition = CurrentCondition;
    bHasRenderedFlexibleRaftState = true;
}

void ARaftSimRaftActor::UpdateRaftWetness(float DeltaSeconds)
{
    float TargetWetness = 0.0f;
    if (Bridge != nullptr)
    {
        if (URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
        {
            FRaftSimWaterSample Sample;
            if (Water->SampleWaterAtWorldPosition(GetActorLocation(), Sample) && Sample.bWet)
            {
                const float RelativeWaterSpeed =
                    (Sample.VelocityMetersPerSecond - GetRaftVelocity()).Size();
                const float ContactSaturation = FMath::Clamp(
                    static_cast<float>(GetActiveWaterContactCount()) / 5.0f +
                        GetMaximumWaterContactIndentationM() / 0.22f,
                    0.0f,
                    1.0f);
                TargetWetness = FMath::Clamp(
                    0.42f + Sample.DepthMeters * 0.18f + RelativeWaterSpeed / 7.5f +
                        ContactSaturation * 0.36f,
                    0.0f,
                    1.0f);
            }
        }
    }

    const float InterpSpeed = TargetWetness > SurfaceWetness ? 7.5f : 0.085f;
    SurfaceWetness = FMath::FInterpTo(
        SurfaceWetness,
        TargetWetness,
        FMath::Clamp(DeltaSeconds, 0.0f, 0.25f),
        InterpSpeed);
    // SurfaceWetness remains the full physical/telemetry signal. The reusable
    // coated-fabric material's saturated endpoint is intentionally extreme
    // for drenched gear close-ups; driving it to one across an entire raft
    // turned the tubes into clear-coated plastic under the hero sun. Preserve
    // visible darkening and highlight breakup through a bounded presentation
    // response while leaving contact, drying and gameplay state unchanged.
    // Keep the full solver wetness for physics and telemetry, but compress the
    // visual film response so coated fabric retains its authored weave and
    // broad micro-roughness instead of reading as uniformly lacquered.
    const float PresentationWetness = FMath::Clamp(
        SurfaceWetness * 0.42f, 0.0f, 0.50f);
    if (TubeMaterialInstance)
    {
        TubeMaterialInstance->SetScalarParameterValue(
            TEXT("Wetness"), PresentationWetness);
    }
    if (FloorMaterialInstance)
    {
        FloorMaterialInstance->SetScalarParameterValue(
            TEXT("Wetness"), PresentationWetness);
    }
}

void ARaftSimRaftActor::UpdateRockObstacles()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_UpdateRockObstacles);
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
        // Vertical broad-phase: D4 contacts are planar (a rock is an infinite
        // vertical cylinder), so a rock whose rendered crest lies well below
        // the tubes pinned the raft on nothing visible (Lava Canyon crests sit
        // about 1 m under the surface). Skip rocks whose top is more than
        // 25 cm below the tube bottom; rocks without rendered bounds keep
        // their contact. The D4 contact model itself is unchanged.
        const FBox RockBounds = Rock->GetComponentsBoundingBox(true);
        if (RockBounds.IsValid &&
            RockBounds.Max.Z < GetActorLocation().Z - (TubeRadiusM + 0.25f) * kCmPerM)
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
        // Seat side follows handedness so the stroke, T-grip hand, and
        // blade all land on the dominant side the guide actually sits.
        const bool bGuideLeftHanded =
            CVarRaftSimGuideLeftHanded.GetValueOnGameThread() != 0;
        Guide->ConfigureAppearance(0, bGuideLeftHanded ? -1 : 1, true);
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
    Avatar->InitializeAvatarVisual();
    Avatar->ResetHighSideTransfer();
    Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
    if (PassengerId == TEXT("guide") && IsSoloOarRig() && OarRig && OarRig->IsBuilt())
    {
        // The rower sits on the frame's seat pad, facing the bow, its
        // lowest seated contact on the pad.
        float PelvisBottomZ = Avatar->GetSeatedPelvisBottomLocalZCm();
        const TArray<FVector> Contacts = Avatar->GetSeatedContactPointsLocalCm();
        if (!Contacts.IsEmpty())
        {
            PelvisBottomZ = TNumericLimits<float>::Max();
            for (const FVector& Contact : Contacts)
            {
                PelvisBottomZ = FMath::Min(PelvisBottomZ, static_cast<float>(Contact.Z));
            }
        }
        const FVector SeatCm = OarRig->GetRowerSeatOriginActorCm(PelvisBottomZ);
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim seat: id=guide oar_rig=%d pelvis_bottom=%.1f seat=(%.1f, %.1f, %.1f)"),
            static_cast<int32>(ResolvedRaftRig), PelvisBottomZ, SeatCm.X, SeatCm.Y, SeatCm.Z);
        Avatar->AttachToComponent(Root, FAttachmentTransformRules::KeepWorldTransform);
        Avatar->SetActorRelativeLocation(SeatCm);
        Avatar->SetActorRelativeRotation(FRotator::ZeroRotator);
        // The rig poses the rower each frame; the avatar applies it after.
        Avatar->AddTickPrerequisiteActor(this);
        OarRig->PoseForValidation(0.0f, 0.0f, 0.0f, Avatar);
        return;
    }
    // Both the raft component's offset and the posed body's underside
    // matter. Seat the visible mesh on the rendered tube, not the old
    // placeholder pelvis or a fixed actor-height guess.
    // The guide and passengers share horizontal anchors with physical loads.
    const bool bLeftHandedGuide = CVarRaftSimGuideLeftHanded.GetValueOnGameThread() != 0;
    // Sit forward of the raised stern tip so the guide's unchanged leg
    // lengths can reach the real interior floor, not hover above a tube.
    FVector SeatCm = RaftSimCrewSeatLayout::AnchorCm(0, true, bLeftHandedGuide);
    if (PassengerId != TEXT("guide"))
    {
        FString Id = PassengerId.ToString();
        Id.RemoveFromStart(TEXT("paddler_"));
        const int32 Index = FMath::Max(FCString::Atoi(*Id) - 1, 0);
        SeatCm = RaftSimCrewSeatLayout::AnchorCm(Index, false, bLeftHandedGuide);
    }
    bool bTubeFound = false;
    const float TubeTopZCm = ComputeSeatTubeTopZCm(SeatCm, bTubeFound);
    float RenderedSeatZCm = 0.0f;
    const bool bRenderedContact = ComputeRenderedSeatOriginZCm(
        SeatCm, Avatar->GetSeatedContactPointsLocalCm(), RenderedSeatZCm);
    if (bRenderedContact)
    {
        // Fit the actual posed glute to the triangle directly beneath it,
        // then let both give: a seated person's buttocks and an inflated
        // tube flatten into each other. One centimetre left a round seat
        // touching a round tube along a line, daylight down both sides ("the
        // crew butts are not sitting fully on the boat", 2026-10-07); 3.5 cm
        // gives a contact patch about 25 cm wide.
        SeatCm.Z = RenderedSeatZCm - RenderedSeatContactCompressionCm;
    }
    else if (bTubeFound)
    {
        // Preserve the legacy placement for adapters without contact
        // samples. The production CC0 path above does not use this guess.
        constexpr float SeatContactSinkCm = 4.0f;
        SeatCm.Z = TubeTopZCm - Avatar->GetSeatedPelvisBottomLocalZCm() -
            SeatContactSinkCm;
    }
    // Probe the interior floor where this paddler's feet should plant
    // (inboard of the tube, forward of the seat) with the same scanner the
    // seat uses. The pose library's leg targets are calibrated against this
    // measured value; the log keeps the calibration honest when the raft
    // mesh changes.
    FVector FootProbeCm = SeatCm;
    FootProbeCm.X += 27.0f;
    FootProbeCm.Y -= FMath::Sign(SeatCm.Y) * 32.0f;
    bool bFloorFound = false;
    const float FloorTopZCm = ComputeSeatTubeTopZCm(FootProbeCm, bFloorFound);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim seat: id=%s measured=%d rendered_contact=%d tube_top=%.1f seat_z=%.1f "
             "floor_found=%d floor_top=%.1f foot_local_z=%.1f"),
        *PassengerId.ToString(), bTubeFound ? 1 : 0, bRenderedContact ? 1 : 0, TubeTopZCm, SeatCm.Z,
        bFloorFound ? 1 : 0, FloorTopZCm, FloorTopZCm - SeatCm.Z);
    Avatar->AttachToComponent(Root, FAttachmentTransformRules::KeepWorldTransform);
    Avatar->SetActorRelativeLocation(SeatCm);
    Avatar->SetActorRelativeRotation(FRotator::ZeroRotator);
    Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
    // Foot fitting moves thigh-weighted glute vertices. Reconcile the actual
    // body contact without changing the seat compression.
    if (bRenderedContact)
    {
        for (int32 Iteration = 0; Iteration < 8; ++Iteration)
        {
            const float Clearance = GetCrewSeatContactClearanceCm(Avatar);
            if (!FMath::IsFinite(Clearance) || FMath::Abs(Clearance) > 10.0f ||
                FMath::Abs(Clearance + RenderedSeatContactCompressionCm) < 0.01f) break;
            SeatCm.Z += -RenderedSeatContactCompressionCm - Clearance;
            Avatar->SetActorRelativeLocation(SeatCm);
            Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
        }
    }
    // Complete seat reconciliation before preparing alternate grounded stances.
    // Preparation never publishes an alternate action or moves rendered parts.
    Avatar->PrepareRenderedFootPlacements();
}

void ARaftSimRaftActor::InitializeCrewSeatingForValidation()
{
    BuildRaftVisual();
    SpawnCrewVisuals();
}

float ARaftSimRaftActor::GetCrewSeatContactClearanceCm(
    ARaftSimCrewAvatarActor* Avatar) const
{
    if (!Avatar)
    {
        return BIG_NUMBER;
    }
    const FVector Seat = GetActorTransform().InverseTransformPosition(Avatar->GetActorLocation());
    float ContactZ = 0.0f;
    return ComputeRenderedSeatOriginZCm(Seat, Avatar->GetSeatedContactPointsLocalCm(), ContactZ)
        ? static_cast<float>(Seat.Z) - ContactZ : BIG_NUMBER;
}

bool ARaftSimRaftActor::ComputeRenderedSeatOriginZCm(
    const FVector& SeatCm, const TArray<FVector>& ContactPoints, float& OutZCm) const
{
    // Section zero is the inflatable tube, excluding rigging and fittings.
    const FProcMeshSection* Tube = RaftVisual ? RaftVisual->GetProcMeshSection(0) : nullptr;
    if (!Tube || ContactPoints.IsEmpty())
    {
        return false;
    }
    bool bFound = false;
    const FTransform ToActor = RaftVisual->GetRelativeTransform();
    for (int32 I = 0; I + 2 < Tube->ProcIndexBuffer.Num(); I += 3)
    {
        const FVector A = ToActor.TransformPosition(FVector(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I]].Position));
        const FVector B = ToActor.TransformPosition(FVector(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I + 1]].Position));
        const FVector C = ToActor.TransformPosition(FVector(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I + 2]].Position));
        if (FMath::Max3(A.X, B.X, C.X) < SeatCm.X - 24.0 ||
            FMath::Min3(A.X, B.X, C.X) > SeatCm.X + 6.0 ||
            FMath::Max3(A.Y, B.Y, C.Y) < SeatCm.Y - 22.0 ||
            FMath::Min3(A.Y, B.Y, C.Y) > SeatCm.Y + 22.0)
        {
            continue;
        }
        const double Denom = (B.Y - C.Y) * (A.X - C.X) + (C.X - B.X) * (A.Y - C.Y);
        if (FMath::Abs(Denom) < 1.e-8)
        {
            continue;
        }
        for (const FVector& P : ContactPoints)
        {
            const double X = SeatCm.X + P.X, Y = SeatCm.Y + P.Y;
            const double U = ((B.Y - C.Y) * (X - C.X) + (C.X - B.X) * (Y - C.Y)) / Denom;
            const double V = ((C.Y - A.Y) * (X - C.X) + (A.X - C.X) * (Y - C.Y)) / Denom;
            const double W = 1.0 - U - V;
            if (U < -1.e-6 || V < -1.e-6 || W < -1.e-6)
            {
                continue;
            }
            const float RequiredZ = static_cast<float>(U * A.Z + V * B.Z + W * C.Z - P.Z);
            OutZCm = bFound ? FMath::Max(OutZCm, RequiredZ) : RequiredZ;
            bFound = true;
        }
    }
    return bFound;
}

float ARaftSimRaftActor::ComputeSeatTubeTopZCm(
    const FVector& SeatCm, bool& bOutFound) const
{
    // The uploaded RaftVisual sections are the surface the player actually
    // sees â€” the production static-mesh extraction and the procedural
    // fallback both land there, and the component carries its own vertical
    // offset relative to the hull frame, so scanning it folds every source
    // of disagreement into one measured number. Highest vertex wins inside
    // a glute-sized column; rigging, D-rings, and thwarts all live outside
    // the seat windows (verified against the builder's layout).
    bOutFound = false;
    float MaxZCm = 0.0f;
    if (RaftVisual == nullptr)
    {
        return MaxZCm;
    }
    constexpr float WindowXCm = 22.0f;
    constexpr float WindowYCm = 16.0f;
    const FTransform VisualToActor = RaftVisual->GetRelativeTransform();
    for (int32 SectionIndex = 0; SectionIndex < RaftVisual->GetNumSections();
         ++SectionIndex)
    {
        const FProcMeshSection* Section =
            RaftVisual->GetProcMeshSection(SectionIndex);
        if (Section == nullptr)
        {
            continue;
        }
        for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
        {
            const FVector ActorCm =
                VisualToActor.TransformPosition(FVector(Vertex.Position));
            if (FMath::Abs(ActorCm.X - SeatCm.X) > WindowXCm ||
                FMath::Abs(ActorCm.Y - SeatCm.Y) > WindowYCm)
            {
                continue;
            }
            if (!bOutFound || ActorCm.Z > MaxZCm)
            {
                MaxZCm = static_cast<float>(ActorCm.Z);
                bOutFound = true;
            }
        }
    }
    return MaxZCm;
}

void ARaftSimRaftActor::IssueCrewCommand(ERaftSimCrewCommand Command)
{
    // Emergency weight transfer takes precedence over holding a rescue rope.
    // Leave the swimmer in the water and allow a fresh cast after returning.
    if (Command == ERaftSimCrewCommand::HighSide && IsGuideRescuing() && BoardingPassenger.IsNone())
    {
        // Drop the rope, finish the pull-in at once and go for the tube.
        FinishAssistedBoarding();
        RescueInteraction = FRaftSimRescueInteractionState{};
        RopeRecoverRemaining = 0.f;
    }
    if (IsSoloOarRig())
    {
        // The same calls control the single rower's real blades, not an invisible crew.
        ActiveCrewCommand = PendingCrewCommand = Command;
        CrewReactionRemaining = 0.f;
        TransientOarSeconds = OarSteerSeconds = 0.f;
        bCrewCommandFromGuidePaddle = false;
        if (Command == ERaftSimCrewCommand::HighSide)
            CrewHighSideDirection = ResolveHighSideDirection();
        RefreshOarCommandIntents();
        return;
    }
    // An explicit call (number keys / command wheel) sets a standing order
    // that never expires; guide-paddle (W/S/A/D) cadence ownership ends
    // here and is re-marked by the caller when the tap owns the crew.
    bCrewCommandFromGuidePaddle = false;
    if (Command == ActiveCrewCommand)
    {
        // Reaffirming the current order cancels a different pending call.
        PendingCrewCommand = Command;
        CrewReactionRemaining = 0.0f;
        if (Command == ERaftSimCrewCommand::HighSide)
        {
            CrewHighSideDirection = ResolveHighSideDirection();
        }
    }
    else if (Command != PendingCrewCommand || CrewReactionRemaining <= 0.0f)
    {
        // Held W/S/A/D refreshes the same command every frame. Only a new
        // pending order starts reaction latency; refreshing it must not
        // postpone crew response forever.
        PendingCrewCommand = Command;
        CrewReactionRemaining = CrewReactionSeconds;
    }
}

int32 ARaftSimRaftActor::ResolveHighSideDirection() const
{
    const FVector Flow = GetActorQuat().UnrotateVector(SampleWaterVelocityMps(GetActorLocation()));
    // The tube about to hit a rock is the one the current is carrying onto
    // it: weight goes there so it cannot ride up the rock while the upstream
    // tube is pulled under. Only a rock abeam and close enough to matter.
    if (const UWorld* World = GetWorld())
    {
        const FVector HullVelocity = GetActorQuat().UnrotateVector(GetRaftVelocity());
        int32 RockSide = 0;
        double ClosestM = DBL_MAX;
        for (TActorIterator<ARaftSimRockObstacleActor> It(World); It; ++It)
        {
            const FVector LocalM = GetActorTransform().InverseTransformPosition(It->GetActorLocation())/kCmPerM;
            const double GapM = FVector(LocalM.X,LocalM.Y,0).Size() - It->GetContactRadiusM() -
                .5*FMath::Max(FootprintWidthM,1.f);
            if (GapM > 1.5 || FMath::Abs(LocalM.Y) < .35*FMath::Abs(LocalM.X) || GapM >= ClosestM) continue;
            // The current (or the hull's own drift) must carry it onto the rock.
            const double Sign = LocalM.Y > 0 ? 1. : -1.;
            if (Flow.Y*Sign < .1 && HullVelocity.Y*Sign < .1) continue;
            ClosestM = GapM;
            RockSide = LocalM.Y > 0 ? 1 : -1;
        }
        if (RockSide != 0) return RockSide;
    }
    // A side-on pin calls for the downstream tube, even before roll develops.
    // With no meaningful cross-current, retain the raised-side response.
    if (FMath::Abs(Flow.Y) > .25 && FMath::Abs(Flow.Y) > .25*Flow.Size2D())
        return Flow.Y > 0 ? 1 : -1;
    return GetActorRotation().Roll >= 0.f ? -1 : 1;
}

float ARaftSimRaftActor::CrewCallStagger(int32 Index) const
{
    if (IsSoloOarRig() || Index == CrewAvatars.Num()-1) return 0.f;
    return .04f + 1.2f*(URaftSimCrewAvatarPoseLibrary::GetDeterministicTimingOffset(Index,false)+.026f);
}

void ARaftSimRaftActor::UpdateCrewTransfer(ARaftSimCrewAvatarActor* Avatar, int32 Index,
    bool bHighSide, float DeltaSeconds, FRaftSimFlexCrewAction& Action)
{
    if (bHighSide && Avatar->GetHighSideTransferDirection() != CrewHighSideDirection)
    {
        FVector Target = GetActorTransform().InverseTransformPosition(Avatar->GetActorLocation());
        // Fixed identities retain their places; missing swimmers leave gaps.
        // Stagger the two original seat rows along the tube, rather than
        // superimposing each opposite-seat pair at the same destination.
        Target.X = IsSoloOarRig() ? -42. : FMath::Lerp(115.,-145.,
            double(Index)/FMath::Max(1,CrewAvatars.Num()-1));
        // Oar-frame rails occupy Y=+/-70cm; land outside them on the tube,
        // not through the frame at the paddle raft's inner-shoulder anchor.
        Target.Y = CrewHighSideDirection * (IsSoloOarRig() ? 82. : 62.);
        float ContactZ = 0.f;
        if (ComputeRenderedSeatOriginZCm(Target,Avatar->GetSeatedContactPointsLocalCm(),ContactZ))
            Target.Z = ContactZ-1.f;
        Avatar->BeginHighSideTransfer(Target,CrewHighSideDirection,CrewCallStagger(Index));
    }
    // "Back to your seats" (or any paddle call) brings them back the same way.
    else if (!bHighSide) Avatar->ReturnFromHighSide(CrewCallStagger(Index));
    Avatar->AdvanceHighSideTransfer(DeltaSeconds);
    Action.bUseCrewTransfer = Avatar->HasHighSideTransfer();
    Action.CrewTransferOffsetM = Avatar->GetHighSideTransferOffsetCm()*.01;
}

void ARaftSimRaftActor::UpdateCrew(float DeltaSeconds)
{
    if (RaftAdapter == nullptr || RaftMode != ERaftSimRaftMode::Upright)
    {
        return;
    }
    if (IsSoloOarRig())
    {
        TransientOarSeconds = FMath::Max(0.f, TransientOarSeconds - DeltaSeconds);
        OarSteerSeconds = FMath::Max(0.f, OarSteerSeconds - DeltaSeconds);
        RefreshOarCommandIntents();
        TArray<FRaftSimFlexCrewAction> Actions;
        ARaftSimCrewAvatarActor* Rower = FindAvatar(TEXT("guide"));
        const bool bHighSide = ActiveCrewCommand == ERaftSimCrewCommand::HighSide;
        if (Rower && Rower->GetAttachParentActor() == this && !IsGuideRescuing())
        {
            Rower->ClearExternalPose();
            const ERaftSimCrewAvatarAction RowerAction = bHighSide
                ? (CrewHighSideDirection < 0 ? ERaftSimCrewAvatarAction::HighSidePort : ERaftSimCrewAvatarAction::HighSideStarboard)
                : (ActiveCrewCommand == ERaftSimCrewCommand::GetDown ? ERaftSimCrewAvatarAction::Brace : ERaftSimCrewAvatarAction::SeatedIdle);
            FRaftSimFlexCrewAction Action;
            Action.SeatId = TEXT("guide");
            if (bHighSide) { Action.HighSideDirection = CrewHighSideDirection; Action.bBrace = true; }
            else if (ActiveCrewCommand == ERaftSimCrewCommand::GetDown) Action.LeanOffset = FVector(0, 0, -.15);
            UpdateCrewTransfer(Rower,0,bHighSide,DeltaSeconds,Action);
            // Rowing costs effort whenever either oar is working.
            UpdateCrewStamina(CrewAvatars.IndexOfByKey(Rower), !ResolveOarCommandIntents().IsNearlyZero() &&
                !bHighSide ? ERaftSimCrewAvatarAction::ForwardStroke : RowerAction, DeltaSeconds);
            Rower->SetAvatarAction(RowerAction);
            if (bHighSide || Action.bUseCrewTransfer || ActiveCrewCommand == ERaftSimCrewCommand::GetDown) Actions.Add(Action);
        }
        RaftAdapter->SetFlexibleCrewActions(Actions);
        return;
    }

    // Crew react to a new command after a short latency.
    if (CrewReactionRemaining > 0.0f)
    {
        CrewReactionRemaining -= DeltaSeconds;
        if (CrewReactionRemaining <= 0.0f)
        {
            const ERaftSimCrewCommand PreviousCommand = ActiveCrewCommand;
            ActiveCrewCommand = PendingCrewCommand;
            if (ActiveCrewCommand != PreviousCommand)
            {
                if (ActiveCrewCommand == ERaftSimCrewCommand::HighSide)
                {
                    CrewHighSideDirection = ResolveHighSideDirection();
                }
                // Start physics and presentation at the same catch. Propulsion
                // advances from this normalized phase only while blades are
                // visibly planted mid-stroke.
                CrewStrokePhase = 0.0f;
                LastCrewStrokeImpulsePhase = -1.0f;
            }
        }
    }

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
        case ERaftSimCrewCommand::TurnRight:
            // Real pivot technique: the side you turn TOWARD back-paddles,
            // the opposite side paddles forward. Resolved per paddler in the
            // avatar loop below; the TurnLeft/TurnRight avatar poses remain
            // the guide's own draw/pry presentation.
            AvatarAction = ERaftSimCrewAvatarAction::ForwardStroke;
            break;
        case ERaftSimCrewCommand::Stop:
            AvatarAction = ERaftSimCrewAvatarAction::BackStroke;
            break;
        case ERaftSimCrewCommand::GetDown:
            AvatarAction = ERaftSimCrewAvatarAction::Brace;
            break;
        case ERaftSimCrewCommand::HighSide:
            AvatarAction = CrewHighSideDirection < 0
                ? ERaftSimCrewAvatarAction::HighSidePort
                : ERaftSimCrewAvatarAction::HighSideStarboard;
            break;
        case ERaftSimCrewCommand::Rest:
        default:
            break;
    }
    if (DirectImpulseDelaySeconds > 0.0f)
    {
        DirectImpulseDelaySeconds -= DeltaSeconds;
        if (DirectImpulseDelaySeconds <= 0.0f && RaftAdapter != nullptr)
        {
            RaftAdapter->AddExternalImpulse(
                PendingDirectLinearImpulseNs, PendingDirectAngularImpulseNms);
            PendingDirectLinearImpulseNs = FVector::ZeroVector;
            PendingDirectAngularImpulseNms = FVector::ZeroVector;
        }
    }
    // A W/S/A/D tap owns the crew for one stroke; expire back to Rest so a
    // single tap reads as a single stroke while holding the key refreshes
    // through the pawn's stroke cooldown. Standing orders (number keys)
    // clear the flag in IssueCrewCommand and never expire.
    if (bCrewCommandFromGuidePaddle)
    {
        GuidePaddleCommandSeconds -= DeltaSeconds;
        if (GuidePaddleCommandSeconds <= 0.0f)
        {
            bCrewCommandFromGuidePaddle = false;
            IssueCrewCommand(ERaftSimCrewCommand::Rest);
        }
    }
    GuideStrokeActionSeconds = FMath::Max(GuideStrokeActionSeconds - DeltaSeconds, 0.0f);
    TArray<FRaftSimFlexCrewAction> Actions;
    for (int32 Index = 0; Index < CrewAvatars.Num(); ++Index)
    {
        ARaftSimCrewAvatarActor* Avatar = CrewAvatars[Index];
        if (!Avatar || Avatar->GetAttachParentActor() != this || Avatar == AssistedBoardingAvatar.Get())
        {
            continue;
        }
        // The guide joins emergency high-side even during a recent stroke.
        // Otherwise its own stroke takes priority over the standing command.
        const bool bGuideAvatar = Index == CrewAvatars.Num() - 1;
        if (bGuideAvatar && IsGuideRescuing()) continue;
        ERaftSimCrewAvatarAction ThisAvatarAction = AvatarAction;
        if (!bGuideAvatar &&
            (ActiveCrewCommand == ERaftSimCrewCommand::TurnLeft ||
             ActiveCrewCommand == ERaftSimCrewCommand::TurnRight))
        {
            // Seat sides alternate with spawn order (even index = port,
            // Side -1). Left turn: port back-paddles, starboard drives
            // forward; right turn mirrors. Both sides share the crew stroke
            // phase, so the sliced yaw impulse stays on the same catch.
            const bool bPortSeat = Index % 2 == 0;
            const bool bBackPaddleSeat =
                ActiveCrewCommand == ERaftSimCrewCommand::TurnLeft
                    ? bPortSeat
                    : !bPortSeat;
            ThisAvatarAction = bBackPaddleSeat
                ? ERaftSimCrewAvatarAction::BackStroke
                : ERaftSimCrewAvatarAction::ForwardStroke;
        }
        const ERaftSimCrewAvatarAction ResolvedAction =
            bGuideAvatar && GuideStrokeActionSeconds > 0.0f && ActiveCrewCommand != ERaftSimCrewCommand::HighSide
                ? GuideStrokeAction
                : ThisAvatarAction;

        // D2 actions are per seat, not a broadcast from the guide. Use the
        // same resolved action as presentation, including the guide's own
        // stroke override; detached swimmers never enter this loop body.
        const bool bHighSide = ResolvedAction == ERaftSimCrewAvatarAction::HighSidePort ||
            ResolvedAction == ERaftSimCrewAvatarAction::HighSideStarboard;
        if (bHighSide || Avatar->HasHighSideTransfer() || ResolvedAction == ERaftSimCrewAvatarAction::Brace)
        {
            if (Actions.IsEmpty()) Actions.Reserve(CrewAvatars.Num());
            FRaftSimFlexCrewAction Action;
            // Render/rescue ids are paddler_1..N; BuildDefaultCrewSeats uses
            // passenger_0..N-1. Keep the physical contract, not the display id.
            Action.SeatId = bGuideAvatar ? TEXT("guide")
                : FString::Printf(TEXT("passenger_%d"), Index);
            if (bHighSide)
            {
                Action.HighSideDirection =
                    ResolvedAction == ERaftSimCrewAvatarAction::HighSidePort ? -1 : 1;
                Action.bBrace = true;
            }
            else if (ResolvedAction == ERaftSimCrewAvatarAction::Brace)
            {
                Action.LeanOffset = FVector(0.0f, 0.0f, -0.15f);
            }
            UpdateCrewTransfer(Avatar,Index,bHighSide,DeltaSeconds,Action);
            if (bHighSide || Action.bUseCrewTransfer || ResolvedAction == ERaftSimCrewAvatarAction::Brace) Actions.Add(Action);
        }
        UpdateCrewStamina(Index, ResolvedAction, DeltaSeconds);
        // A spent paddler's stroke drags: slower cadence, same technique.
        const bool bStroking = ResolvedAction == ERaftSimCrewAvatarAction::ForwardStroke ||
            ResolvedAction == ERaftSimCrewAvatarAction::BackStroke ||
            ResolvedAction == ERaftSimCrewAvatarAction::TurnLeft ||
            ResolvedAction == ERaftSimCrewAvatarAction::TurnRight;
        Avatar->SetAvatarAction(ResolvedAction, bStroking
            ? .8f + .2f * (CrewStamina.IsValidIndex(Index) ? CrewStamina[Index] : 1.f) : 1.f);
    }
    // Publish empty as well, so rest/strokes clear all prior weight shifts.
    RaftAdapter->SetFlexibleCrewActions(Actions);

    // Advance the same 0..1 cadence used by the visible stroke. The total
    // per-stroke impulse is sliced only across the planted mid-stroke window;
    // catch setup and airborne recovery contribute no propulsion.
    const bool bCrewReturning = CrewAvatars.ContainsByPredicate([this](const auto& Avatar)
        {return Avatar && Avatar->GetAttachParentActor()==this && Avatar->HasHighSideTransfer();});
    if (!IsPropulsiveCrewCommand(ActiveCrewCommand) || bCrewReturning)
    {
        CrewStrokePhase = 0.0f;
        return;
    }
    const float StrokeInterval = FMath::Max(
        CrewStrokeIntervalSeconds, FixedSubstepSeconds);
    const float PhaseAdvance = FMath::Min(
        DeltaSeconds / StrokeInterval, 1.0f);
    const float PhaseStart = CrewStrokePhase;
    const float UnwrappedPhaseEnd = PhaseStart + PhaseAdvance;
    const float PowerStart =
        URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseStart();
    const float PowerEnd =
        URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseEnd();
    if ((PhaseStart < PowerStart && UnwrappedPhaseEnd >= PowerStart) ||
        UnwrappedPhaseEnd >= 1.0f + PowerStart)
    {
        // The blades plant as the power window opens.
        ++CrewStrokeCatchCount;
    }
    const auto MeasurePowerOverlap =
        [PowerStart, PowerEnd](float SegmentStart, float SegmentEnd)
        {
            return FMath::Max(
                0.0f,
                FMath::Min(SegmentEnd, PowerEnd) -
                    FMath::Max(SegmentStart, PowerStart));
        };
    float PowerOverlap = MeasurePowerOverlap(
        PhaseStart, FMath::Min(UnwrappedPhaseEnd, 1.0f));
    if (UnwrappedPhaseEnd > 1.0f)
    {
        PowerOverlap += MeasurePowerOverlap(0.0f, UnwrappedPhaseEnd - 1.0f);
    }
    CrewStrokePhase = FMath::Frac(UnwrappedPhaseEnd);
    if (PowerOverlap <= KINDA_SMALL_NUMBER)
    {
        return;
    }
    const float ImpulseFraction = PowerOverlap /
        FMath::Max(PowerEnd - PowerStart, KINDA_SMALL_NUMBER);
    // Each paddler aboard pulls with their own remaining strength (a fresh
    // full crew is exactly PaddlerCount); tired arms move less water.
    const float Crew = GetCrewStrokeStrength();
    if (Crew <= KINDA_SMALL_NUMBER)
    {
        return;
    }
    const float PerPaddler =
        PaddleStrokeImpulseNs * 0.5f * ImpulseFraction;
    LastCrewStrokeImpulsePhase = FMath::Clamp(CrewStrokePhase, PowerStart, PowerEnd);
    ++CrewStrokeImpulseApplicationCount;
    const FVector Forward = GetActorForwardVector();
    // Paddling drives the hull TO paddling speed over the water, not past
    // it. Uncapped cadence impulses compounded to 9.7 m/s on 2026-08-10 -
    // triple a paddled raft - which crossed the pool in seconds, slammed
    // the cascade's wave train, shipped 294 kg of overwash, and rolled.
    const float PaddleShortfall = GetPaddlePropulsionShortfall(Forward);
    if ((CrewStrokeImpulseApplicationCount & 7) == 0)
    {
        // Throttled propulsion diagnostic: answers "paddling does nothing"
        // reports from the session log alone (speed, governor, impulse).
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim crew propulsion: raftSpeed=%.2f m/s "
                 "shortfall=%.2f impulseNs=%.0f command=%d"),
            GetRaftVelocity().Size2D(),
            PaddleShortfall,
            PerPaddler * Crew * PaddleShortfall,
            static_cast<int32>(ActiveCrewCommand));
    }
    const float WaterPurchase = GetPaddleWaterPurchase();
    if (WaterPurchase <= KINDA_SMALL_NUMBER)
    {
        return;
    }
    switch (ActiveCrewCommand)
    {
        case ERaftSimCrewCommand::AllForward:
            RaftAdapter->AddExternalImpulse(
                Forward * PerPaddler * Crew * PaddleShortfall * WaterPurchase,
                FVector::ZeroVector);
            break;
        case ERaftSimCrewCommand::AllBackward:
        {
            // The raw stroke impulse is sized for the FORWARD feel, where
            // the propulsion governor fades it near cruise. Backward it
            // met no such brake until sternway built, so on the softened
            // hull drag one crew back stroke delivered a ~10 m/s delta on
            // the 220 kg body â€” +3 m/s of way erased instantly ("a single
            // back paddle stroke suddenly stopped the boat but it should
            // have had lots of forward momentum"). Back-paddling against
            // the boat's own way is mechanically the crew's weakest
            // stroke: cap each stroke at a fixed speed change so shedding
            // real momentum takes the several strokes it takes on a real
            // raft.
            constexpr float kBackStrokeMaxDeltaVPerStrokeMps = 0.85f;
            const float BodyMassKg = FMath::Max(
                RaftAdapter->GetRaftBodyConfig().MassKg, 100.0f);
            const float RequestedNs = PerPaddler * Crew *
                GetPaddlePropulsionShortfall(-Forward) * WaterPurchase;
            const float CapNs = BodyMassKg * kBackStrokeMaxDeltaVPerStrokeMps *
                ImpulseFraction;
            RaftAdapter->AddExternalImpulse(
                -Forward * FMath::Min(RequestedNs, CapNs),
                FVector::ZeroVector);
            break;
        }
        case ERaftSimCrewCommand::TurnLeft:
        case ERaftSimCrewCommand::TurnRight:
        {
            // Yaw uses its own impulse basis: pivot strokes meet far less
            // resistance than hull drag, so the forward knob must not scale
            // them.
            const float TurnPerPaddler =
                CrewTurnStrokeImpulseNs * 0.5f * ImpulseFraction;
            const float TurnSign =
                ActiveCrewCommand == ERaftSimCrewCommand::TurnLeft
                ? -1.0f
                : 1.0f;
            RaftAdapter->AddExternalImpulse(
                FVector::ZeroVector,
                FVector(0.0f, 0.0f,
                    TurnSign * TurnPerPaddler * Crew * 1.1f * WaterPurchase));
            break;
        }
        case ERaftSimCrewCommand::Stop:
        {
            // Brace/back-paddle to shed speed. Same per-stroke cap as the
            // back stroke, and never more than the momentum that remains â€”
            // with the softened hull drag an uncapped brake impulse
            // overshoots and visibly REVERSES a slow raft instead of
            // holding it.
            constexpr float kBrakeMaxDeltaVPerStrokeMps = 0.85f;
            const FVector Vel = RaftAdapter->GetKinematicState().LinearVelocityMetersPerSecond;
            const float BodyMassKg = FMath::Max(
                RaftAdapter->GetRaftBodyConfig().MassKg, 100.0f);
            const float RequestedNs =
                PerPaddler * Crew * WaterPurchase;
            const float CapNs = FMath::Min(
                BodyMassKg * kBrakeMaxDeltaVPerStrokeMps * ImpulseFraction,
                BodyMassKg * Vel.Size());
            RaftAdapter->AddExternalImpulse(
                -Vel.GetSafeNormal() * FMath::Min(RequestedNs, CapNs),
                FVector::ZeroVector);
            break;
        }
        default:
            break;
    }
}

float ARaftSimRaftActor::GetPaddleWaterPurchase() const
{
    // Paddles only move the boat when the blades reach water. On a dry bar
    // the crew's strokes sweep sand, and a loaded raft is far too heavy to
    // scoot from that ("paddling on dry land should be impossible", player
    // recording 2026-08-31 â€” the beached raft crawled across the beach
    // under AllForward). Each side's blade station is sampled where the
    // blades actually plant; a half-beached raft keeps half its purchase,
    // and a firmly grounded hull keeps only enough bite to work itself off
    // a gravel touch, not to drive overland.
    if (Bridge == nullptr)
    {
        return 1.0f;
    }
    const URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime();
    if (Water == nullptr)
    {
        return 1.0f;
    }
    const FVector RightCm = GetActorRightVector() * 165.0f;
    float Purchase = 0.0f;
    for (const float Side : {-1.0f, 1.0f})
    {
        FRaftSimWaterSample Sample;
        if (Water->SampleWaterAtWorldPosition(
                GetActorLocation() + RightCm * Side, Sample) &&
            Sample.bWet && Sample.DepthMeters > 0.10f)
        {
            Purchase += 0.5f;
        }
    }
    if (Purchase > 0.0f && RaftAdapter != nullptr &&
        RaftAdapter->GetLastGroundedSupportPointCount() >= 3)
    {
        // A grounded hull whose CENTRE stands over dry ground is parked on
        // land: whatever water a blade tip can still reach, the crew cannot
        // drag a loaded raft across sand ("paddling on dry ground still
        // moves the boat", 2026-09-01 â€” the first pass only capped the
        // grounded case, so a beached raft at the waterline kept 35% of its
        // thrust). Reduced bite survives only while the hull itself still
        // stands in water, which is what lets a crew work off a gravel
        // touch mid-river.
        FRaftSimWaterSample CenterSample;
        const bool bCenterInWater = Water->SampleWaterAtWorldPosition(
            GetActorLocation(), CenterSample) &&
            CenterSample.bWet && CenterSample.DepthMeters > 0.05f;
        Purchase = bCenterInWater ? FMath::Min(Purchase, 0.35f) : 0.0f;
    }
    return Purchase;
}

float ARaftSimRaftActor::GetPaddlePropulsionShortfall(
    const FVector& StrokeDirection) const
{
    // 1.0 when the hull is at or below water speed in the stroke direction,
    // fading to 0.0 as it approaches the configured crewed paddling speed
    // over the water. Keeps strokes honest: they close the gap to hull
    // speed instead of compounding without bound.
    FVector WaterVelocityMps = FVector::ZeroVector;
    if (Bridge != nullptr)
    {
        if (const URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
        {
            FRaftSimWaterSample Sample;
            if (Water->SampleWaterAtWorldPosition(GetActorLocation(), Sample) &&
                Sample.bWet)
            {
                WaterVelocityMps = Sample.VelocityMetersPerSecond;
            }
        }
    }
    const float RelativeForwardMps = FVector::DotProduct(
        GetRaftVelocity() - WaterVelocityMps, StrokeDirection);
    return FMath::Clamp(
        1.0f - RelativeForwardMps /
            FMath::Max(MaxPaddleSpeedOverWaterMps, 0.5f),
        0.0f,
        1.0f);
}

FVector ARaftSimRaftActor::GetRaftVelocity() const
{
    return RaftAdapter != nullptr
        ? RaftAdapter->GetKinematicState().LinearVelocityMetersPerSecond
        : FVector::ZeroVector;
}

void ARaftSimRaftActor::ApplyPaddleStroke(ERaftSimPaddleSide Side, float ForwardScale)
{
    if (IsSoloOarRig())
    {
        const float Scale = FMath::Clamp(ForwardScale, -1.f, 1.f);
        if (FMath::Abs(Scale) < .2f) return;
        IssueCrewCommand(ERaftSimCrewCommand::Rest);
        TransientOarIntents = FVector2D(Scale, Scale);
        TransientOarSeconds = .75f;
        RefreshOarCommandIntents();
        return;
    }
    if (RaftAdapter == nullptr)
    {
        return;
    }
    const float Scale = FMath::Clamp(ForwardScale, -1.0f, 1.0f);
    const FVector StrokeDirection = GetActorForwardVector() * FMath::Sign(Scale);
    const float Shortfall = GetPaddlePropulsionShortfall(StrokeDirection);
    // Discrete per-stroke diagnostic: settles "back paddle doesn't seem to
    // be implemented" style reports from the session log alone (input
    // mapping, sign, and governor factor all visible per stroke).
    ++PaddleStrokeCount;
    (void)Side;
    // W/S IS the crew's paddle command â€” the crew animates and propels, the
    // guide does not stroke (first split shipped 2026-08-11 inverted this
    // and the playtest immediately reported "crew animation no longer fires
    // when paddle command given"). A tap owns the crew for one cadence
    // stroke and expires back to Rest; an explicit standing order (number
    // keys) is refreshed rather than fought.
    const ERaftSimCrewCommand CadenceCommand = Scale >= 0.0f
        ? ERaftSimCrewCommand::AllForward
        : ERaftSimCrewCommand::AllBackward;
    IssueCrewCommand(CadenceCommand);
    bCrewCommandFromGuidePaddle = true;
    GuidePaddleCommandSeconds = 0.75f;
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim guide stroke: scale=%.2f shortfall=%.2f crew=1"),
        Scale, Shortfall);
}

void ARaftSimRaftActor::QueueDirectStrokeImpulse(
    const FVector& LinearImpulseNs, const FVector& AngularImpulseNms)
{
    // Hold the kick until the guide pose's planted mid-stroke: instantaneous impulses
    // at animation start made the boat move before any blade visually
    // reached the water (2026-08-11: "the boat turns but the paddle
    // animation comes after the motion"). The same power-window midpoint is
    // used for direct guide strokes and crew propulsion.
    // The guide's blade obeys the same water-purchase rule as the crew's:
    // no water under the blade, no push.
    const float WaterPurchase = GetPaddleWaterPurchase();
    PendingDirectLinearImpulseNs += LinearImpulseNs * WaterPurchase;
    PendingDirectAngularImpulseNms += AngularImpulseNms * WaterPurchase;
    if (DirectImpulseDelaySeconds <= 0.0f)
    {
        const float PowerMidPhase = 0.5f * (
            URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseStart() +
            URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseEnd());
        DirectImpulseDelaySeconds = CrewStrokeIntervalSeconds * PowerMidPhase;
    }
}

void ARaftSimRaftActor::ApplyTurnStroke(float TurnScale)
{
    if (IsSoloOarRig())
    {
        const float Scale = FMath::Clamp(TurnScale, -1.f, 1.f);
        if (FMath::Abs(Scale) < .2f) return;
        IssueCrewCommand(ERaftSimCrewCommand::Rest);
        TransientOarIntents = FVector2D(Scale, -Scale);
        TransientOarSeconds = .75f;
        RefreshOarCommandIntents();
        return;
    }
    if (RaftAdapter == nullptr)
    {
        return;
    }
    const float Scale = FMath::Clamp(TurnScale, -1.0f, 1.0f);
    ++PaddleStrokeCount;
    // A/D is the crew's turn command (opposing-sides pivot strokes), same
    // ownership rules as W/S: tap = one crew stroke, then Rest. The guide
    // never animates on a call; his own blade is ApplyGuideSteerStroke.
    const ERaftSimCrewCommand TurnCommand = Scale > 0.0f
        ? ERaftSimCrewCommand::TurnRight
        : ERaftSimCrewCommand::TurnLeft;
    IssueCrewCommand(TurnCommand);
    bCrewCommandFromGuidePaddle = true;
    GuidePaddleCommandSeconds = 0.75f;
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim guide turn: scale=%.2f crew=1"), Scale);
}

void ARaftSimRaftActor::ApplyGuideSteerStroke(float TurnScale)
{
    if (IsSoloOarRig())
    {
        OarSteerScale = FMath::Clamp(TurnScale, -1.f, 1.f);
        OarSteerSeconds = .75f;
        RefreshOarCommandIntents();
        return;
    }
    if (RaftAdapter == nullptr)
    {
        return;
    }
    const float Scale = FMath::Clamp(TurnScale, -1.0f, 1.0f);
    ++PaddleStrokeCount;
    GuideStrokeAction = Scale > 0.0f
        ? ERaftSimCrewAvatarAction::TurnRight
        : ERaftSimCrewAvatarAction::TurnLeft;
    GuideStrokeActionSeconds = 1.0f;
    // The guide's own stern sweep ("the guide is using his paddle to
    // steer, not paddle with the crew"). Full yaw authority â€” the stern
    // lever arm is precisely where a raft guide's turning power comes
    // from â€” and it works over a standing crew order, so "call all
    // forward, steer with your own blade" is the actual technique. A real
    // sweep also moves water aft, so the same stroke pulls the hull
    // forward a little â€” or backward while the crew is back-paddling (the
    // back-ferry) â€” through the same speed governor as every stroke. The
    // impulse waits for the pose catch like every stroke.
    const float StrokeDirectionSign =
        ActiveCrewCommand == ERaftSimCrewCommand::AllBackward ? -1.0f : 1.0f;
    const FVector StrokeDirection =
        GetActorForwardVector() * StrokeDirectionSign;
    const float SweepShortfall = GetPaddlePropulsionShortfall(StrokeDirection);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim guide steer: scale=%.2f sweepDir=%.0f shortfall=%.2f"),
        Scale, StrokeDirectionSign, SweepShortfall);
    const float GuideStrength = GetGuideStrokeStrength();
    QueueDirectStrokeImpulse(
        StrokeDirection *
            GuideSteerForwardImpulseNs * FMath::Abs(Scale) * SweepShortfall * GuideStrength,
        FVector(0.0f, 0.0f, Scale * GuideSteerYawImpulseNms * GuideStrength));
}

void ARaftSimRaftActor::SetGuideFirstPersonView(bool bFirstPerson)
{
    if (ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide")))
    {
        Guide->SetFirstPersonHeadHidden(bFirstPerson);
    }
}

void ARaftSimRaftActor::SetGuideFirstPersonBodyHidden(bool bShouldHide)
{
    if (ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide")))
    {
        Guide->SetFirstPersonBodyHidden(bShouldHide);
    }
}

bool ARaftSimRaftActor::GetGuideEyeWorldLocationCm(FVector& OutCm) const
{
    const ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide"));
    if (!Guide)
    {
        return false;
    }
    OutCm = Guide->GetFirstPersonEyeWorldLocationCm();
    return !OutCm.ContainsNaN();
}

bool ARaftSimRaftActor::GetGuideHeadWorldLocationCm(FVector& OutCm) const
{
    const ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide"));
    if (Guide == nullptr)
    {
        return false;
    }
    OutCm = Guide->GetPoseHeadWorldLocationCm();
    return true;
}

void ARaftSimRaftActor::Tick(float DeltaSeconds)
{
    CSV_SCOPED_TIMING_STAT(RaftSimTickRaft,Tick);
    Super::Tick(DeltaSeconds);
    if (Bridge == nullptr || RaftAdapter == nullptr)
    {
        return;
    }

    // Throttled drift telemetry: raft speed against the sampled current at
    // the hull. This is the direct instrument for "the river does not carry
    // the boat" reports â€” if water_speed is real and raft_speed stays near
    // zero without input, the water-to-hull drag coupling is the defect.
    DriftTelemetrySeconds += DeltaSeconds;
    if (DriftTelemetrySeconds >= 10.0f)
    {
        DriftTelemetrySeconds = 0.0f;
        float WaterSpeedMps = 0.0f;
        float WaterHeadingDeg = 0.0f;
        float SolverSurfaceZCm = 0.0f;
        float SupportSurfaceZCm = 0.0f;
        float FloorCenterZCm = 0.0f;
        bool bHasFloorCenter = false;
        bool bHullWet = false;
        // Lateral telemetry for the "drifts sideways into the left bank"
        // report (2026-09-02): river-frame lateral offset, the cross-stream
        // components of water and raft velocity, and the cross-stream
        // support-surface slope, so a steady bank-ward creep can be pinned
        // on the flow field, the surface tilt, or the hull model.
        float RiverLateralM = 0.0f;
        float WaterLateralMps = 0.0f;
        float RaftLateralMps = 0.0f;
        float SurfaceSlopeLateral = 0.0f;
        float RiverTangentDeg = 0.0f;
        if (const URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
        {
            FRaftSimWaterSample Sample;
            if (Water->SampleWaterAtWorldPosition(GetActorLocation(), Sample))
            {
                bHullWet = Sample.bWet;
                SolverSurfaceZCm = Sample.SurfaceHeightMeters * 100.0f;
                if (Sample.bWet)
                {
                    WaterSpeedMps = Sample.VelocityMetersPerSecond.Size2D();
                    WaterHeadingDeg = FMath::RadiansToDegrees(FMath::Atan2(
                        Sample.VelocityMetersPerSecond.Y,
                        Sample.VelocityMetersPerSecond.X));
                }
            }
            SupportSurfaceZCm = SolverSurfaceZCm;
            FRaftSimWaterSample SupportSample;
            if (Water->SampleRaftSupportSurfaceAtWorldPosition(
                    GetActorLocation(), SupportSample) &&
                SupportSample.bWet)
            {
                SupportSurfaceZCm = SupportSample.SurfaceHeightMeters * 100.0f;
            }
            FVector2D RiverPosition;
            FVector RiverTangent;
            FVector RiverLeftNormal;
            if (Water->WorldToRiverCoordinates(
                    GetActorLocation(), RiverPosition, RiverTangent, RiverLeftNormal))
            {
                const FVector LeftDirection = RiverLeftNormal.GetSafeNormal2D();
                RiverLateralM = RiverPosition.Y;
                RiverTangentDeg = FMath::RadiansToDegrees(
                    FMath::Atan2(RiverTangent.Y, RiverTangent.X));
                WaterLateralMps = Sample.bWet
                    ? FVector::DotProduct(Sample.VelocityMetersPerSecond, LeftDirection)
                    : 0.0f;
                RaftLateralMps = FVector::DotProduct(GetRaftVelocity(), LeftDirection);
                FRaftSimWaterSample LeftSample;
                FRaftSimWaterSample RightSample;
                const FVector LateralOffsetCm = LeftDirection * 100.0f;
                if (Water->SampleRaftSupportSurfaceAtWorldPosition(
                        GetActorLocation() + LateralOffsetCm, LeftSample) &&
                    Water->SampleRaftSupportSurfaceAtWorldPosition(
                        GetActorLocation() - LateralOffsetCm, RightSample) &&
                    LeftSample.bWet && RightSample.bWet)
                {
                    SurfaceSlopeLateral =
                        (LeftSample.SurfaceHeightMeters - RightSample.SurfaceHeightMeters) / 2.0f;
                }
            }
        }
        bHasFloorCenter = GetRenderedFloorCenterWorldZCm(FloorCenterZCm);
        const float FloorFreeboardCm = bHasFloorCenter
            ? FloorCenterZCm - SupportSurfaceZCm
            : 0.0f;
        const float RenderedFloorFreeboardCm = bHasFloorCenter
            ? FloorFreeboardCm -
                ARaftSimWaterSurfaceActor::GetLiveSurfaceRenderLiftCm()
            : 0.0f;
        float SunPitchDeg = 0.0f;
        float SunIntensityLux = 0.0f;
        if (TActorIterator<ADirectionalLight> SunIt{GetWorld()})
        {
            SunPitchDeg = SunIt->GetActorRotation().Pitch;
            if (const ULightComponent* SunLight = SunIt->GetLightComponent())
            {
                SunIntensityLux = SunLight->Intensity;
            }
        }
        // -RaftSimDriftScreenshot: grab the live player viewport alongside
        // each drift sample, so first-person presentation (paddle rig, water
        // look) can be inspected from headless -game -RenderOffscreen runs.
        static const bool bDriftScreenshot =
            FParse::Param(FCommandLine::Get(), TEXT("RaftSimDriftScreenshot"));
        if (bDriftScreenshot)
        {
            FScreenshotRequest::RequestScreenshot(false);
        }
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim raft drift: raft_speed_mps=%.3f water_speed_mps=%.3f ")
            TEXT("raft_z_cm=%.1f surface_z_cm=%.1f solver_surface_z_cm=%.1f ")
            TEXT("support_delta_cm=%.1f floor_z_cm=%.1f floor_freeboard_cm=%.1f ")
            TEXT("render_floor_freeboard_cm=%.1f pitch_deg=%.1f wet=%d retained_kg=%.0f ")
            TEXT("pressure=%.2f integrity=%.2f dry_points=%d ground_points=%d ")
            TEXT("ground_penetration_m=%.3f x_cm=%.0f y_cm=%.0f ")
            TEXT("sun_pitch=%.1f sun_intensity=%.1f ")
            TEXT("lateral_m=%.2f water_lat_mps=%.3f raft_lat_mps=%.3f ")
            TEXT("roll_deg=%.2f surf_slope_lat=%.4f tangent_dir_deg=%.1f ")
            TEXT("water_dir_deg=%.1f raft_dir_deg=%.1f"),
            GetRaftVelocity().Size(),
            WaterSpeedMps,
            GetActorLocation().Z,
            SupportSurfaceZCm,
            SolverSurfaceZCm,
            SupportSurfaceZCm - SolverSurfaceZCm,
            FloorCenterZCm,
            FloorFreeboardCm,
            RenderedFloorFreeboardCm,
            GetActorRotation().Pitch,
            bHullWet ? 1 : 0,
            GetD3RetainedWaterMassKg(),
            RaftCondition.PressureFraction,
            RaftCondition.FabricIntegrity,
            RaftAdapter->GetLastDrySupportPointCount(),
            RaftAdapter->GetLastGroundedSupportPointCount(),
            RaftAdapter->GetLastMaximumGroundPenetrationMeters(),
            GetActorLocation().X,
            GetActorLocation().Y,
            SunPitchDeg,
            SunIntensityLux,
            RiverLateralM,
            WaterLateralMps,
            RaftLateralMps,
            GetActorRotation().Roll,
            SurfaceSlopeLateral,
            RiverTangentDeg,
            WaterHeadingDeg,
            FMath::RadiansToDegrees(FMath::Atan2(
                GetRaftVelocity().Y, GetRaftVelocity().X)));
    }

    RockObstacleRefreshRemaining -= DeltaSeconds;
    if (RockObstacleRefreshRemaining <= 0.0f)
    {
        UpdateRockObstacles();
        RockObstacleRefreshRemaining = 0.05f;
    }

    FRaftSimPhysicsTickInput Input;
    // The bridge bounds work and retains debt; do not discard hitch time here.
    Input.FrameDeltaSeconds = DeltaSeconds;
    // A presentation refresh frame (15 Hz, ~20 ms of surface work on South
    // Fork) takes at most two fixed ticks; the lighter frames between
    // refreshes run the deferred ones. Whole ticks only, nothing dropped or
    // resized, and once four ticks are owed the normal bound applies again.
    if (!PresentationSurface.IsValid() && (PresentationSurfaceSearchSeconds -= DeltaSeconds) <= 0.0f)
    {
        PresentationSurfaceSearchSeconds = 1.0f;
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(GetWorld()); It) PresentationSurface = *It;
    }
    static const bool bNoRefreshTickBound = FParse::Param(FCommandLine::Get(), TEXT("RaftSimNoRefreshTickBound"));
    if (const ARaftSimWaterSurfaceActor* Surface = PresentationSurface.Get();
        !bNoRefreshTickBound && Surface && Surface->RefreshesThisFrame(DeltaSeconds) &&
        Bridge->GetLastOutput().SimulationBacklogSeconds + DeltaSeconds <= 4.0 * Bridge->GetWaterStepSeconds())
    {
        Input.MaximumFixedTicks = 2;
    }
    FRaftSimPhysicsTickOutput Output;
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_PhysicsBridgeTick);
        Output = Bridge->TickBridge(Input);
    }
    if (Output.CommittedPhysicsFrame > 0)
    {
        FVector Location = Output.RaftState.WorldTransform.GetTranslation();
        FVector Velocity = Output.RaftState.LinearVelocityMetersPerSecond;
        if (RaftSimWorldPositionGuard::Recover(Location,Velocity,GetActorLocation()))
        {
            FRaftSimRaftKinematicState Recovered = RaftAdapter->GetKinematicState();
            Recovered.WorldTransform.SetTranslation(Location);
            Recovered.LinearVelocityMetersPerSecond = Velocity;
            RaftAdapter->SetKinematicState(Recovered);
            UE_LOG(LogTemp,Warning,TEXT("Raft position outside finite engine world; restored previous valid pose"));
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

    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_CapsizeUpdate);
        UpdateCapsizeLoop(FMath::Min(DeltaSeconds, 0.25f));
        UpdatePassengerWashouts(DeltaSeconds);
    }
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_CrewUpdate);
        UpdateCrew(FMath::Min(DeltaSeconds, 0.25f));
        if (OarRig && IsSoloOarRig())
        {
            // Rowing only while the rower sits upright on the seat.
            ARaftSimCrewAvatarActor* Rower = FindAvatar(TEXT("guide"));
            const bool bRowerAboard = RaftMode == ERaftSimRaftMode::Upright && Rower &&
                Rower->GetAttachParentActor() == this && FindSwimmerIndex(TEXT("guide")) == INDEX_NONE && !IsGuideRescuing();
            OarRig->TickRig(FMath::Min(DeltaSeconds, 0.25f), this, Rower, bRowerAboard);
        }
    }
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_RescueUpdate);
        UpdateRescueInteraction(FMath::Min(DeltaSeconds, 0.25f));
        UpdateFlipLine(FMath::Min(DeltaSeconds, 0.25f));
        UpdateRescueLineVisual();
    }
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_ConditionUpdate);
        UpdateRaftCondition(FMath::Min(DeltaSeconds, 0.25f));
    }
    UpdateFlexibleRaftVisual();
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_WetnessUpdate);
        UpdateRaftWetness(FMath::Min(DeltaSeconds, 0.25f));
    }
}

#if !UE_BUILD_SHIPPING
bool ARaftSimRaftActor::AdvanceIsolatedFlipDemo(float Dt)
{
    if(!RaftAdapter || !RaftAdapter->StepRaftDynamics(Dt))return false;
    SetActorTransform(RaftAdapter->GetKinematicState().WorldTransform);
    // Same physical capsize gate and crew lifecycle as normal gameplay.
    if(RaftMode==ERaftSimRaftMode::Upright &&
        RaftSimCapsizePolicy::PhysicallyInverted(GetActorQuat(),CapsizeRollDegrees))
    {
        EnterCapsize(); // Real crew ejection/occupancy/rescue lifecycle.
    }
    if(RaftMode!=ERaftSimRaftMode::Upright)DriftSwimmers(Dt);
    return true;
}
#endif

void ARaftSimRaftActor::UpdateCapsizeLoop(float DeltaSeconds)
{
    const FRaftSimFlexStepTelemetry& Telemetry = RaftAdapter->GetLastFlexibleStepTelemetry();

    if (RaftMode == ERaftSimRaftMode::Upright)
    {
        // Risk remains telemetry; only an integrated physical inversion ejects
        // crew. A risk estimate cannot animate an upright hull through a rock.
        const bool bFlipRisk = Telemetry.bReferenceFlipRisk && Telemetry.ReferenceFlipMarginNm < 0.0;
        FlipRiskLatchSeconds = bFlipRisk
            ? FlipRiskLatchSeconds + DeltaSeconds
            : FMath::Max(0.0f, FlipRiskLatchSeconds - DeltaSeconds);

        if (RaftSimCapsizePolicy::PhysicallyInverted(GetActorQuat(),CapsizeRollDegrees))
        {
            EnterCapsize();
        }
        if (Swimmers.IsEmpty())
        {
            return;
        }
    }

    // Evidence: rescue-equipment-v3's live breaker ejected at upZ=-0.180,
    // then the empty hull physically returned to roll=0, while this state
    // stayed Capsized and rejected boarding for 110 seconds. Reconcile the
    // mode with measured upright geometry WITHOUT seating crew, resetting
    // physics, or completing an active flip-line. Its separate test still
    // requires a real pull and integrated righting from both inverted sides.
    if (RaftMode == ERaftSimRaftMode::Capsized && !IsFlipLineActive() && GetActorUpVector().Z > .65f)
    {
        RaftMode = ERaftSimRaftMode::Upright;
        RaftAdapter->SetFlexibleCapsized(false);
    }
    // Capsized or Recovering: swimmers drift and can be reseated.
    DriftSwimmers(DeltaSeconds);

    if (RaftMode == ERaftSimRaftMode::Recovering)
    {
        // No remote automatic reseating: recover each swimmer at the tube.
        if (Swimmers.Num() == 0)
        {
            RaftMode = ERaftSimRaftMode::Upright;
            FlipRiskLatchSeconds = 0.0f;
        }
    }
}

void ARaftSimRaftActor::EnterCapsize()
{
    CancelFlipLine();
    FinishAssistedBoarding();
    RescueInteraction = FRaftSimRescueInteractionState{};
    RopeRecoverRemaining = ThrowWindUpRemaining = 0.f;
    bThrowBagDeployed = bGuideRescuePoseActive = false;
    GuideRescueYawDeg = 0.f;
    PhysicalCapsizeEntryUpZ=GetActorQuat().GetUpVector().Z;
    CancelTimedBoarding();
    const FRaftSimFlexStepTelemetry EntryTelemetry = RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry()
        : FRaftSimFlexStepTelemetry{};
    UE_LOG(
        LogTemp,
        Warning,
        TEXT("RaftSim capsize: raft=%s location_cm=%s rotation_deg=%s "
             "flip_margin_nm=%.3f flip_threshold_nm=%.3f retained_water_kg=%.3f "
             "retained_roll_moment_nm=%.3f dynamic_roll_moment_nm=%.3f "
             "wet_samples=%d/%d contacts=%d "
             "wrapping=%d pinned=%d"),
        *GetName(),
        *GetActorLocation().ToCompactString(),
        *GetActorRotation().ToCompactString(),
        EntryTelemetry.ReferenceFlipMarginNm,
        EntryTelemetry.ReferenceFlipThresholdNm,
        EntryTelemetry.TotalRetainedWaterMassKg,
        EntryTelemetry.RetainedWaterRollMomentNm,
        EntryTelemetry.OvertoppingDynamicRollMomentNm,
        EntryTelemetry.LiveWetSampleCount,
        EntryTelemetry.LiveWaterSampleCount,
        EntryTelemetry.ContactCount,
        EntryTelemetry.WrappingContactCount,
        EntryTelemetry.PinnedObstacleCount);
    RaftMode = ERaftSimRaftMode::Capsized;
    FlipRiskLatchSeconds = 0.0f;
    // Right the boat here on re-flip. Guard against a diverged sink so the
    // recovery point stays near where the crew went overboard — relative to
    // the LOCAL water surface, not world Z=0: the old absolute ±2 m clamp
    // assumed a tank at the origin, and on the South Fork full reach (river
    // at ~300 m) it parked the recovery point 300 m under the riverbed, so
    // every capsize re-flipped the hull inside terrain and the physics threw
    // it 400 m into the sky at 40 m/s (2026-09-02 reach survey, 2400 m and
    // 9400 m).
    CapsizeLocation = GetActorLocation();
    {
        float ReferenceZCm = CapsizeLocation.Z;
        if (Bridge != nullptr)
        {
            if (const URaftSimWaterRuntimeAdapter* WaterAdapter = Bridge->GetWaterRuntime())
            {
                FRaftSimWaterSample Sample;
                if (WaterAdapter->SampleWaterAtWorldPosition(CapsizeLocation, Sample) &&
                    Sample.bWet && FMath::IsFinite(Sample.SurfaceHeightMeters))
                {
                    ReferenceZCm = Sample.SurfaceHeightMeters * kCmPerM;
                }
            }
        }
        if (!FMath::IsFinite(ReferenceZCm))
        {
            ReferenceZCm = CheckpointTransform.GetLocation().Z;
        }
        CapsizeLocation.Z = FMath::Clamp(
            CapsizeLocation.Z, ReferenceZCm - 200.0f, ReferenceZCm + 200.0f);
    }

    if (RaftAdapter != nullptr)
    {
        // An open-floor paddle raft sheds retained deck water and crew mass
        // when it physically rolls over. Keep the authoritative pose and rate;
        // no roll constraint or animation drives the empty hull.
        RaftAdapter->SetFlexibleCapsized(true);
        FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
        State.WorldTransform = GetActorTransform();
        const FRaftSimFlexStepTelemetry& Telemetry =
            RaftAdapter->GetLastFlexibleStepTelemetry();
        CapsizeFlipDirection = Telemetry.RetainedWaterRollMomentNm < 0.0 ? -1.0f : 1.0f;
        if (FMath::IsNearlyZero(static_cast<float>(Telemetry.RetainedWaterRollMomentNm)))
        {
            CapsizeFlipDirection = GetActorRotation().Roll < 0.0f ? -1.0f : 1.0f;
        }
        const FRotator StartRotation = GetActorRotation();
        CapsizeStartPitchDegrees = FMath::UnwindDegrees(StartRotation.Pitch);
        CapsizeStartRollDegrees = FMath::UnwindDegrees(StartRotation.Roll);
        CapsizeRollAxisWorld = GetActorForwardVector().GetSafeNormal();
        if (CapsizeRollAxisWorld.IsNearlyZero())
        {
            CapsizeRollAxisWorld = FVector::ForwardVector;
        }
        CapsizeTargetRotation = FRotator(
            0.0f, StartRotation.Yaw, CapsizeFlipDirection * 180.0f).Quaternion();
        // Preserve the integrated pose AND release momentum in normal gameplay.
        RaftAdapter->SetKinematicState(State);
        CapsizeTransitionRemainingSeconds = 0.f;
    }

    SpawnSwimmers(CrewSize, true);
}

void ARaftSimRaftActor::SpawnSwimmers(int32 Count, bool bIncludeGuide, FName OnlyPassenger, FVector WashVelocityMps)
{
    const int32 Available = FMath::Clamp(Count, 0, PaddlerCount + (bIncludeGuide ? 1 : 0));
    if (Available == 0) return;
    // Keep existing swimmers (including their positions and rescue clocks)
    // when another ejection or capsize adds crew; never orphan their seats.
    const int32 PreviousSwimmerCount = Swimmers.Num();
    const FVector RaftWorldCm = IsFiniteVector(GetActorLocation())
        ? GetActorLocation()
        : CheckpointTransform.GetLocation();
    const FVector RaftM = RaftWorldCm / kCmPerM;
    const FVector FlowMps = SampleWaterVelocityMps(RaftWorldCm);
    for (int32 Index = 0; Index < Available; ++Index)
    {
        FRaftSimSwimmerRescueFrame Swimmer;
        Swimmer.PassengerId = !OnlyPassenger.IsNone() ? OnlyPassenger : bIncludeGuide && Index == 0
            ? FName(TEXT("guide"))
            : FName(*FString::Printf(TEXT("paddler_%d"), Index + (bIncludeGuide ? 0 : 1)));
        if (FindSwimmerIndex(Swimmer.PassengerId) != INDEX_NONE) continue;
        float Angle = (2.0f * PI * Index) / FMath::Max(1, Available);
        if (!OnlyPassenger.IsNone())
            if (const auto* Avatar = FindAvatar(OnlyPassenger))
            {
                const FVector Outward = Avatar->GetActorLocation() - RaftWorldCm;
                Angle = FMath::Atan2(Outward.Y, Outward.X);
            }
        Swimmer.SwimmerWorldPositionMeters =
            RaftM + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * 1.5f;
        Swimmer.SwimmerDriftVelocityMetersPerSecond = FlowMps;
        const bool PhysicalRelease=RaftAdapter && (!OnlyPassenger.IsNone() ||
            (bIncludeGuide && RaftMode==ERaftSimRaftMode::Capsized));
        if(PhysicalRelease)
        {
            if(const auto* Avatar=FindAvatar(Swimmer.PassengerId))
            {
                const FVector ReleaseM=Avatar->GetActorLocation()/kCmPerM;
                const auto& K=RaftAdapter->GetKinematicState();
                // Keep the existing event-only hull-clearance placement in XY,
                // but do not teleport a submerged release to the surface.
                Swimmer.SwimmerWorldPositionMeters.Z=ReleaseM.Z;
                if (!OnlyPassenger.IsNone()) Swimmer.SwimmerWorldPositionMeters = ReleaseM;
                Swimmer.SwimmerDriftVelocityMetersPerSecond=K.LinearVelocityMetersPerSecond+
                    FVector::CrossProduct(K.AngularVelocityRadiansPerSecond,ReleaseM-RaftM) +
                    WashVelocityMps.GetClampedToMaxSize(2.);
            }
        }
        // Game rescue budget includes climbing/righting and sequential casts
        // for the whole crew. Skill still affects swimmer drift and fatigue.
        Swimmer.RescueWindowSeconds = 120.0f;
        Swimmer.bThrowLineAvailable = true;
        Swimmers.Add(Swimmer);

        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId))
        {
            // Ejection must not turn the swimmer toward world +X while the
            // detached guide camera retains its world heading. Keep heading,
            // but release seated/capsize roll and pitch for the authored swim.
            const FQuat SwimHeading = PhysicalRelease ? Avatar->GetActorQuat() :
                FRotator(0.0f, Avatar->GetActorRotation().Yaw, 0.0f).Quaternion();
            Avatar->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
            Avatar->SetActorTransform(FTransform(
                SwimHeading,
                Swimmer.SwimmerWorldPositionMeters * kCmPerM,
                FVector::OneVector));
            Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
            // Establish separation using the actually published hull and
            // posed visible swimmer, not a fixed radius inside a long hull.
            // Project conservative world boxes onto the ejection direction;
            // positive separation on one axis excludes initial intersection.
            // This event-only query does not scan meshes in the frame loop.
            if (RaftVisual && RaftVisual->GetNumSections() > 0)
            {
                const FVector Away(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
                const FVector AbsAway = Away.GetAbs();
                const FBox HullBounds = RaftVisual->CalcBounds(RaftVisual->GetComponentTransform()).GetBox();
                FBox BodyBounds(ForceInit);
                TInlineComponentArray<UPrimitiveComponent*> BodyParts(Avatar);
                for (const UPrimitiveComponent* Part : BodyParts)
                {
                    if (Part && Part->IsRegistered() && Part->IsVisible())
                        BodyBounds += Part->CalcBounds(Part->GetComponentTransform()).GetBox();
                }
                if (HullBounds.IsValid && BodyBounds.IsValid)
                {
                    const double HullSupport = FVector::DotProduct(HullBounds.GetCenter(), Away) +
                        FVector::DotProduct(HullBounds.GetExtent(), AbsAway);
                    const double BodyNear = FVector::DotProduct(BodyBounds.GetCenter(), Away) -
                        FVector::DotProduct(BodyBounds.GetExtent(), AbsAway);
                    // Five centimetres is an explicit numerical clearance,
                    // not inferred hull size or a reduced collision envelope.
                    const double ShiftCm = FMath::Max(0.0, HullSupport + 5.0 - BodyNear);
                    Swimmers.Last().SwimmerWorldPositionMeters += Away * (ShiftCm / kCmPerM);
                    Avatar->SetActorLocation(Swimmers.Last().SwimmerWorldPositionMeters * kCmPerM);
                }
            }
        }
    }
    for(int32 I=PreviousSwimmerCount;I<Swimmers.Num();++I)
    {
        if (OnlyPassenger.IsNone()) AttachSwimmerToWaterSurface(Swimmers[I]);
        if(auto* Avatar=FindAvatar(Swimmers[I].PassengerId))
            Avatar->SetActorLocation(Swimmers[I].SwimmerWorldPositionMeters*kCmPerM);
    }
    RefreshCrewSeatOccupancy();
    if (Swimmers.Num() == PreviousSwimmerCount) return;
    // Appending another washed-out passenger must not drop a connected rope
    // or reset an existing swimmer's rescue clock/selection.
    if (!OnlyPassenger.IsNone() && PreviousSwimmerCount > 0 &&
        FindSwimmerIndex(RescueInteraction.TargetPassengerId) != INDEX_NONE) return;
    RescueInteraction = FRaftSimRescueInteractionState{};
    SelectedSwimmerIndex = INDEX_NONE;
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

void ARaftSimRaftActor::RefreshCrewSeatOccupancy()
{
    if (!RaftAdapter) return;
    RaftAdapter->SetFlexibleCrewSeatOccupied(TEXT("guide"), FindSwimmerIndex(TEXT("guide")) == INDEX_NONE);
    for (int32 Index = 0; Index < PaddlerCount; ++Index)
    {
        const FName PassengerId(*FString::Printf(TEXT("paddler_%d"), Index + 1));
        RaftAdapter->SetFlexibleCrewSeatOccupied(FString::Printf(TEXT("passenger_%d"), Index),
            FindSwimmerIndex(PassengerId) == INDEX_NONE);
    }
}

void ARaftSimRaftActor::AttachSwimmerToWaterSurface(FRaftSimSwimmerRescueFrame& Swimmer) const
{
    // Released crew continue their integrated vertical trajectory until their
    // PFD brings them back to the SAME bound local water surface.
    if(RaftMode==ERaftSimRaftMode::Capsized)return;
#if !UE_BUILD_SHIPPING
    // Isolated labs replace the raft runtime, not the map's shared water
    // subsystem. Crew must see the same authored field as that boat.
    if(RaftAdapter && Bridge && RaftAdapter!=Bridge->GetRaftRuntime())
    {
        if(RaftMode==ERaftSimRaftMode::Capsized)return; // Native submersion candidate owns Z.
        FRaftSimFlexUniformWater Field;
        if(RaftAdapter->SampleBoundFlexibleWater(Swimmer.SwimmerWorldPositionMeters*kCmPerM,Field) && Field.bWet)
        {
            FRaftSimWaterSample Sample;Sample.bWet=true;Sample.SurfaceHeightMeters=Field.SurfaceHeightM;
            RaftSimAttachSwimmerToSurface(Swimmer.SwimmerWorldPositionMeters,Sample);
        }
        return;
    }
#endif
    // Actual replay leaves the near-hull swimming view unaccepted. It does not
    // establish a solver/render datum error; qualify hull/camera contact first.
    static const bool Review=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSwimmerSurfaceReview"));
    if(!Review) return;
    if(!Bridge) return;
    const auto* Water=Bridge->GetWaterRuntime();
    if(!Water) return;
    FRaftSimWaterSample Sample;
    if(Water->SampleWaterAtWorldPosition(Swimmer.SwimmerWorldPositionMeters*kCmPerM,Sample))
    {
        const bool Attached=RaftSimAttachSwimmerToSurface(Swimmer.SwimmerWorldPositionMeters,Sample);
        static const bool Audit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSwimmerSurfaceAudit"));
        if(Audit && GFrameCounter%30==0)
            UE_LOG(LogTemp,Display,TEXT("SwimmerSurfaceAudit passenger=%s frame=%llu attached=%d wet=%d root_m=%.9f surface_m=%.9f"),
                *Swimmer.PassengerId.ToString(),GFrameCounter,Attached,Sample.bWet,
                Swimmer.SwimmerWorldPositionMeters.Z,double(Sample.SurfaceHeightMeters));
    }
}

void ARaftSimRaftActor::DriftSwimmers(float DeltaSeconds)
{
    for (int32 Index = 0; Index < Swimmers.Num(); ++Index)
    {
        if (Swimmers[Index].PassengerId == BoardingPassenger) continue;
        if (Swimmers[Index].PassengerId == TEXT("guide") && IsFlipLineActive() && !bFlipGuideReleased) continue;
        const FVector SwimmerCm = Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM;
        const FVector FlowMps = SampleWaterVelocityMps(SwimmerCm);
        FRaftSimFlexUniformWater Field;
        // PFD resurfacing must continue after the empty boat is righted;
        // otherwise a released flip-line guide freezes above/below the water.
        const bool SubmergedLab=RaftAdapter &&
            RaftAdapter->SampleBoundFlexibleWater(SwimmerCm,Field) && Field.bWet;
        if(SubmergedLab)
            Swimmers[Index]=RaftSimAdvanceSubmergedSwimmer(Swimmers[Index],FlowMps,Field.SurfaceHeightM,DeltaSeconds);
        if(!SubmergedLab)Swimmers[Index] = URaftSimSwimmerRescueLibrary::IntegrateSwimmerDrift(
            Swimmers[Index], FlowMps, DeltaSeconds);
        if (!IsFiniteVector(Swimmers[Index].SwimmerWorldPositionMeters))
        {
            Swimmers[Index].SwimmerWorldPositionMeters =
                (IsFiniteVector(GetActorLocation())
                    ? GetActorLocation()
                    : CheckpointTransform.GetLocation()) / kCmPerM;
            Swimmers[Index].SwimmerDriftVelocityMetersPerSecond = FVector::ZeroVector;
        }
        // Drift can carry a swimmer back into the hull before a rescue starts.
        // Reuse the same conservative posed-body support plane as pulling;
        // do not pull exterior swimmers inward or alter the water elevation.
        // The selected ready swimmer is already posed for tube contact. Do not
        // overwrite that pose (and reset its phase) before the rescue update
        // restores it later in this same frame. Clearance must use that body.
        const bool bTarget = RescueInteraction.TargetPassengerId == Swimmers[Index].PassengerId;
        // A swimmer on a connected rope is held by it, on their back.
        const bool bOnRope = bTarget && RescueInteraction.Method == ERaftSimRescueMethod::ThrowLine &&
            (RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling ||
             RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry);
        const ERaftSimCrewAvatarAction DriftAction =
            bTarget && RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry
                ? ERaftSimCrewAvatarAction::Reentry
                : (bOnRope ? ERaftSimCrewAvatarAction::RopeTow : ERaftSimCrewAvatarAction::Swimming);
        if(auto* Avatar=FindAvatar(Swimmers[Index].PassengerId))
            Avatar->SetAvatarAction(DriftAction);
        FVector HullTarget;
        if(!bOnRope && GetSwimmerTubeTarget(Swimmers[Index].PassengerId,Swimmers[Index].SwimmerWorldPositionMeters,HullTarget))
        {
            const FVector Away=(HullTarget-GetActorLocation()/kCmPerM).GetSafeNormal2D();
            // Half a centimetre of slack: a heeled hull's deck plane is not
            // the water plane, and an exact re-push would creep.
            if(FVector::DotProduct(Swimmers[Index].SwimmerWorldPositionMeters-HullTarget,Away)<-.005)
                Swimmers[Index].SwimmerWorldPositionMeters=HullTarget;
        }
        if (!SubmergedLab) AttachSwimmerToWaterSurface(Swimmers[Index]);
        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmers[Index].PassengerId))
        {
            Avatar->SetActorLocation(Swimmers[Index].SwimmerWorldPositionMeters * kCmPerM);
            Avatar->SetAvatarAction(DriftAction);
            if(SubmergedLab)
            {
                const FQuat Heading=FRotator(0,Avatar->GetActorRotation().Yaw,0).Quaternion();
                Avatar->SetActorRotation(FQuat::Slerp(Avatar->GetActorQuat(),Heading,1.-FMath::Exp(-2.*DeltaSeconds)).GetNormalized());
            }
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
        if (Swimmers[Index].PassengerId == BoardingPassenger) continue;
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
    if (!BoardingPassenger.IsNone() || IsGuideRescuing() || IsFlipLineActive()) return;
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
    if (RopeRecoverRemaining > 0.f)
    {
        RescueInteraction.FeedbackCode = TEXT("rescue_recovering_rope");
        return false;
    }
    if (!BoardingPassenger.IsNone() || IsGuideRescuing() || IsFlipLineActive() ||
        RaftMode == ERaftSimRaftMode::Capsized || IsPassengerSwimming(TEXT("guide"))) return false;
    const auto* TransferringGuide = FindAvatar(TEXT("guide"));
    if (ActiveCrewCommand == ERaftSimCrewCommand::HighSide || (TransferringGuide && TransferringGuide->HasHighSideTransfer()))
    {
        RescueInteraction.FeedbackCode = TEXT("rescue_finish_high_side_first");
        return false;
    }
    if (!Swimmers.IsValidIndex(SelectedSwimmerIndex))
    {
        SelectRescueTarget(1.0f);
    }
    if (!Swimmers.IsValidIndex(SelectedSwimmerIndex))
    {
        return false;
    }
    const FRaftSimSwimmerRescueFrame& Swimmer = Swimmers[SelectedSwimmerIndex];
    // Each person swims as well as they do (URaftSimCrewRoster): a strong
    // swimmer helps the reach or throw, a weak one needs more help.
    const ERaftSimCrewSwimAbility Ability = URaftSimCrewRoster::GetIdentity(Swimmer.PassengerId).SwimAbility;
    FRaftSimSwimmingSkillProfile Skill =
        URaftSimSwimmingSkillLibrary::MakeSwimmingSkillProfile(
            Ability == ERaftSimCrewSwimAbility::Weak ? ERaftSimSwimmingSkillLevel::WeakSwimmer
            : Ability == ERaftSimCrewSwimAbility::Strong ? ERaftSimSwimmingSkillLevel::StrongSwimmer
            : ERaftSimSwimmingSkillLevel::AverageSwimmer);
    const FVector LineStartM = GetRescueHandWorldM();
    Skill.TimeToCriticalSeconds = Swimmer.RescueWindowSeconds;
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
    if (Method == ERaftSimRescueMethod::ThrowLine &&
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::LineInFlight)
        StartThrowChoreography();
    return RescueInteraction.Phase == ERaftSimRescueInteractionPhase::LineInFlight ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling;
}

bool ARaftSimRaftActor::GetSwimmerTubeTarget(FName PassengerId, const FVector& SwimmerM, FVector& TargetM) const
{
    const auto* Avatar = FindAvatar(PassengerId);
    if (!Avatar || !RaftVisual || RaftVisual->GetNumSections() == 0) return false;
    FVector Away = (SwimmerM - GetActorLocation() / kCmPerM).GetSafeNormal2D();
    if (Away.IsNearlyZero()) Away = GetActorRightVector().GetSafeNormal2D();
    const FVector AbsAway = Away.GetAbs();
    FBox BodyBox(ForceInit);
    TInlineComponentArray<UPrimitiveComponent*> Parts(Avatar);
    for (const UPrimitiveComponent* Part : Parts)
        if (Part && Part->IsRegistered() && Part->IsVisible())
            BodyBox += Part->CalcBounds(Part->GetComponentTransform()).GetBox();
    if (!BodyBox.IsValid) return false;
    // Outermost rendered TUBE surface within the swimmer's own depth band,
    // along the outward direction. A swimmer can pass under a tube a rolling
    // hull has lifted clear of the water, never through one at the surface.
    // A world-axis bounding box was far larger than a yawed or heeled boat
    // (abeam at 45 deg of yaw ~3.1 m against a 1 m half-beam) and parked
    // swimmers beyond the 1.35 m boarding reach.
    const FProcMeshSection* Tube = RaftVisual->GetProcMeshSection(0);
    const FTransform Hull = RaftVisual->GetComponentTransform();
    const double SwimmerZ = SwimmerM.Z * kCmPerM;
    double HullSupport = -DBL_MAX;
    if (Tube)
    {
        // World outward reach and height are linear in the local vertex:
        // two dot products per vertex instead of a full transform.
        const FVector AxisX = Hull.GetScaledAxis(EAxis::X), AxisY = Hull.GetScaledAxis(EAxis::Y),
            AxisZ = Hull.GetScaledAxis(EAxis::Z), Origin = Hull.GetLocation();
        const FVector Reach(FVector::DotProduct(AxisX, Away), FVector::DotProduct(AxisY, Away), FVector::DotProduct(AxisZ, Away));
        const FVector Height(AxisX.Z, AxisY.Z, AxisZ.Z);
        const double ReachOrigin = FVector::DotProduct(Origin, Away);
        for (const FProcMeshVertex& Vertex : Tube->ProcVertexBuffer)
        {
            const FVector Local(Vertex.Position);
            if (FMath::Abs(FVector::DotProduct(Local, Height) + Origin.Z - SwimmerZ) <= 60.0)
                HullSupport = FMath::Max(HullSupport, FVector::DotProduct(Local, Reach) + ReachOrigin);
        }
    }
    // Nothing of the hull at the swimmer's level: no contact to resolve.
    if (HullSupport == -DBL_MAX) return false;
    const double BodyNearOffset = FVector::DotProduct(BodyBox.GetCenter() - Avatar->GetActorLocation(), Away) -
        FVector::DotProduct(BodyBox.GetExtent(), AbsAway);
    // Preserve lateral position and water elevation; only move along the
    // outward axis to the conservative visible-hull contact plane.
    TargetM = SwimmerM + Away * ((HullSupport + 5.0 - BodyNearOffset) / kCmPerM -
        FVector::DotProduct(SwimmerM, Away));
    return IsFiniteVector(TargetM);
}

bool ARaftSimRaftActor::FindBoardingTubeSupports(const FVector& SwimmerWorldCm, double HandSpacingCm,
    FVector& LeftLocalCm, FVector& RightLocalCm) const
{
    // Event-only palm-support candidates on the published outer tube (section0).
    // No box proxy, floor/thwart fallback, or assertion that a grip exists here.
    if (!RaftVisual || !IsFiniteVector(SwimmerWorldCm) || !FMath::IsFinite(HandSpacingCm) ||
        HandSpacingCm <= 0. || !GetActorTransform().IsValid()) return false;
    const FProcMeshSection* Tube = RaftVisual->GetProcMeshSection(0);
    if (!Tube || !Tube->bSectionVisible || Tube->ProcVertexBuffer.IsEmpty()) return false;
    const FTransform ToRaft = RaftVisual->GetComponentTransform().GetRelativeTransform(GetActorTransform());
    FBox Bounds(ForceInit);
    for (const auto& Vertex : Tube->ProcVertexBuffer)
    {
        const FVector P = ToRaft.TransformPosition(Vertex.Position);
        if (!IsFiniteVector(P)) return false;
        Bounds += P;
    }
    const FVector Swimmer = GetActorTransform().InverseTransformPosition(SwimmerWorldCm);
    const double Side = Swimmer.Y >= Bounds.GetCenter().Y ? 1. : -1.;
    // Prefer the side tube's middle half, rather than the higher bow/stern rocker.
    const double CenterX = FMath::Clamp(Swimmer.X,
        Bounds.GetCenter().X - Bounds.GetExtent().X * .5,
        Bounds.GetCenter().X + Bounds.GetExtent().X * .5);
    const FVector Seeds[2] = {
        FVector(CenterX - Side * HandSpacingCm * .5, Side > 0. ? Bounds.Max.Y : Bounds.Min.Y, Bounds.Max.Z),
        FVector(CenterX + Side * HandSpacingCm * .5, Side > 0. ? Bounds.Max.Y : Bounds.Min.Y, Bounds.Max.Z)};
    FVector Supports[2];
    double Best[2] = {DBL_MAX, DBL_MAX};
    for (int32 I = 0; I + 2 < Tube->ProcIndexBuffer.Num(); I += 3)
    {
        const FVector A = ToRaft.TransformPosition(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I]].Position);
        const FVector B = ToRaft.TransformPosition(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I+1]].Position);
        const FVector C = ToRaft.TransformPosition(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I+2]].Position);
        const FVector Normal = FVector::CrossProduct(B-A, C-A).GetSafeNormal();
        const FVector Center = (A+B+C)/3.;
        // Upper half and upward-facing slope, independent of mesh winding.
        if (Center.Z < Bounds.GetCenter().Z || Side * (Center.Y-Bounds.GetCenter().Y) <= 0. ||
            FMath::Abs(Normal.Z) < .5) continue;
        for (int32 Hand = 0; Hand < 2; ++Hand)
        {
            const FVector Point = FMath::ClosestPointOnTriangleToPoint(Seeds[Hand], A, B, C);
            const double Distance = FVector::DistSquared(Point, Seeds[Hand]);
            if (Distance < Best[Hand]) { Best[Hand] = Distance; Supports[Hand] = Point; }
        }
    }
    if (Best[0] == DBL_MAX || Best[1] == DBL_MAX ||
        FVector::Distance(Supports[0], Supports[1]) < HandSpacingCm * .5) return false;
    LeftLocalCm = Supports[0]; RightLocalCm = Supports[1];
    return true;
}

double ARaftSimRaftActor::GetRenderedHullDistanceM(const FVector& WorldM) const
{
    // Event-only exact triangle distance. Do not use bounding-box distance to
    // authorize reentry at an empty corner of the conservative pull envelope.
    if (!RaftVisual || !IsFiniteVector(WorldM)) return TNumericLimits<double>::Max();
    const FVector P = WorldM * kCmPerM;
    const FTransform Transform = RaftVisual->GetComponentTransform();
    double BestSquared = TNumericLimits<double>::Max();
    for (int32 S = 0; S < RaftVisual->GetNumSections(); ++S)
    {
        const FProcMeshSection* Section = RaftVisual->GetProcMeshSection(S);
        if (!Section || !Section->bSectionVisible) continue;
        for (int32 I = 0; I + 2 < Section->ProcIndexBuffer.Num(); I += 3)
        {
            const FVector A = Transform.TransformPosition(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I]].Position);
            const FVector B = Transform.TransformPosition(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+1]].Position);
            const FVector C = Transform.TransformPosition(Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+2]].Position);
            if (FVector::CrossProduct(B-A, C-A).SizeSquared() <= UE_DOUBLE_SMALL_NUMBER) continue;
            BestSquared = FMath::Min(BestSquared, FVector::DistSquared(P, FMath::ClosestPointOnTriangleToPoint(P,A,B,C)));
        }
    }
    return FMath::Sqrt(BestSquared) / kCmPerM;
}

void ARaftSimRaftActor::UpdateRescueInteraction(float DeltaSeconds)
{
    UpdateAssistedBoarding(DeltaSeconds);
    if (IsFlipLineActive()) return;
    if (!BoardingPassenger.IsNone()) { UpdateTimedBoarding(DeltaSeconds); return; }
    RopeRecoverRemaining = FMath::Max(0.f, RopeRecoverRemaining - FMath::Max(0.f, DeltaSeconds));
    PoseGuideForRescue(DeltaSeconds);
    AdvanceThrowBag(DeltaSeconds);
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
        RescueInteraction.Phase != ERaftSimRescueInteractionPhase::Pulling &&
        RescueInteraction.Phase != ERaftSimRescueInteractionPhase::ReadyForReentry)
    {
        return;
    }

    if (auto* Guide = FindAvatar(TEXT("guide")); Guide && !bGuideRescuePoseActive)
        Guide->SetAvatarAction(RescueInteraction.Phase == ERaftSimRescueInteractionPhase::LineInFlight
            ? ERaftSimCrewAvatarAction::ThrowLine : ERaftSimCrewAvatarAction::HaulLine);
    const FVector StartM = GetRescueHandWorldM();
    FRaftSimSwimmerRescueFrame& Swimmer = Swimmers[TargetIndex];
    const bool bWasPulling = RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling;
    const bool bRope = RescueInteraction.Method == ERaftSimRescueMethod::ThrowLine;
    float RescueStep = DeltaSeconds;
    if (bRope && RescueInteraction.Phase == ERaftSimRescueInteractionPhase::LineInFlight)
    {
        // The bag is still in the fist through the wind-up and swing; once
        // released, one library flight spans the distance-scaled toss.
        const float Held = FMath::Clamp(ThrowWindUpRemaining, 0.f, FMath::Max(0.f, RescueStep));
        ThrowWindUpRemaining -= Held;
        RescueStep -= Held;
        if (Held > 0.f && ThrowWindUpRemaining <= 0.f)
            if (const auto* Guide = FindAvatar(TEXT("guide")))
                ThrowReleaseWorldCm = Guide->GetActorTransform().TransformPosition(Guide->GetPublishedCrewPose().RightHandCm);
        ThrowFlightElapsed += RescueStep;
        RescueStep *= .45f / FMath::Max(ThrowFlightSeconds, .45f);
    }
    else if (bRope && bRopeSwimmerAtStation && RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling)
    {
        // Already alongside the guide's tube: settle them for the pull-in
        // rather than waiting out the haul clock of a longer throw.
        RescueStep *= 3.f;
    }
    RescueInteraction = URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
        RescueInteraction,
        StartM,
        Swimmer.SwimmerWorldPositionMeters,
        RescueStep);
    if (bRope && RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Failed)
    {
        // Missed: strip the line back in before another throw.
        RopeRecoverRemaining = 1.4f;
        return;
    }

    if (RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry)
    {
        ARaftSimCrewAvatarActor* SwimmerAvatar = FindAvatar(Swimmer.PassengerId);
        if (SwimmerAvatar)
            // Finish hauling against the SWIMMING body's contact envelope.
            // Switching to the shorter reentry pose before reaching that
            // envelope made drift push the swimmer out on every next tick.
            // On a rope they ride it on their back, head to the rescuer.
            SwimmerAvatar->SetAvatarAction(RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry && !bWasPulling
                ? ERaftSimCrewAvatarAction::Reentry
                : (bRope ? ERaftSimCrewAvatarAction::RopeTow : ERaftSimCrewAvatarAction::Swimming));
        FVector TubeTarget;
        if (!(bRope ? GetGuideHaulStation(Swimmer.PassengerId, Swimmer.SwimmerWorldPositionMeters, TubeTarget)
                : GetSwimmerTubeTarget(Swimmer.PassengerId, Swimmer.SwimmerWorldPositionMeters, TubeTarget))) return;
        const FVector Away = (TubeTarget - GetActorLocation() / kCmPerM).GetSafeNormal2D();
        const bool bAlreadyInsideEnvelope = !bRope &&
            FVector::DotProduct(Swimmer.SwimmerWorldPositionMeters - TubeTarget, Away) < 0.0;
        // A roped swimmer comes in on the guide's draws, never faster than
        // the 1.4 m/s haul and never in a timer jump.
        const float HaulSpeed = bRope ? 1.4f * GetHaulPullFraction() : 1.4f;
        Swimmer.SwimmerWorldPositionMeters = bAlreadyInsideEnvelope ? TubeTarget :
            Swimmer.SwimmerWorldPositionMeters + (TubeTarget-Swimmer.SwimmerWorldPositionMeters)
                .GetClampedToMaxSize(HaulSpeed * DeltaSeconds);
        bRopeSwimmerAtStation = bRope && FVector::Dist2D(Swimmer.SwimmerWorldPositionMeters, TubeTarget) <= .3;
        if (bRope && SwimmerAvatar && DeltaSeconds > 0.f)
        {
            // Head up the rope while towed; square to the tube once there.
            const FVector Look = RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling
                ? StartM - Swimmer.SwimmerWorldPositionMeters
                : GetActorLocation() / kCmPerM - TubeTarget;
            if (!Look.IsNearlyZero(1.e-3))
                SwimmerAvatar->SetActorRotation(FMath::RInterpTo(SwimmerAvatar->GetActorRotation(),
                    FRotator(0.f, Look.Rotation().Yaw, 0.f), DeltaSeconds, 5.f));
        }
        Swimmer.PullInProgress = RescueInteraction.PullProgress;
        Swimmer.RescueMethod = RescueInteraction.Method;
        if (RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry)
        {
            if (bWasPulling && FVector::Distance(Swimmer.SwimmerWorldPositionMeters, TubeTarget) > .15f)
            {
                RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Pulling;
                RescueInteraction.FeedbackCode = TEXT("rescue_pulling");
            }
            if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId);
                Avatar && RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry)
            {
                Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
            }
        }
        AttachSwimmerToWaterSurface(Swimmer);
        RescueInteraction.LineEndWorldMeters = Swimmer.SwimmerWorldPositionMeters;
        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId))
            Avatar->SetActorLocation(Swimmer.SwimmerWorldPositionMeters * kCmPerM);
    }
}

void ARaftSimRaftActor::CancelTimedBoarding()
{
    if (BoardingPassenger.IsNone()) return;
    if (auto* Avatar = FindAvatar(BoardingPassenger))
        Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
    // Release the interaction owner as well as the animation owner. Otherwise
    // the next rescue update reapplies ReadyForReentry and a request can restart
    // the cancelled transfer without a new rescue interaction.
    if (RescueInteraction.TargetPassengerId == BoardingPassenger)
        RescueInteraction = FRaftSimRescueInteractionState{};
    BoardingPassenger = NAME_None;
    BoardingElapsed = BoardingDuration = 0.f;
}

void ARaftSimRaftActor::UpdateTimedBoarding(float DeltaSeconds)
{
    const int32 Index = FindSwimmerIndex(BoardingPassenger);
    auto* Avatar = FindAvatar(BoardingPassenger);
    if (!Swimmers.IsValidIndex(Index) || !Avatar || RaftMode == ERaftSimRaftMode::Capsized)
    { CancelTimedBoarding(); return; }
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    BoardingElapsed = FMath::Min(BoardingDuration, BoardingElapsed + FMath::Min(DeltaSeconds, .25f));
    const float T = BoardingElapsed / BoardingDuration;
    const float ReachFraction = ARaftSimCrewAvatarActor::BoardingReachFraction;
    const bool bApproaching = T <= ReachFraction;
    const float PullFraction = ARaftSimCrewAvatarActor::BoardingLegOverFraction;
    const bool bPulling = T <= PullFraction;
    const float StageT = bApproaching ? T / ReachFraction :
        (bPulling ? 0.f : (T-PullFraction) / (1.f-PullFraction));
    const float Ease = StageT*StageT*(3.f-2.f*StageT);
    const FTransform& From = bApproaching ? BoardingStartLocal : BoardingReachLocal;
    const FTransform& To = bApproaching || bPulling ? BoardingReachLocal : BoardingSeatLocal;
    // The reach stage replaces the unsupported sine lift. The subsequent seat
    // transfer is still a review placeholder, NOT a qualified pull-over path.
    const FTransform Local(FQuat::Slerp(From.GetRotation(), To.GetRotation(), Ease),
        FMath::Lerp(From.GetLocation(), To.GetLocation(), Ease),
        FMath::Lerp(From.GetScale3D(), To.GetScale3D(), Ease));
    Avatar->SetActorTransform(Local * GetActorTransform());
    Avatar->SetBoardingTransferFrames(BoardingReachLocal.GetRelativeTransform(Local),
        BoardingSeatLocal.GetRelativeTransform(Local));
    Avatar->AdvanceBoardingPose(T);
    Swimmers[Index].SwimmerWorldPositionMeters = Avatar->GetActorLocation() / kCmPerM;
    if (T >= 1.f)
    {
        BoardingPassenger = NAME_None;
        BoardingElapsed = BoardingDuration = 0.f;
        ++CompletedRescueCount;
        RemoveSwimmerAt(Index);
    }
}

bool ARaftSimRaftActor::RequestSelectedReentry()
{
    if (RaftMode == ERaftSimRaftMode::Capsized || IsFlipLineActive()) return false;
    const int32 GuideIndex = FindSwimmerIndex(TEXT("guide"));
    if (Swimmers.IsValidIndex(GuideIndex))
    {
        const double GuideHullM = GetRenderedHullDistanceM(Swimmers[GuideIndex].SwimmerWorldPositionMeters);
        if (GuideHullM > 1.35)
        {
            UE_LOG(LogTemp, Display, TEXT("Guide boarding deferred: hull_distance_m=%.3f guide=%s raft=%s"),
                GuideHullM, *Swimmers[GuideIndex].SwimmerWorldPositionMeters.ToString(), *(GetActorLocation() / kCmPerM).ToString());
            return false;
        }
        SelectedSwimmerIndex = GuideIndex;
        RescueInteraction.TargetPassengerId = TEXT("guide");
        RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
    }
    if (!BoardingPassenger.IsNone()) return false;
    const int32 TargetIndex = FindSwimmerIndex(RescueInteraction.TargetPassengerId);
    if (!Swimmers.IsValidIndex(TargetIndex))
    {
        return false;
    }
    // "Bring to tube" measures the actual rendered hull, not the raft center.
    // The library's unchanged1.35m distance and readiness gates still apply.
    const float DistanceM = GetRenderedHullDistanceM(Swimmers[TargetIndex].SwimmerWorldPositionMeters);
    const auto PreviousInteraction = RescueInteraction;
    RescueInteraction = URaftSimSwimmerRescueLibrary::CompleteReseat(RescueInteraction, DistanceM);
    if (RescueInteraction.Phase != ERaftSimRescueInteractionPhase::Completed)
    {
        UE_LOG(LogTemp, Display, TEXT("Rescue boarding deferred: distance_m=%.6f phase=%d reason=%s"),
            DistanceM, int(PreviousInteraction.Phase), *RescueInteraction.FeedbackCode.ToString());
        return false;
    }
    if (IsGuideBusyWithBoarding())
    {
        // One pull-in at a time: the guide's hands are on the last swimmer.
        RescueInteraction = PreviousInteraction;
        RescueInteraction.FeedbackCode = TEXT("rescue_boarding_in_progress");
        return false;
    }
    // Integrated review only until continuous rendered clearance is qualified.
    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimTimedReentryReview")))
    {
        auto* Avatar = FindAvatar(Swimmers[TargetIndex].PassengerId);
        if (!Avatar) { RescueInteraction = PreviousInteraction; return false; }
        const FTransform StartWorld = Avatar->GetActorTransform();
        const auto StartPose = Avatar->GetPublishedCrewPose();
        FVector LeftSupport, RightSupport;
        if (!StartWorld.IsValid() || !FindBoardingTubeSupports(StartWorld.GetLocation(),
            FVector::Distance(StartPose.LeftHandCm, StartPose.RightHandCm), LeftSupport, RightSupport))
        { RescueInteraction = PreviousInteraction; return false; }
        BoardingStartLocal = StartWorld.GetRelativeTransform(GetActorTransform());
        const FVector Right = (RightSupport-LeftSupport).GetSafeNormal();
        const FVector Forward = FVector::CrossProduct(Right, FVector::UpVector).GetSafeNormal();
        const FQuat ReachRotation = FRotationMatrix::MakeFromXY(Forward, Right).ToQuat();
        // Authored palm-center clearance, not measured skin or grip geometry.
        LeftSupport += FVector::UpVector * 3.; RightSupport += FVector::UpVector * 3.;
        BoardingReachLocal = FTransform(ReachRotation, FVector::ZeroVector, BoardingStartLocal.GetScale3D());
        const FVector HandMid = (StartPose.LeftHandCm+StartPose.RightHandCm)*.5;
        BoardingReachLocal.SetLocation((LeftSupport+RightSupport)*.5 - BoardingReachLocal.TransformVector(HandMid));
        auto ReachPose = StartPose;
        ReachPose.LeftHandCm = BoardingReachLocal.InverseTransformPosition(LeftSupport);
        ReachPose.RightHandCm = BoardingReachLocal.InverseTransformPosition(RightSupport);
        auto PullPose = ReachPose;
        const FVector ReachHands = (ReachPose.LeftHandCm+ReachPose.RightHandCm)*.5;
        // Authored intermediate posture: torso just inboard of the hands,
        // legs still outboard. This is not a measured or force-solved climb.
        const FVector TorsoShift(ReachHands.X+5.-ReachPose.TorsoCenterCm.X, 0.,
            ReachHands.Z+20.-ReachPose.TorsoCenterCm.Z);
        PullPose.TorsoCenterCm += TorsoShift;
        PullPose.HeadCenterCm += TorsoShift;
        PullPose.LeftShoulderCm += TorsoShift; PullPose.RightShoulderCm += TorsoShift;
        PullPose.LeftHipCm += TorsoShift; PullPose.RightHipCm += TorsoShift;
        const auto OutsideLeg = [](const FVector& OldHip, const FVector& OldKnee, const FVector& OldFoot,
            const FVector& Hip, FVector& Knee, FVector& Foot)
        {
            Knee = Hip + FVector(-.6,0.,-.8) * FVector::Distance(OldHip,OldKnee);
            Foot = Knee + FVector(-.4,0.,-FMath::Sqrt(.84)) * FVector::Distance(OldKnee,OldFoot);
        };
        OutsideLeg(ReachPose.LeftHipCm,ReachPose.LeftKneeCm,ReachPose.LeftFootCm,
            PullPose.LeftHipCm,PullPose.LeftKneeCm,PullPose.LeftFootCm);
        OutsideLeg(ReachPose.RightHipCm,ReachPose.RightKneeCm,ReachPose.RightFootCm,
            PullPose.RightHipCm,PullPose.RightKneeCm,PullPose.RightFootCm);
        auto LiftPose = PullPose;
        auto LegOverPose = PullPose;
        // Lift outside before crossing the tube. Height is an authored review
        // target, not a clearance guarantee; strict rendered-boot audit remains.
        const double FootZ = ReachHands.Z + 25.;
        LiftPose.LeftFootCm.Z = LiftPose.RightFootCm.Z = FootZ;
        LegOverPose.LeftFootCm = FVector(ReachHands.X-10., PullPose.LeftHipCm.Y, FootZ);
        LegOverPose.RightFootCm = FVector(ReachHands.X-10., PullPose.RightHipCm.Y, FootZ);
        const auto PrepareLeg = [](const FVector& Hip, const FVector& OldKnee, const FVector& OldFoot,
            const FVector& LiftFoot, const FVector& OverFoot, double Side, FVector& LiftKnee, FVector& OverKnee)
        {
            const double Thigh = FVector::Distance(Hip,OldKnee), Shin = FVector::Distance(OldKnee,OldFoot);
            const auto Fits = [&](const FVector& A, const FVector& B)
            {
                const FVector Delta=B-A;
                const double T=Delta.IsNearlyZero() ? 0. : FMath::Clamp(FVector::DotProduct(Hip-A,Delta)/Delta.SizeSquared(),0.,1.);
                return FVector::Distance(Hip,A+Delta*T) > FMath::Abs(Thigh-Shin)+.001 &&
                    FMath::Max(FVector::Distance(Hip,A),FVector::Distance(Hip,B)) < Thigh+Shin-.001;
            };
            const FVector Hint(0,Side*Thigh,0);
            return Fits(OldFoot,LiftFoot) && Fits(LiftFoot,OverFoot) &&
                RaftSimCrewBoarding::SolveLeg(Hip,LiftFoot,Thigh,Shin,Hint,LiftKnee) &&
                RaftSimCrewBoarding::SolveLeg(Hip,OverFoot,Thigh,Shin,Hint,OverKnee);
        };
        if (!PrepareLeg(PullPose.LeftHipCm,PullPose.LeftKneeCm,PullPose.LeftFootCm,
            LiftPose.LeftFootCm,LegOverPose.LeftFootCm,-1.,LiftPose.LeftKneeCm,LegOverPose.LeftKneeCm) ||
            !PrepareLeg(PullPose.RightHipCm,PullPose.RightKneeCm,PullPose.RightFootCm,
            LiftPose.RightFootCm,LegOverPose.RightFootCm,1.,LiftPose.RightKneeCm,LegOverPose.RightKneeCm))
        { RescueInteraction = PreviousInteraction; return false; }
        // Resolve the same fitted destination used by completion, without a
        // world tick or ownership/mass transfer between preparation and restore.
        AttachAvatarToSeat(Avatar, Swimmers[TargetIndex].PassengerId);
        BoardingSeatLocal = Avatar->GetActorTransform().GetRelativeTransform(GetActorTransform());
        const auto EndPose = Avatar->GetPublishedCrewPose();
        Avatar->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        Avatar->SetActorTransform(StartWorld);
        Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
        Avatar->SetBoardingPose(StartPose, EndPose, 0.f);
        Avatar->SetBoardingReachPose(ReachPose);
        Avatar->SetBoardingPullPose(PullPose);
        Avatar->SetBoardingLegOverPoses(LiftPose, LegOverPose);
        BoardingPassenger = Swimmers[TargetIndex].PassengerId;
        BoardingElapsed = 0.f;
        BoardingDuration = FMath::Max(4.f, float((FVector::Distance(
            BoardingStartLocal.GetLocation(), BoardingReachLocal.GetLocation()) + FVector::Distance(
            BoardingReachLocal.GetLocation(), BoardingSeatLocal.GetLocation())) / 80.));
        RescueInteraction = PreviousInteraction;
        RescueInteraction.bLineVisible = false;
        RescueInteraction.FeedbackCode = TEXT("rescue_climbing");
        return true;
    }
    // The seat and its mass are restored now; the visible pull-in over the
    // tube (by the PFD straps, or a self-rescue climb) plays out after.
    const FName Boarded = Swimmers[TargetIndex].PassengerId;
    ARaftSimCrewAvatarActor* BoardedAvatar = FindAvatar(Boarded);
    const FTransform StartWorld = BoardedAvatar ? BoardedAvatar->GetActorTransform() : FTransform::Identity;
    const FRaftSimCrewAvatarPose StartPose = BoardedAvatar ? BoardedAvatar->GetPublishedCrewPose() : FRaftSimCrewAvatarPose{};
    ++CompletedRescueCount;
    RemoveSwimmerAt(TargetIndex);
    if (BoardedAvatar) BeginAssistedBoarding(BoardedAvatar, Boarded, StartWorld, StartPose);
    return true;
}

void ARaftSimRaftActor::RemoveSwimmerAt(int32 Index)
{
    if (!Swimmers.IsValidIndex(Index))
    {
        return;
    }
    const FName PassengerId = Swimmers[Index].PassengerId;
    if (PassengerId == BoardingPassenger) CancelTimedBoarding();
    if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(PassengerId))
    {
        AttachAvatarToSeat(Avatar, PassengerId);
    }
    Swimmers.RemoveAt(Index);
    RefreshCrewSeatOccupancy();
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
    if (PassengerId == TEXT("guide") && IsFlipLineActive() && !bFlipGuideReleased) return;
    const int32 Index = FindSwimmerIndex(PassengerId);
    if (!Swimmers.IsValidIndex(Index) || WorldDirection.ContainsNaN())
    {
        return;
    }
    Swimmers[Index].SwimmerWorldPositionMeters +=
        WorldDirection.GetSafeNormal2D() * FMath::Clamp(DistanceM, 0.0f, 0.65f);
    if (!WorldDirection.GetSafeNormal2D().IsNearlyZero())
        if (auto* Avatar = FindAvatar(PassengerId))
            Avatar->SetActorRotation(FRotator(0,WorldDirection.Rotation().Yaw,0));
}

void ARaftSimRaftActor::ForceCrewOverboardForTesting(int32 Count)
{
    SpawnSwimmers(Count, false);
}

void ARaftSimRaftActor::ResetToCheckpoint()
{
    TryResetToCheckpoint();
}

void ARaftSimRaftActor::SetCheckpointPreparation(FRaftSimCheckpointPreparation Preparation)
{
    CheckpointPreparation=MoveTemp(Preparation);
    // A destroyed scenario owner must not silently fall back to an unprepared
    // teleport. Worlds that never install a handler retain legacy tank resets.
    bCheckpointPreparationRequired=true;
}

bool ARaftSimRaftActor::TryResetToCheckpoint()
{
    return TryRestoreCheckpoint(CheckpointTransform);
}

bool ARaftSimRaftActor::TryRestoreCheckpoint(const FTransform& Destination)
{
    if (!Destination.IsValid() || bCheckpointResetInProgress) return false;
    TGuardValue<bool> ResetGuard(bCheckpointResetInProgress,true);
    FTransform Prepared=Destination;
    if (bCheckpointPreparationRequired &&
        (!CheckpointPreparation.IsBound() || !CheckpointPreparation.Execute(Prepared)))
    {
        UE_LOG(LogTemp,Display,TEXT("CHECKPOINT_RESET_REJECTED destination unavailable; raft and crew retained"));
        return false;
    }
    if (!Prepared.IsValid()) return false;
    // No crew repair, pose, velocity or saved checkpoint changes until the
    // scenario has activated terrain and verified destination water.
    CancelTimedBoarding();
    FinishAssistedBoarding();
    CheckpointTransform=Prepared;
    CancelFlipLine();
    RopeRecoverRemaining = ThrowWindUpRemaining = 0.f;
    bThrowBagDeployed = false;
    if (auto* Guide = FindAvatar(TEXT("guide")); Guide && Guide->GetAttachParentActor() == this)
    {
        if (bGuideRescuePoseActive) Guide->ClearExternalPose();
        if (!Guide->HasHighSideTransfer()) Guide->SetActorRelativeRotation(FRotator::ZeroRotator);
    }
    bGuideRescuePoseActive = false;
    GuideRescueYawDeg = 0.f;
    for (const FRaftSimSwimmerRescueFrame& Swimmer : Swimmers)
    {
        if (ARaftSimCrewAvatarActor* Avatar = FindAvatar(Swimmer.PassengerId))
        {
            AttachAvatarToSeat(Avatar, Swimmer.PassengerId);
        }
    }
    Swimmers.Reset();
    PassengerWashImpulseNs.Reset();
    PassengerSwampedSeconds.Reset();
    RescueInteraction = FRaftSimRescueInteractionState{};
    SelectedSwimmerIndex = INDEX_NONE;
    RescueFailureResetRemaining = -1.0f;
    RaftMode = ERaftSimRaftMode::Upright;
    RefreshCrewSeatOccupancy();
    FlipRiskLatchSeconds = 0.0f;
    CapsizeTransitionRemainingSeconds = 0.0f;
    SetActorTransform(CheckpointTransform);
    RaftCondition = URaftSimRaftConditionLibrary::ApplyCheckpointRepair(RaftCondition);
    if (RaftAdapter)
    {
        RaftAdapter->SetFlexibleCapsized(false);
        RaftAdapter->ResetFlexiblePersistentState();
        FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
        State.WorldTransform = CheckpointTransform;
        // Checkpoint restores happen in the river, not in an inertial vacuum.
        // Rejoin the local current immediately so the reset boat and the
        // solver-advected foam retain the same passive drift speed.
        State.LinearVelocityMetersPerSecond =
            SampleWaterVelocityMps(CheckpointTransform.GetLocation());
        State.LinearVelocityMetersPerSecond.Z = 0.0f;
        State.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
        RaftAdapter->SetKinematicState(State);
        if (Bridge) Bridge->ClearRaftStepFailureAfterRestore();
    }
    ++CheckpointRestoreCount;
    return true;
}

void ARaftSimRaftActor::SetCheckpointTransform(
    FTransform NewCheckpoint, bool bRestoreImmediately)
{
    if (!NewCheckpoint.IsValid())
    {
        return;
    }
    if (bRestoreImmediately)
    {
        TryRestoreCheckpoint(NewCheckpoint);
    }
    else CheckpointTransform = NewCheckpoint;
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

FVector ARaftSimRaftActor::SampleWaterVelocityMps(const FVector& WorldLocationCm) const
{
#if !UE_BUILD_SHIPPING
    if(RaftAdapter && (!Bridge || RaftAdapter!=Bridge->GetRaftRuntime()))
    {
        FRaftSimFlexUniformWater Field;
        if(RaftAdapter->SampleBoundFlexibleWater(WorldLocationCm,Field) && Field.bWet && !Field.VelocityMps.ContainsNaN())
            return Field.VelocityMps.GetClampedToMaxSize(12.);
        return FVector::ZeroVector;
    }
#endif
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
    if (RaftMode != ERaftSimRaftMode::Capsized || IsFlipLineActive() || !RaftAdapter) return;
    const int32 GuideIndex = FindSwimmerIndex(TEXT("guide"));
    if (!Swimmers.IsValidIndex(GuideIndex) || GetActorUpVector().Z > -.5f ||
        GetRenderedHullDistanceM(Swimmers[GuideIndex].SwimmerWorldPositionMeters) > 1.35) return;
    FlipClimbStartLocalCm = GetActorTransform().InverseTransformPosition(
        Swimmers[GuideIndex].SwimmerWorldPositionMeters * 100.);
    FlipLineSide = FlipClimbStartLocalCm.Y < 0. ? -1.f : 1.f;
    FlipWaterWorldZCm = float(Swimmers[GuideIndex].SwimmerWorldPositionMeters.Z * 100.);
    FlipPullFacing = FVector::ZeroVector;
    if (!PrepareFlipLineStations()) return;
    FlipLinePhase = ERaftSimFlipLinePhase::Climbing;
    FlipLineSeconds = FlipLineLogSeconds = 0.f;
    bFlipGuideReleased = bFlipLineClipped = false;
    RescueInteraction = FRaftSimRescueInteractionState{};
    if (auto* Guide = FindAvatar(TEXT("guide"))) Guide->ResetHighSideTransfer();
}

void ARaftSimRaftActor::HandleHighSideResponse(int32 Direction)
{
    if (RaftAdapter == nullptr || Direction == 0 || RaftMode != ERaftSimRaftMode::Upright)
    {
        return;
    }
    // The dedicated response key is immediate (unlike a delayed crew call),
    // but must still update the same visible and physical participants and
    // persist as an order instead of being erased by the next ordinary tick.
    IssueCrewCommand(ERaftSimCrewCommand::HighSide);
    ActiveCrewCommand = PendingCrewCommand = ERaftSimCrewCommand::HighSide;
    CrewReactionRemaining = 0.0f;
    CrewHighSideDirection = FMath::Clamp(Direction, -1, 1);
    CrewStrokePhase = 0.0f;
    LastCrewStrokeImpulsePhase = -1.0f;
    UpdateCrew(0.0f);
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
    ManualOarIntents = TransientOarIntents = FVector2D::ZeroVector;
    TransientOarSeconds = OarSteerSeconds = 0.f;
    RefreshOarCommandIntents();
    CrewReactionRemaining = 0.0f;
    CrewStrokePhase = 0.0f;
    LastCrewStrokeImpulsePhase = -1.0f;
}

void ARaftSimRaftActor::TeleportForTesting(
    const FVector& WorldLocationCm,
    float FacingYawDegrees,
    bool bApplyFacing)
{
    const FQuat Facing = bApplyFacing
        ? FRotator(0.0f, FacingYawDegrees, 0.0f).Quaternion()
        : GetActorQuat();
    if (RaftAdapter != nullptr)
    {
        FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
        State.WorldTransform.SetTranslation(WorldLocationCm);
        State.WorldTransform.SetRotation(Facing);
        RaftAdapter->SetKinematicState(State);
    }
    SetActorLocationAndRotation(WorldLocationCm, Facing);
    ResetMotionForTesting();
}
