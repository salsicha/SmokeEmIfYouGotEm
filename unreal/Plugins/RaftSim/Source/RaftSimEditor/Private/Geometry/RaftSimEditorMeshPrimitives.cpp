#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
AStaticMeshActor* AddPreviewMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FVector& Location,
    const FRotator& Rotation,
    const FVector& Scale,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride,
    bool bUseMeshDefaultMaterial)
{
    if (!World || !Mesh || !GEditor)
    {
        return nullptr;
    }

    AStaticMeshActor* Actor = Cast<AStaticMeshActor>(
        GEditor->AddActor(World->GetCurrentLevel(), AStaticMeshActor::StaticClass(), FTransform(Rotation, Location, Scale), true, RF_Transactional, false));
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Component->SetCastShadow(false);
    if (MaterialOverride)
    {
        Component->SetMaterial(0, MaterialOverride);
    }
    else if (!bUseMeshDefaultMaterial)
    {
        ApplyPreviewColor(Component, Color);
    }
    return Actor;
}

AStaticMeshActor* AddPreviewTranslucentMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FVector& Location,
    const FRotator& Rotation,
    const FVector& Scale,
    const FLinearColor& Color,
    float Opacity)
{
    AStaticMeshActor* Actor = AddPreviewMeshActor(World, Mesh, Label, Location, Rotation, Scale, Color);
    if (Actor && Actor->GetStaticMeshComponent())
    {
        Actor->GetStaticMeshComponent()->SetCastShadow(false);
        Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        ApplyPreviewTranslucentColor(Actor->GetStaticMeshComponent(), Color, Opacity);
    }
    return Actor;
}

UInstancedStaticMeshComponent* AddPreviewInstancedMeshComponent(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FLinearColor& Color)
{
    if (!World || !Mesh)
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UInstancedStaticMeshComponent* Component =
        NewObject<UInstancedStaticMeshComponent>(Actor, *FString::Printf(TEXT("%s_Instances"), *Label));
    if (!Component)
    {
        Actor->Destroy();
        return nullptr;
    }

    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCastShadow(false);
    Actor->SetRootComponent(Component);
    Actor->AddInstanceComponent(Component);
    Component->RegisterComponent();
    ApplyPreviewColor(Component, Color);
    return Component;
}

UHierarchicalInstancedStaticMeshComponent* AddLandscapeCandidateInstancedMeshComponent(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    bool bCastShadow,
    UMaterialInterface* MaterialOverride)
{
    if (!World || !Mesh)
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UHierarchicalInstancedStaticMeshComponent* Component =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(
            Actor,
            *FString::Printf(TEXT("%s_Instances"), *Label));
    if (!Component)
    {
        Actor->Destroy();
        return nullptr;
    }

    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCastShadow(bCastShadow);
    Component->SetCullDistances(0, 60000);
    if (MaterialOverride)
    {
        for (int32 MaterialIndex = 0; MaterialIndex < Mesh->GetStaticMaterials().Num(); ++MaterialIndex)
        {
            Component->SetMaterial(MaterialIndex, MaterialOverride);
        }
    }
    Actor->SetRootComponent(Component);
    Actor->AddInstanceComponent(Component);
    Component->RegisterComponent();
    return Component;
}

AActor* AddPreviewProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride,
    const TArray<FLinearColor>* VertexColorOverride,
    bool bCreateCollision)
{
    if (!World || Vertices.IsEmpty() || Triangles.IsEmpty())
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UProceduralMeshComponent* MeshComponent =
        NewObject<UProceduralMeshComponent>(Actor, *FString::Printf(TEXT("%s_Mesh"), *Label));
    if (!MeshComponent)
    {
        Actor->Destroy();
        return nullptr;
    }

    Actor->SetRootComponent(MeshComponent);
    Actor->AddInstanceComponent(MeshComponent);
    MeshComponent->RegisterComponent();
    MeshComponent->SetMobility(EComponentMobility::Static);
    MeshComponent->SetCastShadow(false);
    MeshComponent->bUseComplexAsSimpleCollision = bCreateCollision;
    MeshComponent->SetCollisionEnabled(
        bCreateCollision ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);

    TArray<FLinearColor> VertexColors;
    if (VertexColorOverride && VertexColorOverride->Num() == Vertices.Num())
    {
        VertexColors = *VertexColorOverride;
    }
    else
    {
        VertexColors.Init(Color, Vertices.Num());
    }
    TArray<FProcMeshTangent> Tangents;
    Tangents.Init(FProcMeshTangent(1.0f, 0.0f, 0.0f), Vertices.Num());

    MeshComponent->CreateMeshSection_LinearColor(
        0,
        Vertices,
        Triangles,
        Normals,
        UVs,
        VertexColors,
        Tangents,
        bCreateCollision);
    if (MaterialOverride)
    {
        MeshComponent->SetMaterial(0, MaterialOverride);
    }
    else
    {
        ApplyPreviewColor(MeshComponent, Color);
    }

    return Actor;
}

AActor* AddPreviewTwoSectionProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& FirstVertices,
    const TArray<int32>& FirstTriangles,
    const TArray<FVector>& FirstNormals,
    const TArray<FVector2D>& FirstUVs,
    UMaterialInterface* FirstMaterial,
    const TArray<FVector>& SecondVertices,
    const TArray<int32>& SecondTriangles,
    const TArray<FVector>& SecondNormals,
    const TArray<FVector2D>& SecondUVs,
    UMaterialInterface* SecondMaterial)
{
    if (!World || FirstVertices.IsEmpty() || FirstTriangles.IsEmpty() ||
        SecondVertices.IsEmpty() || SecondTriangles.IsEmpty() || !FirstMaterial ||
        !SecondMaterial)
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UProceduralMeshComponent* MeshComponent =
        NewObject<UProceduralMeshComponent>(Actor, *FString::Printf(TEXT("%s_Mesh"), *Label));
    if (!MeshComponent)
    {
        Actor->Destroy();
        return nullptr;
    }

    Actor->SetRootComponent(MeshComponent);
    Actor->AddInstanceComponent(MeshComponent);
    MeshComponent->RegisterComponent();
    MeshComponent->SetMobility(EComponentMobility::Static);
    MeshComponent->SetCastShadow(false);
    MeshComponent->bUseComplexAsSimpleCollision = false;
    MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    auto CreateSection = [MeshComponent](
                             int32 SectionIndex,
                             const TArray<FVector>& Vertices,
                             const TArray<int32>& Triangles,
                             const TArray<FVector>& Normals,
                             const TArray<FVector2D>& UVs,
                             UMaterialInterface* Material)
    {
        TArray<FLinearColor> VertexColors;
        VertexColors.Init(FLinearColor::White, Vertices.Num());
        TArray<FProcMeshTangent> Tangents;
        Tangents.Init(FProcMeshTangent(1.0f, 0.0f, 0.0f), Vertices.Num());
        MeshComponent->CreateMeshSection_LinearColor(
            SectionIndex,
            Vertices,
            Triangles,
            Normals,
            UVs,
            VertexColors,
            Tangents,
            false);
        MeshComponent->SetMaterial(SectionIndex, Material);
    };
    CreateSection(
        0,
        FirstVertices,
        FirstTriangles,
        FirstNormals,
        FirstUVs,
        FirstMaterial);
    CreateSection(
        1,
        SecondVertices,
        SecondTriangles,
        SecondNormals,
        SecondUVs,
        SecondMaterial);
    return Actor;
}

void AppendNativeCanopyTaperedSegment(
    const FVector& Start,
    const FVector& End,
    float StartRadius,
    float EndRadius,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    const FVector Axis = End - Start;
    const float Length = Axis.Size();
    if (Length < 1.0f || SegmentCount < 3)
    {
        return;
    }
    const FVector Direction = Axis / Length;
    FVector BasisX = FVector::CrossProduct(Direction, FVector::UpVector).GetSafeNormal();
    if (BasisX.IsNearlyZero())
    {
        BasisX = FVector::RightVector;
    }
    const FVector BasisY = FVector::CrossProduct(Direction, BasisX).GetSafeNormal();
    const int32 BaseIndex = Vertices.Num();
    for (int32 Ring = 0; Ring < 2; ++Ring)
    {
        const FVector Center = Ring == 0 ? Start : End;
        const float Radius = Ring == 0 ? StartRadius : EndRadius;
        for (int32 Index = 0; Index < SegmentCount; ++Index)
        {
            const float U = static_cast<float>(Index) / static_cast<float>(SegmentCount);
            const float Angle = U * 2.0f * PI;
            const FVector Radial = BasisX * FMath::Cos(Angle) + BasisY * FMath::Sin(Angle);
            Vertices.Add(Center + Radial * Radius);
            Normals.Add(Radial);
            UVs.Add(FVector2D(U, Ring == 0 ? 0.0f : Length / 320.0f));
        }
    }
    for (int32 Index = 0; Index < SegmentCount; ++Index)
    {
        const int32 Next = (Index + 1) % SegmentCount;
        const int32 A = BaseIndex + Index;
        const int32 B = BaseIndex + Next;
        const int32 C = BaseIndex + SegmentCount + Index;
        const int32 D = BaseIndex + SegmentCount + Next;
        Triangles.Append({A, C, B, B, C, D});
    }
}

