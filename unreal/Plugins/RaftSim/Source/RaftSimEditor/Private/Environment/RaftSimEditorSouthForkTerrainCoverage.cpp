#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr int32 SouthForkFarFieldCorridorReliefTransitionCells = 3;
constexpr float SouthForkMinimumCompletedShorelineDepthM = 0.03f;
constexpr float SouthForkMaximumCompletedShorelineDepthM = 0.25f;
constexpr float SouthForkMaximumTerrainClippedBankHeightM = 0.05f;
constexpr float SouthForkMinimumVisibleWaterDepthM = 0.005f;

struct FSouthForkClippedWaterVertex
{
    FVector Position = FVector::ZeroVector;
    FVector2D Uv = FVector2D::ZeroVector;
    FLinearColor Color = FLinearColor::Transparent;
    float ShorelineDepthM = 0.0f;
    FVector Normal = FVector::UpVector;
    FVector FlowTangent = FVector::ForwardVector;
};

FSouthForkClippedWaterVertex InterpolateClippedWaterVertex(
    const FSouthForkClippedWaterVertex& A,
    const FSouthForkClippedWaterVertex& B,
    float Alpha)
{
    FSouthForkClippedWaterVertex Result;
    Result.Position = FMath::Lerp(A.Position, B.Position, Alpha);
    Result.Uv = FMath::Lerp(A.Uv, B.Uv, Alpha);
    Result.Color = FMath::Lerp(A.Color, B.Color, Alpha);
    Result.ShorelineDepthM = FMath::Lerp(
        A.ShorelineDepthM, B.ShorelineDepthM, Alpha);
    Result.Normal = FMath::Lerp(A.Normal, B.Normal, Alpha).GetSafeNormal(
        KINDA_SMALL_NUMBER, FVector::UpVector);
    Result.FlowTangent = FMath::Lerp(
        A.FlowTangent, B.FlowTangent, Alpha).GetSafeNormal(
            KINDA_SMALL_NUMBER, FVector::ForwardVector);
    return Result;
}

template <typename TSignedDistance>
void ClipSouthForkWaterPolygon(
    TArray<FSouthForkClippedWaterVertex>& InOutPolygon,
    TSignedDistance SignedDistance)
{
    if (InOutPolygon.IsEmpty())
    {
        return;
    }

    TArray<FSouthForkClippedWaterVertex> Clipped;
    Clipped.Reserve(InOutPolygon.Num() + 2);
    FSouthForkClippedWaterVertex Previous = InOutPolygon.Last();
    float PreviousDistance = SignedDistance(Previous);
    bool bPreviousInside = PreviousDistance >= 0.0f;
    for (const FSouthForkClippedWaterVertex& Current : InOutPolygon)
    {
        const float CurrentDistance = SignedDistance(Current);
        const bool bCurrentInside = CurrentDistance >= 0.0f;
        if (bCurrentInside != bPreviousInside)
        {
            const float Denominator = PreviousDistance - CurrentDistance;
            const float Alpha = FMath::IsNearlyZero(Denominator)
                ? 0.5f
                : FMath::Clamp(PreviousDistance / Denominator, 0.0f, 1.0f);
            Clipped.Add(InterpolateClippedWaterVertex(
                Previous, Current, Alpha));
        }
        if (bCurrentInside)
        {
            Clipped.Add(Current);
        }
        Previous = Current;
        PreviousDistance = CurrentDistance;
        bPreviousInside = bCurrentInside;
    }
    InOutPolygon = MoveTemp(Clipped);
}
}

FLinearColor DecodeSouthForkPreviewSrgbColor(const FLinearColor& Encoded)
{
    const FColor Srgb(
        FMath::RoundToInt(FMath::Clamp(Encoded.R, 0.0f, 1.0f) * 255.0f),
        FMath::RoundToInt(FMath::Clamp(Encoded.G, 0.0f, 1.0f) * 255.0f),
        FMath::RoundToInt(FMath::Clamp(Encoded.B, 0.0f, 1.0f) * 255.0f),
        FMath::RoundToInt(FMath::Clamp(Encoded.A, 0.0f, 1.0f) * 255.0f));
    return FLinearColor::FromSRGBColor(Srgb);
}

float DecodeSouthForkHeightM(
    uint16 Encoded,
    double MinimumM,
    double MaximumM)
{
    return static_cast<float>(
        MinimumM + (MaximumM - MinimumM) *
            static_cast<double>(Encoded) / 65535.0);
}

FLinearColor CompleteSouthForkShorelinePresentation(
    FLinearColor HydraulicPresentation,
    float ShorelineDepthM,
    int64& InOutCompletionVertexCount)
{
    // Presentation alpha is the solver-owned wet mask. Close only shallow
    // presentation discrepancies where the decoded terrain is demonstrably
    // below the decoded water surface. The quarter-metre cap keeps this from
    // promoting dry solver cells into deep visual water. This is visual
    // procedural completion: it neither modifies authoritative solver arrays
    // nor adds collision.
    const bool bCompleteMissingShoreline =
        HydraulicPresentation.A <= 0.5f &&
        ShorelineDepthM >= SouthForkMinimumCompletedShorelineDepthM &&
        ShorelineDepthM <= SouthForkMaximumCompletedShorelineDepthM;
    if (bCompleteMissingShoreline)
    {
        HydraulicPresentation.A = 1.0f;
        HydraulicPresentation.G = FMath::Max(
            HydraulicPresentation.G,
            FMath::Clamp(ShorelineDepthM / 2.5f, 0.0f, 1.0f));
        ++InOutCompletionVertexCount;
    }
    return HydraulicPresentation;
}

