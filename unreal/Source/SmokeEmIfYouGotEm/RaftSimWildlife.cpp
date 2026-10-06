#include "RaftSimWildlife.h"
#include "ProfilingDebugging/CsvProfiler.h"
CSV_DEFINE_CATEGORY(RaftSimTickWildlife,true);

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Sound/SoundAttenuation.h"

namespace
{
using ESpecies = ERaftSimWildlifeSpecies;
using EHabitat = ERaftSimWildlifeHabitat;
using EBody = ERaftSimWildlifeBody;

FLinearColor C(float R, float G, float B) { return FLinearColor(R, G, B); }

/** Shaded primitives for the low-poly animals (both windings, like the raft gear). */
struct FWildShape
{
    TArray<FVector> V;
    TArray<int32> T;
    TArray<FVector> N;
    TArray<FVector2D> UV;
    TArray<FProcMeshTangent> Tan;
    TArray<FLinearColor> Col;

    int32 Add(const FVector& P, const FVector& Normal)
    {
        V.Add(P);
        N.Add(Normal.GetSafeNormal());
        UV.Add(FVector2D::ZeroVector);
        Tan.Add(FProcMeshTangent(FVector::CrossProduct(Normal, FVector::UpVector).GetSafeNormal(), false));
        Col.Add(FLinearColor::White);
        return V.Num() - 1;
    }

    void Ellipsoid(const FVector& Center, const FVector& R, const FRotator& Rot = FRotator::ZeroRotator,
        int32 Segments = 12, int32 Rings = 8)
    {
        const FQuat Q = Rot.Quaternion();
        const int32 Base = V.Num();
        for (int32 Ring = 0; Ring <= Rings; ++Ring)
        {
            const float Phi = PI * Ring / Rings;
            for (int32 Seg = 0; Seg <= Segments; ++Seg)
            {
                const float Theta = UE_TWO_PI * Seg / Segments;
                const FVector Unit(FMath::Sin(Phi) * FMath::Cos(Theta), FMath::Sin(Phi) * FMath::Sin(Theta), FMath::Cos(Phi));
                Add(Center + Q.RotateVector(Unit * R),
                    Q.RotateVector(FVector(Unit.X / R.X, Unit.Y / R.Y, Unit.Z / R.Z)));
            }
        }
        for (int32 Ring = 0; Ring < Rings; ++Ring)
        {
            for (int32 Seg = 0; Seg < Segments; ++Seg)
            {
                const int32 A = Base + Ring * (Segments + 1) + Seg;
                const int32 B = A + Segments + 1;
                T.Append({A, B, A + 1, A + 1, B, B + 1});
            }
        }
    }

    /** A tapered tube from A (radius RA) to B (radius RB). */
    void Cone(const FVector& A, const FVector& B, float RA, float RB, int32 Sides = 8)
    {
        const FVector Axis = (B - A).GetSafeNormal();
        if (Axis.IsNearlyZero())
        {
            return;
        }
        const FVector U = FVector::CrossProduct(Axis, FMath::Abs(Axis.Z) < 0.9f ? FVector::UpVector : FVector::ForwardVector)
            .GetSafeNormal();
        const FVector W = FVector::CrossProduct(Axis, U);
        const int32 Base = V.Num();
        for (int32 Ring = 0; Ring < 2; ++Ring)
        {
            for (int32 Side = 0; Side < Sides; ++Side)
            {
                const float Angle = UE_TWO_PI * Side / Sides;
                const FVector Out = U * FMath::Cos(Angle) + W * FMath::Sin(Angle);
                Add((Ring ? B : A) + Out * (Ring ? RB : RA), Out);
            }
        }
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 Next = (Side + 1) % Sides;
            T.Append({Base + Side, Base + Sides + Side, Base + Next, Base + Next, Base + Sides + Side, Base + Sides + Next});
        }
        const int32 CapA = Add(A, -Axis);
        const int32 CapB = Add(B, Axis);
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 Next = (Side + 1) % Sides;
            T.Append({CapA, Base + Next, Base + Side, CapB, Base + Sides + Side, Base + Sides + Next});
        }
    }

    /** A thin convex plate (wing, tail fan, fin): outline in local XY, then placed. */
    void Slab(const TArray<FVector2D>& Outline, float Thickness, const FTransform& Xf)
    {
        FVector2D Centroid = FVector2D::ZeroVector;
        for (const FVector2D& P : Outline)
        {
            Centroid += P;
        }
        Centroid /= FMath::Max(Outline.Num(), 1);
        for (int32 Face = 0; Face < 2; ++Face)
        {
            const float Z = (Face ? -0.5f : 0.5f) * Thickness;
            const FVector Normal = Xf.TransformVectorNoScale(FVector(0, 0, Face ? -1.0f : 1.0f));
            const int32 Hub = Add(Xf.TransformPosition(FVector(Centroid, Z)), Normal);
            const int32 First = V.Num();
            for (const FVector2D& P : Outline)
            {
                Add(Xf.TransformPosition(FVector(P, Z)), Normal);
            }
            for (int32 Index = 0; Index < Outline.Num(); ++Index)
            {
                const int32 A = First + Index;
                const int32 B = First + (Index + 1) % Outline.Num();
                T.Append({Hub, A, B});
            }
        }
    }

    void Commit(UProceduralMeshComponent* Component, int32 Section) const
    {
        TArray<int32> Both = T;
        for (int32 Index = 0; Index + 2 < T.Num(); Index += 3)
        {
            Both.Append({T[Index], T[Index + 2], T[Index + 1]});
        }
        Component->CreateMeshSection_LinearColor(Section, V, Both, N, UV, Col, Tan, false);
    }
};

FRaftSimWildlifeSpeciesInfo MakeInfo(ESpecies Species, EHabitat Habitat, EBody Body, ERaftSimWildlifeCall Call, float Size,
    FLinearColor Body0, FLinearColor Head, FLinearColor Limbs, FLinearColor Accent, FLinearColor Under, FLinearColor Tail)
{
    FRaftSimWildlifeSpeciesInfo Info;
    Info.Species = Species;
    Info.Habitat = Habitat;
    Info.Body = Body;
    Info.Call = Call;
    Info.SizeMeters = Size;
    Info.Body0 = Body0;
    Info.Head = Head;
    Info.Limbs = Limbs;
    Info.Accent = Accent;
    Info.Under = Under;
    Info.Tail = Tail;
    return Info;
}

FRaftSimWildlifeSpeciesInfo WithNumbers(FRaftSimWildlifeSpeciesInfo Info, int32 MaxNearby, int32 GroupMin, int32 GroupMax,
    float AltitudeMin = 30.0f, float AltitudeMax = 90.0f)
{
    Info.MaxNearby = MaxNearby;
    Info.GroupMin = GroupMin;
    Info.GroupMax = GroupMax;
    Info.AltitudeMin = AltitudeMin;
    Info.AltitudeMax = AltitudeMax;
    return Info;
}

FString MapLeaf(const FString& MapName)
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
    return Leaf;
}

bool IsFlightBody(EBody Body)
{
    return Body == EBody::Soarer || Body == EBody::Flapper;
}
}

