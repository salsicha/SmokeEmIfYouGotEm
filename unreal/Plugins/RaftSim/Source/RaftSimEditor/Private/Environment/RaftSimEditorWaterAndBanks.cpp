#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
void DisablePreviewProceduralMeshCollision(AActor* Actor)
{
    if (!Actor)
    {
        return;
    }

    TArray<UProceduralMeshComponent*> MeshComponents;
    Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
    for (UProceduralMeshComponent* MeshComponent : MeshComponents)
    {
        if (MeshComponent)
        {
            MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
    }
}

void AddPreviewSourceMaskedShorelineLipOverhangDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    constexpr int32 SegmentSteps = 18;
    constexpr int32 CrossSteps = 4;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const float WaterSurfaceZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const int32 LipCount = Spec.bDesertCanyon ? 78 : (Spec.bHasWaterfalls ? 104 : 88);
    const FLinearColor InnerWetShadow = Spec.bDesertCanyon
        ? FLinearColor(0.205f, 0.150f, 0.092f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.015f, 0.050f, 0.030f) : FLinearColor(0.055f, 0.082f, 0.060f));
    const FLinearColor LipFaceColor = Spec.bDesertCanyon
        ? FLinearColor(0.365f, 0.245f, 0.145f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.034f, 0.086f, 0.042f) : FLinearColor(0.130f, 0.128f, 0.092f));
    const FLinearColor OuterBankColor = Spec.bDesertCanyon
        ? FLinearColor(0.560f, 0.390f, 0.230f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.128f, 0.052f) : FLinearColor(0.210f, 0.190f, 0.128f));

    for (int32 LipIndex = 0; LipIndex < LipCount; ++LipIndex)
    {
        const float SequenceT = FMath::Frac(0.113f + 0.618034f * static_cast<float>(LipIndex));
        const float Side = (LipIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(LipIndex) * 0.923f + (Spec.bHasWaterfalls ? 0.37f : 0.0f);
        const float BaseX = FMath::Lerp(-5200.0f, 25700.0f, SequenceT) +
            145.0f * FMath::Sin(Phase * 1.41f) +
            62.0f * FMath::Sin(Phase * 0.53f);

        float SelectedX = BaseX;
        float SelectedOffset = ActiveRiverHalfWidth + 32.0f * WetBankScale;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                74.0f * FMath::Sin(Phase * 0.81f + static_cast<float>(CandidateIndex) * 1.13f);
            const float CandidateOffset = ActiveRiverHalfWidth + WetBankScale *
                (-12.0f + 22.0f * static_cast<float>(CandidateIndex) +
                 30.0f * FMath::Abs(FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.71f)));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float EdgePreference = 1.0f -
                FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + 34.0f * WetBankScale)) /
                        FMath::Max(1.0f, 128.0f * WetBankScale),
                    0.0f,
                    1.0f);
            const float WetToePreference = 1.0f - FMath::Clamp(FMath::Abs(WaterT - 0.48f) / 0.52f, 0.0f, 1.0f);
            const float Score = EdgePreference * 1.42f + WetToePreference * 0.42f + WaterT * 0.22f -
                VegetationT * (Spec.bDesertCanyon ? 0.12f : 0.46f) +
                0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.77f);
            if (Score > BestScore)
            {
                BestScore = Score;
                SelectedX = CandidateX;
                SelectedOffset = CandidateOffset;
            }
        }

        const float PatchLength = (Spec.bDesertCanyon ? 720.0f : (Spec.bHasWaterfalls ? 470.0f : 560.0f)) *
            (0.70f + 0.08f * static_cast<float>(LipIndex % 7));
        const float PatchWidth = (Spec.bDesertCanyon ? 116.0f : (Spec.bHasWaterfalls ? 84.0f : 94.0f)) *
            WetBankScale * (0.76f + 0.06f * static_cast<float>(LipIndex % 5));
        const float WaterOverlap = (Spec.bDesertCanyon ? 38.0f : 30.0f) * WetBankScale *
            (0.70f + 0.08f * static_cast<float>(LipIndex % 4));

        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        Normals.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        UVs.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        VertexColors.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        Triangles.Reserve(SegmentSteps * CrossSteps * 6);

        for (int32 SegmentIndex = 0; SegmentIndex <= SegmentSteps; ++SegmentIndex)
        {
            const float U = static_cast<float>(SegmentIndex) / static_cast<float>(SegmentSteps);
            const float LongTaper = FMath::Sin(U * PI);
            const float X = SelectedX - PatchLength * 0.50f + PatchLength * U +
                FMath::Sin(Phase * 0.61f + U * UE_TWO_PI * 1.3f) * PatchWidth * 0.16f * LongTaper;
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float EdgeMeander = WetBankScale *
                (18.0f * FMath::Sin(Phase + U * UE_TWO_PI * 1.15f) +
                 9.0f * FMath::Sin(Phase * 0.33f + U * UE_TWO_PI * 2.70f));

            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float InnerT = 1.0f - V;
                const float CrossOffset = FMath::Lerp(-WaterOverlap, PatchWidth - WaterOverlap, V);
                const float EdgeScallop =
                    FMath::Sin(Phase * 1.19f + U * UE_TWO_PI * 2.2f + V * 3.1f) * PatchWidth * 0.045f +
                    FMath::Sin(Phase * 0.47f + U * UE_TWO_PI * 4.8f) * PatchWidth * 0.026f * InnerT;
                const float Offset = SelectedOffset + EdgeMeander + CrossOffset + EdgeScallop;
                const float Y = CenterY + Side * Offset;
                const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
                const float SourceWaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
                const float SourceVegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
                const float LipCrownT = FMath::Sin(V * PI) * LongTaper;
                const float WetEdgeLift = FMath::Lerp(2.0f, Spec.bDesertCanyon ? 9.0f : 7.0f, V);
                const float LipLift = WetEdgeLift + LipCrownT * (Spec.bDesertCanyon ? 10.0f : 7.5f);
                const float Z = FMath::Max(
                    TerrainZ + LipLift,
                    WaterSurfaceZ + 1.8f + InnerT * (Spec.bDesertCanyon ? 1.7f : 1.2f));
                const float Fleck = FMath::Clamp(
                    0.84f + 0.10f * FMath::Sin(Phase + U * 7.2f) + 0.06f * FMath::Sin(Phase * 0.73f + V * 5.4f),
                    0.66f,
                    1.04f);
                const FLinearColor InnerToFace = FMath::Lerp(InnerWetShadow, LipFaceColor, FMath::Clamp(V * 1.35f, 0.0f, 1.0f));
                FLinearColor LipColor = FMath::Lerp(InnerToFace, OuterBankColor, SmoothPreviewStep(0.48f, 1.0f, V));
                LipColor = FMath::Lerp(
                    LipColor,
                    ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.32f : 0.24f),
                    FMath::Clamp(SourceWaterT * InnerT * 0.28f, 0.0f, 0.30f));
                LipColor = FMath::Lerp(
                    LipColor,
                    ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 0.42f : 0.28f),
                    FMath::Clamp(SourceVegetationT * V * (Spec.bDesertCanyon ? 0.08f : 0.22f), 0.0f, 0.24f));

                Vertices.Add(FVector(X, Y, Z));
                UVs.Add(FVector2D(U * 5.2f, V));
                VertexColors.Add(NormalizePreviewTerrainProxyPatchColor(Spec, ScalePreviewColor(LipColor, Fleck)));
            }
        }

        const int32 RowSize = CrossSteps + 1;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentSteps; ++SegmentIndex)
        {
            for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
            {
                const int32 A = SegmentIndex * RowSize + CrossIndex;
                const int32 B = A + 1;
                const int32 C = (SegmentIndex + 1) * RowSize + CrossIndex;
                const int32 D = C + 1;
                Triangles.Add(A);
                Triangles.Add(C);
                Triangles.Add(B);
                Triangles.Add(B);
                Triangles.Add(C);
                Triangles.Add(D);
            }
        }

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        SoftenPreviewTerrainNormals(Normals, GetPreviewTerrainNormalSofteningBlend(Spec));
        AActor* LipActor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceMaskedShorelineLipOverhang_%03d_%s"), LipIndex, *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            LipFaceColor,
            LoadOrCreatePreviewTerrainVertexColorMaterial(),
            &VertexColors);
        DisablePreviewProceduralMeshCollision(LipActor);
    }
}

