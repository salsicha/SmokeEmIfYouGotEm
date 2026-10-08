#include "RaftSimRaftSplash.h"

#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
constexpr int32 kDropPool = 720;
constexpr float kGravityCm = 980.0f;
}

URaftSimRaftSplashComponent::URaftSimRaftSplashComponent(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    PrimaryComponentTick.bCanEverTick = false;
    SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetCastShadow(false);
}

void URaftSimRaftSplashComponent::Configure(FWaterSampler InSampler, UMaterialInterface* DropletMaterial)
{
    Sampler = MoveTemp(InSampler);
    Random.Initialize(52361);
    Drops.SetNum(kDropPool);
    for (FDrop& Drop : Drops)
    {
        Drop.PositionCm = GetComponentLocation();
        Drop.VelocityCmPerSecond = FVector::ZeroVector;
        Drop.Age = Drop.Life = 1.0f;
        Drop.SizeCm = 0.0f;
        Drop.Spin = 0.0f;
        Drop.Tile = 0;
        Drop.bSheet = false;
    }
    Triangles.Reset();
    for (int32 Quad = 0; Quad < kDropPool; ++Quad)
    {
        const int32 Base = Quad * 4;
        Triangles.Append({Base, Base + 1, Base + 2, Base, Base + 2, Base + 3});
    }
    if (UMaterialInstanceDynamic* Material = DropletMaterial ? UMaterialInstanceDynamic::Create(DropletMaterial, this) : nullptr)
    {
        Material->SetScalarParameterValue(TEXT("ParticleDepthFadeCm"), 2.0f);
        Material->SetScalarParameterValue(TEXT("ParticleRoughness"), 0.6f);
        Material->SetScalarParameterValue(TEXT("ParticleSpecular"), 0.2f);
        SetMaterial(0, Material);
    }
    bSectionCreated = false;
}

void URaftSimRaftSplashComponent::TrackRaft(const FTransform& RaftTransform, const FVector& RaftVelocityCmPerSecond,
    float InHalfLengthCm, float InHalfWidthCm)
{
    Raft = RaftTransform;
    RaftVelocity = RaftVelocityCmPerSecond;
    HalfLengthCm = InHalfLengthCm;
    HalfWidthCm = InHalfWidthCm;
    bTracking = true;
}

void URaftSimRaftSplashComponent::Splash(const FVector& AtCm, float Strength)
{
    const float S = FMath::Clamp(Strength, 0.0f, 1.3f);
    if (S <= 0.05f)
    {
        return;
    }
    ++SplashCount;
    // Over the boat: from the hit toward the raft's middle.
    FVector Inward = (Raft.GetLocation() - AtCm).GetSafeNormal2D();
    if (Inward.IsNearlyZero())
    {
        Inward = -Raft.GetUnitAxis(EAxis::X);
    }
    const FVector Tangent(-Inward.Y, Inward.X, 0.0f);
    int32 Droplets = FMath::RoundToInt(60.0f + 140.0f * S);
    int32 Sheets = FMath::RoundToInt(5.0f + 6.0f * S);
    // Even a moderate hit throws water up past the crew's heads (about
    // 1.2 m needs ~5 m/s); harder hits throw it higher and further.
    const float Throw = 0.6f + 0.4f * S;
    for (FDrop& Drop : Drops)
    {
        if (Droplets <= 0 && Sheets <= 0)
        {
            break;
        }
        if (Drop.Age < Drop.Life)
        {
            continue;
        }
        // A few broad sheets of water break up over the tube first; a
        // shower of droplets follows them over the boat.
        Drop.bSheet = Sheets > 0;
        Drop.PositionCm = AtCm + Tangent * Random.FRandRange(-45.0f, 45.0f) + FVector::UpVector * 10.0f;
        if (Drop.bSheet)
        {
            Drop.VelocityCmPerSecond = RaftVelocity + FVector::UpVector * Random.FRandRange(320.0f, 500.0f) * Throw +
                Inward * Random.FRandRange(180.0f, 320.0f) * Throw + Tangent * Random.FRandRange(-60.0f, 60.0f);
            Drop.Life = Random.FRandRange(0.4f, 0.7f);
            Drop.SizeCm = Random.FRandRange(70.0f, 160.0f) * FMath::Max(S, 0.5f);
            --Sheets;
        }
        else
        {
            Drop.VelocityCmPerSecond = RaftVelocity + FVector::UpVector * Random.FRandRange(420.0f, 700.0f) * Throw +
                Inward * Random.FRandRange(220.0f, 520.0f) * Throw + Tangent * Random.FRandRange(-130.0f, 130.0f);
            Drop.Life = Random.FRandRange(0.8f, 1.5f);
            Drop.SizeCm = Random.FRandRange(10.0f, 30.0f);
            --Droplets;
        }
        Drop.Age = 0.0f;
        Drop.Spin = Random.FRandRange(0.0f, 2.0f * PI);
        Drop.Tile = Random.RandRange(0, 15);
    }
}