FRaftSimWildlifeSpeciesInfo GetWildlifeSpeciesInfo(ERaftSimWildlifeSpecies Species)
{
    using ECall = ERaftSimWildlifeCall;
    const FLinearColor White = C(0.80f, 0.80f, 0.78f);
    const FLinearColor Black = C(0.012f, 0.012f, 0.013f);
    FRaftSimWildlifeSpeciesInfo Info;
    switch (Species)
    {
        case ESpecies::BaldEagle:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::BaldEagle, 2.0f,
                C(0.04f, 0.025f, 0.013f), White, C(0.035f, 0.022f, 0.012f), C(0.85f, 0.6f, 0.04f),
                C(0.04f, 0.025f, 0.013f), White);
            Info.DihedralDeg = 3.0f;
            break;
        case ESpecies::Osprey:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::Osprey, 1.6f,
                C(0.06f, 0.04f, 0.025f), White, C(0.06f, 0.04f, 0.025f), Black, C(0.72f, 0.71f, 0.69f),
                C(0.35f, 0.3f, 0.25f));
            Info.DihedralDeg = 8.0f;
            break;
        case ESpecies::TurkeyVulture:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::None, 1.75f,
                C(0.02f, 0.015f, 0.012f), C(0.45f, 0.05f, 0.04f), C(0.025f, 0.018f, 0.014f), C(0.75f, 0.7f, 0.6f),
                C(0.25f, 0.25f, 0.25f), C(0.025f, 0.02f, 0.015f));
            Info.DihedralDeg = 15.0f;
            break;
        case ESpecies::CaliforniaCondor:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::None, 2.9f,
                Black, C(0.6f, 0.25f, 0.12f), Black, C(0.75f, 0.7f, 0.6f), C(0.72f, 0.72f, 0.70f), Black);
            Info.DihedralDeg = 5.0f;
            break;
        case ESpecies::AndeanCondor:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::None, 3.1f,
                Black, C(0.25f, 0.12f, 0.1f), Black, White, Black, Black);
            Info.DihedralDeg = 4.0f;
            break;
        case ESpecies::AfricanFishEagle:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::AfricanFishEagle, 2.0f,
                C(0.15f, 0.04f, 0.015f), White, C(0.015f, 0.012f, 0.01f), C(0.8f, 0.6f, 0.05f),
                C(0.15f, 0.04f, 0.015f), White);
            break;
        case ESpecies::VerreauxsEagle:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Soarer, ECall::None, 2.1f,
                Black, Black, Black, C(0.8f, 0.6f, 0.05f), Black, Black);
            break;
        case ESpecies::CommonRaven:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Flapper, ECall::CommonRaven, 1.2f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::GreatBlueHeron:
            Info = MakeInfo(Species, EHabitat::Shore, EBody::Heron, ECall::GreatBlueHeron, 1.8f,
                C(0.12f, 0.14f, 0.17f), C(0.7f, 0.7f, 0.68f), C(0.12f, 0.14f, 0.17f), C(0.6f, 0.4f, 0.05f),
                C(0.2f, 0.21f, 0.23f), C(0.12f, 0.14f, 0.17f));
            break;
        case ESpecies::CommonMerganser:
            Info = MakeInfo(Species, EHabitat::Pool, EBody::Duck, ECall::None, 0.65f,
                C(0.25f, 0.25f, 0.27f), C(0.35f, 0.08f, 0.03f), C(0.25f, 0.25f, 0.27f), C(0.6f, 0.05f, 0.02f),
                White, C(0.2f, 0.2f, 0.22f));
            break;
        case ESpecies::TorrentDuck:
            Info = MakeInfo(Species, EHabitat::Rapid, EBody::Duck, ECall::TorrentDuck, 0.45f,
                C(0.05f, 0.05f, 0.05f), White, C(0.06f, 0.06f, 0.06f), C(0.6f, 0.06f, 0.03f),
                C(0.06f, 0.06f, 0.06f), C(0.05f, 0.05f, 0.05f));
            break;
        case ESpecies::HarlequinDuck:
            Info = MakeInfo(Species, EHabitat::Rapid, EBody::Duck, ECall::None, 0.42f,
                C(0.06f, 0.08f, 0.13f), C(0.06f, 0.08f, 0.13f), C(0.06f, 0.08f, 0.13f), C(0.3f, 0.08f, 0.03f),
                C(0.06f, 0.08f, 0.13f), C(0.03f, 0.03f, 0.04f));
            break;
        case ESpecies::MantledHowler:
            Info = MakeInfo(Species, EHabitat::Canopy, EBody::Monkey, ECall::MantledHowler, 0.55f,
                C(0.015f, 0.012f, 0.01f), C(0.015f, 0.012f, 0.01f), C(0.015f, 0.012f, 0.01f), C(0.3f, 0.18f, 0.06f),
                C(0.02f, 0.015f, 0.012f), C(0.015f, 0.012f, 0.01f));
            break;
        case ESpecies::KeelBilledToucan:
            Info = MakeInfo(Species, EHabitat::Canopy, EBody::PerchedBird, ECall::KeelBilledToucan, 0.5f,
                Black, C(0.8f, 0.65f, 0.05f), Black, C(0.15f, 0.45f, 0.08f), C(0.6f, 0.03f, 0.02f), Black);
            break;
        case ESpecies::MontezumaOropendola:
            Info = MakeInfo(Species, EHabitat::Canopy, EBody::PerchedBird, ECall::MontezumaOropendola, 0.48f,
                C(0.2f, 0.06f, 0.02f), Black, C(0.2f, 0.06f, 0.02f), C(0.6f, 0.25f, 0.03f), C(0.2f, 0.06f, 0.02f),
                C(0.8f, 0.65f, 0.05f));
            break;
        case ESpecies::DesertBighorn:
            Info = MakeInfo(Species, EHabitat::Cliff, EBody::Quadruped, ECall::BighornClash, 1.6f,
                C(0.35f, 0.25f, 0.15f), C(0.35f, 0.25f, 0.15f), C(0.3f, 0.22f, 0.13f), C(0.45f, 0.38f, 0.28f),
                C(0.75f, 0.72f, 0.65f), C(0.2f, 0.14f, 0.08f));
            break;
        case ESpecies::BlackTailedDeer:
            Info = MakeInfo(Species, EHabitat::Bank, EBody::Quadruped, ECall::None, 1.5f,
                C(0.18f, 0.13f, 0.08f), C(0.18f, 0.13f, 0.08f), C(0.15f, 0.11f, 0.07f), C(0.15f, 0.11f, 0.07f),
                C(0.6f, 0.58f, 0.52f), Black);
            break;
        case ESpecies::GrizzlyBear:
            Info = MakeInfo(Species, EHabitat::Shore, EBody::Quadruped, ECall::None, 2.0f,
                C(0.12f, 0.07f, 0.035f), C(0.14f, 0.09f, 0.05f), C(0.08f, 0.05f, 0.025f), C(0.3f, 0.25f, 0.18f),
                C(0.1f, 0.06f, 0.03f), C(0.12f, 0.07f, 0.035f));
            break;
        case ESpecies::ChacmaBaboon:
            Info = MakeInfo(Species, EHabitat::Cliff, EBody::Quadruped, ECall::ChacmaBaboon, 0.8f,
                C(0.13f, 0.11f, 0.08f), C(0.04f, 0.035f, 0.03f), C(0.09f, 0.075f, 0.055f), C(0.04f, 0.035f, 0.03f),
                C(0.13f, 0.11f, 0.08f), C(0.1f, 0.085f, 0.06f));
            break;
        case ESpecies::Hippopotamus:
            Info = MakeInfo(Species, EHabitat::Pool, EBody::Hippo, ECall::Hippo, 3.5f,
                C(0.12f, 0.1f, 0.09f), C(0.12f, 0.1f, 0.09f), C(0.12f, 0.1f, 0.09f), C(0.45f, 0.2f, 0.18f),
                C(0.4f, 0.22f, 0.2f), C(0.12f, 0.1f, 0.09f));
            break;
        case ESpecies::NileCrocodile:
            // Juveniles, 0.6-1.2 m, basking on rocks at the waterline.
            Info = MakeInfo(Species, EHabitat::Rock, EBody::Crocodile, ECall::None, 1.2f,
                C(0.08f, 0.09f, 0.05f), C(0.08f, 0.09f, 0.05f), C(0.07f, 0.08f, 0.045f), C(0.6f, 0.5f, 0.35f),
                C(0.4f, 0.38f, 0.28f), C(0.08f, 0.09f, 0.05f));
            break;
        case ESpecies::SockeyeSalmon:
            // Bunched in the eddies along the canyon walls, leaping.
            Info = MakeInfo(Species, EHabitat::Pool, EBody::Fish, ECall::SalmonSplash, 0.55f,
                C(0.6f, 0.04f, 0.03f), C(0.08f, 0.2f, 0.08f), C(0.6f, 0.04f, 0.03f), C(0.08f, 0.2f, 0.08f),
                C(0.6f, 0.04f, 0.03f), C(0.08f, 0.2f, 0.08f));
            break;
        case ESpecies::AustralParakeet:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Flapper, ECall::AustralParakeet, 0.4f,
                C(0.12f, 0.3f, 0.06f), C(0.12f, 0.3f, 0.06f), C(0.1f, 0.25f, 0.05f), C(0.5f, 0.08f, 0.03f),
                C(0.15f, 0.32f, 0.08f), C(0.5f, 0.08f, 0.03f));
            break;
        case ESpecies::TrumpeterHornbill:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Flapper, ECall::TrumpeterHornbill, 0.95f,
                Black, Black, Black, C(0.4f, 0.38f, 0.35f), White, Black);
            break;
        case ESpecies::Sunbittern:
            // Barred grey-brown, the spread wings flashing orange eyespots.
            Info = MakeInfo(Species, EHabitat::Shore, EBody::Heron, ECall::Sunbittern, 0.75f,
                C(0.15f, 0.13f, 0.1f), C(0.04f, 0.035f, 0.03f), C(0.18f, 0.14f, 0.08f), C(0.6f, 0.3f, 0.05f),
                C(0.6f, 0.3f, 0.05f), C(0.15f, 0.13f, 0.1f));
            break;
        case ESpecies::FasciatedTigerHeron:
            Info = MakeInfo(Species, EHabitat::Rock, EBody::Heron, ECall::None, 1.0f,
                C(0.06f, 0.065f, 0.07f), C(0.05f, 0.05f, 0.05f), C(0.07f, 0.07f, 0.075f), C(0.15f, 0.15f, 0.1f),
                C(0.2f, 0.18f, 0.14f), C(0.06f, 0.065f, 0.07f));
            break;
        case ESpecies::SouthernLapwing:
            Info = MakeInfo(Species, EHabitat::Shore, EBody::Heron, ECall::SouthernLapwing, 0.55f,
                C(0.25f, 0.22f, 0.18f), C(0.03f, 0.03f, 0.03f), C(0.25f, 0.22f, 0.18f), C(0.5f, 0.1f, 0.08f),
                White, C(0.03f, 0.03f, 0.03f));
            break;
        case ESpecies::BlackFacedIbis:
            Info = MakeInfo(Species, EHabitat::Sky, EBody::Flapper, ECall::BlackFacedIbis, 1.3f,
                C(0.25f, 0.25f, 0.25f), C(0.5f, 0.4f, 0.25f), C(0.12f, 0.12f, 0.12f), Black,
                C(0.15f, 0.15f, 0.15f), Black);
            break;
        case ESpecies::RockPratincole:
            Info = MakeInfo(Species, EHabitat::Rock, EBody::PerchedBird, ECall::RockPratincole, 0.19f,
                C(0.08f, 0.07f, 0.06f), White, C(0.08f, 0.07f, 0.06f), C(0.6f, 0.2f, 0.15f),
                C(0.08f, 0.07f, 0.06f), C(0.05f, 0.045f, 0.04f));
            break;
        case ESpecies::RedShoulderedHawk:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::RedShoulderedHawk, 0.5f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::AcornWoodpecker:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::AcornWoodpecker, 0.2f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::RingedKingfisher:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::RingedKingfisher, 0.4f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::BeltedKingfisher:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::BeltedKingfisher, 0.3f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::RedWingedStarling:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::RedWingedStarling, 0.3f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::CanyonWren:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::CanyonWren, 0.14f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::AmericanDipper:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::AmericanDipper, 0.18f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::Chucao:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::Chucao, 0.18f,
                Black, Black, Black, Black, Black, Black);
            break;
        case ESpecies::Cicadas:
            Info = MakeInfo(Species, EHabitat::Voice, EBody::None, ECall::Cicadas, 0.05f,
                Black, Black, Black, Black, Black, Black);
            break;
    }
    return Info;
}

TArray<FRaftSimWildlifeSpeciesInfo> GetRiverWildlife(const FString& MapName)
{
    const FString Leaf = MapLeaf(MapName);
    TArray<FRaftSimWildlifeSpeciesInfo> Table;
    auto Add = [&Table](ESpecies Species, int32 MaxNearby, int32 GroupMin = 1, int32 GroupMax = 1,
        float AltitudeMin = 30.0f, float AltitudeMax = 90.0f, float SpawnChance = 0.7f) -> FRaftSimWildlifeSpeciesInfo&
    {
        FRaftSimWildlifeSpeciesInfo& Info = Table.Add_GetRef(
            WithNumbers(GetWildlifeSpeciesInfo(Species), MaxNearby, GroupMin, GroupMax, AltitudeMin, AltitudeMax));
        Info.SpawnChance = SpawnChance;
        return Info;
    };
    // Species, numbers and habitats follow docs/river-wildlife-reference.md.
    if (Leaf == TEXT("L_SouthForkAmerican_FullReach") || Leaf == TEXT("L_SouthFork_Troublemaker"))
    {
        // Bald eagles mostly toward the lower Gorge, perched or soaring
        // 50-300 m up; hawks and woodpeckers heard from the bank oaks.
        Add(ESpecies::BaldEagle, 1, 1, 1, 50.0f, 200.0f, 0.5f);
        Add(ESpecies::TurkeyVulture, 2, 1, 3, 30.0f, 200.0f);
        Add(ESpecies::CommonMerganser, 1, 1, 6);
        Add(ESpecies::GreatBlueHeron, 1);
        Add(ESpecies::RedShoulderedHawk, 1);
        Add(ESpecies::AcornWoodpecker, 1);
    }
    else if (Leaf == TEXT("L_Hance"))
    {
        // Condors high on the walls; bighorn on talus and at the water;
        // the canyon wren's cascade off the cliffs. No turkey vultures
        // above river mile 150.
        Add(ESpecies::CaliforniaCondor, 1, 1, 3, 100.0f, 400.0f);
        Add(ESpecies::DesertBighorn, 1, 2, 6);
        Add(ESpecies::CommonRaven, 1, 1, 2, 30.0f, 150.0f);
        Add(ESpecies::GreatBlueHeron, 1);
        Add(ESpecies::CanyonWren, 2);
        Add(ESpecies::Cicadas, 1);
    }
    else if (Leaf == TEXT("L_UpperHuacas"))
    {
        Add(ESpecies::MantledHowler, 2, 2, 4);
        Add(ESpecies::MontezumaOropendola, 1, 1, 3);
        Add(ESpecies::KeelBilledToucan, 1, 1, 3);
        Add(ESpecies::Sunbittern, 1);
        Add(ESpecies::FasciatedTigerHeron, 1);
        Add(ESpecies::RingedKingfisher, 1);
        Add(ESpecies::Cicadas, 2);
    }
    else if (Leaf == TEXT("L_Terminator"))
    {
        // Torrent ducks are not documented on the main stem: a rare pair.
        Add(ESpecies::AndeanCondor, 1, 1, 3, 100.0f, 500.0f);
        Add(ESpecies::BlackFacedIbis, 1, 4, 10, 15.0f, 60.0f);
        Add(ESpecies::SouthernLapwing, 1, 1, 2);
        Add(ESpecies::Chucao, 1);
        Add(ESpecies::RingedKingfisher, 1);
        Add(ESpecies::AustralParakeet, 1, 6, 10, 10.0f, 30.0f, 0.4f);
        Add(ESpecies::TorrentDuck, 1, 2, 2, 30.0f, 90.0f, 0.1f);
    }
    else if (Leaf == TEXT("L_LavaCanyon"))
    {
        // Salmon schooling and leaping in the wall eddies (late August);
        // a bear is a rare bonus in the canyon.
        Add(ESpecies::SockeyeSalmon, 2, 3, 6);
        Add(ESpecies::BaldEagle, 1, 1, 1, 25.0f, 90.0f);
        Add(ESpecies::Osprey, 1, 1, 1, 15.0f, 45.0f);
        Add(ESpecies::CommonMerganser, 1, 6, 12).bBrood = true;
        Add(ESpecies::CommonRaven, 1, 1, 2, 20.0f, 80.0f);
        Add(ESpecies::GrizzlyBear, 1, 1, 1, 30.0f, 90.0f, 0.08f);
        Add(ESpecies::BeltedKingfisher, 1);
    }
    else if (Leaf == TEXT("L_Zambezi") || Leaf == TEXT("L_ZambeziUpperGorge"))
    {
        // No hippos on the Batoka rapids (they live above the falls); the
        // gorge's animals are cliff dwellers, and rock pratincoles sit on
        // the rocks in the rapids.
        Add(ESpecies::ChacmaBaboon, 1, 5, 10);
        Add(ESpecies::VerreauxsEagle, 1, 1, 2, 100.0f, 300.0f);
        Add(ESpecies::RockPratincole, 2, 2, 6);
        Add(ESpecies::NileCrocodile, 1, 1, 1, 30.0f, 90.0f, 0.5f);
        Add(ESpecies::AfricanFishEagle, 1, 1, 1, 20.0f, 80.0f, 0.2f);
        Add(ESpecies::TrumpeterHornbill, 1, 2, 4, 15.0f, 40.0f);
        Add(ESpecies::RedWingedStarling, 2);
        Add(ESpecies::Cicadas, 1);
    }
    return Table;
}

ARaftSimWildlifeCreature::ARaftSimWildlifeCreature()
{
    PrimaryActorTick.bCanEverTick = true;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("Pivot"));
    Pivot->SetupAttachment(Root);
    SetActorEnableCollision(false);
}

UMaterialInterface* ARaftSimWildlifeCreature::Tint(const FLinearColor& Color, bool bGlossy)
{
    // Feathers and fur read matte; bills, eyes and wet hide take a sheen.
    UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, bGlossy
        ? TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet")
        : TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"));
    if (!Base)
    {
        return nullptr;
    }
    UMaterialInstanceDynamic* Instance = UMaterialInstanceDynamic::Create(Base, this);
    Instance->SetVectorParameterValue(TEXT("BaseTint"), Color);
    return Instance;
}

UProceduralMeshComponent* ARaftSimWildlifeCreature::AddPart(const TCHAR* Name, USceneComponent* Parent, const FVector& OffsetCm)
{
    UProceduralMeshComponent* Part = NewObject<UProceduralMeshComponent>(this, Name);
    Part->SetupAttachment(Parent);
    Part->SetRelativeLocation(OffsetCm);
    Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Part->SetCastShadow(true);
    Part->RegisterComponent();
    return Part;
}

