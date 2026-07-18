#include "RaftSimRaftActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float kCmPerM = 100.0f;
constexpr float kGravityMps2 = 9.80665f;
}

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
        HullMesh->SetRelativeScale3D(FVector(4.3f, 2.0f, 0.56f));
        HullMesh->SetRelativeLocation(FVector(0.0f, 0.0f, 0.0f));
    }

    SternSeatAttachPoint = CreateDefaultSubobject<USceneComponent>(TEXT("SternSeatAttachPoint"));
    SternSeatAttachPoint->SetupAttachment(Root);
    // Guide sits on the stern tube, slightly above the deck.
    SternSeatAttachPoint->SetRelativeLocation(FVector(-165.0f, 0.0f, 55.0f));

    // Six tube sample points: bow pair, midship pair, stern pair (meters, local).
    TubeSamplePointsM = {
        FVector(1.85f, -0.85f, 0.0f), FVector(1.85f, 0.85f, 0.0f),
        FVector(0.0f, -1.0f, 0.0f),   FVector(0.0f, 1.0f, 0.0f),
        FVector(-1.85f, -0.85f, 0.0f), FVector(-1.85f, 0.85f, 0.0f),
    };
}

void ARaftSimRaftActor::BeginPlay()
{
    Super::BeginPlay();
    // P2: live solver water. Resolve the bridge subsystem's adapter and stand
    // up a flat-tank FV window (surface Z=0, 3 m deep, 2 m cells, 160x160 m).
    // Dev water: the report gate governs river-water approval claims, not the
    // genuine-solver tank, so the gate requirement is disabled here.
    WaterAdapter = nullptr;
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            if (URaftSimWaterRuntimeAdapter* Adapter = Bridge->GetWaterRuntime())
            {
                FRaftSimWaterRuntimeConfig DevConfig;
                DevConfig.bRequireAcceptedReportManifest = false;
                Adapter->Configure(DevConfig);
                if (Adapter->ConfigureDevTankWindow(
                        FVector2D(-80.0, -80.0), 160.0f, 160.0f, 2.0f,
                        /*SurfaceHeightM=*/0.0f, /*DepthM=*/3.0f))
                {
                    WaterAdapter = Adapter;
                }
            }
        }
    }
}

float ARaftSimRaftActor::SampleWaterSurfaceZ(const FVector& WorldPosition) const
{
    if (WaterAdapter != nullptr)
    {
        FRaftSimWaterSample Sample;
        if (WaterAdapter->SampleWaterAtWorldPosition(WorldPosition, Sample) && Sample.bWet)
        {
            return Sample.SurfaceHeightMeters * kCmPerM;
        }
    }
    // Flat test-tank surface: world Z = 0.
    return 0.0f;
}

void ARaftSimRaftActor::ApplyPaddleStroke(ERaftSimPaddleSide Side, float ForwardScale)
{
    const float Scale = FMath::Clamp(ForwardScale, -1.0f, 1.0f);
    const FVector Forward = GetActorForwardVector();
    const FVector ImpulseNs = Forward * (PaddleStrokeImpulseNs * Scale);
    PendingImpulseNs += ImpulseNs;

    // Off-center strokes also yaw the raft a little.
    if (Side != ERaftSimPaddleSide::Both)
    {
        const float LeverArmM = 0.9f;
        const float SideSign = (Side == ERaftSimPaddleSide::Port) ? -1.0f : 1.0f;
        PendingAngularImpulse.Z += -SideSign * Scale * PaddleStrokeImpulseNs * LeverArmM * 0.35f;
    }
}

void ARaftSimRaftActor::ApplyTurnStroke(float TurnScale)
{
    const float Scale = FMath::Clamp(TurnScale, -1.0f, 1.0f);
    PendingAngularImpulse.Z += Scale * PaddleStrokeImpulseNs * 1.15f;
}

void ARaftSimRaftActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TimeAccumulator += FMath::Min(DeltaSeconds, 0.25f);
    if (WaterAdapter != nullptr)
    {
        WaterAdapter->StepWater(FMath::Min(DeltaSeconds, 0.25f));
    }
    while (TimeAccumulator >= FixedSubstepSeconds)
    {
        StepRaft(FixedSubstepSeconds);
        TimeAccumulator -= FixedSubstepSeconds;
    }
}

void ARaftSimRaftActor::StepRaft(float SubstepSeconds)
{
    const FTransform Xf = GetActorTransform();
    const int32 NumPoints = TubeSamplePointsM.Num();
    const float PerPointBuoyancyN =
        (MassKg * kGravityMps2 * BuoyancyWeightMultiple) / static_cast<float>(NumPoints);

    FVector TotalForceN(0.0f, 0.0f, -MassKg * kGravityMps2);
    FVector TotalTorqueNm = FVector::ZeroVector;
    float SubmergedFraction = 0.0f;

    for (const FVector& LocalM : TubeSamplePointsM)
    {
        const FVector WorldCm = Xf.TransformPosition(LocalM * kCmPerM);
        const float SurfaceZCm = SampleWaterSurfaceZ(WorldCm);
        const float SubmersionM = (SurfaceZCm - WorldCm.Z) / kCmPerM;
        const float Saturation =
            FMath::Clamp(SubmersionM / (2.0f * TubeRadiusM), 0.0f, 1.0f);
        if (Saturation <= 0.0f)
        {
            continue;
        }
        SubmergedFraction += Saturation / static_cast<float>(NumPoints);

        const FVector PointForceN(0.0f, 0.0f, PerPointBuoyancyN * Saturation);
        TotalForceN += PointForceN;
        const FVector LeverM = (WorldCm - Xf.GetLocation()) / kCmPerM;
        TotalTorqueNm += FVector::CrossProduct(LeverM, PointForceN);
    }

    // Quadratic water drag opposing velocity, scaled by submersion.
    const float Speed = LinearVelocity.Size();
    if (Speed > KINDA_SMALL_NUMBER && SubmergedFraction > 0.0f)
    {
        TotalForceN += -LinearVelocity.GetSafeNormal() *
                       (LinearDragCoefficient * SubmergedFraction * Speed * Speed);
    }

    // Linear heave damping: quadratic drag alone is negligible at bobbing
    // speeds, leaving the buoyancy spring underdamped.
    if (SubmergedFraction > 0.0f)
    {
        TotalForceN.Z += -HeaveDampingNsPerM * SubmergedFraction * LinearVelocity.Z;
    }

    // Integrate impulses accumulated from paddle input.
    LinearVelocity += PendingImpulseNs / MassKg;
    // Approximate yaw inertia of a flat raft: (1/12) m (L^2 + W^2).
    const float YawInertia = MassKg * (4.3f * 4.3f + 2.0f * 2.0f) / 12.0f;
    AngularVelocityRad.Z += PendingAngularImpulse.Z / YawInertia;
    PendingImpulseNs = FVector::ZeroVector;
    PendingAngularImpulse = FVector::ZeroVector;

    // Semi-implicit Euler.
    LinearVelocity += (TotalForceN / MassKg) * SubstepSeconds;
    const FVector RollPitchAccel = TotalTorqueNm / FMath::Max(YawInertia * 0.45f, 1.0f);
    AngularVelocityRad += FVector(RollPitchAccel.X, RollPitchAccel.Y, 0.0f) * SubstepSeconds;
    AngularVelocityRad *= FMath::Clamp(1.0f - AngularDampingPerSecond * SubstepSeconds, 0.0f, 1.0f);

    FVector NewLocation = Xf.GetLocation() + LinearVelocity * kCmPerM * SubstepSeconds;
    const FVector DeltaRotRad = AngularVelocityRad * SubstepSeconds;
    const FQuat DeltaQuat =
        FQuat(FVector::XAxisVector, DeltaRotRad.X) *
        FQuat(FVector::YAxisVector, DeltaRotRad.Y) *
        FQuat(FVector::ZAxisVector, DeltaRotRad.Z);
    SetActorLocationAndRotation(NewLocation, (DeltaQuat * Xf.GetRotation()).GetNormalized());
}
