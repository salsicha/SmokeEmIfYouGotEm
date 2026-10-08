#include "RaftSimHoleWaterActor.h"

#include "Camera/PlayerCameraManager.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimHoleChurn.h"
#include "RaftSimHoleWave.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRaftSplash.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterVfxActor.h"

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimHoles, Log, All);

namespace
{
// Waves drawn at once, the nearest holes to the view within this radius.
constexpr int32 kMaxDrawnHoles = 6;
constexpr double kDrawRadiusCm = 12000.0;
// Holes heard at once, the nearest of those drawn.
constexpr int32 kHolesHeard = 2;
// A pile lower than this is not drawn (a breaking ripple, not a hole).
constexpr double kSmallestPileM = 0.12;
// Sites closer than this are one hole seen by two owners.
constexpr double kSameHoleCm = 200.0;
// A wave follows its hole as long as the hole stays this close.
constexpr double kFollowCm = 300.0;
// The river's surface is sampled over each wave this often.
constexpr float kSurfaceCacheSeconds = 0.2f;
}

ARaftSimHoleWaterActor::ARaftSimHoleWaterActor()
{
    PrimaryActorTick.bCanEverTick = true;
    // After the water and raft have stepped this frame.
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

bool ARaftSimHoleWaterActor::IsEnabled()
{
    const IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(TEXT("RaftSim.HoleWater"));
    return Variable && Variable->GetInt() != 0;
}

int32 ARaftSimHoleWaterActor::GetDrawnHoleCount() const
{
    int32 Count = 0;
    for (const bool bInUse : WaveInUse)
    {
        Count += bInUse ? 1 : 0;
    }
    return Count;
}

URaftSimHoleChurnComponent* ARaftSimHoleWaterActor::NewWave()
{
    auto* Wave = NewObject<URaftSimHoleChurnComponent>(this);
    Wave->SetupAttachment(RootComponent);
    Wave->RegisterComponent();
    Wave->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Wave->SetCastShadow(false);
    Wave->SetTranslucentSortPriority(2);
    return Wave;
}

void ARaftSimHoleWaterActor::HideWaves()
{
    for (int32 Index = 0; Index < Waves.Num(); ++Index)
    {
        if (WaveInUse.IsValidIndex(Index) && WaveInUse[Index])
        {
            Waves[Index]->SetSoundActive(false, 0);
            Waves[Index]->SetVisibility(false);
            WaveInUse[Index] = false;
        }
    }
}

void ARaftSimHoleWaterActor::SetHoleParticlesHidden(bool bHide)
{
    if (!bHide && !bHoleParticlesHidden)
    {
        return;
    }
    // The rapid particles only ever activate, move and rescale these; their
    // visibility is ours to keep while the waves are drawn.
    for (TActorIterator<ARaftSimWaterVfxActor> It(GetWorld()); It; ++It)
    {
        TArray<UNiagaraComponent*> Effects;
        It->GetComponents(Effects);
        for (UNiagaraComponent* Effect : Effects)
        {
            const FString Name = GetNameSafe(Effect ? Effect->GetAsset() : nullptr);
            if (Name.Contains(TEXT("RapidRoller")) || Name.Contains(TEXT("CrestSpray")))
            {
                Effect->SetVisibility(!bHide);
            }
        }
    }
    bHoleParticlesHidden = bHide;
}

void ARaftSimHoleWaterActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UWorld* World = GetWorld();
    URaftSimPhysicsBridgeSubsystem* Bridge = World && World->GetGameInstance()
        ? World->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    if (!IsEnabled() || !Water || !Water->HasLiveWindow() || !Water->HasFeatureKinematics())
    {
        HideWaves();
        SetHoleParticlesHidden(false);
        return;
    }
    if (!Raft.IsValid())
    {
        for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It)
        {
            Raft = *It;
            break;
        }
    }
    FVector View = Raft.IsValid() ? Raft->GetActorLocation() : GetActorLocation();
    if (const APlayerController* Player = World->GetFirstPlayerController())
    {
        if (Player->PlayerCameraManager)
        {
            View = Player->PlayerCameraManager->GetCameraLocation();
        }
    }

    // The holes near the view, nearest first, each drawn the size the hull
    // meets it.
    struct FHole
    {
        RaftSimHoleWave::FShape Shape;
        FVector CrestCm;
        FVector Downstream;
        double DistanceSquared;
    };
    TArray<FHole> Holes;
    const float DatumM = Water->GetRiverVerticalDatumM();
    for (const URaftSimWaterRuntimeAdapter::FSupportBreakingSite& Site : Water->GetFeatureBreakingSites())
    {
        const FVector2D Flow = Site.FlowDirection.GetSafeNormal();
        if (Flow.IsNearlyZero())
        {
            continue;
        }
        const RaftSimHoleWave::FShape Shape = RaftSimHoleWave::FShape::ForSite(Site.PhysicalCrestHeightMeters,
            Site.PhysicalCrestLengthMeters, FMath::Clamp(Site.Intensity * Site.SpillingFraction, 0.0f, 1.0f));
        FVector CrestCm;
        if (Shape.HeightM * Shape.Intensity < kSmallestPileM || !Water->RiverToWorldPosition(Site.RiverCoordinatesMeters, DatumM, CrestCm) ||
            FVector::DistSquared2D(CrestCm, View) > FMath::Square(kDrawRadiusCm))
        {
            continue;
        }
        FRaftSimWaterSample Sample;
        FVector2D Coordinates;
        FVector Tangent, Left;
        if (!Water->SampleRaftSupportSurfaceAtWorldPosition(CrestCm, Sample) || !Sample.bWet ||
            !Water->WorldToRiverCoordinates(CrestCm, Coordinates, Tangent, Left))
        {
            continue;
        }
        CrestCm.Z = Sample.SurfaceHeightMeters * 100.0;
        Holes.Add({Shape, CrestCm, (Tangent * Flow.X + Left * Flow.Y).GetSafeNormal2D(), FVector::DistSquared2D(CrestCm, View)});
    }
    Holes.Sort([](const FHole& A, const FHole& B) { return A.DistanceSquared < B.DistanceSquared; });
    TArray<FHole> Drawn;
    for (const FHole& Hole : Holes)
    {
        if (Drawn.Num() < kMaxDrawnHoles && !Drawn.ContainsByPredicate([&Hole](const FHole& Other)
            { return FVector::DistSquared2D(Other.CrestCm, Hole.CrestCm) < FMath::Square(kSameHoleCm); }))
        {
            Drawn.Add(Hole);
        }
    }

    // Each wave stays on its hole as the hole drifts; a hole newly in view
    // takes a free wave.
    WaveInUse.SetNumZeroed(Waves.Num());
    TArray<int32> WaveOfHole;
    WaveOfHole.Init(INDEX_NONE, Drawn.Num());
    TArray<bool> Kept;
    Kept.Init(false, Waves.Num());
    for (int32 H = 0; H < Drawn.Num(); ++H)
    {
        double Best = FMath::Square(kFollowCm);
        for (int32 W = 0; W < Waves.Num(); ++W)
        {
            const double Distance = FVector::DistSquared2D(Waves[W]->GetSite().CrestCm, Drawn[H].CrestCm);
            if (WaveInUse[W] && !Kept[W] && Distance < Best)
            {
                Best = Distance;
                WaveOfHole[H] = W;
            }
        }
        if (WaveOfHole[H] != INDEX_NONE)
        {
            Kept[WaveOfHole[H]] = true;
        }
    }
    for (int32 W = 0; W < Waves.Num(); ++W)
    {
        if (WaveInUse[W] && !Kept[W])
        {
            Waves[W]->SetSoundActive(false, 0);
            Waves[W]->SetVisibility(false);
            WaveInUse[W] = false;
        }
    }
    if (!WaveMaterial)
    {
        WaveMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip.M_RaftSim_BreakingWaterLip"));
    }
    const TWeakObjectPtr<URaftSimWaterRuntimeAdapter> WeakWater = Water;
    float RaftHalfLengthCm = 0.0f, RaftHalfWidthCm = 0.0f;
    if (Raft.IsValid())
    {
        const FRaftSimRaftBodyConfig Body = Raft->MakeProductionBodyConfig();
        RaftHalfLengthCm = float(Body.LengthMeters * 0.5 + Body.TubeRadiusMeters) * 105.0f;
        RaftHalfWidthCm = float(Body.WidthMeters * 0.5) * 105.0f;
    }
    for (int32 H = 0; H < Drawn.Num(); ++H)
    {
        const FHole& Hole = Drawn[H];
        int32 W = WaveOfHole[H];
        if (W == INDEX_NONE)
        {
            W = WaveInUse.IndexOfByKey(false);
            if (W == INDEX_NONE)
            {
                W = Waves.Add(NewWave());
                WaveInUse.Add(false);
            }
            Waves[W]->Configure(URaftSimHoleChurnComponent::SiteOf(Hole.Shape, Hole.CrestCm, Hole.Downstream, NextSeed++),
                [WeakWater](const FVector& PointCm)
                {
                    FRaftSimWaterSample Sample;
                    URaftSimWaterRuntimeAdapter* Adapter = WeakWater.Get();
                    return Adapter && Adapter->SampleRaftSupportSurfaceAtWorldPosition(PointCm, Sample) && Sample.bWet
                        ? float(Sample.SurfaceHeightMeters * 100.0) : float(PointCm.Z);
                },
                WaveMaterial);
            Waves[W]->CacheSurface(kSurfaceCacheSeconds);
            Waves[W]->SetVisibility(true);
            WaveInUse[W] = true;
            UE_LOG(LogRaftSimHoles, Log, TEXT("HOLE_WAVE drawn crest_cm=%s downstream=%s pile_m=%.2f length_m=%.1f half_width_m=%.1f strength=%.2f roll_mps=%.2f"),
                *Hole.CrestCm.ToCompactString(), *Hole.Downstream.ToCompactString(), Hole.Shape.HeightM, Hole.Shape.LengthM,
                Hole.Shape.HalfWidthM, Hole.Shape.Intensity, Hole.Shape.RollMps);
        }
        else
        {
            Waves[W]->Retarget(URaftSimHoleChurnComponent::SiteOf(Hole.Shape, Hole.CrestCm, Hole.Downstream, 0));
        }
        Waves[W]->SetSoundActive(H < kHolesHeard, uint32(Waves[W]->GetSite().Seed));
        if (Raft.IsValid())
        {
            Waves[W]->SetRaftExclusion(Raft->GetActorTransform(), RaftHalfLengthCm, RaftHalfWidthCm);
        }
        Waves[W]->Advance(DeltaSeconds, View);
    }
    SetHoleParticlesHidden(true);

    // Water over the crew when the raft hits a hole or a wave hard.
    if (Raft.IsValid())
    {
        if (!Splash)
        {
            Splash = NewObject<URaftSimRaftSplashComponent>(this);
            Splash->SetupAttachment(RootComponent);
            Splash->RegisterComponent();
            Splash->SetTranslucentSortPriority(4);
            Splash->Configure([WeakWater](const FVector& PointCm, float& OutHeightCm, FVector& OutVelocityCmPerSecond)
                {
                    FRaftSimWaterSample Sample;
                    URaftSimWaterRuntimeAdapter* Adapter = WeakWater.Get();
                    if (!Adapter || !Adapter->SampleRaftInteractionWaterAtWorldPosition(PointCm, Sample) || !Sample.bWet)
                    {
                        return false;
                    }
                    OutHeightCm = float(Sample.SurfaceHeightMeters * 100.0);
                    OutVelocityCmPerSecond = Sample.VelocityMetersPerSecond * 100.0;
                    return true;
                },
                LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_NiagaraWaterParticle.M_RaftSim_NiagaraWaterParticle")));
        }
        Splash->TrackRaft(Raft->GetActorTransform(), Raft->GetRaftVelocity() * 100.0, RaftHalfLengthCm, RaftHalfWidthCm);
        Splash->Advance(DeltaSeconds, View);
    }
}