namespace
{
/** Wing planform for a soaring or flapping bird: inner panel plus splayed
 * primaries ("fingers") at the tip. Built along +Y (right wing); Side -1
 * mirrors it. Two plates: upper colour above, underwing colour below. */
void BuildWing(FWildShape& Upper, FWildShape& Lower, float Span, float RootChord, float MidChord, int32 Fingers,
    float Side, bool bPointed)
{
    const float Mid = Span * (bPointed ? 0.55f : 0.65f);
    auto Mirror = [Side](const TArray<FVector2D>& Outline)
    {
        TArray<FVector2D> Out;
        for (const FVector2D& P : Outline)
        {
            Out.Add(FVector2D(P.X, P.Y * Side));
        }
        return Out;
    };
    TArray<FVector2D> Inner = {{0.3f * RootChord, 0.0f}, {0.3f * MidChord, Mid}, {-0.7f * MidChord, Mid}, {-0.7f * RootChord, 0.0f}};
    const FTransform Up(FVector(0, 0, 0.4f));
    const FTransform Down(FVector(0, 0, -0.4f));
    Upper.Slab(Mirror(Inner), 0.6f, Up);
    Lower.Slab(Mirror(Inner), 0.6f, Down);
    if (bPointed)
    {
        TArray<FVector2D> Tip = {{0.3f * MidChord, Mid}, {-0.1f * MidChord, Span}, {-0.7f * MidChord, Mid}};
        Upper.Slab(Mirror(Tip), 0.5f, Up);
        Lower.Slab(Mirror(Tip), 0.5f, Down);
        return;
    }
    // The splayed primaries of a soaring broad wing.
    for (int32 Finger = 0; Finger < Fingers; ++Finger)
    {
        const float X = 0.3f * MidChord - (Finger + 0.5f) * MidChord / Fingers;
        const float Width = 0.85f * MidChord / Fingers;
        const float Reach = (Span - Mid) * (0.7f + 0.3f * FMath::Sin(PI * (Finger + 0.5f) / Fingers));
        const float Splay = FMath::DegreesToRadians((Finger - 0.5f * (Fingers - 1)) * 4.0f);
        const FVector2D Dir(-FMath::Sin(Splay), FMath::Cos(Splay));
        const FVector2D Base(X, Mid);
        const FVector2D Across(Dir.Y, -Dir.X);
        TArray<FVector2D> Feather = {Base + Across * Width * 0.5f, Base + Dir * Reach * 0.9f + Across * Width * 0.35f,
            Base + Dir * Reach, Base + Dir * Reach * 0.9f - Across * Width * 0.35f, Base - Across * Width * 0.5f};
        Upper.Slab(Mirror(Feather), 0.4f, Up);
    }
}
}