bool ConditionSouthForkDryWaterSurfaceRow(
    const TArray<FLinearColor>& SourceHydraulicPresentation,
    TArray<float>& InOutSurfaceElevationsM,
    int32& OutLeftWetColumn,
    int32& OutRightWetColumn)
{
    OutLeftWetColumn = INDEX_NONE;
    OutRightWetColumn = INDEX_NONE;
    if (SourceHydraulicPresentation.IsEmpty() ||
        SourceHydraulicPresentation.Num() != InOutSurfaceElevationsM.Num())
    {
        return false;
    }

    for (int32 Column = 0; Column < SourceHydraulicPresentation.Num(); ++Column)
    {
        if (SourceHydraulicPresentation[Column].A > 0.5f)
        {
            if (OutLeftWetColumn == INDEX_NONE)
            {
                OutLeftWetColumn = Column;
            }
            OutRightWetColumn = Column;
        }
    }
    if (OutLeftWetColumn == INDEX_NONE)
    {
        return false;
    }

    // Dry pixels in the cooked hydraulic surface store a terrain-conditioned
    // sentinel rather than a valid free-surface elevation. Interpolating that
    // sentinel into a clipped shoreline makes water climb the bank (more than
    // twenty metres in the Meat Grinder source row). Fill dry samples from
    // the nearest solver-wet samples before any visual refinement. This does
    // not change wet solver values, masks, collision, or gameplay hydraulics.
    TArray<int32> NearestWetOnLeft;
    TArray<int32> NearestWetOnRight;
    NearestWetOnLeft.Init(INDEX_NONE, SourceHydraulicPresentation.Num());
    NearestWetOnRight.Init(INDEX_NONE, SourceHydraulicPresentation.Num());
    int32 NearestWet = INDEX_NONE;
    for (int32 Column = 0; Column < SourceHydraulicPresentation.Num(); ++Column)
    {
        if (SourceHydraulicPresentation[Column].A > 0.5f)
        {
            NearestWet = Column;
        }
        NearestWetOnLeft[Column] = NearestWet;
    }
    NearestWet = INDEX_NONE;
    for (int32 Column = SourceHydraulicPresentation.Num() - 1;
         Column >= 0;
         --Column)
    {
        if (SourceHydraulicPresentation[Column].A > 0.5f)
        {
            NearestWet = Column;
        }
        NearestWetOnRight[Column] = NearestWet;
    }

    const TArray<float> SourceElevationsM = InOutSurfaceElevationsM;
    for (int32 Column = 0; Column < SourceHydraulicPresentation.Num(); ++Column)
    {
        if (SourceHydraulicPresentation[Column].A > 0.5f)
        {
            continue;
        }
        const int32 Left = NearestWetOnLeft[Column];
        const int32 Right = NearestWetOnRight[Column];
        if (Left != INDEX_NONE && Right != INDEX_NONE && Left != Right)
        {
            const float Alpha = static_cast<float>(Column - Left) /
                static_cast<float>(Right - Left);
            InOutSurfaceElevationsM[Column] = FMath::Lerp(
                SourceElevationsM[Left], SourceElevationsM[Right], Alpha);
        }
        else
        {
            const int32 Boundary = Left != INDEX_NONE ? Left : Right;
            InOutSurfaceElevationsM[Column] = SourceElevationsM[Boundary];
        }
    }
    return true;
}

bool PrepareSouthForkWaterSurfaceRow(
    const TArray<uint16>& EncodedSurfaceHeights,
    const TArray<FLinearColor>& SourceHydraulicPresentation,
    int32 Width,
    int32 Row,
    double MinimumElevationM,
    double MaximumElevationM,
    TArray<float>& OutSurfaceElevationsM,
    TArray<FLinearColor>& OutHydraulicPresentation,
    int32& OutLeftWetColumn,
    int32& OutRightWetColumn)
{
    const int32 RowStart = Row * Width;
    if (Width < 1 || Row < 0 ||
        !EncodedSurfaceHeights.IsValidIndex(RowStart + Width - 1) ||
        !SourceHydraulicPresentation.IsValidIndex(RowStart + Width - 1))
    {
        return false;
    }
    OutSurfaceElevationsM.SetNumUninitialized(Width);
    OutHydraulicPresentation.SetNumUninitialized(Width);
    for (int32 Column = 0; Column < Width; ++Column)
    {
        const int32 Index = RowStart + Column;
        OutSurfaceElevationsM[Column] = DecodeSouthForkHeightM(
            EncodedSurfaceHeights[Index],
            MinimumElevationM,
            MaximumElevationM);
        OutHydraulicPresentation[Column] =
            SourceHydraulicPresentation[Index];
    }
    return ConditionSouthForkDryWaterSurfaceRow(
        OutHydraulicPresentation, OutSurfaceElevationsM,
        OutLeftWetColumn, OutRightWetColumn);
}

