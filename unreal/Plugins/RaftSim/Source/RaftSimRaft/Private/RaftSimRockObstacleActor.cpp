#include "RaftSimRockObstacleActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "KismetProceduralMeshLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr int32 BoulderSegments = 48;
constexpr int32 BoulderLatitudeDivisions = 18;

float BoulderProfile(float Theta, float Phi)
{
    // A bounded deterministic profile keeps the visible rock inside the same
    // horizontal envelope used by D4 contact while avoiding a primitive
    // sphere silhouette. Broad faces, a shouldered crown, and mixed angular
    // frequencies read as a water-worn procedural boulder without pretending
    // to reconstruct undocumented South Fork geology.
    return FMath::Clamp(
        0.82f +
            0.105f * FMath::Sin(3.0f * Theta + 0.65f) +
            0.065f * FMath::Sin(5.0f * Theta - 1.4f * Phi) +
            0.045f * FMath::Cos(7.0f * Theta + 0.9f * Phi) +
            0.025f * FMath::Sin(11.0f * Theta - 2.1f * Phi),
        0.62f,
        0.98f);
}
}

ARaftSimRockObstacleActor::ARaftSimRockObstacleActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    RockMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("RockMesh"));
    RockMesh->SetupAttachment(SceneRoot);
    // Contact is authoritative in the D4 adapter. A second Unreal collision
    // response would double-apply the obstacle and corrupt wrap/pin evidence.
    RockMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RockMesh->SetCollisionObjectType(ECC_WorldStatic);

    ProductionRockVisual =
        CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProductionRockVisual"));
    ProductionRockVisual->SetupAttachment(SceneRoot);
    ProductionRockVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProductionRockVisual->SetCollisionObjectType(ECC_WorldStatic);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ProductionRockAsset(
        TEXT("/Game/RaftSim/Environment/Rocks/Production/"
             "SM_RaftSim_ProductionRiverBoulder."
             "SM_RaftSim_ProductionRiverBoulder"));
    if (ProductionRockAsset.Succeeded())
    {
        ProductionRockVisual->SetStaticMesh(ProductionRockAsset.Object);
    }

    ReviewedRockVisual =
        CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ReviewedRockVisual"));
    ReviewedRockVisual->SetupAttachment(SceneRoot);
    ReviewedRockVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ReviewedRockVisual->SetCollisionObjectType(ECC_WorldStatic);
    // The photogrammetry scan is an open-base shell. Letting that underside
    // cast a directional shadow projects a rectangular slab across the raft
    // and water; authored closed world rocks and the procedural fallback keep
    // their normal shadows, while this optional shell still receives light.
    ReviewedRockVisual->SetCastShadow(false);

    // This scan is the hash-verified CC0 Poly Haven Rock Moss Set 01 analog
    // already used by the South Fork corridor. It improves silhouette and
    // microgeometry but is not represented as site-specific geology. If it is
    // absent from a build, RebuildVisualGeometry exposes the project-owned
    // procedural fallback instead.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ReviewedRockAsset(
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "RockMossSet01_1K/SM_RockMossSet01_rock_moss_set_01_rock03."
             "SM_RockMossSet01_rock_moss_set_01_rock03"));
    if (ReviewedRockAsset.Succeeded())
    {
        ReviewedRockVisual->SetStaticMesh(ReviewedRockAsset.Object);
    }

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SharedRockMaterial(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder."
             "M_RaftSim_RiverBoulder"));
    if (SharedRockMaterial.Succeeded())
    {
        RockMesh->SetMaterial(0, SharedRockMaterial.Object);
        // Photogrammetry assets may carry more than one source section. Every
        // slot must be overridden or uncovered sections silently retain the
        // rejected mossy/ochre review material.
        const int32 ReviewedMaterialSlots = ReviewedRockVisual->GetNumMaterials();
        for (int32 MaterialIndex = 0; MaterialIndex < ReviewedMaterialSlots; ++MaterialIndex)
        {
            ReviewedRockVisual->SetMaterial(MaterialIndex, SharedRockMaterial.Object);
        }
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ProductionRockMaterial(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/"
             "MI_RaftSim_SouthForkProductionBoulder."
             "MI_RaftSim_SouthForkProductionBoulder"));
    if (ProductionRockMaterial.Succeeded())
    {
        ProductionRockVisual->SetMaterial(0, ProductionRockMaterial.Object);
    }
    RebuildVisualGeometry();
}

