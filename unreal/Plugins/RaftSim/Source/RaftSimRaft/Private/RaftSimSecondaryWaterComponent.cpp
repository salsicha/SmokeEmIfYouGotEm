#include "RaftSimSecondaryWaterComponent.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/PlatformTime.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterSurfaceActor.h"

URaftSimSecondaryWaterComponent::URaftSimSecondaryWaterComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void URaftSimSecondaryWaterComponent::BeginPlay()
{
    Super::BeginPlay();
    if (!FParse::Param(FCommandLine::Get(), TEXT("RaftSimSecondaryWaterReview")) ||
        !GetWorld()->GetMapName().EndsWith(TEXT("SouthForkRegisteredRockPlayable"))) return;
    if (!FParse::Param(FCommandLine::Get(), TEXT("RaftSimStatefulCrestReview")))
    {
        UE_LOG(LogTemp, Warning, TEXT("Secondary water review requires the shared stateful crest carrier; retaining existing VFX"));
        return;
    }
    auto* Bridge = GetWorld()->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    Adapter = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    if (TActorIterator<ARaftSimWaterSurfaceActor> It(GetWorld()); It) Surface = *It;
    auto* Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    auto* Material = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_SecondaryWaterReview.M_SecondaryWaterReview"));
    if (!Adapter || !Surface.IsValid() || !Mesh || !Material)
    {
        UE_LOG(LogTemp, Error, TEXT("Secondary water review unavailable; retaining existing VFX"));
        return;
    }
    Instances = NewObject<UInstancedStaticMeshComponent>(GetOwner(), TEXT("SecondaryWaterReviewFragments"));
    GetOwner()->AddInstanceComponent(Instances);
    Instances->SetMobility(EComponentMobility::Movable);
    Instances->SetStaticMesh(Mesh);
    Instances->SetMaterial(0, Material);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Instances->SetCanEverAffectNavigation(false);
    Instances->SetCastShadow(false);
    Instances->RegisterComponent();
    InitializeInstanceHistory(Instances, PreviousTransforms);
    // Sample only after the actor has published this frame's macro carrier.
    AddTickPrerequisiteActor(Surface.Get());
    bReady = true;
    SetComponentTickEnabled(true);
    UE_LOG(LogTemp, Display, TEXT("Secondary water review ready: capacity=128 fixed_hz=60 max_steps=4; macro carrier only, no GPU ripple readback or solid sweep"));
}

void URaftSimSecondaryWaterComponent::InitializeInstanceHistory(
    UInstancedStaticMeshComponent* Component, TArray<FTransform>& History)
{
    check(Component && Component->GetInstanceCount() == 0);
    // The explicit previous-transform batch overload requires this storage;
    // merely supplying an external history array does not allocate it.
    Component->SetHasPerInstancePrevTransforms(true);
    History.Init(FTransform(FQuat::Identity, FVector::ZeroVector, FVector::ZeroVector),
        FRaftSimSecondaryWater::Capacity);
    Component->AddInstances(History, false, true);
}

bool URaftSimSecondaryWaterComponent::Sample(const FVector& PositionM,
    FRaftSimSecondaryWater::FCarrier& Out) const
{
    if (!Adapter || !Surface.IsValid()) return false;
    const FVector WorldCm = PositionM * 100.0;
    FVector2D River;
    FVector Downstream, Left, Carrier;
    FRaftSimWaterSample Water;
    if (!Adapter->WorldToRiverCoordinates(WorldCm, River, Downstream, Left) ||
        !Surface->SampleVisibleCarrierAtRiverCoordinates(River, Carrier) ||
        !Adapter->SampleWaterFieldAtRiverCoordinates(River, Water) || !Water.bWet) return false;
    Out.HeightM = Carrier.Z * 0.01;
    Out.VelocityMps = Downstream * Water.VelocityMetersPerSecond.X + Left * Water.VelocityMetersPerSecond.Y;
    return Out.IsFinite();
}