void URaftSimRaftSplashComponent::DetectHits(float DeltaSeconds)
{
    if (!bTracking || !Sampler || DeltaSeconds <= 0.0f)
    {
        return;
    }
    Cooldown -= DeltaSeconds;
    const FVector Forward = Raft.GetUnitAxis(EAxis::X);
    // The end of the boat meeting the water: whichever end leads into it.
    const float Heading = FVector::DotProduct(RaftVelocity, Forward) >= 0.0f ? 1.0f : -1.0f;
    float BestStrength = 0.0f;
    FVector BestPoint = FVector::ZeroVector;
    for (int32 Index = 0; Index < 3; ++Index)
    {
        const FVector Point = Raft.TransformPositionNoScale(
            FVector(Heading * HalfLengthCm * 0.92f, (Index - 1) * 0.6f * HalfWidthCm, 0.0f));
        float WaterCm = 0.0f;
        FVector WaterVelocity = FVector::ZeroVector;
        if (!Sampler(Point, WaterCm, WaterVelocity))
        {
            continue;
        }
        const float FreeboardCm = Point.Z + 25.0f - WaterCm;
        const float RiseCmPerSecond = bHaveFreeboard ? (LastFreeboardCm[Index] - FreeboardCm) / DeltaSeconds : 0.0f;
        LastFreeboardCm[Index] = FreeboardCm;
        // Water closing on the leading end: the boat driving into it, or it
        // driving back at the boat.
        const float RushCmPerSecond = FVector::DotProduct(RaftVelocity - WaterVelocity, Forward * Heading);
        if (FreeboardCm > 18.0f)
        {
            continue;
        }
        const float Strength = FMath::Clamp((RiseCmPerSecond - 60.0f) / 200.0f, 0.0f, 1.0f) +
            FMath::Clamp((RushCmPerSecond - 220.0f) / 450.0f, 0.0f, 0.8f);
        if (Strength > BestStrength)
        {
            BestStrength = Strength;
            BestPoint = Point + FVector::UpVector * (WaterCm - Point.Z);
        }
    }
    bHaveFreeboard = true;
    if (BestStrength > 0.2f && Cooldown <= 0.0f)
    {
        Splash(BestPoint, FMath::Min(BestStrength, 1.2f));
        Cooldown = 0.45f;
    }
}

