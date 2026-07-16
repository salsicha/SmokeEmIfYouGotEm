#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
FBox GetZambeziCliffComparisonEffectiveBounds(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return FBox(EForceInit::ForceInit);
    }

    const FBox RawBounds = Mesh->GetBoundingBox();
    if (RawBounds.GetSize().Z >= 100.0f || Mesh->GetNumSourceModels() == 0)
    {
        return RawBounds;
    }
    const FVector BuildScale = Mesh->GetSourceModel(0).BuildSettings.BuildScale3D;
    return FBox(RawBounds.Min * BuildScale, RawBounds.Max * BuildScale);
}

                                       
 
                                           
                                              
                                       
  

bool AddZambeziCliffComparisonInstances(
    UWorld* World,
    ACameraActor* Camera,
    UStaticMesh* CliffMesh,
    TArray<FZambeziCliffComparisonPlacement>& OutPlacements,
    FString& OutSummary)
{
    if (!World || !Camera || !CliffMesh)
    {
        return false;
    }

    TActorIterator<ALandscape> LandscapeIt(World);
    ALandscape* Landscape = LandscapeIt ? *LandscapeIt : nullptr;
    if (!Landscape)
    {
        OutSummary += TEXT("Zambezi cliff comparison could not find the source Landscape height authority.\n");
        return false;
    }

    const FVector CameraLocation = Camera->GetActorLocation();
    const FBox EffectiveCliffBounds = GetZambeziCliffComparisonEffectiveBounds(CliffMesh);
    FVector Forward = Camera->GetActorForwardVector();
    Forward.Z = 0.0f;
    Forward.Normalize();
    const FVector Right(-Forward.Y, Forward.X, 0.0f);
    const float ForwardDistancesCm[] = {
        16500.0f, 22500.0f, 29500.0f, 36500.0f,
        45500.0f, 55500.0f, 67500.0f, 80500.0f};
    const float SideSigns[] = {-1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f};
    const float LateralOffsetsCm[] = {
        8600.0f, 9800.0f, 11200.0f, 9400.0f,
        12600.0f, 10800.0f, 13800.0f, 11800.0f};
    const float UniformScales[] = {1.08f, 0.94f, 1.34f, 1.16f, 1.48f, 1.24f, 1.58f, 1.38f};
    const float YawOffsetsDeg[] = {-8.0f, 11.0f, 7.0f, -13.0f, 15.0f, -6.0f, -17.0f, 9.0f};

    OutPlacements.Reset();
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(ForwardDistancesCm); ++Index)
    {
        const FVector CandidateLocation =
            CameraLocation + Forward * ForwardDistancesCm[Index] +
            Right * SideSigns[Index] * LateralOffsetsCm[Index];
        const float GroundZ = Landscape->GetHeightAtLocation(
            FVector(CandidateLocation.X, CandidateLocation.Y, 0.0f),
            EHeightfieldSource::Editor).Get(TNumericLimits<float>::Lowest());
        if (!FMath::IsFinite(GroundZ))
        {
            OutSummary += FString::Printf(
                TEXT("Zambezi cliff comparison could not resolve ground height for placement %d.\n"),
                Index);
            return false;
        }

        FActorSpawnParameters SpawnParameters;
        SpawnParameters.ObjectFlags = RF_Transient;
        AStaticMeshActor* CliffActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform::Identity,
            SpawnParameters);
        if (!CliffActor || !CliffActor->GetStaticMeshComponent())
        {
            OutSummary += FString::Printf(
                TEXT("Zambezi cliff comparison failed to spawn placement %d.\n"),
                Index);
            return false;
        }

        const float UniformScale = UniformScales[Index];
        const FRotator Rotation(0.0f, Camera->GetActorRotation().Yaw + YawOffsetsDeg[Index], 0.0f);
        const FVector Location(
            CandidateLocation.X,
            CandidateLocation.Y,
            GroundZ - EffectiveCliffBounds.Min.Z * UniformScale + 4.0f);
        CliffActor->SetActorLabel(FString::Printf(TEXT("RaftSim_ZambeziCliffReview_%02d"), Index));
        CliffActor->Tags.Add(TEXT("RaftSim_ExternalReviewOnly"));
        CliffActor->SetActorLocationAndRotation(Location, Rotation);
        CliffActor->SetActorScale3D(FVector(UniformScale));
        UStaticMeshComponent* MeshComponent = CliffActor->GetStaticMeshComponent();
        MeshComponent->SetStaticMesh(CliffMesh);
        MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        MeshComponent->SetGenerateOverlapEvents(false);
        MeshComponent->SetCastShadow(true);
        MeshComponent->SetMobility(EComponentMobility::Static);
        MeshComponent->MarkRenderStateDirty();

        FZambeziCliffComparisonPlacement& Placement = OutPlacements.AddDefaulted_GetRef();
        Placement.Location = Location;
        Placement.Rotation = Rotation;
        Placement.Scale = FVector(UniformScale);
    }

    OutSummary += FString::Printf(
        TEXT("Placed %d transient, non-colliding Namaqualand cliff analog instances at bounded 0.94-1.58x scale for the Zambezi comparison capture.\n"),
        OutPlacements.Num());
    return OutPlacements.Num() == UE_ARRAY_COUNT(ForwardDistancesCm);
}

                                      
 
                        
                                           
                                              
                                       
  

bool AddZambeziBatokaBasaltCorridorComparisonInstances(
    UWorld* World,
    ACameraActor* Camera,
    const TArray<UStaticMesh*>& ModuleMeshes,
    TArray<FZambeziBatokaCorridorPlacement>& OutPlacements,
    FString& OutSummary)
{
    if (!World || !Camera || ModuleMeshes.Num() != 4)
    {
        return false;
    }
    for (UStaticMesh* ModuleMesh : ModuleMeshes)
    {
        if (!ModuleMesh)
        {
            return false;
        }
    }

    TActorIterator<ALandscape> LandscapeIt(World);
    ALandscape* Landscape = LandscapeIt ? *LandscapeIt : nullptr;
    if (!Landscape)
    {
        OutSummary += TEXT(
            "Batoka V10 corridor comparison could not find the source Landscape height authority.\n");
        return false;
    }

    const FVector CameraLocation = Camera->GetActorLocation();
    FVector Forward = Camera->GetActorForwardVector();
    Forward.Z = 0.0f;
    Forward.Normalize();
    const FVector Right(-Forward.Y, Forward.X, 0.0f);
    const float ForwardDistancesCm[] = {
        22000.0f, 31000.0f, 40500.0f, 50500.0f,
        61000.0f, 72000.0f, 84500.0f, 98000.0f};
    const float SideSigns[] = {-1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f, -1.0f, 1.0f};
    const float LateralOffsetsCm[] = {
        10500.0f, 11800.0f, 12600.0f, 11200.0f,
        13900.0f, 12100.0f, 14600.0f, 13200.0f};
    const float UniformScales[] = {3.20f, 2.80f, 3.60f, 3.00f, 4.00f, 3.40f, 4.40f, 3.80f};
    const float YawOffsetsDeg[] = {-5.0f, 7.0f, 4.0f, -8.0f, 9.0f, -4.0f, -10.0f, 6.0f};

    OutPlacements.Reset();
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(ForwardDistancesCm); ++Index)
    {
        UStaticMesh* ModuleMesh = ModuleMeshes[Index % ModuleMeshes.Num()];
        const FVector CandidateLocation =
            CameraLocation + Forward * ForwardDistancesCm[Index] +
            Right * SideSigns[Index] * LateralOffsetsCm[Index];
        const float GroundZ = Landscape->GetHeightAtLocation(
            FVector(CandidateLocation.X, CandidateLocation.Y, 0.0f),
            EHeightfieldSource::Editor).Get(TNumericLimits<float>::Lowest());
        if (!FMath::IsFinite(GroundZ))
        {
            OutSummary += FString::Printf(
                TEXT("Batoka V10 comparison could not resolve Landscape height for placement %d.\n"),
                Index);
            return false;
        }

        FActorSpawnParameters SpawnParameters;
        SpawnParameters.ObjectFlags = RF_Transient;
        AStaticMeshActor* ModuleActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform::Identity,
            SpawnParameters);
        if (!ModuleActor || !ModuleActor->GetStaticMeshComponent())
        {
            OutSummary += FString::Printf(
                TEXT("Batoka V10 comparison failed to spawn placement %d.\n"),
                Index);
            return false;
        }

        const float UniformScale = UniformScales[Index];
        const FVector ToCamera = (CameraLocation - CandidateLocation).GetSafeNormal2D();
        const FRotator Rotation(
            0.0f,
            ToCamera.Rotation().Yaw + 90.0f + YawOffsetsDeg[Index],
            0.0f);
        const FBox Bounds = ModuleMesh->GetBoundingBox();
        const FVector EmbeddedOrigin =
            CandidateLocation + ToCamera * Bounds.Min.Y * UniformScale;
        const FVector Location(
            EmbeddedOrigin.X,
            EmbeddedOrigin.Y,
            GroundZ - Bounds.Min.Z * UniformScale - 1000.0f);
        ModuleActor->SetActorLabel(FString::Printf(
            TEXT("RaftSim_ZambeziBatokaV10_TransientReview_%02d"),
            Index));
        ModuleActor->Tags.Add(TEXT("RaftSim_VisualReviewOnly"));
        ModuleActor->Tags.Add(TEXT("RaftSim_ExternalPixelsReviewOnly"));
        ModuleActor->SetActorLocationAndRotation(Location, Rotation);
        ModuleActor->SetActorScale3D(FVector(UniformScale));
        UStaticMeshComponent* MeshComponent = ModuleActor->GetStaticMeshComponent();
        MeshComponent->SetStaticMesh(ModuleMesh);
        MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        MeshComponent->SetGenerateOverlapEvents(false);
        MeshComponent->SetCastShadow(true);
        MeshComponent->SetMobility(EComponentMobility::Static);
        MeshComponent->MarkRenderStateDirty();

        FZambeziBatokaCorridorPlacement& Placement = OutPlacements.AddDefaulted_GetRef();
        Placement.ModuleAsset = ModuleMesh->GetPathName();
        Placement.Location = Location;
        Placement.Rotation = Rotation;
        Placement.Scale = FVector(UniformScale);
    }

    OutSummary += FString::Printf(
        TEXT("Placed %d transient, non-colliding V10 Batoka visual modules at gorge-scale 2.80-4.40x with front planes slope-aligned and bases buried 10 m; source map and collision remain unchanged.\n"),
        OutPlacements.Num());
    return OutPlacements.Num() == UE_ARRAY_COUNT(ForwardDistancesCm);
}

                                           
 
               
                        
                       
                   
                         
                         
                          
                          
                                
                               
                                 
                              
                              
                               
  

                                        
 
                            
                              
                          
                            
                                              
  

float GetBatokaDeterministicUnit(int32 Seed, int32 Channel)
{
    const float Value = FMath::Sin(
        static_cast<float>(Seed) * 0.17321f +
        static_cast<float>(Channel) * 1.61803f + 0.27183f) * 43758.5453f;
    return FMath::Abs(FMath::Frac(Value));
}

void AddBatokaBasaltQuad(
    const FVector& A,
    const FVector& B,
    const FVector& C,
    const FVector& D,
    const FLinearColor& ColorA,
    const FLinearColor& ColorB,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors)
{
    const int32 BaseIndex = OutVertices.Num();
    OutVertices.Append({A, B, C, D});
    OutTriangles.Append({
        BaseIndex,
        BaseIndex + 1,
        BaseIndex + 2,
        BaseIndex,
        BaseIndex + 2,
        BaseIndex + 3});
    const FVector Normal = FVector::CrossProduct(B - A, C - A).GetSafeNormal();
    OutNormals.Append({Normal, Normal, Normal, Normal});
    OutUVs.Append({
        FVector2D(0.0f, 0.0f),
        FVector2D(1.0f, 0.0f),
        FVector2D(1.0f, 1.0f),
        FVector2D(0.0f, 1.0f)});
    OutVertexColors.Append({
        ColorA,
        ScalePreviewColor(ColorA, 0.94f),
        ColorB,
        ScalePreviewColor(ColorB, 1.03f)});
}