void AddPreviewSourceMaskedBankBarMicrogeometryDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const float WaterSurfaceZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const int32 BarPebbleCount = Spec.bDesertCanyon ? 178 : (Spec.bHasWaterfalls ? 150 : 132);
    const int32 SlopeFlakeCount = Spec.bDesertCanyon ? 128 : (Spec.bHasWaterfalls ? 156 : 118);

    for (int32 PebbleIndex = 0; PebbleIndex < BarPebbleCount; ++PebbleIndex)
    {
        const float T = FMath::Frac(0.073f + 0.618034f * static_cast<float>(PebbleIndex));
        const float Side = (PebbleIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(PebbleIndex) * 1.173f;
        const float BaseX = FMath::Lerp(-4200.0f, 25800.0f, T) +
            135.0f * FMath::Sin(Phase * 1.31f) +
            70.0f * FMath::Sin(Phase * 0.47f);

        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * (ActiveRiverHalfWidth + 150.0f * WetBankScale);
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 92.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.07f);
            const float CandidateOffset = ActiveRiverHalfWidth + WetBankScale *
                (70.0f + 58.0f * static_cast<float>(CandidateIndex) +
                 96.0f * FMath::Abs(FMath::Sin(Phase * 0.83f + static_cast<float>(CandidateIndex) * 0.37f)));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float ExposedBarT =
                1.0f - FMath::Clamp(FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + 185.0f * WetBankScale)) /
                                         FMath::Max(1.0f, 320.0f * WetBankScale),
                                     0.0f,
                                     1.0f);
            const float WetToeT = 1.0f - FMath::Clamp(FMath::Abs(WaterT - 0.36f) / 0.54f, 0.0f, 1.0f);
            const float Score = ExposedBarT * 1.30f + WetToeT * 0.36f - VegetationT * (Spec.bHasWaterfalls ? 0.42f : 0.58f) +
                0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.9f);
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float SizeNoise = 0.72f + 0.10f * static_cast<float>(PebbleIndex % 7) +
            0.08f * FMath::Abs(FMath::Sin(Phase));
        const FVector Scale = Spec.bDesertCanyon
            ? FVector(0.105f * SizeNoise, 0.058f * SizeNoise, 0.012f * SizeNoise)
            : FVector(
                  (Spec.bHasWaterfalls ? 0.072f : 0.082f) * SizeNoise,
                  (Spec.bHasWaterfalls ? 0.046f : 0.050f) * SizeNoise,
                  0.010f * SizeNoise);
        const FLinearColor DryBarColor = Spec.bDesertCanyon
            ? FMath::Lerp(FLinearColor(0.44f, 0.31f, 0.20f), FLinearColor(0.62f, 0.48f, 0.31f), 0.32f + 0.16f * FMath::Sin(Phase))
            : (Spec.bHasWaterfalls
                  ? FMath::Lerp(FLinearColor(0.038f, 0.055f, 0.044f), FLinearColor(0.085f, 0.105f, 0.060f), VegetationT * 0.48f)
                  : FMath::Lerp(FLinearColor(0.15f, 0.145f, 0.112f), FLinearColor(0.25f, 0.225f, 0.155f), 0.26f + VegetationT * 0.26f));
        const FLinearColor WetBarColor = FMath::Lerp(
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.45f : 0.38f),
            ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.34f : 0.30f),
            Spec.bDesertCanyon ? 0.24f : 0.42f);
        const FLinearColor BarColor = FMath::Lerp(
            DryBarColor,
            WetBarColor,
            FMath::Clamp(0.18f + WaterT * 0.46f, 0.0f, 0.62f));

        AActor* PebbleActor = AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceMaskedExposedBarMicroPebble_%03d_%s"), PebbleIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(TerrainZ + 5.5f, WaterSurfaceZ + 2.0f)),
            static_cast<float>((PebbleIndex * 31) % 360),
            Scale,
            ScalePreviewColor(BarColor, 0.86f + 0.05f * static_cast<float>(PebbleIndex % 5)),
            PebbleIndex + 9100);
        DisablePreviewProceduralMeshCollision(PebbleActor);
    }

    for (int32 FlakeIndex = 0; FlakeIndex < SlopeFlakeCount; ++FlakeIndex)
    {
        const float T = FMath::Frac(0.191f + 0.618034f * static_cast<float>(FlakeIndex));
        const float Side = (FlakeIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(FlakeIndex) * 1.407f;
        const float BaseX = FMath::Lerp(-4500.0f, 25700.0f, T) +
            180.0f * FMath::Sin(Phase * 0.91f) +
            85.0f * FMath::Sin(Phase * 1.61f);
        const float NearOffset = Spec.bDesertCanyon ? 560.0f : (Spec.bHasWaterfalls ? 360.0f : 380.0f);
        const float FarOffset = Spec.bDesertCanyon ? 2480.0f : (Spec.bHasWaterfalls ? 1180.0f : 1020.0f);

        float X = BaseX;
        float SignedOffset = Side * (ActiveRiverHalfWidth + NearOffset);
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float OffsetWave = FMath::Pow(
                FMath::Abs(FMath::Sin(Phase * 0.59f + static_cast<float>(CandidateIndex) * 0.73f)),
                Spec.bDesertCanyon ? 0.82f : 0.58f);
            const float CandidateOffset = ActiveRiverHalfWidth + NearOffset + FarOffset * OffsetWave;
            const float CandidateX = BaseX + 190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.23f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float SlopeT = SmoothPreviewStep(
                ActiveRiverHalfWidth + NearOffset * 0.60f,
                ActiveRiverHalfWidth + NearOffset + FarOffset * 0.86f,
                CandidateOffset);
            const float Score = Spec.bDesertCanyon
                ? SlopeT * 0.98f + (1.0f - WaterT) * 0.34f - VegetationT * 0.18f
                : SlopeT * 0.56f + VegetationT * (Spec.bHasWaterfalls ? 0.66f : 0.38f) + (1.0f - WaterT) * 0.24f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float SizeNoise = 0.74f + 0.09f * static_cast<float>(FlakeIndex % 6) +
            0.07f * FMath::Abs(FMath::Sin(Phase * 0.77f));
        const FVector Scale = Spec.bDesertCanyon
            ? FVector(0.155f * SizeNoise, 0.036f * SizeNoise, 0.009f * SizeNoise)
            : FVector(
                  (Spec.bHasWaterfalls ? 0.112f : 0.124f) * SizeNoise,
                  (Spec.bHasWaterfalls ? 0.032f : 0.034f) * SizeNoise,
                  0.008f * SizeNoise);
        const FLinearColor SlopeBaseColor = Spec.bDesertCanyon
            ? FMath::Lerp(FLinearColor(0.32f, 0.22f, 0.14f), FLinearColor(0.55f, 0.40f, 0.25f), 0.34f + 0.18f * FMath::Sin(Phase))
            : (Spec.bHasWaterfalls
                  ? FMath::Lerp(FLinearColor(0.030f, 0.055f, 0.035f), FLinearColor(0.065f, 0.135f, 0.055f), VegetationT * 0.58f)
                  : FMath::Lerp(FLinearColor(0.18f, 0.165f, 0.118f), FLinearColor(0.27f, 0.25f, 0.155f), VegetationT * 0.32f));
        const FLinearColor SlopeWetColor = FMath::Lerp(
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.50f : 0.42f),
            ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.26f : 0.24f),
            Spec.bDesertCanyon ? 0.16f : 0.28f);
        const FLinearColor FlakeColor = FMath::Lerp(
            SlopeBaseColor,
            SlopeWetColor,
            FMath::Clamp(WaterT * 0.22f, 0.0f, 0.34f));

        AActor* FlakeActor = AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceMaskedBankSlopeMaterialFlake_%03d_%s"), FlakeIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 9.0f : 7.0f)),
            static_cast<float>((FlakeIndex * 43) % 360),
            Scale,
            ScalePreviewColor(FlakeColor, 0.82f + 0.05f * static_cast<float>(FlakeIndex % 6)),
            FlakeIndex + 11700);
        DisablePreviewProceduralMeshCollision(FlakeActor);
    }
}