void URaftSimRaftSplashComponent::Advance(float DeltaSeconds, const FVector& ViewLocationCm)
{
    const float Dt = FMath::Clamp(DeltaSeconds, 0.0f, 0.1f);
    DetectHits(Dt);
    TArray<FVector> Vertices, Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    Vertices.Reserve(kDropPool * 4);
    Normals.Reserve(kDropPool * 4);
    Uvs.Reserve(kDropPool * 4);
    Colors.Reserve(kDropPool * 4);
    Tangents.Reserve(kDropPool * 4);
    const float RaftFloorZ = Raft.GetLocation().Z + 15.0f;
    const FTransform& ToWorld = GetComponentTransform();
    for (FDrop& Drop : Drops)
    {
        float Alpha = 0.0f;
        if (Drop.Age < Drop.Life)
        {
            Drop.Age += Dt;
            Drop.VelocityCmPerSecond.Z -= kGravityCm * Dt;
            Drop.VelocityCmPerSecond *= FMath::Exp((Drop.bSheet ? -2.5f : -0.6f) * Dt);
            Drop.PositionCm += Drop.VelocityCmPerSecond * Dt;
            // Falling drops end on the boat's floor or in the river.
            const FVector Local = Raft.InverseTransformPositionNoScale(Drop.PositionCm);
            const bool bOverRaft = FMath::Square(Local.X / FMath::Max(HalfLengthCm, 1.0f)) +
                FMath::Square(Local.Y / FMath::Max(HalfWidthCm, 1.0f)) < 1.0f;
            float WaterCm = -1.0e6f;
            FVector WaterVelocity;
            if (Drop.VelocityCmPerSecond.Z < 0.0f &&
                ((bOverRaft && Drop.PositionCm.Z < RaftFloorZ) ||
                 (!bOverRaft && Sampler && Sampler(Drop.PositionCm, WaterCm, WaterVelocity) && Drop.PositionCm.Z < WaterCm)))
            {
                Drop.Age = Drop.Life;
            }
            const float T = FMath::Clamp(Drop.Age / Drop.Life, 0.0f, 1.0f);
            if (Drop.Age < Drop.Life)
            {
                Alpha = Drop.bSheet ? 0.8f * FMath::Square(1.0f - T) : 0.9f * (1.0f - 0.7f * T);
            }
            Drop.Spin += Dt * (Drop.bSheet ? 1.5f : 4.0f);
        }
        const float T = FMath::Clamp(Drop.Age / FMath::Max(Drop.Life, 0.01f), 0.0f, 1.0f);
        const float Size = Alpha > 0.0f ? Drop.SizeCm * (Drop.bSheet ? FMath::Lerp(0.6f, 1.4f, T) : FMath::Lerp(1.0f, 1.6f, T)) : 0.0f;
        const FVector Forward = (Drop.PositionCm - ViewLocationCm).GetSafeNormal();
        FVector Right = FVector::CrossProduct(FVector::UpVector, Forward).GetSafeNormal();
        if (Right.IsNearlyZero())
        {
            Right = FVector::RightVector;
        }
        const FVector Up = FVector::CrossProduct(Forward, Right);
        const float C = FMath::Cos(Drop.Spin), S = FMath::Sin(Drop.Spin);
        const FVector R = (Right * C + Up * S) * Size, V = (Up * C - Right * S) * Size;
        const FVector2D TileOrigin((Drop.Tile % 4) * 0.25f, (Drop.Tile / 4) * 0.25f);
        for (const FVector2D Q : {FVector2D(-1, -1), FVector2D(1, -1), FVector2D(1, 1), FVector2D(-1, 1)})
        {
            Vertices.Add(ToWorld.InverseTransformPosition(Drop.PositionCm + R * Q.X + V * Q.Y));
            Normals.Add(ToWorld.InverseTransformVectorNoScale(-Forward));
            Uvs.Add(TileOrigin + FVector2D(Q.X * 0.5f + 0.5f, Q.Y * 0.5f + 0.5f) * 0.25f);
            Colors.Add(FLinearColor(0.9f, 0.95f, 1.0f, Alpha));
            Tangents.Add(FProcMeshTangent(Right, false));
        }
    }
    if (!bSectionCreated)
    {
        CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, Uvs, Colors, Tangents, false);
        bSectionCreated = true;
    }
    else
    {
        UpdateMeshSection_LinearColor(0, Vertices, Normals, Uvs, Colors, Tangents);
    }
}
