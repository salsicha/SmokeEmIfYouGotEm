#include "RaftSimRaftActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Components/LightComponent.h"
#include "Engine/DirectionalLight.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
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
#include "UnrealClient.h"
#include "RaftSimRiverbedActor.h"
#include "RaftSimWaterVfxActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "UObject/ConstructorHelpers.h"

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
        Command == ERaftSimCrewCommand::TurnRight;
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
    // Deterministic stepping and replay hashes remain available, but gameplay
    // must not append a JSON line to disk on every fixed water tick. Validation
    // tools opt into capture explicitly when they need an audit artifact.
    WaterConfig.bEnableDeterministicCapture = false;

    // The rigid-body support stage integrates one combined body, so its mass
    // and inertia must include the occupied crew represented by D2. The flex
    // model below keeps MassKg as the dry raft mass and applies the same crew
    // masses to tube compression; using dry mass here made moving-water rafts
    // settle far below their loaded waterline and admit runaway deck water.
    const float LoadedBodyMassKg =
        MassKg + kGuideMassKg + kPassengerMassKg * static_cast<float>(PaddlerCount);
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
                    /*RoughnessManning=*/0.041f,
                    RiverConfig->bRecenterHydraulicCrux);
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
    FlexParameters.GuideMassKg = kGuideMassKg;
    FlexParameters.PassengerMassKg = kPassengerMassKg;
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
    const TArray<FLinearColor> NoColors;
    ProductionRaftRestSections.Reset();
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
        bUsingProductionRaftRestMesh =
            RaftSimRaftMesh::ExtractProductionRaftRestMesh(
                ProductionMesh, ProductionRaftRestSections);
    }

    TArray<RaftSimRaftMesh::FMeshData> FallbackSections;
    TArray<RaftSimRaftMesh::FMeshData>* Sections = &FallbackSections;
    if (bUsingProductionRaftRestMesh)
    {
        RaftSimRaftMesh::DeformProductionRaftRestMesh(
            ProductionRaftRestSections,
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
}

void ARaftSimRaftActor::UpdateFlexibleRaftVisual()
{
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
            ProductionRaftRestSections,
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
    // An explicit call (number keys / command wheel) owns the command until
    // changed; guide-paddle cadence ownership ends here.
    bCrewCommandFromGuidePaddle = false;
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
            const ERaftSimCrewCommand PreviousCommand = ActiveCrewCommand;
            ActiveCrewCommand = PendingCrewCommand;
            if (ActiveCrewCommand != PreviousCommand)
            {
                // The visual stroke starts at its catch on this same command
                // transition. Deliver the discrete reduced-model impulse near
                // peak blade speed in the power phase, then repeat on the
                // shared 0.8 s cadence instead of free-running a hidden timer
                // while the crew rests.
                constexpr float PowerImpulsePhase = 0.29f;
                CrewStrokeTimer = IsPropulsiveCrewCommand(ActiveCrewCommand)
                    ? FMath::Max(
                        CrewStrokeIntervalSeconds * PowerImpulsePhase,
                        FixedSubstepSeconds)
                    : 0.0f;
            }
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
    for (int32 Index = 0; Index < CrewAvatars.Num(); ++Index)
    {
        ARaftSimCrewAvatarActor* Avatar = CrewAvatars[Index];
        if (!Avatar || Avatar->GetAttachParentActor() != this)
        {
            continue;
        }
        // The stern (last) avatar is the guide; its own recent stroke wins
        // over the crew command so player inputs read on the body.
        const bool bGuideAvatar = Index == CrewAvatars.Num() - 1;
        Avatar->SetAvatarAction(
            bGuideAvatar && GuideStrokeActionSeconds > 0.0f
                ? GuideStrokeAction
                : AvatarAction);
    }

    // Paddle strokes on cadence for propulsion/turn commands. Rest, brace and
    // emergency weight-shift poses do not advance an invisible paddle cycle.
    if (!IsPropulsiveCrewCommand(ActiveCrewCommand))
    {
        CrewStrokeTimer = 0.0f;
        return;
    }
    CrewStrokeTimer -= DeltaSeconds;
    if (CrewStrokeTimer > 0.0f)
    {
        return;
    }
    CrewStrokeTimer = FMath::Max(
        CrewStrokeTimer + CrewStrokeIntervalSeconds,
        FixedSubstepSeconds);

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
    GuideStrokeAction = Scale >= 0.0f
        ? ERaftSimCrewAvatarAction::ForwardStroke
        : ERaftSimCrewAvatarAction::BackStroke;
    GuideStrokeActionSeconds = 1.0f;
    // The guide's call is the crew's stroke: W/S cadence puts the whole
    // crew on forward/back paddle while strokes keep coming, and they rest
    // when the guide stops — unless an explicit command (number keys /
    // wheel) owns the crew (2026-08-10 playtest: "the crew are the ones
    // who are supposed to paddle").
    const ERaftSimCrewCommand CadenceCommand = Scale >= 0.0f
        ? ERaftSimCrewCommand::AllForward
        : ERaftSimCrewCommand::AllBackward;
    if (ActiveCrewCommand == ERaftSimCrewCommand::Rest ||
        bCrewCommandFromGuidePaddle)
    {
        IssueCrewCommand(CadenceCommand);
        bCrewCommandFromGuidePaddle = true;
    }
    GuidePaddleCommandSeconds = 1.4f;
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
    ++PaddleStrokeCount;
    GuideStrokeAction = Scale > 0.0f
        ? ERaftSimCrewAvatarAction::TurnRight
        : ERaftSimCrewAvatarAction::TurnLeft;
    GuideStrokeActionSeconds = 1.0f;
}

void ARaftSimRaftActor::SetGuideFirstPersonView(bool bFirstPerson)
{
    if (ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide")))
    {
        Guide->SetFirstPersonHeadHidden(bFirstPerson);
    }
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
    Super::Tick(DeltaSeconds);
    if (Bridge == nullptr || RaftAdapter == nullptr)
    {
        return;
    }

    // Throttled drift telemetry: raft speed against the sampled current at
    // the hull. This is the direct instrument for "the river does not carry
    // the boat" reports — if water_speed is real and raft_speed stays near
    // zero without input, the water-to-hull drag coupling is the defect.
    DriftTelemetrySeconds += DeltaSeconds;
    if (DriftTelemetrySeconds >= 10.0f)
    {
        DriftTelemetrySeconds = 0.0f;
        float WaterSpeedMps = 0.0f;
        float SurfaceZCm = 0.0f;
        bool bHullWet = false;
        if (const URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
        {
            FRaftSimWaterSample Sample;
            if (Water->SampleWaterAtWorldPosition(GetActorLocation(), Sample))
            {
                bHullWet = Sample.bWet;
                SurfaceZCm = Sample.SurfaceHeightMeters * 100.0f;
                if (Sample.bWet)
                {
                    WaterSpeedMps = Sample.VelocityMetersPerSecond.Size2D();
                }
            }
        }
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
            TEXT("raft_z_cm=%.1f surface_z_cm=%.1f wet=%d retained_kg=%.0f ")
            TEXT("pressure=%.2f integrity=%.2f dry_points=%d x_cm=%.0f y_cm=%.0f ")
            TEXT("sun_pitch=%.1f sun_intensity=%.1f"),
            GetRaftVelocity().Size(),
            WaterSpeedMps,
            GetActorLocation().Z,
            SurfaceZCm,
            bHullWet ? 1 : 0,
            GetD3RetainedWaterMassKg(),
            RaftCondition.PressureFraction,
            RaftCondition.FabricIntegrity,
            RaftAdapter->GetLastDrySupportPointCount(),
            GetActorLocation().X,
            GetActorLocation().Y,
            SunPitchDeg,
            SunIntensityLux);
    }

    RockObstacleRefreshRemaining -= DeltaSeconds;
    if (RockObstacleRefreshRemaining <= 0.0f)
    {
        UpdateRockObstacles();
        RockObstacleRefreshRemaining = 0.05f;
    }

    FRaftSimPhysicsTickInput Input;
    Input.FrameDeltaSeconds = FMath::Min(DeltaSeconds, 0.25f);
    FRaftSimPhysicsTickOutput Output;
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_PhysicsBridgeTick);
        Output = Bridge->TickBridge(Input);
    }
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

    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_CapsizeUpdate);
        UpdateCapsizeTransition(FMath::Min(DeltaSeconds, 0.25f));
        UpdateCapsizeLoop(FMath::Min(DeltaSeconds, 0.25f));
    }
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_CrewUpdate);
        UpdateCrew(FMath::Min(DeltaSeconds, 0.25f));
    }
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimRaft_RescueUpdate);
        UpdateRescueInteraction(FMath::Min(DeltaSeconds, 0.25f));
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