void AddPreviewProceduralBankTextureCards(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float RemainingSquareSourceCardCull = 0.54f;
    const float RemainingSquareCardOpacityDemotion = 0.42f;
    const float SquareFoliageSourceCardArtifactDemotion = 0.16f;
    const int32 CardsPerSide = Spec.bDesertCanyon ? 14 : (Spec.bHasWaterfalls ? 18 : 16);
    const float NearBankOffset = Spec.bDesertCanyon ? 520.0f : 260.0f;
    const float FarBankOffset = Spec.bDesertCanyon ? 1880.0f : (Spec.bHasWaterfalls ? 1180.0f : 980.0f);
    const float FoliageCardVisibilityBreakupT = Spec.bHasWaterfalls ? 0.09f : 0.12f;

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        for (int32 CardIndex = 0; CardIndex < CardsPerSide; ++CardIndex)
        {
            const float T = static_cast<float>(CardIndex) / static_cast<float>(FMath::Max(1, CardsPerSide - 1));
            const float Phase = static_cast<float>(CardIndex) * 1.618f + static_cast<float>(SideIndex) * 0.73f;
            const float BaseX = FMath::Lerp(-5050.0f, 25400.0f, T) +
                210.0f * FMath::Sin(Phase * 1.21f) +
                90.0f * FMath::Sin(Phase * 0.37f);
            const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset +
                FarBankOffset * FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.83f)), Spec.bDesertCanyon ? 0.72f : 0.58f);
            float X = BaseX;
            float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
            float BestScore = -1000.0f;
            for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
            {
                const float CandidateX = BaseX +
                    115.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.19f);
                const float CandidateOffset = BaseOffset +
                    Side * 155.0f * FMath::Cos(Phase * 0.67f + static_cast<float>(CandidateIndex) * 1.41f);
                const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
                const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
                const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
                const float Score = Spec.bDesertCanyon
                    ? (0.35f - WaterT * 0.55f + 0.20f * FMath::Sin(Phase + static_cast<float>(CandidateIndex)))
                    : (VegetationT * 1.55f - WaterT * 0.90f +
                          0.06f * FMath::Sin(Phase + static_cast<float>(CandidateIndex)));
                if (Score > BestScore)
                {
                    BestScore = Score;
                    X = CandidateX;
                    Y = CandidateY;
                }
            }

            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
            const bool bCanopyCard =
                Spec.bHasWaterfalls &&
                CardIndex % 13 == 0 &&
                BaseOffset < ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.48f;
            const float Noise = 0.86f + 0.10f * FMath::Sin(Phase * 1.77f) + 0.05f * FMath::Sin(Phase * 0.43f);

            FLinearColor GroundColor;
            if (Spec.bDesertCanyon)
            {
                GroundColor = FMath::Lerp(
                    FLinearColor(0.32f, 0.22f, 0.14f),
                    FLinearColor(0.56f, 0.42f, 0.25f),
                    FMath::Clamp(0.35f + 0.24f * FMath::Sin(Phase * 0.91f), 0.0f, 1.0f));
            }
            else if (Spec.bHasWaterfalls)
            {
                GroundColor = FMath::Lerp(
                    FLinearColor(0.025f, 0.075f, 0.035f),
                    FLinearColor(0.075f, 0.19f, 0.070f),
                    FMath::Clamp(0.28f + VegetationT * 0.64f, 0.0f, 1.0f));
            }
            else
            {
                GroundColor = FMath::Lerp(
                    FLinearColor(0.12f, 0.11f, 0.075f),
                    FLinearColor(0.22f, 0.30f, 0.12f),
                    FMath::Clamp(0.22f + VegetationT * 0.55f, 0.0f, 1.0f));
            }
            GroundColor = FMath::Lerp(
                GroundColor,
                ScalePreviewColor(Spec.WaterColor, 0.45f),
                FMath::Clamp(WaterT * 0.18f, 0.0f, 0.24f));
            GroundColor = ScalePreviewColor(GroundColor, Noise);

            const float Yaw = static_cast<float>((CardIndex * 47 + SideIndex * 113) % 360);
            if (bCanopyCard)
            {
                const FLinearColor CanopyCardColor = ScalePreviewColor(
                    FMath::Lerp(GroundColor, Spec.FoliageColor, Spec.bHasWaterfalls ? 0.62f : 0.48f),
                    (Spec.bHasWaterfalls ? 0.82f : 0.90f) * FoliageCardVisibilityBreakupT);
                AddPreviewOrganicBranchFrondActor(
                    World,
                    FString::Printf(TEXT("RaftSim_MaskAwareCanopyCardOrganicCull_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + 82.0f),
                    Yaw,
                    FVector(
                        (0.32f + 0.08f * FMath::Abs(FMath::Sin(Phase))) * RemainingSquareSourceCardCull,
                        0.30f * RemainingSquareSourceCardCull,
                        0.36f * RemainingSquareSourceCardCull),
                    CanopyCardColor,
                    CardIndex + SideIndex * 97 + 18100,
                    true,
                    true);
            }
            else
            {
                AddPreviewTranslucentMeshActor(
                    World,
                    PlaneMesh,
                    FString::Printf(TEXT("RaftSim_MaskAwareGroundCover_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 18.0f : 15.0f)),
                    FRotator(0.0f, Yaw, 0.0f),
                    FVector(
                        (Spec.bDesertCanyon ? 0.74f : (Spec.bHasWaterfalls ? 0.66f : 0.54f)) *
                            SquareFoliageSourceCardArtifactDemotion,
                        (Spec.bDesertCanyon ? 0.28f : (Spec.bHasWaterfalls ? 0.32f : 0.26f)) * 0.28f,
                        1.0f),
                    GroundColor,
                    (Spec.bDesertCanyon ? 0.09f : (Spec.bHasWaterfalls ? 0.08f : 0.085f)) *
                        RemainingSquareCardOpacityDemotion);
            }
        }
    }
}

void AddPreviewFoamRibbon(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& Color)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 28;
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(Segments * 6);
    UVs.Reserve(Segments * 6);
    VertexColors.Reserve(Segments * 6);
    Triangles.Reserve(Segments * 12);

    const float RibbonMidX = StartX + Length * 0.50f;
    const float RemainingWaterOverlaySlabDemotion = SmoothPreviewStep(5600.0f, 10800.0f, RibbonMidX);
    const float PaleFoamSlashArtifactDemotion = 0.26f;
    const float FoamRailContinuityBreakupT =
        FMath::Lerp(0.62f, 0.42f, RemainingWaterOverlaySlabDemotion);
    const bool bNearFrameWaterRibbon = RibbonMidX < 7800.0f;
    const float NearFrameRibbonWidthScale =
        FMath::Lerp(0.08f, 0.31f, RemainingWaterOverlaySlabDemotion) *
        PaleFoamSlashArtifactDemotion;
    const FLinearColor RibbonColor = ClampPreviewColor(FMath::Lerp(
        Spec.WaterColor,
        Color,
        FMath::Lerp(Spec.bDesertCanyon ? 0.030f : 0.034f, Spec.bDesertCanyon ? 0.18f : 0.16f, RemainingWaterOverlaySlabDemotion) *
            PaleFoamSlashArtifactDemotion));

    auto AddFoamLaceCrossSection = [&](float T, float WidthFade, float SegmentFade) -> int32
    {
        const float X = StartX + Length * T;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Sway = FMath::Sin(Phase + T * UE_TWO_PI) * Width * 0.32f * NearFrameRibbonWidthScale;
        const float Taper = FMath::Sin(T * PI);
        const float LocalHalfWidth =
            FMath::Max(1.1f, Width * NearFrameRibbonWidthScale * (0.10f + 0.50f * Taper) * WidthFade);
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = GetPreviewWaterSurfaceBaseZCm(Spec) + (bNearFrameWaterRibbon ? 5.0f : 12.0f) +
            SurfaceWave + 2.0f * FMath::Sin(Phase * 1.7f + T * PI);

        const int32 BaseVertex = Vertices.Num();
        Vertices.Add(FVector(X, CenterY - LocalHalfWidth, Z));
        Vertices.Add(FVector(X, CenterY + LocalHalfWidth, Z + 0.6f));
        UVs.Add(FVector2D(T, 0.0f));
        UVs.Add(FVector2D(T, 1.0f));
        const FLinearColor LaceColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RibbonColor,
            FMath::Clamp(0.36f + SegmentFade * 0.38f, 0.0f, 0.72f)));
        VertexColors.Add(LaceColor);
        VertexColors.Add(LaceColor);
        return BaseVertex;
    };

    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        const float SegmentStartT = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float SegmentEndT = static_cast<float>(SegmentIndex + 1) / static_cast<float>(Segments);
        const float SegmentMidT = (SegmentStartT + SegmentEndT) * 0.50f;
        const float LacePulse =
            0.50f + 0.50f * FMath::Sin(Phase * 2.17f + SegmentMidT * UE_TWO_PI * 7.0f) +
            0.18f * FMath::Sin(Phase * 0.91f + SegmentMidT * UE_TWO_PI * 19.0f);
        const float SegmentFade = SmoothPreviewStep(FoamRailContinuityBreakupT, 1.10f, LacePulse);
        if (SegmentFade <= 0.02f)
        {
            continue;
        }

        const float EndWidthFade = FMath::Clamp(0.18f + SegmentFade * 0.24f, 0.14f, 0.42f);
        const int32 A = AddFoamLaceCrossSection(SegmentStartT, EndWidthFade, SegmentFade);
        const int32 C = AddFoamLaceCrossSection(SegmentMidT, SegmentFade, SegmentFade);
        const int32 E = AddFoamLaceCrossSection(SegmentEndT, EndWidthFade, SegmentFade);
        const int32 B = A + 1;
        const int32 D = C + 1;
        const int32 F = E + 1;
        Triangles.Add(A);
        Triangles.Add(C);
        Triangles.Add(B);
        Triangles.Add(B);
        Triangles.Add(C);
        Triangles.Add(D);
        Triangles.Add(C);
        Triangles.Add(E);
        Triangles.Add(D);
        Triangles.Add(D);
        Triangles.Add(E);
        Triangles.Add(F);
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty())
    {
        return;
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        RibbonColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewFlowTextureRibbon(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& HighlightColor,
    const FLinearColor& ShadowColor)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 16;
    const float FlowTextureRailArtifactDemotion = 0.34f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float ResidualCenterFlowTextureRibbonCullT =
        SmoothPreviewStep(0.32f, 0.58f, FMath::Abs(LateralOffset) / FMath::Max(1.0f, ActiveRiverHalfWidth));
    const float CenterGuideRibbonDemotion = ResidualCenterFlowTextureRibbonCullT;
    if (CenterGuideRibbonDemotion <= 0.16f)
    {
        return;
    }
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * 2);
    UVs.Reserve((Segments + 1) * 2);
    VertexColors.Reserve((Segments + 1) * 2);
    Triangles.Reserve(Segments * 6);

    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float T = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * T;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Sway =
            FMath::Sin(Phase + T * UE_TWO_PI) * Width * 0.34f +
            FMath::Sin(Phase * 0.67f + T * UE_TWO_PI * 2.0f) * Width * 0.16f;
        const float Taper = FMath::Sin(T * PI);
        const float RemainingWaterOverlaySlabDemotion = SmoothPreviewStep(12600.0f, 19800.0f, X);
        const float NearFrameWaterRibbonDemotion = RemainingWaterOverlaySlabDemotion;
        const float NearFrameWidthScale =
            FMath::Lerp(0.05f, 0.34f, NearFrameWaterRibbonDemotion) * FlowTextureRailArtifactDemotion *
            CenterGuideRibbonDemotion;
        const float LocalHalfWidth = FMath::Max(0.9f, Width * NearFrameWidthScale * (0.10f + 0.30f * Taper));
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = WaterBaseZ + FMath::Lerp(3.0f, 12.0f, NearFrameWaterRibbonDemotion) +
            SurfaceWave + 1.6f * FMath::Sin(Phase * 1.3f + T * PI);
        const float Pulse =
            FMath::Clamp(0.44f + 0.34f * FMath::Sin(Phase + T * UE_TWO_PI * 3.0f) + 0.16f * Taper, 0.0f, 1.0f);
        const FLinearColor RawFlowColor = ClampPreviewColor(FMath::Lerp(ShadowColor, HighlightColor, Pulse));
        const FLinearColor FlowColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RawFlowColor,
            FMath::Lerp(0.025f, 0.28f, NearFrameWaterRibbonDemotion) * FlowTextureRailArtifactDemotion *
                CenterGuideRibbonDemotion));

        Vertices.Add(FVector(X, CenterY - LocalHalfWidth, Z));
        Vertices.Add(FVector(X, CenterY + LocalHalfWidth, Z + 0.7f));
        UVs.Add(FVector2D(T * 5.0f, 0.0f));
        UVs.Add(FVector2D(T * 5.0f, 1.0f));
        VertexColors.Add(ScalePreviewColor(FlowColor, 0.88f + 0.08f * Taper));
        VertexColors.Add(ScalePreviewColor(FlowColor, 0.98f));
    }

    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        const int32 A = SegmentIndex * 2;
        const int32 B = A + 1;
        const int32 C = A + 2;
        const int32 D = A + 3;
        Triangles.Add(A);
        Triangles.Add(C);
        Triangles.Add(B);
        Triangles.Add(B);
        Triangles.Add(C);
        Triangles.Add(D);
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        HighlightColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewFlowBandTextureDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float TextureScale = FMath::Clamp(0.65f * Spec.FlowCurrentCueScale + 0.35f * Spec.FlowFoamScale, 0.45f, 1.45f);
    const int32 BaseRibbonCount = Spec.bDesertCanyon ? 10 : (Spec.bHasWaterfalls ? 16 : 14);
    const int32 RibbonCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseRibbonCount) * FMath::Clamp(TextureScale, 0.55f, 1.35f)));
    const FLinearColor HighlightColor = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.43f, 0.31f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.11f, 0.58f, 0.48f) : FLinearColor(0.15f, 0.64f, 0.62f));
    const FLinearColor ShadowColor = Spec.bDesertCanyon
        ? FLinearColor(0.26f, 0.22f, 0.16f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.025f, 0.28f, 0.22f) : FLinearColor(0.035f, 0.34f, 0.36f));

    for (int32 RibbonIndex = 0; RibbonIndex < RibbonCount; ++RibbonIndex)
    {
        const float T = FMath::Frac(0.127f + 0.6180339f * static_cast<float>(RibbonIndex));
        const float X = FMath::Lerp(8800.0f, 25300.0f, T);
        const float LateralJitter =
            FMath::Sin(static_cast<float>(RibbonIndex) * 1.63f) * ActiveRiverHalfWidth * 0.74f +
            FMath::Sin(static_cast<float>(RibbonIndex) * 0.41f) * ActiveRiverHalfWidth * 0.12f;
        const float Length =
            (Spec.bDesertCanyon ? 420.0f : (Spec.bHasWaterfalls ? 320.0f : 350.0f)) *
            (0.66f + 0.12f * static_cast<float>(RibbonIndex % 5)) * TextureScale;
        const float Width =
            (Spec.bDesertCanyon ? 9.0f : 7.0f) *
            (0.72f + 0.10f * static_cast<float>(RibbonIndex % 4)) *
            FMath::Clamp(TextureScale, 0.70f, 1.22f);
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FlowTextureRibbon_%03d_%s"), RibbonIndex, *Spec.RiverId),
            X - Length * 0.42f,
            Length,
            LateralJitter,
            Width,
            static_cast<float>(RibbonIndex) * 0.77f,
            HighlightColor,
            ShadowColor);
    }
}