bool ShouldEmitSouthForkShorelineCell(
    const FLinearColor& I0,
    const FLinearColor& I1,
    const FLinearColor& I2,
    const FLinearColor& I3,
    float I0ShorelineDepthM,
    float I1ShorelineDepthM,
    float I2ShorelineDepthM,
    float I3ShorelineDepthM,
    int64& InOutTransitionCellCount)
{
    const bool bI0Wet = I0.A > 0.5f;
    const bool bI1Wet = I1.A > 0.5f;
    const bool bI2Wet = I2.A > 0.5f;
    const bool bI3Wet = I3.A > 0.5f;
    const bool bAnyWetVertex = bI0Wet || bI1Wet || bI2Wet || bI3Wet;
    const bool bAllWetVertices = bI0Wet && bI1Wet && bI2Wet && bI3Wet;
    if (!bAnyWetVertex || bAllWetVertices)
    {
        return bAllWetVertices;
    }

    const bool bI0BoundedBank = !bI0Wet &&
        I0ShorelineDepthM >= -SouthForkMaximumTerrainClippedBankHeightM &&
        I0ShorelineDepthM < SouthForkMinimumCompletedShorelineDepthM;
    const bool bI1BoundedBank = !bI1Wet &&
        I1ShorelineDepthM >= -SouthForkMaximumTerrainClippedBankHeightM &&
        I1ShorelineDepthM < SouthForkMinimumCompletedShorelineDepthM;
    const bool bI2BoundedBank = !bI2Wet &&
        I2ShorelineDepthM >= -SouthForkMaximumTerrainClippedBankHeightM &&
        I2ShorelineDepthM < SouthForkMinimumCompletedShorelineDepthM;
    const bool bI3BoundedBank = !bI3Wet &&
        I3ShorelineDepthM >= -SouthForkMaximumTerrainClippedBankHeightM &&
        I3ShorelineDepthM < SouthForkMinimumCompletedShorelineDepthM;
    const bool bHasBoundedBankVertex =
        bI0BoundedBank || bI1BoundedBank || bI2BoundedBank || bI3BoundedBank;
    const bool bHasOutsideSkirtVertex =
        (!bI0Wet && !bI0BoundedBank) ||
        (!bI1Wet && !bI1BoundedBank) ||
        (!bI2Wet && !bI2BoundedBank) ||
        (!bI3Wet && !bI3BoundedBank);
    if (!bHasBoundedBankVertex || bHasOutsideSkirtVertex)
    {
        return false;
    }

    // Emit only a five-centimetre terrain-clipped bank skirt. Deep missing
    // mask gaps and tall dry-bank cells remain absent, avoiding broad hidden
    // water quads and preserving the solver wet mask as presentation
    // authority. This mesh has no collision and does not alter hydraulics.
    ++InOutTransitionCellCount;
    return true;
}

bool RefineSouthForkWaterPresentationGrid(
    int32 SubdivisionFactor,
    int32& InOutWidth,
    int32& InOutHeight,
    TArray<FVector>& InOutVertices,
    TArray<FVector2D>& InOutUvs,
    TArray<FLinearColor>& InOutColors,
    TArray<float>& InOutShorelineDepthsM)
{
    const int32 SourceCount = InOutWidth * InOutHeight;
    if (SubdivisionFactor < 1 || InOutWidth < 2 || InOutHeight < 2 ||
        InOutVertices.Num() != SourceCount || InOutUvs.Num() != SourceCount ||
        InOutColors.Num() != SourceCount ||
        InOutShorelineDepthsM.Num() != SourceCount)
    {
        return false;
    }
    if (SubdivisionFactor == 1)
    {
        return true;
    }

    const int32 SourceWidth = InOutWidth;
    const int32 SourceHeight = InOutHeight;
    TArray<FVector> SourceVertices = MoveTemp(InOutVertices);
    TArray<FVector2D> SourceUvs = MoveTemp(InOutUvs);
    TArray<FLinearColor> SourceColors = MoveTemp(InOutColors);
    TArray<float> SourceShorelineDepthsM = MoveTemp(InOutShorelineDepthsM);
    const int32 RefinedWidth = (SourceWidth - 1) * SubdivisionFactor + 1;
    const int32 RefinedHeight = (SourceHeight - 1) * SubdivisionFactor + 1;
    const int32 RefinedCount = RefinedWidth * RefinedHeight;
    InOutVertices.SetNumUninitialized(RefinedCount);
    InOutUvs.SetNumUninitialized(RefinedCount);
    InOutColors.SetNumUninitialized(RefinedCount);
    InOutShorelineDepthsM.SetNumUninitialized(RefinedCount);

    for (int32 Row = 0; Row < RefinedHeight; ++Row)
    {
        const int32 SourceRow0 = FMath::Min(Row / SubdivisionFactor, SourceHeight - 1);
        const int32 SourceRow1 = FMath::Min(SourceRow0 + 1, SourceHeight - 1);
        const float RowAlpha = static_cast<float>(Row % SubdivisionFactor) /
            static_cast<float>(SubdivisionFactor);
        for (int32 Column = 0; Column < RefinedWidth; ++Column)
        {
            const int32 SourceColumn0 = FMath::Min(
                Column / SubdivisionFactor, SourceWidth - 1);
            const int32 SourceColumn1 = FMath::Min(
                SourceColumn0 + 1, SourceWidth - 1);
            const float ColumnAlpha = static_cast<float>(Column % SubdivisionFactor) /
                static_cast<float>(SubdivisionFactor);
            const int32 I00 = SourceRow0 * SourceWidth + SourceColumn0;
            const int32 I01 = SourceRow0 * SourceWidth + SourceColumn1;
            const int32 I10 = SourceRow1 * SourceWidth + SourceColumn0;
            const int32 I11 = SourceRow1 * SourceWidth + SourceColumn1;
            const int32 Destination = Row * RefinedWidth + Column;
            auto Bilinear = [ColumnAlpha, RowAlpha](const auto& V00, const auto& V01,
                                                    const auto& V10, const auto& V11)
            {
                return FMath::Lerp(
                    FMath::Lerp(V00, V01, ColumnAlpha),
                    FMath::Lerp(V10, V11, ColumnAlpha), RowAlpha);
            };
            InOutVertices[Destination] = Bilinear(
                SourceVertices[I00], SourceVertices[I01],
                SourceVertices[I10], SourceVertices[I11]);
            InOutUvs[Destination] = Bilinear(
                SourceUvs[I00], SourceUvs[I01], SourceUvs[I10], SourceUvs[I11]);
            InOutColors[Destination] = Bilinear(
                SourceColors[I00], SourceColors[I01],
                SourceColors[I10], SourceColors[I11]);
            InOutShorelineDepthsM[Destination] = Bilinear(
                SourceShorelineDepthsM[I00], SourceShorelineDepthsM[I01],
                SourceShorelineDepthsM[I10], SourceShorelineDepthsM[I11]);
        }
    }
    InOutWidth = RefinedWidth;
    InOutHeight = RefinedHeight;
    return true;
}