void ARaftSimWildlifeCreature::BuildBody()
{
    const float Size = Info.SizeMeters * 100.0f;
    auto Commit = [this](UProceduralMeshComponent* Part, const FWildShape& Shape, int32 Section, const FLinearColor& Color,
        bool bGlossy = false)
    {
        if (Part && Shape.V.Num() > 0)
        {
            Shape.Commit(Part, Section);
            Part->SetMaterial(Section, Tint(Color, bGlossy));
        }
    };
    switch (Info.Body)
    {
        case EBody::Soarer:
        case EBody::Flapper:
        {
            const bool bSoarer = Info.Body == EBody::Soarer;
            const float W = Size;
            const float L = (bSoarer ? 0.42f : 0.5f) * W;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector::ZeroVector);
            FWildShape Torso, Belly;
            Torso.Ellipsoid(FVector::ZeroVector, FVector(0.3f * L, 0.12f * L, 0.11f * L));
            Belly.Ellipsoid(FVector(0.0f, 0.0f, -0.02f * L), FVector(0.27f * L, 0.112f * L, 0.1f * L));
            Commit(BodyPart, Torso, 0, Info.Body0);
            Commit(BodyPart, Belly, 1, Info.Under);
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.28f * L, 0.0f, 0.03f * L));
            FWildShape Head, Bill;
            Head.Ellipsoid(FVector(0.06f * L, 0, 0), FVector(0.1f * L, 0.07f * L, 0.075f * L));
            Bill.Cone(FVector(0.14f * L, 0, 0), FVector(0.24f * L, 0, -0.035f * L), 0.035f * L, 0.006f * L, 6);
            Commit(HeadPart, Head, 0, Info.Head);
            Commit(HeadPart, Bill, 1, Info.Accent, true);
            if (Info.Species == ESpecies::AndeanCondor)
            {
                // The white ruff at the base of the bare neck.
                FWildShape Ruff;
                Ruff.Ellipsoid(FVector(-0.02f * L, 0, 0), FVector(0.05f * L, 0.1f * L, 0.09f * L));
                Commit(HeadPart, Ruff, 2, Info.Accent);
            }
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.27f * L, 0.0f, 0.0f));
            FWildShape Tail;
            const float TailLength = (bSoarer ? 0.3f : 0.38f) * L;
            Tail.Slab({{0.0f, -0.06f * L}, {0.0f, 0.06f * L}, {-TailLength, 0.13f * L}, {-TailLength, -0.13f * L}}, 0.8f,
                FTransform::Identity);
            Commit(TailPart, Tail, 0, Info.Tail);
            const float Span = 0.5f * W - 0.09f * L;
            for (const float Side : {-1.0f, 1.0f})
            {
                UProceduralMeshComponent* Wing = AddPart(Side < 0 ? TEXT("WingL") : TEXT("WingR"), BodyPart,
                    FVector(0.05f * L, Side * 0.09f * L, 0.03f * L));
                FWildShape Upper, Lower;
                const bool bPointed = Info.Species == ESpecies::AustralParakeet;
                BuildWing(Upper, Lower, Span, (bSoarer ? 0.24f : 0.22f) * W, (bSoarer ? 0.2f : 0.17f) * W,
                    bSoarer ? 6 : 5, Side, bPointed);
                Commit(Wing, Upper, 0, Info.Limbs);
                Commit(Wing, Lower, 1, Info.Under);
                WingParts.Add(Wing);
            }
            break;
        }
        case EBody::Heron:
        {
            const float W = Size;
            const float L = 0.64f * W;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector(0.0f, 0.0f, 0.62f * L));
            FWildShape Torso;
            Torso.Ellipsoid(FVector::ZeroVector, FVector(0.22f * L, 0.1f * L, 0.12f * L), FRotator(20.0f, 0, 0));
            Commit(BodyPart, Torso, 0, Info.Body0);
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.17f * L, 0.0f, 0.1f * L));
            FWildShape Neck, Head, Bill;
            Neck.Cone(FVector::ZeroVector, FVector(0.04f * L, 0, 0.16f * L), 0.04f * L, 0.03f * L);
            Neck.Cone(FVector(0.04f * L, 0, 0.16f * L), FVector(0.0f, 0, 0.3f * L), 0.03f * L, 0.028f * L);
            Head.Ellipsoid(FVector(0.04f * L, 0, 0.32f * L), FVector(0.07f * L, 0.04f * L, 0.045f * L));
            Bill.Cone(FVector(0.1f * L, 0, 0.32f * L), FVector(0.3f * L, 0, 0.3f * L), 0.018f * L, 0.003f * L, 6);
            Commit(HeadPart, Neck, 0, Info.Under);
            Commit(HeadPart, Head, 1, Info.Head);
            Commit(HeadPart, Bill, 2, Info.Accent, true);
            for (const float Side : {-1.0f, 1.0f})
            {
                UProceduralMeshComponent* Leg = AddPart(Side < 0 ? TEXT("LegL") : TEXT("LegR"), BodyPart,
                    FVector(-0.02f * L, Side * 0.04f * L, -0.05f * L));
                FWildShape Shank;
                Shank.Cone(FVector::ZeroVector, FVector(0.0f, Side * 0.01f * L, -0.58f * L), 0.014f * L, 0.01f * L, 6);
                Commit(Leg, Shank, 0, Info.Accent);
                LegParts.Add(Leg);
                UProceduralMeshComponent* Wing = AddPart(Side < 0 ? TEXT("WingL") : TEXT("WingR"), BodyPart,
                    FVector(0.05f * L, Side * 0.08f * L, 0.05f * L));
                FWildShape Upper, Lower;
                BuildWing(Upper, Lower, 0.5f * W - 0.08f * L, 0.2f * W, 0.17f * W, 5, Side, false);
                Commit(Wing, Upper, 0, Info.Limbs);
                Commit(Wing, Lower, 1, Info.Under);
                WingParts.Add(Wing);
            }
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.2f * L, 0.0f, -0.05f * L));
            FWildShape Tail;
            Tail.Slab({{0.0f, -0.04f * L}, {0.0f, 0.04f * L}, {-0.12f * L, 0.05f * L}, {-0.12f * L, -0.05f * L}}, 0.8f,
                FTransform::Identity);
            Commit(TailPart, Tail, 0, Info.Tail);
            break;
        }
        case EBody::Duck:
        {
            const float L = Size;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector::ZeroVector);
            FWildShape Torso, Flank;
            Torso.Ellipsoid(FVector(0, 0, 0.04f * L), FVector(0.42f * L, 0.2f * L, 0.15f * L));
            Flank.Ellipsoid(FVector(-0.03f * L, 0, 0.07f * L), FVector(0.33f * L, 0.205f * L, 0.1f * L));
            Commit(BodyPart, Torso, 0, Info.Body0);
            Commit(BodyPart, Flank, 1, Info.Species == ESpecies::HarlequinDuck ? Info.Accent : Info.Limbs);
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.3f * L, 0.0f, 0.12f * L));
            FWildShape Neck, Head, Bill;
            Neck.Cone(FVector::ZeroVector, FVector(0.04f * L, 0, 0.18f * L), 0.08f * L, 0.07f * L);
            Head.Ellipsoid(FVector(0.06f * L, 0, 0.22f * L), FVector(0.12f * L, 0.08f * L, 0.09f * L));
            Bill.Cone(FVector(0.16f * L, 0, 0.2f * L), FVector(0.3f * L, 0, 0.18f * L), 0.035f * L, 0.02f * L, 6);
            Commit(HeadPart, Neck, 0, Info.Head);
            Commit(HeadPart, Head, 1, Info.Head);
            Commit(HeadPart, Bill, 2, Info.Accent, true);
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.38f * L, 0.0f, 0.08f * L));
            FWildShape Tail;
            Tail.Slab({{0.0f, -0.07f * L}, {0.0f, 0.07f * L}, {-0.14f * L, 0.05f * L}, {-0.14f * L, -0.05f * L}}, 0.6f,
                FTransform(FRotator(20.0f, 0, 0)));
            Commit(TailPart, Tail, 0, Info.Tail);
            for (const float Side : {-1.0f, 1.0f})
            {
                // Folded until the duck flushes and flies.
                UProceduralMeshComponent* Wing = AddPart(Side < 0 ? TEXT("WingL") : TEXT("WingR"), BodyPart,
                    FVector(0.08f * L, Side * 0.15f * L, 0.12f * L));
                FWildShape Upper, Lower;
                BuildWing(Upper, Lower, 0.65f * L, 0.25f * L, 0.18f * L, 4, Side, true);
                Commit(Wing, Upper, 0, Info.Limbs);
                Commit(Wing, Lower, 1, Info.Under);
                WingParts.Add(Wing);
            }
            break;
        }
        case EBody::Monkey:
        {
            const float L = Size;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector::ZeroVector);
            FWildShape Torso, Mantle, Limbs, Branch;
            Torso.Ellipsoid(FVector(0, 0, 0.3f * L), FVector(0.24f * L, 0.21f * L, 0.32f * L), FRotator(-15.0f, 0, 0));
            // The mantled howler's golden-brown flank fringe.
            Mantle.Ellipsoid(FVector(-0.03f * L, 0, 0.22f * L), FVector(0.2f * L, 0.225f * L, 0.18f * L));
            for (const float Side : {-1.0f, 1.0f})
            {
                Limbs.Cone(FVector(0.06f * L, Side * 0.16f * L, 0.48f * L), FVector(0.26f * L, Side * 0.13f * L, 0.04f * L),
                    0.06f * L, 0.045f * L);
                Limbs.Cone(FVector(-0.04f * L, Side * 0.13f * L, 0.12f * L), FVector(0.2f * L, Side * 0.17f * L, 0.24f * L),
                    0.07f * L, 0.05f * L);
                Limbs.Cone(FVector(0.2f * L, Side * 0.17f * L, 0.24f * L), FVector(0.16f * L, Side * 0.1f * L, 0.0f),
                    0.05f * L, 0.04f * L);
            }
            // A bough to sit on, in case the tree's own branch is not right here.
            Branch.Cone(FVector(-0.05f * L, -1.2f * L, -0.06f * L), FVector(0.1f * L, 1.2f * L, -0.02f * L), 0.07f * L, 0.05f * L);
            Commit(BodyPart, Torso, 0, Info.Body0);
            Commit(BodyPart, Mantle, 1, Info.Accent);
            Commit(BodyPart, Limbs, 2, Info.Limbs);
            Commit(BodyPart, Branch, 3, C(0.07f, 0.05f, 0.035f));
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.1f * L, 0.0f, 0.6f * L));
            FWildShape Head;
            Head.Ellipsoid(FVector(0.02f * L, 0, 0.05f * L), FVector(0.13f * L, 0.12f * L, 0.13f * L));
            Head.Ellipsoid(FVector(0.12f * L, 0, -0.01f * L), FVector(0.08f * L, 0.085f * L, 0.08f * L));
            Commit(HeadPart, Head, 0, Info.Head);
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.2f * L, 0.0f, 0.1f * L));
            FWildShape Tail;
            Tail.Cone(FVector::ZeroVector, FVector(-0.08f * L, 0, -0.8f * L), 0.035f * L, 0.03f * L);
            Tail.Cone(FVector(-0.08f * L, 0, -0.8f * L), FVector(0.05f * L, 0, -1.2f * L), 0.03f * L, 0.02f * L);
            Tail.Cone(FVector(0.05f * L, 0, -1.2f * L), FVector(0.12f * L, 0, -1.05f * L), 0.02f * L, 0.015f * L);
            Commit(TailPart, Tail, 0, Info.Tail);
            break;
        }
        case EBody::PerchedBird:
        {
            const float L = Size;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector::ZeroVector);
            FWildShape Torso, Bib, Branch;
            Torso.Ellipsoid(FVector(0, 0, 0.28f * L), FVector(0.2f * L, 0.13f * L, 0.26f * L), FRotator(-30.0f, 0, 0));
            Bib.Ellipsoid(FVector(0.1f * L, 0, 0.4f * L), FVector(0.1f * L, 0.115f * L, 0.12f * L));
            if (Info.Habitat != EHabitat::Rock)
            {
                Branch.Cone(FVector(-0.05f * L, -1.0f * L, -0.03f * L), FVector(0.05f * L, 1.0f * L, -0.01f * L), 0.05f * L, 0.04f * L);
            }
            Commit(BodyPart, Torso, 0, Info.Body0);
            Commit(BodyPart, Bib, 1, Info.Head);
            Commit(BodyPart, Branch, 2, C(0.07f, 0.05f, 0.035f));
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.06f * L, 0.0f, 0.56f * L));
            FWildShape Head, Bill;
            Head.Ellipsoid(FVector::ZeroVector, FVector(0.11f * L, 0.09f * L, 0.1f * L));
            if (Info.Species == ESpecies::KeelBilledToucan)
            {
                // The huge, light bill.
                Bill.Ellipsoid(FVector(0.27f * L, 0, -0.02f * L), FVector(0.22f * L, 0.05f * L, 0.08f * L), FRotator(-8.0f, 0, 0));
            }
            else
            {
                Bill.Cone(FVector(0.08f * L, 0, 0), FVector(0.3f * L, 0, -0.03f * L), 0.05f * L, 0.008f * L, 6);
            }
            Commit(HeadPart, Head, 0, Info.Body0);
            Commit(HeadPart, Bill, 1, Info.Accent, true);
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.12f * L, 0.0f, 0.12f * L));
            FWildShape Tail;
            Tail.Slab({{0.0f, -0.06f * L}, {0.0f, 0.06f * L}, {-0.5f * L, 0.07f * L}, {-0.5f * L, -0.07f * L}}, 0.8f,
                FTransform(FRotator(-60.0f, 0, 0)));
            Commit(TailPart, Tail, 0, Info.Tail);
            break;
        }
        case EBody::Quadruped:
        {
            const float L = Size;
            const bool bBear = Info.Species == ESpecies::GrizzlyBear;
            const bool bBaboon = Info.Species == ESpecies::ChacmaBaboon;
            const bool bSheep = Info.Species == ESpecies::DesertBighorn;
            const float Leg = L * (bBear ? 0.3f : (bBaboon ? 0.36f : (bSheep ? 0.45f : 0.52f)));
            const FVector BodyR = bBear ? FVector(0.48f * L, 0.24f * L, 0.25f * L) : FVector(0.44f * L, 0.15f * L, 0.18f * L);
            const float BodyZ = Leg + BodyR.Z * 0.7f;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector(0.0f, 0.0f, BodyZ));
            FWildShape Torso, Rump;
            Torso.Ellipsoid(FVector::ZeroVector, BodyR);
            if (bBear)
            {
                Torso.Ellipsoid(FVector(0.22f * L, 0, 0.15f * L), FVector(0.2f * L, 0.2f * L, 0.16f * L));
            }
            Rump.Ellipsoid(FVector(-0.36f * L, 0, 0.02f * L), FVector(0.1f * L, 0.12f * L, 0.13f * L));
            Commit(BodyPart, Torso, 0, Info.Body0);
            Commit(BodyPart, Rump, 1, Info.Under);
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.4f * L, 0.0f, 0.08f * L));
            FWildShape Neck, Head, Extras;
            const float HeadUp = bBear ? 0.05f * L : (bBaboon ? 0.08f * L : (bSheep ? 0.12f * L : 0.17f * L));
            Neck.Cone(FVector::ZeroVector, FVector(0.1f * L, 0, HeadUp), (bBear ? 0.14f : 0.07f) * L, (bBear ? 0.11f : 0.055f) * L);
            const FVector HeadCenter(0.14f * L, 0, HeadUp + 0.02f * L);
            Head.Ellipsoid(HeadCenter, bBear ? FVector(0.13f * L, 0.11f * L, 0.1f * L) : FVector(0.09f * L, 0.06f * L, 0.065f * L));
            // Muzzle: a baboon's long dog-like snout, a bear's broad one.
            Head.Ellipsoid(HeadCenter + FVector((bBaboon ? 0.12f : 0.09f) * L, 0, -0.025f * L),
                FVector((bBaboon ? 0.09f : 0.06f) * L, (bBear ? 0.06f : 0.035f) * L, (bBear ? 0.05f : 0.035f) * L));
            for (const float Side : {-1.0f, 1.0f})
            {
                if (bSheep)
                {
                    // Massive horns curling back, down and forward.
                    FVector Prev = HeadCenter + FVector(0.0f, Side * 0.045f * L, 0.05f * L);
                    for (int32 Step = 1; Step <= 8; ++Step)
                    {
                        const float A = Step / 8.0f * 1.7f * PI;
                        const FVector Next = HeadCenter + FVector(-0.12f * L * FMath::Sin(A), Side * (0.06f + 0.05f * Step / 8.0f) * L,
                            0.05f * L + 0.12f * L * (FMath::Cos(A) - 1.0f) * 0.5f);
                        Extras.Cone(Prev, Next, (0.06f - 0.005f * Step) * L, (0.055f - 0.005f * Step) * L, 8);
                        Prev = Next;
                    }
                }
                else
                {
                    const float Ear = Info.Species == ESpecies::BlackTailedDeer ? 0.07f * L : 0.03f * L;
                    Extras.Ellipsoid(HeadCenter + FVector(-0.03f * L, Side * 0.05f * L, 0.06f * L),
                        FVector(0.015f * L, Ear * 0.5f, Ear), FRotator(0, 0, Side * 30.0f), 6, 4);
                }
            }
            Commit(HeadPart, Neck, 0, Info.Body0);
            Commit(HeadPart, Head, 1, Info.Head);
            Commit(HeadPart, Extras, 2, bSheep ? Info.Accent : Info.Limbs);
            for (int32 Index = 0; Index < 4; ++Index)
            {
                const float X = (Index < 2 ? 0.3f : -0.3f) * L;
                const float Y = (Index % 2 == 0 ? -1.0f : 1.0f) * BodyR.Y * 0.6f;
                UProceduralMeshComponent* LegPart = AddPart(*FString::Printf(TEXT("Leg%d"), Index), BodyPart,
                    FVector(X, Y, -BodyR.Z * 0.5f));
                FWildShape Limb;
                const float Reach = BodyZ - BodyR.Z * 0.5f;
                Limb.Cone(FVector::ZeroVector, FVector(0, 0, -Reach), (bBear ? 0.08f : 0.045f) * L, (bBear ? 0.07f : 0.022f) * L);
                Commit(LegPart, Limb, 0, Info.Limbs);
                LegParts.Add(LegPart);
            }
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.43f * L, 0.0f, 0.06f * L));
            FWildShape Tail;
            if (bBaboon)
            {
                // The baboon's tail arches up from the rump and falls away.
                Tail.Cone(FVector::ZeroVector, FVector(-0.1f * L, 0, 0.12f * L), 0.03f * L, 0.025f * L);
                Tail.Cone(FVector(-0.1f * L, 0, 0.12f * L), FVector(-0.3f * L, 0, -0.3f * L), 0.025f * L, 0.018f * L);
            }
            else
            {
                Tail.Cone(FVector::ZeroVector, FVector(-0.06f * L, 0, -0.08f * L), 0.03f * L, 0.02f * L);
            }
            Commit(TailPart, Tail, 0, Info.Tail);
            break;
        }
        case EBody::Hippo:
        {
            const float L = Size;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector::ZeroVector);
            FWildShape Torso;
            Torso.Ellipsoid(FVector(0, 0, -0.17f * L), FVector(0.48f * L, 0.22f * L, 0.19f * L));
            Commit(BodyPart, Torso, 0, Info.Body0, true);
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.42f * L, 0.0f, -0.08f * L));
            FWildShape Head, Bumps, Eyes;
            Head.Ellipsoid(FVector(0.12f * L, 0, 0.0f), FVector(0.17f * L, 0.11f * L, 0.09f * L));
            Head.Ellipsoid(FVector(0.27f * L, 0, -0.01f * L), FVector(0.08f * L, 0.12f * L, 0.08f * L));
            for (const float Side : {-1.0f, 1.0f})
            {
                // Eyes, ears and nostrils ride high so they clear the water.
                Eyes.Ellipsoid(FVector(0.06f * L, Side * 0.065f * L, 0.08f * L), FVector(0.03f * L, 0.025f * L, 0.025f * L), FRotator::ZeroRotator, 8, 5);
                Bumps.Ellipsoid(FVector(0.3f * L, Side * 0.045f * L, 0.065f * L), FVector(0.025f * L, 0.02f * L, 0.015f * L), FRotator::ZeroRotator, 8, 5);
                UProceduralMeshComponent* EarPart = AddPart(Side < 0 ? TEXT("EarL") : TEXT("EarR"), HeadPart,
                    FVector(-0.01f * L, Side * 0.06f * L, 0.08f * L));
                FWildShape Ear;
                Ear.Ellipsoid(FVector(0, 0, 0.02f * L), FVector(0.012f * L, 0.02f * L, 0.03f * L), FRotator::ZeroRotator, 6, 4);
                Commit(EarPart, Ear, 0, Info.Accent);
                LegParts.Add(EarPart);
            }
            Commit(HeadPart, Head, 0, Info.Head, true);
            Commit(HeadPart, Bumps, 1, Info.Head, true);
            Commit(HeadPart, Eyes, 2, C(0.03f, 0.02f, 0.015f), true);
            JawPart = AddPart(TEXT("Jaw"), HeadPart, FVector(0.0f, 0.0f, -0.05f * L));
            FWildShape Jaw;
            Jaw.Ellipsoid(FVector(0.16f * L, 0, -0.02f * L), FVector(0.16f * L, 0.11f * L, 0.05f * L));
            Commit(JawPart, Jaw, 0, Info.Under, true);
            break;
        }
        case EBody::Crocodile:
        {
            const float L = Size;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector(0.0f, 0.0f, 0.05f * L));
            FWildShape Torso, Belly, Limbs;
            Torso.Ellipsoid(FVector::ZeroVector, FVector(0.24f * L, 0.1f * L, 0.05f * L));
            Belly.Ellipsoid(FVector(0, 0, -0.01f * L), FVector(0.22f * L, 0.095f * L, 0.045f * L));
            for (int32 Index = 0; Index < 4; ++Index)
            {
                const float X = (Index < 2 ? 0.14f : -0.14f) * L;
                const float Side = Index % 2 == 0 ? -1.0f : 1.0f;
                Limbs.Cone(FVector(X, Side * 0.08f * L, 0.0f), FVector(X + 0.02f * L, Side * 0.17f * L, -0.045f * L),
                    0.025f * L, 0.018f * L, 6);
            }
            Commit(BodyPart, Torso, 0, Info.Body0, true);
            Commit(BodyPart, Belly, 1, Info.Under);
            Commit(BodyPart, Limbs, 2, Info.Limbs);
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.22f * L, 0.0f, 0.0f));
            FWildShape Tail;
            Tail.Cone(FVector::ZeroVector, FVector(-0.2f * L, 0, -0.01f * L), 0.075f * L, 0.045f * L);
            Tail.Cone(FVector(-0.2f * L, 0, -0.01f * L), FVector(-0.42f * L, 0, -0.02f * L), 0.045f * L, 0.008f * L);
            Commit(TailPart, Tail, 0, Info.Body0, true);
            HeadPart = AddPart(TEXT("Head"), BodyPart, FVector(0.22f * L, 0.0f, 0.005f * L));
            FWildShape Head;
            Head.Ellipsoid(FVector(0.08f * L, 0, 0), FVector(0.1f * L, 0.06f * L, 0.035f * L));
            Head.Ellipsoid(FVector(0.24f * L, 0, -0.005f * L), FVector(0.12f * L, 0.035f * L, 0.022f * L));
            Commit(HeadPart, Head, 0, Info.Head, true);
            JawPart = AddPart(TEXT("Jaw"), HeadPart, FVector(0.03f * L, 0.0f, -0.025f * L));
            FWildShape Jaw;
            Jaw.Ellipsoid(FVector(0.17f * L, 0, -0.01f * L), FVector(0.19f * L, 0.045f * L, 0.016f * L));
            Commit(JawPart, Jaw, 0, Info.Accent);
            break;
        }
        case EBody::Fish:
        {
            const float L = Size;
            BodyPart = AddPart(TEXT("Body"), Pivot, FVector::ZeroVector);
            FWildShape Torso, Head;
            Torso.Ellipsoid(FVector::ZeroVector, FVector(0.4f * L, 0.08f * L, 0.14f * L));
            Head.Ellipsoid(FVector(0.3f * L, 0, -0.01f * L), FVector(0.15f * L, 0.075f * L, 0.1f * L));
            Commit(BodyPart, Torso, 0, Info.Body0, true);
            Commit(BodyPart, Head, 1, Info.Head, true);
            TailPart = AddPart(TEXT("Tail"), BodyPart, FVector(-0.38f * L, 0.0f, 0.0f));
            FWildShape Fin;
            Fin.Slab({{0.0f, -0.03f * L}, {0.0f, 0.03f * L}, {-0.16f * L, 0.12f * L}, {-0.16f * L, -0.12f * L}}, 0.5f,
                FTransform(FRotator(0, 0, 90.0f)));
            Commit(TailPart, Fin, 0, Info.Accent);
            break;
        }
        case EBody::None:
        default:
            break;
    }
}