void AddPreviewWaterTurbidityPatch(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 14;
    constexpr int32 CrossSteps = 2;
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * (CrossSteps + 1));
    Normals.Reserve((Segments + 1) * (CrossSteps + 1));
    UVs.Reserve((Segments + 1) * (CrossSteps + 1));
    VertexColors.Reserve((Segments + 1) * (CrossSteps + 1));
    Triangles.Reserve(Segments * CrossSteps * 6);

    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float U = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * U;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float LongitudinalTaper = FMath::Sin(U * PI);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Cross = (V - 0.5f) * Width * (0.42f + 0.58f * LongitudinalTaper);
            const float Sway =
                FMath::Sin(Phase + U * UE_TWO_PI) * Width * 0.23f +
                FMath::Sin(Phase * 0.59f + U * UE_TWO_PI * 2.0f) * Width * 0.10f;
            const float CenterY = RiverCenterY + LateralOffset + Sway;
            const float SurfaceWave =
                FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f) +
                FMath::Sin(Phase + U * UE_TWO_PI * 2.4f + V * 1.7f) * (Spec.bDesertCanyon ? 1.2f : 2.4f);
            const float Fleck =
                FMath::Clamp(0.78f + 0.16f * LongitudinalTaper + 0.06f * FMath::Sin(Phase + V * 3.3f), 0.62f, 1.04f);
            Vertices.Add(FVector(X, CenterY + Cross, WaterBaseZ + 17.0f + SurfaceWave));
            UVs.Add(FVector2D(U * 5.0f, V));
            VertexColors.Add(ScalePreviewColor(FMath::Lerp(InnerColor, OuterColor, V), Fleck));
        }
    }

    const int32 RowSize = CrossSteps + 1;
    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = SegmentIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (SegmentIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        InnerColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewWaterSurfaceChopAndTurbidityDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.58f * Spec.FlowCurrentCueScale + 0.42f * Spec.FlowFoamScale, 0.52f, 1.42f);
    const int32 BaseChopCount = Spec.bDesertCanyon ? 22 : (Spec.bHasWaterfalls ? 34 : 28);
    const int32 ChopCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseChopCount) * FMath::Clamp(FlowEnergy, 0.62f, 1.32f)));
    const FLinearColor ChopHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.60f, 0.52f, 0.38f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.18f, 0.66f, 0.55f) : FLinearColor(0.17f, 0.70f, 0.70f));
    const FLinearColor ChopShadow = Spec.bDesertCanyon
        ? FLinearColor(0.32f, 0.27f, 0.20f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.03f, 0.30f, 0.24f) : FLinearColor(0.04f, 0.36f, 0.40f));

    for (int32 ChopIndex = 0; ChopIndex < ChopCount; ++ChopIndex)
    {
        const float T = FMath::Frac(0.211f + 0.381966f * static_cast<float>(ChopIndex));
        const float X = FMath::Lerp(-4400.0f, 25300.0f, T);
        const float Lateral =
            FMath::Sin(static_cast<float>(ChopIndex) * 1.17f) * ActiveRiverHalfWidth * 0.64f +
            FMath::Sin(static_cast<float>(ChopIndex) * 0.37f) * ActiveRiverHalfWidth * 0.16f;
        const float Length =
            (Spec.bDesertCanyon ? 520.0f : 420.0f) *
            (0.72f + 0.16f * static_cast<float>(ChopIndex % 5)) * FlowEnergy;
        const float Width =
            (Spec.bDesertCanyon ? 18.0f : 16.0f) *
            (0.74f + 0.18f * static_cast<float>(ChopIndex % 4)) * FMath::Clamp(FlowEnergy, 0.72f, 1.24f);
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FlowSurfaceChopCrest_%03d_%s"), ChopIndex, *Spec.RiverId),
            X - Length * 0.42f,
            Length,
            Lateral,
            Width,
            static_cast<float>(ChopIndex) * 0.93f,
            ChopHighlight,
            ChopShadow);
    }

    const float TurbidityDepthPatchArtifactDemotion = 0.0f;
    const int32 BaseTurbidityCount = Spec.bDesertCanyon ? 18 : (Spec.bHasWaterfalls ? 22 : 18);
    const int32 TurbidityCount = TurbidityDepthPatchArtifactDemotion > 0.0f
        ? FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseTurbidityCount) * FMath::Clamp(FlowEnergy, 0.70f, 1.20f)))
        : 0;
    const FLinearColor InnerTurbidity = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.52f, 0.40f, 0.26f), 0.58f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.08f, 0.42f, 0.32f), 0.45f)
                               : FMath::Lerp(Spec.WaterColor, FLinearColor(0.07f, 0.52f, 0.54f), 0.38f));
    const FLinearColor OuterTurbidity = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.66f, 0.50f, 0.30f), 0.42f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.55f, 0.38f), 0.36f)
                               : FMath::Lerp(Spec.WaterColor, FLinearColor(0.14f, 0.62f, 0.60f), 0.30f));

    for (int32 PatchIndex = 0; PatchIndex < TurbidityCount; ++PatchIndex)
    {
        const float T = FMath::Frac(0.097f + 0.618034f * static_cast<float>(PatchIndex));
        const float X = FMath::Lerp(-4800.0f, 25000.0f, T);
        const float EdgeBias = (PatchIndex % 3 == 0) ? 0.68f : 0.38f;
        const float Side = (PatchIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral =
            Side * ActiveRiverHalfWidth * EdgeBias +
            FMath::Sin(static_cast<float>(PatchIndex) * 1.53f) * ActiveRiverHalfWidth * 0.18f;
        const float Length =
            (Spec.bDesertCanyon ? 1260.0f : 980.0f) *
            (0.74f + 0.12f * static_cast<float>(PatchIndex % 6)) * FMath::Clamp(FlowEnergy, 0.74f, 1.18f);
        const float Width =
            (Spec.bDesertCanyon ? 88.0f : 74.0f) *
            (0.72f + 0.12f * static_cast<float>(PatchIndex % 5));
        AddPreviewWaterTurbidityPatch(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FlowTurbidityDepthPatch_%03d_%s"), PatchIndex, *Spec.RiverId),
            X - Length * 0.45f,
            Length,
            Lateral,
            Width,
            static_cast<float>(PatchIndex) * 0.71f,
            InnerTurbidity,
            OuterTurbidity);
    }
}