void AddBatokaBasaltBlock(
    const FVector& Center,
    const FVector& Size,
    float YawDegrees,
    const FLinearColor& BaseColor,
    int32 Seed,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors)
{
    const float HalfX = Size.X * 0.5f;
    const float HalfY = Size.Y * 0.5f;
    const float HalfZ = Size.Z * 0.5f;
    const float BottomSkewX = (GetBatokaDeterministicUnit(Seed, 1) - 0.5f) * Size.X * 0.08f;
    const float TopSkewX = (GetBatokaDeterministicUnit(Seed, 2) - 0.5f) * Size.X * 0.16f;
    const float FrontSkewY = (GetBatokaDeterministicUnit(Seed, 3) - 0.5f) * Size.Y * 0.14f;
    const float BackSkewY = (GetBatokaDeterministicUnit(Seed, 4) - 0.5f) * Size.Y * 0.12f;
    const float TopLeanY = (GetBatokaDeterministicUnit(Seed, 5) - 0.5f) * Size.Y * 0.18f;
    const float CosYaw = FMath::Cos(FMath::DegreesToRadians(YawDegrees));
    const float SinYaw = FMath::Sin(FMath::DegreesToRadians(YawDegrees));
    auto TransformLocal = [Center, CosYaw, SinYaw](const FVector& Local)
    {
        return Center + FVector(
            Local.X * CosYaw - Local.Y * SinYaw,
            Local.X * SinYaw + Local.Y * CosYaw,
            Local.Z);
    };

    const FVector FBL = TransformLocal(FVector(-HalfX + BottomSkewX, -HalfY + FrontSkewY, -HalfZ));
    const FVector FBR = TransformLocal(FVector(HalfX + BottomSkewX, -HalfY - FrontSkewY, -HalfZ));
    const FVector FTR = TransformLocal(FVector(HalfX + TopSkewX, -HalfY + TopLeanY, HalfZ));
    const FVector FTL = TransformLocal(FVector(-HalfX + TopSkewX, -HalfY - TopLeanY, HalfZ));
    const FVector BBL = TransformLocal(FVector(-HalfX - BottomSkewX, HalfY + BackSkewY, -HalfZ));
    const FVector BBR = TransformLocal(FVector(HalfX - BottomSkewX, HalfY - BackSkewY, -HalfZ));
    const FVector BTR = TransformLocal(FVector(HalfX - TopSkewX, HalfY + TopLeanY, HalfZ));
    const FVector BTL = TransformLocal(FVector(-HalfX - TopSkewX, HalfY - TopLeanY, HalfZ));

    const FLinearColor FrontColor = ScalePreviewColor(
        BaseColor,
        0.78f + 0.25f * GetBatokaDeterministicUnit(Seed, 6));
    const FLinearColor SideColor = ScalePreviewColor(
        BaseColor,
        0.64f + 0.18f * GetBatokaDeterministicUnit(Seed, 7));
    const FLinearColor BackColor = ScalePreviewColor(BaseColor, 0.60f);
    const FLinearColor TopColor = FMath::Lerp(
        ScalePreviewColor(BaseColor, 1.04f),
        FLinearColor(0.31f, 0.27f, 0.22f, 1.0f),
        0.16f + 0.20f * GetBatokaDeterministicUnit(Seed, 8));
    const FLinearColor BottomColor = ScalePreviewColor(BaseColor, 0.54f);

    AddBatokaBasaltQuad(
        FBL, FBR, FTR, FTL, FrontColor, ScalePreviewColor(FrontColor, 1.08f),
        OutVertices, OutTriangles, OutNormals, OutUVs, OutVertexColors);
    AddBatokaBasaltQuad(
        BBR, BBL, BTL, BTR, BackColor, ScalePreviewColor(BackColor, 1.04f),
        OutVertices, OutTriangles, OutNormals, OutUVs, OutVertexColors);
    AddBatokaBasaltQuad(
        BBL, FBL, FTL, BTL, SideColor, ScalePreviewColor(SideColor, 0.90f),
        OutVertices, OutTriangles, OutNormals, OutUVs, OutVertexColors);
    AddBatokaBasaltQuad(
        FBR, BBR, BTR, FTR, ScalePreviewColor(SideColor, 1.08f), SideColor,
        OutVertices, OutTriangles, OutNormals, OutUVs, OutVertexColors);
    AddBatokaBasaltQuad(
        FTL, FTR, BTR, BTL, TopColor, ScalePreviewColor(TopColor, 1.08f),
        OutVertices, OutTriangles, OutNormals, OutUVs, OutVertexColors);
    AddBatokaBasaltQuad(
        BBL, BBR, FBR, FBL, BottomColor, BottomColor,
        OutVertices, OutTriangles, OutNormals, OutUVs, OutVertexColors);
}

void AddBatokaTalusRock(
    const FVector& BaseLocation,
    const FVector& Size,
    float YawDegrees,
    const FLinearColor& BaseColor,
    int32 Seed,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors)
{
    constexpr int32 SegmentCount = 8;
    constexpr int32 RingCount = 3;
    const float RingHeights[RingCount] = {0.06f, 0.38f, 0.72f};
    const float RingRadii[RingCount] = {0.76f, 1.0f, 0.68f};
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const float CosYaw = FMath::Cos(YawRadians);
    const float SinYaw = FMath::Sin(YawRadians);
    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 VertexSeed = Seed + RingIndex * 67 + SegmentIndex * 101;
            const float Angle = 2.0f * PI * static_cast<float>(SegmentIndex) /
                static_cast<float>(SegmentCount) +
                (GetBatokaDeterministicUnit(VertexSeed, 1) - 0.5f) * 0.22f;
            const float RadiusVariation = FMath::Lerp(
                0.76f,
                1.16f,
                GetBatokaDeterministicUnit(VertexSeed, 2));
            const float LocalX = FMath::Cos(Angle) * Size.X * 0.5f *
                RingRadii[RingIndex] * RadiusVariation;
            const float LocalY = FMath::Sin(Angle) * Size.Y * 0.5f *
                RingRadii[RingIndex] *
                FMath::Lerp(0.82f, 1.12f, GetBatokaDeterministicUnit(VertexSeed, 3));
            const float LocalZ = Size.Z *
                (RingHeights[RingIndex] +
                 (GetBatokaDeterministicUnit(VertexSeed, 4) - 0.5f) * 0.08f);
            OutVertices.Add(BaseLocation + FVector(
                LocalX * CosYaw - LocalY * SinYaw,
                LocalX * SinYaw + LocalY * CosYaw,
                LocalZ));
            OutUVs.Add(FVector2D(
                static_cast<float>(SegmentIndex) / static_cast<float>(SegmentCount),
                RingHeights[RingIndex]));
            OutVertexColors.Add(ScalePreviewColor(
                BaseColor,
                FMath::Lerp(0.72f, 1.10f, GetBatokaDeterministicUnit(VertexSeed, 5))));
        }
    }

    const int32 TopIndex = OutVertices.Num();
    OutVertices.Add(BaseLocation + FVector(
        (GetBatokaDeterministicUnit(Seed, 31) - 0.5f) * Size.X * 0.18f,
        (GetBatokaDeterministicUnit(Seed, 32) - 0.5f) * Size.Y * 0.18f,
        Size.Z * FMath::Lerp(0.88f, 1.04f, GetBatokaDeterministicUnit(Seed, 33))));
    OutUVs.Add(FVector2D(0.5f, 1.0f));
    OutVertexColors.Add(ScalePreviewColor(BaseColor, 1.12f));
    const int32 BottomIndex = OutVertices.Num();
    OutVertices.Add(BaseLocation + FVector(0.0f, 0.0f, 1.0f));
    OutUVs.Add(FVector2D(0.5f, 0.0f));
    OutVertexColors.Add(ScalePreviewColor(BaseColor, 0.62f));

    const int32 FirstRingIndex = TopIndex - RingCount * SegmentCount;
    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 CurrentRing = FirstRingIndex + RingIndex * SegmentCount;
        const int32 NextRing = CurrentRing + SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            const int32 A = CurrentRing + SegmentIndex;
            const int32 B = CurrentRing + NextSegment;
            const int32 C = NextRing + SegmentIndex;
            const int32 D = NextRing + NextSegment;
            OutTriangles.Append({A, B, D, A, D, C});
        }
    }
    const int32 LastRing = FirstRingIndex + (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        OutTriangles.Append({
            LastRing + SegmentIndex,
            LastRing + NextSegment,
            TopIndex,
            BottomIndex,
            FirstRingIndex + NextSegment,
            FirstRingIndex + SegmentIndex});
    }
}

TArray<FVector> ComputeBatokaBasaltNormals(
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles)
{
    TArray<FVector> Normals;
    Normals.Init(FVector::ZeroVector, Vertices.Num());
    for (int32 TriangleIndex = 0; TriangleIndex + 2 < Triangles.Num(); TriangleIndex += 3)
    {
        const int32 A = Triangles[TriangleIndex];
        const int32 B = Triangles[TriangleIndex + 1];
        const int32 C = Triangles[TriangleIndex + 2];
        if (!Vertices.IsValidIndex(A) || !Vertices.IsValidIndex(B) || !Vertices.IsValidIndex(C))
        {
            continue;
        }
        const FVector WeightedNormal = FVector::CrossProduct(
            Vertices[B] - Vertices[A],
            Vertices[C] - Vertices[A]);
        Normals[A] += WeightedNormal;
        Normals[B] += WeightedNormal;
        Normals[C] += WeightedNormal;
    }
    for (FVector& Normal : Normals)
    {
        Normal = Normal.GetSafeNormal(UE_SMALL_NUMBER, FVector::UpVector);
    }
    return Normals;
}