bool SmoothSouthForkWaterVisibilityLongitudinally(
    int32 Radius,
    int32 Width,
    int32 Height,
    TArray<FLinearColor>& InOutHydraulicPresentation)
{
    if (Radius < 1 || Width < 1 || Height < 2 ||
        InOutHydraulicPresentation.Num() != Width * Height)
    {
        return false;
    }
    const TArray<FLinearColor> Source = InOutHydraulicPresentation;
    for (int32 Row = 0; Row < Height; ++Row)
    {
        for (int32 Column = 0; Column < Width; ++Column)
        {
            float WeightedAlpha = 0.0f;
            float WeightSum = 0.0f;
            for (int32 Offset = -Radius; Offset <= Radius; ++Offset)
            {
                const int32 SampleRow = FMath::Clamp(Row + Offset, 0, Height - 1);
                const float Weight = static_cast<float>(Radius + 1 - FMath::Abs(Offset));
                WeightedAlpha += Source[SampleRow * Width + Column].A * Weight;
                WeightSum += Weight;
            }
            InOutHydraulicPresentation[Row * Width + Column].A =
                WeightedAlpha / WeightSum;
        }
    }
    return true;
}

bool BuildSouthForkTerrainClippedWaterGeometry(
    const TArray<FVector>& GridVertices,
    const TArray<FVector2D>& GridUvs,
    const TArray<FLinearColor>& GridColors,
    const TArray<float>& GridShorelineDepthsM,
    int32 GridWidth,
    int32 GridHeight,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector2D>& OutUvs,
    TArray<FLinearColor>& OutColors,
    TArray<FVector>& OutNormals,
    TArray<FProcMeshTangent>& OutTangents,
    int64& InOutTransitionCellCount)
{
    const int32 GridCount = GridWidth * GridHeight;
    if (GridWidth < 2 || GridHeight < 2 || GridVertices.Num() != GridCount ||
        GridUvs.Num() != GridCount || GridColors.Num() != GridCount ||
        GridShorelineDepthsM.Num() != GridCount)
    {
        return false;
    }

    TArray<int32> FullGridTriangles;
    FullGridTriangles.Reserve((GridWidth - 1) * (GridHeight - 1) * 6);
    for (int32 Row = 0; Row < GridHeight - 1; ++Row)
    {
        for (int32 Column = 0; Column < GridWidth - 1; ++Column)
        {
            const int32 I0 = Row * GridWidth + Column;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + GridWidth;
            const int32 I3 = I2 + 1;
            FullGridTriangles.Append({I0, I1, I2, I1, I3, I2});
        }
    }
    const TArray<FVector> GridNormals =
        ComputePreviewMeshNormals(GridVertices, FullGridTriangles);
    const TArray<FProcMeshTangent> GridTangents =
        BuildSouthForkFlowTangents(GridVertices, GridWidth, GridHeight);

    OutVertices.Reset();
    OutTriangles.Reset();
    OutUvs.Reset();
    OutColors.Reset();
    OutNormals.Reset();
    OutTangents.Reset();
    OutVertices.Reserve(FullGridTriangles.Num());
    OutTriangles.Reserve(FullGridTriangles.Num());
    OutUvs.Reserve(FullGridTriangles.Num());
    OutColors.Reserve(FullGridTriangles.Num());
    OutNormals.Reserve(FullGridTriangles.Num());
    OutTangents.Reserve(FullGridTriangles.Num());

    auto MakeVertex = [&](int32 Index)
    {
        FSouthForkClippedWaterVertex Vertex;
        Vertex.Position = GridVertices[Index];
        Vertex.Uv = GridUvs[Index];
        Vertex.Color = GridColors[Index];
        Vertex.ShorelineDepthM = GridShorelineDepthsM[Index];
        Vertex.Normal = GridNormals[Index];
        Vertex.FlowTangent = GridTangents[Index].TangentX;
        return Vertex;
    };
    auto IsVisibleWater = [&](int32 Index)
    {
        return GridColors[Index].A >= 0.5f &&
            GridShorelineDepthsM[Index] >= SouthForkMinimumVisibleWaterDepthM;
    };

    for (int32 Row = 0; Row < GridHeight - 1; ++Row)
    {
        for (int32 Column = 0; Column < GridWidth - 1; ++Column)
        {
            const int32 I0 = Row * GridWidth + Column;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + GridWidth;
            const int32 I3 = I2 + 1;
            const bool bVisible[] = {
                IsVisibleWater(I0), IsVisibleWater(I1),
                IsVisibleWater(I2), IsVisibleWater(I3)};
            const bool bAnyVisible =
                bVisible[0] || bVisible[1] || bVisible[2] || bVisible[3];
            const bool bAllVisible =
                bVisible[0] && bVisible[1] && bVisible[2] && bVisible[3];
            const int32 TriangleIndices[][3] = {
                {I0, I1, I2},
                {I1, I3, I2}};
            const int32 TriangleCountBeforeCell = OutTriangles.Num();
            for (const int32 (&Triangle)[3] : TriangleIndices)
            {
                TArray<FSouthForkClippedWaterVertex> Polygon{
                    MakeVertex(Triangle[0]),
                    MakeVertex(Triangle[1]),
                    MakeVertex(Triangle[2])};
                ClipSouthForkWaterPolygon(
                    Polygon,
                    [](const FSouthForkClippedWaterVertex& Vertex)
                    {
                        return Vertex.Color.A - 0.5f;
                    });
                ClipSouthForkWaterPolygon(
                    Polygon,
                    [](const FSouthForkClippedWaterVertex& Vertex)
                    {
                        return Vertex.ShorelineDepthM -
                            SouthForkMinimumVisibleWaterDepthM;
                    });
                if (Polygon.Num() < 3)
                {
                    continue;
                }

                const int32 VertexBase = OutVertices.Num();
                for (const FSouthForkClippedWaterVertex& Vertex : Polygon)
                {
                    OutVertices.Add(Vertex.Position);
                    OutUvs.Add(Vertex.Uv);
                    OutColors.Add(Vertex.Color);
                    OutNormals.Add(Vertex.Normal);
                    OutTangents.Add(FProcMeshTangent(
                        Vertex.FlowTangent, false));
                }
                for (int32 FanIndex = 1; FanIndex < Polygon.Num() - 1; ++FanIndex)
                {
                    const FVector EdgeA =
                        Polygon[FanIndex].Position - Polygon[0].Position;
                    const FVector EdgeB =
                        Polygon[FanIndex + 1].Position - Polygon[0].Position;
                    if (FVector::CrossProduct(EdgeA, EdgeB).SizeSquared() <= 1.0f)
                    {
                        continue;
                    }
                    OutTriangles.Append({
                        VertexBase,
                        VertexBase + FanIndex,
                        VertexBase + FanIndex + 1});
                }
            }
            if (bAnyVisible && !bAllVisible &&
                OutTriangles.Num() > TriangleCountBeforeCell)
            {
                ++InOutTransitionCellCount;
            }
        }
    }
    return !OutTriangles.IsEmpty();
}