void AddPreviewWaterShaderDepthReflectionScaffoldDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    constexpr int32 XSteps = 92;
    // Odd cross-step count plus center reblending avoids a visible shader-scaffold center rail in review captures.
    constexpr int32 CrossSteps = 13;
    const float NearCameraWaterScaffoldClearanceMinX = 25200.0f;
    const float CentralWaterScaffoldPlateDemotion = 0.12f;
    const float ResidualCenterWaterShaderPlateDemotion = 0.82f;
    const float MinX = NearCameraWaterScaffoldClearanceMinX;
    const float MaxX = 26000.0f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.55f * Spec.FlowCurrentCueScale + 0.45f * Spec.FlowFoamScale, 0.48f, 1.45f);

    const FLinearColor DeepCore = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.19f, 0.20f, 0.16f), 0.32f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.010f, 0.17f, 0.145f), 0.28f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.012f, 0.22f, 0.245f), 0.30f));
    const FLinearColor ShallowTint = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.47f, 0.40f, 0.27f), 0.26f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.055f, 0.36f, 0.25f), 0.25f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.060f, 0.44f, 0.48f), 0.26f));
    const FLinearColor SkyReflection = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.64f, 0.58f, 0.43f), 0.30f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.22f, 0.64f, 0.56f), 0.28f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.24f, 0.66f, 0.68f), 0.30f));
    const FLinearColor BankReflection = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FMath::Lerp(Spec.RockColor, FLinearColor(0.55f, 0.43f, 0.28f), 0.45f), 0.32f)
        : FMath::Lerp(Spec.WaterColor, Spec.FoliageColor, Spec.bHasWaterfalls ? 0.22f : 0.18f);

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
    Normals.Reserve((XSteps + 1) * (CrossSteps + 1));
    UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
    VertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
    Triangles.Reserve(XSteps * CrossSteps * 6);

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width = ActiveRiverHalfWidth *
            (Spec.bDesertCanyon ? 0.28f : 0.24f) *
            CentralWaterScaffoldPlateDemotion *
            (0.95f + 0.05f * FMath::Sin(X * 0.0012f));
        const float LongitudinalFeather = SmoothPreviewStep(0.0f, 0.13f, U);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.22f);
            const float DeepT = 1.0f - FMath::Clamp(EdgeT, 0.0f, 1.0f);
            const float CenterFeather = SmoothPreviewStep(0.0f, 0.72f, DeepT);
            const float ResidualCenterShaderScaffoldEraseT = SmoothPreviewStep(0.72f, 0.99f, DeepT);
            const float FlowLine =
                FMath::Clamp(
                    0.48f + 0.28f * FMath::Sin(X * 0.0039f - Lateral * 0.0068f) +
                        0.18f * FMath::Sin(X * 0.011f + Lateral * 0.0032f),
                    0.0f,
                    1.0f);
            const float FresnelEdge = FMath::Pow(FMath::Clamp(EdgeT, 0.0f, 1.0f), 2.15f);
            const float ReflectionT = FMath::Clamp(
                ((0.055f + 0.085f * FlowLine) * FlowEnergy + FresnelEdge * 0.060f) *
                    LongitudinalFeather *
                    CentralWaterScaffoldPlateDemotion *
                    (1.0f - ResidualCenterShaderScaffoldEraseT * ResidualCenterWaterShaderPlateDemotion),
                0.0f,
                0.040f);
            FLinearColor WaterColor = FMath::Lerp(ShallowTint, DeepCore, DeepT);
            WaterColor = FMath::Lerp(
                WaterColor,
                BankReflection,
                FMath::Clamp(FresnelEdge * 0.075f * CentralWaterScaffoldPlateDemotion, 0.0f, 0.040f));
            WaterColor = FMath::Lerp(WaterColor, SkyReflection, ReflectionT);
            WaterColor = FMath::Lerp(
                WaterColor,
                Spec.WaterColor,
                FMath::Clamp(
                    0.72f + 0.12f * (1.0f - CenterFeather) +
                        0.06f * FMath::Sin(X * 0.0023f + Lateral * 0.0051f),
                    0.64f,
                    0.90f));
            WaterColor = FMath::Lerp(
                WaterColor,
                Spec.WaterColor,
                FMath::Clamp(ResidualCenterShaderScaffoldEraseT * ResidualCenterWaterShaderPlateDemotion * 0.42f, 0.0f, 0.36f));

            const float SurfaceWave =
                (FMath::Sin(X * 0.011f + Lateral * 0.015f) * (Spec.bDesertCanyon ? 1.2f : 2.4f) +
                 FMath::Sin(X * 0.018f - Lateral * 0.006f) * (Spec.bDesertCanyon ? 0.5f : 0.9f)) *
                LongitudinalFeather *
                (1.0f - ResidualCenterShaderScaffoldEraseT * ResidualCenterWaterShaderPlateDemotion * 0.32f);
            Vertices.Add(FVector(X, CenterY + Lateral, WaterBaseZ + 3.6f + SurfaceWave));
            UVs.Add(FVector2D(U * 22.0f, V));
            VertexColors.Add(ClampPreviewColor(WaterColor));
        }
    }

    const int32 RowSize = CrossSteps + 1;
    for (int32 XIndex = 0; XIndex < XSteps; ++XIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = XIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (XIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_WaterShaderDepthReflectionScaffold_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.WaterColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);

    const int32 ReflectionRibbonCount = Spec.bDesertCanyon ? 2 : (Spec.bHasWaterfalls ? 3 : 3);
    for (int32 ReflectionIndex = 0; ReflectionIndex < ReflectionRibbonCount; ++ReflectionIndex)
    {
        const float T = FMath::Frac(0.081f + 0.618034f * static_cast<float>(ReflectionIndex));
        const float X = FMath::Lerp(NearCameraWaterScaffoldClearanceMinX, 25300.0f, T);
        const float Side = (ReflectionIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral = Side * ActiveRiverHalfWidth * (0.58f + 0.22f * FMath::Sin(static_cast<float>(ReflectionIndex) * 0.73f));
        const float Length =
            (Spec.bDesertCanyon ? 560.0f : 440.0f) *
            (0.72f + 0.12f * static_cast<float>(ReflectionIndex % 5)) * FMath::Clamp(FlowEnergy, 0.68f, 1.22f);
        const float Width =
            (Spec.bDesertCanyon ? 9.0f : 7.0f) *
            (0.74f + 0.10f * static_cast<float>(ReflectionIndex % 4));
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaterShaderFresnelBankReflection_%03d_%s"), ReflectionIndex, *Spec.RiverId),
            X - Length * 0.44f,
            Length,
            Lateral,
            Width,
            static_cast<float>(ReflectionIndex) * 0.67f,
            FMath::Lerp(Spec.WaterColor, SkyReflection, 0.48f),
            FMath::Lerp(Spec.WaterColor, BankReflection, 0.44f));
    }

    const int32 RefractionSeamCount = 0;
    for (int32 SeamIndex = 0; SeamIndex < RefractionSeamCount; ++SeamIndex)
    {
        const float T = FMath::Frac(0.143f + 0.414214f * static_cast<float>(SeamIndex));
        const float X = FMath::Lerp(NearCameraWaterScaffoldClearanceMinX, 24800.0f, T);
        const float Side = (SeamIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral = Side * ActiveRiverHalfWidth * (0.28f + 0.32f * FMath::Abs(FMath::Sin(static_cast<float>(SeamIndex) * 0.89f)));
        const FLinearColor SeamHighlight = Spec.bDesertCanyon
            ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.58f, 0.50f, 0.34f), 0.34f)
            : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.55f, 0.42f), 0.32f)
                                    : FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.58f, 0.58f), 0.34f));
        const FLinearColor SeamShadow = Spec.bDesertCanyon
            ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.27f, 0.23f, 0.16f), 0.30f)
            : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.020f, 0.22f, 0.17f), 0.28f)
                                    : FMath::Lerp(Spec.WaterColor, FLinearColor(0.025f, 0.27f, 0.29f), 0.30f));
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaterShaderRefractionSeam_%03d_%s"), SeamIndex, *Spec.RiverId),
            X - 170.0f,
            Spec.bDesertCanyon ? 360.0f : 300.0f,
            Lateral,
            Spec.bDesertCanyon ? 4.5f : 3.5f,
            static_cast<float>(SeamIndex) * 0.91f,
            SeamHighlight,
            SeamShadow);
    }
}