void BuildZambeziBatokaBasaltModuleGeometry(
    const FZambeziBatokaBasaltModuleDefinition& Definition,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors,
    FZambeziBatokaBasaltModuleMetrics& OutMetrics)
{
    OutVertices.Reset();
    OutTriangles.Reset();
    OutNormals.Reset();
    OutUVs.Reset();
    OutVertexColors.Reset();
    OutMetrics = FZambeziBatokaBasaltModuleMetrics();

    const int32 XCells = Definition.ColumnCount * 3;
    const int32 ZCells = Definition.MinimumLayerCount * 6;
    const int32 SurfaceRowSize = ZCells + 1;
    const FLinearColor MassiveBasalt(0.34f, 0.37f, 0.39f, 1.0f);
    const FLinearColor WarmBasalt(0.46f, 0.41f, 0.34f, 1.0f);
    const FLinearColor AmygdaloidalBand(0.49f, 0.31f, 0.27f, 1.0f);
    const FLinearColor BrecciatedBasalt(0.53f, 0.45f, 0.37f, 1.0f);

    TArray<float> ColumnTopHeights;
    ColumnTopHeights.SetNum(XCells + 1);
    for (int32 XIndex = 0; XIndex <= XCells; ++XIndex)
    {
        const float XNorm = static_cast<float>(XIndex) / static_cast<float>(XCells);
        const float GullyDistance = Definition.GullyCenterT >= 0.0f
            ? FMath::Abs(XNorm - Definition.GullyCenterT)
            : 1.0f;
        const float GullyT = Definition.GullyCenterT >= 0.0f
            ? 1.0f - FMath::Clamp(
                  GullyDistance / FMath::Max(0.001f, Definition.GullyHalfWidthT),
                  0.0f,
                  1.0f)
            : 0.0f;
        ColumnTopHeights[XIndex] = Definition.HeightCm * FMath::Clamp(
            0.94f +
                0.042f * FMath::Sin(XNorm * 7.0f + Definition.Seed * 0.017f) +
                0.025f * FMath::Sin(XNorm * 17.0f + Definition.Seed * 0.031f) -
                GullyT * 0.08f,
            0.82f,
            1.03f);
    }

    TArray<FVector> SurfacePositions;
    TArray<FLinearColor> SurfaceColors;
    SurfacePositions.SetNum((XCells + 1) * (ZCells + 1));
    SurfaceColors.SetNum(SurfacePositions.Num());
    for (int32 XIndex = 0; XIndex <= XCells; ++XIndex)
    {
        const float XNorm = static_cast<float>(XIndex) / static_cast<float>(XCells);
        const float BaseX = FMath::Lerp(-Definition.WidthCm * 0.5f, Definition.WidthCm * 0.5f, XNorm);
        const float GullyDistance = Definition.GullyCenterT >= 0.0f
            ? FMath::Abs(XNorm - Definition.GullyCenterT)
            : 1.0f;
        const float GullyT = Definition.GullyCenterT >= 0.0f
            ? 1.0f - FMath::Clamp(
                  GullyDistance / FMath::Max(0.001f, Definition.GullyHalfWidthT),
                  0.0f,
                  1.0f)
            : 0.0f;
        for (int32 ZIndex = 0; ZIndex <= ZCells; ++ZIndex)
        {
            const float ZNorm = static_cast<float>(ZIndex) / static_cast<float>(ZCells);
            const int32 VertexSeed = Definition.Seed + XIndex * 911 + ZIndex * 353;
            float VerticalJointDepth = 0.0f;
            float PrimaryJointT = 0.0f;
            const float JointStyleScale = Definition.Id == TEXT("jointed_mid_scarp")
                ? 1.0f
                : (Definition.Id == TEXT("lower_massive_scarp") ? 0.54f : 0.78f);
            const int32 JointCount = FMath::Max(3, Definition.ColumnCount / 2);
            for (int32 JointIndex = 0; JointIndex < JointCount; ++JointIndex)
            {
                const int32 JointSeed = Definition.Seed + (JointIndex + 1) * 617;
                const float JointCenter =
                    static_cast<float>(JointIndex + 1) / static_cast<float>(JointCount + 1) +
                    (GetBatokaDeterministicUnit(JointSeed, 1) - 0.5f) * 0.070f +
                    FMath::Sin(ZNorm * 4.0f + JointIndex * 1.37f) * 0.012f;
                const float JointHalfWidth = FMath::Lerp(
                    0.014f,
                    0.028f,
                    GetBatokaDeterministicUnit(JointSeed, 2));
                const float DistanceT = FMath::Abs(XNorm - JointCenter) / JointHalfWidth;
                const float JointProfile = FMath::Exp(-DistanceT * DistanceT);
                const float JointDepth = JointProfile * JointStyleScale * FMath::Lerp(
                    42.0f,
                    104.0f,
                    GetBatokaDeterministicUnit(JointSeed, 3));
                VerticalJointDepth = FMath::Max(VerticalJointDepth, JointDepth);
                PrimaryJointT = FMath::Max(PrimaryJointT, JointProfile);
            }
            const float BreakOneT = FMath::Exp(-FMath::Square((ZNorm - 0.34f) / 0.045f));
            const float BreakTwoT = FMath::Exp(-FMath::Square((ZNorm - 0.67f) / 0.040f));
            const float FlowBreakT = FMath::Max(BreakOneT, BreakTwoT);
            auto SmoothStep01 = [](float Value)
            {
                const float T = FMath::Clamp(Value, 0.0f, 1.0f);
                return T * T * (3.0f - 2.0f * T);
            };
            const float FlowSetback =
                SmoothStep01((ZNorm - 0.322f) / 0.026f) * 54.0f +
                SmoothStep01((ZNorm - 0.650f) / 0.030f) * 78.0f;
            const float MacroRelief =
                42.0f * FMath::Sin(XNorm * 5.0f + ZNorm * 2.1f + Definition.Seed * 0.011f) +
                19.0f * FMath::Sin(XNorm * 12.0f - ZNorm * 4.7f + Definition.Seed * 0.023f) +
                11.0f * FMath::Sin(XNorm * 23.0f + ZNorm * 10.0f + Definition.Seed * 0.037f);
            const float MicroRelief =
                (GetBatokaDeterministicUnit(VertexSeed, 2) - 0.5f) *
                FMath::Lerp(8.0f, 22.0f, Definition.BrecciaWeight);
            const float GullyRecession = GullyT * Definition.GullyDepthCm *
                (0.28f + 0.16f * FMath::Sin(ZNorm * PI));
            const float CellWidth = Definition.WidthCm / static_cast<float>(XCells);
            const float CellHeight = Definition.HeightCm / static_cast<float>(ZCells);
            const float XJitter = XIndex > 0 && XIndex < XCells
                ? (GetBatokaDeterministicUnit(Definition.Seed + XIndex * 2029, 4) - 0.5f) *
                    CellWidth * 0.18f
                : 0.0f;
            const float FractureLean =
                (ZNorm - 0.5f) * CellWidth * FMath::Lerp(
                    -0.14f,
                    0.14f,
                    GetBatokaDeterministicUnit(Definition.Seed + XIndex * 1877, 8));
            const float ZJitter = ZIndex > 0 && ZIndex < ZCells
                ? (GetBatokaDeterministicUnit(Definition.Seed + ZIndex * 2131, 5) - 0.5f) *
                    CellHeight * 0.20f
                : 0.0f;
            const float X = BaseX + XJitter + FractureLean;
            const float Z = ZNorm * ColumnTopHeights[XIndex] + ZJitter +
                FMath::Sin(XNorm * 9.0f + ZIndex * 0.81f) * CellHeight * 0.05f;
            const float Y =
                -Definition.DepthCm * 0.34f +
                FlowSetback +
                VerticalJointDepth + MacroRelief + MicroRelief + GullyRecession;
            const int32 SurfaceIndex = XIndex * SurfaceRowSize + ZIndex;
            SurfacePositions[SurfaceIndex] = FVector(X, Y, Z);

            const float SurfaceVariation = FMath::Clamp(
                0.40f +
                    0.30f * GetBatokaDeterministicUnit(VertexSeed, 3) +
                    0.18f * FMath::Sin(XNorm * 23.0f + ZNorm * 31.0f),
                0.0f,
                1.0f);
            FLinearColor Color = FMath::Lerp(MassiveBasalt, WarmBasalt, SurfaceVariation * 0.52f);
            Color = FMath::Lerp(Color, AmygdaloidalBand, FlowBreakT * (0.34f + Definition.BrecciaWeight * 0.18f));
            Color = FMath::Lerp(
                Color,
                BrecciatedBasalt,
                Definition.BrecciaWeight *
                    FMath::Pow(FMath::Clamp((ZNorm - 0.68f) / 0.32f, 0.0f, 1.0f), 1.4f) * 0.48f);
            Color = ScalePreviewColor(Color, FMath::Lerp(1.0f, 0.66f, PrimaryJointT));
            SurfaceColors[SurfaceIndex] = Color;
        }
    }

    const float TextureTileCm = 5000.0f;
    const float TextureAngle = FMath::DegreesToRadians(FMath::Lerp(
        -13.0f,
        17.0f,
        GetBatokaDeterministicUnit(Definition.Seed, 41)));
    const float TextureCos = FMath::Cos(TextureAngle);
    const float TextureSin = FMath::Sin(TextureAngle);
    const FVector2D TextureOffset(
        GetBatokaDeterministicUnit(Definition.Seed, 42) * 3.0f,
        GetBatokaDeterministicUnit(Definition.Seed, 43) * 3.0f);
    auto ProjectTextureUV = [TextureTileCm, TextureCos, TextureSin, TextureOffset](
                                const FVector& Position)
    {
        return TextureOffset + FVector2D(
            (Position.X * TextureCos - Position.Z * TextureSin) / TextureTileCm,
            (Position.X * TextureSin + Position.Z * TextureCos) / TextureTileCm);
    };
    OutVertices = SurfacePositions;
    OutNormals.Init(FVector::ZeroVector, OutVertices.Num());
    OutUVs.Reserve(OutVertices.Num());
    OutVertexColors.Reserve(OutVertices.Num());
    for (int32 SurfaceIndex = 0; SurfaceIndex < SurfacePositions.Num(); ++SurfaceIndex)
    {
        OutUVs.Add(ProjectTextureUV(SurfacePositions[SurfaceIndex]));
        OutVertexColors.Add(SurfaceColors[SurfaceIndex]);
    }
    for (int32 XIndex = 0; XIndex < XCells; ++XIndex)
    {
        for (int32 ZIndex = 0; ZIndex < ZCells; ++ZIndex)
        {
            const int32 LowerLeftIndex = XIndex * SurfaceRowSize + ZIndex;
            const int32 LowerRightIndex = (XIndex + 1) * SurfaceRowSize + ZIndex;
            const int32 UpperLeftIndex = LowerLeftIndex + 1;
            const int32 UpperRightIndex = LowerRightIndex + 1;
            OutTriangles.Append({
                LowerLeftIndex,
                UpperLeftIndex,
                LowerRightIndex,
                LowerRightIndex,
                UpperLeftIndex,
                UpperRightIndex});
        }
    }
    OutMetrics.WallCellCount = XCells * ZCells;

    const int32 TalusBlockCount = FMath::RoundToInt(
        static_cast<float>(Definition.ColumnCount) * Definition.TalusDensity * 4.6f);
    for (int32 TalusIndex = 0; TalusIndex < TalusBlockCount; ++TalusIndex)
    {
        const int32 TalusSeed = Definition.Seed * 31 + TalusIndex * 173;
        const float X = FMath::Lerp(
            -Definition.WidthCm * 0.54f,
            Definition.WidthCm * 0.54f,
            GetBatokaDeterministicUnit(TalusSeed, 1));
        const float ApronT = GetBatokaDeterministicUnit(TalusSeed, 2);
        const float Y = -FMath::Lerp(
            Definition.DepthCm * 0.04f,
            Definition.DepthCm * 0.68f,
            FMath::Pow(ApronT, 0.72f));
        const float Width = FMath::Lerp(
            90.0f,
            410.0f,
            FMath::Pow(GetBatokaDeterministicUnit(TalusSeed, 3), 1.55f));
        const float Depth = Width * FMath::Lerp(
            0.62f,
            1.36f,
            GetBatokaDeterministicUnit(TalusSeed, 4));
        const float Height = Width * FMath::Lerp(
            0.35f,
            0.92f,
            GetBatokaDeterministicUnit(TalusSeed, 5));
        const FLinearColor TalusColor = FMath::Lerp(
            FLinearColor(0.235f, 0.245f, 0.245f, 1.0f),
            FLinearColor(0.365f, 0.305f, 0.245f, 1.0f),
            0.20f + 0.50f * GetBatokaDeterministicUnit(TalusSeed, 6));
        AddBatokaTalusRock(
            FVector(X, Y, -4.0f),
            FVector(Width, Depth, Height),
            FMath::Lerp(-32.0f, 32.0f, GetBatokaDeterministicUnit(TalusSeed, 7)),
            TalusColor,
            TalusSeed,
            OutVertices,
            OutTriangles,
            OutUVs,
            OutVertexColors);
        ++OutMetrics.TalusBlockCount;
    }

    OutNormals = ComputeBatokaBasaltNormals(OutVertices, OutTriangles);
    for (int32 SurfaceIndex = 0; SurfaceIndex < SurfacePositions.Num(); ++SurfaceIndex)
    {
        if (OutNormals[SurfaceIndex].Y > 0.0f)
        {
            OutNormals[SurfaceIndex] *= -1.0f;
        }
    }
    OutMetrics.VertexCount = OutVertices.Num();
    OutMetrics.TriangleCount = OutTriangles.Num() / 3;
    for (const FVector& Vertex : OutVertices)
    {
        OutMetrics.Bounds += Vertex;
    }
}