void ARaftSimRockObstacleActor::BeginPlay()
{
    Super::BeginPlay();
    ApplyWaterlineToMaterials();
}

void ARaftSimRockObstacleActor::ApplyWaterlineToMaterials()
{
    URaftSimWaterRuntimeAdapter* WaterAdapter = nullptr;
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            WaterAdapter = Bridge->GetWaterRuntime();
        }
    }
    FRaftSimWaterSample Sample;
    const bool bSampled = WaterAdapter != nullptr && WaterAdapter->HasLiveWindow() &&
        WaterAdapter->SampleWaterAtWorldPosition(GetActorLocation(), Sample);
    if (!bSampled)
    {
        // The live river window is configured by the raft after most level
        // actors have begun play; retry briefly, then stay fail-safe dry.
        if (WaterlineAttemptsRemaining-- > 0 && GetWorld() != nullptr)
        {
            GetWorld()->GetTimerManager().SetTimer(
                WaterlineRetryHandle,
                FTimerDelegate::CreateUObject(
                    this, &ARaftSimRockObstacleActor::ApplyWaterlineToMaterials),
                0.5f, false);
        }
        return;
    }

    const float WaterlineZCm = Sample.SurfaceHeightMeters * 100.0f;
    auto PushWaterline = [this, WaterlineZCm](UMeshComponent* Mesh)
    {
        if (Mesh == nullptr)
        {
            return;
        }
        const int32 SlotCount = Mesh->GetNumMaterials();
        for (int32 Slot = 0; Slot < SlotCount; ++Slot)
        {
            UMaterialInterface* Current = Mesh->GetMaterial(Slot);
            if (Current == nullptr)
            {
                continue;
            }
            UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Current);
            if (Dynamic == nullptr)
            {
                Dynamic = UMaterialInstanceDynamic::Create(Current, Mesh);
                Mesh->SetMaterial(Slot, Dynamic);
            }
            Dynamic->SetScalarParameterValue(TEXT("RockWaterlineZCm"), WaterlineZCm);
            if (Mesh == ProductionRockVisual)
            {
                // The dedicated South Fork material does not consume this
                // legacy selector, but keep it neutral for fail-safe use with
                // older cooked assets. Reviewed scans remain on their separate
                // source-material path.
                Dynamic->SetScalarParameterValue(TEXT("RockVisualSourceBlend"), 0.0f);
            }
        }
    };
    PushWaterline(RockMesh);
    PushWaterline(ProductionRockVisual);
    PushWaterline(ReviewedRockVisual);
}

bool ARaftSimRockObstacleActor::HasProductionRiverBoulder() const
{
    return ProductionRockVisual != nullptr &&
        ProductionRockVisual->GetStaticMesh() != nullptr;
}

void ARaftSimRockObstacleActor::ConfigureContact(
    float InRadiusM,
    float InFrictionCoefficient)
{
    ContactRadiusM = FMath::Max(0.1f, InRadiusM);
    FrictionCoefficient = FMath::Clamp(InFrictionCoefficient, 0.0f, 2.0f);
    RebuildVisualGeometry();
}

void ARaftSimRockObstacleActor::SetPreferReviewedVisual(bool bInPreferReviewedVisual)
{
    // Evidence/gameplay actors call this after SpawnActor has registered the
    // default subobjects. Force a real visibility transition so Nanite does
    // not retain the constructor-time proxy with its pre-configure transform.
    if (ReviewedRockVisual)
    {
        ReviewedRockVisual->SetVisibility(false, false);
    }
    bPreferReviewedVisual = bInPreferReviewedVisual;
    RebuildVisualGeometry();
    if (ReviewedRockVisual)
    {
        ReviewedRockVisual->MarkRenderTransformDirty();
        ReviewedRockVisual->MarkRenderStateDirty();
    }
}

void ARaftSimRockObstacleActor::SetReviewedVisualMeshForDiagnostics(UStaticMesh* InMesh)
{
    if (ReviewedRockVisual == nullptr || InMesh == nullptr)
    {
        return;
    }
    ReviewedRockVisual->SetStaticMesh(InMesh);
    // Preview imports carry their own rights-reviewed UV material. Remove the
    // constructor's production-fallback override only for this explicit mesh
    // substitution so reviewers see the source PBR response.
    ReviewedRockVisual->EmptyOverrideMaterials();
    RebuildVisualGeometry();
    ReviewedRockVisual->MarkRenderTransformDirty();
    ReviewedRockVisual->MarkRenderStateDirty();
}