void ARaftSimWildlifeCreature::Configure(ERaftSimWildlifeSpecies InSpecies, const FVector& HomeCm,
    const FVector& RiverDirection, float WaterZCm, uint32 Seed, const FVector& Facing)
{
    Species = InSpecies;
    Info = GetWildlifeSpeciesInfo(Species);
    Random.Initialize(static_cast<int32>(Seed));
    Home = HomeCm;
    River = RiverDirection.GetSafeNormal2D();
    if (River.IsNearlyZero())
    {
        River = FVector::ForwardVector;
    }
    WaterZ = WaterZCm;
    Heading = FMath::RadiansToDegrees(FMath::Atan2(River.Y, River.X)) + Random.FRandRange(-60.0f, 60.0f);
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        Bridge = GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    }
    BuildBody();
    // Soaring circles: wide and slow for condors, tighter for the rest.
    CircleRadius = Random.FRandRange(25.0f, 60.0f) * 100.0f * (Info.SizeMeters > 2.5f ? 1.6f : 1.0f);
    CircleAngle = Random.FRandRange(0.0f, UE_TWO_PI);
    CircleDirection = Random.FRand() < 0.5f ? -1.0f : 1.0f;
    Altitude = HomeCm.Z - WaterZCm;
    Lifetime = Random.FRandRange(70.0f, 200.0f);
    NextFlap = Random.FRandRange(3.0f, 12.0f);
    if (Info.Body == EBody::Hippo)
    {
        StateUntil = Random.FRandRange(10.0f, 40.0f);
    }
    if (Info.Body == EBody::Fish)
    {
        StateUntil = Random.FRandRange(1.0f, 5.0f);
        FlapUntil = -10.0f;
        Pivot->SetVisibility(false, true);
    }
    if (!Facing.IsNearlyZero())
    {
        // Perched, standing and basking animals face the water.
        Heading = FMath::RadiansToDegrees(FMath::Atan2(Facing.Y, Facing.X)) + Random.FRandRange(-25.0f, 25.0f);
    }
    if (Info.Call != ERaftSimWildlifeCall::None)
    {
        Voice = NewObject<UAudioComponent>(this, TEXT("Voice"));
        Voice->SetupAttachment(Pivot);
        Voice->bAutoActivate = false;
        Voice->bAllowSpatialization = true;
        float Inner = 25.0f, Falloff = 260.0f;
        RaftSimWildlife::GetCallRange(Info.Call, Inner, Falloff);
        FSoundAttenuationSettings Settings;
        Settings.bAttenuate = true;
        Settings.bSpatialize = true;
        Settings.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
        Settings.AttenuationShape = EAttenuationShape::Sphere;
        Settings.AttenuationShapeExtents = FVector(Inner * 100.0f, 0.0f, 0.0f);
        Settings.FalloffDistance = Falloff * 100.0f;
        Settings.dBAttenuationAtMax = -45.0f;
        Settings.bEnableReverbSend = true;
        Settings.ReverbSendMethod = EReverbSendMethod::Manual;
        Settings.ManualReverbSendLevel = 0.35f;
        Voice->bOverrideAttenuation = true;
        Voice->SetAttenuationOverrides(Settings);
        Voice->RegisterComponent();
        VoiceWave = NewObject<URaftSimCallSoundWave>(this);
        VoiceWave->InitializeVoice(Seed * 31u + 17u);
        Voice->SetSound(VoiceWave);
        Voice->Play();
        NextCall = Random.FRandRange(2.0f, 0.6f * RaftSimWildlife::NextCallInterval(Info.Call, Random));
    }
    SetActorLocation(Home);
    SetActorRotation(FRotator(0.0f, Heading, 0.0f));
    Animate(0.0f, 0.0f);
}

void ARaftSimWildlifeCreature::ConfigureForReview(ERaftSimWildlifeSpecies InSpecies, FVector HomeCm, float WaterZCm,
    float AnimationTime)
{
    bReview = true;
    Configure(InSpecies, HomeCm, FVector::ForwardVector, WaterZCm, 7u, FVector::ZeroVector);
    Heading = 0.0f;
    SetActorRotation(FRotator::ZeroRotator);
    if (Info.Body == EBody::Fish)
    {
        Pivot->SetVisibility(true, true);
    }
    Animate(AnimationTime, 0.0f);
    if (Info.Body == EBody::Soarer || Info.Body == EBody::Flapper)
    {
        // Review: hold the bird where it was put, wings spread.
        SetActorLocationAndRotation(HomeCm, FRotator::ZeroRotator);
        Pivot->SetRelativeRotation(FRotator::ZeroRotator);
    }
    else if (Info.Body == EBody::Fish)
    {
        SetActorLocation(HomeCm);
    }
    SetActorTickEnabled(false);
}

void ARaftSimWildlifeCreature::CallNow()
{
    if (VoiceWave && VoiceWave->GetVoice())
    {
        VoiceWave->GetVoice()->Play(RaftSimWildlife::BuildCall(Info.Call, Random), 1.0f);
        ++CallCount;
    }
}

float ARaftSimWildlifeCreature::SampleWaterZ(const FVector& WorldCm, bool* bOutWet) const
{
    const URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    FRaftSimWaterSample Sample;
    const bool bWet = Water && Water->SampleWaterAtWorldPosition(WorldCm, Sample) && Sample.bWet;
    if (bOutWet)
    {
        *bOutWet = bWet;
    }
    return bWet ? Sample.SurfaceHeightMeters * 100.0f : WaterZ;
}

void ARaftSimWildlifeCreature::NotifyRaftDistance(float DistanceMeters, const FVector& RaftLocationCm)
{
    const FVector Away = (GetActorLocation() - RaftLocationCm).GetSafeNormal2D();
    switch (Info.Body)
    {
        case EBody::Heron:
        case EBody::Duck:
            // Herons and ducks flush ahead of a boat, the heron croaking.
            if (!bFlying && DistanceMeters < (Info.Body == EBody::Heron ? 30.0f : 18.0f))
            {
                bFlying = true;
                StateUntil = Time + 14.0f;
                const FVector Flight = (Away + River * 0.8f).GetSafeNormal2D();
                Velocity = Flight * (Info.Body == EBody::Heron ? 800.0f : 1200.0f);
                if (Info.Body == EBody::Heron)
                {
                    CallNow();
                }
            }
            break;
        case EBody::Quadruped:
            if (Species == ESpecies::BlackTailedDeer && !bFlying && DistanceMeters < 30.0f)
            {
                bFlying = true;
                StateUntil = Time + 8.0f;
                Velocity = Away * 600.0f;
            }
            if (Species == ESpecies::ChacmaBaboon && DistanceMeters < 45.0f && Time > NextCall - 1000.0f && !bFlying)
            {
                // Baboons bark at a boat passing below them.
                bFlying = true;
                CallNow();
            }
            break;
        case EBody::Crocodile:
            if (!bSubmerged && DistanceMeters < 30.0f)
            {
                bSubmerged = true;
                StateUntil = Time + 2.5f;
                Velocity = (-Away + River * 0.2f).GetSafeNormal2D() * 160.0f;
            }
            break;
        case EBody::Hippo:
            if (!bSubmerged && DistanceMeters < 40.0f)
            {
                bSubmerged = true;
                StateUntil = Time + Random.FRandRange(20.0f, 40.0f);
            }
            break;
        default:
            break;
    }
}

void ARaftSimWildlifeCreature::Tick(float DeltaSeconds)
{
    CSV_SCOPED_TIMING_STAT(RaftSimTickWildlife,Creature);
    Super::Tick(DeltaSeconds);
    const float Dt = FMath::Clamp(DeltaSeconds, 0.0f, 0.1f);
    Time += Dt;
    Animate(Time, Dt);
    if (Info.Call != ERaftSimWildlifeCall::None && Time >= NextCall)
    {
        const bool bCanCall = !(Info.Body == EBody::Hippo && bSubmerged) && !(Info.Body == EBody::Duck && bSubmerged) &&
            Info.Body != EBody::Fish;
        if (bCanCall)
        {
            CallNow();
        }
        NextCall = Time + RaftSimWildlife::NextCallInterval(Info.Call, Random);
    }
}

