#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"

namespace RaftSimEditorEnvironment::LandscapeFoliage
{
FZambeziPlacementCounts AddZambeziLaunchPlacements(const FPlacementContext& Context, const FPlacementQueries& Queries)
{
    auto& Landscape = Context.Landscape;
    auto& OutResult = Context.OutResult;
    auto& OutSummary = Context.OutSummary;
    auto& BroadleafTreeMesh = Context.BroadleafTreeMesh;
    auto& ConiferTreeMesh = Context.ConiferTreeMesh;
    auto& ShrubMesh = Context.ShrubMesh;
    auto& UnderstoryMesh = Context.UnderstoryMesh;
    auto& ZambeziGroundCoverMeshB = Context.ZambeziGroundCoverMeshB;
    auto& ZambeziRunnableLaunchGroundCoverInstances = Context.ZambeziRunnableLaunchGroundCoverInstances;
    auto& ZambeziRunnableLaunchGroundCoverInstancesB = Context.ZambeziRunnableLaunchGroundCoverInstancesB;
    auto& ZambeziRunnableLaunchRiparianTreeInstances = Context.ZambeziRunnableLaunchRiparianTreeInstances;
    auto& ZambeziRunnableLaunchUmbrellaTreeInstances = Context.ZambeziRunnableLaunchUmbrellaTreeInstances;
    auto& ZambeziRunnableLaunchThornScrubInstances = Context.ZambeziRunnableLaunchThornScrubInstances;
    auto& bZambeziWoodland = Queries.bZambeziWoodland;
    auto& ActiveRiverHalfWidth = Queries.ActiveRiverHalfWidth;
    auto& ResolveLogicalRiverPoint = Queries.ResolveLogicalRiverPoint;
    auto& GetMinimumCenterlineDistanceCm = Queries.GetMinimumCenterlineDistanceCm;
    auto& GetConditionedWaterWorldZ = Queries.GetConditionedWaterWorldZ;
    auto& GetLandscapeHeight = Queries.GetLandscapeHeight;
    auto& GetLandscapeSlopeDegrees = Queries.GetLandscapeSlopeDegrees;
    auto& AddGroundedInstance = Queries.AddGroundedInstance;

    int32 RunnableLaunchGroundCoverPlacedCount = 0;
    int32 RunnableLaunchWoodyPlacedCount = 0;
    int32 RunnableLaunchWoodyRejectedSlopeCount = 0;
    float RunnableLaunchWoodyMaximumSlopeDegrees = 0.0f;
    int32 RunnableLaunchGroundCoverPlacedPerStratum[
        ZambeziRunnableLaunchEcologyStratumCount] = {};
    int32 RunnableLaunchWoodyPlacedPerStratum[
        ZambeziRunnableLaunchEcologyStratumCount] = {};
    bool bRunnableLaunchEcologyStrataValidated = !bZambeziWoodland;
    if (bZambeziWoodland)
    {
        // The actual runnable raft starts near station 75 m, far upstream of
        // both documentary capture windows and of the sparse full-reach
        // distribution. Give that gameplay window its own countable bank
        // ecology layer. It remains outside the active river, non-colliding,
        // source-Landscape grounded, and independent of all water/physics.
        constexpr int32 BankSideCount = 2;
        const int32 GroundCoverInstancesPerSide =
            ZambeziRunnableLaunchBankCoverInstanceCount / BankSideCount;
        int32 RunnableLaunchGroundCoverRejectedCount = 0;
        float RunnableLaunchGroundCoverMaximumSlopeDegrees = 0.0f;
        for (int32 CoverIndex = 0;
             CoverIndex < ZambeziRunnableLaunchBankCoverInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const int32 ElevationBand = AlongIndex %
                ZambeziRunnableLaunchEcologyElevationBandCount;
            const int32 StratumIndex = SideIndex *
                    ZambeziRunnableLaunchEcologyElevationBandCount +
                ElevationBand;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 9101)) /
                static_cast<float>(GroundCoverInstancesPerSide);
            // The launch mosaic begins ahead of the station-75 m camera and
            // continues through the first kilometre. Both morphology families
            // use a 1.2 km HISM cull range, so the far bench remains part of
            // the visible gorge instead of collapsing into one shoreline row.
            const float BaseLogicalX = FMath::Lerp(-2460.0f, -1560.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float BandOffsetMinimumCm = ElevationBand == 0
                ? 1200.0f
                : (ElevationBand == 1 ? 2500.0f : 5000.0f);
            const float BandOffsetMaximumCm = ElevationBand == 0
                ? 24000.0f
                : (ElevationBand == 1 ? 28000.0f : 36000.0f);
            const int32 PatchIndex = AlongIndex / 18;
            const float PatchOffsetT = ZambeziVegetationUnitRandom(
                PatchIndex + SideIndex * 10007 + ElevationBand * 701,
                9109);
            const float IndividualOffsetT = ZambeziVegetationUnitRandom(
                CoverIndex,
                9113);
            const float TargetAdditionalOffset = FMath::Lerp(
                BandOffsetMinimumCm,
                BandOffsetMaximumCm,
                FMath::Pow(
                    0.72f * PatchOffsetT + 0.28f * IndividualOffsetT,
                    1.18f));
            const float TargetSlopeDegrees = FMath::Lerp(
                ElevationBand == 0 ? 3.0f : (ElevationBand == 1 ? 10.0f : 17.0f),
                ElevationBand == 0 ? 18.0f : (ElevationBand == 1 ? 29.0f : 38.0f),
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 9117),
                    1.25f));
            const float TargetDryHeightAboveWaterCm = FMath::Lerp(
                ZambeziRunnableLaunchGroundCoverTargetMinimumDryHeightCm[
                    ElevationBand],
                ZambeziRunnableLaunchGroundCoverTargetMaximumDryHeightCm[
                    ElevationBand],
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 9119),
                    1.18f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + TargetAdditionalOffset));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 256; ++CandidateIndex)
            {
                const int32 CandidateSeedIndex =
                    CoverIndex * 193 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    FMath::Lerp(
                        -140.0f,
                        140.0f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9121));
                const float CandidateAdditionalOffset = FMath::Lerp(
                    BandOffsetMinimumCm,
                    BandOffsetMaximumCm,
                    ZambeziVegetationUnitRandom(
                        CandidateSeedIndex,
                        9127));
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
                        ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziRunnableLaunchGroundCoverBandMinimumDryHeightCm[
                            ElevationBand] ||
                    DryHeightAboveWaterCm >
                        ZambeziRunnableLaunchGroundCoverBandMaximumDryHeightCm[
                            ElevationBand] ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 1500.0f)
                {
                    continue;
                }
                // V19 distributes cover across dry benches and moderate
                // slopes. The former absolute-slope score selected the same
                // flattest contour repeatedly and read as a shoreline ribbon.
                const float PlacementScore =
                    0.72f * FMath::Abs(SlopeDegrees - TargetSlopeDegrees) +
                    0.00150f * FMath::Abs(
                        CandidateAdditionalOffset - TargetAdditionalOffset) +
                    0.00100f * FMath::Abs(
                        DryHeightAboveWaterCm -
                        TargetDryHeightAboveWaterCm) +
                    0.00030f * FMath::Abs(
                        CandidateLogicalX - BaseLogicalX);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchGroundCoverRejectedCount;
                continue;
            }

            const float ElevationBandHeightScale = ElevationBand == 0
                ? 0.76f
                : (ElevationBand == 1 ? 1.0f : 1.18f);
            const float TargetHeightCm = ElevationBandHeightScale * FMath::Lerp(
                55.0f,
                155.0f,
                ZambeziVegetationUnitRandom(CoverIndex, 9133));
            UStaticMesh* GroundCoverMesh = UnderstoryMesh;
            UHierarchicalInstancedStaticMeshComponent* GroundCoverInstances =
                ZambeziRunnableLaunchGroundCoverInstances;
            if ((CoverIndex & 1) != 0)
            {
                GroundCoverMesh = ZambeziGroundCoverMeshB;
                GroundCoverInstances = ZambeziRunnableLaunchGroundCoverInstancesB;
            }
            const float SelectedMeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    GroundCoverMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / SelectedMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.20f,
                2.45f,
                ZambeziVegetationUnitRandom(CoverIndex, 9151));
            const int32 InstanceIndex = AddGroundedInstance(
                GroundCoverInstances,
                GroundCoverMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.07f, 0.0f, 1.7f),
                    360.0f * ZambeziVegetationUnitRandom(CoverIndex, 9161),
                    1.1f * FMath::Sin(static_cast<float>(CoverIndex) * 0.91f)),
                FVector(
                    UniformScale * FootprintScale,
                    UniformScale * FootprintScale * FMath::Lerp(
                        0.80f,
                        1.20f,
                        ZambeziVegetationUnitRandom(CoverIndex, 9173)),
                    UniformScale));
            GroundCoverInstances->SetCustomDataValue(
                InstanceIndex,
                0,
                static_cast<float>(StratumIndex),
                false);
            RunnableLaunchGroundCoverMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchGroundCoverMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++RunnableLaunchGroundCoverPlacedCount;
            ++RunnableLaunchGroundCoverPlacedPerStratum[StratumIndex];
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi runnable-launch bank cover: %d/%d opaque, grounded, "
                 "non-colliding, non-shadow-casting instances across both "
                 "banks; %d candidates rejected by full-route distance, dry "
                 "height, or %.1f-degree slope gates; maximum selected slope "
                 "%.2f degrees.\n"),
            RunnableLaunchGroundCoverPlacedCount,
            ZambeziRunnableLaunchBankCoverInstanceCount,
            RunnableLaunchGroundCoverRejectedCount,
            ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees,
            RunnableLaunchGroundCoverMaximumSlopeDegrees);

        constexpr int32 WoodySpeciesSlotCount = 4;
        const int32 InstancesPerWoodyLane =
            ZambeziRunnableLaunchWoodyInstanceCount /
            (BankSideCount * WoodySpeciesSlotCount);
        for (int32 WoodyIndex = 0;
             WoodyIndex < ZambeziRunnableLaunchWoodyInstanceCount;
             ++WoodyIndex)
        {
            const int32 SpeciesSlot = WoodyIndex % WoodySpeciesSlotCount;
            const int32 SideIndex =
                (WoodyIndex / WoodySpeciesSlotCount) % BankSideCount;
            const int32 AlongIndex = WoodyIndex /
                (WoodySpeciesSlotCount * BankSideCount);
            const int32 ElevationBand = AlongIndex %
                ZambeziRunnableLaunchEcologyElevationBandCount;
            const int32 StratumIndex = SideIndex *
                    ZambeziRunnableLaunchEcologyElevationBandCount +
                ElevationBand;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(WoodyIndex, 9203)) /
                static_cast<float>(InstancesPerWoodyLane);
            // Woody forms begin ahead of the guide camera and fill the first
            // kilometre as a broad dry-bank mosaic instead of a ridge row.
            const float BaseLogicalX = FMath::Lerp(-2360.0f, -1560.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float BandOffsetMinimumCm = ElevationBand == 0
                ? 5000.0f
                : (ElevationBand == 1 ? 5000.0f : 8000.0f);
            const float BandOffsetMaximumCm = ElevationBand == 0
                ? 30000.0f
                : (ElevationBand == 1 ? 30000.0f : 38000.0f);
            const int32 PatchIndex = AlongIndex / 6;
            const float PatchOffsetT = ZambeziVegetationUnitRandom(
                PatchIndex + SideIndex * 12007 +
                    SpeciesSlot * 907 + ElevationBand * 503,
                9207);
            const float TargetAdditionalOffset = FMath::Lerp(
                BandOffsetMinimumCm,
                BandOffsetMaximumCm,
                FMath::Pow(
                    0.68f * PatchOffsetT +
                        0.32f * ZambeziVegetationUnitRandom(
                            WoodyIndex,
                            9211),
                    1.10f));
            const float TargetSlopeDegrees = FMath::Lerp(
                ElevationBand == 0 ? 3.0f : (ElevationBand == 1 ? 9.0f : 15.0f),
                ElevationBand == 0 ? 16.0f : (ElevationBand == 1 ? 25.0f : 32.0f),
                ZambeziVegetationUnitRandom(WoodyIndex, 9217));
            const float TargetDryHeightAboveWaterCm = FMath::Lerp(
                ZambeziRunnableLaunchWoodyTargetMinimumDryHeightCm[
                    ElevationBand],
                ZambeziRunnableLaunchWoodyTargetMaximumDryHeightCm[
                    ElevationBand],
                FMath::Pow(
                    ZambeziVegetationUnitRandom(WoodyIndex, 9219),
                    1.12f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + TargetAdditionalOffset));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 400; ++CandidateIndex)
            {
                const int32 CandidateSeedIndex =
                    WoodyIndex * 257 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    FMath::Lerp(
                        -180.0f,
                        180.0f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9221));
                const float CandidateAdditionalOffset = FMath::Lerp(
                    BandOffsetMinimumCm,
                    BandOffsetMaximumCm,
                    ZambeziVegetationUnitRandom(
                        CandidateSeedIndex,
                        9227));
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
                const float MinimumAdditionalRouteClearanceCm =
                    ElevationBand == 0 ? 3500.0f : 5000.0f;
                if (SlopeDegrees >
                        ZambeziRunnableLaunchWoodySlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziRunnableLaunchWoodyBandMinimumDryHeightCm[
                            ElevationBand] ||
                    DryHeightAboveWaterCm >
                        ZambeziRunnableLaunchWoodyBandMaximumDryHeightCm[
                            ElevationBand] ||
                    FullRouteDistanceCm <
                        ActiveRiverHalfWidth +
                            MinimumAdditionalRouteClearanceCm)
                {
                    continue;
                }
                const float PlacementScore =
                    0.78f * FMath::Abs(
                        SlopeDegrees - TargetSlopeDegrees) +
                    0.00165f * FMath::Abs(
                        CandidateAdditionalOffset - TargetAdditionalOffset) +
                    0.00150f * FMath::Abs(
                        DryHeightAboveWaterCm -
                        TargetDryHeightAboveWaterCm) +
                    0.00035f * FMath::Abs(
                        CandidateLogicalX - BaseLogicalX);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchWoodyRejectedSlopeCount;
                continue;
            }

            UStaticMesh* WoodyMesh = ShrubMesh;
            UHierarchicalInstancedStaticMeshComponent* WoodyInstances =
                ZambeziRunnableLaunchThornScrubInstances;
            bool bWoodyCanopy = false;
            float TargetHeightCm = FMath::Lerp(
                170.0f,
                390.0f,
                ZambeziVegetationUnitRandom(WoodyIndex, 9241));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    ElevationBand == 0 ? 650.0f :
                        (ElevationBand == 1 ? 560.0f : 440.0f),
                    ElevationBand == 0 ? 1120.0f :
                        (ElevationBand == 1 ? 1020.0f : 880.0f),
                    ZambeziVegetationUnitRandom(WoodyIndex, 9257));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    ElevationBand == 0 ? 620.0f :
                        (ElevationBand == 1 ? 540.0f : 420.0f),
                    ElevationBand == 0 ? 1080.0f :
                        (ElevationBand == 1 ? 980.0f : 840.0f),
                    ZambeziVegetationUnitRandom(WoodyIndex, 9277));
                bWoodyCanopy = true;
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(WoodyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            const int32 InstanceIndex = AddGroundedInstance(
                WoodyInstances,
                WoodyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.035f, 0.0f, 1.2f),
                    360.0f * ZambeziVegetationUnitRandom(WoodyIndex, 9283),
                    0.8f * FMath::Sin(static_cast<float>(WoodyIndex) * 0.73f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.18f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 9293)),
                    UniformScale * FMath::Lerp(
                        0.84f,
                        1.16f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 9311)),
                    UniformScale));
            WoodyInstances->SetCustomDataValue(
                InstanceIndex,
                0,
                static_cast<float>(StratumIndex),
                false);
            ++RunnableLaunchWoodyPlacedCount;
            ++RunnableLaunchWoodyPlacedPerStratum[StratumIndex];
            RunnableLaunchWoodyMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchWoodyMaximumSlopeDegrees,
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

        // The centerline bends sharply at the launch. A purely cross-section
        // relative distribution leaves the outside wall behind the camera and
        // concentrates the remaining canopy on a distant skyline. Supplement
        // the two-bank strata with a deterministic, source-grounded patch
        // mosaic sampled through the actual launch view cone. This layer is
        // still dry-bank-only, non-colliding, and presentation-only; it cannot
        // change terrain, water, navigation, collision, or raft forces.
        int32 RunnableLaunchCameraFaceWoodyPlacedCount = 0;
        int32 RunnableLaunchCameraFaceWoodyRejectedCount = 0;
        const FVector2D LaunchViewCenter =
            ResolveLogicalRiverPoint(-2425.0f, 0.0f);
        const FVector2D LaunchViewAhead =
            ResolveLogicalRiverPoint(-2150.0f, 0.0f);
        const FVector2D LaunchViewForward =
            (LaunchViewAhead - LaunchViewCenter).GetSafeNormal();
        const FVector2D LaunchViewRight(
            -LaunchViewForward.Y,
            LaunchViewForward.X);
        for (int32 FaceIndex = 0;
             FaceIndex < ZambeziRunnableLaunchCameraFaceWoodyInstanceCount;
             ++FaceIndex)
        {
            const int32 SpeciesSlot = FaceIndex % WoodySpeciesSlotCount;
            const int32 ElevationBand =
                (FaceIndex / WoodySpeciesSlotCount) %
                ZambeziRunnableLaunchEcologyElevationBandCount;
            const int32 HorizontalLane = FaceIndex % 12;
            const int32 ForwardLane = (FaceIndex / 12) % 5;
            const int32 PatchIndex = FaceIndex / 20;
            const float TargetViewRatio = FMath::Lerp(
                -0.80f,
                0.80f,
                (static_cast<float>(HorizontalLane) +
                    0.22f + 0.56f * ZambeziVegetationUnitRandom(
                        PatchIndex,
                        9341)) /
                    12.0f);
            const float TargetForwardCm = FMath::Lerp(
                9000.0f,
                52000.0f,
                (static_cast<float>(ForwardLane) +
                    0.18f + 0.64f * ZambeziVegetationUnitRandom(
                        PatchIndex,
                        9343)) /
                    5.0f);
            const float TargetSlopeDegrees = FMath::Lerp(
                ElevationBand == 0 ? 4.0f :
                    (ElevationBand == 1 ? 10.0f : 16.0f),
                ElevationBand == 0 ? 17.0f :
                    (ElevationBand == 1 ? 26.0f : 33.0f),
                ZambeziVegetationUnitRandom(FaceIndex, 9349));
            const float TargetDryHeightAboveWaterCm = FMath::Lerp(
                ZambeziRunnableLaunchWoodyTargetMinimumDryHeightCm[
                    ElevationBand],
                ZambeziRunnableLaunchWoodyTargetMaximumDryHeightCm[
                    ElevationBand],
                ZambeziVegetationUnitRandom(FaceIndex, 9353));
            FVector2D BestPoint = LaunchViewCenter;
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestDryHeightAboveWaterCm = 0.0f;
            float BestViewRatio = 0.0f;
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0;
                 CandidateIndex < 320;
                 ++CandidateIndex)
            {
                const int32 CandidateSeedIndex =
                    FaceIndex * 353 + CandidateIndex;
                const float CandidateForwardCm = FMath::Clamp(
                    TargetForwardCm + FMath::Lerp(
                        -7000.0f,
                        7000.0f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9361)),
                    8000.0f,
                    56000.0f);
                const float CandidateViewRatio = FMath::Clamp(
                    TargetViewRatio + FMath::Lerp(
                        -0.20f,
                        0.20f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9371)),
                    -0.90f,
                    0.90f);
                const FVector2D CandidatePoint =
                    LaunchViewCenter +
                    LaunchViewForward * CandidateForwardCm +
                    LaunchViewRight *
                        (CandidateViewRatio * CandidateForwardCm);
                const float CandidateLogicalX =
                    -2425.0f + CandidateForwardCm / 100.0f;
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm =
                    GetLandscapeHeight(CandidatePoint.X, CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                if (SlopeDegrees >
                        ZambeziRunnableLaunchWoodySlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziRunnableLaunchWoodyBandMinimumDryHeightCm[0] ||
                    DryHeightAboveWaterCm >
                        ZambeziRunnableLaunchWoodyBandMaximumDryHeightCm[2] ||
                    FullRouteDistanceCm <
                        ActiveRiverHalfWidth + 3500.0f)
                {
                    continue;
                }
                const float PlacementScore =
                    0.70f * FMath::Abs(
                        SlopeDegrees - TargetSlopeDegrees) +
                    18.0f * FMath::Abs(
                        CandidateViewRatio - TargetViewRatio) +
                    0.00040f * FMath::Abs(
                        CandidateForwardCm - TargetForwardCm) +
                    0.00150f * FMath::Abs(
                        DryHeightAboveWaterCm -
                            TargetDryHeightAboveWaterCm);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestDryHeightAboveWaterCm = DryHeightAboveWaterCm;
                    BestViewRatio = CandidateViewRatio;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchCameraFaceWoodyRejectedCount;
                continue;
            }

            const int32 SideIndex = BestViewRatio < 0.0f ? 0 : 1;
            const int32 ActualElevationBand =
                BestDryHeightAboveWaterCm < 1800.0f
                ? 0
                : (BestDryHeightAboveWaterCm < 5000.0f ? 1 : 2);
            const int32 StratumIndex = SideIndex *
                    ZambeziRunnableLaunchEcologyElevationBandCount +
                ActualElevationBand;
            UStaticMesh* WoodyMesh = ShrubMesh;
            UHierarchicalInstancedStaticMeshComponent* WoodyInstances =
                ZambeziRunnableLaunchThornScrubInstances;
            bool bWoodyCanopy = false;
            float TargetHeightCm = FMath::Lerp(
                240.0f,
                480.0f,
                ZambeziVegetationUnitRandom(FaceIndex, 9383));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    760.0f,
                    1320.0f,
                    ZambeziVegetationUnitRandom(FaceIndex, 9391));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    720.0f,
                    1240.0f,
                    ZambeziVegetationUnitRandom(FaceIndex, 9397));
                bWoodyCanopy = true;
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    WoodyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            const int32 InstanceIndex = AddGroundedInstance(
                WoodyInstances,
                WoodyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(
                        BestSlopeDegrees * 0.03f,
                        0.0f,
                        1.1f),
                    360.0f * ZambeziVegetationUnitRandom(
                        FaceIndex,
                        9403),
                    0.7f * FMath::Sin(
                        static_cast<float>(FaceIndex) * 0.67f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.80f,
                        1.22f,
                        ZambeziVegetationUnitRandom(FaceIndex, 9413)),
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.18f,
                        ZambeziVegetationUnitRandom(FaceIndex, 9419)),
                    UniformScale));
            WoodyInstances->SetCustomDataValue(
                InstanceIndex,
                0,
                static_cast<float>(StratumIndex),
                false);
            ++RunnableLaunchWoodyPlacedCount;
            ++RunnableLaunchCameraFaceWoodyPlacedCount;
            ++RunnableLaunchWoodyPlacedPerStratum[StratumIndex];
            RunnableLaunchWoodyMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchWoodyMaximumSlopeDegrees,
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
            TEXT("Zambezi V19 launch-camera face mosaic: %d/%d opaque, "
                 "source-grounded, non-colliding woody instances; %d "
                 "candidates rejected by view-cone, route-clearance, dry-"
                 "height, or %.1f-degree slope gates.\n"),
            RunnableLaunchCameraFaceWoodyPlacedCount,
            ZambeziRunnableLaunchCameraFaceWoodyInstanceCount,
            RunnableLaunchCameraFaceWoodyRejectedCount,
            ZambeziRunnableLaunchWoodySlopeCeilingDegrees);
        OutSummary += FString::Printf(
            TEXT("Zambezi runnable-launch woody ecology: %d/%d opaque, grounded, "
                 "non-colliding instances; %d candidates rejected by full-route "
                 "distance, dry height, or %.1f-degree slope gates and maximum "
                 "placed slope %.2f degrees.\n"),
            RunnableLaunchWoodyPlacedCount,
            ZambeziRunnableLaunchWoodyInstanceCount +
                ZambeziRunnableLaunchCameraFaceWoodyInstanceCount,
            RunnableLaunchWoodyRejectedSlopeCount,
            ZambeziRunnableLaunchWoodySlopeCeilingDegrees,
            RunnableLaunchWoodyMaximumSlopeDegrees);

        bRunnableLaunchEcologyStrataValidated = true;
        for (int32 StratumIndex = 0;
             StratumIndex < ZambeziRunnableLaunchEcologyStratumCount;
             ++StratumIndex)
        {
            bRunnableLaunchEcologyStrataValidated &=
                RunnableLaunchGroundCoverPlacedPerStratum[StratumIndex] >=
                    ZambeziRunnableLaunchMinimumGroundCoverPerStratum &&
                RunnableLaunchWoodyPlacedPerStratum[StratumIndex] >=
                    ZambeziRunnableLaunchMinimumWoodyPerStratum;
        }
        bRunnableLaunchEcologyStrataValidated &=
            RunnableLaunchCameraFaceWoodyPlacedCount >=
                ZambeziRunnableLaunchMinimumCameraFaceWoodyInstanceCount;
        OutSummary += FString::Printf(
            TEXT("Zambezi V19 ecology strata (left low/mid/high, right "
                 "low/mid/high): cover=[%d,%d,%d,%d,%d,%d] woody="
                 "[%d,%d,%d,%d,%d,%d], minimums=%d/%d validated=%d.\n"),
            RunnableLaunchGroundCoverPlacedPerStratum[0],
            RunnableLaunchGroundCoverPlacedPerStratum[1],
            RunnableLaunchGroundCoverPlacedPerStratum[2],
            RunnableLaunchGroundCoverPlacedPerStratum[3],
            RunnableLaunchGroundCoverPlacedPerStratum[4],
            RunnableLaunchGroundCoverPlacedPerStratum[5],
            RunnableLaunchWoodyPlacedPerStratum[0],
            RunnableLaunchWoodyPlacedPerStratum[1],
            RunnableLaunchWoodyPlacedPerStratum[2],
            RunnableLaunchWoodyPlacedPerStratum[3],
            RunnableLaunchWoodyPlacedPerStratum[4],
            RunnableLaunchWoodyPlacedPerStratum[5],
            ZambeziRunnableLaunchMinimumGroundCoverPerStratum,
            ZambeziRunnableLaunchMinimumWoodyPerStratum,
            bRunnableLaunchEcologyStrataValidated);
    }

    return {RunnableLaunchGroundCoverPlacedCount, RunnableLaunchWoodyPlacedCount, bRunnableLaunchEcologyStrataValidated};
}