UMaterialInterface* LoadOrCreateZambeziBatokaBasaltReviewMaterial(FString& OutSummary)
{
    static const TCHAR* MaterialPackagePath =
        TEXT("/Game/RaftSim/Environment/ProceduralGeology/ZambeziBatokaBasalt/Materials/"
             "M_RaftSim_ZambeziBatokaBasalt_V10_TwoScaleReview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Environment/ProceduralGeology/ZambeziBatokaBasalt/Materials/"
             "M_RaftSim_ZambeziBatokaBasalt_V10_TwoScaleReview."
             "M_RaftSim_ZambeziBatokaBasalt_V10_TwoScaleReview");
    UMaterial* Material = LoadObject<UMaterial>(nullptr, MaterialObjectPath);
    if (Material)
    {
        return Material;
    }

    static const TCHAR* MacroTextureRoot =
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K/");
    static const TCHAR* DetailTextureRoot =
        TEXT("/Game/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K/");
    auto LoadRockTexture = [](const TCHAR* Root, const TCHAR* AssetName)
    {
        const FString ObjectPath = FString::Printf(
            TEXT("%s%s.%s"),
            Root,
            AssetName,
            AssetName);
        return LoadObject<UTexture2D>(nullptr, *ObjectPath);
    };
    UTexture2D* ColorTexture = LoadRockTexture(MacroTextureRoot,
        TEXT("T_RaftSim_Batoka_AerialRocks02_Diffuse_4K"));
    UTexture2D* NormalTexture = LoadRockTexture(MacroTextureRoot,
        TEXT("T_RaftSim_Batoka_AerialRocks02_NormalDX_4K"));
    UTexture2D* AoTexture = LoadRockTexture(MacroTextureRoot,
        TEXT("T_RaftSim_Batoka_AerialRocks02_AO_4K"));
    UTexture2D* RoughnessTexture = LoadRockTexture(MacroTextureRoot,
        TEXT("T_RaftSim_Batoka_AerialRocks02_Roughness_4K"));
    UTexture2D* DisplacementTexture = LoadRockTexture(MacroTextureRoot,
        TEXT("T_RaftSim_Batoka_AerialRocks02_Displacement_4K"));
    UTexture2D* DetailColorTexture = LoadRockTexture(DetailTextureRoot,
        TEXT("T_RaftSim_Batoka_Rock037_Color_2K"));
    UTexture2D* DetailNormalTexture = LoadRockTexture(DetailTextureRoot,
        TEXT("T_RaftSim_Batoka_Rock037_NormalDX_2K"));
    UTexture2D* DetailRoughnessTexture = LoadRockTexture(DetailTextureRoot,
        TEXT("T_RaftSim_Batoka_Rock037_Roughness_2K"));
    if (!ColorTexture || !NormalTexture || !AoTexture || !RoughnessTexture ||
        !DisplacementTexture || !DetailColorTexture || !DetailNormalTexture ||
        !DetailRoughnessTexture)
    {
        OutSummary += TEXT(
            "Could not load the hash-reviewed Poly Haven macro and ambientCG detail textures for Batoka V10.\n");
        return nullptr;
    }

    UPackage* Package = CreatePackage(MaterialPackagePath);
    Material = Package
        ? NewObject<UMaterial>(
              Package,
              TEXT("M_RaftSim_ZambeziBatokaBasalt_V10_TwoScaleReview"),
              RF_Public | RF_Standalone | RF_Transactional)
        : nullptr;
    if (!Material)
    {
        OutSummary += TEXT("Could not create the Batoka V10 two-scale review material.\n");
        return nullptr;
    }

    FAssetRegistryModule::AssetCreated(Material);
    Material->Modify();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;

    UMaterialExpressionTextureCoordinate* Coordinates =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    Material->GetExpressionCollection().AddExpression(Coordinates);
    UMaterialExpressionTextureCoordinate* DetailCoordinates =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    DetailCoordinates->UTiling = 5000.0f / 240.0f;
    DetailCoordinates->VTiling = 5000.0f / 240.0f;
    Material->GetExpressionCollection().AddExpression(DetailCoordinates);
    auto AddTextureSample = [Material](
                                const TCHAR* ParameterName,
                                UTexture2D* Texture,
                                EMaterialSamplerType SamplerType,
                                UMaterialExpressionTextureCoordinate* TextureCoordinates)
    {
        UMaterialExpressionTextureSampleParameter2D* Sample =
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = ParameterName;
        Sample->Texture = Texture;
        Sample->SamplerType = SamplerType;
        Sample->Coordinates.Expression = TextureCoordinates;
        Sample->Group = TEXT("BatokaV10TwoScaleReview");
        Material->GetExpressionCollection().AddExpression(Sample);
        return Sample;
    };
    UMaterialExpressionTextureSampleParameter2D* ColorSample = AddTextureSample(
        TEXT("AerialRocks02Diffuse"),
        ColorTexture,
        SAMPLERTYPE_Color,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* NormalSample = AddTextureSample(
        TEXT("AerialRocks02NormalDX"),
        NormalTexture,
        SAMPLERTYPE_Normal,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* AoSample = AddTextureSample(
        TEXT("AerialRocks02AO"),
        AoTexture,
        SAMPLERTYPE_Masks,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* RoughnessSample = AddTextureSample(
        TEXT("AerialRocks02Roughness"),
        RoughnessTexture,
        SAMPLERTYPE_Masks,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* DisplacementSample = AddTextureSample(
        TEXT("AerialRocks02Displacement"),
        DisplacementTexture,
        SAMPLERTYPE_Masks,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* DetailColorSample = AddTextureSample(
        TEXT("Rock037DetailColor"),
        DetailColorTexture,
        SAMPLERTYPE_Color,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* DetailNormalSample = AddTextureSample(
        TEXT("Rock037DetailNormalDX"),
        DetailNormalTexture,
        SAMPLERTYPE_Normal,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* DetailRoughnessSample = AddTextureSample(
        TEXT("Rock037DetailRoughness"),
        DetailRoughnessTexture,
        SAMPLERTYPE_Masks,
        DetailCoordinates);

    UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
    Material->GetExpressionCollection().AddExpression(VertexColor);
    UMaterialExpressionConstant3Vector* TextureColorBalance =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    TextureColorBalance->Constant = FLinearColor(0.78f, 0.58f, 0.72f, 1.0f);
    Material->GetExpressionCollection().AddExpression(TextureColorBalance);
    UMaterialExpressionMultiply* ScaledTextureColor = NewObject<UMaterialExpressionMultiply>(Material);
    ScaledTextureColor->A.Expression = ColorSample;
    ScaledTextureColor->B.Expression = TextureColorBalance;
    Material->GetExpressionCollection().AddExpression(ScaledTextureColor);
    UMaterialExpressionConstant* DetailColorScale = NewObject<UMaterialExpressionConstant>(Material);
    DetailColorScale->R = 1.18f;
    Material->GetExpressionCollection().AddExpression(DetailColorScale);
    UMaterialExpressionMultiply* ScaledDetailColor = NewObject<UMaterialExpressionMultiply>(Material);
    ScaledDetailColor->A.Expression = DetailColorSample;
    ScaledDetailColor->B.Expression = DetailColorScale;
    Material->GetExpressionCollection().AddExpression(ScaledDetailColor);
    UMaterialExpressionConstant* DetailColorWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailColorWeight->R = 0.16f;
    Material->GetExpressionCollection().AddExpression(DetailColorWeight);
    UMaterialExpressionLinearInterpolate* TwoScaleTextureColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    TwoScaleTextureColor->A.Expression = ScaledTextureColor;
    TwoScaleTextureColor->B.Expression = ScaledDetailColor;
    TwoScaleTextureColor->Alpha.Expression = DetailColorWeight;
    Material->GetExpressionCollection().AddExpression(TwoScaleTextureColor);
    UMaterialExpressionConstant* VertexColorWeight = NewObject<UMaterialExpressionConstant>(Material);
    VertexColorWeight->R = 0.10f;
    Material->GetExpressionCollection().AddExpression(VertexColorWeight);
    UMaterialExpressionLinearInterpolate* TintedBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    TintedBaseColor->A.Expression = TwoScaleTextureColor;
    TintedBaseColor->B.Expression = VertexColor;
    TintedBaseColor->Alpha.Expression = VertexColorWeight;
    Material->GetExpressionCollection().AddExpression(TintedBaseColor);

    UMaterialExpressionComponentMask* DisplacementMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    DisplacementMask->Input.Expression = DisplacementSample;
    DisplacementMask->R = true;
    Material->GetExpressionCollection().AddExpression(DisplacementMask);
    UMaterialExpressionConstant* WeatheringWeight = NewObject<UMaterialExpressionConstant>(Material);
    WeatheringWeight->R = 0.04f;
    Material->GetExpressionCollection().AddExpression(WeatheringWeight);
    UMaterialExpressionMultiply* WeatheringAlpha = NewObject<UMaterialExpressionMultiply>(Material);
    WeatheringAlpha->A.Expression = DisplacementMask;
    WeatheringAlpha->B.Expression = WeatheringWeight;
    Material->GetExpressionCollection().AddExpression(WeatheringAlpha);
    UMaterialExpressionConstant3Vector* WeatheredBasalt =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    WeatheredBasalt->Constant = FLinearColor(0.31f, 0.255f, 0.20f, 1.0f);
    Material->GetExpressionCollection().AddExpression(WeatheredBasalt);
    UMaterialExpressionLinearInterpolate* FinalBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    FinalBaseColor->A.Expression = TintedBaseColor;
    FinalBaseColor->B.Expression = WeatheredBasalt;
    FinalBaseColor->Alpha.Expression = WeatheringAlpha;
    Material->GetExpressionCollection().AddExpression(FinalBaseColor);

    UMaterialExpressionComponentMask* RoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    RoughnessMask->Input.Expression = RoughnessSample;
    RoughnessMask->R = true;
    Material->GetExpressionCollection().AddExpression(RoughnessMask);
    UMaterialExpressionComponentMask* DetailRoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    DetailRoughnessMask->Input.Expression = DetailRoughnessSample;
    DetailRoughnessMask->R = true;
    Material->GetExpressionCollection().AddExpression(DetailRoughnessMask);
    UMaterialExpressionConstant* DetailRoughnessWeight =
        NewObject<UMaterialExpressionConstant>(Material);
    DetailRoughnessWeight->R = 0.28f;
    Material->GetExpressionCollection().AddExpression(DetailRoughnessWeight);
    UMaterialExpressionLinearInterpolate* TwoScaleRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    TwoScaleRoughness->A.Expression = RoughnessMask;
    TwoScaleRoughness->B.Expression = DetailRoughnessMask;
    TwoScaleRoughness->Alpha.Expression = DetailRoughnessWeight;
    Material->GetExpressionCollection().AddExpression(TwoScaleRoughness);
    UMaterialExpressionConstant* RoughnessFloor = NewObject<UMaterialExpressionConstant>(Material);
    RoughnessFloor->R = 0.72f;
    Material->GetExpressionCollection().AddExpression(RoughnessFloor);
    UMaterialExpressionConstant* RoughnessWeight = NewObject<UMaterialExpressionConstant>(Material);
    RoughnessWeight->R = 0.64f;
    Material->GetExpressionCollection().AddExpression(RoughnessWeight);
    UMaterialExpressionLinearInterpolate* Roughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    Roughness->A.Expression = RoughnessFloor;
    Roughness->B.Expression = TwoScaleRoughness;
    Roughness->Alpha.Expression = RoughnessWeight;
    Material->GetExpressionCollection().AddExpression(Roughness);

    UMaterialExpressionComponentMask* AoMask = NewObject<UMaterialExpressionComponentMask>(Material);
    AoMask->Input.Expression = AoSample;
    AoMask->R = true;
    Material->GetExpressionCollection().AddExpression(AoMask);
    UMaterialExpressionConstant* FullAo = NewObject<UMaterialExpressionConstant>(Material);
    FullAo->R = 1.0f;
    Material->GetExpressionCollection().AddExpression(FullAo);
    UMaterialExpressionConstant* AoWeight = NewObject<UMaterialExpressionConstant>(Material);
    AoWeight->R = 0.32f;
    Material->GetExpressionCollection().AddExpression(AoWeight);
    UMaterialExpressionLinearInterpolate* AmbientOcclusion =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    AmbientOcclusion->A.Expression = FullAo;
    AmbientOcclusion->B.Expression = AoMask;
    AmbientOcclusion->Alpha.Expression = AoWeight;
    Material->GetExpressionCollection().AddExpression(AmbientOcclusion);

    UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
    Specular->R = 0.11f;
    Material->GetExpressionCollection().AddExpression(Specular);
    UMaterialExpressionConstant* DiagnosticAmbientScale =
        NewObject<UMaterialExpressionConstant>(Material);
    DiagnosticAmbientScale->R = 0.028f;
    Material->GetExpressionCollection().AddExpression(DiagnosticAmbientScale);
    UMaterialExpressionMultiply* DiagnosticAmbient = NewObject<UMaterialExpressionMultiply>(Material);
    DiagnosticAmbient->A.Expression = FinalBaseColor;
    DiagnosticAmbient->B.Expression = DiagnosticAmbientScale;
    Material->GetExpressionCollection().AddExpression(DiagnosticAmbient);
    UMaterialExpressionConstant* DetailNormalWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailNormalWeight->R = 0.42f;
    Material->GetExpressionCollection().AddExpression(DetailNormalWeight);
    UMaterialExpressionLinearInterpolate* TwoScaleNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    TwoScaleNormal->A.Expression = NormalSample;
    TwoScaleNormal->B.Expression = DetailNormalSample;
    TwoScaleNormal->Alpha.Expression = DetailNormalWeight;
    Material->GetExpressionCollection().AddExpression(TwoScaleNormal);

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, FinalBaseColor);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, DiagnosticAmbient);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, TwoScaleNormal);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, AmbientOcclusion);
    Material->PostEditChange();
    Material->MarkPackageDirty();
    FAssetCompilingManager::Get().FinishAllCompilation();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        MaterialPackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save Batoka V10 two-scale review material %s.\n"),
            *Filename);
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved Batoka V10 one-sided two-scale surface review material %s.\n"),
        MaterialObjectPath);
    return Material;
}

                                              
 
                                   
                                    
                                    
                             
                              
                                
                            
                           
                           
                                       
                                      
                                          
                                     
                                        
                                        
                                     
                                 
                                     
                                   
                                                                     
                                                                        
                                                                    
                                                                       
                                           
                                      
                                 
                                 
                                  
                                
                                        
                                      
                                           
                                           
                                       
                                            
                                                                        
                                                                           
                                                         
  

                                      
 
                       
                                     
                                         
                                        
                                       
                                       
                                                                        
                                                                            
                                                                           
                                                                          
                                                                          
  

bool ApplyFutaleufuCanopyCorridorLightingTreatment(
    UWorld* World,
    EFutaleufuCanopyCorridorLightingTreatment Treatment,
    FString& OutSummary)
{
    if (!World)
    {
        return false;
    }
    if (Treatment == EFutaleufuCanopyCorridorLightingTreatment::Baseline)
    {
        OutSummary += TEXT("Retained the saved Futaleufu corridor light rig for the V18 baseline.\n");
        return true;
    }

    ASkyLight* CorridorSkyLight = nullptr;
    for (TActorIterator<ASkyLight> It(World); It; ++It)
    {
        ASkyLight* Candidate = *It;
        if (!CorridorSkyLight ||
            (Candidate && Candidate->GetActorLabel() == TEXT("RaftSim_SkyLight_PhotorealPreview")))
        {
            CorridorSkyLight = Candidate;
        }
        if (Candidate && Candidate->GetActorLabel() == TEXT("RaftSim_SkyLight_PhotorealPreview"))
        {
            break;
        }
    }
    if (!CorridorSkyLight || !CorridorSkyLight->GetLightComponent())
    {
        OutSummary += TEXT("Futaleufu V18 lighting treatment could not find the corridor skylight.\n");
        return false;
    }

    const float SkyLightIntensity =
        Treatment == EFutaleufuCanopyCorridorLightingTreatment::IsolatedReviewFill
        ? 1.65f
        : 3.10f;
    CorridorSkyLight->GetLightComponent()->SetIntensity(SkyLightIntensity);
    CorridorSkyLight->GetLightComponent()->RecaptureSky();

    if (Treatment == EFutaleufuCanopyCorridorLightingTreatment::IsolatedReviewFill)
    {
        ADirectionalLight* FrontFill = World->SpawnActor<ADirectionalLight>(
            ADirectionalLight::StaticClass(),
            FTransform(FRotator(-32.0f, 42.0f, 0.0f)));
        ADirectionalLight* BackFill = World->SpawnActor<ADirectionalLight>(
            ADirectionalLight::StaticClass(),
            FTransform(FRotator(-28.0f, -138.0f, 0.0f)));
        if (!FrontFill || !FrontFill->GetLightComponent() ||
            !BackFill || !BackFill->GetLightComponent())
        {
            OutSummary += TEXT("Futaleufu V18 lighting treatment could not create both transient fill lights.\n");
            return false;
        }
        FrontFill->SetFlags(RF_Transient);
        FrontFill->SetActorLabel(TEXT("RaftSim_V18_Coigue_TransientFrontFill"));
        FrontFill->GetLightComponent()->SetIntensity(0.75f);
        FrontFill->GetLightComponent()->SetLightColor(FLinearColor(0.94f, 0.98f, 1.0f));
        FrontFill->GetLightComponent()->SetCastShadows(false);
        BackFill->SetFlags(RF_Transient);
        BackFill->SetActorLabel(TEXT("RaftSim_V18_Coigue_TransientBackFill"));
        BackFill->GetLightComponent()->SetIntensity(0.38f);
        BackFill->GetLightComponent()->SetLightColor(FLinearColor(1.0f, 0.96f, 0.90f));
        BackFill->GetLightComponent()->SetCastShadows(false);
        OutSummary += TEXT("Applied the transient isolated-review front/back fill and 1.65 skylight treatment.\n");
    }
    else
    {
        OutSummary += TEXT("Applied the transient 3.10 skylight-only treatment and recaptured the sky.\n");
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    return true;
}

const TCHAR* GetFutaleufuCanopyCorridorRenderModeToken(
    EFutaleufuCanopyCorridorRenderMode RenderMode)
{
    switch (RenderMode)
    {
    case EFutaleufuCanopyCorridorRenderMode::NativeLeavesNoShadow:
        return TEXT("NativeLeavesNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::OpaqueLeavesNoShadow:
        return TEXT("OpaqueLeavesNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourNoShadow:
        return TEXT("NativeAlphaScaleFourNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow:
        return TEXT("NativeAlphaScaleTwoNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleThreeNoShadow:
        return TEXT("NativeAlphaScaleThreeNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoBoundedShadow:
        return TEXT("NativeAlphaScaleTwoBoundedShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeConstantOpacityNoShadow:
        return TEXT("NativeConstantOpacityNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourAoOffNoShadow:
        return TEXT("NativeAlphaScaleFourAoOffNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourFlatNormalNoShadow:
        return TEXT("NativeAlphaScaleFourFlatNormalNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourEmissiveNoShadow:
        return TEXT("NativeAlphaScaleFourEmissiveNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleNoShadow:
        return TEXT("NativeAlphaScaleFourBaseColorDoubleNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourTransmissionWhiteNoShadow:
        return TEXT("NativeAlphaScaleFourTransmissionWhiteNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow:
        return TEXT("NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourNoShadow:
        return TEXT("DefaultLitAlphaScaleFourNoShadow");
    case EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourBaseColorDoubleNoShadow:
        return TEXT("DefaultLitAlphaScaleFourBaseColorDoubleNoShadow");
    default:
        return TEXT("Native");
    }
}

bool AddFutaleufuCanopyCorridorComparisonInstances(
    UWorld* World,
    ACameraActor* Camera,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    EFutaleufuCanopyCorridorRenderMode RenderMode,
    FFutaleufuCanopyCorridorComparisonStats& OutStats,
    FString& OutSummary,
    bool bDenseLocalReview,
    bool bAreaSampledReview,
    bool bWorldStableReview)
{
    OutStats = FFutaleufuCanopyCorridorComparisonStats();
    if (!World || !Camera || Candidate.PreviewSpec.RiverId != TEXT("futaleufu_terminator"))
    {
        return false;
    }

    TActorIterator<ALandscape> LandscapeIt(World);
    ALandscape* Landscape = LandscapeIt ? *LandscapeIt : nullptr;
    if (!Landscape)
    {
        OutSummary += TEXT("Futaleufu canopy comparison could not find the source Landscape height authority.\n");
        return false;
    }

    FRaftSimPreviewImage VegetationMask;
    FRaftSimPreviewImage WaterMask;
    if (!LoadPreviewPngImage(Candidate.PreviewSpec.VegetationMaskImage, VegetationMask) ||
        !LoadPreviewPngImage(Candidate.PreviewSpec.WaterMaskImage, WaterMask))
    {
        OutSummary += TEXT("Futaleufu canopy comparison requires the source vegetation and water masks.\n");
        return false;
    }

    TArray<FRaftSimLandscapeCandidateCenterlinePoint> Centerline;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, Centerline, OutSummary) || Centerline.Num() < 2)
    {
        return false;
    }

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->GetActorLabel().Contains(TEXT("LandscapeCandidate_PveWhole")))
        {
            continue;
        }
        TArray<UPrimitiveComponent*> Components;
        Actor->GetComponents<UPrimitiveComponent>(Components);
        for (UPrimitiveComponent* Component : Components)
        {
            if (Component)
            {
                Component->SetVisibility(false, true);
                Component->SetHiddenInGame(true, true);
            }
        }
        Actor->SetActorHiddenInGame(true);
        Actor->SetIsTemporarilyHiddenInEditor(true);
        ++OutStats.HiddenFallbackActorCount;
    }

    static const TCHAR* VariantTokens[] = {
        TEXT("AdultPrototype"),
        TEXT("ForestGrownAdultPrototype"),
        TEXT("StormDamagedAdultPrototype"),
        TEXT("CompetitionLeanAdultPrototype"),
        TEXT("CrownGapAdultPrototype"),
        TEXT("IntermediatePrototype"),
        TEXT("SuppressedIntermediatePrototype"),
        TEXT("ReleasedIntermediatePrototype")};
    static const FString MeshRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Meshes/");
    UMaterial* BarkMaterial = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/"
             "M_RaftSim_FutaleufuCoigue_Bark.M_RaftSim_FutaleufuCoigue_Bark"));
    UMaterial* LeafMaterial = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/"
             "M_RaftSim_FutaleufuCoigue_Leaves.M_RaftSim_FutaleufuCoigue_Leaves"));
    if (!BarkMaterial || !LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu canopy comparison could not load the project-owned bark/leaf materials.\n");
        return false;
    }
    if (!EnsureFutaleufuNativeCanopyInstancedMaterialUsage(BarkMaterial, OutSummary) ||
        !EnsureFutaleufuNativeCanopyInstancedMaterialUsage(LeafMaterial, OutSummary))
    {
        return false;
    }
    const bool bDefaultLitDiagnostic =
        RenderMode == EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourBaseColorDoubleNoShadow;
    UMaterial* SourceLeafMaterial = LeafMaterial;
    if (bDefaultLitDiagnostic)
    {
        SourceLeafMaterial = LoadObject<UMaterial>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/"
                 "M_RaftSim_FutaleufuCoigue_Leaves_DefaultLitDiagnostic."
                 "M_RaftSim_FutaleufuCoigue_Leaves_DefaultLitDiagnostic"));
        if (!SourceLeafMaterial ||
            !EnsureFutaleufuNativeCanopyInstancedMaterialUsage(SourceLeafMaterial, OutSummary))
        {
            OutSummary += TEXT("Futaleufu canopy comparison could not load the masked DefaultLit diagnostic material.\n");
            return false;
        }
    }
    UMaterialInterface* CorridorLeafMaterial = SourceLeafMaterial;
    const bool bBoundedLeafShadow =
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoBoundedShadow;
    const bool bLeafCastShadow =
        RenderMode == EFutaleufuCanopyCorridorRenderMode::Native || bBoundedLeafShadow;
    if (RenderMode == EFutaleufuCanopyCorridorRenderMode::OpaqueLeavesNoShadow)
    {
        CorridorLeafMaterial = CreatePreviewColorMaterial(
            World,
            FLinearColor(0.045f, 0.31f, 0.065f, 1.0f));
        if (!CorridorLeafMaterial)
        {
            OutSummary += TEXT("Futaleufu canopy diagnostic could not create the opaque leaf material.\n");
            return false;
        }
    }
    else if (
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleThreeNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoBoundedShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeConstantOpacityNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourAoOffNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourFlatNormalNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourEmissiveNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourTransmissionWhiteNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourNoShadow ||
        RenderMode == EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourBaseColorDoubleNoShadow)
    {
        UMaterialInstanceDynamic* DiagnosticLeafMaterial =
            UMaterialInstanceDynamic::Create(SourceLeafMaterial, World);
        if (!DiagnosticLeafMaterial)
        {
            OutSummary += TEXT("Futaleufu canopy diagnostic could not create the native leaf material override.\n");
            return false;
        }
        float OpacityScale = 4.0f;
        if (RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeConstantOpacityNoShadow)
        {
            OpacityScale = 1.0f;
        }
        else if (
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow ||
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoBoundedShadow)
        {
            OpacityScale = 2.0f;
        }
        else if (RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleThreeNoShadow)
        {
            OpacityScale = 3.0f;
        }
        DiagnosticLeafMaterial->SetScalarParameterValue(TEXT("LeafOpacityScale"), OpacityScale);
        DiagnosticLeafMaterial->SetScalarParameterValue(
            TEXT("LeafOpacityOverride"),
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeConstantOpacityNoShadow
                ? 1.0f
                : 0.0f);
        DiagnosticLeafMaterial->SetScalarParameterValue(
            TEXT("LeafAOInfluence"),
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourAoOffNoShadow
                ? 0.0f
                : 0.55f);
        DiagnosticLeafMaterial->SetScalarParameterValue(
            TEXT("LeafNormalStrength"),
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourFlatNormalNoShadow
                ? 0.0f
                : 1.0f);
        DiagnosticLeafMaterial->SetScalarParameterValue(
            TEXT("LeafDiagnosticEmissive"),
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourEmissiveNoShadow
                ? 0.35f
                : 0.0f);
        const bool bDoubleBaseColor =
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleNoShadow ||
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow ||
            RenderMode == EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourBaseColorDoubleNoShadow;
        const bool bWhiteTransmission =
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourTransmissionWhiteNoShadow ||
            RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow;
        DiagnosticLeafMaterial->SetScalarParameterValue(
            TEXT("LeafBaseColorScale"),
            bDoubleBaseColor ? 2.36f : 1.18f);
        DiagnosticLeafMaterial->SetVectorParameterValue(
            TEXT("LeafTransmissionTint"),
            bWhiteTransmission
                ? FLinearColor::White
                : FLinearColor(0.55f, 0.78f, 0.36f));
        CorridorLeafMaterial = DiagnosticLeafMaterial;
    }

    auto LoadVariantMesh = [](const FString& AssetToken, const TCHAR* Suffix)
    {
        const FString AssetName = FString::Printf(
            TEXT("SM_RaftSim_FutaleufuCoigue_%s_%s"),
            *AssetToken,
            Suffix);
        const FString ObjectPath = MeshRoot + AssetName + TEXT(".") + AssetName;
        return LoadObject<UStaticMesh>(nullptr, *ObjectPath);
    };
    auto MarkTransientReviewComponent = [](UHierarchicalInstancedStaticMeshComponent* Component)
    {
        if (!Component)
        {
            return;
        }
        Component->SetFlags(RF_Transient);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        if (AActor* Owner = Component->GetOwner())
        {
            Owner->SetFlags(RF_Transient);
            Owner->Tags.Add(TEXT("RaftSim_ExternalReviewOnly"));
        }
    };

    TArray<FFutaleufuCanopyCorridorVariant> Variants;
    Variants.SetNum(UE_ARRAY_COUNT(VariantTokens));
    bool bAssetsAndComponentsComplete = true;
    for (int32 VariantIndex = 0; VariantIndex < Variants.Num(); ++VariantIndex)
    {
        FFutaleufuCanopyCorridorVariant& Variant = Variants[VariantIndex];
        Variant.AssetToken = VariantTokens[VariantIndex];
        Variant.TrunkMesh = LoadVariantMesh(Variant.AssetToken, TEXT("Trunk"));
        Variant.BranchletMesh = LoadVariantMesh(Variant.AssetToken, TEXT("Branchlets"));
        Variant.NearLeafMesh = LoadVariantMesh(Variant.AssetToken, TEXT("Leaves"));
        Variant.MidLeafMesh = LoadVariantMesh(Variant.AssetToken, TEXT("LeavesFar"));
        Variant.FarLeafMesh = LoadVariantMesh(Variant.AssetToken, TEXT("LeavesFarRuntime"));
        bAssetsAndComponentsComplete &= Variant.TrunkMesh && Variant.BranchletMesh &&
            Variant.NearLeafMesh && Variant.MidLeafMesh && Variant.FarLeafMesh;
        if (!bAssetsAndComponentsComplete)
        {
            continue;
        }
        const FString LabelStem = FString::Printf(
            TEXT("RaftSim_FutaleufuCoigueCorridorReview_%s_%s"),
            GetFutaleufuCanopyCorridorRenderModeToken(RenderMode),
            *Variant.AssetToken);
        Variant.TrunkInstances = AddLandscapeCandidateInstancedMeshComponent(
            World, Variant.TrunkMesh, LabelStem + TEXT("_Trunks"), true, BarkMaterial);
        Variant.BranchletInstances = AddLandscapeCandidateInstancedMeshComponent(
            World, Variant.BranchletMesh, LabelStem + TEXT("_NearBranchlets"), true, BarkMaterial);
        Variant.NearLeafInstances = AddLandscapeCandidateInstancedMeshComponent(
            World,
            Variant.NearLeafMesh,
            LabelStem + TEXT("_NearLeaves"),
            bLeafCastShadow,
            CorridorLeafMaterial);
        Variant.MidLeafInstances = AddLandscapeCandidateInstancedMeshComponent(
            World,
            Variant.MidLeafMesh,
            LabelStem + TEXT("_MidLeaves"),
            bLeafCastShadow && !bBoundedLeafShadow,
            CorridorLeafMaterial);
        Variant.FarLeafInstances = AddLandscapeCandidateInstancedMeshComponent(
            World,
            Variant.FarLeafMesh,
            LabelStem + TEXT("_FarRuntimeLeaves"),
            bLeafCastShadow && !bBoundedLeafShadow,
            CorridorLeafMaterial);
        if (bBoundedLeafShadow)
        {
            for (UHierarchicalInstancedStaticMeshComponent* LeafComponent : {
                     Variant.NearLeafInstances,
                     Variant.MidLeafInstances,
                     Variant.FarLeafInstances})
            {
                if (!LeafComponent)
                {
                    continue;
                }
                const bool bNearRepresentation = LeafComponent == Variant.NearLeafInstances;
                LeafComponent->SetCastShadow(bNearRepresentation);
                LeafComponent->bCastStaticShadow = false;
                LeafComponent->bCastDynamicShadow = bNearRepresentation;
                LeafComponent->SetCastContactShadow(false);
                LeafComponent->SetAffectDistanceFieldLighting(false);
                LeafComponent->SetAffectDynamicIndirectLighting(false);
            }
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component : {
                 Variant.TrunkInstances,
                 Variant.BranchletInstances,
                 Variant.NearLeafInstances,
                 Variant.MidLeafInstances,
                 Variant.FarLeafInstances})
        {
            bAssetsAndComponentsComplete &= Component != nullptr;
            MarkTransientReviewComponent(Component);
        }
        if (Variant.BranchletInstances)
        {
            Variant.BranchletInstances->SetCullDistances(0, 38000);
        }
        if (Variant.NearLeafInstances)
        {
            Variant.NearLeafInstances->SetCullDistances(0, 38000);
        }
        if (Variant.MidLeafInstances)
        {
            Variant.MidLeafInstances->SetCullDistances(0, 62000);
        }
        if (Variant.FarLeafInstances)
        {
            Variant.FarLeafInstances->SetCullDistances(0, 120000);
        }
    }
    if (!bAssetsAndComponentsComplete)
    {
        OutSummary += TEXT("Futaleufu canopy comparison could not load or instance all eight retained coigue forms.\n");
        return false;
    }

    auto Halton = [](int32 Index, int32 Base)
    {
        float Result = 0.0f;
        float Fraction = 1.0f / static_cast<float>(Base);
        int32 Value = Index + 1;
        while (Value > 0)
        {
            Result += Fraction * static_cast<float>(Value % Base);
            Value /= Base;
            Fraction /= static_cast<float>(Base);
        }
        return Result;
    };
    auto SampleSourceMask = [&Candidate](const FRaftSimPreviewImage& Mask, const FVector2D& WorldXY)
    {
        constexpr float LandscapeMinX = -5800.0f;
        const float U = FMath::Clamp(
            (WorldXY.X - LandscapeMinX) / Candidate.HorizontalSpanXCm,
            0.0f,
            1.0f);
        const float V = FMath::Clamp(
            (WorldXY.Y + Candidate.HorizontalSpanYCm * 0.5f) / Candidate.HorizontalSpanYCm,
            0.0f,
            1.0f);
        return Mask.SampleLuma(U, V);
    };
    auto LandscapeHeight = [Landscape](const FVector2D& WorldXY)
    {
        return Landscape->GetHeightAtLocation(
            FVector(WorldXY.X, WorldXY.Y, 0.0f),
            EHeightfieldSource::Editor).Get(TNumericLimits<float>::Lowest());
    };

    const bool bLocalReview =
        bDenseLocalReview || bAreaSampledReview || bWorldStableReview;
    float CameraProgress = 0.73f;
    if (bLocalReview)
    {
        float BestDistanceSquared = TNumericLimits<float>::Max();
        const FVector2D CameraXY(Camera->GetActorLocation().X, Camera->GetActorLocation().Y);
        constexpr int32 CameraProgressSampleCount = 512;
        for (int32 SampleIndex = 0; SampleIndex <= CameraProgressSampleCount; ++SampleIndex)
        {
            const float Progress =
                static_cast<float>(SampleIndex) / static_cast<float>(CameraProgressSampleCount);
            const float DistanceSquared = FVector2D::DistSquared(
                CameraXY,
                SampleLandscapeCandidateCenterlineWorld(Candidate, Centerline, Progress));
            if (DistanceSquared < BestDistanceSquared)
            {
                BestDistanceSquared = DistanceSquared;
                CameraProgress = Progress;
            }
        }
    }
    const int32 TargetTreeCount = bWorldStableReview ? 24000 : (bLocalReview ? 9000 : 1200);
    const int32 MaximumCandidateCount = bWorldStableReview ? 480000 : (bLocalReview ? 240000 : 60000);
    const float MinimumSpacingCm = bLocalReview ? 650.0f : 1500.0f;
    const float RiverSetbackCm = bLocalReview ? 2400.0f : 6500.0f;
    const float MaximumLateralOffsetCm = bLocalReview ? 75000.0f : 30000.0f;
    const float SamplingHalfExtentCm = bAreaSampledReview ? 110000.0f : 0.0f;
    const float SamplingAlongHalfExtentCm = bWorldStableReview ? 300000.0f : 0.0f;
    const float SamplingCrossHalfExtentCm = bWorldStableReview ? 110000.0f : 0.0f;
    const float ProgressMinimum = bWorldStableReview
        ? 0.54f
        : (bLocalReview
        ? FMath::Max(0.0f, CameraProgress - 0.06f)
        : 0.55f);
    const float ProgressMaximum = bWorldStableReview
        ? 0.92f
        : (bLocalReview
        ? FMath::Min(1.0f, CameraProgress + 0.06f)
        : 0.91f);
    constexpr float MinimumElevationCm = 10000.0f;
    constexpr float MaximumElevationCm = 90000.0f;
    constexpr float MaximumSlopeDegrees = 39.0f;
    constexpr float NearDistanceCm = 30000.0f;
    constexpr float MidDistanceCm = 50000.0f;
    constexpr float SlopeSampleOffsetCm = 1500.0f;
    TMap<FIntPoint, TArray<FVector2D>> SpatialBuckets;
    const FVector CameraLocation = Camera->GetActorLocation();
    const FVector2D CameraXY(CameraLocation.X, CameraLocation.Y);
    TArray<FVector2D> CenterlineReviewSamples;
    if (bAreaSampledReview || bWorldStableReview)
    {
        constexpr int32 CenterlineReviewSampleCount = 512;
        CenterlineReviewSamples.Reserve(CenterlineReviewSampleCount + 1);
        for (int32 SampleIndex = 0; SampleIndex <= CenterlineReviewSampleCount; ++SampleIndex)
        {
            CenterlineReviewSamples.Add(SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                Centerline,
                static_cast<float>(SampleIndex) /
                    static_cast<float>(CenterlineReviewSampleCount)));
        }
    }
    constexpr int32 OccupancyFieldResolution = 512;
    constexpr float OccupancyFeatherDistanceCm = 18000.0f;
    TArray<float> SpatialVegetationOccupancy;
    if (bWorldStableReview)
    {
        const int32 FieldCellCount = OccupancyFieldResolution * OccupancyFieldResolution;
        TArray<float> DistanceToInside;
        TArray<float> DistanceToOutside;
        DistanceToInside.SetNumUninitialized(FieldCellCount);
        DistanceToOutside.SetNumUninitialized(FieldCellCount);
        constexpr float InfiniteDistance = 1.0e12f;
        for (int32 Y = 0; Y < OccupancyFieldResolution; ++Y)
        {
            const float V = static_cast<float>(Y) /
                static_cast<float>(OccupancyFieldResolution - 1);
            for (int32 X = 0; X < OccupancyFieldResolution; ++X)
            {
                const float U = static_cast<float>(X) /
                    static_cast<float>(OccupancyFieldResolution - 1);
                const int32 Index = Y * OccupancyFieldResolution + X;
                const bool bInside = VegetationMask.SampleLuma(U, V) >= 0.34f;
                DistanceToInside[Index] = bInside ? 0.0f : InfiniteDistance;
                DistanceToOutside[Index] = bInside ? InfiniteDistance : 0.0f;
            }
        }
        const float StepX = Candidate.HorizontalSpanXCm /
            static_cast<float>(OccupancyFieldResolution - 1);
        const float StepY = Candidate.HorizontalSpanYCm /
            static_cast<float>(OccupancyFieldResolution - 1);
        const float StepDiagonal = FMath::Sqrt(StepX * StepX + StepY * StepY);
        auto RelaxDistanceField = [=](TArray<float>& Distances)
        {
            auto Relax = [&Distances](int32 Index, int32 NeighborIndex, float Step)
            {
                Distances[Index] = FMath::Min(
                    Distances[Index],
                    Distances[NeighborIndex] + Step);
            };
            for (int32 Y = 0; Y < OccupancyFieldResolution; ++Y)
            {
                for (int32 X = 0; X < OccupancyFieldResolution; ++X)
                {
                    const int32 Index = Y * OccupancyFieldResolution + X;
                    if (X > 0)
                    {
                        Relax(Index, Index - 1, StepX);
                    }
                    if (Y > 0)
                    {
                        Relax(Index, Index - OccupancyFieldResolution, StepY);
                        if (X > 0)
                        {
                            Relax(Index, Index - OccupancyFieldResolution - 1, StepDiagonal);
                        }
                        if (X + 1 < OccupancyFieldResolution)
                        {
                            Relax(Index, Index - OccupancyFieldResolution + 1, StepDiagonal);
                        }
                    }
                }
            }
            for (int32 Y = OccupancyFieldResolution - 1; Y >= 0; --Y)
            {
                for (int32 X = OccupancyFieldResolution - 1; X >= 0; --X)
                {
                    const int32 Index = Y * OccupancyFieldResolution + X;
                    if (X + 1 < OccupancyFieldResolution)
                    {
                        Relax(Index, Index + 1, StepX);
                    }
                    if (Y + 1 < OccupancyFieldResolution)
                    {
                        Relax(Index, Index + OccupancyFieldResolution, StepY);
                        if (X > 0)
                        {
                            Relax(Index, Index + OccupancyFieldResolution - 1, StepDiagonal);
                        }
                        if (X + 1 < OccupancyFieldResolution)
                        {
                            Relax(Index, Index + OccupancyFieldResolution + 1, StepDiagonal);
                        }
                    }
                }
            }
        };
        RelaxDistanceField(DistanceToInside);
        RelaxDistanceField(DistanceToOutside);
        SpatialVegetationOccupancy.SetNumUninitialized(FieldCellCount);
        for (int32 Index = 0; Index < FieldCellCount; ++Index)
        {
            const float SignedDistanceCm =
                DistanceToOutside[Index] - DistanceToInside[Index];
            SpatialVegetationOccupancy[Index] = SmoothPreviewStep(
                -OccupancyFeatherDistanceCm,
                OccupancyFeatherDistanceCm,
                SignedDistanceCm);
        }
    }
    auto SampleSpatialVegetationOccupancy =
        [&Candidate, &SpatialVegetationOccupancy](const FVector2D& WorldXY)
    {
        if (SpatialVegetationOccupancy.IsEmpty())
        {
            return 0.0f;
        }
        constexpr float LandscapeMinX = -5800.0f;
        const float U = FMath::Clamp(
            (WorldXY.X - LandscapeMinX) / Candidate.HorizontalSpanXCm,
            0.0f,
            1.0f);
        const float V = FMath::Clamp(
            (WorldXY.Y + Candidate.HorizontalSpanYCm * 0.5f) /
                Candidate.HorizontalSpanYCm,
            0.0f,
            1.0f);
        const float PixelX = U * static_cast<float>(OccupancyFieldResolution - 1);
        const float PixelY = V * static_cast<float>(OccupancyFieldResolution - 1);
        const int32 X0 = FMath::FloorToInt(PixelX);
        const int32 Y0 = FMath::FloorToInt(PixelY);
        const int32 X1 = FMath::Min(X0 + 1, OccupancyFieldResolution - 1);
        const int32 Y1 = FMath::Min(Y0 + 1, OccupancyFieldResolution - 1);
        const float FracX = PixelX - static_cast<float>(X0);
        const float FracY = PixelY - static_cast<float>(Y0);
        const float Top = FMath::Lerp(
            SpatialVegetationOccupancy[Y0 * OccupancyFieldResolution + X0],
            SpatialVegetationOccupancy[Y0 * OccupancyFieldResolution + X1],
            FracX);
        const float Bottom = FMath::Lerp(
            SpatialVegetationOccupancy[Y1 * OccupancyFieldResolution + X0],
            SpatialVegetationOccupancy[Y1 * OccupancyFieldResolution + X1],
            FracX);
        return FMath::Lerp(Top, Bottom, FracY);
    };
    OutStats.bDenseLocalReview = bDenseLocalReview;
    OutStats.bAreaSampledReview = bAreaSampledReview;
    OutStats.bWorldStableReview = bWorldStableReview;
    OutStats.TargetTreeCount = TargetTreeCount;
    OutStats.ProgressMinimum = ProgressMinimum;
    OutStats.ProgressMaximum = ProgressMaximum;
    OutStats.MinimumSpacingCm = MinimumSpacingCm;
    OutStats.RiverSetbackCm = RiverSetbackCm;
    OutStats.MaximumLateralOffsetCm = MaximumLateralOffsetCm;
    OutStats.SamplingHalfExtentCm = SamplingHalfExtentCm;
    OutStats.SamplingAlongHalfExtentCm = SamplingAlongHalfExtentCm;
    OutStats.SamplingCrossHalfExtentCm = SamplingCrossHalfExtentCm;
    OutStats.OccupancyFieldResolution = bWorldStableReview
        ? OccupancyFieldResolution
        : 0;
    OutStats.OccupancyFeatherDistanceCm = bWorldStableReview
        ? OccupancyFeatherDistanceCm
        : 0.0f;

    for (int32 CandidateIndex = 0;
         CandidateIndex < MaximumCandidateCount && OutStats.AcceptedTreeCount < TargetTreeCount;
         ++CandidateIndex)
    {
        ++OutStats.CandidateCount;
        float Progress = FMath::Lerp(
            ProgressMinimum,
            ProgressMaximum,
            Halton(CandidateIndex, 2));
        FVector2D WorldXY;
        float RiverDistanceCm = RiverSetbackCm;
        if (bWorldStableReview)
        {
            Progress = FMath::Lerp(
                ProgressMinimum,
                ProgressMaximum,
                FMath::Frac(Halton(CandidateIndex, 2) + 0.381966011f));
            FVector2D DomainTangent;
            const FVector2D DomainCenter = SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                Centerline,
                Progress,
                &DomainTangent);
            const FVector2D DomainNormal(-DomainTangent.Y, DomainTangent.X);
            const float CrossOffset = FMath::Lerp(
                -SamplingCrossHalfExtentCm,
                SamplingCrossHalfExtentCm,
                FMath::Frac(Halton(CandidateIndex, 3) + 0.618033989f));
            WorldXY = DomainCenter + DomainNormal * CrossOffset;
        }
        else if (bAreaSampledReview)
        {
            const float SampleX = FMath::Frac(Halton(CandidateIndex, 2) + 0.381966011f);
            const float SampleY = FMath::Frac(Halton(CandidateIndex, 3) + 0.618033989f);
            WorldXY = CameraXY + FVector2D(
                FMath::Lerp(-SamplingHalfExtentCm, SamplingHalfExtentCm, SampleX),
                FMath::Lerp(-SamplingHalfExtentCm, SamplingHalfExtentCm, SampleY));

        }
        if (bAreaSampledReview || bWorldStableReview)
        {
            float BestDistanceSquared = TNumericLimits<float>::Max();
            int32 BestSegmentIndex = 0;
            float BestSegmentT = 0.0f;
            for (int32 SegmentIndex = 0;
                 SegmentIndex + 1 < CenterlineReviewSamples.Num();
                 ++SegmentIndex)
            {
                const FVector2D SegmentStart = CenterlineReviewSamples[SegmentIndex];
                const FVector2D Segment =
                    CenterlineReviewSamples[SegmentIndex + 1] - SegmentStart;
                const float SegmentLengthSquared = Segment.SizeSquared();
                const float SegmentT = SegmentLengthSquared > UE_SMALL_NUMBER
                    ? FMath::Clamp(
                          FVector2D::DotProduct(WorldXY - SegmentStart, Segment) /
                              SegmentLengthSquared,
                          0.0f,
                          1.0f)
                    : 0.0f;
                const float DistanceSquared = FVector2D::DistSquared(
                    WorldXY,
                    SegmentStart + Segment * SegmentT);
                if (DistanceSquared < BestDistanceSquared)
                {
                    BestDistanceSquared = DistanceSquared;
                    BestSegmentIndex = SegmentIndex;
                    BestSegmentT = SegmentT;
                }
            }
            RiverDistanceCm = FMath::Sqrt(BestDistanceSquared);
            Progress = (static_cast<float>(BestSegmentIndex) + BestSegmentT) /
                static_cast<float>(CenterlineReviewSamples.Num() - 1);
            if (RiverDistanceCm < RiverSetbackCm)
            {
                ++OutStats.RejectedRiverSetbackCount;
                continue;
            }
        }
        else
        {
            const bool bMacroGap =
                (Progress > 0.675f && Progress < 0.692f) ||
                (Progress > 0.752f && Progress < 0.770f) ||
                (Progress > 0.842f && Progress < 0.854f);
            const float MicroGapThreshold = bDenseLocalReview ? 0.035f : 0.075f;
            const bool bMicroGap =
                FMath::Frac(Halton(CandidateIndex, 7) + Progress * 11.0f) <
                MicroGapThreshold;
            if (bMacroGap || bMicroGap)
            {
                ++OutStats.RejectedNaturalGapCount;
                continue;
            }

            FVector2D Tangent;
            const FVector2D Center = SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                Centerline,
                Progress,
                &Tangent);
            const FVector2D Normal(-Tangent.Y, Tangent.X);
            const float Side = Halton(CandidateIndex, 3) < 0.5f ? -1.0f : 1.0f;
            const float LateralT = FMath::Pow(Halton(CandidateIndex, 5), 0.72f);
            const float LateralOffset = FMath::Lerp(
                RiverSetbackCm,
                MaximumLateralOffsetCm,
                LateralT);
            WorldXY = Center + Normal * Side * LateralOffset;
            RiverDistanceCm = LateralOffset;
        }
        const float VegetationT = SampleSourceMask(VegetationMask, WorldXY);
        const float SpatialOccupancyT = bWorldStableReview
            ? SampleSpatialVegetationOccupancy(WorldXY)
            : VegetationT;
        const float VegetationThreshold = bWorldStableReview
            ? 0.10f
            : (bAreaSampledReview ? 0.27f : 0.34f);
        if (SpatialOccupancyT < VegetationThreshold)
        {
            ++OutStats.RejectedVegetationMaskCount;
            continue;
        }
        const float WaterT = SampleSourceMask(WaterMask, WorldXY);
        if (WaterT > 0.28f)
        {
            ++OutStats.RejectedWaterMaskCount;
            continue;
        }
        if (bAreaSampledReview || bWorldStableReview)
        {
            const float BroadStandNoise =
                0.5f + 0.5f * FMath::PerlinNoise2D(WorldXY * 0.0000065f + FVector2D(17.0f, -31.0f));
            const float MidStandNoise =
                0.5f + 0.5f * FMath::PerlinNoise2D(WorldXY * 0.000018f + FVector2D(-43.0f, 29.0f));
            const float StandNoise = FMath::Clamp(
                BroadStandNoise * 0.68f + MidStandNoise * 0.32f,
                0.0f,
                1.0f);
            const float MaskFeather = bWorldStableReview
                ? SpatialOccupancyT
                : SmoothPreviewStep(0.27f, 0.68f, VegetationT);
            const float RiverGradient = SmoothPreviewStep(
                RiverSetbackCm,
                RiverSetbackCm + 18000.0f,
                RiverDistanceCm);
            const float StandProbability = FMath::Clamp(
                (0.34f + StandNoise * 0.58f) *
                    FMath::Lerp(0.30f, 1.0f, MaskFeather) *
                    FMath::Lerp(0.72f, 1.0f, RiverGradient),
                0.0f,
                0.96f);
            if (StandNoise < 0.20f || Halton(CandidateIndex, 23) > StandProbability)
            {
                ++OutStats.RejectedStandDensityCount;
                continue;
            }
        }

        const float GroundZ = LandscapeHeight(WorldXY);
        if (!FMath::IsFinite(GroundZ) || GroundZ < MinimumElevationCm || GroundZ > MaximumElevationCm)
        {
            ++OutStats.RejectedElevationCount;
            continue;
        }
        const float HeightMinusX = LandscapeHeight(WorldXY - FVector2D(SlopeSampleOffsetCm, 0.0f));
        const float HeightPlusX = LandscapeHeight(WorldXY + FVector2D(SlopeSampleOffsetCm, 0.0f));
        const float HeightMinusY = LandscapeHeight(WorldXY - FVector2D(0.0f, SlopeSampleOffsetCm));
        const float HeightPlusY = LandscapeHeight(WorldXY + FVector2D(0.0f, SlopeSampleOffsetCm));
        if (!FMath::IsFinite(HeightMinusX) || !FMath::IsFinite(HeightPlusX) ||
            !FMath::IsFinite(HeightMinusY) || !FMath::IsFinite(HeightPlusY))
        {
            ++OutStats.RejectedSlopeCount;
            continue;
        }
        const FVector2D Gradient(
            (HeightPlusX - HeightMinusX) / (2.0f * SlopeSampleOffsetCm),
            (HeightPlusY - HeightMinusY) / (2.0f * SlopeSampleOffsetCm));
        const float SlopeDegrees = FMath::RadiansToDegrees(FMath::Atan(Gradient.Size()));
        if (SlopeDegrees > MaximumSlopeDegrees)
        {
            ++OutStats.RejectedSlopeCount;
            continue;
        }
        const FVector2D Downhill = (-Gradient).GetSafeNormal();
        const FVector2D MoistAspect(-0.5f, -0.8660254f);
        const float MoistAspectT = Downhill.IsNearlyZero()
            ? 0.5f
            : 0.5f + 0.5f * FVector2D::DotProduct(Downhill, MoistAspect);
        if (MoistAspectT < 0.28f && Halton(CandidateIndex, 11) < 0.52f)
        {
            ++OutStats.RejectedDryAspectCount;
            continue;
        }

        const FIntPoint Bucket(
            FMath::FloorToInt(WorldXY.X / MinimumSpacingCm),
            FMath::FloorToInt(WorldXY.Y / MinimumSpacingCm));
        bool bSpacingRejected = false;
        for (int32 OffsetX = -1; OffsetX <= 1 && !bSpacingRejected; ++OffsetX)
        {
            for (int32 OffsetY = -1; OffsetY <= 1 && !bSpacingRejected; ++OffsetY)
            {
                if (const TArray<FVector2D>* Existing = SpatialBuckets.Find(
                        Bucket + FIntPoint(OffsetX, OffsetY)))
                {
                    for (const FVector2D& ExistingXY : *Existing)
                    {
                        if (FVector2D::Distance(WorldXY, ExistingXY) < MinimumSpacingCm)
                        {
                            bSpacingRejected = true;
                            break;
                        }
                    }
                }
            }
        }
        if (bSpacingRejected)
        {
            ++OutStats.RejectedSpacingCount;
            continue;
        }
        SpatialBuckets.FindOrAdd(Bucket).Add(WorldXY);

        const int32 VariantIndex = FMath::Clamp(
            FMath::FloorToInt(Halton(CandidateIndex, 13) * static_cast<float>(Variants.Num())),
            0,
            Variants.Num() - 1);
        FFutaleufuCanopyCorridorVariant& Variant = Variants[VariantIndex];
        const float UniformScale = bLocalReview
            ? 0.78f + Halton(CandidateIndex, 17) * 0.34f
            : 0.72f + Halton(CandidateIndex, 17) * 0.31f;
        const FRotator Rotation(
            0.0f,
            FMath::Fmod(Halton(CandidateIndex, 19) * 360.0f + Progress * 137.5f, 360.0f),
            0.0f);
        const FBox TrunkBounds = Variant.TrunkMesh->GetBoundingBox();
        const FVector Location(
            WorldXY.X,
            WorldXY.Y,
            GroundZ - TrunkBounds.Min.Z * UniformScale);
        const FTransform Transform(Rotation, Location, FVector(UniformScale));
        Variant.TrunkInstances->AddInstance(Transform, true);
        const float CameraDistance2D = FVector2D::Distance(
            WorldXY,
            FVector2D(CameraLocation.X, CameraLocation.Y));
        if (CameraDistance2D <= NearDistanceCm)
        {
            Variant.BranchletInstances->AddInstance(Transform, true);
            Variant.NearLeafInstances->AddInstance(Transform, true);
            ++OutStats.NearTreeCount;
        }
        else if (CameraDistance2D <= MidDistanceCm)
        {
            Variant.MidLeafInstances->AddInstance(Transform, true);
            ++OutStats.MidTreeCount;
        }
        else
        {
            Variant.FarLeafInstances->AddInstance(Transform, true);
            ++OutStats.FarTreeCount;
        }
        ++OutStats.AcceptedTreeCount;
        OutStats.MinimumAcceptedSlopeDegrees = FMath::Min(
            OutStats.MinimumAcceptedSlopeDegrees,
            SlopeDegrees);
        OutStats.MaximumAcceptedSlopeDegrees = FMath::Max(
            OutStats.MaximumAcceptedSlopeDegrees,
            SlopeDegrees);
        OutStats.MinimumAcceptedElevationCm = FMath::Min(
            OutStats.MinimumAcceptedElevationCm,
            GroundZ);
        OutStats.MaximumAcceptedElevationCm = FMath::Max(
            OutStats.MaximumAcceptedElevationCm,
            GroundZ);
        OutStats.AcceptedVegetationMaskSum += VegetationT;
        OutStats.AcceptedWaterMaskSum += WaterT;
        OutStats.MinimumAcceptedRiverDistanceCm = FMath::Min(
            OutStats.MinimumAcceptedRiverDistanceCm,
            RiverDistanceCm);
        OutStats.MaximumAcceptedRiverDistanceCm = FMath::Max(
            OutStats.MaximumAcceptedRiverDistanceCm,
            RiverDistanceCm);
        auto MixFingerprint = [&OutStats](uint64 Value)
        {
            OutStats.PlacementFingerprint ^= Value;
            OutStats.PlacementFingerprint *= 1099511628211ull;
        };
        MixFingerprint(static_cast<uint64>(CandidateIndex));
        MixFingerprint(static_cast<uint64>(FMath::RoundToInt(WorldXY.X)));
        MixFingerprint(static_cast<uint64>(FMath::RoundToInt(WorldXY.Y)));
        MixFingerprint(static_cast<uint64>(VariantIndex));
    }

    const bool bComplete =
        OutStats.AcceptedTreeCount == TargetTreeCount &&
        OutStats.NearTreeCount > 0 &&
        OutStats.MidTreeCount > 0 &&
        OutStats.FarTreeCount > 0 &&
        OutStats.HiddenFallbackActorCount >= 4;
    OutSummary += FString::Printf(
        TEXT("Futaleufu %s source-masked canopy comparison placed %d/%d transient non-colliding trees "
             "(%d near full, %d mid, %d runtime far) in %s render mode across progress %.4f-%.4f, "
             "hid %d fallback PVE actors, and evaluated %d candidates.\n"),
        bAreaSampledReview
            ? TEXT("2D area-sampled camera-local")
            : (bWorldStableReview
                   ? TEXT("spatial-occupancy world-stable")
                   : (bDenseLocalReview ? TEXT("dense centerline camera-local") : TEXT("retained sparse route-wide"))),
        OutStats.AcceptedTreeCount,
        TargetTreeCount,
        OutStats.NearTreeCount,
        OutStats.MidTreeCount,
        OutStats.FarTreeCount,
        GetFutaleufuCanopyCorridorRenderModeToken(RenderMode),
        ProgressMinimum,
        ProgressMaximum,
        OutStats.HiddenFallbackActorCount,
        OutStats.CandidateCount);
    return bComplete;
}
} // namespace RaftSimEditorEnvironment