void AddPreviewShallowWaterClarityAndAerationDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* WaterMask,
    UStaticMesh* PlaneMesh)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 156;
    constexpr int32 CrossSteps = 4;
    const float ShallowWaterEdgeBandDemotion = 0.20f;
    const float ShallowEdgeRailArtifactDemotion = 0.30f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.52f * Spec.FlowCurrentCueScale + 0.48f * Spec.FlowFoamScale, 0.52f, 1.48f);

    const FLinearColor CoreTint = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.34f, 0.30f, 0.22f), 0.30f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.020f, 0.25f, 0.19f), 0.26f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.030f, 0.36f, 0.38f), 0.24f));
    const FLinearColor ShallowBedTint = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.34f, 0.23f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.13f, 0.075f) : FLinearColor(0.075f, 0.25f, 0.22f));
    const FLinearColor AeratedTint = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.47f, 0.35f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.22f, 0.52f, 0.39f) : FLinearColor(0.24f, 0.54f, 0.52f));

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve((Segments + 1) * (CrossSteps + 1));
        Normals.Reserve((Segments + 1) * (CrossSteps + 1));
        UVs.Reserve((Segments + 1) * (CrossSteps + 1));
        VertexColors.Reserve((Segments + 1) * (CrossSteps + 1));
        Triangles.Reserve(Segments * CrossSteps * 6);

        for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
        {
            const float U = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
            const float X = FMath::Lerp(8600.0f, 25800.0f, U);
            const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
            const float Width = ActiveRiverHalfWidth *
                (0.98f + 0.055f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.14f : 0.04f));
            const float LongitudinalFeather = FMath::Clamp(
                SmoothPreviewStep(0.0f, 0.055f, U) * (1.0f - SmoothPreviewStep(0.965f, 1.0f, U)),
                0.0f,
                1.0f);
            const float NearFrameShallowWaterBandDemotion = SmoothPreviewStep(10800.0f, 16800.0f, X);
            const float BandInnerEdge = FMath::Lerp(0.993f, 0.986f, NearFrameShallowWaterBandDemotion);
            const float BandOuterEdge = FMath::Lerp(0.997f, 0.993f, NearFrameShallowWaterBandDemotion);

            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float EdgeT = FMath::Pow(FMath::Clamp(V, 0.0f, 1.0f), 1.12f);
                const float Lateral = Side * FMath::Lerp(Width * BandInnerEdge, Width * BandOuterEdge, EdgeT);
                const float Sway =
                    Side * (FMath::Sin(X * 0.0049f + EdgeT * 2.2f) * 18.0f +
                            FMath::Sin(X * 0.013f + static_cast<float>(SideIndex) * 1.7f) * 8.0f) *
                    LongitudinalFeather;
                const float Y = RiverCenterY + Lateral + Sway;
                const float SourceWaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
                const float Mottle =
                    FMath::Clamp(
                        0.50f + 0.24f * FMath::Sin(X * 0.0063f + EdgeT * 3.1f) +
                            0.18f * FMath::Sin(X * 0.017f - EdgeT * 5.2f),
                        0.0f,
                        1.0f);
                const float BedRevealT =
                    FMath::Clamp(0.025f + EdgeT * 0.055f + (1.0f - SourceWaterT) * 0.020f + Mottle * 0.018f, 0.0f, 0.12f);
                const float AerationT =
                    FMath::Clamp((0.006f + 0.010f * FlowEnergy) * (1.0f - EdgeT * 0.70f) * Mottle, 0.0f, 0.016f);
                FLinearColor WaterColor = FMath::Lerp(CoreTint, ShallowBedTint, BedRevealT);
                WaterColor = FMath::Lerp(WaterColor, AeratedTint, AerationT);
                WaterColor = FMath::Lerp(WaterColor, Spec.WaterColor, FMath::Clamp(0.82f + SourceWaterT * 0.10f, 0.80f, 0.94f));
                WaterColor = FMath::Lerp(
                    Spec.WaterColor,
                    WaterColor,
                    FMath::Lerp(0.003f, 0.018f, NearFrameShallowWaterBandDemotion) *
                        LongitudinalFeather *
                        ShallowWaterEdgeBandDemotion *
                        ShallowEdgeRailArtifactDemotion);

                const float SurfaceWave =
                    (FMath::Sin(X * 0.012f + EdgeT * 2.7f) * (Spec.bDesertCanyon ? 1.4f : 2.6f) +
                     FMath::Sin(X * 0.023f - EdgeT * 4.1f) * (Spec.bDesertCanyon ? 0.7f : 1.2f)) *
                    LongitudinalFeather;
                Vertices.Add(FVector(X, Y, WaterBaseZ + 3.6f + SurfaceWave));
                UVs.Add(FVector2D(U * 18.0f, V));
                VertexColors.Add(ClampPreviewColor(WaterColor));
            }
        }

        const int32 RowSize = CrossSteps + 1;
        for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
        {
            for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
            {
                const int32 A = SegmentIndex * RowSize + CrossIndex;
                const int32 B = A + 1;
                const int32 C = (SegmentIndex + 1) * RowSize + CrossIndex;
                const int32 D = C + 1;
                Triangles.Add(A);
                Triangles.Add(C);
                Triangles.Add(B);
                Triangles.Add(B);
                Triangles.Add(C);
                Triangles.Add(D);
            }
        }

        Normals.SetNum(Vertices.Num());
        for (FVector& Normal : Normals)
        {
            Normal = FVector::UpVector;
        }
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(
                TEXT("RaftSim_ShallowWaterClarityBand_%s_%s"),
                Side < 0.0f ? TEXT("Left") : TEXT("Right"),
                *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            CoreTint,
            LoadOrCreatePreviewWaterVertexColorMaterial(),
            &VertexColors);
    }

    if (!PlaneMesh)
    {
        return;
    }

    const int32 BaseBubbleCount = Spec.bDesertCanyon ? 42 : (Spec.bHasWaterfalls ? 96 : 72);
    const int32 BubbleCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseBubbleCount) * FMath::Clamp(FlowEnergy, 0.70f, 1.26f)));
    const FLinearColor BubbleColor = Spec.bDesertCanyon
        ? FLinearColor(0.72f, 0.68f, 0.54f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.72f, 0.92f, 0.80f, 1.0f) : FLinearColor(0.76f, 0.92f, 0.88f, 1.0f));

    for (int32 BubbleIndex = 0; BubbleIndex < BubbleCount; ++BubbleIndex)
    {
        const float T = FMath::Frac(0.059f + 0.6180339f * static_cast<float>(BubbleIndex));
        const float X = FMath::Lerp(-4300.0f, 25000.0f, T);
        const float Side = (BubbleIndex % 2 == 0) ? -1.0f : 1.0f;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width = ActiveRiverHalfWidth *
            (0.96f + 0.06f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.14f : 0.04f));
        const float EdgeLane = 0.48f + 0.36f * FMath::Abs(FMath::Sin(static_cast<float>(BubbleIndex) * 1.31f));
        const float Lateral = Side * Width * EdgeLane +
            FMath::Sin(static_cast<float>(BubbleIndex) * 2.17f) * Width * 0.08f;
        const float SourceWaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, RiverCenterY + Lateral);
        const float NearFrameBubbleDemotion = SmoothPreviewStep(2200.0f, 7600.0f, X);
        const float Opacity =
            (Spec.bDesertCanyon ? 0.070f : (Spec.bHasWaterfalls ? 0.145f : 0.110f)) *
            FMath::Clamp(0.74f + SourceWaterT * 0.42f + FlowEnergy * 0.18f, 0.55f, 1.25f) *
            FMath::Lerp(0.20f, 1.0f, NearFrameBubbleDemotion);
        const float LengthScale =
            (Spec.bDesertCanyon ? 0.14f : 0.11f) *
            (0.70f + 0.10f * static_cast<float>(BubbleIndex % 5)) *
            FMath::Lerp(0.42f, 1.0f, NearFrameBubbleDemotion);
        const float WidthScale =
            (Spec.bDesertCanyon ? 0.026f : 0.022f) *
            (0.74f + 0.10f * static_cast<float>(BubbleIndex % 4)) *
            FMath::Lerp(0.50f, 1.0f, NearFrameBubbleDemotion);

        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_ShallowWaterAerationBubbleLace_%03d_%s"), BubbleIndex, *Spec.RiverId),
            FVector(
                X,
                RiverCenterY + Lateral,
                WaterBaseZ + 27.0f + 1.8f * FMath::Sin(static_cast<float>(BubbleIndex) * 0.73f)),
            FRotator(0.0f, static_cast<float>((BubbleIndex * 23) % 360), 0.0f),
            FVector(LengthScale, WidthScale, 1.0f),
            BubbleColor,
            Opacity);
    }
}