void ARaftSimRockObstacleActor::RebuildVisualGeometry()
{
    if (RockMesh == nullptr)
    {
        return;
    }

    const float HorizontalRadiusCm = ContactRadiusM * 100.0f;
    const float VerticalRadiusCm = HorizontalRadiusCm * 0.725f;
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;

    // One bottom pole, seventeen irregular rings, then one top pole.
    Vertices.Add(FVector(0.0f, 0.0f, -VerticalRadiusCm * 0.88f));
    UVs.Add(FVector2D(0.5f, 0.0f));
    for (int32 Latitude = 1; Latitude < BoulderLatitudeDivisions; ++Latitude)
    {
        const float V = static_cast<float>(Latitude) / BoulderLatitudeDivisions;
        const float Phi = -0.5f * PI + V * PI;
        for (int32 Segment = 0; Segment < BoulderSegments; ++Segment)
        {
            const float U = static_cast<float>(Segment) / BoulderSegments;
            const float Theta = U * 2.0f * PI;
            const float Profile = BoulderProfile(Theta, Phi);
            // A sub-unit cosine exponent holds more width near the crown and
            // base than a sphere. The closed pole fans still taper to zero,
            // producing shouldered faces instead of the rejected ball shape.
            const float CrownProfile = FMath::Pow(
                FMath::Max(0.0f, FMath::Cos(Phi)), 0.72f);
            const float RingRadiusCm = HorizontalRadiusCm * CrownProfile * Profile;
            const float X = RingRadiusCm * FMath::Cos(Theta) *
                (0.96f + 0.035f * FMath::Sin(2.0f * Phi + 0.4f));
            const float Y = RingRadiusCm * FMath::Sin(Theta) *
                (0.91f + 0.045f * FMath::Cos(3.0f * Phi - 0.2f));
            const float ZProfile =
                0.91f + 0.055f * FMath::Sin(2.0f * Theta + 1.1f) * FMath::Cos(Phi);
            const float Z = VerticalRadiusCm * FMath::Sin(Phi) * ZProfile +
                VerticalRadiusCm * 0.035f * FMath::Sin(3.0f * Theta) *
                    FMath::Square(FMath::Cos(Phi));
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U, V));
        }
    }
    const int32 TopPole = Vertices.Add(
        FVector(0.0f, 0.0f, VerticalRadiusCm * 0.98f));
    UVs.Add(FVector2D(0.5f, 1.0f));

    auto RingVertex = [](int32 Latitude, int32 Segment)
    {
        const int32 WrappedSegment = (Segment + BoulderSegments) % BoulderSegments;
        return 1 + (Latitude - 1) * BoulderSegments + WrappedSegment;
    };
    for (int32 Segment = 0; Segment < BoulderSegments; ++Segment)
    {
        Triangles.Append({0, RingVertex(1, Segment), RingVertex(1, Segment + 1)});
    }
    for (int32 Latitude = 1; Latitude < BoulderLatitudeDivisions - 1; ++Latitude)
    {
        for (int32 Segment = 0; Segment < BoulderSegments; ++Segment)
        {
            const int32 A = RingVertex(Latitude, Segment);
            const int32 B = RingVertex(Latitude, Segment + 1);
            const int32 C = RingVertex(Latitude + 1, Segment);
            const int32 D = RingVertex(Latitude + 1, Segment + 1);
            Triangles.Append({A, C, B, B, C, D});
        }
    }
    for (int32 Segment = 0; Segment < BoulderSegments; ++Segment)
    {
        Triangles.Append({
            RingVertex(BoulderLatitudeDivisions - 1, Segment),
            TopPole,
            RingVertex(BoulderLatitudeDivisions - 1, Segment + 1)});
    }

    TArray<FVector> Normals;
    TArray<FProcMeshTangent> Tangents;
    UKismetProceduralMeshLibrary::CalculateTangentsForMesh(
        Vertices, Triangles, UVs, Normals, Tangents);
    // CalculateTangents follows triangle winding. Unreal's procedural front
    // face convention is opposite the analytic spherical parameterization
    // above, so restore outward lighting normals after reversing the indices.
    for (int32 VertexIndex = 0; VertexIndex < Normals.Num(); ++VertexIndex)
    {
        Normals[VertexIndex] *= -1.0f;
        if (Tangents.IsValidIndex(VertexIndex))
        {
            // Flipping only N leaves a left-handed TBN basis. That was hidden
            // while the boulder used geometric normals, but made the reviewed
            // tangent-space normal texture turn upward faces black. Preserve a
            // right-handed basis by flipping the generated bitangent sign too.
            Tangents[VertexIndex].bFlipTangentY =
                !Tangents[VertexIndex].bFlipTangentY;
        }
    }
    TArray<FLinearColor> Colors;
    // Alpha zero selects the project-owned procedural mineral branch in the
    // shared material. Imported reviewed static meshes have no override color
    // and therefore supply the default white/alpha-one vertex value, selecting
    // their UV-authored scan textures without mapping those textures onto this
    // generated shell.
    Colors.Init(FLinearColor(0.24f, 0.23f, 0.20f, 0.0f), Vertices.Num());
    RockMesh->ClearAllMeshSections();
    RockMesh->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents,
        /*bCreateCollision=*/false);

    UStaticMesh* ReviewedMesh = ReviewedRockVisual
        ? ReviewedRockVisual->GetStaticMesh()
        : nullptr;
    if (ReviewedMesh != nullptr && bPreferReviewedVisual)
    {
        if (ProductionRockVisual)
        {
            ProductionRockVisual->SetVisibility(false, false);
        }
        const FBoxSphereBounds Bounds = ReviewedMesh->GetBounds();
        const float MaxHorizontalExtentCm =
            FMath::Max(Bounds.BoxExtent.X, Bounds.BoxExtent.Y);
        const float TargetHorizontalExtentCm = HorizontalRadiusCm * 0.93f;
        const float UniformScale = MaxHorizontalExtentCm > KINDA_SMALL_NUMBER
            ? TargetHorizontalExtentCm / MaxHorizontalExtentCm
            : 1.0f;
        ReviewedRockVisual->SetRelativeScale3D(FVector(UniformScale));
        ReviewedRockVisual->SetRelativeLocation(
            -Bounds.Origin * UniformScale +
            FVector(0.0f, 0.0f, -HorizontalRadiusCm * 0.02f));
        // The scan and fallback are sibling render components below a neutral
        // transform root, so neither path can inherit the other's visibility.
        ReviewedRockVisual->SetVisibility(true, false);
        RockMesh->SetVisibility(true, false);
        RockMesh->SetMeshSectionVisible(0, false);
    }
    else if (HasProductionRiverBoulder())
    {
        const FBoxSphereBounds Bounds = ProductionRockVisual->GetStaticMesh()->GetBounds();
        const float MaxHorizontalExtentCm =
            FMath::Max(Bounds.BoxExtent.X, Bounds.BoxExtent.Y);
        const float TargetHorizontalExtentCm = HorizontalRadiusCm * 0.96f;
        const float UniformScale = MaxHorizontalExtentCm > KINDA_SMALL_NUMBER
            ? TargetHorizontalExtentCm / MaxHorizontalExtentCm
            : 1.0f;
        ProductionRockVisual->SetRelativeScale3D(FVector(UniformScale));
        ProductionRockVisual->SetRelativeLocation(
            -Bounds.Origin * UniformScale +
            FVector(0.0f, 0.0f, -HorizontalRadiusCm * 0.015f));
        ProductionRockVisual->SetVisibility(true, false);
        ProductionRockVisual->MarkRenderTransformDirty();
        ProductionRockVisual->MarkRenderStateDirty();
        if (ReviewedRockVisual)
        {
            ReviewedRockVisual->SetVisibility(false, false);
        }
        RockMesh->SetVisibility(true, false);
        RockMesh->SetMeshSectionVisible(0, false);
    }
    else
    {
        if (ProductionRockVisual)
        {
            ProductionRockVisual->SetVisibility(false, false);
        }
        if (ReviewedRockVisual)
        {
            ReviewedRockVisual->SetVisibility(false, false);
        }
        RockMesh->SetVisibility(true, false);
        RockMesh->SetMeshSectionVisible(0, true);
    }
}
