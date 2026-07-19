#include "RaftSimWaterVfxActor.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInterface.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float CmPerM = 100.0f;
constexpr float GravityMps2 = 9.80665f;

float DeterministicWave(int32 Index, float Phase, float Frequency)
{
    return 0.5f + 0.5f * FMath::Sin(
        Phase * Frequency + static_cast<float>(Index) * 2.39996323f);
}

void ConfigureVfxComponent(
    UHierarchicalInstancedStaticMeshComponent* Component,
    UStaticMesh* Mesh,
    UMaterialInterface* Material)
{
    if (!Component)
    {
        return;
    }
    Component->SetStaticMesh(Mesh);
    Component->SetMaterial(0, Material);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCastShadow(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetMobility(EComponentMobility::Movable);
}
}

ARaftSimWaterVfxActor::ARaftSimWaterVfxActor()
{
    PrimaryActorTick.bCanEverTick = true;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    SprayInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("SolverSpray"));
    SprayInstances->SetupAttachment(Root);
    MistInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("AeratedMist"));
    MistInstances->SetupAttachment(Root);
    SheetInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("RaftImpactSheets"));
    SheetInstances->SetupAttachment(Root);
    DropletInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("ContactDroplets"));
    DropletInstances->SetupAttachment(Root);

    UnderwaterPostProcess = CreateDefaultSubobject<UPostProcessComponent>(
        TEXT("UnderwaterPostProcess"));
    UnderwaterPostProcess->SetupAttachment(Root);
    UnderwaterPostProcess->bUnbound = true;
    UnderwaterPostProcess->BlendWeight = 0.0f;
    FPostProcessSettings& Underwater = UnderwaterPostProcess->Settings;
    Underwater.bOverride_SceneColorTint = true;
    Underwater.SceneColorTint = FLinearColor(0.34f, 0.62f, 0.64f, 1.0f);
    Underwater.bOverride_ColorSaturation = true;
    Underwater.ColorSaturation = FVector4(0.48f, 0.72f, 0.78f, 1.0f);
    Underwater.bOverride_ColorContrast = true;
    Underwater.ColorContrast = FVector4(0.82f, 0.88f, 0.92f, 1.0f);
    Underwater.bOverride_VignetteIntensity = true;
    Underwater.VignetteIntensity = 0.52f;
    Underwater.bOverride_SceneFringeIntensity = true;
    Underwater.SceneFringeIntensity = 1.6f;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(
        TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(
        TEXT("/Engine/BasicShapes/Plane.Plane"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SprayMaterial(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist.M_RaftSim_SprayMist"));
    UStaticMesh* SphereMesh = Sphere.Succeeded() ? Sphere.Object : nullptr;
    UStaticMesh* PlaneMesh = Plane.Succeeded() ? Plane.Object : nullptr;
    UMaterialInterface* Material =
        SprayMaterial.Succeeded() ? SprayMaterial.Object : nullptr;
    ConfigureVfxComponent(SprayInstances, SphereMesh, Material);
    ConfigureVfxComponent(MistInstances, SphereMesh, Material);
    ConfigureVfxComponent(SheetInstances, PlaneMesh, Material);
    ConfigureVfxComponent(DropletInstances, SphereMesh, Material);
}

void ARaftSimWaterVfxActor::BeginPlay()
{
    Super::BeginPlay();
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            WaterAdapter = Bridge->GetWaterRuntime();
        }
    }
    if (UWorld* World = GetWorld())
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            TrackedRaft = *It;
        }
    }
}