void ARaftSimRaftActor::UpdateCapsizeTransition(float DeltaSeconds)
{
    if (RaftMode != ERaftSimRaftMode::Capsized ||
        CapsizeTransitionRemainingSeconds <= 0.0f || RaftAdapter == nullptr)
    {
        return;
    }
    const float Duration = FMath::Max(CapsizeTransitionSeconds, FixedSubstepSeconds);
    CapsizeTransitionRemainingSeconds = FMath::Max(
        0.0f, CapsizeTransitionRemainingSeconds - FMath::Max(DeltaSeconds, 0.0f));
    const float Alpha = FMath::Clamp(
        1.0f - CapsizeTransitionRemainingSeconds / Duration, 0.0f, 1.0f);
    const float SmoothAlpha = Alpha * Alpha * (3.0f - 2.0f * Alpha);
    const FRotator LiveRotation = GetActorRotation();
    const float TransitionPitchDegrees =
        FMath::Lerp(CapsizeStartPitchDegrees, 0.0f, SmoothAlpha);
    const float TransitionRollDegrees = FMath::Lerp(
        CapsizeStartRollDegrees, CapsizeFlipDirection * 180.0f, SmoothAlpha);
    const FQuat TransitionRotation = FRotator(
        TransitionPitchDegrees, LiveRotation.Yaw, TransitionRollDegrees).Quaternion();
    CapsizeTargetRotation = FRotator(
        0.0f, LiveRotation.Yaw, CapsizeFlipDirection * 180.0f).Quaternion();
    CapsizeRollAxisWorld = TransitionRotation.GetForwardVector().GetSafeNormal();
    const float AngularSpeedRadiansPerSecond = CapsizeFlipDirection * PI *
        (6.0f * Alpha * (1.0f - Alpha)) / Duration;

    // The reduced rigid-body model does not resolve the air/water volume that
    // carries a real raft through the unstable side-on phase. D3 decides when
    // and which way the boat overturns; this bounded authoritative constraint
    // advances that unresolved roll while the adapter continues integrating
    // translation, buoyancy, drag and D4 contacts from the matching pose/rate.
    SetActorRotation(TransitionRotation);
    FRaftSimRaftKinematicState State = RaftAdapter->GetKinematicState();
    State.WorldTransform.SetTranslation(GetActorLocation());
    State.WorldTransform.SetRotation(TransitionRotation);
    State.AngularVelocityRadiansPerSecond = CapsizeRollAxisWorld *
        AngularSpeedRadiansPerSecond;
    if (CapsizeTransitionRemainingSeconds <= 0.0f)
    {
        State.WorldTransform.SetRotation(CapsizeTargetRotation.GetNormalized());
        State.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
        SetActorRotation(CapsizeTargetRotation.GetNormalized());
    }
    RaftAdapter->SetKinematicState(State);
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
    const FRaftSimFlexStepTelemetry EntryTelemetry = RaftAdapter
        ? RaftAdapter->GetLastFlexibleStepTelemetry()
        : FRaftSimFlexStepTelemetry{};
    UE_LOG(
        LogTemp,
        Warning,
        TEXT("RaftSim capsize: raft=%s location_cm=%s rotation_deg=%s "
             "flip_margin_nm=%.3f flip_threshold_nm=%.3f retained_water_kg=%.3f "
             "retained_roll_moment_nm=%.3f wet_samples=%d/%d contacts=%d "
             "wrapping=%d pinned=%d"),
        *GetName(),
        *GetActorLocation().ToCompactString(),
        *GetActorRotation().ToCompactString(),
        EntryTelemetry.ReferenceFlipMarginNm,
        EntryTelemetry.ReferenceFlipThresholdNm,
        EntryTelemetry.TotalRetainedWaterMassKg,
        EntryTelemetry.RetainedWaterRollMomentNm,
        EntryTelemetry.LiveWetSampleCount,
        EntryTelemetry.LiveWaterSampleCount,
        EntryTelemetry.ContactCount,
        EntryTelemetry.WrappingContactCount,
        EntryTelemetry.PinnedObstacleCount);
    RaftMode = ERaftSimRaftMode::Capsized;
    FlipRiskLatchSeconds = 0.0f;
    // Right the boat here on re-flip. Guard against a diverged sink so the
    // recovery point stays near where the crew went overboard.
    CapsizeLocation = GetActorLocation();
    CapsizeLocation.Z = FMath::Clamp(CapsizeLocation.Z, -200.0f, 200.0f);

    if (RaftAdapter != nullptr)
    {
        // An open-floor paddle raft sheds retained deck water and crew mass
        // when it rolls over. Keep the current authoritative pose and establish
        // the D3-selected direction for the bounded roll constraint; every
        // transition frame is copied back into this same adapter state.
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
        State.AngularVelocityRadiansPerSecond = FVector::ZeroVector;
        RaftAdapter->SetKinematicState(State);
        CapsizeTransitionRemainingSeconds = FMath::Max(
            CapsizeTransitionSeconds, FixedSubstepSeconds);
    }

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
    CapsizeTransitionRemainingSeconds = 0.0f;
    SetActorTransform(CheckpointTransform);
    RaftCondition = URaftSimRaftConditionLibrary::ApplyCheckpointRepair(RaftCondition);
    if (RaftAdapter)
    {
        RaftAdapter->SetFlexibleCapsized(false);
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
    // The guide and boat continue downstream after a capsize. Re-right the
    // hull where the guide is now swimming instead of teleporting it back to
    // the stale capsize point; this keeps the crew reachable when the live
    // hydraulic field carries them through fast current.
    FVector ReflipLocation = CapsizeLocation;
    const int32 GuideIndex = FindSwimmerIndex(TEXT("guide"));
    if (Swimmers.IsValidIndex(GuideIndex))
    {
        const FVector GuideWorldCm =
            Swimmers[GuideIndex].SwimmerWorldPositionMeters * kCmPerM;
        if (IsFiniteVector(GuideWorldCm))
        {
            ReflipLocation.X = GuideWorldCm.X;
            ReflipLocation.Y = GuideWorldCm.Y;
        }
    }

    // Drain retained water and begin reseating swimmers around the guide.
    RaftMode = ERaftSimRaftMode::Recovering;
    CapsizeTransitionRemainingSeconds = 0.0f;
    SetActorLocationAndRotation(
        ReflipLocation, FRotator(0.0f, GetActorRotation().Yaw, 0.0f));
    if (RaftAdapter != nullptr)
    {
        RaftAdapter->SetFlexibleCapsized(false);
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