void AddPreviewFoamAndHydraulics(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FoamScale = FMath::Max(0.35f, Spec.FlowFoamScale);
    const int32 FlowAwareFoamTrainCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(Spec.FoamTrainCount) * FMath::Clamp(FoamScale, 0.5f, 1.35f)));

    for (int32 FoamIndex = 0; FoamIndex < FlowAwareFoamTrainCount; ++FoamIndex)
    {
        const float X = -4050.0f + static_cast<float>(FoamIndex) * (28000.0f / FMath::Max(1, FlowAwareFoamTrainCount));
        const float Offset = FMath::Sin(static_cast<float>(FoamIndex) * 1.7f) * ActiveRiverHalfWidth * 0.42f;
        const float Length = (Spec.bDesertCanyon ? 1420.0f : 1050.0f) * FoamScale;
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FoamTongue_%02d_%s"), FoamIndex, *Spec.RiverId),
            X - Length * 0.48f,
            Length,
            Offset,
            (54.0f + 12.0f * static_cast<float>(FoamIndex % 3)) * FoamScale,
            static_cast<float>(FoamIndex) * 0.83f,
            FLinearColor(0.82f, 0.90f, 0.86f));
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaveHighlight_%02d_%s"), FoamIndex, *Spec.RiverId),
            X - Length * 0.26f,
            Length * 0.55f,
            Offset * 0.55f,
            (22.0f + 5.0f * static_cast<float>(FoamIndex % 2)) * FoamScale,
            static_cast<float>(FoamIndex) * 1.19f + 0.4f,
            Spec.bDesertCanyon ? FLinearColor(0.78f, 0.82f, 0.76f) : FLinearColor(0.72f, 0.88f, 0.84f));

        if (!Spec.bDesertCanyon && FoamIndex % 3 == 0)
        {
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_EddyLine_%02d_%s"), FoamIndex, *Spec.RiverId),
                X + 80.0f,
                720.0f * FoamScale,
                ActiveRiverHalfWidth * 0.76f,
                18.0f * FoamScale,
                static_cast<float>(FoamIndex) * 0.47f,
                FLinearColor(0.88f, 0.94f, 0.90f));
        }
    }
}

void AddPreviewFlowDependentHydraulicAerationAndSprayDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    UStaticMesh* PlaneMesh,
    UStaticMesh* SphereMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.54f * Spec.FlowFoamScale + 0.46f * Spec.FlowCurrentCueScale, 0.46f, 1.42f);
    const int32 BaseHydraulicCount = Spec.bDesertCanyon ? 12 : (Spec.bHasWaterfalls ? 24 : 18);
    const int32 HydraulicCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseHydraulicCount) * FMath::Clamp(FlowEnergy, 0.58f, 1.28f)));
    const float HazardReadabilityOpacityLimit = Spec.bDesertCanyon ? 0.080f : (Spec.bHasWaterfalls ? 0.115f : 0.105f);
    const float WaterOverlaySlabOpacityDemotion = 0.54f;
    const FLinearColor AerationCore = Spec.bDesertCanyon
        ? FLinearColor(0.70f, 0.67f, 0.53f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.78f, 0.96f, 0.84f, 1.0f) : FLinearColor(0.80f, 0.94f, 0.88f, 1.0f));
    const FLinearColor AerationShadow = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.48f, 0.42f, 0.30f, 1.0f), 0.42f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.18f, 0.52f, 0.36f, 1.0f), 0.38f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.24f, 0.60f, 0.56f, 1.0f), 0.34f));

    for (int32 HydraulicIndex = 0; HydraulicIndex < HydraulicCount; ++HydraulicIndex)
    {
        const float SequenceT = static_cast<float>(HydraulicIndex) / static_cast<float>(FMath::Max(1, HydraulicCount - 1));
        const float Phase = static_cast<float>(HydraulicIndex) * 1.6180339f;
        const float BaseX =
            FMath::Lerp(3600.0f, 25000.0f, FMath::Frac(0.089f + SequenceT * 0.94f + 0.031f * FMath::Sin(Phase)));
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, BaseX);
        float BestLateral = 0.0f;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidatePhase = Phase + static_cast<float>(CandidateIndex) * 0.73f;
            const float Side = ((HydraulicIndex + CandidateIndex) % 2 == 0) ? -1.0f : 1.0f;
            const float CenterHydraulicLaneMinimum = 0.34f;
            const float LaneBias = (HydraulicIndex % 5 == 0)
                ? CenterHydraulicLaneMinimum
                : (CenterHydraulicLaneMinimum + 0.44f * FMath::Abs(FMath::Sin(CandidatePhase * 0.91f)));
            const float CandidateX = BaseX + 190.0f * FMath::Sin(CandidatePhase * 1.19f);
            const float CandidateLateral =
                Side * ActiveRiverHalfWidth * LaneBias +
                FMath::Sin(CandidatePhase * 1.71f) * ActiveRiverHalfWidth * 0.10f;
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + CandidateLateral;
            const float SourceWaterT = WaterMask ? SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY) : 0.78f;
            const float CenterLaneT =
                1.0f - FMath::Clamp(FMath::Abs(CandidateLateral) / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f);
            const float HydraulicPulse =
                0.50f + 0.36f * FMath::Sin(CandidatePhase * 1.37f) + 0.14f * FMath::Sin(CandidateX * 0.004f);
            const float Score = SourceWaterT * 0.58f + CenterLaneT * 0.26f + HydraulicPulse * 0.18f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
                BestLateral = CandidateLateral;
            }
        }

        const float NearFrameDemotion = SmoothPreviewStep(7600.0f, 12600.0f, X);
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float EdgeT = FMath::Clamp(FMath::Abs(BestLateral) / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f);
        const float FlowPulse =
            FMath::Clamp(0.58f + 0.23f * FMath::Sin(Phase * 1.11f) + 0.16f * FMath::Sin(X * 0.0061f), 0.34f, 0.98f);
        const float MatLengthCm =
            (Spec.bDesertCanyon ? 430.0f : (Spec.bHasWaterfalls ? 340.0f : 380.0f)) *
            (0.74f + 0.16f * static_cast<float>(HydraulicIndex % 5)) *
            FMath::Clamp(FlowEnergy, 0.68f, 1.18f) *
            FMath::Lerp(0.28f, 0.78f, NearFrameDemotion);
        const float MatWidthCm =
            (Spec.bDesertCanyon ? 64.0f : (Spec.bHasWaterfalls ? 78.0f : 70.0f)) *
            (0.72f + 0.12f * static_cast<float>(HydraulicIndex % 4)) *
            FMath::Clamp(0.86f + (1.0f - EdgeT) * 0.22f, 0.74f, 1.14f) *
            FMath::Lerp(0.34f, 0.72f, NearFrameDemotion);
        const float Opacity =
            FMath::Clamp(
                HazardReadabilityOpacityLimit *
                    FMath::Clamp(0.56f + FlowPulse * 0.40f + FlowEnergy * 0.16f, 0.48f, 1.10f) *
                    FMath::Lerp(0.18f, 0.72f, NearFrameDemotion) *
                    WaterOverlaySlabOpacityDemotion,
                0.010f,
                HazardReadabilityOpacityLimit);
        const FLinearColor RawMatColor = ClampPreviewColor(FMath::Lerp(
            FMath::Lerp(Spec.WaterColor, AerationShadow, 0.56f),
            AerationCore,
            FMath::Clamp(0.28f + FlowPulse * 0.48f + (1.0f - EdgeT) * 0.10f, 0.0f, 0.84f)));
        const FLinearColor MatColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RawMatColor,
            FMath::Lerp(0.10f, 0.52f, NearFrameDemotion)));
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_FlowDependentHydraulicAerationMat_%03d_%s"), HydraulicIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(WaterBaseZ + 32.0f + 3.6f * FMath::Sin(Phase), TerrainZ + 6.0f)),
            FRotator(0.0f, static_cast<float>((HydraulicIndex * 31) % 360), 0.0f),
            FVector(MatLengthCm / 100.0f, MatWidthCm / 100.0f, 1.0f),
            MatColor,
            Opacity);

        if (NearFrameDemotion > 0.18f || HydraulicIndex % 3 == 0)
        {
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_FlowDependentWaveTrainFoamLace_%03d_%s"), HydraulicIndex, *Spec.RiverId),
                X - MatLengthCm * 0.54f,
                MatLengthCm * 0.82f,
                BestLateral + FMath::Sin(Phase * 1.73f) * MatWidthCm * 0.30f,
                FMath::Max(4.0f, MatWidthCm * 0.10f),
                Phase,
                MatColor);
        }

        if (SphereMesh)
        {
            const int32 BaseSprayBeads = Spec.bDesertCanyon ? 1 : (Spec.bHasWaterfalls ? 3 : 2);
            const int32 SprayBeadCount = FMath::Max(
                0,
                FMath::RoundToInt(static_cast<float>(BaseSprayBeads) * FMath::Clamp(FlowEnergy * NearFrameDemotion, 0.28f, 1.18f)));
            for (int32 SprayBeadIndex = 0; SprayBeadIndex < SprayBeadCount; ++SprayBeadIndex)
            {
                const float BeadPhase = Phase + static_cast<float>(SprayBeadIndex) * 1.27f;
                const float BeadX = X + FMath::Sin(BeadPhase * 1.41f) * MatLengthCm * 0.33f;
                const float BeadY = Y + FMath::Cos(BeadPhase * 1.19f) * MatWidthCm * 0.56f;
                const float BeadLift =
                    (Spec.bDesertCanyon ? 28.0f : (Spec.bHasWaterfalls ? 58.0f : 40.0f)) *
                    (0.72f + 0.16f * static_cast<float>(SprayBeadIndex)) *
                    FMath::Clamp(FlowEnergy, 0.60f, 1.16f);
                const float BeadScale =
                    (Spec.bDesertCanyon ? 0.020f : (Spec.bHasWaterfalls ? 0.030f : 0.025f)) *
                    (0.78f + 0.10f * static_cast<float>((HydraulicIndex + SprayBeadIndex) % 4));
                AddPreviewTranslucentMeshActor(
                    World,
                    SphereMesh,
                    FString::Printf(
                        TEXT("RaftSim_FlowDependentSprayBead_%03d_%02d_%s"),
                        HydraulicIndex,
                        SprayBeadIndex,
                        *Spec.RiverId),
                    FVector(BeadX, BeadY, FMath::Max(WaterBaseZ + 44.0f + BeadLift, TerrainZ + 16.0f)),
                    FRotator::ZeroRotator,
                    FVector(BeadScale, BeadScale, BeadScale),
                    MatColor,
                    FMath::Clamp(Opacity * (Spec.bHasWaterfalls ? 0.82f : 0.66f), 0.025f, 0.155f));
            }
        }
    }
}

void AddPreviewWaterSurfaceDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const FLinearColor CurrentHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.38f, 0.31f, 0.21f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.05f, 0.39f, 0.32f) : FLinearColor(0.07f, 0.46f, 0.49f));
    const FLinearColor CurrentShadow = Spec.bDesertCanyon
        ? FLinearColor(0.30f, 0.24f, 0.17f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.03f, 0.31f, 0.25f) : FLinearColor(0.04f, 0.36f, 0.39f));
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float CurrentCueScale = FMath::Max(0.35f, Spec.FlowCurrentCueScale);
    const float CurrentStreakNearFrameStartX = 13800.0f;
    const float CurrentStreakLengthScale = 0.15f;
    const float CurrentStreakArtifactDemotion = 0.0f;
    const int32 BaseCurrentCount = Spec.bDesertCanyon ? 2 : (Spec.bHasWaterfalls ? 3 : 3);
    const int32 CurrentCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseCurrentCount) * FMath::Clamp(CurrentCueScale, 0.5f, 1.3f)));
    for (int32 CurrentIndex = 0; CurrentIndex < CurrentCount; ++CurrentIndex)
    {
        const float X = FMath::Lerp(
            CurrentStreakNearFrameStartX,
            23800.0f,
            static_cast<float>(CurrentIndex) / static_cast<float>(FMath::Max(1, CurrentCount - 1)));
        const float SideBias = (CurrentIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral =
            (SideBias * 0.18f + FMath::Sin(static_cast<float>(CurrentIndex) * 1.37f) * 0.18f) *
            ActiveRiverHalfWidth;
        const float Length = (Spec.bDesertCanyon ? 1380.0f : 980.0f) * CurrentCueScale * CurrentStreakLengthScale;
        const FLinearColor DetailColor =
            ClampPreviewColor(FMath::Lerp(
                Spec.WaterColor,
                FMath::Lerp(CurrentShadow, CurrentHighlight, 0.50f + 0.18f * FMath::Sin(static_cast<float>(CurrentIndex) * 0.91f)),
                0.20f * CurrentStreakArtifactDemotion));
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_CurrentStreak_%02d_%s"), CurrentIndex, *Spec.RiverId),
            X,
            Length,
            Lateral,
            (2.6f + 0.9f * static_cast<float>(CurrentIndex % 3)) * CurrentCueScale,
            static_cast<float>(CurrentIndex) * 0.61f,
            DetailColor,
            FMath::Lerp(Spec.WaterColor, DetailColor, 0.18f * CurrentStreakArtifactDemotion));
    }
}

void AddPreviewWaterMicroRippleGlintDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec, UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.55f * Spec.FlowCurrentCueScale + 0.45f * Spec.FlowFoamScale, 0.55f, 1.45f);
    const int32 BaseRippleCount = Spec.bDesertCanyon ? 86 : (Spec.bHasWaterfalls ? 132 : 112);
    const int32 RippleCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseRippleCount) * FMath::Clamp(FlowEnergy, 0.68f, 1.28f)));

    const FLinearColor BrightGlint = Spec.bDesertCanyon
        ? FLinearColor(0.78f, 0.70f, 0.52f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.48f, 0.92f, 0.76f, 1.0f) : FLinearColor(0.52f, 0.92f, 0.92f, 1.0f));
    const float DarkMicroRippleArtifactDemotion = 0.0f;
    const FLinearColor RawDarkRipple = Spec.bDesertCanyon
        ? FLinearColor(0.26f, 0.24f, 0.17f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.22f, 0.17f, 1.0f) : FLinearColor(0.025f, 0.27f, 0.30f, 1.0f));
    const FLinearColor DarkRipple =
        FMath::Lerp(Spec.WaterColor, RawDarkRipple, DarkMicroRippleArtifactDemotion);
    const FLinearColor BankTint = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.40f, 0.26f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.11f, 0.36f, 0.24f, 1.0f) : FLinearColor(0.12f, 0.42f, 0.38f, 1.0f));
    for (int32 RippleIndex = 0; RippleIndex < RippleCount; ++RippleIndex)
    {
        const float SequenceT = static_cast<float>(RippleIndex) / static_cast<float>(FMath::Max(1, RippleCount - 1));
        const float Phase = static_cast<float>(RippleIndex) * 1.6180339f;
        const float X = FMath::Lerp(-4300.0f, 24850.0f, FMath::Frac(0.071f + SequenceT * 0.91f + 0.019f * FMath::Sin(Phase)));
        const float Width =
            ActiveRiverHalfWidth * (0.93f + 0.09f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.15f : 0.04f));
        const float LateralT = FMath::Sin(Phase * 0.77f) * 0.62f + FMath::Sin(Phase * 1.31f) * 0.22f;
        const float Lateral = FMath::Clamp(LateralT, -0.92f, 0.92f) * Width;
        const float EdgeT = FMath::Pow(FMath::Abs(Lateral) / FMath::Max(1.0f, Width), 1.35f);
        const bool bBright = (RippleIndex % 4) != 0;
        const FLinearColor RippleColor = bBright
            ? FMath::Lerp(BrightGlint, BankTint, FMath::Clamp(EdgeT * 0.42f, 0.0f, 0.48f))
            : FMath::Lerp(DarkRipple, BankTint, FMath::Clamp(EdgeT * 0.32f, 0.0f, 0.42f));
        const float LengthCm =
            (Spec.bDesertCanyon ? 620.0f : 520.0f) *
            (0.74f + 0.24f * static_cast<float>(RippleIndex % 5)) *
            FMath::Clamp(FlowEnergy, 0.72f, 1.18f);
        const float WidthCm =
            (Spec.bDesertCanyon ? 13.0f : 11.0f) *
            (0.82f + 0.18f * static_cast<float>(RippleIndex % 4));
        const FLinearColor RibbonHighlight = bBright ? RippleColor : FMath::Lerp(RippleColor, BrightGlint, 0.18f);
        const FLinearColor RibbonShadow = bBright ? FMath::Lerp(DarkRipple, RippleColor, 0.35f) : RippleColor;

        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaterMicroRippleGlint_%03d_%s"), RippleIndex, *Spec.RiverId),
            X - LengthCm * 0.50f,
            LengthCm,
            Lateral,
            WidthCm,
            Phase,
            RibbonHighlight,
            RibbonShadow);
    }
}
} // namespace RaftSimEditorEnvironment