void ARaftSimWildlifeCreature::Animate(float T, float Dt)
{
    auto SetWings = [this](float Dihedral, float Flap, float Sweep, float Fold)
    {
        for (int32 Index = 0; Index < WingParts.Num(); ++Index)
        {
            const float Side = Index == 0 ? -1.0f : 1.0f;
            // Roll lifts the wing tip (dihedral and flap; Unreal's positive
            // roll drops the right side); yaw sweeps it back; folding tucks
            // it down along the body.
            // A folded wing lies back along the flank: the one-piece plate
            // shortens to the folded length instead of hanging below.
            WingParts[Index]->SetRelativeRotation(FRotator(0.0f, Side * (Sweep + Fold * 82.0f),
                -Side * (Dihedral + Flap) + Side * Fold * 12.0f));
            WingParts[Index]->SetRelativeScale3D(FVector(1.0f, FMath::Lerp(1.0f, 0.32f, Fold), 1.0f));
        }
    };
    switch (Info.Body)
    {
        case EBody::Soarer:
        case EBody::Flapper:
        {
            const bool bSoarer = Info.Body == EBody::Soarer;
            const float Speed = (bSoarer ? 1100.0f : (Species == ESpecies::AustralParakeet ? 1300.0f : 900.0f)) *
                (Info.SizeMeters > 2.5f ? 1.25f : 1.0f);
            const float Radius = bSoarer ? CircleRadius : CircleRadius * 0.6f;
            CircleAngle += CircleDirection * Speed / FMath::Max(Radius, 100.0f) * Dt;
            if (!bReview && T > Lifetime)
            {
                // Time to move on: drift off downriver and climb away.
                Home += (River * 900.0f + FVector(0, 0, 250.0f)) * Dt;
                if (T > Lifetime + 40.0f)
                {
                    bWantsRemoval = true;
                }
            }
            else if (!bReview)
            {
                Home += River * 120.0f * Dt;
            }
            const FVector Offset(FMath::Cos(CircleAngle) * Radius, FMath::Sin(CircleAngle) * Radius,
                250.0f * FMath::Sin(0.13f * T + CircleAngle));
            SetActorLocation(Home + Offset);
            const float Yaw = FMath::RadiansToDegrees(CircleAngle) + 90.0f * CircleDirection;
            const float Bank = FMath::RadiansToDegrees(FMath::Atan(Speed * Speed / (980.0f * Radius)));
            SetActorRotation(FRotator(0.0f, Yaw, 0.0f));
            Pivot->SetRelativeRotation(FRotator(bSoarer ? -2.0f : 0.0f, 0.0f, CircleDirection * FMath::Min(Bank, 35.0f)));
            // Soarers mostly glide, with an occasional burst of deep flaps;
            // ravens and parrots row along with short glides.
            float Flap = 0.0f;
            if (bSoarer)
            {
                if (T > NextFlap)
                {
                    FlapUntil = T + Random.FRandRange(1.0f, 2.2f);
                    NextFlap = FlapUntil + Random.FRandRange(6.0f, 20.0f) * (Info.SizeMeters > 2.5f ? 3.0f : 1.0f);
                }
                if (T < FlapUntil)
                {
                    Flap = 32.0f * FMath::Sin(UE_TWO_PI * (Info.SizeMeters > 2.5f ? 1.4f : 2.4f) * T);
                }
                Flap += 2.0f * FMath::Sin(UE_TWO_PI * 0.4f * T);
            }
            else
            {
                const float Rate = Species == ESpecies::AustralParakeet ? 9.0f : 3.6f;
                const float Gliding = FMath::Sin(0.7f * T + CircleAngle) > 0.55f ? 0.15f : 1.0f;
                Flap = 38.0f * Gliding * FMath::Sin(UE_TWO_PI * Rate * T);
            }
            SetWings(Info.DihedralDeg, Flap, bSoarer ? 2.0f : 8.0f, 0.0f);
            if (TailPart)
            {
                TailPart->SetRelativeRotation(FRotator(0.0f, -CircleDirection * 6.0f, 0.0f));
            }
            break;
        }
        case EBody::Heron:
        {
            if (!bFlying)
            {
                SetActorLocation(Home);
                SetWings(0.0f, 0.0f, 0.0f, 1.0f);
                // A heron stands motionless, now and then turning its head.
                if (HeadPart)
                {
                    HeadPart->SetRelativeRotation(FRotator(0.0f, 35.0f * FMath::Sin(0.15f * T + Home.X), 0.0f));
                }
            }
            else
            {
                const float Climb = FMath::Min(T - (StateUntil - 14.0f), 3.0f) / 3.0f;
                const FVector Location = GetActorLocation() + Velocity * Dt + FVector(0, 0, 160.0f * Dt * (1.0f - Climb));
                SetActorLocation(Location);
                SetActorRotation(FRotator(0.0f, FMath::RadiansToDegrees(FMath::Atan2(Velocity.Y, Velocity.X)), 0.0f));
                SetWings(0.0f, 40.0f * FMath::Sin(UE_TWO_PI * 2.2f * T), 5.0f, 0.0f);
                for (UProceduralMeshComponent* Leg : LegParts)
                {
                    // Legs trail behind in flight; the neck folds back.
                    Leg->SetRelativeRotation(FRotator(70.0f, 0.0f, 0.0f));
                }
                if (HeadPart)
                {
                    HeadPart->SetRelativeRotation(FRotator(-35.0f, 0.0f, 0.0f));
                }
                if (BodyPart)
                {
                    BodyPart->SetRelativeRotation(FRotator(-18.0f, 0.0f, 0.0f));
                }
                if (T > StateUntil)
                {
                    bWantsRemoval = true;
                }
            }
            break;
        }
        case EBody::Duck:
        {
            if (bFlying)
            {
                SetActorLocation(GetActorLocation() + Velocity * Dt + FVector(0, 0, 120.0f * Dt));
                SetActorRotation(FRotator(0.0f, FMath::RadiansToDegrees(FMath::Atan2(Velocity.Y, Velocity.X)), 0.0f));
                SetWings(0.0f, 45.0f * FMath::Sin(UE_TWO_PI * 7.0f * T), 6.0f, 0.0f);
                if (T > StateUntil)
                {
                    bWantsRemoval = true;
                }
                break;
            }
            SetWings(0.0f, 0.0f, 0.0f, 1.0f);
            // Paddling slowly up the edge water, now and then diving.
            if (!bReview)
            {
                Home += -River * 25.0f * Dt + FVector(River.Y, -River.X, 0.0f) * 15.0f * FMath::Sin(0.3f * T) * Dt;
                if (!bSubmerged && T > StateUntil)
                {
                    bSubmerged = Random.FRand() < 0.4f;
                    StateUntil = T + (bSubmerged ? Random.FRandRange(4.0f, 9.0f) : Random.FRandRange(10.0f, 30.0f));
                }
                else if (bSubmerged && T > StateUntil)
                {
                    bSubmerged = false;
                    StateUntil = T + Random.FRandRange(10.0f, 30.0f);
                }
            }
            const float Surface = bReview ? WaterZ : SampleWaterZ(Home);
            SetActorLocation(FVector(Home.X, Home.Y, Surface + (bSubmerged ? -80.0f : 2.0f * FMath::Sin(2.1f * T))));
            SetActorRotation(FRotator(0.0f, FMath::RadiansToDegrees(FMath::Atan2(-River.Y, -River.X)) + 15.0f * FMath::Sin(0.3f * T), 0.0f));
            Pivot->SetVisibility(!bSubmerged, true);
            break;
        }
        case EBody::Monkey:
        {
            // Sitting in the canopy, swaying a little, looking about.
            if (BodyPart)
            {
                BodyPart->SetRelativeRotation(FRotator(0.0f, 0.0f, 3.0f * FMath::Sin(0.5f * T + Home.Y)));
            }
            if (HeadPart)
            {
                HeadPart->SetRelativeRotation(FRotator(12.0f * FMath::Max(0.0f, FMath::Sin(0.21f * T)), 25.0f * FMath::Sin(0.11f * T), 0.0f));
            }
            if (TailPart)
            {
                TailPart->SetRelativeRotation(FRotator(0.0f, 0.0f, 6.0f * FMath::Sin(0.7f * T)));
            }
            break;
        }
        case EBody::PerchedBird:
        {
            if (HeadPart)
            {
                // Quick, jerky head turns, held between.
                const float Step = FMath::FloorToFloat(T * 0.8f + Home.X * 0.001f);
                HeadPart->SetRelativeRotation(FRotator(0.0f, 50.0f * FMath::Sin(Step * 2.7f), 0.0f));
            }
            if (TailPart)
            {
                TailPart->SetRelativeRotation(FRotator(5.0f * FMath::Sin(3.0f * T), 0.0f, 0.0f));
            }
            break;
        }
        case EBody::Quadruped:
        {
            const bool bDeerFleeing = Species == ESpecies::BlackTailedDeer && bFlying;
            const float Cycle = FMath::Fmod(T + Home.X * 0.01f, 16.0f);
            const bool bWalking = bDeerFleeing || (!bReview && Cycle < 7.0f);
            const float Speed = bDeerFleeing ? 600.0f : (Species == ESpecies::GrizzlyBear ? 70.0f : 45.0f);
            if (bWalking && !bReview)
            {
                if (!bDeerFleeing)
                {
                    Heading += 8.0f * FMath::Sin(0.2f * T) * Dt;
                    // Stay near home: turn back when straying.
                    const FVector ToHome = Home - GetActorLocation();
                    if (ToHome.Size2D() > 1500.0f)
                    {
                        Heading = FMath::RadiansToDegrees(FMath::Atan2(ToHome.Y, ToHome.X));
                    }
                }
                else
                {
                    Heading = FMath::RadiansToDegrees(FMath::Atan2(Velocity.Y, Velocity.X));
                    if (T > StateUntil)
                    {
                        bWantsRemoval = true;
                    }
                }
                FVector Location = GetActorLocation() + FRotator(0.0f, Heading, 0.0f).Vector() * Speed * Dt;
                // Follow the ground.
                FHitResult Hit;
                FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimWildlifeGround), false, this);
                if (GetWorld()->LineTraceSingleByChannel(Hit, Location + FVector(0, 0, 400.0f), Location - FVector(0, 0, 800.0f),
                        ECC_Visibility, Params))
                {
                    Location.Z = Hit.ImpactPoint.Z;
                }
                SetActorLocationAndRotation(Location, FRotator(0.0f, Heading, 0.0f));
            }
            const float Gait = bWalking ? (bDeerFleeing ? 3.0f : 1.4f) : 0.0f;
            for (int32 Index = 0; Index < LegParts.Num(); ++Index)
            {
                const float Phase = (Index == 0 || Index == 3) ? 0.0f : PI;
                LegParts[Index]->SetRelativeRotation(FRotator((bWalking ? 22.0f : 0.0f) * FMath::Sin(UE_TWO_PI * Gait * T + Phase), 0.0f, 0.0f));
            }
            if (HeadPart)
            {
                // Grazing or looking about while stood.
                HeadPart->SetRelativeRotation(bWalking ? FRotator(4.0f * FMath::Sin(UE_TWO_PI * Gait * T), 0.0f, 0.0f)
                    : FRotator(Species == ESpecies::ChacmaBaboon ? 0.0f : -35.0f * FMath::Max(0.0f, FMath::Sin(0.3f * T)),
                        20.0f * FMath::Sin(0.17f * T), 0.0f));
            }
            break;
        }
        case EBody::Hippo:
        {
            if (!bReview && T > StateUntil)
            {
                bSubmerged = !bSubmerged;
                StateUntil = T + (bSubmerged ? Random.FRandRange(15.0f, 45.0f) : Random.FRandRange(20.0f, 60.0f));
            }
            const float Surface = bReview ? WaterZ : SampleWaterZ(Home);
            // Surfaced, only the top of the head and back break the water.
            const float TargetZ = Surface + (bSubmerged ? -260.0f : 16.0f);
            const FVector Location = GetActorLocation();
            const float Z = bReview ? TargetZ : FMath::FInterpTo(Location.Z, TargetZ, Dt, 0.8f);
            SetActorLocation(FVector(Home.X, Home.Y, Z));
            // Ear flicks, and a gaping yawn while it honks.
            const bool bYawning = CallCount > 0 && FMath::Fmod(T, 30.0f) < 2.0f && !bSubmerged;
            for (int32 Index = 0; Index < LegParts.Num(); ++Index)
            {
                const float Flick = FMath::Fmod(T * 0.37f + Index * 0.5f, 1.0f) < 0.06f ? 40.0f : 0.0f;
                LegParts[Index]->SetRelativeRotation(FRotator(0.0f, 0.0f, (Index == 0 ? -1.0f : 1.0f) * Flick));
            }
            if (HeadPart)
            {
                HeadPart->SetRelativeRotation(FRotator(bYawning ? 28.0f : 0.0f, 0.0f, 0.0f));
            }
            if (JawPart)
            {
                JawPart->SetRelativeRotation(FRotator(bYawning ? -55.0f : 0.0f, 0.0f, 0.0f));
            }
            break;
        }
        case EBody::Crocodile:
        {
            if (bSubmerged && !bReview)
            {
                // Sliding off the bank and sinking out of sight.
                const float Surface = SampleWaterZ(GetActorLocation());
                FVector Location = GetActorLocation() + Velocity * Dt;
                Location.Z = FMath::FInterpTo(Location.Z, Surface - 60.0f, Dt, 1.2f);
                SetActorLocation(Location);
                if (T > StateUntil + 15.0f)
                {
                    bWantsRemoval = true;
                }
            }
            if (JawPart)
            {
                // Basking with the jaws agape.
                JawPart->SetRelativeRotation(FRotator(bSubmerged ? 0.0f : -28.0f, 0.0f, 0.0f));
            }
            if (TailPart)
            {
                TailPart->SetRelativeRotation(FRotator(0.0f, 10.0f * FMath::Sin(0.25f * T), 0.0f));
            }
            break;
        }
        case EBody::Fish:
        {
            if (bReview)
            {
                break;
            }
            // Salmon leaping in the rapid: a short arc upstream, then gone.
            constexpr float JumpSeconds = 0.75f;
            if (T > StateUntil)
            {
                StateUntil = T + JumpSeconds + Random.FRandRange(2.0f, 7.0f);
                FlapUntil = T;
                Velocity = FVector(Random.FRandRange(-300.0f, 300.0f), Random.FRandRange(-300.0f, 300.0f), 0.0f);
                CallNow();
            }
            const float Since = T - FlapUntil;
            if (Since < JumpSeconds)
            {
                const float U = Since / JumpSeconds;
                const float Height = 110.0f * 4.0f * U * (1.0f - U);
                const FVector Start = Home + Velocity;
                const FVector Location = Start - River * 160.0f * U;
                const float Surface = SampleWaterZ(Start);
                SetActorLocation(FVector(Location.X, Location.Y, Surface + Height - 10.0f));
                SetActorRotation(FRotator(FMath::Lerp(45.0f, -45.0f, U), FMath::RadiansToDegrees(FMath::Atan2(-River.Y, -River.X)), 0.0f));
                Pivot->SetVisibility(true, true);
                if (TailPart)
                {
                    TailPart->SetRelativeRotation(FRotator(0.0f, 25.0f * FMath::Sin(UE_TWO_PI * 6.0f * T), 0.0f));
                }
            }
            else
            {
                Pivot->SetVisibility(false, true);
            }
            break;
        }
        case EBody::None:
        default:
            break;
    }
}

ARaftSimWildlifeDirector::ARaftSimWildlifeDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void ARaftSimWildlifeDirector::BeginPlay()
{
    Super::BeginPlay();
    Table = GetRiverWildlife(GetWorld() ? GetWorld()->GetMapName() : FString());
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        Bridge = GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    }
    Random.Initialize(static_cast<int32>(GetTypeHash(GetWorld() ? GetWorld()->GetMapName() : FString())));
    UE_LOG(LogTemp, Display, TEXT("RaftSim wildlife: %d species on %s"), Table.Num(),
        GetWorld() ? *GetWorld()->GetMapName() : TEXT("?"));
    if (Table.IsEmpty())
    {
        SetActorTickEnabled(false);
    }
}