void URaftSimSecondaryWaterComponent::TickComponent(float DeltaSeconds, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    if (!bReady || !Surface.IsValid() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0) return;
    const double Start = FPlatformTime::Seconds();
    Elapsed += DeltaSeconds;
    PendingSeconds += DeltaSeconds;
    TArray<ARaftSimWaterSurfaceActor::FBreakingSite> Sites;
    Surface->GetBreakingSites(Sites);
    Sites.RemoveAll([](const auto& Site) { return Site.Intensity <= 0.12f || Site.PersistenceWeight <= 0.01f; });
    // At most six sources; live fragments retain their birth state if this list changes.
    if (Sites.Num() > 6) Sites.SetNum(6);
    auto Sampler = [this](const FVector& P, FRaftSimSecondaryWater::FCarrier& C) { return Sample(P, C); };
    int32 Steps = 0;
    while (PendingSeconds + 1.e-9 >= FRaftSimSecondaryWater::StepSeconds && Steps++ < 4)
    {
        Simulation.Step(FRaftSimSecondaryWater::StepSeconds, Sampler);
        if (!Sites.IsEmpty())
        {
            // Fixed total budget, not multiplied by the number of sites.
            EmissionCredit += 80.0 * FRaftSimSecondaryWater::StepSeconds;
            while (EmissionCredit >= 1.0)
            {
                EmissionCredit -= 1.0;
                const auto& Site = Sites[Random.RandRange(0, Sites.Num() - 1)];
                if (Random.FRand() > Site.Intensity * Site.PersistenceWeight) continue;
                FVector Across = FVector::CrossProduct(FVector::UpVector, Site.WorldVelocityMps.GetSafeNormal2D());
                const FVector Position = Site.WorldPositionCm * 0.01 + Across * Random.FRandRange(-0.6f, 0.6f);
                // Ejection is a bounded presentation scale, not inferred
                // measured turbulence. Horizontal current is inherited once.
                const FVector Ejection = Across * Random.FRandRange(-0.35f, 0.35f) +
                    FVector::UpVector * Random.FRandRange(1.2f, 2.8f);
                Simulation.Spawn(Position, Ejection, Random.FRandRange(0.02f, 0.045f), Sampler);
            }
        }
        PendingSeconds -= FRaftSimSecondaryWater::StepSeconds;
    }
    TArray<FTransform> Transforms;
    Transforms.Reserve(FRaftSimSecondaryWater::Capacity);
    const double Alpha = FMath::Clamp(PendingSeconds / FRaftSimSecondaryWater::StepSeconds, 0.0, 1.0);
    for (int32 I = 0; I < FRaftSimSecondaryWater::Capacity; ++I)
    {
        const auto& P = Simulation.Particles[I];
        const double Fade = P.bFoam ? FMath::Clamp(1.0 - P.FoamAge / 0.8, 0.0, 1.0) : 1.0;
        // Engine sphere radius=50cm. Constant volume while airborne, then
        // smooth erosion on the surface. No scrolling texture or facing card.
        const double Scale = P.bAlive ? P.RadiusM * 2.0 * Fade : 0.0;
        // One fixed step of interpolation latency prevents a 60Hz stepping
        // artifact on faster displays. Previous-render transforms remain distinct.
        const FVector RenderPosition = FMath::Lerp(P.PreviousPositionM, P.PositionM, Alpha);
        const FTransform Transform(FQuat::Identity, RenderPosition * 100.0, FVector(Scale));
        Transforms.Add(Transform);
        if (PreviousBirthIds[I] != P.BirthId || !P.bAlive)
            PreviousTransforms[I] = Transform; // no motion vector across pool reuse/death
        PreviousBirthIds[I] = P.BirthId;
    }
    Instances->BatchUpdateInstancesTransforms(0, Transforms, PreviousTransforms, true, true, false);
    PreviousTransforms = MoveTemp(Transforms);
    CpuSeconds += FPlatformTime::Seconds() - Start;
    ++FrameCount;
    if (Elapsed >= NextReportSeconds)
    {
        UE_LOG(LogTemp, Display, TEXT("Secondary water review: t=%.3f alive=%d spawned=%llu returned=%llu rejected=%llu expired=%llu pending_s=%.6f cpu_mean_ms=%.4f"),
            Elapsed, Simulation.AliveCount(), Simulation.Spawned, Simulation.Returned, Simulation.Rejected,
            Simulation.Expired, PendingSeconds, 1000.0 * CpuSeconds / FrameCount);
        NextReportSeconds += 5;
    }
}
