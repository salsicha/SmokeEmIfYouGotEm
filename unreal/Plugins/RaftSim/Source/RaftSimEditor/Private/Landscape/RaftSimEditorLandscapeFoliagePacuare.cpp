#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"

#include "NiagaraActor.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"

namespace RaftSimEditorEnvironment::LandscapeFoliage
{
FPacuarePlacementCounts AddPacuarePlacements(const FPlacementContext& Context, const FPlacementQueries& Queries)
{
    auto& Landscape = Context.Landscape;
    auto& OutResult = Context.OutResult;
    auto& OutSummary = Context.OutSummary;
    auto& bPacuare = Context.bPacuare;
    auto& ReviewedRockMeshes = Context.ReviewedRockMeshes;
    auto& PacuareScannedFernMeshes = Context.PacuareScannedFernMeshes;
    auto& ShrubMesh = Context.ShrubMesh;
    auto& UnderstoryMesh = Context.UnderstoryMesh;
    auto& PacuareForestFloorMeshes = Context.PacuareForestFloorMeshes;
    auto& PacuareOrganicShorelineRockInstances = Context.PacuareOrganicShorelineRockInstances;
    auto& PacuareOrganicShorelineGroundCoverInstances = Context.PacuareOrganicShorelineGroundCoverInstances;
    auto& PacuareOrganicShorelineShrubInstances = Context.PacuareOrganicShorelineShrubInstances;
    auto& PacuareScannedFernInstances = Context.PacuareScannedFernInstances;
    auto& PacuareForestFloorInstances = Context.PacuareForestFloorInstances;
    auto& bPhysicalCorridor = Queries.bPhysicalCorridor;
    auto& ActiveRiverHalfWidth = Queries.ActiveRiverHalfWidth;
    auto& ResolveLogicalRiverPoint = Queries.ResolveLogicalRiverPoint;
    auto& GetMinimumCenterlineDistanceCm = Queries.GetMinimumCenterlineDistanceCm;
    auto& GetConditionedWaterWorldZ = Queries.GetConditionedWaterWorldZ;
    auto& GetLandscapeHeight = Queries.GetLandscapeHeight;
    auto& GetLandscapeSlopeDegrees = Queries.GetLandscapeSlopeDegrees;
    auto& AddGroundedInstance = Queries.AddGroundedInstance;

    // Target densities were set on the 600 m straight Upper Huacas reach; a
    // longer (geographic) reach keeps them per metre of centreline, and the
    // validation minimums scale the same way (FPacuarePlacementCounts).
    const float PacuareLengthScale = FMath::Max(1.0f, Queries.CenterlineLengthM / 600.0f);
    const auto Scaled = [PacuareLengthScale](int32 Count)
    {
        return 2 * FMath::RoundToInt(0.5f * static_cast<float>(Count) * PacuareLengthScale);
    };
    const int32 RockTarget = Scaled(PacuareOrganicShorelineRockTargetInstanceCount);
    const int32 GroundTarget = Scaled(PacuareOrganicShorelineGroundCoverTargetInstanceCount);
    const int32 FernTarget = Scaled(PacuareScannedFernTargetInstanceCount);
    const int32 ShrubTarget = Scaled(PacuareOrganicShorelineShrubTargetInstanceCount);
    const int32 LitterTarget = Scaled(PacuareForestFloorLeafLitterTargetInstanceCount);
    const int32 WoodyTarget = Scaled(PacuareForestFloorWoodyTargetInstanceCount);
    // The geographic reach has the real (steeper) gorge walls: search more
    // candidates, further along the bank, for each instance instead of
    // lowering the placement minimums.
    const int32 SearchScale = PacuareLengthScale > 1.0f ? 5 : 1;
    const float AlongJitterScale = PacuareLengthScale > 1.0f ? 4.0f : 1.0f;
    int32 PacuareShorelineRockPlacedCount = 0;
    int32 PacuareShorelineRockRejectedPlacementCount = 0;
    int32 PacuareShorelineGroundCoverPlacedCount = 0;
    int32 PacuareShorelineGroundCoverRejectedPlacementCount = 0;
    int32 PacuareScannedFernPlacedCount = 0;
    int32 PacuareShorelineShrubPlacedCount = 0;
    int32 PacuareShorelineShrubRejectedPlacementCount = 0;
    int32 PacuareForestFloorLeafLitterPlacedCount = 0;
    int32 PacuareForestFloorWoodyPlacedCount = 0;
    int32 PacuareForestFloorRejectedPlacementCount = 0;
    float PacuareShorelineMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float PacuareShorelineMaximumSlopeDegrees = 0.0f;
    if (bPacuare && bPhysicalCorridor &&
        ReviewedRockMeshes.Num() == 6 &&
        PacuareOrganicShorelineRockInstances.Num() == 6)
    {
        // Upper Huacas is only 78 m wide, so the 30 m source context leaves a
        // narrow bank transition visible from the raft. Fill that unresolved
        // band with deterministic, source-grounded moss-rock morphology,
        // short rainforest floor cover, and shrubs. The complete visible
        // river width and a hard centerline clearance remain protected. These
        // HISM layers are non-colliding visual infill; Landscape height and
        // collision plus cooked-field water retain all geography, bathymetry,
        // hydraulic, and raft-force authority.
        const float VisibleRiverHalfWidth =
            FMath::Max(1700.0f, ActiveRiverHalfWidth * 1.32f);
        constexpr int32 BankSideCount = 2;
        const int32 RockInstancesPerSide =
            RockTarget / BankSideCount;
        for (int32 RockIndex = 0;
             RockIndex < RockTarget;
             ++RockIndex)
        {
            const float Side = RockIndex % 2 == 0 ? -1.0f : 1.0f;
            const int32 AlongIndex = RockIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(RockIndex, 11101)) /
                static_cast<float>(RockInstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2425.0f, 25325.0f, AlongT) +
                FMath::Lerp(
                    -72.0f,
                    72.0f,
                    ZambeziVegetationUnitRandom(RockIndex, 11107));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 260.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 28 * SearchScale;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + AlongJitterScale * FMath::Lerp(
                    -90.0f,
                    90.0f,
                    ZambeziVegetationUnitRandom(
                        RockIndex * 31 + CandidateIndex,
                        11113));
                const float AdditionalOffset = FMath::Lerp(
                    45.0f,
                    1650.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            RockIndex * 37 + CandidateIndex,
                            11117),
                        1.72f));
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
                        PacuareOrganicShorelineRockSlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 30.0f ||
                    HeightAboveWaterCm < -5.0f ||
                    HeightAboveWaterCm > 1450.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    30.0f,
                    430.0f,
                    ZambeziVegetationUnitRandom(RockIndex, 11119));
                const float Score =
                    0.62f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 1450.0f +
                    0.25f * AdditionalOffset / 1650.0f +
                    0.13f * SlopeDegrees /
                        PacuareOrganicShorelineRockSlopeCeilingDegrees;
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
                ++PacuareShorelineRockRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = RockIndex % 30;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      95.0f,
                      155.0f,
                      ZambeziVegetationUnitRandom(RockIndex, 11123))
                : (ScaleClass < 7
                       ? FMath::Lerp(
                             38.0f,
                             88.0f,
                             ZambeziVegetationUnitRandom(RockIndex, 11129))
                       : FMath::Lerp(
                             12.0f,
                             42.0f,
                             ZambeziVegetationUnitRandom(RockIndex, 11131)));
            const int32 VariantIndex = RockIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            UHierarchicalInstancedStaticMeshComponent* RockComponent =
                PacuareOrganicShorelineRockInstances[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                RockComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.08f, 0.0f, 4.0f),
                    360.0f * ZambeziVegetationUnitRandom(RockIndex, 11137),
                    FMath::Lerp(
                        -5.0f,
                        5.0f,
                        ZambeziVegetationUnitRandom(RockIndex, 11141))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.68f,
                        1.52f,
                        ZambeziVegetationUnitRandom(RockIndex, 11149)),
                    UniformScale * FMath::Lerp(
                        0.70f,
                        1.46f,
                        ZambeziVegetationUnitRandom(RockIndex, 11159)),
                    UniformScale));
            ++PacuareShorelineRockPlacedCount;
            ++OutResult.DressingBoulderInstanceCount;
            PacuareShorelineMinimumCenterlineDistanceCm = FMath::Min(
                PacuareShorelineMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            PacuareShorelineMaximumSlopeDegrees = FMath::Max(
                PacuareShorelineMaximumSlopeDegrees,
                BestSlopeDegrees);
        }

        const int32 ForestFloorTargetCount =
            LitterTarget +
            WoodyTarget;
        if (PacuareForestFloorMeshes.Num() == 4 &&
            PacuareForestFloorInstances.Num() == 4)
        {
            for (int32 ForestFloorIndex = 0;
                 ForestFloorIndex < ForestFloorTargetCount;
                 ++ForestFloorIndex)
            {
                const bool bWoody = ForestFloorIndex >=
                    LitterTarget;
                const int32 FamilyIndex = bWoody
                    ? ForestFloorIndex -
                        LitterTarget
                    : ForestFloorIndex;
                const int32 FamilyTargetCount = bWoody
                    ? WoodyTarget
                    : LitterTarget;
                const float Side = FamilyIndex % 2 == 0 ? -1.0f : 1.0f;
                const int32 AlongIndex = FamilyIndex / BankSideCount;
                const int32 InstancesPerSide = FamilyTargetCount / BankSideCount;
                const float AlongT =
                    (static_cast<float>(AlongIndex) +
                     ZambeziVegetationUnitRandom(
                         ForestFloorIndex + PacuareForestFloorDeterministicSeed,
                         12203)) /
                    static_cast<float>(InstancesPerSide);
                const float BaseLogicalX =
                    FMath::Lerp(-2425.0f, 25325.0f, AlongT) +
                    FMath::Lerp(
                        -135.0f,
                        135.0f,
                        ZambeziVegetationUnitRandom(
                            ForestFloorIndex + PacuareForestFloorDeterministicSeed,
                            12211));
                FVector2D BestPoint = ResolveLogicalRiverPoint(
                    BaseLogicalX,
                    Side * (VisibleRiverHalfWidth + (bWoody ? 310.0f : 120.0f)));
                float BestSlopeDegrees = TNumericLimits<float>::Max();
                float BestCenterlineDistanceCm = 0.0f;
                float BestScore = TNumericLimits<float>::Max();
                // The geographic reach's real walls leave too few <= 32 degree
                // spots near the banks in its gorge stretches; roots and
                // deadwood lie on the same slopes as leaf litter there.
                const float SlopeCeilingDegrees = bWoody
                    ? (PacuareLengthScale > 1.0f ? PacuareForestFloorLeafLitterSlopeCeilingDegrees
                                                 : PacuareForestFloorWoodySlopeCeilingDegrees)
                    : PacuareForestFloorLeafLitterSlopeCeilingDegrees;
                for (int32 CandidateIndex = 0;
                     CandidateIndex < 32 * SearchScale * (bWoody ? 2 : 1);
                     ++CandidateIndex)
                {
                    const int32 CandidateSeed =
                        (ForestFloorIndex + PacuareForestFloorDeterministicSeed) * 41 +
                        CandidateIndex;
                    const float CandidateLogicalX = BaseLogicalX + AlongJitterScale * FMath::Lerp(
                        -150.0f,
                        150.0f,
                        ZambeziVegetationUnitRandom(CandidateSeed, 12227));
                    const float AdditionalOffset = FMath::Lerp(
                        bWoody ? 210.0f : 55.0f,
                        bWoody ? (PacuareLengthScale > 1.0f ? 3500.0f : 2350.0f) : 2100.0f,
                        FMath::Pow(
                            ZambeziVegetationUnitRandom(CandidateSeed, 12239),
                            bWoody ? 1.22f : 1.58f));
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
                    const float MinimumDryHeightCm = bWoody ? 60.0f : 18.0f;
                    const float MaximumDryHeightCm = bWoody ? 2200.0f : 1750.0f;
                    if (SlopeDegrees > SlopeCeilingDegrees ||
                        CenterlineDistanceCm < VisibleRiverHalfWidth +
                            (bWoody ? 180.0f : 45.0f) ||
                        HeightAboveWaterCm < MinimumDryHeightCm ||
                        HeightAboveWaterCm > MaximumDryHeightCm)
                    {
                        continue;
                    }
                    const float TargetDryHeightCm = FMath::Lerp(
                        bWoody ? 260.0f : 65.0f,
                        bWoody ? 1180.0f : 720.0f,
                        ZambeziVegetationUnitRandom(
                            ForestFloorIndex + PacuareForestFloorDeterministicSeed,
                            12241));
                    const float Score =
                        0.55f * FMath::Abs(
                            HeightAboveWaterCm - TargetDryHeightCm) /
                            MaximumDryHeightCm +
                        0.30f * AdditionalOffset /
                            (bWoody ? 2350.0f : 2100.0f) +
                        0.15f * SlopeDegrees / SlopeCeilingDegrees;
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
                    ++PacuareForestFloorRejectedPlacementCount;
                    continue;
                }

                const int32 MeshIndex = bWoody
                    ? 2 + FamilyIndex % 2
                    : FamilyIndex % 2;
                UStaticMesh* ForestFloorMesh =
                    PacuareForestFloorMeshes[MeshIndex];
                UHierarchicalInstancedStaticMeshComponent* ForestFloorComponent =
                    PacuareForestFloorInstances[MeshIndex];
                const float TargetHeightCm = bWoody
                    ? (MeshIndex == 2
                           ? FMath::Lerp(
                                 38.0f,
                                 86.0f,
                                 ZambeziVegetationUnitRandom(
                                     ForestFloorIndex, 12251))
                           : FMath::Lerp(
                                 30.0f,
                                 62.0f,
                                 ZambeziVegetationUnitRandom(
                                     ForestFloorIndex, 12253)))
                    : FMath::Lerp(
                          8.0f,
                          18.0f,
                          ZambeziVegetationUnitRandom(
                              ForestFloorIndex, 12263));
                const float MeshHeightCm = FMath::Max(
                    1.0f,
                    GetLandscapeCandidateEffectiveMeshBounds(
                        ForestFloorMesh).GetSize().Z);
                const float UniformScale = TargetHeightCm / MeshHeightCm;
                AddGroundedInstance(
                    ForestFloorComponent,
                    ForestFloorMesh,
                    BestPoint,
                    GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                    FRotator(
                        FMath::Clamp(BestSlopeDegrees * 0.035f, 0.0f, 1.4f),
                        360.0f * ZambeziVegetationUnitRandom(
                            ForestFloorIndex, 12269),
                        FMath::Lerp(
                            -2.0f,
                            2.0f,
                            ZambeziVegetationUnitRandom(
                                ForestFloorIndex, 12277))),
                    FVector(
                        UniformScale * FMath::Lerp(
                            0.78f,
                            1.30f,
                            ZambeziVegetationUnitRandom(
                                ForestFloorIndex, 12281)),
                        UniformScale * FMath::Lerp(
                            0.76f,
                            1.34f,
                            ZambeziVegetationUnitRandom(
                                ForestFloorIndex, 12289)),
                        UniformScale));
                if (bWoody)
                {
                    ++PacuareForestFloorWoodyPlacedCount;
                }
                else
                {
                    ++PacuareForestFloorLeafLitterPlacedCount;
                }
                PacuareShorelineMinimumCenterlineDistanceCm = FMath::Min(
                    PacuareShorelineMinimumCenterlineDistanceCm,
                    BestCenterlineDistanceCm);
                PacuareShorelineMaximumSlopeDegrees = FMath::Max(
                    PacuareShorelineMaximumSlopeDegrees,
                    BestSlopeDegrees);
            }
        }

        const int32 EcologyTargetCount =
            GroundTarget +
            ShrubTarget;
        for (int32 EcologyIndex = 0;
             EcologyIndex < EcologyTargetCount;
             ++EcologyIndex)
        {
            const bool bShrub = EcologyIndex >=
                GroundTarget;
            const int32 FamilyIndex = bShrub
                ? EcologyIndex -
                    GroundTarget
                : EcologyIndex;
            const int32 FamilyTargetCount = bShrub
                ? ShrubTarget
                : GroundTarget;
            const float Side = FamilyIndex % 2 == 0 ? -1.0f : 1.0f;
            const int32 AlongIndex = FamilyIndex / BankSideCount;
            const int32 InstancesPerSide = FamilyTargetCount / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(EcologyIndex, 11201)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2425.0f, 25325.0f, AlongT) +
                FMath::Lerp(
                    -105.0f,
                    105.0f,
                    ZambeziVegetationUnitRandom(EcologyIndex, 11213));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + (bShrub ? 420.0f : 190.0f)));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            const float SlopeCeilingDegrees = bShrub
                ? PacuareOrganicShorelineShrubSlopeCeilingDegrees
                : PacuareOrganicShorelineGroundCoverSlopeCeilingDegrees;
            for (int32 CandidateIndex = 0; CandidateIndex < 24 * SearchScale;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + AlongJitterScale * FMath::Lerp(
                    -125.0f,
                    125.0f,
                    ZambeziVegetationUnitRandom(
                        EcologyIndex * 29 + CandidateIndex,
                        11227));
                const float AdditionalOffset = FMath::Lerp(
                    bShrub ? 230.0f : 75.0f,
                    bShrub ? 1950.0f : 1800.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            EcologyIndex * 43 + CandidateIndex,
                            11239),
                        bShrub ? 1.18f : 1.48f));
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
                const float MinimumDryHeightCm = bShrub ? 35.0f : 12.0f;
                const float MaximumDryHeightCm = bShrub ? 2100.0f : 1650.0f;
                if (SlopeDegrees > SlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth +
                        (bShrub ? 180.0f : 55.0f) ||
                    HeightAboveWaterCm < MinimumDryHeightCm ||
                    HeightAboveWaterCm > MaximumDryHeightCm)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    bShrub ? 210.0f : 75.0f,
                    bShrub ? 980.0f : 620.0f,
                    ZambeziVegetationUnitRandom(EcologyIndex, 11243));
                const float Score =
                    0.57f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) /
                        MaximumDryHeightCm +
                    0.28f * AdditionalOffset /
                        (bShrub ? 1950.0f : 1800.0f) +
                    0.15f * SlopeDegrees / SlopeCeilingDegrees;
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
                if (bShrub)
                {
                    ++PacuareShorelineShrubRejectedPlacementCount;
                }
                else
                {
                    ++PacuareShorelineGroundCoverRejectedPlacementCount;
                }
                continue;
            }

            const bool bUseScannedFern = !bShrub &&
                FamilyIndex % 10 < 7 &&
                PacuareScannedFernMeshes.Num() == 4 &&
                PacuareScannedFernInstances.Num() == 4;
            const int32 ScannedFernVariantIndex = bUseScannedFern
                ? FamilyIndex % PacuareScannedFernMeshes.Num()
                : INDEX_NONE;
            UStaticMesh* EcologyMesh = bShrub
                ? ShrubMesh
                : (bUseScannedFern
                       ? PacuareScannedFernMeshes[ScannedFernVariantIndex]
                       : UnderstoryMesh);
            UHierarchicalInstancedStaticMeshComponent* EcologyComponent = bShrub
                ? PacuareOrganicShorelineShrubInstances
                : (bUseScannedFern
                       ? PacuareScannedFernInstances[ScannedFernVariantIndex]
                       : PacuareOrganicShorelineGroundCoverInstances);
            const float TargetHeightCm = FMath::Lerp(
                bShrub ? 135.0f : (bUseScannedFern ? 38.0f : 26.0f),
                bShrub ? 360.0f : (bUseScannedFern ? 96.0f : 118.0f),
                ZambeziVegetationUnitRandom(EcologyIndex, 11251));
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(EcologyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                EcologyComponent,
                EcologyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.025f, 0.0f, 1.0f),
                    360.0f * ZambeziVegetationUnitRandom(EcologyIndex, 11257),
                    FMath::Lerp(
                        -1.2f,
                        1.2f,
                        ZambeziVegetationUnitRandom(EcologyIndex, 11261))),
                FVector(
                    UniformScale * FMath::Lerp(
                        bShrub ? 0.76f : 0.66f,
                        bShrub ? 1.28f : 1.46f,
                        ZambeziVegetationUnitRandom(EcologyIndex, 11269)),
                    UniformScale * FMath::Lerp(
                        bShrub ? 0.78f : 0.70f,
                        bShrub ? 1.24f : 1.40f,
                        ZambeziVegetationUnitRandom(EcologyIndex, 11273)),
                    UniformScale));
            if (bShrub)
            {
                ++PacuareShorelineShrubPlacedCount;
            }
            else
            {
                ++PacuareShorelineGroundCoverPlacedCount;
                PacuareScannedFernPlacedCount += bUseScannedFern ? 1 : 0;
            }
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
            PacuareShorelineMinimumCenterlineDistanceCm = FMath::Min(
                PacuareShorelineMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            PacuareShorelineMaximumSlopeDegrees = FMath::Max(
                PacuareShorelineMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareOrganicShorelineRockInstances)
        {
            Component->MarkRenderStateDirty();
        }
        PacuareOrganicShorelineGroundCoverInstances->MarkRenderStateDirty();
        PacuareOrganicShorelineShrubInstances->MarkRenderStateDirty();
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareScannedFernInstances)
        {
            Component->MarkRenderStateDirty();
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareForestFloorInstances)
        {
            Component->MarkRenderStateDirty();
        }
        OutResult.DressingPacuareScannedFernInstanceCount =
            PacuareScannedFernPlacedCount;
        OutResult.DressingPacuareForestFloorTargetInstanceCount =
            ForestFloorTargetCount;
        OutResult.DressingPacuareForestFloorInstanceCount =
            PacuareForestFloorLeafLitterPlacedCount +
            PacuareForestFloorWoodyPlacedCount;
        OutResult.DressingPacuareForestFloorRejectedPlacementCount =
            PacuareForestFloorRejectedPlacementCount;
        OutResult.DressingPacuareForestFloorMinimumCenterlineDistanceCm =
            PacuareShorelineMinimumCenterlineDistanceCm;
        OutResult.DressingPacuareForestFloorMaximumSlopeDegrees =
            PacuareShorelineMaximumSlopeDegrees;
        OutSummary += FString::Printf(
            TEXT("Pacuare organic shoreline V1: %d/%d moss-rock analogs, ")
            TEXT("%d/%d short rainforest-floor patches (%d/%d rights-reviewed ")
            TEXT("scanned fern morphology analogs), and %d/%d shrubs ")
            TEXT("placed across both full-route banks; rejected rock/cover/shrub ")
            TEXT("targets=%d/%d/%d, minimum centerline distance %.1f cm, and ")
            TEXT("maximum slope %.2f degrees. Source-Landscape-grounded, ")
            TEXT("non-colliding procedural gap fill with no lithology, species, ")
            TEXT("ecology, survey, hydraulic, bathymetry, or raft-force authority.\n"),
            PacuareShorelineRockPlacedCount,
            RockTarget,
            PacuareShorelineGroundCoverPlacedCount,
            GroundTarget,
            PacuareScannedFernPlacedCount,
            FernTarget,
            PacuareShorelineShrubPlacedCount,
            ShrubTarget,
            PacuareShorelineRockRejectedPlacementCount,
            PacuareShorelineGroundCoverRejectedPlacementCount,
            PacuareShorelineShrubRejectedPlacementCount,
            PacuareShorelineMinimumCenterlineDistanceCm,
            PacuareShorelineMaximumSlopeDegrees);
        OutSummary += FString::Printf(
            TEXT("Pacuare forest-floor structure V1: %d/%d folded-leaf litter ")
            TEXT("clusters and %d/%d buttress-root/deadwood clusters placed; ")
            TEXT("%d targets rejected, deterministic seed=%d, minimum ")
            TEXT("centerline distance %.1f cm, maximum slope %.2f degrees. ")
            TEXT("Opaque project-owned procedural infill is source-Landscape-")
            TEXT("grounded and non-colliding with no species, ecology, terrain, ")
            TEXT("water, hydraulic, bathymetric, or raft-force authority.\n"),
            PacuareForestFloorLeafLitterPlacedCount,
            LitterTarget,
            PacuareForestFloorWoodyPlacedCount,
            WoodyTarget,
            PacuareForestFloorRejectedPlacementCount,
            PacuareForestFloorDeterministicSeed,
            PacuareShorelineMinimumCenterlineDistanceCm,
            PacuareShorelineMaximumSlopeDegrees);
    }

    // Evidence dressing (physics/scripts/build_pacuare_evidence_dressing.py),
    // written beside the terrain. The canopy: orthophoto crown tops plus
    // infill inside the IGN tree-cover polygons over the whole Landscape
    // window, so the gorge walls carry the closed forest the photographs show
    // instead of a bare drape.
    const FString EvidenceFolder = TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/huacas_evidence_2017");
    FEvidenceCanopyCounts EvidenceCanopy;
    if (bPacuare && bPhysicalCorridor)
    {
        EvidenceCanopy = AddEvidenceCanopy(
            Context, Queries, EvidenceFolder, TEXT("huacas_evidence_canopy_placement.json"),
            TEXT("raftsim.pacuare.huacas_evidence_canopy.v1"), TEXT("RaftSim_PacuareEvidence"),
            TEXT("RaftSimPacuareEvidenceCanopy"),
            TEXT("orthophoto crown tops and infill inside IGN forestal2017 tree cover"));
    }
    const int32 EvidenceCanopyExpected = EvidenceCanopy.Expected;
    const int32 EvidenceCanopyPlaced = EvidenceCanopy.Placed;

    // Emergent-rock shells: the photographed rocks are Landscape bumps of the
    // evidence bed (collision and solver obstacle) that render as faceted
    // prisms at the Landscape spacing. Compact rocks get a reviewed rock mesh
    // fitted to the footprint ellipse, from below the surface to just above
    // the bump. Visual only, like the shoreline rocks whose materials they use.
    int32 EvidenceRockExpected = 0;
    int32 EvidenceRockPlaced = 0;
    if (bPacuare && bPhysicalCorridor && ReviewedRockMeshes.Num() == 6 &&
        PacuareOrganicShorelineRockInstances.Num() == 6)
    {
        const TSharedPtr<FJsonObject> RockRoot = LoadEvidencePlacement(
            EvidenceFolder, TEXT("huacas_evidence_rock_placement.json"), TEXT("raftsim.pacuare.huacas_evidence_rocks.v1"),
            OutSummary);
        const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
        if (!RockRoot.IsValid() || !RockRoot->TryGetArrayField(TEXT("instances"), Rows))
        {
            EvidenceRockExpected = 1;
        }
        else
        {
            EvidenceRockExpected = Rows->Num();
            UHierarchicalInstancedStaticMeshComponent* Components[6] = {};
            FVector MeshSizes[6];
            bool bComponentsReady = true;
            for (int32 Variant = 0; Variant < 6; ++Variant)
            {
                Components[Variant] = AddLandscapeCandidateInstancedMeshComponent(
                    Context.World, ReviewedRockMeshes[Variant],
                    FString::Printf(TEXT("RaftSim_PacuareEvidenceRock%d_pacuare"), Variant), true);
                if (!Components[Variant] || !PacuareOrganicShorelineRockInstances[Variant])
                {
                    bComponentsReady = false;
                    continue;
                }
                Components[Variant]->GetOwner()->Tags.Append(
                    {TEXT("RaftSimPacuareEvidenceRock"), TEXT("RaftSimImageryRockPositions"),
                     TEXT("RaftSimNoTerrainCollisionOrWaterAuthority")});
                const UHierarchicalInstancedStaticMeshComponent* Source = PacuareOrganicShorelineRockInstances[Variant];
                for (int32 Slot = 0; Slot < Source->GetNumMaterials(); ++Slot)
                {
                    Components[Variant]->SetMaterial(Slot, Source->GetMaterial(Slot));
                }
                MeshSizes[Variant] = GetLandscapeCandidateEffectiveMeshBounds(ReviewedRockMeshes[Variant]).GetSize();
            }
            for (const TSharedPtr<FJsonValue>& Value : *Rows)
            {
                const TArray<TSharedPtr<FJsonValue>>* Row = nullptr;
                if (!bComponentsReady || !Value.IsValid() || !Value->TryGetArray(Row) || Row->Num() < 8)
                {
                    continue;
                }
                // x_cm, y_cm, base_z_cm, length_m, width_m, height_m, yaw_deg, variant
                const int32 Variant = FMath::Clamp(static_cast<int32>((*Row)[7]->AsNumber()), 0, 5);
                const FVector& Size = MeshSizes[Variant];
                const FVector Scale(
                    100.0f * static_cast<float>((*Row)[3]->AsNumber()) / FMath::Max(1.0f, static_cast<float>(Size.X)),
                    100.0f * static_cast<float>((*Row)[4]->AsNumber()) / FMath::Max(1.0f, static_cast<float>(Size.Y)),
                    100.0f * static_cast<float>((*Row)[5]->AsNumber()) / FMath::Max(1.0f, static_cast<float>(Size.Z)));
                AddGroundedInstance(
                    Components[Variant], ReviewedRockMeshes[Variant],
                    FVector2D((*Row)[0]->AsNumber(), (*Row)[1]->AsNumber()),
                    static_cast<float>((*Row)[2]->AsNumber()),
                    FRotator(0.0f, static_cast<float>((*Row)[6]->AsNumber()), 0.0f), Scale);
                ++EvidenceRockPlaced;
            }
            OutSummary += FString::Printf(
                TEXT("Pacuare emergent-rock shells: %d/%d reviewed rock meshes fitted to photographed rock ")
                TEXT("footprints (heights inferred); visual only over the Landscape rock bumps.\n"),
                EvidenceRockPlaced, EvidenceRockExpected);
        }
    }

    // Huacas Falls (physics/scripts/add_pacuare_huacas_falls.py): the 30-46 m
    // river-right fall the observations describe between the Huacas rapids
    // is painted into the drape along its fall line; spray mist rises from
    // its plunge and drifts off the lower cascade. Visual only.
    if (bPacuare && bPhysicalCorridor)
    {
        FString FallText;
        TSharedPtr<FJsonObject> Fall;
        if (FFileHelper::LoadFileToString(FallText, *FPaths::ConvertRelativePathToFull(FPaths::Combine(
                GetRepoRoot(), EvidenceFolder, TEXT("huacas_evidence_observed_waterfall.json")))))
        {
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(FallText), Fall);
        }
        UNiagaraSystem* Mist = LoadObject<UNiagaraSystem>(
            nullptr, TEXT("/Game/RaftSim/VFX/Water/NS_RaftSim_AeratedMist.NS_RaftSim_AeratedMist"));
        const TArray<TSharedPtr<FJsonValue>>* Base = nullptr;
        const TArray<TSharedPtr<FJsonValue>>* Lip = nullptr;
        int32 MistPlaced = 0;
        if (Fall.IsValid() && Mist && Fall->TryGetArrayField(TEXT("base_cm"), Base) &&
            Fall->TryGetArrayField(TEXT("lip_cm"), Lip) && Base->Num() == 2 && Lip->Num() == 2)
        {
            const FVector2D BaseXY((*Base)[0]->AsNumber(), (*Base)[1]->AsNumber());
            const FVector2D LipXY((*Lip)[0]->AsNumber(), (*Lip)[1]->AsNumber());
            // plunge, lower cascade, mid cascade: rate and size fall off upward
            const float Along[3] = {0.0f, 0.25f, 0.5f};
            const float Rates[3] = {110.0f, 60.0f, 35.0f};
            const float Scales[3] = {3.2f, 2.2f, 1.6f};
            for (int32 Index = 0; Index < 3; ++Index)
            {
                const FVector2D XY = FMath::Lerp(BaseXY, LipXY, Along[Index]);
                const FVector Location(XY.X, XY.Y, Queries.GetLandscapeHeight(XY.X, XY.Y) + 120.0f);
                ANiagaraActor* Actor = Context.World->SpawnActor<ANiagaraActor>(Location, FRotator::ZeroRotator);
                if (!Actor || !Actor->GetNiagaraComponent())
                {
                    continue;
                }
                Actor->SetActorLabel(FString::Printf(TEXT("RaftSim_PacuareHuacasFallsMist_%d"), Index));
                Actor->Tags.Append({TEXT("RaftSimPacuareHuacasFalls"), TEXT("RaftSimObservedWaterfall"),
                                    TEXT("RaftSimNoTerrainCollisionOrWaterAuthority")});
                UNiagaraComponent* Component = Actor->GetNiagaraComponent();
                Component->SetAsset(Mist);
                Component->SetAutoActivate(true);
                Component->SetVariableFloat(TEXT("User.SpawnRate"), Rates[Index]);
                Component->SetVariableQuat(TEXT("User.SourcePlaneRotation"), FQuat::Identity);
                Actor->SetActorScale3D(FVector(Scales[Index]));
                ++MistPlaced;
            }
            // The wall is in shade, so the painted cascade reads grey: three
            // thin falling-water strands (the project's translucent
            // flow-lace breaking-water material) lie along the fall line,
            // 0.6 m off the rock.
            UStaticMesh* Plane = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
            UMaterialInterface* Lace = LoadObject<UMaterialInterface>(
                nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip.M_RaftSim_BreakingWaterLip"));
            const FVector Lip3(LipXY, Queries.GetLandscapeHeight(LipXY.X, LipXY.Y));
            const FVector Base3(BaseXY, Queries.GetLandscapeHeight(BaseXY.X, BaseXY.Y));
            const FVector FallDir = (Base3 - Lip3).GetSafeNormal();
            const FVector FallAcross = FVector::CrossProduct(FallDir, FVector::UpVector).GetSafeNormal();
            FVector FallOut = FVector::CrossProduct(FallAcross, FallDir).GetSafeNormal();
            if (FallOut.Z < 0.0f)
            {
                FallOut = -FallOut;
            }
            const float LengthCm = FVector::Dist(Lip3, Base3);
            // offset across the fall (cm), width (cm), share of the length
            const float Strands[3][3] = {{0.0f, 600.0f, 1.0f}, {-330.0f, 240.0f, 0.82f}, {360.0f, 200.0f, 0.68f}};
            int32 StrandsPlaced = 0;
            for (int32 Index = 0; Plane && Lace && Index < 3; ++Index)
            {
                const float Length = LengthCm * Strands[Index][2];
                const FVector Centre = Lip3 + FallDir * (LengthCm - 0.5f * Length) + FallAcross * Strands[Index][0] + FallOut * 60.0f;
                AStaticMeshActor* Strand = AddPreviewMeshActor(
                    Context.World, Plane, FString::Printf(TEXT("RaftSim_PacuareHuacasFallsStrand_%d"), Index),
                    Centre, FRotationMatrix::MakeFromXY(FallAcross, FallDir).Rotator(),
                    FVector(Strands[Index][1] / 100.0f, Length / 100.0f, 1.0f), FLinearColor::White, Lace);
                if (!Strand)
                {
                    continue;
                }
                Strand->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                Strand->GetStaticMeshComponent()->SetCastShadow(false);
                Strand->Tags.Append({TEXT("RaftSimPacuareHuacasFalls"), TEXT("RaftSimObservedWaterfall"),
                                     TEXT("RaftSimNoTerrainCollisionOrWaterAuthority")});
                ++StrandsPlaced;
            }
            MistPlaced += StrandsPlaced;
        }
        OutSummary += FString::Printf(
            TEXT("Pacuare Huacas Falls: %s, %d spray-mist emitters and falling-water strands (inferred appearance).\n"),
            Fall.IsValid() ? TEXT("cascade painted along its fall line") : TEXT("record missing"), MistPlaced);
    }

    FPacuarePlacementCounts Counts{PacuareShorelineRockPlacedCount, PacuareShorelineGroundCoverPlacedCount, PacuareScannedFernPlacedCount,
                                   PacuareShorelineShrubPlacedCount, PacuareForestFloorLeafLitterPlacedCount, PacuareForestFloorWoodyPlacedCount};
    Counts.RockMinimum = Scaled(PacuareOrganicShorelineRockMinimumInstanceCount);
    Counts.GroundCoverMinimum = Scaled(PacuareOrganicShorelineGroundCoverMinimumInstanceCount);
    Counts.FernMinimum = Scaled(PacuareScannedFernMinimumInstanceCount);
    Counts.ShrubMinimum = Scaled(PacuareOrganicShorelineShrubMinimumInstanceCount);
    Counts.LeafLitterMinimum = Scaled(PacuareForestFloorLeafLitterMinimumInstanceCount);
    Counts.WoodyMinimum = Scaled(PacuareForestFloorWoodyMinimumInstanceCount);
    Counts.EvidenceCanopyExpected = EvidenceCanopyExpected;
    Counts.EvidenceCanopyPlaced = EvidenceCanopyPlaced;
    Counts.EvidenceRockExpected = EvidenceRockExpected;
    Counts.EvidenceRockPlaced = EvidenceRockPlaced;
    return Counts;
}
}