bool ARaftSimWildlifeDirector::SampleWater(const FVector& AtCm, float& OutZ, float& OutSpeed, float& OutDepth,
    FVector& OutVelocity) const
{
    const URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    FRaftSimWaterSample Sample;
    if (!Water || !Water->SampleWaterAtWorldPosition(AtCm, Sample) || !Sample.bWet || Sample.DepthMeters < 0.05f)
    {
        return false;
    }
    OutZ = Sample.SurfaceHeightMeters * 100.0f;
    OutSpeed = Sample.VelocityMetersPerSecond.Size2D();
    OutDepth = Sample.DepthMeters;
    OutVelocity = Sample.VelocityMetersPerSecond;
    return true;
}

bool ARaftSimWildlifeDirector::FindWaterEdge(const FVector& FromCm, const FVector& Lateral, FVector& OutEdgeCm,
    float& OutWaterZ) const
{
    float Z = 0.0f, Speed = 0.0f, Depth = 0.0f;
    FVector Velocity;
    if (!SampleWater(FromCm, Z, Speed, Depth, Velocity))
    {
        return false;
    }
    OutWaterZ = Z;
    for (float Step = 200.0f; Step <= 15000.0f; Step += 200.0f)
    {
        const FVector Probe = FromCm + Lateral * Step;
        float ProbeZ = 0.0f;
        if (!SampleWater(Probe, ProbeZ, Speed, Depth, Velocity))
        {
            OutEdgeCm = FVector(Probe.X, Probe.Y, OutWaterZ);
            return true;
        }
        OutWaterZ = ProbeZ;
    }
    return false;
}

bool ARaftSimWildlifeDirector::TraceGround(const FVector& AtCm, float& OutZ) const
{
    TArray<FHitResult> Hits;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimWildlifePlacement), false, this);
    if (Raft)
    {
        Params.AddIgnoredActor(Raft);
    }
    if (!GetWorld()->LineTraceMultiByChannel(Hits, AtCm + FVector(0, 0, 30000.0f), AtCm - FVector(0, 0, 8000.0f),
            ECC_Visibility, Params))
    {
        return false;
    }
    for (const FHitResult& Hit : Hits)
    {
        // Trees are perches, not ground.
        bool bTree = false;
        for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& Tree : Trees)
        {
            bTree |= Tree.Get() == Hit.GetComponent();
        }
        if (!bTree && !Cast<ARaftSimWildlifeCreature>(Hit.GetActor()))
        {
            OutZ = Hit.ImpactPoint.Z;
            return true;
        }
    }
    return false;
}

bool ARaftSimWildlifeDirector::FindTreeTop(const FVector& NearCm, float Radius, FVector& OutCm) const
{
    TArray<TPair<UInstancedStaticMeshComponent*, int32>> Candidates;
    for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& Weak : Trees)
    {
        UInstancedStaticMeshComponent* Tree = Weak.Get();
        if (!Tree)
        {
            continue;
        }
        for (const int32 Instance : Tree->GetInstancesOverlappingSphere(NearCm, Radius, true))
        {
            Candidates.Add({Tree, Instance});
            if (Candidates.Num() > 64)
            {
                break;
            }
        }
    }
    if (Candidates.IsEmpty())
    {
        return false;
    }
    // The tree nearest the spot asked for (the bank's edge), so the animal
    // is in view from the river, not deep in the forest.
    int32 Nearest = 0;
    float NearestDistance = TNumericLimits<float>::Max();
    for (int32 Index = 0; Index < Candidates.Num(); ++Index)
    {
        FTransform Candidate;
        Candidates[Index].Key->GetInstanceTransform(Candidates[Index].Value, Candidate, true);
        const float Distance = FVector::Dist2D(Candidate.GetLocation(), NearCm) * Random.FRandRange(0.8f, 1.2f);
        if (Distance < NearestDistance)
        {
            NearestDistance = Distance;
            Nearest = Index;
        }
    }
    const TPair<UInstancedStaticMeshComponent*, int32>& Pick = Candidates[Nearest];
    FTransform Xf;
    Pick.Key->GetInstanceTransform(Pick.Value, Xf, true);
    const FBox Bounds = Pick.Key->GetStaticMesh()->GetBoundingBox();
    const float Height = Bounds.Max.Z * Xf.GetScale3D().Z;
    const float Crown = 0.5f * FMath::Max(Bounds.GetSize().X * Xf.GetScale3D().X, Bounds.GetSize().Y * Xf.GetScale3D().Y);
    // High in the crown, out on its river-facing edge where it can be seen.
    const FVector ToNear = (NearCm - Xf.GetLocation()).GetSafeNormal2D();
    OutCm = Xf.GetLocation() + FVector(0, 0, Height * Random.FRandRange(0.7f, 0.88f)) + ToNear * Crown * 0.8f;
    return true;
}

bool ARaftSimWildlifeDirector::FindRockTop(const FVector& NearCm, float Radius, float WaterZCm, FVector& OutCm)
{
    if (!bRocksGathered)
    {
        bRocksGathered = true;
        for (TActorIterator<ARaftSimRockObstacleActor> It(GetWorld()); It; ++It)
        {
            Rocks.Add(*It);
        }
    }
    // Boulders whose tops stand clear of the water but not far above it.
    TArray<FVector> Tops;
    for (const TWeakObjectPtr<AActor>& Weak : Rocks)
    {
        const AActor* Rock = Weak.Get();
        if (!Rock || FVector::Dist2D(Rock->GetActorLocation(), NearCm) > Radius)
        {
            continue;
        }
        const FBox Bounds = Rock->GetComponentsBoundingBox(true);
        if (!Bounds.IsValid || Bounds.Max.Z < WaterZCm + 15.0f || Bounds.Max.Z > WaterZCm + 400.0f)
        {
            continue;
        }
        const FVector Center = Bounds.GetCenter();
        const FVector Extent = Bounds.GetExtent();
        Tops.Add(FVector(Center.X + Random.FRandRange(-0.25f, 0.25f) * Extent.X,
            Center.Y + Random.FRandRange(-0.25f, 0.25f) * Extent.Y, Bounds.Max.Z - 6.0f));
    }
    if (Tops.IsEmpty())
    {
        return false;
    }
    OutCm = Tops[Random.RandHelper(Tops.Num())];
    return true;
}

bool ARaftSimWildlifeDirector::FindPlacement(const FRaftSimWildlifeSpeciesInfo& Entry, FVector& OutCm, float& OutWaterZ)
{
    const FVector Origin = Raft->GetActorLocation();
    float WaterZ = 0.0f, Speed = 0.0f, Depth = 0.0f;
    FVector Velocity;
    FVector Direction = Raft->GetActorForwardVector().GetSafeNormal2D();
    if (SampleWater(Origin, WaterZ, Speed, Depth, Velocity) && Velocity.Size2D() > 0.3f)
    {
        Direction = Velocity.GetSafeNormal2D();
    }
    // Follow the river downstream from the boat: the current turns with the
    // bends, so the spot stays on the river.
    const float Ahead = Entry.Habitat == EHabitat::Voice ? Random.FRandRange(20.0f, 110.0f)
        : (Entry.Habitat == EHabitat::Sky ? Random.FRandRange(60.0f, 220.0f) : Random.FRandRange(55.0f, 170.0f));
    FVector Point = Origin;
    float PointZ = WaterZ;
    for (float Walked = 0.0f; Walked < Ahead; Walked += 10.0f)
    {
        const FVector Next = Point + Direction * 1000.0f;
        float NextZ = 0.0f;
        if (!SampleWater(Next, NextZ, Speed, Depth, Velocity))
        {
            break;
        }
        Point = Next;
        PointZ = NextZ;
        if (Velocity.Size2D() > 0.3f)
        {
            Direction = (Direction + Velocity.GetSafeNormal2D()).GetSafeNormal2D();
        }
    }
    const FVector Lateral = FVector(-Direction.Y, Direction.X, 0.0f) * (Random.FRand() < 0.5f ? -1.0f : 1.0f);
    LastFacing = -Lateral;
    OutWaterZ = PointZ;
    FVector Edge;
    float EdgeWaterZ = PointZ;
    switch (Entry.Habitat)
    {
        case EHabitat::Sky:
            OutCm = Point + FVector(0, 0, Random.FRandRange(Entry.AltitudeMin, Entry.AltitudeMax) * 100.0f);
            OutCm.Z += PointZ - Point.Z;
            return true;
        case EHabitat::Rock:
            // A boulder standing out of the river; failing that, the bank.
            if (FindRockTop(Point, 6000.0f, PointZ, OutCm))
            {
                return true;
            }
            break;
        case EHabitat::Pool:
        case EHabitat::Rapid:
        {
            // Calm, deep water for hippos and ducks; fast water for salmon
            // and torrent ducks.
            const bool bPool = Entry.Habitat == EHabitat::Pool;
            float Best = bPool ? 1.0e9f : -1.0f;
            bool bFound = false;
            for (int32 Try = 0; Try < 14; ++Try)
            {
                const FVector Probe = Point + Direction * Random.FRandRange(-2500.0f, 2500.0f) +
                    Lateral * Random.FRandRange(0.0f, 2500.0f);
                float ProbeZ = 0.0f;
                if (!SampleWater(Probe, ProbeZ, Speed, Depth, Velocity))
                {
                    continue;
                }
                const bool bOk = bPool ? (Speed < 1.0f && Depth > (Entry.Body == EBody::Hippo ? 1.5f : 0.4f))
                    : (Speed > 2.0f && Depth > 0.4f);
                if (bOk && (bPool ? Speed < Best : Speed > Best))
                {
                    Best = Speed;
                    OutCm = FVector(Probe.X, Probe.Y, ProbeZ);
                    OutWaterZ = ProbeZ;
                    bFound = true;
                }
            }
            return bFound;
        }
        default:
            break;
    }
    if (!FindWaterEdge(Point, Lateral, Edge, EdgeWaterZ))
    {
        return false;
    }
    OutWaterZ = EdgeWaterZ;
    float Ground = 0.0f;
    switch (Entry.Habitat)
    {
        case EHabitat::Rock:
        case EHabitat::Shore:
        {
            // At the waterline: herons wading, crocodiles and bears at the
            // edge. Where the bank rises steeply, stand in the shallows
            // instead, in view from the river.
            FVector At = Edge - Lateral * 100.0f;
            if (!TraceGround(At, Ground) || Ground > EdgeWaterZ + 50.0f)
            {
                At = Edge - Lateral * 250.0f;
                Ground = EdgeWaterZ - 8.0f;
            }
            OutCm = FVector(At.X, At.Y, FMath::Max(Ground, EdgeWaterZ - 10.0f));
            return true;
        }
        case EHabitat::Bank:
        case EHabitat::Voice:
        {
            const FVector At = Edge + Lateral * Random.FRandRange(200.0f, 900.0f);
            if (!TraceGround(At, Ground))
            {
                return false;
            }
            OutCm = FVector(At.X, At.Y, Ground + (Entry.Habitat == EHabitat::Voice ? 150.0f : 0.0f));
            if (Entry.Call == ERaftSimWildlifeCall::CanyonWren || Entry.Call == ERaftSimWildlifeCall::RedWingedStarling)
            {
                // Heard off the cliffs, a little way up the wall.
                const FVector Wall = Edge + Lateral * Random.FRandRange(600.0f, 2500.0f);
                if (TraceGround(Wall, Ground))
                {
                    OutCm = FVector(Wall.X, Wall.Y, Ground + 100.0f);
                }
            }
            else if (Entry.Call == ERaftSimWildlifeCall::RingedKingfisher ||
                Entry.Call == ERaftSimWildlifeCall::BeltedKingfisher)
            {
                OutCm = FVector(Edge.X, Edge.Y, EdgeWaterZ + 300.0f);
            }
            if (Entry.Habitat == EHabitat::Voice && (Entry.Call == ERaftSimWildlifeCall::Cicadas ||
                Entry.Call == ERaftSimWildlifeCall::AcornWoodpecker || Entry.Call == ERaftSimWildlifeCall::RedShoulderedHawk))
            {
                FVector Tree;
                if (FindTreeTop(At, 2500.0f, Tree))
                {
                    OutCm = Tree;
                }
            }
            return true;
        }
        case EHabitat::Cliff:
        {
            // Up the canyon wall, on a ledge above the water.
            for (int32 Try = 0; Try < 6; ++Try)
            {
                const FVector At = Edge + Lateral * Random.FRandRange(1200.0f, 5000.0f);
                if (TraceGround(At, Ground) && Ground > EdgeWaterZ + 600.0f)
                {
                    OutCm = FVector(At.X, At.Y, Ground);
                    return true;
                }
            }
            return false;
        }
        case EHabitat::Canopy:
        {
            // The first trees on the bank, overhanging the river.
            const FVector At = Edge + Lateral * Random.FRandRange(100.0f, 600.0f);
            return FindTreeTop(At, 2500.0f, OutCm);
        }
        default:
            return false;
    }
}

