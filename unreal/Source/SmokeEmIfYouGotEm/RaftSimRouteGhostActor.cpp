#include "RaftSimRouteGhostActor.h"

#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"

ARaftSimRouteGhostActor::ARaftSimRouteGhostActor()
{
    PrimaryActorTick.bCanEverTick = false;
    Ribbon = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("BestRouteRibbon"));
    SetRootComponent(Ribbon);
    Ribbon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Ribbon->SetCastShadow(false);
    if (UMaterialInterface* Material = LoadObject<UMaterialInterface>(
            nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_UnlitColorPreview.M_RaftSim_UnlitColorPreview")))
    {
        Ribbon->SetMaterial(0, Material);
    }
}

void ARaftSimRouteGhostActor::SetRoute(const TArray<FVector>& WorldPoints)
{
    Ribbon->ClearAllMeshSections();
    RoutePointCount = WorldPoints.Num();
    if (WorldPoints.Num() < 2)
    {
        return;
    }
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    constexpr float HalfWidthCm = 18.0f;
    for (int32 Index = 0; Index < WorldPoints.Num(); ++Index)
    {
        const FVector Previous = WorldPoints[FMath::Max(0, Index - 1)];
        const FVector Next = WorldPoints[FMath::Min(WorldPoints.Num() - 1, Index + 1)];
        FVector Side = FVector::CrossProduct((Next - Previous).GetSafeNormal(), FVector::UpVector).GetSafeNormal();
        if (Side.IsNearlyZero())
        {
            Side = FVector::RightVector;
        }
        const FVector Center = WorldPoints[Index] + FVector(0.0f, 0.0f, 65.0f);
        Vertices.Add(Center - GetActorLocation() - Side * HalfWidthCm);
        Vertices.Add(Center - GetActorLocation() + Side * HalfWidthCm);
        Normals.Append({FVector::UpVector, FVector::UpVector});
        UVs.Append({FVector2D(static_cast<float>(Index), 0.0f), FVector2D(static_cast<float>(Index), 1.0f)});
        Colors.Append({FLinearColor(0.02f, 0.78f, 1.0f, 0.65f), FLinearColor(0.02f, 0.78f, 1.0f, 0.65f)});
        Tangents.Append({FProcMeshTangent(Next - Previous, false), FProcMeshTangent(Next - Previous, false)});
        if (Index > 0)
        {
            const int32 A = (Index - 1) * 2;
            const int32 B = A + 1;
            const int32 C = Index * 2;
            const int32 D = C + 1;
            Triangles.Append({A, C, B, B, C, D});
        }
    }
    Ribbon->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false, false);
}