void AppendNativeCanopyLeafCard(
    const FVector& Center,
    const FVector& Right,
    const FVector& Up,
    float Width,
    float Height,
    int32 AtlasTile,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    const FVector CardRight = Right.GetSafeNormal() * Width * 0.5f;
    const FVector CardUp = Up.GetSafeNormal() * Height * 0.5f;
    const FVector Normal = FVector::CrossProduct(CardRight, CardUp).GetSafeNormal();
    const int32 BaseIndex = Vertices.Num();
    Vertices.Append({
        Center - CardRight - CardUp,
        Center + CardRight - CardUp,
        Center + CardRight + CardUp,
        Center - CardRight + CardUp});
    Normals.Append({Normal, Normal, Normal, Normal});

    const int32 Tile = FMath::Abs(AtlasTile) % 16;
    const int32 Column = Tile % 4;
    const int32 Row = Tile / 4;
    constexpr float Inset = 0.012f;
    const float MinU = (static_cast<float>(Column) + Inset) / 4.0f;
    const float MaxU = (static_cast<float>(Column + 1) - Inset) / 4.0f;
    const float MinV = (static_cast<float>(Row) + Inset) / 4.0f;
    const float MaxV = (static_cast<float>(Row + 1) - Inset) / 4.0f;
    UVs.Append({
        FVector2D(MinU, MaxV),
        FVector2D(MaxU, MaxV),
        FVector2D(MaxU, MinV),
        FVector2D(MinU, MinV)});
    Triangles.Append({BaseIndex, BaseIndex + 2, BaseIndex + 1, BaseIndex, BaseIndex + 3, BaseIndex + 2});
}

void AppendNativeCanopyAtlasCurvedCard(
    const FVector& Start,
    const FVector& Axis,
    const FVector& Right,
    float Width,
    float Length,
    float Camber,
    float LateralSweep,
    int32 SegmentCount,
    int32 AtlasTile,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    if (SegmentCount < 2 || Width <= 0.0f || Length <= 0.0f)
    {
        return;
    }
    const FVector CardAxis = Axis.GetSafeNormal();
    const FVector CardRight =
        (Right - CardAxis * FVector::DotProduct(Right, CardAxis)).GetSafeNormal();
    if (CardAxis.IsNearlyZero() || CardRight.IsNearlyZero())
    {
        return;
    }
    const FVector BaseNormal = FVector::CrossProduct(CardRight, CardAxis).GetSafeNormal();
    const int32 Tile = FMath::Abs(AtlasTile) % 16;
    const int32 Column = Tile % 4;
    const int32 Row = Tile / 4;
    constexpr float Inset = 0.012f;
    const float MinU = (static_cast<float>(Column) + Inset) / 4.0f;
    const float MaxU = (static_cast<float>(Column + 1) - Inset) / 4.0f;
    const float MinV = (static_cast<float>(Row) + Inset) / 4.0f;
    const float MaxV = (static_cast<float>(Row + 1) - Inset) / 4.0f;
    const int32 BaseIndex = Vertices.Num();
    for (int32 SegmentIndex = 0; SegmentIndex <= SegmentCount; ++SegmentIndex)
    {
        const float T = static_cast<float>(SegmentIndex) / SegmentCount;
        const float CamberPhase = FMath::Sin(PI * T);
        const float SweepPhase = FMath::Sin(2.0f * PI * T);
        const FVector Center =
            Start + CardAxis * (Length * T) + BaseNormal * (Camber * CamberPhase) +
            CardRight * (LateralSweep * SweepPhase);
        const FVector Tangent =
            (CardAxis * Length + BaseNormal * (Camber * PI * FMath::Cos(PI * T)) +
             CardRight * (LateralSweep * 2.0f * PI * FMath::Cos(2.0f * PI * T)))
                .GetSafeNormal();
        const FVector SurfaceNormal =
            FVector::CrossProduct(CardRight, Tangent).GetSafeNormal();
        const float HalfWidth = Width * 0.5f * (0.94f + 0.06f * CamberPhase);
        Vertices.Append({Center - CardRight * HalfWidth, Center + CardRight * HalfWidth});
        Normals.Append({SurfaceNormal, SurfaceNormal});
        const float V = FMath::Lerp(MaxV, MinV, T);
        UVs.Append({FVector2D(MinU, V), FVector2D(MaxU, V)});
    }
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 A = BaseIndex + SegmentIndex * 2;
        const int32 B = A + 2;
        Triangles.Append({A, B + 1, A + 1, A, B, B + 1});
    }
}