bool ApplySouthForkWaterPresentationMicroRelief(
    TArray<FVector>& InOutVertices,
    const TArray<FVector2D>& Uvs,
    const TArray<FLinearColor>& HydraulicPresentation,
    const TArray<float>& ShorelineDepthsM,
    float& OutMaximumAbsoluteDisplacementCm)
{
    OutMaximumAbsoluteDisplacementCm = 0.0f;
    if (InOutVertices.IsEmpty() || Uvs.Num() != InOutVertices.Num() ||
        HydraulicPresentation.Num() != InOutVertices.Num() ||
        ShorelineDepthsM.Num() != InOutVertices.Num())
    {
        return false;
    }

    for (int32 Index = 0; Index < InOutVertices.Num(); ++Index)
    {
        // UVs preserve the registered river coordinates at one UV unit per
        // three metres. Add relief only after the 4 m hydraulic field has
        // been refined to a 2 m visual grid, so these smaller wave shoulders
        // create geometric normal variation instead of being interpolated
        // away. The source solver height, wet mask, collision, and navigation
        // products remain unchanged.
        const float StationM = Uvs[Index].X * 3.0f;
        const float LateralM = Uvs[Index].Y * 3.0f;
        const FLinearColor& Hydraulic = HydraulicPresentation[Index];
        const float HydraulicEnergy = FMath::Clamp(
            Hydraulic.R * 0.72f + Hydraulic.B * 0.48f,
            0.0f, 1.0f);
        const float WetMask = FMath::Clamp(
            (Hydraulic.A - 0.35f) / 0.65f, 0.0f, 1.0f);
        const float ShorelineFade = FMath::SmoothStep(
            0.08f, 0.60f, ShorelineDepthsM[Index]);

        const float PhaseWarp =
            0.62f * FMath::Sin(StationM * 0.083f + LateralM * 0.041f);
        const float CalmReliefM =
            0.060f * FMath::Sin(StationM * 0.63f + LateralM * 0.13f + PhaseWarp) +
            0.030f * FMath::Sin(StationM * 1.03f - LateralM * 0.27f - PhaseWarp);
        const float HydraulicReliefM = HydraulicEnergy *
            (0.090f * FMath::Sin(StationM * 0.41f + LateralM * 0.62f) +
             0.060f * FMath::Sin(StationM * 0.78f - LateralM * 0.44f));
        const float BreakingEnergy = FMath::SmoothStep(
            0.045f, 0.62f, FMath::Clamp(Hydraulic.R, 0.0f, 1.0f));
        const float BreakingReliefM = BreakingEnergy *
            (0.260f * FMath::Sin(
                StationM * 0.24f + LateralM * 0.11f + PhaseWarp) +
             0.160f * FMath::Sin(
                StationM * 0.51f - LateralM * 0.19f - PhaseWarp));
        const float DisplacementCm =
            (CalmReliefM + HydraulicReliefM + BreakingReliefM) *
            ShorelineFade * WetMask * 100.0f;
        InOutVertices[Index].Z += DisplacementCm;
        OutMaximumAbsoluteDisplacementCm = FMath::Max(
            OutMaximumAbsoluteDisplacementCm, FMath::Abs(DisplacementCm));
    }
    return true;
}

