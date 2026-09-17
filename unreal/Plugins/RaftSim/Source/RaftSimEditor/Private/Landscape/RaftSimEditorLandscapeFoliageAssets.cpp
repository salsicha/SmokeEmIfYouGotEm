#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"

namespace RaftSimEditorEnvironment::LandscapeFoliage
{
float ZambeziVegetationUnitRandom(int32 Index, int32 Salt)
{
    uint32 Hash = static_cast<uint32>(Index) * 0x9E3779B9u;
    Hash ^= static_cast<uint32>(Salt) * 0x85EBCA6Bu;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}

void AppendZambeziColoredSegment(
    const FVector& Start,
    const FVector& End,
    float StartRadius,
    float EndRadius,
    int32 SideCount,
    const FLinearColor& StartColor,
    const FLinearColor& EndColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    const int32 FirstVertex = Vertices.Num();
    AppendNativeCanopyTaperedSegment(
        Start,
        End,
        StartRadius,
        EndRadius,
        SideCount,
        Vertices,
        Triangles,
        Normals,
        Uvs);
    const int32 AddedVertexCount = Vertices.Num() - FirstVertex;
    for (int32 VertexIndex = 0; VertexIndex < AddedVertexCount; ++VertexIndex)
    {
        const bool bEndRing = VertexIndex >= AddedVertexCount / 2;
        Colors.Add(bEndRing ? EndColor : StartColor);
    }
}

void AppendOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    int32 RingCount,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    check(RingCount >= 3);
    check(SegmentCount >= 6);
    const int32 BottomIndex = Vertices.Num();
    Vertices.Add(Center - FVector::UpVector * Radii.Z);
    Normals.Add(-FVector::UpVector);
    Uvs.Add(FVector2D(0.5f, 1.0f));
    Colors.Add(ScalePreviewColor(BaseColor, 0.70f));

    const int32 FirstRingStart = Vertices.Num();
    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        const float RingT = static_cast<float>(RingIndex + 1) /
            static_cast<float>(RingCount + 1);
        const float Latitude = -0.5f * PI + RingT * PI;
        const float Radial = FMath::Cos(Latitude);
        const float UnitZ = FMath::Sin(Latitude);
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const float SegmentT = static_cast<float>(SegmentIndex) /
                static_cast<float>(SegmentCount);
            const float Longitude = SegmentT * UE_TWO_PI;
            const float EdgeNoise =
                0.94f +
                0.045f * FMath::Sin(
                    Longitude * (3.0f + static_cast<float>(Seed % 3)) +
                    static_cast<float>(RingIndex) * 0.83f + Seed * 0.19f) +
                0.020f * FMath::Sin(Longitude * 7.0f - Seed * 0.31f);
            const FVector Unit(
                Radial * FMath::Cos(Longitude) * EdgeNoise,
                Radial * FMath::Sin(Longitude) * EdgeNoise,
                UnitZ * (0.94f + 0.06f * FMath::Sin(Longitude * 2.0f + Seed)));
            Vertices.Add(Center + Unit * Radii);
            Normals.Add(FVector(
                Unit.X / FMath::Max(1.0f, Radii.X),
                Unit.Y / FMath::Max(1.0f, Radii.Y),
                Unit.Z / FMath::Max(1.0f, Radii.Z)).GetSafeNormal());
            Uvs.Add(FVector2D(SegmentT, 1.0f - RingT));
            const float Tint = 0.82f + 0.14f * RingT +
                0.06f * FMath::Sin(Longitude * 4.0f + Seed * 0.47f);
            Colors.Add(ScalePreviewColor(BaseColor, Tint));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(Center + FVector::UpVector * Radii.Z);
    Normals.Add(FVector::UpVector);
    Uvs.Add(FVector2D(0.5f, 0.0f));
    Colors.Add(ScalePreviewColor(BaseColor, 1.02f));

    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Append({
            BottomIndex,
            FirstRingStart + NextSegment,
            FirstRingStart + SegmentIndex});
    }
    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 LowerStart = FirstRingStart + RingIndex * SegmentCount;
        const int32 UpperStart = LowerStart + SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            Triangles.Append({
                LowerStart + SegmentIndex,
                UpperStart + NextSegment,
                UpperStart + SegmentIndex,
                LowerStart + SegmentIndex,
                LowerStart + NextSegment,
                UpperStart + NextSegment});
        }
    }
    const int32 LastRingStart =
        FirstRingStart + (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Append({
            LastRingStart + SegmentIndex,
            LastRingStart + NextSegment,
            TopIndex});
    }
}

void AppendZambeziOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    AppendOpaqueLobe(
        Center,
        Radii,
        Seed,
        BaseColor,
        8,
        16,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);
}

void AppendOrientedRainforestLobe(
    const FVector& Center,
    const FVector& Radii,
    const FRotator& Rotation,
    int32 Seed,
    const FLinearColor& BaseColor,
    int32 RingCount,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    const int32 FirstVertex = Vertices.Num();
    AppendOpaqueLobe(
        Center,
        Radii,
        Seed,
        BaseColor,
        RingCount,
        SegmentCount,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);
    for (int32 VertexIndex = FirstVertex;
         VertexIndex < Vertices.Num();
         ++VertexIndex)
    {
        Vertices[VertexIndex] = Center + Rotation.RotateVector(
            Vertices[VertexIndex] - Center);
    }
}

void AppendRainforestOpaqueCrownlet(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    // One large low-resolution ellipsoid produced the repeated polygon fans
    // visible from the Upper Huacas guide cameras.  The V2 fallback keeps an
    // opaque, distance-stable core but wraps it in smaller oblique crownlets.
    // This is morphology-only presentation geometry: it has no collision,
    // species authority, wind authority, or terrain/hydraulic influence.
    const float CoreScale = FMath::Lerp(
        0.58f,
        0.68f,
        ZambeziVegetationUnitRandom(Seed, 6101));
    AppendOpaqueLobe(
        Center,
        Radii * FVector(
            CoreScale,
            CoreScale * 0.86f,
            CoreScale * 0.72f),
        Seed,
        ScalePreviewColor(BaseColor, 0.91f),
        10,
        20,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);

    constexpr int32 LeafClusterCount = 6;
    for (int32 ClusterIndex = 0;
         ClusterIndex < LeafClusterCount;
         ++ClusterIndex)
    {
        const int32 ClusterSeed = Seed + 89 + ClusterIndex * 47;
        const float Angle =
            UE_TWO_PI * static_cast<float>(ClusterIndex) /
                static_cast<float>(LeafClusterCount) +
            Seed * 0.031f +
            FMath::Lerp(
                -0.24f,
                0.24f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6113));
        const float RadialScale = FMath::Lerp(
            0.32f,
            0.48f,
            ZambeziVegetationUnitRandom(ClusterSeed, 6121));
        const FVector Offset(
            FMath::Cos(Angle) * Radii.X * RadialScale,
            FMath::Sin(Angle) * Radii.Y * RadialScale,
            Radii.Z * FMath::Lerp(
                -0.24f,
                0.27f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6131)));
        const FVector ClusterRadii = Radii * FVector(
            FMath::Lerp(
                0.38f,
                0.52f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6133)),
            FMath::Lerp(
                0.22f,
                0.34f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6143)),
            FMath::Lerp(
                0.24f,
                0.38f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6151)));
        const FRotator ClusterRotation(
            FMath::Lerp(
                -20.0f,
                20.0f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6163)),
            FMath::RadiansToDegrees(Angle),
            FMath::Lerp(
                -13.0f,
                13.0f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6173)));
        AppendOrientedRainforestLobe(
            Center + Offset,
            ClusterRadii,
            ClusterRotation,
            ClusterSeed,
            ScalePreviewColor(
                BaseColor,
                FMath::Lerp(
                    0.82f,
                    1.16f,
                    ZambeziVegetationUnitRandom(ClusterSeed, 6197))),
            6,
            12,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
}

void AppendTemperateOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    bool bRainforestPalette,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    if (bRainforestPalette)
    {
        AppendRainforestOpaqueCrownlet(
            Center,
            Radii,
            Seed,
            BaseColor,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        return;
    }

    // Build one continuous, asymmetric crownlet from four overlapping volumes.
    // This keeps the opaque, distance-stable fallback while removing the single
    // balloon/diamond silhouette that dominated the runnable river cameras.
    const float CoreScale = FMath::Lerp(
        0.84f,
        0.93f,
        ZambeziVegetationUnitRandom(Seed, 6029));
    AppendOpaqueLobe(
        Center,
        Radii * FVector(CoreScale, CoreScale * 0.96f, CoreScale * 1.04f),
        Seed,
        BaseColor,
        9,
        18,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);

    constexpr int32 SatelliteLobeCount = 3;
    for (int32 LobeIndex = 0;
         LobeIndex < SatelliteLobeCount;
         ++LobeIndex)
    {
        const int32 LobeSeed = Seed + 71 + LobeIndex * 43;
        const float Angle =
            UE_TWO_PI * static_cast<float>(LobeIndex) /
                static_cast<float>(SatelliteLobeCount) +
            Seed * 0.037f +
            FMath::Lerp(
                -0.31f,
                0.31f,
                ZambeziVegetationUnitRandom(LobeSeed, 6037));
        const float RadialScale = FMath::Lerp(
            0.20f,
            0.31f,
            ZambeziVegetationUnitRandom(LobeSeed, 6043));
        const FVector LobeOffset(
            FMath::Cos(Angle) * Radii.X * RadialScale,
            FMath::Sin(Angle) * Radii.Y * RadialScale,
            Radii.Z * FMath::Lerp(
                -0.18f,
                0.20f,
                ZambeziVegetationUnitRandom(LobeSeed, 6053)));
        const FVector LobeRadii = Radii * FVector(
            FMath::Lerp(
                0.39f,
                0.49f,
                ZambeziVegetationUnitRandom(LobeSeed, 6067)),
            FMath::Lerp(
                0.36f,
                0.46f,
                ZambeziVegetationUnitRandom(LobeSeed, 6073)),
            FMath::Lerp(
                0.41f,
                0.52f,
                ZambeziVegetationUnitRandom(LobeSeed, 6079)));
        AppendOpaqueLobe(
            Center + LobeOffset,
            LobeRadii,
            LobeSeed,
            ScalePreviewColor(
                BaseColor,
                FMath::Lerp(
                    0.88f,
                    1.08f,
                    ZambeziVegetationUnitRandom(LobeSeed, 6089))),
            5,
            10,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
}

void AppendPacuareFoldedLeaf(
    const FVector& Center,
    float LengthCm,
    float WidthCm,
    float FoldHeightCm,
    float CurlHeightCm,
    const FRotator& Rotation,
    const FLinearColor& TopColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    constexpr int32 StationCount = 6;
    constexpr int32 VerticesPerStation = 6;
    constexpr float ThicknessCm = 1.2f;
    const int32 FirstVertex = Vertices.Num();
    const FLinearColor BottomColor = ScalePreviewColor(TopColor, 0.58f);
    for (int32 StationIndex = 0; StationIndex < StationCount; ++StationIndex)
    {
        const float T = static_cast<float>(StationIndex) /
            static_cast<float>(StationCount - 1);
        const float UnitX = 2.0f * T - 1.0f;
        const float EdgeTaper = 0.10f + 0.90f *
            FMath::Pow(FMath::Max(0.0f, FMath::Sin(PI * T)), 0.62f);
        const float HalfWidth = 0.5f * WidthCm * EdgeTaper;
        const float BaseZ = CurlHeightCm * UnitX * UnitX +
            0.75f * FMath::Sin(PI * T);
        const float RidgeZ = FoldHeightCm *
            (0.22f + 0.78f * FMath::Sin(PI * T));
        const float X = UnitX * 0.5f * LengthCm;
        const FVector LocalPoints[VerticesPerStation] = {
            FVector(X, -HalfWidth, BaseZ),
            FVector(X, 0.0f, BaseZ + RidgeZ),
            FVector(X, HalfWidth, BaseZ),
            FVector(X, -HalfWidth, BaseZ - ThicknessCm),
            FVector(X, 0.0f, BaseZ + RidgeZ - ThicknessCm),
            FVector(X, HalfWidth, BaseZ - ThicknessCm)};
        for (int32 PointIndex = 0;
             PointIndex < VerticesPerStation;
             ++PointIndex)
        {
            Vertices.Add(Center + Rotation.RotateVector(LocalPoints[PointIndex]));
            Normals.Add(PointIndex < 3 ? FVector::UpVector : -FVector::UpVector);
            Uvs.Add(FVector2D(T, PointIndex % 3 == 0
                ? 0.0f
                : (PointIndex % 3 == 1 ? 0.5f : 1.0f)));
            Colors.Add(PointIndex < 3 ? TopColor : BottomColor);
        }
    }

    for (int32 StationIndex = 0;
         StationIndex < StationCount - 1;
         ++StationIndex)
    {
        const int32 A = FirstVertex + StationIndex * VerticesPerStation;
        const int32 B = A + VerticesPerStation;
        Triangles.Append({
            A + 0, B + 0, B + 1, A + 0, B + 1, A + 1,
            A + 1, B + 1, B + 2, A + 1, B + 2, A + 2,
            A + 3, B + 4, B + 3, A + 3, A + 4, B + 4,
            A + 4, B + 5, B + 4, A + 4, A + 5, B + 5,
            A + 0, A + 3, B + 3, A + 0, B + 3, B + 0,
            A + 2, B + 5, A + 5, A + 2, B + 2, B + 5});
    }
    const int32 Start = FirstVertex;
    const int32 End = FirstVertex +
        (StationCount - 1) * VerticesPerStation;
    Triangles.Append({
        Start + 0, Start + 1, Start + 3,
        Start + 1, Start + 4, Start + 3,
        Start + 1, Start + 2, Start + 4,
        Start + 2, Start + 5, Start + 4,
        End + 0, End + 3, End + 1,
        End + 1, End + 3, End + 4,
        End + 1, End + 4, End + 2,
        End + 2, End + 4, End + 5});
}

UStaticMesh* CreatePacuareForestFloorMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    EPacuareForestFloorForm Form,
    int32 Seed,
    UMaterialInterface* Material,
    FString& OutSummary)
{
    if (!World || !AssetToken || !Material)
    {
        return nullptr;
    }

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    const FLinearColor WetBark(0.040f, 0.029f, 0.018f, 1.0f);
    const FLinearColor BarkBreak(0.094f, 0.062f, 0.031f, 1.0f);
    const FLinearColor Moss(0.034f, 0.086f, 0.030f, 1.0f);
    const FLinearColor LitterBrown(0.100f, 0.052f, 0.022f, 1.0f);
    const FLinearColor LitterOlive(0.075f, 0.083f, 0.026f, 1.0f);

    if (Form == EPacuareForestFloorForm::FoldedLeafLitter)
    {
        constexpr int32 LeafCount = 14;
        for (int32 LeafIndex = 0; LeafIndex < LeafCount; ++LeafIndex)
        {
            const int32 LeafSeed = Seed + LeafIndex * 47;
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(LeafSeed, 12001);
            const float Radius = FMath::Lerp(
                12.0f,
                178.0f,
                FMath::Sqrt(ZambeziVegetationUnitRandom(LeafSeed, 12007)));
            const FVector Center(
                FMath::Cos(Angle) * Radius,
                FMath::Sin(Angle) * Radius,
                FMath::Lerp(1.8f, 7.0f,
                    ZambeziVegetationUnitRandom(LeafSeed, 12011)));
            const FLinearColor LeafColor = FMath::Lerp(
                LitterBrown,
                LitterOlive,
                ZambeziVegetationUnitRandom(LeafSeed, 12037));
            AppendPacuareFoldedLeaf(
                Center,
                FMath::Lerp(38.0f, 82.0f,
                    ZambeziVegetationUnitRandom(LeafSeed, 12041)),
                FMath::Lerp(16.0f, 36.0f,
                    ZambeziVegetationUnitRandom(LeafSeed, 12043)),
                FMath::Lerp(2.4f, 8.5f,
                    ZambeziVegetationUnitRandom(LeafSeed, 12049)),
                FMath::Lerp(0.8f, 7.2f,
                    ZambeziVegetationUnitRandom(LeafSeed, 12071)),
                FRotator(
                    FMath::Lerp(-8.0f, 8.0f,
                        ZambeziVegetationUnitRandom(LeafSeed, 12073)),
                    FMath::RadiansToDegrees(Angle) +
                        FMath::Lerp(-85.0f, 85.0f,
                            ZambeziVegetationUnitRandom(LeafSeed, 12097)),
                    FMath::Lerp(-12.0f, 12.0f,
                        ZambeziVegetationUnitRandom(LeafSeed, 12101))),
                ScalePreviewColor(
                    LeafColor,
                    FMath::Lerp(0.72f, 1.12f,
                        ZambeziVegetationUnitRandom(LeafSeed, 12107))),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == EPacuareForestFloorForm::ButtressRoot)
    {
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            FVector(4.0f, -3.0f, 68.0f),
            46.0f,
            24.0f,
            12,
            WetBark,
            BarkBreak,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        constexpr int32 RootCount = 9;
        for (int32 RootIndex = 0; RootIndex < RootCount; ++RootIndex)
        {
            const int32 RootSeed = Seed + RootIndex * 67;
            const float Angle = UE_TWO_PI * static_cast<float>(RootIndex) /
                    static_cast<float>(RootCount) +
                FMath::Lerp(-0.18f, 0.18f,
                    ZambeziVegetationUnitRandom(RootSeed, 12113));
            const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector Tangent(-Direction.Y, Direction.X, 0.0f);
            const float Length = FMath::Lerp(125.0f, 255.0f,
                ZambeziVegetationUnitRandom(RootSeed, 12119));
            const FVector Mid = Direction * Length * 0.48f +
                Tangent * FMath::Lerp(-18.0f, 18.0f,
                    ZambeziVegetationUnitRandom(RootSeed, 12143)) +
                FVector::UpVector * 13.0f;
            const FVector End = Direction * Length +
                Tangent * FMath::Lerp(-26.0f, 26.0f,
                    ZambeziVegetationUnitRandom(RootSeed, 12149)) +
                FVector::UpVector * 4.0f;
            AppendZambeziColoredSegment(
                FVector(0.0f, 0.0f, 18.0f),
                Mid,
                20.0f,
                9.0f,
                8,
                WetBark,
                ScalePreviewColor(WetBark, 1.08f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                9.0f,
                2.4f,
                7,
                ScalePreviewColor(WetBark, 1.08f),
                RootIndex % 3 == 0 ? Moss : BarkBreak,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else
    {
        FVector Start(-145.0f, -22.0f, 18.0f);
        constexpr int32 SegmentCount = 5;
        for (int32 SegmentIndex = 0;
             SegmentIndex < SegmentCount;
             ++SegmentIndex)
        {
            const float SegmentT = static_cast<float>(SegmentIndex + 1) /
                static_cast<float>(SegmentCount);
            const FVector End(
                FMath::Lerp(-145.0f, 155.0f, SegmentT),
                24.0f * FMath::Sin(SegmentT * PI * 1.4f + Seed * 0.03f),
                16.0f + 10.0f * FMath::Sin(SegmentT * PI));
            AppendZambeziColoredSegment(
                Start,
                End,
                FMath::Lerp(22.0f, 10.0f,
                    static_cast<float>(SegmentIndex) / SegmentCount),
                FMath::Lerp(20.0f, 7.0f, SegmentT),
                10,
                SegmentIndex % 2 == 0 ? WetBark : BarkBreak,
                SegmentIndex == SegmentCount - 1 ? BarkBreak : WetBark,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            if (SegmentIndex == 1 || SegmentIndex == 3)
            {
                const float BranchSide = SegmentIndex == 1 ? -1.0f : 1.0f;
                AppendZambeziColoredSegment(
                    FMath::Lerp(Start, End, 0.62f),
                    FMath::Lerp(Start, End, 0.62f) +
                        FVector(42.0f, BranchSide * 88.0f, 28.0f),
                    8.0f,
                    2.2f,
                    7,
                    WetBark,
                    BarkBreak,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
            }
            Start = End;
        }
        for (int32 MossIndex = 0; MossIndex < 5; ++MossIndex)
        {
            const float T = 0.16f + 0.15f * MossIndex;
            AppendOpaqueLobe(
                FVector(
                    FMath::Lerp(-125.0f, 135.0f, T),
                    12.0f * FMath::Sin(T * PI * 2.3f),
                    37.0f),
                FVector(18.0f, 13.0f, 7.0f),
                Seed + MossIndex * 31,
                ScalePreviewColor(Moss, 0.82f + 0.06f * MossIndex),
                4,
                8,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty() ||
        Colors.Num() != Vertices.Num() || Uvs.Num() != Vertices.Num())
    {
        OutSummary += FString::Printf(
            TEXT("Pacuare forest-floor geometry contract failed for %s.\n"),
            AssetToken);
        return nullptr;
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_PacuareForestFloor_%s_BuildSource"), AssetToken),
        Vertices,
        Triangles,
        Normals,
        Uvs,
        FLinearColor::White,
        Material,
        &Colors,
        false);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    const FString PackagePath = FString(PacuareRainforestVegetationMeshRoot) +
        AssetToken;
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        Material,
        true,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Prepared Pacuare forest-floor %s: vertices=%d triangles=%d "
                 "Nanite=%d collision=false.\n"),
            AssetToken,
            Mesh->GetNumVertices(0),
            Mesh->GetNumTriangles(0),
            Mesh->IsNaniteEnabled());
    }
    return Mesh;
}

bool CreatePacuareForestFloorAssets(
    UWorld* World,
    UMaterialInterface* Material,
    TArray<UStaticMesh*>& OutMeshes,
    FString& OutSummary)
{
    OutMeshes = {
        CreatePacuareForestFloorMesh(
            World,
            TEXT("SM_RaftSim_Pacuare_FoldedLeafLitter_A_ForestFloorV1"),
            EPacuareForestFloorForm::FoldedLeafLitter,
            PacuareForestFloorDeterministicSeed,
            Material,
            OutSummary),
        CreatePacuareForestFloorMesh(
            World,
            TEXT("SM_RaftSim_Pacuare_FoldedLeafLitter_B_ForestFloorV1"),
            EPacuareForestFloorForm::FoldedLeafLitter,
            PacuareForestFloorDeterministicSeed + 911,
            Material,
            OutSummary),
        CreatePacuareForestFloorMesh(
            World,
            TEXT("SM_RaftSim_Pacuare_ButtressRoot_A_ForestFloorV1"),
            EPacuareForestFloorForm::ButtressRoot,
            PacuareForestFloorDeterministicSeed + 1901,
            Material,
            OutSummary),
        CreatePacuareForestFloorMesh(
            World,
            TEXT("SM_RaftSim_Pacuare_Deadwood_A_ForestFloorV1"),
            EPacuareForestFloorForm::Deadwood,
            PacuareForestFloorDeterministicSeed + 2903,
            Material,
            OutSummary)};
    const bool bComplete = OutMeshes.Num() == 4 &&
        Algo::AllOf(OutMeshes, [](UStaticMesh* Mesh)
        {
            return Mesh && Mesh->IsNaniteEnabled() &&
                Mesh->GetNumVertices(0) > 100 &&
                Mesh->GetNumTriangles(0) > 100;
        });
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete Pacuare forest-floor structure family.\n");
    }
    return bComplete;
}

UMaterial* CreateOpaqueVegetationMaterial(
    const TCHAR* MaterialPath,
    const TCHAR* ProfileLabel,
    float ShadowFillStrength,
    float InstanceEnergyMinimum,
    float InstanceEnergyMaximum,
    FString& OutSummary)
{
    const FString AssetName =
        FPackageName::GetLongPackageAssetName(MaterialPath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), MaterialPath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material
        ? Material->GetOutermost()
        : CreatePackage(MaterialPath);
    if (!Package)
    {
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->DitheredLODTransition = true;

    auto Add = [Material](auto* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionVertexColor* VertexColor = Add(
        NewObject<UMaterialExpressionVertexColor>(Material));
    UMaterialExpressionPerInstanceRandom* InstanceRandom = Add(
        NewObject<UMaterialExpressionPerInstanceRandom>(Material));
    UMaterialExpressionVectorParameter* VegetationColorScale = Add(
        NewObject<UMaterialExpressionVectorParameter>(Material));
    VegetationColorScale->ParameterName = TEXT("VegetationColorScale");
    VegetationColorScale->DefaultValue = FLinearColor::White;
    VegetationColorScale->Group = TEXT("RaftSimOpaqueVegetation");
    UMaterialExpressionConstant* EnergyMinimum = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    EnergyMinimum->R = InstanceEnergyMinimum;
    UMaterialExpressionConstant* EnergyMaximum = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    EnergyMaximum->R = InstanceEnergyMaximum;
    UMaterialExpressionLinearInterpolate* InstanceEnergy = Add(
        NewObject<UMaterialExpressionLinearInterpolate>(Material));
    InstanceEnergy->A.Expression = EnergyMinimum;
    InstanceEnergy->B.Expression = EnergyMaximum;
    InstanceEnergy->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* ScaledVertexColor = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ScaledVertexColor->A.Expression = VertexColor;
    ScaledVertexColor->B.Expression = VegetationColorScale;
    UMaterialExpressionMultiply* VariedVertexColor = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    VariedVertexColor->A.Expression = ScaledVertexColor;
    VariedVertexColor->B.Expression = InstanceEnergy;
    UMaterialExpressionConstant* Roughness = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    Roughness->R = 0.91f;
    UMaterialExpressionConstant* Specular = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    Specular->R = 0.08f;
    UMaterialExpressionConstant* AmbientOcclusion = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    AmbientOcclusion->R = 1.0f;
    UMaterialExpressionConstant* ShadowFloor = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    ShadowFloor->R = ShadowFillStrength;
    UMaterialExpressionScalarParameter* VegetationShadowFillScale = Add(
        NewObject<UMaterialExpressionScalarParameter>(Material));
    VegetationShadowFillScale->ParameterName =
        TEXT("VegetationShadowFillScale");
    VegetationShadowFillScale->DefaultValue = 1.0f;
    VegetationShadowFillScale->Group = TEXT("RaftSimOpaqueVegetation");
    UMaterialExpressionMultiply* ScaledShadowFloor = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ScaledShadowFloor->A.Expression = ShadowFloor;
    ScaledShadowFloor->B.Expression = VegetationShadowFillScale;
    UMaterialExpressionMultiply* ShadowFill = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ShadowFill->A.Expression = VariedVertexColor;
    ShadowFill->B.Expression = ScaledShadowFloor;

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(
        EditorOnlyData->BaseColor, VariedVertexColor);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(
        EditorOnlyData->AmbientOcclusion, AmbientOcclusion);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, ShadowFill);

    Material->SetUsageByFlag(MATUSAGE_InstancedStaticMeshes, true);
    Material->SetUsageByFlag(MATUSAGE_Nanite, true);
    Material->PostEditChange();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    const FMaterialResource* Resource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!Resource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !Resource->GetCompileErrors().IsEmpty())
    {
        OutSummary += TEXT(
            "Opaque vegetation material failed its shader gate.\n");
        return nullptr;
    }

    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        MaterialPath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save %s opaque vegetation material.\n"),
            ProfileLabel);
        return nullptr;
    }
    return Material;
}

UMaterial* CreateZambeziOpaqueVegetationMaterial(FString& OutSummary)
{
    return CreateOpaqueVegetationMaterial(
        ZambeziVegetationMaterialPath,
        TEXT("Zambezi"),
        0.09f,
        1.0f,
        1.0f,
        OutSummary);
}

UStaticMesh* CreateZambeziOpaqueVegetationMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    EZambeziVegetationForm Form,
    int32 Seed,
    UMaterialInterface* Material,
    const TCHAR* MeshRoot,
    const TCHAR* ProfileLabel,
    bool bHanceDrylandPalette,
    bool bSecondaryMorphology,
    FString& OutSummary)
{
    if (!World || !AssetToken || !Material || !MeshRoot || !ProfileLabel)
    {
        return nullptr;
    }

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    const FLinearColor BarkBase = bHanceDrylandPalette
        ? FLinearColor(0.105f, 0.066f, 0.030f, 1.0f)
        : FLinearColor(0.175f, 0.125f, 0.070f, 1.0f);
    const FLinearColor BarkTip = bHanceDrylandPalette
        ? FLinearColor(0.142f, 0.091f, 0.040f, 1.0f)
        : FLinearColor(0.215f, 0.155f, 0.082f, 1.0f);
    const FLinearColor LeafGreen = Form == EZambeziVegetationForm::UmbrellaTree
        ? FLinearColor(0.060f, 0.088f, 0.022f, 1.0f)
        : FLinearColor(0.052f, 0.080f, 0.020f, 1.0f);
    const FLinearColor ScrubGreen = bHanceDrylandPalette
        ? FLinearColor(0.050f, 0.060f, 0.018f, 1.0f)
        : FLinearColor(0.050f, 0.075f, 0.018f, 1.0f);
    const FLinearColor DryGrass = bHanceDrylandPalette
        ? FLinearColor(0.180f, 0.118f, 0.035f, 1.0f)
        : FLinearColor(0.200f, 0.135f, 0.035f, 1.0f);
    const FLinearColor LowPlantGreen = bHanceDrylandPalette
        ? FLinearColor(0.055f, 0.068f, 0.018f, 1.0f)
        : FLinearColor(0.065f, 0.095f, 0.022f, 1.0f);
    const FLinearColor BladeGreen = bHanceDrylandPalette
        ? FLinearColor(0.070f, 0.082f, 0.020f, 1.0f)
        : FLinearColor(0.085f, 0.115f, 0.027f, 1.0f);

    if (Form == EZambeziVegetationForm::SavannaGroundCover)
    {
        AppendZambeziOpaqueLobe(
            FVector(0.0f, 0.0f, bSecondaryMorphology ? 8.0f : 10.0f),
            bSecondaryMorphology
                ? FVector(72.0f, 58.0f, 11.0f)
                : FVector(46.0f, 38.0f, 15.0f),
            Seed,
            ScalePreviewColor(DryGrass, 0.62f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        // One opaque mesh instance covers a several-metre patch.  This is
        // intentionally solid tapered geometry rather than masked crossed
        // cards, so the near banks break up organically without returning the
        // black/green card artifacts rejected by the visual review.
        const int32 BladeCount = bSecondaryMorphology ? 28 : 54;
        for (int32 BladeIndex = 0; BladeIndex < BladeCount; ++BladeIndex)
        {
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1201);
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = FMath::Lerp(
                bSecondaryMorphology ? 18.0f : 12.0f,
                bSecondaryMorphology ? 275.0f : 240.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1213));
            const float Height = FMath::Lerp(
                bSecondaryMorphology ? 18.0f : 24.0f,
                bSecondaryMorphology ? 56.0f : 82.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1231));
            const float Lean = FMath::Lerp(
                5.0f,
                bSecondaryMorphology ? 38.0f : 28.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1249));
            const FVector Start = Direction * Radius;
            const FVector End = Start + Direction * Lean + FVector::UpVector * Height;
            const float Dryness = ZambeziVegetationUnitRandom(
                BladeIndex + Seed, 1277);
            const FLinearColor BladeColor = FMath::Lerp(
                BladeGreen,
                DryGrass,
                Dryness);
            AppendZambeziColoredSegment(
                Start,
                End,
                1.8f,
                0.42f,
                5,
                ScalePreviewColor(BladeColor, 0.72f),
                ScalePreviewColor(BladeColor, 1.08f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        const int32 LowForbCount = bSecondaryMorphology ? 18 : 11;
        for (int32 ForbIndex = 0; ForbIndex < LowForbCount; ++ForbIndex)
        {
            const int32 RandomIndex = ForbIndex + Seed * 2;
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(RandomIndex, 1301);
            const float Radius = FMath::Lerp(
                34.0f,
                205.0f,
                ZambeziVegetationUnitRandom(RandomIndex, 1303));
            const float Scale = FMath::Lerp(
                0.72f,
                1.24f,
                ZambeziVegetationUnitRandom(RandomIndex, 1307));
            const FLinearColor ForbColor = FMath::Lerp(
                LowPlantGreen,
                DryGrass,
                ZambeziVegetationUnitRandom(RandomIndex, 1319));
            AppendZambeziOpaqueLobe(
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Radius +
                    FVector::UpVector * (9.0f * Scale),
                (bSecondaryMorphology
                     ? FVector(29.0f, 23.0f, 9.0f)
                     : FVector(21.0f, 17.0f, 11.0f)) * Scale,
                RandomIndex,
                ForbColor,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == EZambeziVegetationForm::ThornScrub)
    {
        const int32 StemCount = bSecondaryMorphology ? 19 : 13;
        for (int32 StemIndex = 0; StemIndex < StemCount; ++StemIndex)
        {
            const float Angle = UE_TWO_PI *
                static_cast<float>(StemIndex) / static_cast<float>(StemCount) +
                Seed * 0.17f;
            const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Length = (bSecondaryMorphology ? 88.0f : 115.0f) +
                (bSecondaryMorphology ? 46.0f : 52.0f) *
                ZambeziVegetationUnitRandom(StemIndex + Seed, 1601);
            const FVector Start = Direction * 9.0f;
            const FVector Mid = Direction * Length * 0.48f +
                FVector::UpVector *
                    ((bSecondaryMorphology ? 58.0f : 75.0f) +
                     (bSecondaryMorphology ? 12.0f : 18.0f) *
                         (StemIndex % 3));
            const FVector End = Direction * Length +
                FVector::UpVector *
                    ((bSecondaryMorphology ? 104.0f : 125.0f) +
                     (bSecondaryMorphology ? 22.0f : 32.0f) *
                         (StemIndex % 4));
            AppendZambeziColoredSegment(
                Start,
                Mid,
                9.0f,
                5.0f,
                7,
                BarkBase,
                BarkTip,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                5.0f,
                2.1f,
                6,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.12f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziOpaqueLobe(
                End,
                (bSecondaryMorphology
                     ? FVector(82.0f, 68.0f, 34.0f)
                     : FVector(64.0f, 52.0f, 46.0f)) *
                    (0.86f + 0.12f * static_cast<float>(StemIndex % 4)),
                Seed + StemIndex * 17,
                ScrubGreen,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else
    {
        const bool bUmbrella = Form == EZambeziVegetationForm::UmbrellaTree;
        const FVector LowerTrunkEnd(
            bUmbrella ? 18.0f : -14.0f,
            bUmbrella ? -12.0f : 16.0f,
            bUmbrella ? 360.0f : 410.0f);
        const FVector UpperTrunkEnd(
            bUmbrella ? -8.0f : 24.0f,
            bUmbrella ? 14.0f : -18.0f,
            bUmbrella ? 555.0f : 610.0f);
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            LowerTrunkEnd,
            bUmbrella ? 48.0f : 42.0f,
            bUmbrella ? 29.0f : 25.0f,
            10,
            BarkBase,
            BarkTip,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        AppendZambeziColoredSegment(
            LowerTrunkEnd,
            UpperTrunkEnd,
            bUmbrella ? 29.0f : 25.0f,
            15.0f,
            9,
            BarkTip,
            ScalePreviewColor(BarkTip, 1.16f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);

        constexpr int32 RootCount = 7;
        for (int32 RootIndex = 0; RootIndex < RootCount; ++RootIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(RootIndex) /
                static_cast<float>(RootCount) + Seed * 0.11f;
            AppendZambeziColoredSegment(
                FVector(0.0f, 0.0f, 18.0f),
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) *
                    (92.0f + 12.0f * static_cast<float>(RootIndex % 3)),
                18.0f,
                4.0f,
                7,
                BarkBase,
                ScalePreviewColor(BarkBase, 0.82f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }

        const int32 BranchCount = bUmbrella ? 14 : 12;
        for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
        {
            const float Angle = FMath::Fmod(
                137.50776f * BranchIndex + Seed * 23.0f,
                360.0f) * PI / 180.0f;
            const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = bUmbrella
                ? 315.0f + 34.0f * static_cast<float>(BranchIndex % 4)
                : 250.0f + 42.0f * static_cast<float>(BranchIndex % 5);
            const float StartZ = bUmbrella
                ? 390.0f + 22.0f * static_cast<float>(BranchIndex % 5)
                : 380.0f + 31.0f * static_cast<float>(BranchIndex % 6);
            const float EndZ = bUmbrella
                ? 575.0f + 28.0f * static_cast<float>(BranchIndex % 3)
                : 590.0f + 55.0f * static_cast<float>(BranchIndex % 5);
            const FVector Start(0.0f, 0.0f, StartZ);
            const FVector Mid = Direction * Radius * 0.48f +
                FVector::UpVector * FMath::Lerp(StartZ, EndZ, 0.62f);
            const FVector End = Direction * Radius + FVector::UpVector * EndZ;
            AppendZambeziColoredSegment(
                Start,
                Mid,
                15.0f,
                8.0f,
                8,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.10f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                8.0f,
                3.2f,
                7,
                ScalePreviewColor(BarkTip, 1.10f),
                ScalePreviewColor(BarkTip, 1.18f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            const FVector LobeRadii = bUmbrella
                ? FVector(188.0f, 132.0f, 72.0f) *
                    (0.88f + 0.08f * static_cast<float>(BranchIndex % 4))
                : FVector(154.0f, 126.0f, 112.0f) *
                    (0.86f + 0.09f * static_cast<float>(BranchIndex % 4));
            AppendZambeziOpaqueLobe(
                End + FVector::UpVector * (bUmbrella ? 18.0f : 34.0f),
                LobeRadii,
                Seed + BranchIndex * 29,
                LeafGreen,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }

        constexpr int32 CrownFillCount = 5;
        for (int32 FillIndex = 0; FillIndex < CrownFillCount; ++FillIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(FillIndex) /
                static_cast<float>(CrownFillCount) + Seed * 0.07f;
            const FVector Center(
                FMath::Cos(Angle) * (bUmbrella ? 118.0f : 92.0f),
                FMath::Sin(Angle) * (bUmbrella ? 118.0f : 92.0f),
                bUmbrella ? 628.0f : 690.0f + 34.0f * (FillIndex % 2));
            AppendZambeziOpaqueLobe(
                Center,
                bUmbrella
                    ? FVector(205.0f, 155.0f, 76.0f)
                    : FVector(168.0f, 142.0f, 128.0f),
                Seed + 500 + FillIndex * 37,
                ScalePreviewColor(LeafGreen, 0.94f + 0.03f * FillIndex),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty() ||
        Colors.Num() != Vertices.Num() || Uvs.Num() != Vertices.Num())
    {
        OutSummary += FString::Printf(
            TEXT("%s vegetation geometry contract failed for %s.\n"),
            ProfileLabel,
            AssetToken);
        return nullptr;
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(
            TEXT("RaftSim_%s_%s_BuildSource"), ProfileLabel, AssetToken),
        Vertices,
        Triangles,
        Normals,
        Uvs,
        FLinearColor::White,
        Material,
        &Colors,
        false);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    const FString PackagePath = FString(MeshRoot) + AssetToken;
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        Material,
        true,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Prepared %s %s opaque volumetric vegetation: "
                 "vertices=%d triangles=%d Nanite=%d collision=false.\n"),
            ProfileLabel,
            AssetToken,
            Mesh->GetNumVertices(0),
            Mesh->GetNumTriangles(0),
            Mesh->IsNaniteEnabled());
    }
    return Mesh;
}

bool CreateZambeziOpaqueVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutRiparianTree,
    UStaticMesh*& OutUmbrellaTree,
    UStaticMesh*& OutThornScrub,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateZambeziOpaqueVegetationMaterial(OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutRiparianTree = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_RiparianTree_A_OpaqueV1"),
        EZambeziVegetationForm::RiparianTree,
        1709,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutUmbrellaTree = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_UmbrellaTree_B_OpaqueV1"),
        EZambeziVegetationForm::UmbrellaTree,
        2713,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutThornScrub = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_ThornScrub_A_OpaqueV1"),
        EZambeziVegetationForm::ThornScrub,
        3907,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutGroundCoverA = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1"),
        EZambeziVegetationForm::SavannaGroundCover,
        4933,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutGroundCoverB = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_SavannaGroundCover_B_OpaqueV2"),
        EZambeziVegetationForm::SavannaGroundCover,
        5077,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        true,
        OutSummary);
    const bool bComplete =
        OutRiparianTree && OutUmbrellaTree && OutThornScrub &&
        OutGroundCoverA && OutGroundCoverB;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete Zambezi opaque vegetation family.\n");
    }
    return bComplete;
}

bool CreateHanceOpaqueDrylandVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutShrubA,
    UStaticMesh*& OutShrubB,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        HanceDrylandVegetationMaterialPath,
        TEXT("Colorado Hance dryland"),
        0.045f,
        1.0f,
        1.0f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutShrubA = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DesertShrub_A_OpaqueV2"),
        EZambeziVegetationForm::ThornScrub,
        7307,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        false,
        OutSummary);
    OutShrubB = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DesertShrub_B_OpaqueV2"),
        EZambeziVegetationForm::ThornScrub,
        7351,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        true,
        OutSummary);
    OutGroundCoverA = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DryGroundCover_A_OpaqueV2"),
        EZambeziVegetationForm::SavannaGroundCover,
        7411,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        false,
        OutSummary);
    OutGroundCoverB = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DryGroundCover_B_OpaqueV2"),
        EZambeziVegetationForm::SavannaGroundCover,
        7457,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        true,
        OutSummary);
    if (!OutShrubA || !OutShrubB || !OutGroundCoverA || !OutGroundCoverB)
    {
        OutSummary += TEXT(
            "Failed to build the Hance opaque dryland vegetation family.\n");
        return false;
    }
    return true;
}

UStaticMesh* CreateTemperateOpaqueVegetationMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    ETemperateVegetationForm Form,
    int32 Seed,
    UMaterialInterface* Material,
    const TCHAR* MeshRoot,
    const TCHAR* ProfileLabel,
    bool bRainforestPalette,
    bool bSecondaryMorphology,
    FString& OutSummary)
{
    if (!World || !AssetToken || !Material)
    {
        return nullptr;
    }

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    // These are linear-space radiance values under a 4.75-5.05 lux review
    // sun. The former preview-green values clipped into pale mint balloons
    // once solid lobes stopped casting their invalid card-like shadows.
    const FLinearColor BarkBase = bRainforestPalette
        ? FLinearColor(0.038f, 0.029f, 0.019f, 1.0f)
        : FLinearColor(0.060f, 0.040f, 0.025f, 1.0f);
    const FLinearColor BarkTip = bRainforestPalette
        ? FLinearColor(0.060f, 0.048f, 0.029f, 1.0f)
        : FLinearColor(0.082f, 0.058f, 0.035f, 1.0f);
    const FLinearColor BroadleafGreen = bRainforestPalette
        ? FLinearColor(0.020f, 0.082f, 0.030f, 1.0f)
        : FLinearColor(0.032f, 0.098f, 0.047f, 1.0f);
    const FLinearColor ConiferGreen = bRainforestPalette
        ? FLinearColor(0.026f, 0.096f, 0.038f, 1.0f)
        : FLinearColor(0.026f, 0.078f, 0.044f, 1.0f);
    const FLinearColor ShrubGreen = bRainforestPalette
        ? FLinearColor(0.030f, 0.110f, 0.040f, 1.0f)
        : FLinearColor(0.035f, 0.090f, 0.042f, 1.0f);
    const FLinearColor GroundGreen = bRainforestPalette
        ? FLinearColor(0.038f, 0.125f, 0.044f, 1.0f)
        : FLinearColor(0.040f, 0.100f, 0.045f, 1.0f);

    if (Form == ETemperateVegetationForm::GroundCover)
    {
        AppendTemperateOpaqueLobe(
            FVector(0.0f, 0.0f, 8.0f),
            FVector(74.0f, 60.0f, 16.0f),
            Seed,
            ScalePreviewColor(GroundGreen, 0.66f),
            bRainforestPalette,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        const int32 BladeCount = bRainforestPalette ? 72 : 58;
        for (int32 BladeIndex = 0; BladeIndex < BladeCount; ++BladeIndex)
        {
            const int32 RandomIndex = Seed + BladeIndex;
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(RandomIndex, 5101);
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = FMath::Lerp(
                10.0f,
                225.0f,
                ZambeziVegetationUnitRandom(RandomIndex, 5113));
            const float Height = FMath::Lerp(
                28.0f,
                96.0f,
                ZambeziVegetationUnitRandom(RandomIndex, 5119));
            const FLinearColor BladeColor = FMath::Lerp(
                bRainforestPalette
                    ? FLinearColor(0.028f, 0.105f, 0.034f, 1.0f)
                    : FLinearColor(0.105f, 0.245f, 0.085f, 1.0f),
                bRainforestPalette
                    ? FLinearColor(0.050f, 0.135f, 0.042f, 1.0f)
                    : FLinearColor(0.19f, 0.25f, 0.095f, 1.0f),
                ZambeziVegetationUnitRandom(RandomIndex, 5147));
            AppendZambeziColoredSegment(
                Direction * Radius,
                Direction * (Radius + 12.0f) + FVector::UpVector * Height,
                1.7f,
                0.38f,
                5,
                ScalePreviewColor(BladeColor, 0.72f),
                ScalePreviewColor(BladeColor, 1.08f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        const int32 ForbCount = bRainforestPalette ? 26 : 18;
        for (int32 ForbIndex = 0; ForbIndex < ForbCount; ++ForbIndex)
        {
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(Seed + ForbIndex, 5209);
            const float Radius = FMath::Lerp(
                28.0f,
                205.0f,
                ZambeziVegetationUnitRandom(Seed + ForbIndex, 5227));
            AppendTemperateOpaqueLobe(
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Radius +
                    FVector::UpVector * 16.0f,
                FVector(28.0f, 20.0f, 13.0f),
                Seed + ForbIndex * 31,
                ScalePreviewColor(
                    GroundGreen,
                    0.76f + 0.28f * ZambeziVegetationUnitRandom(
                        Seed + ForbIndex, 5231)),
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == ETemperateVegetationForm::RiparianShrub)
    {
        const int32 StemCount = bRainforestPalette ? 20 : 16;
        for (int32 StemIndex = 0; StemIndex < StemCount; ++StemIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(StemIndex) /
                static_cast<float>(StemCount) + Seed * 0.13f;
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Length = 90.0f + 75.0f *
                ZambeziVegetationUnitRandom(Seed + StemIndex, 5407);
            const FVector Mid = Direction * Length * 0.45f +
                FVector::UpVector * (72.0f + 12.0f * (StemIndex % 4));
            const FVector End = Direction * Length +
                FVector::UpVector * (145.0f + 24.0f * (StemIndex % 5));
            AppendZambeziColoredSegment(
                FVector::ZeroVector,
                Mid,
                7.5f,
                4.0f,
                7,
                BarkBase,
                BarkTip,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                4.0f,
                1.6f,
                6,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.10f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendTemperateOpaqueLobe(
                End,
                FVector(66.0f, 54.0f, 48.0f) *
                    (0.84f + 0.10f * static_cast<float>(StemIndex % 4)),
                Seed + StemIndex * 19,
                ShrubGreen,
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == ETemperateVegetationForm::ConiferTree &&
             !bRainforestPalette)
    {
        constexpr float TreeHeightCm = 850.0f;
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            FVector(8.0f, -7.0f, TreeHeightCm),
            42.0f,
            7.0f,
            10,
            BarkBase,
            BarkTip,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        constexpr int32 TierCount = 11;
        for (int32 TierIndex = 0; TierIndex < TierCount; ++TierIndex)
        {
            const float TierT = static_cast<float>(TierIndex) /
                static_cast<float>(TierCount - 1);
            const float TierZ = FMath::Lerp(160.0f, 845.0f, TierT) +
                FMath::Lerp(
                    -18.0f,
                    18.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5651));
            const float TierRadius = FMath::Lerp(310.0f, 62.0f, TierT) *
                FMath::Lerp(
                    0.88f,
                    1.12f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5659));
            const int32 BranchCount = 6 + FMath::Clamp(
                FMath::FloorToInt(
                    3.0f * ZambeziVegetationUnitRandom(
                        Seed + TierIndex,
                        5663)),
                0,
                2);
            const float TierRotation = FMath::Lerp(
                -0.24f,
                0.24f,
                ZambeziVegetationUnitRandom(Seed + TierIndex, 5667));
            for (int32 BranchIndex = 0;
                 BranchIndex < BranchCount;
                 ++BranchIndex)
            {
                const int32 BranchSeed = Seed + TierIndex * 107 +
                    BranchIndex * 23;
                const bool bStormShortenedBranch =
                    BranchIndex == BranchCount - 1 && BranchCount > 5 &&
                    ZambeziVegetationUnitRandom(BranchSeed, 5668) < 0.22f;
                const float Angle = UE_TWO_PI *
                        static_cast<float>(BranchIndex) /
                        static_cast<float>(BranchCount) +
                    TierIndex * 0.43f + Seed * 0.017f + TierRotation +
                    FMath::Lerp(
                        -0.15f,
                        0.15f,
                        ZambeziVegetationUnitRandom(
                            Seed + TierIndex * 17 + BranchIndex,
                            5669));
                const FVector Direction(
                    FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
                const float BranchLengthScale = FMath::Lerp(
                    0.84f,
                    1.15f,
                    ZambeziVegetationUnitRandom(BranchSeed, 5671)) *
                    (bStormShortenedBranch ? 0.62f : 1.0f);
                const float BranchZOffset = FMath::Lerp(
                    -24.0f,
                    24.0f,
                    ZambeziVegetationUnitRandom(BranchSeed, 5677));
                const FVector Start(
                    8.0f * TierT,
                    -7.0f * TierT,
                    TierZ + BranchZOffset);
                const FVector End =
                    Start + Direction * TierRadius * BranchLengthScale +
                    FVector::UpVector *
                        FMath::Lerp(-18.0f, 48.0f, TierT);
                AppendZambeziColoredSegment(
                    Start,
                    End,
                    FMath::Lerp(10.0f, 4.0f, TierT),
                    1.8f,
                    6,
                    BarkTip,
                    ScalePreviewColor(BarkTip, 1.08f),
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendTemperateOpaqueLobe(
                    FMath::Lerp(Start, End, 0.37f) +
                        FVector::UpVector * 10.0f,
                    FVector(
                        FMath::Lerp(70.0f, 34.0f, TierT),
                        FMath::Lerp(52.0f, 27.0f, TierT),
                        FMath::Lerp(42.0f, 25.0f, TierT)) *
                        FMath::Lerp(
                            0.86f,
                            1.12f,
                            ZambeziVegetationUnitRandom(BranchSeed, 5683)),
                    BranchSeed,
                    ScalePreviewColor(
                        ConiferGreen,
                        0.80f + 0.18f *
                            ZambeziVegetationUnitRandom(BranchSeed, 5689)),
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendTemperateOpaqueLobe(
                    FMath::Lerp(Start, End, 0.68f),
                    FVector(
                        FMath::Lerp(80.0f, 38.0f, TierT),
                        FMath::Lerp(56.0f, 30.0f, TierT),
                        FMath::Lerp(34.0f, 24.0f, TierT)),
                    Seed + TierIndex * 101 + BranchIndex * 13,
                    ScalePreviewColor(
                        ConiferGreen,
                        0.82f + 0.16f * ZambeziVegetationUnitRandom(
                            TierIndex + BranchIndex, Seed)),
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendTemperateOpaqueLobe(
                    End,
                    FVector(
                        FMath::Lerp(92.0f, 42.0f, TierT),
                        FMath::Lerp(60.0f, 32.0f, TierT),
                        FMath::Lerp(38.0f, 24.0f, TierT)),
                    Seed + TierIndex * 103 + BranchIndex * 17,
                    ConiferGreen,
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
            }

            const float ConiferCrownBodyScale = FMath::Lerp(
                0.68f,
                0.82f,
                ZambeziVegetationUnitRandom(Seed + TierIndex, 5767));
            const FVector CrownBodyCenter(
                8.0f * TierT + FMath::Lerp(
                    -18.0f,
                    18.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5779)),
                -7.0f * TierT + FMath::Lerp(
                    -16.0f,
                    16.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5783)),
                TierZ + FMath::Lerp(
                    -10.0f,
                    18.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5791)));
            AppendTemperateOpaqueLobe(
                CrownBodyCenter,
                FVector(
                    TierRadius * ConiferCrownBodyScale,
                    TierRadius * ConiferCrownBodyScale * 0.91f,
                    FMath::Lerp(112.0f, 54.0f, TierT)),
                Seed + 1301 + TierIndex * 61,
                ScalePreviewColor(
                    ConiferGreen,
                    FMath::Lerp(
                        0.80f,
                        0.98f,
                        ZambeziVegetationUnitRandom(
                            Seed + TierIndex,
                            5801))),
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        AppendTemperateOpaqueLobe(
            FVector(0.0f, 0.0f, 900.0f),
            FVector(54.0f, 48.0f, 92.0f),
            Seed + 991,
            ConiferGreen,
            bRainforestPalette,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
    else
    {
        const bool bRainforestCanopyB =
            bRainforestPalette && Form == ETemperateVegetationForm::ConiferTree;
        const float LowerTrunkHeight = bRainforestCanopyB ? 470.0f : 410.0f;
        const float UpperTrunkHeight = bRainforestCanopyB ? 770.0f : 650.0f;
        const FVector LowerTrunkEnd(-12.0f, 10.0f, LowerTrunkHeight);
        const FVector UpperTrunkEnd(18.0f, -14.0f, UpperTrunkHeight);
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            LowerTrunkEnd,
            46.0f,
            28.0f,
            10,
            BarkBase,
            BarkTip,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        AppendZambeziColoredSegment(
            LowerTrunkEnd,
            UpperTrunkEnd,
            28.0f,
            12.0f,
            9,
            BarkTip,
            ScalePreviewColor(BarkTip, 1.12f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        const int32 BranchCount = bRainforestPalette ? 17 : 13;
        for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
        {
            const float Angle = FMath::Fmod(
                137.50776f * BranchIndex + Seed * 19.0f,
                360.0f) * PI / 180.0f;
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = bRainforestPalette
                ? FMath::Lerp(
                      bRainforestCanopyB ? 145.0f : 185.0f,
                      bRainforestCanopyB ? 285.0f : 345.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5843))
                : FMath::Lerp(
                      205.0f,
                      355.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5843));
            const float StartZ = bRainforestPalette
                ? FMath::Lerp(
                      LowerTrunkHeight * 0.80f,
                      UpperTrunkHeight * 0.94f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5851))
                : FMath::Lerp(
                      365.0f,
                      535.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5851));
            const float EndZ = bRainforestPalette
                ? UpperTrunkHeight + FMath::Lerp(
                      -95.0f,
                      bRainforestCanopyB ? 105.0f : 155.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5861))
                : FMath::Lerp(
                      585.0f,
                      790.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5861));
            const FVector Start(0.0f, 0.0f, StartZ);
            const FVector End = Direction * Radius + FVector::UpVector * EndZ;
            AppendZambeziColoredSegment(
                Start,
                End,
                13.0f,
                3.0f,
                7,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.10f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            const float CrownScale = bRainforestPalette
                ? FMath::Lerp(
                      0.72f,
                      1.18f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5879))
                : FMath::Lerp(
                      0.78f,
                      1.12f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5879));
            const FVector CrownRadii = bRainforestPalette
                ? FVector(
                      bRainforestCanopyB ? 112.0f : 138.0f,
                      bRainforestCanopyB ? 92.0f : 112.0f,
                      bRainforestCanopyB ? 88.0f : 96.0f) * CrownScale
                : FVector(158.0f, 132.0f, 112.0f) * CrownScale;
            AppendTemperateOpaqueLobe(
                End + FVector::UpVector * (18.0f + 18.0f * CrownScale),
                CrownRadii,
                Seed + BranchIndex * 29,
                ScalePreviewColor(
                    BroadleafGreen,
                    0.84f + 0.14f * ZambeziVegetationUnitRandom(
                        Seed + BranchIndex, 5903)),
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            if (bRainforestPalette && BranchIndex % 2 == 0)
            {
                const FVector Tangent(-Direction.Y, Direction.X, 0.0f);
                AppendTemperateOpaqueLobe(
                    End - Direction * (38.0f + 24.0f * CrownScale) +
                        Tangent * (BranchIndex % 4 < 2 ? 34.0f : -34.0f) +
                        FVector::UpVector * 58.0f,
                    CrownRadii * FVector(0.66f, 0.72f, 0.72f),
                    Seed + BranchIndex * 41 + 17,
                    ScalePreviewColor(BroadleafGreen, 0.92f),
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
            }
        }
        const int32 CrownFillCount = bRainforestPalette ? 10 : 8;
        for (int32 FillIndex = 0; FillIndex < CrownFillCount; ++FillIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(FillIndex) /
                static_cast<float>(CrownFillCount) + Seed * 0.05f;
            const float FillRadius = bRainforestPalette
                ? FMath::Lerp(
                      45.0f,
                      bRainforestCanopyB ? 115.0f : 155.0f,
                      ZambeziVegetationUnitRandom(Seed + FillIndex, 5923))
                : FMath::Lerp(
                      52.0f,
                      138.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + FillIndex,
                          5923));
            const float FillScale = bRainforestPalette
                ? FMath::Lerp(
                      0.62f,
                      1.08f,
                      ZambeziVegetationUnitRandom(Seed + FillIndex, 5939))
                : FMath::Lerp(
                      0.82f,
                      1.10f,
                      ZambeziVegetationUnitRandom(
                          Seed + FillIndex,
                          5939));
            AppendTemperateOpaqueLobe(
                FVector(
                    FMath::Cos(Angle) * FillRadius,
                    FMath::Sin(Angle) * FillRadius,
                    (bRainforestPalette ? UpperTrunkHeight + 70.0f : 700.0f) +
                        (bRainforestPalette
                             ? FMath::Lerp(
                                   -52.0f,
                                   98.0f,
                                   ZambeziVegetationUnitRandom(
                                       Seed + FillIndex, 5953))
                             : FMath::Lerp(
                                   -82.0f,
                                   92.0f,
                                   ZambeziVegetationUnitRandom(
                                       Seed + FillIndex,
                                       5953)))),
                FVector(172.0f, 145.0f, 126.0f) * FillScale,
                Seed + 700 + FillIndex * 37,
                BroadleafGreen,
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }

    if (bSecondaryMorphology && !bRainforestPalette)
    {
        // The B family is a different deterministic plant silhouette, not an
        // instance-scale variation. Seeded branch/crown placement above is
        // combined with form-specific proportions and a bounded growth lean.
        // The transform is baked into the mesh before normals are recomputed.
        for (FVector& Vertex : Vertices)
        {
            const float HeightT = FMath::Clamp(Vertex.Z / 1100.0f, 0.0f, 1.0f);
            if (Form == ETemperateVegetationForm::ConiferTree)
            {
                Vertex.X = Vertex.X * 0.80f + 44.0f * HeightT * HeightT;
                Vertex.Y *= 0.87f;
                Vertex.Z *= 1.18f;
            }
            else if (Form == ETemperateVegetationForm::BroadleafTree)
            {
                Vertex.X = Vertex.X * 0.79f - 38.0f * HeightT * HeightT;
                Vertex.Y *= 0.93f;
                Vertex.Z *= 1.16f;
            }
            else if (Form == ETemperateVegetationForm::RiparianShrub)
            {
                Vertex.X = Vertex.X * 1.22f + 18.0f * HeightT;
                Vertex.Y *= 0.76f;
                Vertex.Z *= 1.08f;
            }
            else
            {
                Vertex.X *= 1.18f;
                Vertex.Y *= 0.82f;
                Vertex.Z *= 0.86f;
            }
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty() ||
        Colors.Num() != Vertices.Num() || Uvs.Num() != Vertices.Num())
    {
        OutSummary += FString::Printf(
            TEXT("Temperate vegetation geometry contract failed for %s.\n"),
            AssetToken);
        return nullptr;
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_Temperate_%s_BuildSource"), AssetToken),
        Vertices,
        Triangles,
        Normals,
        Uvs,
        FLinearColor::White,
        Material,
        &Colors,
        false);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    const FString PackagePath = FString(MeshRoot) + AssetToken;
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        Material,
        true,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Prepared %s %s opaque volumetric vegetation: "
                 "vertices=%d triangles=%d Nanite=%d collision=false.\n"),
            ProfileLabel,
            AssetToken,
            Mesh->GetNumVertices(0),
            Mesh->GetNumTriangles(0),
            Mesh->IsNaniteEnabled());
    }
    return Mesh;
}

bool CreateTemperateOpaqueVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutBroadleafTreeA,
    UStaticMesh*& OutBroadleafTreeB,
    UStaticMesh*& OutConiferTreeA,
    UStaticMesh*& OutConiferTreeB,
    UStaticMesh*& OutShrubA,
    UStaticMesh*& OutShrubB,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        TemperateVegetationMaterialPath,
        TEXT("temperate-river"),
        0.06f,
        0.88f,
        1.13f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutBroadleafTreeA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_BroadleafTree_A_OpaqueV1"),
        ETemperateVegetationForm::BroadleafTree,
        6101,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutBroadleafTreeB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_BroadleafTree_B_OpaqueV1"),
        ETemperateVegetationForm::BroadleafTree,
        6113,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    OutConiferTreeA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_ConiferTree_A_OpaqueV1"),
        ETemperateVegetationForm::ConiferTree,
        6203,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutConiferTreeB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_ConiferTree_B_OpaqueV1"),
        ETemperateVegetationForm::ConiferTree,
        6217,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    OutShrubA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_RiparianShrub_A_OpaqueV1"),
        ETemperateVegetationForm::RiparianShrub,
        6301,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutShrubB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_RiparianShrub_B_OpaqueV1"),
        ETemperateVegetationForm::RiparianShrub,
        6317,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    OutGroundCoverA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_GroundCover_A_OpaqueV1"),
        ETemperateVegetationForm::GroundCover,
        6421,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutGroundCoverB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_GroundCover_B_OpaqueV1"),
        ETemperateVegetationForm::GroundCover,
        6437,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    const bool bComplete =
        OutBroadleafTreeA && OutBroadleafTreeB &&
        OutConiferTreeA && OutConiferTreeB &&
        OutShrubA && OutShrubB && OutGroundCoverA && OutGroundCoverB;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete opaque temperate vegetation family.\n");
    }
    return bComplete;
}

UMaterialInstanceConstant* CreateChilkoMutedGroundCoverMaterial(
    UMaterialInterface* Parent,
    FString& OutSummary)
{
    if (!Parent)
    {
        return nullptr;
    }
    const FString AssetName =
        FPackageName::GetLongPackageAssetName(
            ChilkoMutedGroundCoverMaterialPath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"),
        ChilkoMutedGroundCoverMaterialPath,
        *AssetName);
    UPackage* Package = CreatePackage(ChilkoMutedGroundCoverMaterialPath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterialInstanceConstant* Instance =
        LoadObject<UMaterialInstanceConstant>(nullptr, *ObjectPath);
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(Parent);
    Instance->ClearParameterValuesEditorOnly();
    // The current shared mesh palette becomes fluorescent under Lava
    // Canyon's open-sky review lighting. Apply a Chilko-only dry-meadow olive
    // retone and reduce the shadow fill while preserving the original mesh,
    // instance distribution, opacity, roughness, and Futaleufu parent output.
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("VegetationColorScale")),
        FLinearColor(0.62f, 0.38f, 0.24f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("VegetationShadowFillScale")),
        0.28f);
    Instance->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        ChilkoMutedGroundCoverMaterialPath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += TEXT(
            "Failed to save the Chilko muted ground-cover material.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Built a Chilko-only muted dry-meadow ground-cover material V3; "
        "the shared Futaleufu temperate parent retains identity defaults.\n");
    return Instance;
}

bool CreatePacuareOpaqueRainforestVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutCanopyTreeA,
    UStaticMesh*& OutCanopyTreeB,
    UStaticMesh*& OutShrub,
    UStaticMesh*& OutGroundCover,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        PacuareRainforestVegetationMaterialPath,
        TEXT("Pacuare rainforest"),
        0.20f,
        0.84f,
        1.16f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutCanopyTreeA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_CanopyTree_A_OpaqueV2"),
        ETemperateVegetationForm::BroadleafTree,
        7103,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    // The second canopy form deliberately reuses the solid broadleaf grammar
    // with a different deterministic seed. It adds crown/branch variation
    // without importing the conifer silhouette that made no ecological sense
    // in the Upper Huacas rainforest fallback.
    OutCanopyTreeB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_CanopyTree_B_OpaqueV2"),
        ETemperateVegetationForm::ConiferTree,
        7207,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    OutShrub = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_RiparianShrub_A_OpaqueV2"),
        ETemperateVegetationForm::RiparianShrub,
        7309,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    OutGroundCover = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_RainforestGroundCover_A_OpaqueV2"),
        ETemperateVegetationForm::GroundCover,
        7411,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    const bool bComplete =
        OutCanopyTreeA && OutCanopyTreeB && OutShrub && OutGroundCover;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete Pacuare opaque rainforest family.\n");
    }
    return bComplete;
}

bool ValidateZambeziOpaqueVegetationMaterial(UMaterialInterface* Material)
{
    const UMaterial* BaseMaterial = Material ? Material->GetMaterial() : nullptr;
    return BaseMaterial && BaseMaterial->BlendMode == BLEND_Opaque &&
        !BaseMaterial->TwoSided &&
        BaseMaterial->GetUsageByFlag(MATUSAGE_InstancedStaticMeshes) &&
        BaseMaterial->GetUsageByFlag(MATUSAGE_Nanite);
}

UMaterialInstanceConstant* LoadOrCreateZambeziRunnableLaunchTalusMaterial(
    FString& OutSummary)
{
    UMaterialInterface* ParentMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        ZambeziRunnableLaunchTalusParentMaterialPath);
    if (!ParentMaterial)
    {
        OutSummary += TEXT(
            "Failed to load the project-owned river-boulder parent for the "
            "Zambezi launch talus.\n");
        return nullptr;
    }

    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"),
        ZambeziRunnableLaunchTalusMaterialPackagePath,
        ZambeziRunnableLaunchTalusMaterialAssetName);
    UPackage* Package = CreatePackage(
        ZambeziRunnableLaunchTalusMaterialPackagePath);
    if (!Package)
    {
        return nullptr;
    }

    UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(
        StaticLoadObject(
            UMaterialInstanceConstant::StaticClass(),
            nullptr,
            *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(
            Package,
            ZambeziRunnableLaunchTalusMaterialAssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            ZambeziRunnableLaunchTalusMaterialAssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(ParentMaterial);
    // Keep enough of the reviewed CC0 scan to preserve real microstructure,
    // but mix most of its green/ochre appearance into the project-authored
    // neutral mineral branch. This remains a generic visual analog and makes
    // no Batoka lithology claim.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockVisualSourceBlend")),
        ZambeziRunnableLaunchTalusReviewedSourceBlend);
    // The scalar remains a dry fail-safe. Launch talus binds each instance's
    // conditioned local visual-surface elevation through custom-data channel
    // zero, so a curved reach never collapses to one invented flat waterline.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockWaterlineZCm")),
        -1.0e7f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockWetBandWidthCm")),
        ZambeziRunnableLaunchTalusWetBandWidthCm);
    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        ZambeziRunnableLaunchTalusMaterialPackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save %s.\n"),
            *ObjectPath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Built Zambezi launch-talus material %s with %.2f reviewed-source "
             "blend and dry-bank waterline fail-safe.\n"),
        *ObjectPath,
        ZambeziRunnableLaunchTalusReviewedSourceBlend);
    return Instance;
}
}