void AppendNativeCanopyCurvedSprayRibbon(
    const FVector& Start,
    const FVector& Control,
    const FVector& End,
    const FVector& NormalHint,
    float StartHalfWidth,
    float EndHalfWidth,
    float HalfThickness,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    if (SegmentCount < 2 || FVector::Distance(Start, End) < 1.0f)
    {
        return;
    }
    const int32 BaseIndex = Vertices.Num();
    for (int32 SegmentIndex = 0; SegmentIndex <= SegmentCount; ++SegmentIndex)
    {
        const float T = static_cast<float>(SegmentIndex) / SegmentCount;
        const float OneMinusT = 1.0f - T;
        const FVector Center =
            Start * (OneMinusT * OneMinusT) + Control * (2.0f * OneMinusT * T) + End * (T * T);
        const FVector Tangent =
            ((Control - Start) * (2.0f * OneMinusT) + (End - Control) * (2.0f * T))
                .GetSafeNormal();
        FVector SurfaceNormal =
            (NormalHint - Tangent * FVector::DotProduct(NormalHint, Tangent)).GetSafeNormal();
        if (SurfaceNormal.IsNearlyZero())
        {
            SurfaceNormal = FVector::UpVector;
        }
        const FVector Side = FVector::CrossProduct(Tangent, SurfaceNormal).GetSafeNormal();
        const float HalfWidth = FMath::Lerp(StartHalfWidth, EndHalfWidth, T);
        const FVector SideOffset = Side * HalfWidth;
        const FVector ThicknessOffset = SurfaceNormal * HalfThickness;
        Vertices.Append({
            Center - SideOffset + ThicknessOffset,
            Center + SideOffset + ThicknessOffset,
            Center + SideOffset - ThicknessOffset,
            Center - SideOffset - ThicknessOffset});
        Normals.Append({SurfaceNormal, SurfaceNormal, -SurfaceNormal, -SurfaceNormal});
        UVs.Append({
            FVector2D(0.0f, T), FVector2D(1.0f, T),
            FVector2D(1.0f, T), FVector2D(0.0f, T)});
    }
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 A = BaseIndex + SegmentIndex * 4;
        const int32 B = A + 4;
        Triangles.Append({
            A, B, A + 1, A + 1, B, B + 1,
            A + 3, A + 2, B + 3, A + 2, B + 2, B + 3,
            A + 1, B + 1, A + 2, A + 2, B + 1, B + 2,
            A, A + 3, B, A + 3, B + 3, B});
    }
}

                                
 
               
                        
                       
                      
                         
                               
                                          
                                  
                                  
                                
                                 
                                 
                                   
                                
                                                     
                                               
                                                  
                                             
                                  
                                    
                                     
                           
                              
                                          
  

                                     
 
                                                                     
                                                                    
                                     
                                    
                                                
                                               
  

float NativeCanopySegmentDistance(
    const FVector& A1,
    const FVector& B1,
    const FVector& A2,
    const FVector& B2)
{
    FVector Closest1;
    FVector Closest2;
    FMath::SegmentDistToSegmentSafe(A1, B1, A2, B2, Closest1, Closest2);
    return FVector::Distance(Closest1, Closest2);
}
} // namespace RaftSimEditorEnvironment