FSouthForkAeratedWaterOverlaySample ComputeSouthForkAeratedWaterOverlaySample(
    const FLinearColor& HydraulicPresentation,
    float ShorelineDepthM,
    float StationM,
    float LateralM)
{
    FSouthForkAeratedWaterOverlaySample Sample;
    // The red channel is the conditioned solver foam field. Requiring a
    // positive red value is the authority boundary: procedural phase and
    // shading can break up an existing aerated region, but can never create a
    // whitewater patch in calm or merely fast water.
    const float SolverFoam = FMath::Clamp(HydraulicPresentation.R, 0.0f, 1.0f);
    const float WetMask = FMath::SmoothStep(
        0.50f, 0.90f, FMath::Clamp(HydraulicPresentation.A, 0.0f, 1.0f));
    const float ShorelineFade = FMath::SmoothStep(
        0.10f, 0.70f, ShorelineDepthM);
    const float FoamCore = FMath::SmoothStep(0.035f, 0.58f, SolverFoam);
    const float Authority = FoamCore * WetMask * ShorelineFade;
    if (SolverFoam <= 0.0f || Authority <= KINDA_SMALL_NUMBER)
    {
        return Sample;
    }

    // A pair of incommensurate river-coordinate phases produces bounded
    // crest shoulders without lifting refined mesh facets into white polygon
    // fins. The broad water already carries hydraulic micro-relief, so this
    // overlay needs only a shallow separation (under 14 cm) to avoid z-fight;
    // it carries no collision and leaves the water/solver arrays untouched.
    const float PhaseWarp =
        0.31f * FMath::Sin(StationM * 0.113f - LateralM * 0.071f);
    const float CrestPulse = 0.5f + 0.5f * FMath::Sin(
        StationM * 0.69f + LateralM * 0.41f + PhaseWarp);
    const float LacePrimary = 0.5f + 0.5f * FMath::Sin(
        StationM * 1.57f + LateralM * 0.83f + PhaseWarp * 3.0f);
    const float LaceCross = 0.5f + 0.5f * FMath::Sin(
        StationM * 0.91f - LateralM * 1.37f - PhaseWarp * 2.0f);
    const float LaceCoverage = FMath::SmoothStep(
        0.28f,
        0.80f,
        FMath::Clamp(0.68f * LacePrimary + 0.32f * LaceCross, 0.0f, 1.0f));
    Sample.Opacity = FMath::Clamp(
        Authority *
            (0.16f + (0.48f + 0.24f * SolverFoam) * LaceCoverage),
        0.0f,
        0.88f);
    Sample.VerticalDisplacementCm = FMath::Clamp(
        Authority *
            (2.5f + 6.5f * SolverFoam + 5.0f * CrestPulse) *
            (0.42f + 0.58f * LaceCoverage),
        0.0f,
        14.0f);
    Sample.Color = FMath::Lerp(
        FLinearColor(0.72f, 0.78f, 0.79f, 1.0f),
        FLinearColor(0.96f, 0.99f, 1.0f, 1.0f),
        FMath::Clamp(Authority, 0.0f, 1.0f));
    Sample.Color.A = Sample.Opacity;
    return Sample;
}

