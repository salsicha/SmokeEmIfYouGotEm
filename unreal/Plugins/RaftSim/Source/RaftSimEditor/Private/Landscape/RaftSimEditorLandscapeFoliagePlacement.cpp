#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"
#include <type_traits>

namespace RaftSimEditorEnvironment::LandscapeFoliage
{
bool AddLandscapeCandidatePlacements(const FPlacementContext& Context)
{
    auto& World = Context.World;
    auto& Landscape = Context.Landscape;
    auto& Candidate = Context.Candidate;
    auto& OutResult = Context.OutResult;
    auto& OutSummary = Context.OutSummary;
    auto& bPacuare = Context.bPacuare;
    auto& bFutaleufu = Context.bFutaleufu;
    auto& bChilko = Context.bChilko;
    auto& bColoradoHance = Context.bColoradoHance;
    auto& bOpaqueTemperate = Context.bOpaqueTemperate;
    auto& bUsesOpaqueVolumetricVegetation = Context.bUsesOpaqueVolumetricVegetation;
    auto& ReviewedRockMeshes = Context.ReviewedRockMeshes;
    auto& ReviewedPineMeshes = Context.ReviewedPineMeshes;
    auto& FutaleufuScannedUnderstoryMeshes = Context.FutaleufuScannedUnderstoryMeshes;
    auto& PacuareScannedFernMeshes = Context.PacuareScannedFernMeshes;
    auto& BroadleafTreeMesh = Context.BroadleafTreeMesh;
    auto& ConiferTreeMesh = Context.ConiferTreeMesh;
    auto& ShrubMesh = Context.ShrubMesh;
    auto& UnderstoryMesh = Context.UnderstoryMesh;
    auto& ZambeziGroundCoverMeshB = Context.ZambeziGroundCoverMeshB;
    auto& TemperateBroadleafTreeMeshB = Context.TemperateBroadleafTreeMeshB;
    auto& TemperateConiferTreeMeshB = Context.TemperateConiferTreeMeshB;
    auto& TemperateShrubMeshB = Context.TemperateShrubMeshB;
    auto& TemperateUnderstoryMeshB = Context.TemperateUnderstoryMeshB;
    auto& PacuareForestFloorMeshes = Context.PacuareForestFloorMeshes;
    auto& HanceDrylandShrubMeshA = Context.HanceDrylandShrubMeshA;
    auto& HanceDrylandShrubMeshB = Context.HanceDrylandShrubMeshB;
    auto& HanceDrylandGroundCoverMeshA = Context.HanceDrylandGroundCoverMeshA;
    auto& HanceDrylandGroundCoverMeshB = Context.HanceDrylandGroundCoverMeshB;
    auto& WaterMask = Context.WaterMask;
    auto& VegetationMask = Context.VegetationMask;
    auto& Spec = Context.Spec;
    auto& BroadleafTreeInstances = Context.BroadleafTreeInstances;
    auto& ConiferTreeInstances = Context.ConiferTreeInstances;
    auto& ShrubInstances = Context.ShrubInstances;
    auto& UnderstoryInstances = Context.UnderstoryInstances;
    auto& TemperateBroadleafTreeInstancesB = Context.TemperateBroadleafTreeInstancesB;
    auto& TemperateConiferTreeInstancesB = Context.TemperateConiferTreeInstancesB;
    auto& TemperateShrubInstancesB = Context.TemperateShrubInstancesB;
    auto& TemperateUnderstoryInstancesB = Context.TemperateUnderstoryInstancesB;
    auto& HanceDrylandGroundCoverInstancesA = Context.HanceDrylandGroundCoverInstancesA;
    auto& HanceDrylandGroundCoverInstancesB = Context.HanceDrylandGroundCoverInstancesB;
    auto& HanceDrylandShrubInstancesA = Context.HanceDrylandShrubInstancesA;
    auto& HanceDrylandShrubInstancesB = Context.HanceDrylandShrubInstancesB;
    auto& ZambeziBankMosaicInstances = Context.ZambeziBankMosaicInstances;
    auto& ZambeziCameraRiparianTreeInstances = Context.ZambeziCameraRiparianTreeInstances;
    auto& ZambeziCameraUmbrellaTreeInstances = Context.ZambeziCameraUmbrellaTreeInstances;
    auto& ZambeziCameraThornScrubInstances = Context.ZambeziCameraThornScrubInstances;
    auto& ZambeziRunnableLaunchGroundCoverInstances = Context.ZambeziRunnableLaunchGroundCoverInstances;
    auto& ZambeziRunnableLaunchGroundCoverInstancesB = Context.ZambeziRunnableLaunchGroundCoverInstancesB;
    auto& ZambeziRunnableLaunchRiparianTreeInstances = Context.ZambeziRunnableLaunchRiparianTreeInstances;
    auto& ZambeziRunnableLaunchUmbrellaTreeInstances = Context.ZambeziRunnableLaunchUmbrellaTreeInstances;
    auto& ZambeziRunnableLaunchThornScrubInstances = Context.ZambeziRunnableLaunchThornScrubInstances;
    auto& ReviewedRockInstances = Context.ReviewedRockInstances;
    auto& TemperateWaterlineStructureInstances = Context.TemperateWaterlineStructureInstances;
    auto& ChilkoOrganicShorelineGravelInstances = Context.ChilkoOrganicShorelineGravelInstances;
    auto& ChilkoOrganicShorelineGroundCoverInstances = Context.ChilkoOrganicShorelineGroundCoverInstances;
    auto& PacuareOrganicShorelineRockInstances = Context.PacuareOrganicShorelineRockInstances;
    auto& PacuareOrganicShorelineGroundCoverInstances = Context.PacuareOrganicShorelineGroundCoverInstances;
    auto& PacuareOrganicShorelineShrubInstances = Context.PacuareOrganicShorelineShrubInstances;
    auto& PacuareScannedFernInstances = Context.PacuareScannedFernInstances;
    auto& PacuareForestFloorInstances = Context.PacuareForestFloorInstances;
    auto& ZambeziRunnableLaunchTalusInstances = Context.ZambeziRunnableLaunchTalusInstances;
    auto& ZambeziDryScarpOutcropInstances = Context.ZambeziDryScarpOutcropInstances;
    auto& ReviewedPineInstances = Context.ReviewedPineInstances;
    auto& FutaleufuScannedUnderstoryInstances = Context.FutaleufuScannedUnderstoryInstances;

    const bool bRainforest = Spec.bHasWaterfalls;
    const bool bZambeziWoodland = Spec.RiverId == TEXT("zambezi_batoka_gorge");
    TArray<FRaftSimLandscapeCandidateCenterlinePoint> PhysicalCenterline;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, PhysicalCenterline, OutSummary))
    {
        return false;
    }
    const bool bPhysicalCorridor = Candidate.bPhysicalScaleSourceCorridor && PhysicalCenterline.Num() >= 2;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float LandscapeHalfWidth = Candidate.HorizontalSpanYCm * 0.5f;
    const float MaxBankOffset = bPhysicalCorridor
        ? FMath::Min(
              bZambeziWoodland ? 52000.0f : 18000.0f,
              LandscapeHalfWidth - 220.0f)
        : FMath::Max(ActiveRiverHalfWidth + 300.0f, LandscapeHalfWidth - 220.0f);
    auto ResolveLogicalRiverPoint =
        [&Candidate, &PhysicalCenterline, bPhysicalCorridor](float LogicalX, float LateralOffset)
    {
        if (!bPhysicalCorridor)
        {
            return FVector2D(
                LogicalX,
                GetPreviewRiverCenterY(Candidate.PreviewSpec, LogicalX) + LateralOffset);
        }
        const float Progress = FMath::Clamp((LogicalX + 2500.0f) / 27900.0f, 0.0f, 1.0f);
        FVector2D Tangent;
        const FVector2D Center = SampleLandscapeCandidateCenterlineWorld(
            Candidate,
            PhysicalCenterline,
            Progress,
            &Tangent);
        const FVector2D Normal(-Tangent.Y, Tangent.X);
        return Center + Normal * LateralOffset;
    };
    TArray<FVector2D> PhysicalCenterlineWorldPoints;
    PhysicalCenterlineWorldPoints.Reserve(PhysicalCenterline.Num());
    for (int32 PointIndex = 0;
         PointIndex < PhysicalCenterline.Num();
         ++PointIndex)
    {
        const float Progress = PhysicalCenterline.Num() > 1
            ? static_cast<float>(PointIndex) /
                static_cast<float>(PhysicalCenterline.Num() - 1)
            : 0.0f;
        PhysicalCenterlineWorldPoints.Add(
            SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                PhysicalCenterline,
                Progress));
    }
    auto GetMinimumCenterlineDistanceCm =
        [&PhysicalCenterlineWorldPoints](const FVector2D& Point)
    {
        float MinimumDistanceSquared = TNumericLimits<float>::Max();
        for (int32 SegmentIndex = 1;
             SegmentIndex < PhysicalCenterlineWorldPoints.Num();
             ++SegmentIndex)
        {
            const FVector2D Start =
                PhysicalCenterlineWorldPoints[SegmentIndex - 1];
            const FVector2D End =
                PhysicalCenterlineWorldPoints[SegmentIndex];
            const FVector2D Delta = End - Start;
            const float LengthSquared = Delta.SizeSquared();
            const float SegmentT = LengthSquared > UE_SMALL_NUMBER
                ? FMath::Clamp(
                    FVector2D::DotProduct(Point - Start, Delta) /
                        LengthSquared,
                    0.0f,
                    1.0f)
                : 0.0f;
            MinimumDistanceSquared = FMath::Min(
                MinimumDistanceSquared,
                FVector2D::DistSquared(Point, Start + Delta * SegmentT));
        }
        return FMath::Sqrt(MinimumDistanceSquared);
    };
    auto GetConditionedWaterWorldZ =
        [&Candidate, &PhysicalCenterline](float LogicalX)
    {
        const float Progress = FMath::Clamp(
            (LogicalX + 2500.0f) / 27900.0f,
            0.0f,
            1.0f);
        float SurfaceWorldZ = 0.0f;
        if (!SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                Candidate,
                PhysicalCenterline,
                Progress,
                SurfaceWorldZ))
        {
            return Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
        }
        return SurfaceWorldZ +
            Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
    };
    auto GetLandscapeHeight = [Landscape, &Spec](float X, float Y)
    {
        return Landscape->GetHeightAtLocation(FVector(X, Y, 0.0f), EHeightfieldSource::Editor)
            .Get(Spec.FlowWaterLevelOffsetCm - 24.0f);
    };
    auto GetLandscapeSlopeDegrees = [&GetLandscapeHeight](float X, float Y)
    {
        // The physical-corridor DEM is sampled at roughly 6-10 m spacing. A
        // 12 m baseline rejects cliff faces without reacting to single-vertex
        // noise or forcing woody vegetation onto the water-adjacent bank.
        constexpr float SampleRadiusCm = 1200.0f;
        const float GradientX =
            (GetLandscapeHeight(X + SampleRadiusCm, Y) -
             GetLandscapeHeight(X - SampleRadiusCm, Y)) /
            (2.0f * SampleRadiusCm);
        const float GradientY =
            (GetLandscapeHeight(X, Y + SampleRadiusCm) -
             GetLandscapeHeight(X, Y - SampleRadiusCm)) /
            (2.0f * SampleRadiusCm);
        return FMath::RadiansToDegrees(
            FMath::Atan(FMath::Sqrt(GradientX * GradientX + GradientY * GradientY)));
    };
    auto AddGroundedInstance = [](UHierarchicalInstancedStaticMeshComponent* Component,
                                  UStaticMesh* Mesh,
                                  const FVector2D& GroundLocation,
                                  float GroundZ,
                                  const FRotator& Rotation,
                                  const FVector& Scale)
    {
        const FBox Bounds = GetLandscapeCandidateEffectiveMeshBounds(Mesh);
        const float GroundedPivotZ = GroundZ - Bounds.Min.Z * Scale.Z;
        return Component->AddInstance(
            FTransform(
                Rotation,
                FVector(GroundLocation.X, GroundLocation.Y, GroundedPivotZ),
                Scale),
            true);
    };

    // The extracted callbacks must not narrow the original lambda results.
    static_assert(std::is_same_v<decltype(ResolveLogicalRiverPoint(0.f, 0.f)), FVector2D>);
    static_assert(std::is_same_v<decltype(GetMinimumCenterlineDistanceCm(FVector2D::ZeroVector)), float>);
    static_assert(std::is_same_v<decltype(GetConditionedWaterWorldZ(0.f)), float>);
    static_assert(std::is_same_v<decltype(GetLandscapeHeight(0.f, 0.f)), float>);
    static_assert(std::is_same_v<decltype(GetLandscapeSlopeDegrees(0.f, 0.f)), float>);
    static_assert(std::is_same_v<decltype(AddGroundedInstance(nullptr, nullptr, FVector2D::ZeroVector, 0.f, FRotator::ZeroRotator, FVector::OneVector)), int32>);
    const FPlacementQueries Queries{
        bPhysicalCorridor,
        bZambeziWoodland,
        ActiveRiverHalfWidth,
        ResolveLogicalRiverPoint,
        GetMinimumCenterlineDistanceCm,
        GetConditionedWaterWorldZ,
        GetLandscapeHeight,
        GetLandscapeSlopeDegrees,
        AddGroundedInstance};

    int32 RunnableLaunchTalusPlacedCount = 0;
    int32 RunnableLaunchTalusRejectedPlacementCount = 0;
    float RunnableLaunchTalusMaximumSlopeDegrees = 0.0f;
    int32 DryScarpOutcropPlacedCount = 0;
    int32 DryScarpOutcropRejectedPlacementCount = 0;
    float DryScarpOutcropMaximumSlopeDegrees = 0.0f;
    float DryScarpOutcropMinimumHeightAboveWaterCm = TNumericLimits<float>::Max();
    const int32 BoulderCount = bPhysicalCorridor
        ? 180
        : (Spec.bDesertCanyon ? 62 : (bRainforest ? 48 : 44));
    for (int32 BoulderIndex = 0; BoulderIndex < BoulderCount; ++BoulderIndex)
    {
        const float T = (static_cast<float>(BoulderIndex) + 0.5f) / static_cast<float>(BoulderCount);
        const float Phase = static_cast<float>(BoulderIndex) * 1.6180339f;
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const bool bChannelRock = BoulderIndex % 9 == 0;
        const float BaseX = FMath::Lerp(
            bPhysicalCorridor ? 5000.0f : -1600.0f,
            25500.0f,
            T) + 180.0f * FMath::Sin(Phase);
        const float BaseOffset = bChannelRock
            ? ActiveRiverHalfWidth * (0.62f + 0.24f * FMath::Abs(FMath::Sin(Phase * 0.77f)))
            : FMath::Lerp(
                  ActiveRiverHalfWidth + (bPhysicalCorridor && BaseX < 3200.0f ? 900.0f : 260.0f),
                  MaxBankOffset * 0.78f,
                  FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.43f)), 0.72f));

        const FVector2D BasePoint = ResolveLogicalRiverPoint(BaseX, Side * BaseOffset);
        float BestX = BasePoint.X;
        float BestY = BasePoint.Y;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 7; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                155.0f * FMath::Sin(Phase * 0.61f + static_cast<float>(CandidateIndex) * 1.17f);
            const float CandidateOffset = FMath::Clamp(
                BaseOffset + 135.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.93f),
                ActiveRiverHalfWidth * 0.20f,
                MaxBankOffset);
            const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                CandidateX,
                Side * CandidateOffset);
            const float CandidateWorldX = CandidatePoint.X;
            const float CandidateWorldY = CandidatePoint.Y;
            const float WaterT = bPhysicalCorridor
                ? FMath::Clamp(1.0f - CandidateOffset / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f)
                : SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateWorldX, CandidateWorldY);
            const float VegetationT = bPhysicalCorridor
                ? SmoothPreviewStep(ActiveRiverHalfWidth + 400.0f, MaxBankOffset, CandidateOffset)
                : SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateWorldX, CandidateWorldY);
            const float TargetWaterT = bChannelRock ? 0.68f : 0.20f;
            const float Score = 1.0f - FMath::Abs(WaterT - TargetWaterT) -
                VegetationT * (bChannelRock ? 0.12f : 0.34f) +
                0.06f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateWorldX;
                BestY = CandidateWorldY;
            }
        }

        const float TargetBoulderHeightCm = bPhysicalCorridor
            ? (65.0f + 18.0f * static_cast<float>(BoulderIndex % 6)) *
                (bChannelRock ? 1.05f : 1.0f)
            : (Spec.bDesertCanyon
                   ? 82.0f + 20.0f * static_cast<float>(BoulderIndex % 5)
                   : (bRainforest ? 74.0f + 18.0f * static_cast<float>(BoulderIndex % 5)
                                  : 66.0f + 16.0f * static_cast<float>(BoulderIndex % 5))) *
                (bChannelRock ? 0.72f : 1.0f);
        const float BoulderScaleZ = TargetBoulderHeightCm / 100.0f;
        if (ReviewedRockMeshes.Num() == 6 && ReviewedRockInstances.Num() == 6)
        {
            const int32 VariantIndex = BoulderIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetBoulderHeightCm / MeshHeightCm;
            AddGroundedInstance(
                ReviewedRockInstances[VariantIndex],
                RockMesh,
                FVector2D(BestX, BestY),
                GetLandscapeHeight(BestX, BestY),
                FRotator(
                    bChannelRock ? -5.0f : 2.0f * FMath::Sin(Phase),
                    static_cast<float>((BoulderIndex * 47) % 360),
                    3.0f * FMath::Cos(Phase * 0.73f)),
                FVector(
                    UniformScale * (0.92f + 0.07f * static_cast<float>(BoulderIndex % 4)),
                    UniformScale * (0.88f + 0.06f * static_cast<float>((BoulderIndex + 2) % 5)),
                    UniformScale));
        }
        else
        {
            const FLinearColor BoulderColor = FMath::Lerp(
                ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.70f : 0.52f),
                ScalePreviewColor(Spec.WaterColor, 0.28f),
                bChannelRock ? 0.24f : (bRainforest ? 0.16f : 0.10f));
            AActor* BoulderActor = AddPreviewIrregularRockActor(
                World,
                FString::Printf(TEXT("RaftSim_LandscapeCandidate_IrregularBoulder_%03d_%s"), BoulderIndex, *Spec.RiverId),
                FVector(BestX, BestY, GetLandscapeHeight(BestX, BestY)),
                static_cast<float>((BoulderIndex * 47) % 360),
                FVector(
                    BoulderScaleZ * (1.15f + 0.08f * static_cast<float>(BoulderIndex % 4)),
                    BoulderScaleZ * (0.76f + 0.07f * static_cast<float>((BoulderIndex + 2) % 5)),
                    BoulderScaleZ),
                BoulderColor,
                BoulderIndex + 42000);
            if (BoulderActor)
            {
                if (UProceduralMeshComponent* BoulderComponent =
                        BoulderActor->FindComponentByClass<UProceduralMeshComponent>())
                {
                    BoulderComponent->SetCastShadow(true);
                    BoulderComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                }
            }
        }
        ++OutResult.DressingBoulderInstanceCount;
    }

    int32 TemperateWaterlinePlacedCount = 0;
    int32 TemperateWaterlineRejectedPlacementCount = 0;
    float TemperateWaterlineMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float TemperateWaterlineMaximumSlopeDegrees = 0.0f;
    if (bOpaqueTemperate &&
        ReviewedRockMeshes.Num() == 6 &&
        TemperateWaterlineStructureInstances.Num() == 6)
    {
        // The source DEM establishes terrain and collision, while the live C++
        // water/solver owns the playable channel. This dense CC0 morphology-
        // donor layer fills only unresolved sub-DEM bank structure. Every
        // instance is grounded on the source Landscape, starts outside the
        // complete visible-water width, remains non-colliding, and carries no
        // lithology, bathymetry, hydraulic, or raft-force authority.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth *
            (bChilko ? 1.20f : 1.18f);
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            TemperateWaterlineStructureTargetInstanceCount / BankSideCount;
        for (int32 StructureIndex = 0;
             StructureIndex < TemperateWaterlineStructureTargetInstanceCount;
             ++StructureIndex)
        {
            const int32 SideIndex = StructureIndex % BankSideCount;
            const int32 AlongIndex = StructureIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(StructureIndex, 10103)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX =
                FMath::Lerp(-2380.0f, 25300.0f, AlongT) +
                95.0f * FMath::Sin(
                    static_cast<float>(StructureIndex) * 1.3247179f);

            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 420.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 72;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX +
                    FMath::Lerp(
                        -115.0f,
                        115.0f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex * 79 + CandidateIndex,
                            10111));
                const float CandidateAdditionalOffset = FMath::Lerp(
                    85.0f,
                    3200.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            StructureIndex * 83 + CandidateIndex,
                            10133),
                        1.72f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side *
                        (VisibleRiverHalfWidth + CandidateAdditionalOffset));
                const float CandidateSlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CandidateCenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float HeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (CandidateSlopeDegrees >
                        TemperateWaterlineStructureSlopeCeilingDegrees ||
                    CandidateCenterlineDistanceCm <
                        VisibleRiverHalfWidth + 60.0f ||
                    HeightAboveWaterCm < -25.0f ||
                    HeightAboveWaterCm > 2200.0f)
                {
                    continue;
                }

                const float TargetDryHeightCm = 85.0f +
                    210.0f * ZambeziVegetationUnitRandom(
                        StructureIndex,
                        10139);
                const float PlacementScore =
                    0.62f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 2200.0f +
                    0.24f * CandidateAdditionalOffset / 3200.0f +
                    0.14f * CandidateSlopeDegrees /
                        TemperateWaterlineStructureSlopeCeilingDegrees;
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = CandidateSlopeDegrees;
                    BestCenterlineDistanceCm =
                        CandidateCenterlineDistanceCm;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++TemperateWaterlineRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = StructureIndex % 20;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      160.0f,
                      260.0f,
                      ZambeziVegetationUnitRandom(StructureIndex, 10141))
                : (ScaleClass < 5
                       ? FMath::Lerp(
                             60.0f,
                             135.0f,
                             ZambeziVegetationUnitRandom(
                                 StructureIndex,
                                 10151))
                       : FMath::Lerp(
                             22.0f,
                             58.0f,
                             ZambeziVegetationUnitRandom(
                                 StructureIndex,
                                 10159)));
            const int32 VariantIndex = StructureIndex %
                ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            UHierarchicalInstancedStaticMeshComponent* StructureComponent =
                TemperateWaterlineStructureInstances[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                StructureComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.10f, 0.0f, 5.5f),
                    360.0f * ZambeziVegetationUnitRandom(
                        StructureIndex,
                        10163),
                    FMath::Lerp(
                        -5.0f,
                        5.0f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex,
                            10169))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.76f,
                        1.34f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex,
                            10177)),
                    UniformScale * FMath::Lerp(
                        0.74f,
                        1.30f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex,
                            10181)),
                    UniformScale));
            ++TemperateWaterlinePlacedCount;
            ++OutResult.DressingBoulderInstanceCount;
            TemperateWaterlineMinimumCenterlineDistanceCm = FMath::Min(
                TemperateWaterlineMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            TemperateWaterlineMaximumSlopeDegrees = FMath::Max(
                TemperateWaterlineMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             TemperateWaterlineStructureInstances)
        {
            if (Component)
            {
                Component->MarkRenderStateDirty();
            }
        }
        OutSummary += FString::Printf(
            TEXT("%s organic waterline structure V1: %d/%d source-grounded, ")
            TEXT("non-colliding CC0 rock analogs across both banks; %d targets ")
            TEXT("rejected by visible-water clearance, dry-height, or %.1f-degree ")
            TEXT("slope gates; minimum full-route centerline distance %.1f cm and ")
            TEXT("maximum placed slope %.2f degrees. Presentation-only procedural ")
            TEXT("gap fill with no lithology, hydraulic, collision, bathymetry, or ")
            TEXT("raft-force authority.\n"),
            *Spec.RiverId,
            TemperateWaterlinePlacedCount,
            TemperateWaterlineStructureTargetInstanceCount,
            TemperateWaterlineRejectedPlacementCount,
            TemperateWaterlineStructureSlopeCeilingDegrees,
            TemperateWaterlineMinimumCenterlineDistanceCm,
            TemperateWaterlineMaximumSlopeDegrees);
    }
    OutResult.DressingTemperateWaterlineTargetInstanceCount =
        bOpaqueTemperate
            ? TemperateWaterlineStructureTargetInstanceCount
            : 0;
    OutResult.DressingTemperateWaterlineInstanceCount =
        TemperateWaterlinePlacedCount;
    OutResult.DressingTemperateWaterlineRejectedPlacementCount =
        TemperateWaterlineRejectedPlacementCount;
    OutResult.DressingTemperateWaterlineMinimumCenterlineDistanceCm =
        TemperateWaterlinePlacedCount > 0
            ? TemperateWaterlineMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingTemperateWaterlineMaximumSlopeDegrees =
        TemperateWaterlineMaximumSlopeDegrees;

    int32 ChilkoShorelineGravelPlacedCount = 0;
    int32 ChilkoShorelineGravelRejectedPlacementCount = 0;
    float ChilkoShorelineGravelMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float ChilkoShorelineGravelMaximumSlopeDegrees = 0.0f;
    if (bChilko && bPhysicalCorridor &&
        ReviewedRockMeshes.Num() == 6 &&
        ChilkoOrganicShorelineGravelInstances.Num() == 6)
    {
        // Break up the broad, visibly smooth Lava Canyon shoreline benches
        // with small, irregular CC0 rock morphology donors. The conditioned
        // source Landscape remains ground/collision authority; this layer is
        // always outside the full visible-water width and cannot affect the
        // solver, bathymetry, hydraulics, or raft forces. V2 covers the entire
        // 0-600 m runnable corridor; V1 stopped before the 300 m evidence site.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth * 1.03f;
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ChilkoOrganicShorelineGravelTargetInstanceCount / BankSideCount;
        for (int32 GravelIndex = 0;
             GravelIndex < ChilkoOrganicShorelineGravelTargetInstanceCount;
             ++GravelIndex)
        {
            const int32 SideIndex = GravelIndex % BankSideCount;
            const int32 AlongIndex = GravelIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(GravelIndex, 10303)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX =
                FMath::Lerp(
                    ChilkoOrganicShorelineStartStationCm,
                    ChilkoOrganicShorelineEndStationCm,
                    AlongT) +
                72.0f * FMath::Sin(
                    static_cast<float>(GravelIndex) * 0.7548777f);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 360.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 48;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -105.0f,
                    105.0f,
                    ZambeziVegetationUnitRandom(
                        GravelIndex * 53 + CandidateIndex,
                        10313));
                const float AdditionalOffset = FMath::Lerp(
                    70.0f,
                    2400.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            GravelIndex * 59 + CandidateIndex,
                            10321),
                        1.90f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        ChilkoOrganicShorelineGravelSlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 45.0f ||
                    HeightAboveWaterCm < -5.0f ||
                    HeightAboveWaterCm > 650.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    48.0f,
                    260.0f,
                    ZambeziVegetationUnitRandom(GravelIndex, 10331));
                const float Score =
                    0.58f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 650.0f +
                    0.29f * AdditionalOffset / 2400.0f +
                    0.13f * SlopeDegrees /
                        ChilkoOrganicShorelineGravelSlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++ChilkoShorelineGravelRejectedPlacementCount;
                continue;
            }

            // Preserve a gravel/cobble-dominant bank. V2 devoted one in 36
            // instances to 0.8-1.4 m silhouettes; that produced the isolated
            // boulder-sized outlier in the matched close view. V3 makes the
            // rare class half as frequent and hard-caps it at one metre.
            const int32 ScaleClass = GravelIndex % 72;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      65.0f,
                      ChilkoOrganicShorelineGravelRareMaximumHeightCm,
                      ZambeziVegetationUnitRandom(GravelIndex, 10343))
                : (ScaleClass < 12
                       ? FMath::Lerp(
                             28.0f,
                             62.0f,
                             ZambeziVegetationUnitRandom(
                                 GravelIndex,
                                 10351))
                       : FMath::Lerp(
                             8.0f,
                             28.0f,
                             ZambeziVegetationUnitRandom(
                                 GravelIndex,
                                 10357)));
            const int32 VariantIndex = GravelIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            UHierarchicalInstancedStaticMeshComponent* GravelComponent =
                ChilkoOrganicShorelineGravelInstances[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                GravelComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.08f, 0.0f, 3.4f),
                    360.0f * ZambeziVegetationUnitRandom(
                        GravelIndex,
                        10369),
                    FMath::Lerp(
                        -4.0f,
                        4.0f,
                        ZambeziVegetationUnitRandom(
                            GravelIndex,
                            10373))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.70f,
                        1.48f,
                        ZambeziVegetationUnitRandom(
                            GravelIndex,
                            10379)),
                    UniformScale * FMath::Lerp(
                        0.72f,
                        1.44f,
                        ZambeziVegetationUnitRandom(
                            GravelIndex,
                            10391)),
                    UniformScale));
            ++ChilkoShorelineGravelPlacedCount;
            ++OutResult.DressingBoulderInstanceCount;
            ChilkoShorelineGravelMinimumCenterlineDistanceCm = FMath::Min(
                ChilkoShorelineGravelMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            ChilkoShorelineGravelMaximumSlopeDegrees = FMath::Max(
                ChilkoShorelineGravelMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGravelInstances)
        {
            Component->MarkRenderStateDirty();
        }
        OutSummary += FString::Printf(
            TEXT("%s organic shoreline gravel V3: %d/%d source-grounded, ")
            TEXT("non-colliding six-morphology cobbles across both full-route ")
            TEXT("banks; %d targets rejected by visible-water clearance, ")
            TEXT("dry-height, or %.1f-degree slope gates; minimum centerline ")
            TEXT("distance %.1f cm and maximum placed slope %.2f degrees. ")
            TEXT("Presentation-only procedural gap fill with no lithology, ")
            TEXT("collision, bathymetry, hydraulic, or raft-force authority.\n"),
            *Spec.RiverId,
            ChilkoShorelineGravelPlacedCount,
            ChilkoOrganicShorelineGravelTargetInstanceCount,
            ChilkoShorelineGravelRejectedPlacementCount,
            ChilkoOrganicShorelineGravelSlopeCeilingDegrees,
            ChilkoShorelineGravelMinimumCenterlineDistanceCm,
            ChilkoShorelineGravelMaximumSlopeDegrees);
    }
    OutResult.DressingChilkoOrganicShorelineGravelTargetInstanceCount =
        bChilko ? ChilkoOrganicShorelineGravelTargetInstanceCount : 0;
    OutResult.DressingChilkoOrganicShorelineGravelInstanceCount =
        ChilkoShorelineGravelPlacedCount;
    OutResult.DressingChilkoOrganicShorelineGravelRejectedPlacementCount =
        ChilkoShorelineGravelRejectedPlacementCount;
    OutResult.DressingChilkoOrganicShorelineGravelMinimumCenterlineDistanceCm =
        ChilkoShorelineGravelPlacedCount > 0
            ? ChilkoShorelineGravelMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingChilkoOrganicShorelineGravelMaximumSlopeDegrees =
        ChilkoShorelineGravelMaximumSlopeDegrees;

    int32 ChilkoShorelineGroundCoverPlacedCount = 0;
    int32 ChilkoShorelineGroundCoverRejectedPlacementCount = 0;
    float ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float ChilkoShorelineGroundCoverMaximumSlopeDegrees = 0.0f;
    if (bChilko && bPhysicalCorridor &&
        ChilkoOrganicShorelineGroundCoverInstances.Num() == 2)
    {
        // Short, non-shadowing meadow patches soften the transition from the
        // gravel band to the wider shrub/canopy layer. They are selected only
        // on dry, low-slope source Landscape and make no species or ecology
        // claim. V2 spans the full runnable 0-600 m corridor.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth * 1.03f;
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ChilkoOrganicShorelineGroundCoverTargetInstanceCount /
            BankSideCount;
        for (int32 CoverIndex = 0;
             CoverIndex < ChilkoOrganicShorelineGroundCoverTargetInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 10403)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX =
                FMath::Lerp(
                    ChilkoOrganicShorelineStartStationCm,
                    ChilkoOrganicShorelineEndStationCm,
                    AlongT) +
                88.0f * FMath::Sin(
                    static_cast<float>(CoverIndex) * 0.618034f);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 620.0f));
            float BestLogicalX = BaseLogicalX;
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 48;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -130.0f,
                    130.0f,
                    ZambeziVegetationUnitRandom(
                        CoverIndex * 61 + CandidateIndex,
                        10411));
                const float AdditionalOffset = FMath::Lerp(
                    120.0f,
                    4200.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            CoverIndex * 73 + CandidateIndex,
                            10427),
                        1.48f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 85.0f ||
                    HeightAboveWaterCm < 18.0f ||
                    HeightAboveWaterCm > 1100.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    125.0f,
                    650.0f,
                    ZambeziVegetationUnitRandom(CoverIndex, 10433));
                const float Score =
                    0.58f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 1100.0f +
                    0.28f * AdditionalOffset / 4200.0f +
                    0.14f * SlopeDegrees /
                        ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestLogicalX = CandidateLogicalX;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++ChilkoShorelineGroundCoverRejectedPlacementCount;
                continue;
            }

            const int32 MorphologyIndex =
                ZambeziVegetationUnitRandom(CoverIndex, 10439) > 0.48f ? 1 : 0;
            UStaticMesh* CoverMesh = MorphologyIndex == 0
                ? UnderstoryMesh
                : TemperateUnderstoryMeshB;
            UHierarchicalInstancedStaticMeshComponent* CoverComponent =
                ChilkoOrganicShorelineGroundCoverInstances[MorphologyIndex];
            const float TargetHeightCm = FMath::Lerp(
                ChilkoOrganicShorelineGroundCoverMinimumHeightCm,
                ChilkoOrganicShorelineGroundCoverMaximumHeightCm,
                ZambeziVegetationUnitRandom(CoverIndex, 10453));
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(CoverMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                CoverComponent,
                CoverMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.02f, 0.0f, 0.65f),
                    360.0f * ZambeziVegetationUnitRandom(
                        CoverIndex,
                        10457),
                    0.45f * FMath::Sin(BestLogicalX * 0.0013f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.74f,
                        1.42f,
                        ZambeziVegetationUnitRandom(
                            CoverIndex,
                            10463)),
                    UniformScale * FMath::Lerp(
                        0.76f,
                        1.38f,
                        ZambeziVegetationUnitRandom(
                            CoverIndex,
                            10477)),
                    UniformScale));
            ++ChilkoShorelineGroundCoverPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
            ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm = FMath::Min(
                ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            ChilkoShorelineGroundCoverMaximumSlopeDegrees = FMath::Max(
                ChilkoShorelineGroundCoverMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGroundCoverInstances)
        {
            Component->MarkRenderStateDirty();
        }
        OutSummary += FString::Printf(
            TEXT("%s organic shoreline ground cover V3: %d/%d short, ")
            TEXT("non-shadowing, source-grounded patches across both full-route ")
            TEXT("dry banks; %d targets rejected by visible-water clearance, ")
            TEXT("dry-height, or %.1f-degree slope gates; minimum centerline ")
            TEXT("distance %.1f cm and maximum placed slope %.2f degrees. ")
            TEXT("Presentation-only procedural gap fill with no species, ")
            TEXT("ecology, survey, hydraulic, collision, or raft-force authority.\n"),
            *Spec.RiverId,
            ChilkoShorelineGroundCoverPlacedCount,
            ChilkoOrganicShorelineGroundCoverTargetInstanceCount,
            ChilkoShorelineGroundCoverRejectedPlacementCount,
            ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees,
            ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm,
            ChilkoShorelineGroundCoverMaximumSlopeDegrees);
    }
    OutResult.DressingChilkoOrganicShorelineGroundCoverTargetInstanceCount =
        bChilko ? ChilkoOrganicShorelineGroundCoverTargetInstanceCount : 0;
    OutResult.DressingChilkoOrganicShorelineGroundCoverInstanceCount =
        ChilkoShorelineGroundCoverPlacedCount;
    OutResult.DressingChilkoOrganicShorelineGroundCoverRejectedPlacementCount =
        ChilkoShorelineGroundCoverRejectedPlacementCount;
    OutResult.DressingChilkoOrganicShorelineGroundCoverMinimumCenterlineDistanceCm =
        ChilkoShorelineGroundCoverPlacedCount > 0
            ? ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingChilkoOrganicShorelineGroundCoverMaximumSlopeDegrees =
        ChilkoShorelineGroundCoverMaximumSlopeDegrees;

    if (bZambeziWoodland &&
        ReviewedRockMeshes.Num() == 6 &&
        ZambeziRunnableLaunchTalusInstances.Num() == 6)
    {
        // The legacy physical-corridor boulder distribution starts around
        // station 5 km. Give the actually runnable first kilometre its own
        // auditable dry-bank talus layer. These generic CC0 rock analogs are
        // visual dressing only: the source Landscape remains collision and
        // height authority, and no instance may enter the active route.
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ZambeziRunnableLaunchTalusInstanceCount / BankSideCount;
        for (int32 TalusIndex = 0;
             TalusIndex < ZambeziRunnableLaunchTalusInstanceCount;
             ++TalusIndex)
        {
            const int32 SideIndex = TalusIndex % BankSideCount;
            const int32 AlongIndex = TalusIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(TalusIndex, 9403)) /
                static_cast<float>(InstancesPerSide);
            // Logical X -2390..-1580 maps to approximately 118-993 m down
            // the conditioned route, just ahead of the station-75 m launch.
            const float BaseLogicalX = FMath::Lerp(-2390.0f, -1580.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + 1800.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            float BestLogicalX = BaseLogicalX;
            for (int32 CandidateIndex = 0; CandidateIndex < 128; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(TalusIndex) * 0.7548777f +
                    static_cast<float>(CandidateIndex) * 1.3247179f;
                const float CandidateLogicalX = BaseLogicalX +
                    32.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    600.0f,
                    14000.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            TalusIndex * 131 + CandidateIndex,
                            9419),
                        1.55f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (ActiveRiverHalfWidth + CandidateAdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                if (SlopeDegrees >
                        ZambeziRunnableLaunchTalusSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 100.0f ||
                    DryHeightAboveWaterCm > 16000.0f ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 300.0f)
                {
                    continue;
                }
                const float PlacementScore =
                    0.08f * FMath::Abs(SlopeDegrees - 18.0f) +
                    0.35f * CandidateAdditionalOffset / 14000.0f +
                    0.15f * FMath::Abs(DryHeightAboveWaterCm - 2800.0f) /
                        16000.0f;
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestLogicalX = CandidateLogicalX;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchTalusRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = TalusIndex % 20;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      380.0f,
                      520.0f,
                      ZambeziVegetationUnitRandom(TalusIndex, 9431))
                : (ScaleClass < 5
                       ? FMath::Lerp(
                             220.0f,
                             360.0f,
                             ZambeziVegetationUnitRandom(TalusIndex, 9433))
                       : FMath::Lerp(
                             95.0f,
                             220.0f,
                             ZambeziVegetationUnitRandom(TalusIndex, 9437)));
            const int32 VariantIndex = TalusIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            UHierarchicalInstancedStaticMeshComponent* TalusComponent =
                ZambeziRunnableLaunchTalusInstances[VariantIndex];
            const int32 InstanceIndex = AddGroundedInstance(
                TalusComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.16f, 0.0f, 7.5f),
                    360.0f * ZambeziVegetationUnitRandom(TalusIndex, 9461),
                    FMath::Lerp(
                        -6.0f,
                        6.0f,
                        ZambeziVegetationUnitRandom(TalusIndex, 9473))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.28f,
                        ZambeziVegetationUnitRandom(TalusIndex, 9491)),
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.22f,
                        ZambeziVegetationUnitRandom(TalusIndex, 9497)),
                    UniformScale));
            TalusComponent->SetCustomDataValue(
                InstanceIndex,
                0,
                GetConditionedWaterWorldZ(BestLogicalX),
                false);
            ++RunnableLaunchTalusPlacedCount;
            RunnableLaunchTalusMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchTalusMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++OutResult.DressingBoulderInstanceCount;
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ZambeziRunnableLaunchTalusInstances)
        {
            if (Component)
            {
                Component->MarkRenderStateDirty();
            }
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi runnable-launch talus: %d/%d source-grounded, "
                 "non-colliding generic rock analogs across both dry banks, each "
                 "with a conditioned-profile waterline in custom-data channel zero; "
                 "%d targets rejected by full-route distance, dry-height, or "
                 "%.1f-degree slope gates; maximum placed slope %.2f degrees. "
                 "Presentation-only with no Batoka lithology or hydraulic authority.\n"),
            RunnableLaunchTalusPlacedCount,
            ZambeziRunnableLaunchTalusInstanceCount,
            RunnableLaunchTalusRejectedPlacementCount,
            ZambeziRunnableLaunchTalusSlopeCeilingDegrees,
            RunnableLaunchTalusMaximumSlopeDegrees);
    }
    OutResult.DressingRunnableLaunchTalusTargetInstanceCount =
        bZambeziWoodland ? ZambeziRunnableLaunchTalusInstanceCount : 0;
    OutResult.DressingRunnableLaunchTalusInstanceCount =
        RunnableLaunchTalusPlacedCount;
    OutResult.DressingRunnableLaunchTalusRejectedPlacementCount =
        RunnableLaunchTalusRejectedPlacementCount;
    OutResult.DressingRunnableLaunchTalusMaximumSlopeDegrees =
        RunnableLaunchTalusMaximumSlopeDegrees;

    if (bZambeziWoodland &&
        ReviewedRockMeshes.Num() == 6 &&
        ZambeziDryScarpOutcropInstances.Num() == 6)
    {
        // The source DEM does not resolve the individual ledges and detached
        // blocks needed to read the launch wall at guide-eye distance. Place a
        // separately auditable, non-colliding CC0 analog layer only on dry
        // source-grounded scarps. It has no lithology, collision, hydraulic, or
        // navigation authority and never enters the active channel.
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ZambeziDryScarpOutcropInstanceCount / BankSideCount;
        for (int32 OutcropIndex = 0;
             OutcropIndex < ZambeziDryScarpOutcropInstanceCount;
             ++OutcropIndex)
        {
            const int32 SideIndex = OutcropIndex % BankSideCount;
            const int32 AlongIndex = OutcropIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(OutcropIndex, 10103)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2400.0f, -1550.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + 4500.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestDryHeightAboveWaterCm = 0.0f;
            float BestPlacementScore = TNumericLimits<float>::Max();
            float BestLogicalX = BaseLogicalX;
            for (int32 CandidateIndex = 0; CandidateIndex < 96; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(OutcropIndex) * 0.6180339f +
                    static_cast<float>(CandidateIndex) * 1.2207441f;
                const float CandidateLogicalX =
                    BaseLogicalX + 42.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    4500.0f,
                    22000.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            OutcropIndex * 137 + CandidateIndex,
                            10111),
                        1.18f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (ActiveRiverHalfWidth + CandidateAdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                if (SlopeDegrees < 6.0f ||
                    SlopeDegrees > ZambeziDryScarpOutcropSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziDryScarpOutcropMinimumHeightAboveWaterCm ||
                    DryHeightAboveWaterCm > 12000.0f ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 3200.0f)
                {
                    continue;
                }
                const float PlacementScore =
                    0.11f * FMath::Abs(SlopeDegrees - 26.0f) +
                    0.22f * CandidateAdditionalOffset / 22000.0f +
                    0.18f * FMath::Abs(DryHeightAboveWaterCm - 4200.0f) /
                        12000.0f;
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestDryHeightAboveWaterCm = DryHeightAboveWaterCm;
                    BestLogicalX = CandidateLogicalX;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++DryScarpOutcropRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = OutcropIndex % 12;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      650.0f,
                      850.0f,
                      ZambeziVegetationUnitRandom(OutcropIndex, 10141))
                : (ScaleClass < 4
                       ? FMath::Lerp(
                             420.0f,
                             650.0f,
                             ZambeziVegetationUnitRandom(OutcropIndex, 10151))
                       : FMath::Lerp(
                             220.0f,
                             420.0f,
                             ZambeziVegetationUnitRandom(OutcropIndex, 10159)));
            const int32 VariantIndex = OutcropIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            UHierarchicalInstancedStaticMeshComponent* OutcropComponent =
                ZambeziDryScarpOutcropInstances[VariantIndex];
            if (!OutcropComponent)
            {
                ++DryScarpOutcropRejectedPlacementCount;
                continue;
            }
            const int32 InstanceIndex = AddGroundedInstance(
                OutcropComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.06f, 0.0f, 3.0f),
                    360.0f * ZambeziVegetationUnitRandom(OutcropIndex, 10163),
                    FMath::Lerp(
                        -3.0f,
                        3.0f,
                        ZambeziVegetationUnitRandom(OutcropIndex, 10169))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.88f,
                        1.28f,
                        ZambeziVegetationUnitRandom(OutcropIndex, 10177)),
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.18f,
                        ZambeziVegetationUnitRandom(OutcropIndex, 10181)),
                    UniformScale));
            OutcropComponent->SetCustomDataValue(
                InstanceIndex,
                0,
                GetConditionedWaterWorldZ(BestLogicalX),
                false);
            ++DryScarpOutcropPlacedCount;
            DryScarpOutcropMaximumSlopeDegrees = FMath::Max(
                DryScarpOutcropMaximumSlopeDegrees,
                BestSlopeDegrees);
            DryScarpOutcropMinimumHeightAboveWaterCm = FMath::Min(
                DryScarpOutcropMinimumHeightAboveWaterCm,
                BestDryHeightAboveWaterCm);
            ++OutResult.DressingBoulderInstanceCount;
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ZambeziDryScarpOutcropInstances)
        {
            if (Component)
            {
                Component->MarkRenderStateDirty();
            }
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi V20 dry-scarp outcrops: %d/%d source-grounded, "
                 "non-shadow-casting, non-colliding generic rock analogs; %d rejected "
                 "by route, 6 m dry-height, or %.1f-degree slope gates; minimum "
                 "dry height %.2f m and maximum placed slope %.2f degrees. "
                 "Presentation-only with no Batoka lithology or hydraulic authority.\n"),
            DryScarpOutcropPlacedCount,
            ZambeziDryScarpOutcropInstanceCount,
            DryScarpOutcropRejectedPlacementCount,
            ZambeziDryScarpOutcropSlopeCeilingDegrees,
            DryScarpOutcropMinimumHeightAboveWaterCm / 100.0f,
            DryScarpOutcropMaximumSlopeDegrees);
    }

    const int32 FoliageClusterCount = bColoradoHance
        ? 0
        : bPhysicalCorridor
        ? (bZambeziWoodland
               ? 5600
               : (bOpaqueTemperate ? 6200 : (Spec.bDesertCanyon ? 800 : 12000)))
        : (Spec.bDesertCanyon ? 110 : (bRainforest ? 420 : 260));
    for (int32 ClusterIndex = 0; ClusterIndex < FoliageClusterCount; ++ClusterIndex)
    {
        const float T = (static_cast<float>(ClusterIndex) + 0.5f) /
            static_cast<float>(FoliageClusterCount);
        const float Phase = static_cast<float>(ClusterIndex) * 1.3247179f;
        const float Side = (ClusterIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(
            bZambeziWoodland ? 4500.0f : -2500.0f,
            25400.0f,
            T) + 230.0f * FMath::Sin(Phase * 0.71f);
        const float BaseOffset = FMath::Lerp(
            ActiveRiverHalfWidth +
                (bZambeziWoodland ? 2600.0f : (Spec.bDesertCanyon ? 260.0f : 180.0f)),
            MaxBankOffset,
            FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.47f)), bRainforest ? 0.42f : 0.66f));

        const FVector2D BasePoint = ResolveLogicalRiverPoint(BaseX, Side * BaseOffset);
        float BestX = BasePoint.X;
        float BestY = BasePoint.Y;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 8; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.07f);
            const float NearCameraMinimumOffset = CandidateX < 2600.0f
                ? ActiveRiverHalfWidth +
                    (bZambeziWoodland
                         ? 5200.0f
                         : (bRainforest ? 860.0f : (Spec.bDesertCanyon ? 720.0f : 660.0f)))
                : ActiveRiverHalfWidth + (bZambeziWoodland ? 2600.0f : 120.0f);
            const float SearchPhase =
                Phase * 0.69f + static_cast<float>(CandidateIndex) * 0.89f;
            const float CandidateOffset = bZambeziWoodland
                ? FMath::Lerp(
                      NearCameraMinimumOffset,
                      MaxBankOffset,
                      0.08f + 0.92f * FMath::Abs(FMath::Sin(SearchPhase)))
                : FMath::Clamp(
                      BaseOffset + 210.0f * FMath::Sin(SearchPhase),
                      NearCameraMinimumOffset,
                      MaxBankOffset);
            const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                CandidateX,
                Side * CandidateOffset);
            const float CandidateWorldX = CandidatePoint.X;
            const float CandidateWorldY = CandidatePoint.Y;
            const float WaterT = bPhysicalCorridor
                ? FMath::Clamp(1.0f - CandidateOffset / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f)
                : SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateWorldX, CandidateWorldY);
            const float VegetationT = bPhysicalCorridor
                ? SmoothPreviewStep(ActiveRiverHalfWidth + 500.0f, MaxBankOffset, CandidateOffset)
                : SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateWorldX, CandidateWorldY);
            const float SlopeDegrees =
                (bZambeziWoodland || bOpaqueTemperate || bPacuare)
                ? GetLandscapeSlopeDegrees(CandidateWorldX, CandidateWorldY)
                : 0.0f;
            const float SteepSlopePenalty = bZambeziWoodland
                ? 3.2f * SmoothPreviewStep(10.0f, 24.0f, SlopeDegrees)
                : bPacuare
                ? 2.2f * SmoothPreviewStep(24.0f, 42.0f, SlopeDegrees)
                : bOpaqueTemperate
                ? 2.5f * SmoothPreviewStep(18.0f, 34.0f, SlopeDegrees)
                : 0.0f;
            const float Score = VegetationT *
                    (bRainforest ? 1.85f : (bZambeziWoodland ? 1.22f : (Spec.bDesertCanyon ? 0.58f : 1.34f))) -
                WaterT * 1.18f +
                ((bZambeziWoodland || bOpaqueTemperate || bPacuare)
                     ? 0.65f * (1.0f - FMath::Clamp(SlopeDegrees / 18.0f, 0.0f, 1.0f))
                     : 0.0f) -
                SteepSlopePenalty +
                0.07f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.83f);
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateWorldX;
                BestY = CandidateWorldY;
            }
        }

        UStaticMesh* SpeciesMesh = UnderstoryMesh;
        UHierarchicalInstancedStaticMeshComponent* SpeciesInstances = UnderstoryInstances;
        bool bCanopyTree = false;
        float TargetHeightCm = 100.0f;
        const bool bNearEvidenceCamera = !bPhysicalCorridor && BaseX < 3800.0f;
        if (bNearEvidenceCamera && !Spec.bDesertCanyon)
        {
            if (ClusterIndex % 2 == 0)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = bRainforest
                    ? 220.0f + 28.0f * static_cast<float>(ClusterIndex % 5)
                    : 185.0f + 24.0f * static_cast<float>(ClusterIndex % 5);
            }
            else
            {
                TargetHeightCm = bRainforest
                    ? 128.0f + 18.0f * static_cast<float>(ClusterIndex % 5)
                    : 104.0f + 15.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bZambeziWoodland)
        {
            const int32 SpeciesSelector = ClusterIndex % 8;
            if (SpeciesSelector <= 4)
            {
                const bool bUmbrellaTree = ClusterIndex % 2 != 0;
                SpeciesMesh = bUmbrellaTree
                    ? ConiferTreeMesh
                    : BroadleafTreeMesh;
                SpeciesInstances = bUmbrellaTree
                    ? ConiferTreeInstances
                    : BroadleafTreeInstances;
                TargetHeightCm = 720.0f + 72.0f * static_cast<float>(ClusterIndex % 7);
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 6)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 190.0f + 28.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 96.0f + 15.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (Spec.bDesertCanyon)
        {
            if (ClusterIndex % 3 == 0)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 165.0f + 24.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 88.0f + 13.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bOpaqueTemperate)
        {
            // Each 20-instance block retains the exact biome ratio, but a
            // coprime permutation and block-specific rotation prevent the
            // former conifer/broadleaf/shrub stripes from repeating downriver.
            constexpr int32 TemperateSpeciesBlockSize = 20;
            constexpr int32 TemperateSpeciesPermutation = 7;
            const int32 TemperateBlockIndex =
                ClusterIndex / TemperateSpeciesBlockSize;
            const int32 TemperateBlockOffset = FMath::Clamp(
                FMath::FloorToInt(
                    ZambeziVegetationUnitRandom(
                        TemperateBlockIndex,
                        bChilko ? 8971 : 8963) *
                    static_cast<float>(TemperateSpeciesBlockSize)),
                0,
                TemperateSpeciesBlockSize - 1);
            const int32 SpeciesSelector =
                ((ClusterIndex % TemperateSpeciesBlockSize) *
                     TemperateSpeciesPermutation +
                 TemperateBlockOffset) %
                TemperateSpeciesBlockSize;
            const int32 ConiferLimit = bChilko ? 12 : 8;
            const int32 BroadleafLimit = bChilko ? 15 : 15;
            const bool bUseSecondaryMorphology =
                ZambeziVegetationUnitRandom(ClusterIndex, 8989) > 0.48f;
            if (SpeciesSelector < ConiferLimit)
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateConiferTreeMeshB
                    : ConiferTreeMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateConiferTreeInstancesB
                    : ConiferTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    bChilko ? 1040.0f : 920.0f,
                    bChilko ? 1640.0f : 1490.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 8999));
                bCanopyTree = true;
            }
            else if (SpeciesSelector < BroadleafLimit)
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateBroadleafTreeMeshB
                    : BroadleafTreeMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateBroadleafTreeInstancesB
                    : BroadleafTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    bChilko ? 720.0f : 880.0f,
                    bChilko ? 1180.0f : 1370.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9001));
                bCanopyTree = true;
            }
            else if (SpeciesSelector < 18)
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateShrubMeshB
                    : ShrubMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateShrubInstancesB
                    : ShrubInstances;
                TargetHeightCm = 205.0f +
                    28.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateUnderstoryMeshB
                    : UnderstoryMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateUnderstoryInstancesB
                    : UnderstoryInstances;
                TargetHeightCm = 92.0f +
                    14.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bRainforest)
        {
            const int32 SpeciesSelector = FMath::Clamp(
                FMath::FloorToInt(
                    ZambeziVegetationUnitRandom(ClusterIndex, 9041) * 10.0f),
                0,
                9);
            if (SpeciesSelector <= 2)
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    880.0f,
                    1460.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9059));
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 4)
            {
                SpeciesMesh = ConiferTreeMesh;
                SpeciesInstances = ConiferTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    1020.0f,
                    1680.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9067));
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 7)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = FMath::Lerp(
                    175.0f,
                    390.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9091));
            }
            else
            {
                TargetHeightCm = FMath::Lerp(
                    68.0f,
                    168.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9103));
            }
        }
        else
        {
            const int32 SpeciesSelector = ClusterIndex % (bPhysicalCorridor ? 20 : 5);
            if (bPhysicalCorridor && SpeciesSelector == 0 &&
                ReviewedPineMeshes.Num() == 3 && ReviewedPineInstances.Num() == 3)
            {
                const int32 PineVariant = (ClusterIndex / 20) % ReviewedPineMeshes.Num();
                SpeciesMesh = ReviewedPineMeshes[PineVariant];
                SpeciesInstances = ReviewedPineInstances[PineVariant];
                TargetHeightCm = 1350.0f + 95.0f * static_cast<float>((ClusterIndex / 20) % 6);
                bCanopyTree = true;
            }
            else if (!bPhysicalCorridor && SpeciesSelector == 0)
            {
                SpeciesMesh = ConiferTreeMesh;
                SpeciesInstances = ConiferTreeInstances;
                TargetHeightCm = 940.0f + 92.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
            else if (SpeciesSelector == (bPhysicalCorridor ? 19 : 4))
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 225.0f + 32.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = 690.0f + 68.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
        }

        const float MeshHeightCm = FMath::Max(
            1.0f,
            GetLandscapeCandidateEffectiveMeshBounds(SpeciesMesh).GetSize().Z);
        const float UniformScale = TargetHeightCm / MeshHeightCm;
        const FVector SpeciesScale(
            UniformScale * FMath::Lerp(
                bRainforest ? 0.72f : (bOpaqueTemperate ? 0.76f : 0.88f),
                bRainforest ? 1.18f : (bOpaqueTemperate ? 1.16f : 1.04f),
                ZambeziVegetationUnitRandom(ClusterIndex, 9133)),
            UniformScale * FMath::Lerp(
                bRainforest ? 0.74f : (bOpaqueTemperate ? 0.78f : 0.90f),
                bRainforest ? 1.16f : (bOpaqueTemperate ? 1.14f : 1.04f),
                ZambeziVegetationUnitRandom(ClusterIndex, 9151)),
            UniformScale);
        AddGroundedInstance(
            SpeciesInstances,
            SpeciesMesh,
            FVector2D(BestX, BestY),
            GetLandscapeHeight(BestX, BestY),
            FRotator(
                1.4f * FMath::Sin(Phase * 0.73f),
                bOpaqueTemperate
                    ? 360.0f * ZambeziVegetationUnitRandom(ClusterIndex, 9161)
                    : static_cast<float>((ClusterIndex * 137) % 360),
                1.2f * FMath::Cos(Phase * 0.61f)),
            SpeciesScale);
        ++OutResult.DressingFoliageInstanceCount;
        if (bCanopyTree)
        {
            ++OutResult.DressingCanopyTreeInstanceCount;
        }
        else
        {
            ++OutResult.DressingUnderstoryInstanceCount;
        }
    }

    const FPacuarePlacementCounts PacuareCounts = AddPacuarePlacements(Context, Queries);
    const int32 PacuareShorelineRockPlacedCount = PacuareCounts.PacuareShorelineRockPlacedCount;
    const int32 PacuareShorelineGroundCoverPlacedCount = PacuareCounts.PacuareShorelineGroundCoverPlacedCount;
    const int32 PacuareScannedFernPlacedCount = PacuareCounts.PacuareScannedFernPlacedCount;
    const int32 PacuareShorelineShrubPlacedCount = PacuareCounts.PacuareShorelineShrubPlacedCount;
    const int32 PacuareForestFloorLeafLitterPlacedCount = PacuareCounts.PacuareForestFloorLeafLitterPlacedCount;
    const int32 PacuareForestFloorWoodyPlacedCount = PacuareCounts.PacuareForestFloorWoodyPlacedCount;

    int32 TemperateNearBankPlacedCount = 0;
    int32 FutaleufuScannedUnderstoryPlacedCount = 0;
    int32 TemperateNearBankRejectedPlacementCount = 0;
    float TemperateNearBankMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float TemperateNearBankMaximumSlopeDegrees = 0.0f;
    if (bOpaqueTemperate && bPhysicalCorridor)
    {
        // Fill the visibly bare strip between waterline rocks and the wider
        // canopy. Every patch is selected against the source Landscape and
        // full centerline, is dry at the conditioned reference surface, and
        // remains a non-colliding presentation layer.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth *
            (bChilko ? 1.20f : 1.18f);
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            TemperateNearBankEcologyTargetInstanceCount / BankSideCount;
        const TArray<UStaticMesh*> NearBankMeshes = {
            UnderstoryMesh,
            TemperateUnderstoryMeshB,
            ShrubMesh,
            TemperateShrubMeshB};
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            NearBankComponents = {
                UnderstoryInstances,
                TemperateUnderstoryInstancesB,
                ShrubInstances,
                TemperateShrubInstancesB};
        for (int32 PatchIndex = 0;
             PatchIndex < TemperateNearBankEcologyTargetInstanceCount;
             ++PatchIndex)
        {
            const int32 SideIndex = PatchIndex % BankSideCount;
            const int32 AlongIndex = PatchIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(PatchIndex, 10211)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2380.0f, 25300.0f, AlongT);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 620.0f));
            float BestLogicalX = BaseLogicalX;
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 64;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -150.0f,
                    150.0f,
                    ZambeziVegetationUnitRandom(
                        PatchIndex * 67 + CandidateIndex,
                        10223));
                const float AdditionalOffset = FMath::Lerp(
                    140.0f,
                    3600.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            PatchIndex * 71 + CandidateIndex,
                            10243),
                        1.55f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees > TemperateNearBankEcologySlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 100.0f ||
                    HeightAboveWaterCm < 15.0f ||
                    HeightAboveWaterCm > 1600.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    110.0f,
                    620.0f,
                    ZambeziVegetationUnitRandom(PatchIndex, 10247));
                const float Score =
                    0.60f * FMath::Abs(HeightAboveWaterCm - TargetDryHeightCm) /
                        1600.0f +
                    0.25f * AdditionalOffset / 3600.0f +
                    0.15f * SlopeDegrees /
                        TemperateNearBankEcologySlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestLogicalX = CandidateLogicalX;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++TemperateNearBankRejectedPlacementCount;
                continue;
            }

            const bool bUseScannedUnderstory = bFutaleufu && PatchIndex % 5 != 0;
            UStaticMesh* PatchMesh = nullptr;
            UHierarchicalInstancedStaticMeshComponent* PatchComponent = nullptr;
            float TargetHeightCm = 0.0f;
            if (bUseScannedUnderstory)
            {
                const int32 ScannedIndex = FMath::Min(
                    FutaleufuScannedUnderstoryMeshes.Num() - 1,
                    FMath::FloorToInt(
                        ZambeziVegetationUnitRandom(PatchIndex, 10253) *
                        FutaleufuScannedUnderstoryMeshes.Num()));
                PatchMesh = FutaleufuScannedUnderstoryMeshes[ScannedIndex];
                PatchComponent =
                    FutaleufuScannedUnderstoryInstances[ScannedIndex];
                TargetHeightCm = ScannedIndex < 3
                    ? FMath::Lerp(
                          75.0f,
                          165.0f,
                          ZambeziVegetationUnitRandom(PatchIndex, 10259))
                    : FMath::Lerp(
                          28.0f,
                          70.0f,
                          ZambeziVegetationUnitRandom(PatchIndex, 10267));
            }
            else
            {
                const bool bShrubPatch = PatchIndex % 6 == 0;
                const bool bSecondaryMorphology =
                    ZambeziVegetationUnitRandom(PatchIndex, 10253) > 0.47f;
                const int32 FamilyIndex =
                    (bShrubPatch ? 2 : 0) + (bSecondaryMorphology ? 1 : 0);
                PatchMesh = NearBankMeshes[FamilyIndex];
                PatchComponent = NearBankComponents[FamilyIndex];
                TargetHeightCm = bShrubPatch
                    ? FMath::Lerp(
                          155.0f,
                          295.0f,
                          ZambeziVegetationUnitRandom(PatchIndex, 10259))
                    : FMath::Lerp(
                          58.0f,
                          138.0f,
                          ZambeziVegetationUnitRandom(PatchIndex, 10267));
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(PatchMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                PatchComponent,
                PatchMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.025f, 0.0f, 0.9f),
                    360.0f * ZambeziVegetationUnitRandom(PatchIndex, 10273),
                    0.6f * FMath::Sin(BestLogicalX * 0.001f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.76f,
                        1.28f,
                        ZambeziVegetationUnitRandom(PatchIndex, 10289)),
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.24f,
                        ZambeziVegetationUnitRandom(PatchIndex, 10291)),
                    UniformScale));
            ++TemperateNearBankPlacedCount;
            FutaleufuScannedUnderstoryPlacedCount +=
                bUseScannedUnderstory ? 1 : 0;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
            TemperateNearBankMinimumCenterlineDistanceCm = FMath::Min(
                TemperateNearBankMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            TemperateNearBankMaximumSlopeDegrees = FMath::Max(
                TemperateNearBankMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             NearBankComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimTemperateNearBankEcologyV4"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimTemperateNearBankEcologyV4"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->MarkRenderStateDirty();
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             FutaleufuScannedUnderstoryInstances)
        {
            Component->MarkRenderStateDirty();
        }
        OutSummary += FString::Printf(
            TEXT("%s near-bank ecology V5: %d/%d source-grounded, dry, ")
            TEXT("non-colliding patches (%d rights-reviewed CC0 scanned small-fir ")
            TEXT("or fern analogs); %d targets rejected ")
            TEXT("by full-route clearance, dry-height, or %.1f-degree slope ")
            TEXT("gates; minimum centerline distance %.1f cm and maximum placed ")
            TEXT("slope %.2f degrees. Procedural gap fill with no species, ")
            TEXT("survey, collision, hydraulic, or raft-force authority.\n"),
            *Spec.RiverId,
            TemperateNearBankPlacedCount,
            TemperateNearBankEcologyTargetInstanceCount,
            FutaleufuScannedUnderstoryPlacedCount,
            TemperateNearBankRejectedPlacementCount,
            TemperateNearBankEcologySlopeCeilingDegrees,
            TemperateNearBankMinimumCenterlineDistanceCm,
            TemperateNearBankMaximumSlopeDegrees);
    }
    OutResult.DressingTemperateNearBankTargetInstanceCount =
        bOpaqueTemperate ? TemperateNearBankEcologyTargetInstanceCount : 0;
    OutResult.DressingTemperateNearBankInstanceCount =
        TemperateNearBankPlacedCount;
    OutResult.DressingFutaleufuScannedUnderstoryInstanceCount =
        FutaleufuScannedUnderstoryPlacedCount;
    OutResult.DressingTemperateNearBankRejectedPlacementCount =
        TemperateNearBankRejectedPlacementCount;
    OutResult.DressingTemperateNearBankMinimumCenterlineDistanceCm =
        TemperateNearBankPlacedCount > 0
            ? TemperateNearBankMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingTemperateNearBankMaximumSlopeDegrees =
        TemperateNearBankMaximumSlopeDegrees;

    int32 HanceDrylandGroundCoverPlacedCount = 0;
    int32 HanceDrylandGroundCoverRejectedCount = 0;
    int32 HanceDrylandShrubPlacedCount = 0;
    int32 HanceDrylandShrubRejectedCount = 0;
    float HanceDrylandMaximumSlopeDegrees = 0.0f;
    if (bColoradoHance && bPhysicalCorridor)
    {
        // The interpreted C3 channel is complete only to lateral +/-39 m.
        // Populate the procedural outer canyon, never the solver strip, with
        // countable opaque dryland patches. Candidate searches prefer lower
        // slopes and enforce dry-height limits so no instance can bridge the
        // water edge or paste across a cliff face.
        constexpr int32 BankSideCount = 2;
        const int32 GroundCoverPerSide =
            HanceDrylandGroundCoverInstanceCount / BankSideCount;
        for (int32 CoverIndex = 0;
             CoverIndex < HanceDrylandGroundCoverInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 10103)) /
                static_cast<float>(GroundCoverPerSide);
            const float BaseLogicalX = FMath::Lerp(-2300.0f, 25200.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float PreferredOffset = FMath::Lerp(
                4300.0f,
                15100.0f,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 10107),
                    1.12f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * PreferredOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 36; ++CandidateIndex)
            {
                const int32 RandomIndex = CoverIndex * 43 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    125.0f * FMath::Sin(
                        CoverIndex * 0.7548777f + CandidateIndex * 1.2207441f);
                const float CandidateOffset = FMath::Lerp(
                    4300.0f,
                    15100.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(RandomIndex, 10111),
                        1.34f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        HanceDrylandGroundCoverSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 90.0f ||
                    DryHeightAboveWaterCm > 7600.0f)
                {
                    continue;
                }
                const float Score =
                    0.040f * SlopeDegrees +
                    FMath::Abs(CandidateOffset - PreferredOffset) / 1300.0f +
                    0.11f * ZambeziVegetationUnitRandom(
                        RandomIndex,
                        10129);
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++HanceDrylandGroundCoverRejectedCount;
                continue;
            }

            const int32 VariantIndex = (CoverIndex / BankSideCount) % 2;
            UStaticMesh* GroundCoverMesh = VariantIndex == 0
                ? HanceDrylandGroundCoverMeshA
                : HanceDrylandGroundCoverMeshB;
            UHierarchicalInstancedStaticMeshComponent* GroundCoverInstances =
                VariantIndex == 0
                    ? HanceDrylandGroundCoverInstancesA
                    : HanceDrylandGroundCoverInstancesB;
            const float GroundCoverMeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    GroundCoverMesh).GetSize().Z);
            const float TargetHeightCm = FMath::Lerp(
                32.0f,
                78.0f,
                ZambeziVegetationUnitRandom(CoverIndex, 10133));
            const float UniformScale = TargetHeightCm / GroundCoverMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.05f,
                1.82f,
                ZambeziVegetationUnitRandom(CoverIndex, 10151));
            AddGroundedInstance(
                GroundCoverInstances,
                GroundCoverMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.05f, 0.0f, 1.5f),
                    360.0f * ZambeziVegetationUnitRandom(CoverIndex, 10159),
                    0.8f * FMath::Sin(CoverIndex * 0.91f)),
                FVector(
                    UniformScale * FootprintScale,
                    UniformScale * FootprintScale * FMath::Lerp(
                        0.80f,
                        1.20f,
                        ZambeziVegetationUnitRandom(CoverIndex, 10177)),
                    UniformScale));
            HanceDrylandMaximumSlopeDegrees = FMath::Max(
                HanceDrylandMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++HanceDrylandGroundCoverPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }

        constexpr int32 ShrubSpeciesLaneCount = BankSideCount;
        const int32 ShrubsPerSide =
            HanceDrylandShrubInstanceCount / ShrubSpeciesLaneCount;
        for (int32 ShrubIndex = 0;
             ShrubIndex < HanceDrylandShrubInstanceCount;
             ++ShrubIndex)
        {
            const int32 SideIndex = ShrubIndex % BankSideCount;
            const int32 AlongIndex = ShrubIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(ShrubIndex, 10201)) /
                static_cast<float>(ShrubsPerSide);
            const float BaseLogicalX = FMath::Lerp(-2200.0f, 25100.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float PreferredOffset = FMath::Lerp(
                4700.0f,
                14900.0f,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(ShrubIndex, 10207),
                    0.92f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * PreferredOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 64; ++CandidateIndex)
            {
                const int32 RandomIndex = ShrubIndex * 71 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    155.0f * FMath::Sin(
                        ShrubIndex * 0.6180339f + CandidateIndex * 1.3247179f);
                const float CandidateOffset = FMath::Lerp(
                    4700.0f,
                    14900.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(RandomIndex, 10211),
                        1.18f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees > HanceDrylandShrubSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 150.0f ||
                    DryHeightAboveWaterCm > 7200.0f)
                {
                    continue;
                }
                const float Score =
                    0.055f * SlopeDegrees +
                    FMath::Abs(CandidateOffset - PreferredOffset) / 1450.0f +
                    0.13f * ZambeziVegetationUnitRandom(
                        RandomIndex,
                        10231);
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++HanceDrylandShrubRejectedCount;
                continue;
            }

            const int32 VariantIndex = (ShrubIndex / BankSideCount) % 2;
            UStaticMesh* HanceShrubMesh = VariantIndex == 0
                ? HanceDrylandShrubMeshA
                : HanceDrylandShrubMeshB;
            UHierarchicalInstancedStaticMeshComponent* HanceShrubInstances =
                VariantIndex == 0
                    ? HanceDrylandShrubInstancesA
                    : HanceDrylandShrubInstancesB;
            const float ShrubMeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    HanceShrubMesh).GetSize().Z);
            const float TargetHeightCm = FMath::Lerp(
                78.0f,
                195.0f,
                ZambeziVegetationUnitRandom(ShrubIndex, 10243));
            const float UniformScale = TargetHeightCm / ShrubMeshHeightCm;
            AddGroundedInstance(
                HanceShrubInstances,
                HanceShrubMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.04f, 0.0f, 1.2f),
                    360.0f * ZambeziVegetationUnitRandom(ShrubIndex, 10259),
                    0.9f * FMath::Sin(ShrubIndex * 0.73f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.22f,
                        ZambeziVegetationUnitRandom(ShrubIndex, 10267)),
                    UniformScale * FMath::Lerp(
                        0.80f,
                        1.20f,
                        ZambeziVegetationUnitRandom(ShrubIndex, 10271)),
                    UniformScale));
            HanceDrylandMaximumSlopeDegrees = FMath::Max(
                HanceDrylandMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++HanceDrylandShrubPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }
        OutSummary += FString::Printf(
            TEXT("Colorado Hance dryland ecology: %d/%d opaque ground-cover "
                 "patches and %d/%d opaque shrubs grounded outside the protected "
                 "+/-39 m solver strip; %d/%d targets rejected by dry-height or "
                 "%.1f/%.1f-degree slope gates; maximum selected slope %.2f "
                 "degrees. Procedural visual gap fill only.\n"),
            HanceDrylandGroundCoverPlacedCount,
            HanceDrylandGroundCoverInstanceCount,
            HanceDrylandShrubPlacedCount,
            HanceDrylandShrubInstanceCount,
            HanceDrylandGroundCoverRejectedCount,
            HanceDrylandShrubRejectedCount,
            HanceDrylandGroundCoverSlopeCeilingDegrees,
            HanceDrylandShrubSlopeCeilingDegrees,
            HanceDrylandMaximumSlopeDegrees);
    }

    int32 CameraVisibleWoodyPlacedCount = 0;
    int32 CameraVisibleWoodyRejectedSlopeCount = 0;
    float CameraVisibleWoodyMaximumSlopeDegrees = 0.0f;
    if (bZambeziWoodland)
    {
        // The general 30 km dressing distribution is intentionally sparse,
        // but that made the two canonical downstream cameras read as bare DEM
        // terrain.  Add a separate low-profile mosaic on both dry banks in
        // front of those cameras.  The water half-width remains a hard inner
        // exclusion and the best of several candidates is chosen by DEM slope,
        // keeping this render-only layer out of the navigable channel.
        constexpr int32 ViewBandCount = 2;
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerLongitudinalLane =
            ZambeziEvidenceBankMosaicInstanceCount /
            (ViewBandCount * BankSideCount);
        const float GroundCoverMeshHeightCm = FMath::Max(
            1.0f,
            GetLandscapeCandidateEffectiveMeshBounds(UnderstoryMesh).GetSize().Z);
        for (int32 MosaicIndex = 0;
             MosaicIndex < ZambeziEvidenceBankMosaicInstanceCount;
             ++MosaicIndex)
        {
            const int32 ViewBand = MosaicIndex % ViewBandCount;
            const int32 SideIndex =
                (MosaicIndex / ViewBandCount) % BankSideCount;
            const int32 AlongIndex =
                MosaicIndex / (ViewBandCount * BankSideCount);
            const float AlongJitter =
                ZambeziVegetationUnitRandom(MosaicIndex, 7103);
            const float AlongT =
                (static_cast<float>(AlongIndex) + AlongJitter) /
                static_cast<float>(InstancesPerLongitudinalLane);
            // Physical-camera progress maps to logical X through
            // (X + 2500) / 27900.  Because that lookup spans the full 30 km
            // source centerline, a few hundred logical centimetres represent
            // hundreds of physical route metres.  These windows begin just
            // past each camera target and cover roughly the next 120-600 m of
            // visible bank without placing meshes around the raft.
            const float BaseLogicalX = ViewBand == 0
                ? FMath::Lerp(410.0f, 850.0f, AlongT)
                : FMath::Lerp(5580.0f, 6020.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float OffsetT = FMath::Pow(
                ZambeziVegetationUnitRandom(MosaicIndex, 7121),
                1.65f);
            const float BaseOffset = ActiveRiverHalfWidth +
                FMath::Lerp(280.0f, 4300.0f, OffsetT);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * BaseOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 10; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(MosaicIndex) * 0.7548777f +
                    static_cast<float>(CandidateIndex) * 1.3247179f;
                const float CandidateLogicalX = BaseLogicalX +
                    18.0f * FMath::Sin(CandidatePhase);
                const float CandidateOffset = FMath::Clamp(
                    BaseOffset + 760.0f * FMath::Cos(CandidatePhase * 0.83f),
                    ActiveRiverHalfWidth + 240.0f,
                    ActiveRiverHalfWidth + 4700.0f);
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                if (SlopeDegrees < BestSlopeDegrees)
                {
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }

            const float TargetHeightCm = FMath::Lerp(
                54.0f,
                96.0f,
                ZambeziVegetationUnitRandom(MosaicIndex, 7151));
            const float UniformScale = TargetHeightCm / GroundCoverMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.15f,
                1.82f,
                ZambeziVegetationUnitRandom(MosaicIndex, 7177));
            AddGroundedInstance(
                ZambeziBankMosaicInstances,
                UnderstoryMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.08f, 0.0f, 1.8f),
                    360.0f * ZambeziVegetationUnitRandom(MosaicIndex, 7193),
                    1.2f * FMath::Sin(static_cast<float>(MosaicIndex) * 0.91f)),
                FVector(
                    UniformScale * FootprintScale,
                    UniformScale * FootprintScale *
                        FMath::Lerp(
                            0.82f,
                            1.18f,
                            ZambeziVegetationUnitRandom(MosaicIndex, 7207)),
                    UniformScale));
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi organic bank mosaic: %d opaque, grounded, non-colliding "
                 "instances in two camera-visible slope-screened bank windows.\n"),
            ZambeziEvidenceBankMosaicInstanceCount);
    }

    if (bZambeziWoodland)
    {
        // Low grass alone still leaves the canonical banks without a readable
        // woody silhouette.  Populate the same two evidence windows with a
        // bounded mix of the existing solid tree and thorn-scrub meshes.  The
        // dedicated components make this visual contract independently
        // countable and keep the sparse full-run distribution unchanged.
        constexpr int32 ViewBandCount = 2;
        constexpr int32 BankSideCount = 2;
        constexpr int32 WoodySpeciesSlotCount = 4;
        const int32 InstancesPerWoodyLane =
            ZambeziEvidenceWoodyInstanceCount /
            (ViewBandCount * BankSideCount * WoodySpeciesSlotCount);
        for (int32 WoodyIndex = 0;
             WoodyIndex < ZambeziEvidenceWoodyInstanceCount;
             ++WoodyIndex)
        {
            const int32 SpeciesSlot = WoodyIndex % WoodySpeciesSlotCount;
            const int32 ViewBand =
                (WoodyIndex / WoodySpeciesSlotCount) % ViewBandCount;
            const int32 SideIndex =
                (WoodyIndex / (WoodySpeciesSlotCount * ViewBandCount)) %
                BankSideCount;
            const int32 AlongIndex = WoodyIndex /
                (WoodySpeciesSlotCount * ViewBandCount * BankSideCount);
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(WoodyIndex, 8101)) /
                static_cast<float>(InstancesPerWoodyLane);
            const float BaseLogicalX = ViewBand == 0
                ? FMath::Lerp(450.0f, 1250.0f, AlongT)
                : FMath::Lerp(5620.0f, 6420.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float MaximumAdditionalOffset = FMath::Max(
                3000.0f,
                FMath::Min(
                    ViewBand == 0 ? 12000.0f : 10000.0f,
                    MaxBankOffset - ActiveRiverHalfWidth));
            const float BaseOffset = ActiveRiverHalfWidth + FMath::Lerp(
                2500.0f,
                MaximumAdditionalOffset,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(WoodyIndex, 8111),
                    1.25f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * BaseOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 40; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(WoodyIndex) * 0.6180339f +
                    static_cast<float>(CandidateIndex) * 1.2207441f;
                const float CandidateLogicalX = BaseLogicalX +
                    76.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    2500.0f,
                    MaximumAdditionalOffset,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            WoodyIndex * 43 + CandidateIndex,
                            8129),
                        1.18f));
                const float CandidateOffset = ActiveRiverHalfWidth +
                    CandidateAdditionalOffset;
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float PlacementScore = SlopeDegrees +
                    1.25f * CandidateAdditionalOffset /
                        FMath::Max(1.0f, MaximumAdditionalOffset);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestSlopeDegrees > ZambeziEvidenceWoodySlopeCeilingDegrees)
            {
                ++CameraVisibleWoodyRejectedSlopeCount;
                continue;
            }

            UStaticMesh* WoodyMesh = ShrubMesh;
            UHierarchicalInstancedStaticMeshComponent* WoodyInstances =
                ZambeziCameraThornScrubInstances;
            bool bWoodyCanopy = false;
            float TargetHeightCm = FMath::Lerp(
                180.0f,
                330.0f,
                ZambeziVegetationUnitRandom(WoodyIndex, 8147));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziCameraRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    720.0f,
                    1100.0f,
                    ZambeziVegetationUnitRandom(WoodyIndex, 8161));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziCameraUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    680.0f,
                    1000.0f,
                    ZambeziVegetationUnitRandom(WoodyIndex, 8167));
                bWoodyCanopy = true;
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(WoodyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                WoodyInstances,
                WoodyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.035f, 0.0f, 1.2f),
                    360.0f * ZambeziVegetationUnitRandom(WoodyIndex, 8179),
                    0.8f * FMath::Sin(static_cast<float>(WoodyIndex) * 0.73f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.18f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 8191)),
                    UniformScale * FMath::Lerp(
                        0.84f,
                        1.16f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 8209)),
                    UniformScale));
            ++CameraVisibleWoodyPlacedCount;
            CameraVisibleWoodyMaximumSlopeDegrees = FMath::Max(
                CameraVisibleWoodyMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++OutResult.DressingFoliageInstanceCount;
            if (bWoodyCanopy)
            {
                ++OutResult.DressingCanopyTreeInstanceCount;
            }
            else
            {
                ++OutResult.DressingUnderstoryInstanceCount;
            }
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi camera-visible woody ecology: %d/%d opaque, grounded, "
                 "non-colliding tree and thorn-scrub instances in two "
                 "downstream windows; %d candidates rejected above %.1f "
                 "degrees and maximum placed slope %.2f degrees.\n"),
            CameraVisibleWoodyPlacedCount,
            ZambeziEvidenceWoodyInstanceCount,
            CameraVisibleWoodyRejectedSlopeCount,
            ZambeziEvidenceWoodySlopeCeilingDegrees,
            CameraVisibleWoodyMaximumSlopeDegrees);
    }

    const FZambeziPlacementCounts ZambeziCounts = AddZambeziLaunchPlacements(Context, Queries);
    const int32 RunnableLaunchGroundCoverPlacedCount = ZambeziCounts.RunnableLaunchGroundCoverPlacedCount;
    const int32 RunnableLaunchWoodyPlacedCount = ZambeziCounts.RunnableLaunchWoodyPlacedCount;
    const bool bRunnableLaunchEcologyStrataValidated = ZambeziCounts.bRunnableLaunchEcologyStrataValidated;

    const int32 ExpectedFoliageInstanceCount = FoliageClusterCount +
        PacuareShorelineGroundCoverPlacedCount +
        PacuareShorelineShrubPlacedCount +
        TemperateNearBankPlacedCount +
        ChilkoShorelineGroundCoverPlacedCount +
        HanceDrylandGroundCoverPlacedCount +
        HanceDrylandShrubPlacedCount +
        (bZambeziWoodland
             ? ZambeziEvidenceBankMosaicInstanceCount +
                 CameraVisibleWoodyPlacedCount +
                 RunnableLaunchGroundCoverPlacedCount +
                 RunnableLaunchWoodyPlacedCount
             : 0);
    OutResult.bDressingValidated =
        OutResult.DressingBoulderInstanceCount ==
            BoulderCount + TemperateWaterlinePlacedCount +
                ChilkoShorelineGravelPlacedCount +
                PacuareShorelineRockPlacedCount +
                RunnableLaunchTalusPlacedCount +
                DryScarpOutcropPlacedCount &&
        OutResult.DressingFoliageInstanceCount == ExpectedFoliageInstanceCount &&
        (!bPacuare ||
         PacuareShorelineRockPlacedCount >=
             PacuareOrganicShorelineRockMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareShorelineGroundCoverPlacedCount >=
             PacuareOrganicShorelineGroundCoverMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareScannedFernPlacedCount >=
             PacuareScannedFernMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareShorelineShrubPlacedCount >=
             PacuareOrganicShorelineShrubMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareForestFloorLeafLitterPlacedCount >=
             PacuareForestFloorLeafLitterMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareForestFloorWoodyPlacedCount >=
             PacuareForestFloorWoodyMinimumInstanceCount) &&
        (!bOpaqueTemperate ||
         TemperateWaterlinePlacedCount >=
             TemperateWaterlineStructureMinimumInstanceCount) &&
        (!bOpaqueTemperate ||
         TemperateNearBankPlacedCount >=
             TemperateNearBankEcologyMinimumInstanceCount) &&
        (!bFutaleufu ||
         FutaleufuScannedUnderstoryPlacedCount >= 1200) &&
        (!bChilko ||
         ChilkoShorelineGravelPlacedCount >=
             ChilkoOrganicShorelineGravelMinimumInstanceCount) &&
        (!bChilko ||
         ChilkoShorelineGroundCoverPlacedCount >=
             ChilkoOrganicShorelineGroundCoverMinimumInstanceCount) &&
        ((Spec.bDesertCanyon && !bZambeziWoodland) ||
         OutResult.DressingCanopyTreeInstanceCount > 0) &&
        OutResult.DressingUnderstoryInstanceCount > 0 &&
        (!bColoradoHance ||
         HanceDrylandGroundCoverPlacedCount >=
             HanceDrylandMinimumGroundCoverInstanceCount) &&
        (!bColoradoHance ||
         HanceDrylandShrubPlacedCount >=
             HanceDrylandMinimumShrubInstanceCount) &&
        (!bZambeziWoodland ||
         RunnableLaunchGroundCoverPlacedCount >=
             ZambeziRunnableLaunchMinimumBankCoverInstanceCount) &&
        (!bZambeziWoodland ||
         RunnableLaunchWoodyPlacedCount >=
             ZambeziRunnableLaunchMinimumWoodyInstanceCount) &&
        bRunnableLaunchEcologyStrataValidated &&
        (!bZambeziWoodland || RunnableLaunchTalusPlacedCount >= 300) &&
        (!bZambeziWoodland ||
         DryScarpOutcropPlacedCount >=
             ZambeziDryScarpOutcropMinimumInstanceCount) &&
        (!bZambeziWoodland ||
         DryScarpOutcropMinimumHeightAboveWaterCm + 0.5f >=
             ZambeziDryScarpOutcropMinimumHeightAboveWaterCm) &&
        (!bZambeziWoodland ||
         DryScarpOutcropMaximumSlopeDegrees <=
             ZambeziDryScarpOutcropSlopeCeilingDegrees + 0.01f) &&
        OutResult.bDressingFoliageMaterialsValidated;
    OutSummary += FString::Printf(
        TEXT("Landscape biome dressing for %s: %d %s, %d foliage instances (%d canopy, %d understory), %d %s foliage slots; Nanite mesh flags boulder=%d broadleaf=%d conifer=%d understory=%d.\n"),
        *Spec.RiverId,
        OutResult.DressingBoulderInstanceCount,
        ReviewedRockMeshes.Num() == 6
            ? TEXT("rights-reviewed six-variant Nanite rock instances")
            : TEXT("dense irregular procedural boulders"),
        OutResult.DressingFoliageInstanceCount,
        OutResult.DressingCanopyTreeInstanceCount,
        OutResult.DressingUnderstoryInstanceCount,
        OutResult.DressingFoliageMaterialBoundSlotCount,
        bUsesOpaqueVolumetricVegetation
            ? TEXT("project-owned opaque volumetric")
            : TEXT("river-specific PVE"),
        OutResult.bDressingBoulderMeshNaniteEnabled,
        OutResult.bDressingBroadleafMeshNaniteEnabled,
        OutResult.bDressingConiferMeshNaniteEnabled,
        OutResult.bDressingUnderstoryMeshNaniteEnabled);
    return OutResult.bDressingValidated;
}
}