int32 AddZambeziWaterlineFringe(const FPlacementContext& Context, const FPlacementQueries& Queries)
{
    // Batoka Gorge in the dry season keeps a green riverine fringe at the
    // waterline (water figs, Syzygium, reeds and shrubs between the basalt
    // boulders and on the beaches) below the dry, leafless slopes. The other
    // L_Zambezi layers start 12-26 m back from the 72 m procedural channel or
    // cover only the launch and camera windows, so the 30 km bank had no
    // waterline vegetation. This places patchy green shrubs and riparian
    // trees within ~15 m of the water along the whole reach (positions and
    // species INFERRED), Landscape-grounded, non-colliding.
    if (!Context.ShrubMesh || !Context.BroadleafTreeMesh)
    {
        return 0;
    }
    const FString RiverId = Context.Candidate.PreviewSpec.RiverId;
    UHierarchicalInstancedStaticMeshComponent* Shrubs = AddLandscapeCandidateInstancedMeshComponent(
        Context.World, Context.ShrubMesh, FString::Printf(TEXT("RaftSim_ZambeziWaterlineFringeShrub_%s"), *RiverId), true);
    UHierarchicalInstancedStaticMeshComponent* Trees = AddLandscapeCandidateInstancedMeshComponent(
        Context.World, Context.BroadleafTreeMesh, FString::Printf(TEXT("RaftSim_ZambeziWaterlineFringeTree_%s"), *RiverId), true);
    if (!Shrubs || !Trees)
    {
        return 0;
    }
    for (UHierarchicalInstancedStaticMeshComponent* Component : {Shrubs, Trees})
    {
        Component->SetCullDistances(0, 120000);
        Component->GetOwner()->Tags.Append(
            {TEXT("RaftSimZambeziWaterlineFringe"), TEXT("InferredVegetationNotSurveyedTrees")});
    }
    constexpr int32 FringeTargetCount = 12000;      // both banks, 30 km
    constexpr float LogicalStart = -2460.0f;
    constexpr float LogicalEnd = 25300.0f;
    const float HalfWidth = Queries.ActiveRiverHalfWidth;
    int32 Placed = 0;
    int32 Rejected = 0;
    int32 PlacedTrees = 0;
    for (int32 Index = 0; Index < FringeTargetCount; ++Index)
    {
        const float Side = Index % 2 == 0 ? -1.0f : 1.0f;
        const int32 AlongIndex = Index / 2;
        const float AlongT = (static_cast<float>(AlongIndex) + ZambeziVegetationUnitRandom(Index, 12301)) /
            static_cast<float>(FringeTargetCount / 2);
        const float BaseLogicalX = FMath::Lerp(LogicalStart, LogicalEnd, AlongT);
        // Patchy, not a hedge: ~40 m patches, about a third of the bank bare
        // basalt boulders between them.
        const int32 PatchIndex = FMath::FloorToInt(BaseLogicalX / 37.0f) * 2 + (Side > 0.0f ? 1 : 0);
        if (ZambeziVegetationUnitRandom(PatchIndex, 12307) < 0.34f)
        {
            continue;
        }
        const bool bTree = ZambeziVegetationUnitRandom(Index, 12311) < 0.14f;
        FVector2D BestPoint = FVector2D::ZeroVector;
        float BestScore = TNumericLimits<float>::Max();
        float BestLogicalX = BaseLogicalX;
        for (int32 Candidate = 0; Candidate < 32; ++Candidate)
        {
            const int32 Seed = Index * 41 + Candidate;
            const float LogicalX = BaseLogicalX + FMath::Lerp(-30.0f, 30.0f, ZambeziVegetationUnitRandom(Seed, 12313));
            // From well inside the procedural 72 m half width (the gorge floor
            // is often narrower) to 30 m beyond it; the water-height test
            // below finds the real edge.
            const float Offset = FMath::Lerp(-3500.0f, 3000.0f, ZambeziVegetationUnitRandom(Seed, 12317));
            const FVector2D Point = Queries.ResolveLogicalRiverPoint(LogicalX, Side * (HalfWidth + Offset));
            const float Slope = Queries.GetLandscapeSlopeDegrees(Point.X, Point.Y);
            const float DryHeightCm = Queries.GetLandscapeHeight(Point.X, Point.Y) -
                Queries.GetConditionedWaterWorldZ(LogicalX);
            const float MinimumDryCm = bTree ? 90.0f : 30.0f;
            const float MaximumDryCm = bTree ? 900.0f : 650.0f;
            if (Slope > 42.0f || DryHeightCm < MinimumDryCm || DryHeightCm > MaximumDryCm ||
                Queries.GetMinimumCenterlineDistanceCm(Point) < 1500.0f)
            {
                continue;
            }
            // Prefer the lowest dry ground: the fringe hugs the waterline.
            const float Score = DryHeightCm / MaximumDryCm + 0.25f * Slope / 42.0f;
            if (Score < BestScore)
            {
                BestScore = Score;
                BestPoint = Point;
                BestLogicalX = LogicalX;
            }
        }
        if (BestScore == TNumericLimits<float>::Max())
        {
            ++Rejected;
            continue;
        }
        const float Yaw = 360.0f * ZambeziVegetationUnitRandom(Index, 12331);
        const float Scale = bTree
            ? FMath::Lerp(0.85f, 1.45f, ZambeziVegetationUnitRandom(Index, 12337))
            : FMath::Lerp(0.75f, 1.6f, ZambeziVegetationUnitRandom(Index, 12341));
        Queries.AddGroundedInstance(
            bTree ? Trees : Shrubs, bTree ? Context.BroadleafTreeMesh : Context.ShrubMesh, BestPoint,
            Queries.GetLandscapeHeight(BestPoint.X, BestPoint.Y) - (bTree ? 30.0f : 15.0f),
            FRotator(0.0f, Yaw, 0.0f), FVector(Scale, Scale, Scale * FMath::Lerp(0.85f, 1.15f,
                ZambeziVegetationUnitRandom(Index, 12347))));
        ++Placed;
        PlacedTrees += bTree ? 1 : 0;
    }
    Context.OutResult.DressingFoliageInstanceCount += Placed;
    Context.OutResult.DressingCanopyTreeInstanceCount += PlacedTrees;
    Context.OutResult.DressingUnderstoryInstanceCount += Placed - PlacedTrees;
    Context.OutSummary += FString::Printf(
        TEXT("%s waterline fringe: %d green riverine shrubs and %d riparian trees within ~15 m of the water "
             "(patchy, positions and species inferred), %d candidates without dry ground near the water.\n"),
        *RiverId, Placed - PlacedTrees, PlacedTrees, Rejected);
    return Placed;
}
}