bool BuildSouthForkRefinedWhitewaterOverlayGeometry(
    const TArray<FVector>& BaseVertices,
    const TArray<FVector2D>& BaseUvs,
    const TArray<FLinearColor>& BaseHydraulicPresentation,
    const TArray<float>& BaseShorelineDepthsM,
    int32 BaseWidth,
    int32 BaseHeight,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector2D>& OutUvs,
    TArray<FLinearColor>& OutColors,
    int32& OutWidth,
    int32& OutHeight)
{
    OutVertices = BaseVertices;
    OutUvs = BaseUvs;
    TArray<FLinearColor> HydraulicPresentation = BaseHydraulicPresentation;
    TArray<float> ShorelineDepthsM = BaseShorelineDepthsM;
    OutWidth = BaseWidth;
    OutHeight = BaseHeight;
    if (!RefineSouthForkWaterPresentationGrid(
            2, OutWidth, OutHeight, OutVertices, OutUvs,
            HydraulicPresentation, ShorelineDepthsM))
    {
        return false;
    }

    OutColors.SetNum(OutVertices.Num());
    for (int32 Index = 0; Index < OutVertices.Num(); ++Index)
    {
        const FSouthForkAeratedWaterOverlaySample Sample =
            ComputeSouthForkAeratedWaterOverlaySample(
                HydraulicPresentation[Index],
                ShorelineDepthsM[Index],
                OutUvs[Index].X * 3.0f,
                OutUvs[Index].Y * 3.0f);
        OutVertices[Index].Z += Sample.VerticalDisplacementCm;
        OutColors[Index] = Sample.Color;
    }

    const int32 CellWidth = OutWidth - 1;
    const int32 CellHeight = OutHeight - 1;
    const int32 CellCount = CellWidth * CellHeight;
    TArray<uint8> ActiveCells;
    ActiveCells.Init(0, CellCount);
    TArray<uint8> OverlayCells;
    OverlayCells.Init(0, CellCount);

    const auto CellIndex = [CellWidth](int32 Row, int32 Column)
    {
        return Row * CellWidth + Column;
    };
    const auto IsWetSupportedCell = [&HydraulicPresentation, &ShorelineDepthsM,
                                     OutWidth](int32 Row, int32 Column)
    {
        const int32 I0 = Row * OutWidth + Column;
        const int32 I1 = I0 + 1;
        const int32 I2 = I0 + OutWidth;
        const int32 I3 = I2 + 1;
        const int32 CellVertices[] = {I0, I1, I2, I3};
        for (const int32 VertexIndex : CellVertices)
        {
            if (HydraulicPresentation[VertexIndex].A < 0.90f ||
                ShorelineDepthsM[VertexIndex] <= 0.10f)
            {
                return false;
            }
        }
        return true;
    };

    // Admission is cell-based, never triangle-based. This preserves the
    // established solver-derived thresholds while preventing a single half of
    // a refined quad from exposing its diagonal as a bright tessellated shard.
    for (int32 Row = 0; Row < OutHeight - 1; ++Row)
    {
        for (int32 Column = 0; Column < OutWidth - 1; ++Column)
        {
            if (!IsWetSupportedCell(Row, Column))
            {
                continue;
            }
            const int32 I0 = Row * OutWidth + Column;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + OutWidth;
            const int32 I3 = I2 + 1;
            const int32 CellTriangles[] = {I0, I1, I2, I1, I3, I2};
            bool bCellIsActive = false;
            for (int32 Triangle = 0; Triangle < 6; Triangle += 3)
            {
                const int32 A = CellTriangles[Triangle];
                const int32 B = CellTriangles[Triangle + 1];
                const int32 C = CellTriangles[Triangle + 2];
                const float MaximumOpacity = FMath::Max3(
                    OutColors[A].A, OutColors[B].A, OutColors[C].A);
                const float MeanOpacity =
                    (OutColors[A].A + OutColors[B].A + OutColors[C].A) / 3.0f;
                if (MaximumOpacity >= 0.025f && MeanOpacity >= 0.006f)
                {
                    bCellIsActive = true;
                    break;
                }
            }
            if (bCellIsActive)
            {
                ActiveCells[CellIndex(Row, Column)] = 1;
            }
        }
    }

    // Retain two one-metre cells of wet, zero-alpha-capable support around the
    // active field. Vertex opacity and the project-owned foam lace can then
    // fade to nothing before geometry ends; padding cannot cross onto dry or
    // shoreline-clipped terrain and never creates foam in calm water.
    constexpr int32 TransparentPaddingCells = 2;
    for (int32 Row = 0; Row < CellHeight; ++Row)
    {
        for (int32 Column = 0; Column < CellWidth; ++Column)
        {
            if (ActiveCells[CellIndex(Row, Column)] == 0)
            {
                continue;
            }
            for (int32 RowOffset = -TransparentPaddingCells;
                 RowOffset <= TransparentPaddingCells;
                 ++RowOffset)
            {
                const int32 PaddedRow = Row + RowOffset;
                if (PaddedRow < 0 || PaddedRow >= CellHeight)
                {
                    continue;
                }
                for (int32 ColumnOffset = -TransparentPaddingCells;
                     ColumnOffset <= TransparentPaddingCells;
                     ++ColumnOffset)
                {
                    const int32 PaddedColumn = Column + ColumnOffset;
                    if (PaddedColumn < 0 || PaddedColumn >= CellWidth ||
                        !IsWetSupportedCell(PaddedRow, PaddedColumn))
                    {
                        continue;
                    }
                    OverlayCells[CellIndex(PaddedRow, PaddedColumn)] = 1;
                }
            }
        }
    }

    OutTriangles.Reset();
    OutTriangles.Reserve(CellCount * 6);
    for (int32 Row = 0; Row < CellHeight; ++Row)
    {
        for (int32 Column = 0; Column < CellWidth; ++Column)
        {
            if (OverlayCells[CellIndex(Row, Column)] == 0)
            {
                continue;
            }
            const int32 I0 = Row * OutWidth + Column;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + OutWidth;
            const int32 I3 = I2 + 1;
            OutTriangles.Append({I0, I1, I2, I1, I3, I2});
        }
    }
    return true;
}

UTexture2D* LoadSouthForkTerrainMacroTextureForReuse(
    const FString& TileId,
    FString& OutSummary)
{
    const FString AssetName = TEXT("T_RaftSim_") + TileId + TEXT("_MacroAlbedo");
    const FString ObjectPath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/MacroTextures/%s.%s"),
        *AssetName,
        *AssetName);
    UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *ObjectPath);
    if (!Texture)
    {
        OutSummary += FString::Printf(
            TEXT("Failed to reuse South Fork macro-albedo texture for %s.\n"),
            *TileId);
        return nullptr;
    }
    // Mesh-reuse captures are evidence passes over already-authored content.
    // Reimporting all 21 macros immediately before capture can temporarily
    // expose an empty running-platform mip chain and alternate two otherwise
    // identical output frames. Load the persisted asset, pin its existing
    // mips, and leave source reimport to the non-reuse authoring path.
    Texture->SetForceMipLevelsToBeResident(120.0f);
    Texture->WaitForStreaming();
    OutSummary += FString::Printf(
        TEXT("Reused persisted South Fork macro-albedo texture for %s.\n"),
        *TileId);
    return Texture;
}