FRaftSimWaterVfxState ARaftSimWaterVfxActor::EvaluatePresentation(
    const FRaftSimWaterSample& Sample,
    const FVector& RaftVelocityMps,
    int32 ContactCount,
    float MaximumIndentationM,
    bool bCameraUnderwater)
{
    FRaftSimWaterVfxState Result;
    if (!Sample.bWet)
    {
        Result.Underwater = bCameraUnderwater ? 1.0f : 0.0f;
        return Result;
    }

    const float DepthM = FMath::Max(Sample.DepthMeters, 0.05f);
    const float WaterSpeedMps = Sample.VelocityMetersPerSecond.Size2D();
    const float Froude = WaterSpeedMps / FMath::Sqrt(GravityMps2 * DepthM);
    const float HydraulicAeration = FMath::Clamp((Froude - 0.72f) / 1.05f, 0.0f, 1.0f);
    const float RelativeImpact = FMath::Clamp(
        (Sample.VelocityMetersPerSecond - RaftVelocityMps).Size() / 6.5f,
        0.0f, 1.0f);
    const float Contact = FMath::Clamp(
        static_cast<float>(ContactCount) / 5.0f + MaximumIndentationM / 0.22f,
        0.0f, 1.0f);

    Result.Spray = FMath::Clamp(
        HydraulicAeration * 0.72f + RelativeImpact * 0.42f + Contact * 0.66f,
        0.0f, 1.0f);
    Result.Mist = FMath::Clamp(
        HydraulicAeration * 0.64f + Result.Spray * 0.24f,
        0.0f, 1.0f);
    Result.ImpactSheet = FMath::Clamp(
        RelativeImpact * 0.46f + Contact * 0.86f,
        0.0f, 1.0f);
    Result.Droplets = FMath::Clamp(
        Result.Spray * 0.74f + Result.ImpactSheet * 0.48f,
        0.0f, 1.0f);
    Result.Underwater = bCameraUnderwater ? 1.0f : 0.0f;
    return Result;
}

bool ARaftSimWaterVfxActor::SampleCameraUnderwater() const
{
    const UWorld* World = GetWorld();
    if (!World || !WaterAdapter)
    {
        return false;
    }
    const APlayerController* Controller = World->GetFirstPlayerController();
    const APlayerCameraManager* Camera = Controller ? Controller->PlayerCameraManager : nullptr;
    if (!Camera)
    {
        return false;
    }
    FRaftSimWaterSample CameraSample;
    const FVector CameraLocation = Camera->GetCameraLocation();
    return WaterAdapter->SampleWaterAtWorldPosition(CameraLocation, CameraSample) &&
        CameraSample.bWet &&
        CameraLocation.Z < CameraSample.SurfaceHeightMeters * CmPerM - 4.0f;
}

void ARaftSimWaterVfxActor::ClearInstances()
{
    SprayInstances->ClearInstances();
    MistInstances->ClearInstances();
    SheetInstances->ClearInstances();
    DropletInstances->ClearInstances();
}