bool ARaftSimWildlifeDirector::TrySpawn(const FRaftSimWildlifeSpeciesInfo& Entry)
{
    if (!bTreesGathered)
    {
        // Tall instanced meshes beside the rivers are the trees.
        bTreesGathered = true;
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        {
            TInlineComponentArray<UInstancedStaticMeshComponent*> Components(*It);
            for (UInstancedStaticMeshComponent* Component : Components)
            {
                const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
                if (!Mesh || Component->GetInstanceCount() == 0)
                {
                    continue;
                }
                const FString Name = Component->GetName() + Mesh->GetName();
                if (Name.Contains(TEXT("Rock")) || Name.Contains(TEXT("Boulder")) || Name.Contains(TEXT("Cliff")) ||
                    Name.Contains(TEXT("Grass")) || Name.Contains(TEXT("Shrub")) || Name.Contains(TEXT("Understory")))
                {
                    continue;
                }
                const FVector Extent = Mesh->GetBoundingBox().GetSize();
                if (Extent.Z > 450.0f && Extent.Z > 0.6f * FMath::Max(Extent.X, Extent.Y))
                {
                    Trees.Add(Component);
                }
            }
        }
        UE_LOG(LogTemp, Display, TEXT("RaftSim wildlife: %d tree layers for perches"), Trees.Num());
    }
    FVector Location;
    float WaterZ = 0.0f;
    if (!FindPlacement(Entry, Location, WaterZ))
    {
        return false;
    }
    if (FVector::Dist2D(Location, Raft->GetActorLocation()) < 3500.0f && Entry.Habitat != EHabitat::Sky &&
        Entry.Habitat != EHabitat::Voice)
    {
        return false;
    }
    FVector River = Raft->GetActorForwardVector();
    float Z = 0.0f, Speed = 0.0f, Depth = 0.0f;
    FVector Velocity;
    if (SampleWater(Raft->GetActorLocation(), Z, Speed, Depth, Velocity) && Velocity.Size2D() > 0.3f)
    {
        River = Velocity;
    }
    const int32 Group = Random.RandRange(Entry.GroupMin, FMath::Max(Entry.GroupMin, Entry.GroupMax));
    for (int32 Member = 0; Member < Group; ++Member)
    {
        FVector At = Location;
        if (Member > 0)
        {
            // The rest of the group close by: the same tree or ledge, the
            // same pool, nearby circles.
            const float Spread = Entry.Habitat == EHabitat::Sky ? 2500.0f : (Entry.Habitat == EHabitat::Canopy ? 900.0f : 500.0f);
            At += FVector(Random.FRandRange(-Spread, Spread), Random.FRandRange(-Spread, Spread), 0.0f);
            float Ground = 0.0f;
            if (Entry.Habitat == EHabitat::Canopy)
            {
                FVector Tree;
                if (FindTreeTop(At, 1500.0f, Tree))
                {
                    At = Tree;
                }
            }
            else if (Entry.Habitat == EHabitat::Cliff || Entry.Habitat == EHabitat::Bank || Entry.Habitat == EHabitat::Shore)
            {
                if (TraceGround(At, Ground))
                {
                    At.Z = Ground;
                }
            }
            else if (Entry.Habitat == EHabitat::Pool || Entry.Habitat == EHabitat::Rapid)
            {
                float MemberZ = 0.0f;
                if (!SampleWater(At, MemberZ, Speed, Depth, Velocity))
                {
                    continue;
                }
                At.Z = MemberZ;
            }
            else if (Entry.Habitat == EHabitat::Sky)
            {
                At.Z += Random.FRandRange(-1500.0f, 1500.0f);
            }
        }
        FActorSpawnParameters Params;
        Params.Owner = this;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        ARaftSimWildlifeCreature* Creature = GetWorld()->SpawnActor<ARaftSimWildlifeCreature>(
            ARaftSimWildlifeCreature::StaticClass(), FTransform(At), Params);
        if (Creature)
        {
            if (Entry.bBrood && Member > 0)
            {
                // Ducklings trailing their mother.
                Creature->SetActorScale3D(FVector(0.45f));
                At += (At - Location).GetSafeNormal2D() * 200.0f;
            }
            const bool bFacesWater = Entry.Habitat == EHabitat::Canopy || Entry.Habitat == EHabitat::Cliff ||
                Entry.Habitat == EHabitat::Bank || Entry.Habitat == EHabitat::Shore;
            Creature->Configure(Entry.Species, At, River, WaterZ, static_cast<uint32>(Random.GetUnsignedInt()),
                bFacesWater ? LastFacing : FVector::ZeroVector);
            Creatures.Add(Creature);
            ++SpawnedCount;
        }
    }
    UE_LOG(LogTemp, Display, TEXT("RaftSim wildlife: %s x%d at %.0f m (%s)"),
        *StaticEnum<ERaftSimWildlifeSpecies>()->GetNameStringByValue(static_cast<int64>(Entry.Species)), Group,
        FVector::Dist(Location, Raft->GetActorLocation()) / 100.0f, *Location.ToCompactString());
    return true;
}

void ARaftSimWildlifeDirector::StartShowcase(const FString& Label, float DelaySeconds, bool bExitWhenDone)
{
    bShowcase = true;
    bShowcaseSpawned = false;
    bShowcaseExit = bExitWhenDone;
    ShowcaseLabel = Label;
    ShowcaseTimer = DelaySeconds;
    ShowcaseIndex = 0;
    bShowcaseFramed = false;
    ShowcaseSubjects.Reset();
    SetActorTickEnabled(true);
    UE_LOG(LogTemp, Display, TEXT("RaftSim wildlife showcase '%s' in %.0f s (%d species)"), *Label, DelaySeconds, Table.Num());
}

void ARaftSimWildlifeDirector::TickShowcase(float DeltaSeconds)
{
    ShowcaseTimer -= DeltaSeconds;
    if (ShowcaseTimer > 0.0f || !Raft)
    {
        return;
    }
    if (!bShowcaseSpawned)
    {
        // Every species of this river, near the raft.
        bShowcaseSpawned = true;
        for (const FRaftSimWildlifeSpeciesInfo& Entry : Table)
        {
            const int32 Before = Creatures.Num();
            for (int32 Try = 0; Try < 8 && Creatures.Num() == Before; ++Try)
            {
                TrySpawn(Entry);
            }
            if (Creatures.Num() > Before && Entry.Body != EBody::None)
            {
                ShowcaseSubjects.Add(Creatures[Before]);
            }
            else if (Creatures.Num() == Before)
            {
                UE_LOG(LogTemp, Warning, TEXT("RaftSim wildlife showcase: no place found for %s"),
                    *StaticEnum<ERaftSimWildlifeSpecies>()->GetNameStringByValue(static_cast<int64>(Entry.Species)));
            }
        }
        ShowcaseTimer = 1.5f;
        return;
    }
    if (ShowcaseIndex >= ShowcaseSubjects.Num())
    {
        UE_LOG(LogTemp, Display, TEXT("RaftSim wildlife showcase complete: %d photographed"), ShowcaseSubjects.Num());
        bShowcase = false;
        if (bShowcaseExit)
        {
            FPlatformMisc::RequestExit(false);
        }
        return;
    }
    ARaftSimWildlifeCreature* Subject = ShowcaseSubjects[ShowcaseIndex].Get();
    if (!Subject)
    {
        ++ShowcaseIndex;
        return;
    }
    // Seen from where a rafter is: the raft at eye height, through a long
    // lens sized so the animal fills a fifth of the frame.
    const FRaftSimWildlifeSpeciesInfo Info = GetWildlifeSpeciesInfo(Subject->GetSpecies());
    const FVector Target = Subject->GetActorLocation() + FVector(0, 0, Info.Body == EBody::Fish ? 0.0f : 0.3f * Info.SizeMeters * 100.0f);
    // Flyers from the raft; animals in the trees and on the banks from out
    // on the water in front of them (they face the river), as the boat
    // passes them.
    const bool bFromRaft = IsFlightBody(Info.Body) || Info.Body == EBody::Fish;
    const FVector Eye = bFromRaft ? Raft->GetActorLocation() + FVector(0, 0, 160.0f)
        : Target + Subject->GetActorForwardVector().GetSafeNormal2D() * FMath::Clamp(Info.SizeMeters * 2500.0f, 900.0f, 3000.0f) +
            FVector(0, 0, 150.0f);
    const float Range = FMath::Max(static_cast<float>(FVector::Dist(Eye, Target)), 100.0f);
    const float Fov = FMath::Clamp(FMath::RadiansToDegrees(2.0f * FMath::Atan(Info.SizeMeters * 250.0f / Range)), 1.5f, 70.0f);
    ACameraActor* Camera = ShowcaseCamera.Get();
    if (!Camera)
    {
        Camera = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), Eye, FRotator::ZeroRotator);
        ShowcaseCamera = Camera;
    }
    if (!Camera)
    {
        bShowcase = false;
        return;
    }
    Camera->SetActorLocationAndRotation(Eye, (Target - Eye).Rotation());
    Camera->GetCameraComponent()->SetFieldOfView(Fov);
    if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
    {
        PC->SetViewTarget(Camera);
    }
    if (!bShowcaseFramed)
    {
        bShowcaseFramed = true;
        ShowcaseTimer = 0.6f;
        return;
    }
    const FString Name = StaticEnum<ERaftSimWildlifeSpecies>()->GetNameStringByValue(static_cast<int64>(Subject->GetSpecies()));
    FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"),
        FString::Printf(TEXT("%s_%s.png"), *ShowcaseLabel, *Name)), false, false);
    UE_LOG(LogTemp, Display, TEXT("RaftSim wildlife showcase: %s at %.0f m from the raft"), *Name,
        FVector::Dist(Subject->GetActorLocation(), Raft->GetActorLocation()) / 100.0f);
    bShowcaseFramed = false;
    ShowcaseTimer = 0.5f;
    ++ShowcaseIndex;
}

namespace
{
// RaftSim.WildlifeShowcase <label> [delaySeconds] [exit]
FAutoConsoleCommandWithWorldAndArgs GWildlifeShowcaseCommand(
    TEXT("RaftSim.WildlifeShowcase"),
    TEXT("Photograph every species of this river near the raft: RaftSim.WildlifeShowcase <label> [delaySeconds] [exit]"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
    {
        if (!World)
        {
            return;
        }
        ARaftSimWildlifeDirector* Director = nullptr;
        if (TActorIterator<ARaftSimWildlifeDirector> It(World); It)
        {
            Director = *It;
        }
        else
        {
            Director = World->SpawnActor<ARaftSimWildlifeDirector>(ARaftSimWildlifeDirector::StaticClass(), FTransform::Identity);
        }
        if (Director)
        {
            Director->StartShowcase(Args.IsValidIndex(0) ? Args[0] : TEXT("wildlife"),
                Args.IsValidIndex(1) ? FCString::Atof(*Args[1]) : 8.0f,
                Args.IsValidIndex(2) && Args[2] == TEXT("exit"));
        }
    }));
}

void ARaftSimWildlifeDirector::Tick(float DeltaSeconds)
{
    CSV_SCOPED_TIMING_STAT(RaftSimTickWildlife,Director);
    Super::Tick(DeltaSeconds);
    if (!Raft)
    {
        if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
        {
            Raft = *It;
        }
        return;
    }
    if (bShowcase)
    {
        TickShowcase(DeltaSeconds);
    }
    const FVector RaftLocation = Raft->GetActorLocation();
    const FVector Forward = Raft->GetActorForwardVector().GetSafeNormal2D();
    for (int32 Index = Creatures.Num() - 1; Index >= 0; --Index)
    {
        ARaftSimWildlifeCreature* Creature = Creatures[Index];
        if (!IsValid(Creature))
        {
            Creatures.RemoveAtSwap(Index);
            continue;
        }
        const FVector Offset = Creature->GetActorLocation() - RaftLocation;
        const float Distance = static_cast<float>(Offset.Size2D()) / 100.0f;
        Creature->NotifyRaftDistance(Distance, RaftLocation);
        // Gone once well behind the boat or far away.
        const bool bBehind = FVector::DotProduct(Offset.GetSafeNormal2D(), Forward) < -0.3f && Distance > 220.0f;
        if (Creature->WantsRemoval() || Distance > 650.0f || bBehind)
        {
            Creature->Destroy();
            Creatures.RemoveAtSwap(Index);
        }
    }
    SpawnSeconds -= DeltaSeconds;
    if (SpawnSeconds > 0.0f || Table.IsEmpty())
    {
        return;
    }
    SpawnSeconds = 1.2f;
    const FRaftSimWildlifeSpeciesInfo& Entry = Table[NextEntry++ % Table.Num()];
    int32 Live = 0;
    for (const ARaftSimWildlifeCreature* Creature : Creatures)
    {
        Live += Creature && Creature->GetSpecies() == Entry.Species ? 1 : 0;
    }
    // Groups count as one sighting toward the species' limit.
    const int32 Sightings = Entry.GroupMax > 1 ? FMath::DivideAndRoundUp(Live, FMath::Max(Entry.GroupMin, 1)) : Live;
    if (Sightings < Entry.MaxNearby && Random.FRand() < Entry.SpawnChance)
    {
        TrySpawn(Entry);
    }
}