UMaterialInstanceConstant* CreateSouthForkTerrainMaterialInstance(
    const FString& TileId,
    UMaterialInterface* Parent,
    UTexture2D* SourceMacroTexture,
    bool bUseCorridorEdgeBlend,
    FString& OutSummary)
{
    if (!Parent || !SourceMacroTexture)
    {
        return nullptr;
    }
    const FString AssetName = TEXT("MI_RaftSim_") + TileId + TEXT("_Terrain");
    const FString PackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/Materials/") +
        AssetName;
    const FString ObjectPath = PackagePath + TEXT(".") + AssetName;
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr, *ObjectPath);
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
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
    Instance->SetTextureParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceMacroTexture")), SourceMacroTexture);
    const bool bForceVertexMacro = bUseCorridorEdgeBlend && FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimUseSouthForkVertexMacro"));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseSourceMacroTexture")),
        bForceVertexMacro ? 0.0f : 1.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseCorridorEdgeBlend")),
        bUseCorridorEdgeBlend ? 1.0f : 0.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceMacroInfluence")),
        // Retain registered aerial geography without letting its low-frequency
        // pixels become a repeated close-range drape. The stronger scan layer
        // restores granular variation beneath grass and shrubs while the edge
        // blend still joins the detailed ribbon to its source-backed underlay.
        bUseCorridorEdgeBlend ? 0.44f : 0.92f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockAlbedoStrength")),
        // Suppress broad slope-facet color blocks; geometry and the scan normal
        // retain the bank's rock response at close range.
        bUseCorridorEdgeBlend ? 0.52f : 0.50f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainSpecular")),
        // The detailed riverbed sits directly below a transmitting water
        // interface. Its former dielectric highlight reflected the sky a
        // second time and appeared as a hard cyan polygon through shallow
        // water. Let the authored water own that interface reflection; retain
        // only a bounded response on exposed far-field terrain.
        bUseCorridorEdgeBlend ? 0.0f : 0.12f);
    // Raw NAIP windows span different acquisition dates and exposure levels.
    // Apply a bounded renderer-space tone per presentation tier so pale source
    // mosaics do not blow out under the production sun, while retaining their
    // registered hue and land-cover variation.
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceMacroTone")),
        bUseCorridorEdgeBlend
            ? FLinearColor(0.72f, 0.78f, 0.70f, 1.0f)
            : FLinearColor(0.62f, 0.68f, 0.60f, 1.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("FarFieldSourceMacroTone")),
        FLinearColor(0.62f, 0.68f, 0.60f, 1.0f));
    Instance->SetStaticSwitchParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseTerrainMicroAlbedo")), bUseCorridorEdgeBlend);
    Instance->SetStaticSwitchParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseTerrainMicroNormal")), bUseCorridorEdgeBlend);
    Instance->SetStaticSwitchParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseTerrainMicroRoughness")), bUseCorridorEdgeBlend);
    Instance->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    return UPackage::SavePackage(Package, Instance, *Filename, SaveArgs)
        ? Instance
        : nullptr;
}

float ComputeSouthForkFarFieldCorridorReliefWeight(
    const FRaftSimPreviewImage& CorridorExclusionMask,
    int32 Row,
    int32 Column)
{
    const int32 Width = CorridorExclusionMask.Width;
    const int32 Height = CorridorExclusionMask.Height;
    if (Width <= 0 || Height <= 0 ||
        CorridorExclusionMask.Pixels.Num() < Width * Height ||
        Row < 0 || Row >= Height || Column < 0 || Column >= Width)
    {
        return 0.0f;
    }

    // Far-field microrelief is intentionally non-gameplay geometry, but its
    // full +/-4.8 m amplitude can pierce the detailed corridor inside their
    // 12 m overlap. Fade only that inferred residual across three far-field
    // cells; authoritative DEM elevation and the overlap remain unchanged.
    for (int32 Radius = 0;
         Radius <= SouthForkFarFieldCorridorReliefTransitionCells;
         ++Radius)
    {
        for (int32 OffsetY = -Radius; OffsetY <= Radius; ++OffsetY)
        {
            for (int32 OffsetX = -Radius; OffsetX <= Radius; ++OffsetX)
            {
                if (FMath::Max(FMath::Abs(OffsetX), FMath::Abs(OffsetY)) != Radius)
                {
                    continue;
                }
                const int32 SampleRow = Row + OffsetY;
                const int32 SampleColumn = Column + OffsetX;
                if (SampleRow < 0 || SampleRow >= Height ||
                    SampleColumn < 0 || SampleColumn >= Width)
                {
                    continue;
                }
                if (CorridorExclusionMask.Pixels[
                        SampleRow * Width + SampleColumn].R <= 0.5f)
                {
                    return FMath::Clamp(
                        static_cast<float>(Radius - 1) /
                            static_cast<float>(
                                SouthForkFarFieldCorridorReliefTransitionCells),
                        0.0f, 1.0f);
                }
            }
        }
    }
    return 1.0f;
}

bool ConfigureSouthForkFarFieldTerrainActor(AStaticMeshActor* Actor)
{
    if (!Actor || !Actor->GetStaticMeshComponent())
    {
        return false;
    }
    // The source-window underlay intentionally overlaps the detailed ribbon.
    // Its dynamic shadow would project the hidden overlap edge as a black
    // diagonal across the sunlit bank, so only this non-colliding backdrop
    // relies on baked aerial tone and ambient occlusion instead.
    Actor->GetStaticMeshComponent()->SetCastShadow(false);
    return true;
}
} // namespace RaftSimEditorEnvironment