void ARaftSimWaterVfxActor::RefreshVfx(float DeltaSeconds)
{
    SimulationPhase += DeltaSeconds;
    if (!TrackedRaft || !WaterAdapter)
    {
        ClearInstances();
        LastPresentationState = FRaftSimWaterVfxState();
        UnderwaterPostProcess->BlendWeight = 0.0f;
        return;
    }

    const FVector RaftLocationCm = TrackedRaft->GetActorLocation();
    FRaftSimWaterSample Sample;
    if (!WaterAdapter->SampleWaterAtWorldPosition(RaftLocationCm, Sample))
    {
        ClearInstances();
        return;
    }
    const bool bCameraUnderwater = SampleCameraUnderwater();
    LastPresentationState = EvaluatePresentation(
        Sample,
        TrackedRaft->GetRaftVelocity(),
        TrackedRaft->GetActiveWaterContactCount(),
        TrackedRaft->GetMaximumWaterContactIndentationM(),
        bCameraUnderwater);
    UnderwaterPostProcess->BlendWeight = FMath::FInterpTo(
        UnderwaterPostProcess->BlendWeight,
        LastPresentationState.Underwater,
        FMath::Max(DeltaSeconds, RefreshIntervalSeconds),
        LastPresentationState.Underwater > 0.5f ? 9.0f : 4.5f);

    ClearInstances();
    if (!Sample.bWet)
    {
        return;
    }

    FVector FlowDirection = Sample.VelocityMetersPerSecond.GetSafeNormal2D();
    if (FlowDirection.IsNearlyZero())
    {
        FlowDirection = TrackedRaft->GetActorForwardVector();
    }
    const FVector AcrossDirection(-FlowDirection.Y, FlowDirection.X, 0.0f);
    const float SurfaceZCm = Sample.SurfaceHeightMeters * CmPerM + 8.0f;
    const FVector SurfaceCenter(RaftLocationCm.X, RaftLocationCm.Y, SurfaceZCm);

    const int32 SprayCount = FMath::RoundToInt(36.0f * LastPresentationState.Spray);
    for (int32 Index = 0; Index < SprayCount; ++Index)
    {
        const float Along = (DeterministicWave(Index, SimulationPhase, 2.1f) - 0.58f) * 430.0f;
        const float Across = (DeterministicWave(Index + 31, SimulationPhase, 1.7f) - 0.5f) * 260.0f;
        const float Arc = DeterministicWave(Index + 73, SimulationPhase, 3.4f);
        const FVector Location = SurfaceCenter + FlowDirection * Along + AcrossDirection * Across +
            FVector::UpVector * (24.0f + 205.0f * Arc * (1.0f - Arc));
        const float Scale = FMath::Lerp(0.025f, 0.105f, Arc) *
            FMath::Lerp(0.75f, 1.35f, LastPresentationState.Spray);
        SprayInstances->AddInstance(
            FTransform(FRotator::ZeroRotator, Location, FVector(Scale, Scale, Scale * 1.7f)),
            true);
    }

    const int32 DropletCount = FMath::RoundToInt(22.0f * LastPresentationState.Droplets);
    for (int32 Index = 0; Index < DropletCount; ++Index)
    {
        const float Travel = FMath::Fmod(SimulationPhase * 0.9f + Index * 0.137f, 1.0f);
        const FVector Location = SurfaceCenter - FlowDirection * (60.0f + 250.0f * Travel) +
            AcrossDirection * ((DeterministicWave(Index + 17, 0.0f, 1.0f) - 0.5f) * 230.0f) +
            FVector::UpVector * (28.0f + 160.0f * 4.0f * Travel * (1.0f - Travel));
        const float Scale = FMath::Lerp(0.012f, 0.035f,
            DeterministicWave(Index + 9, SimulationPhase, 1.4f));
        DropletInstances->AddInstance(
            FTransform(FRotator::ZeroRotator, Location, FVector(Scale, Scale, Scale * 2.2f)),
            true);
    }

    const int32 MistCount = FMath::RoundToInt(10.0f * LastPresentationState.Mist);
    for (int32 Index = 0; Index < MistCount; ++Index)
    {
        const float Drift = FMath::Fmod(SimulationPhase * 0.12f + Index * 0.173f, 1.0f);
        const FVector Location = SurfaceCenter - FlowDirection * (120.0f + Drift * 520.0f) +
            AcrossDirection * ((DeterministicWave(Index + 5, 0.0f, 1.0f) - 0.5f) * 460.0f) +
            FVector::UpVector * (90.0f + Drift * 180.0f);
        const float Scale = FMath::Lerp(0.35f, 0.82f,
            DeterministicWave(Index + 19, SimulationPhase, 0.7f));
        MistInstances->AddInstance(
            FTransform(FRotator::ZeroRotator, Location, FVector(Scale, Scale, Scale * 0.48f)),
            true);
    }

    const int32 SheetCount = FMath::RoundToInt(5.0f * LastPresentationState.ImpactSheet);
    for (int32 Index = 0; Index < SheetCount; ++Index)
    {
        const float Side = (Index % 2 == 0) ? -1.0f : 1.0f;
        const FVector Location = SurfaceCenter + FlowDirection * 155.0f +
            AcrossDirection * Side * (70.0f + 18.0f * Index) +
            FVector::UpVector * (45.0f + 20.0f * Index);
        const FRotator Rotation = FRotationMatrix::MakeFromXZ(
            (FlowDirection + FVector::UpVector * 0.65f).GetSafeNormal(),
            AcrossDirection * Side).Rotator();
        SheetInstances->AddInstance(
            FTransform(Rotation, Location,
                FVector(0.58f + 0.16f * Index, 0.22f, 1.0f)),
            true);
    }
}

void ARaftSimWaterVfxActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TimeSinceRefresh += DeltaSeconds;
    if (TimeSinceRefresh >= RefreshIntervalSeconds)
    {
        const float RefreshDelta = TimeSinceRefresh;
        TimeSinceRefresh = 0.0f;
        RefreshVfx(RefreshDelta);
    }
}
