#include "RaftSimRaftMesh.h"

#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"

namespace RaftSimRaftMesh
{
namespace
{
constexpr float kCmPerM = 100.0f;
// The production source mesh predates the self-bailing-floor waterline fix:
// its nominal top plane was authored at 15.5 cm while the parametric raft now
// places that plane at the side-tube centre. Keep the immutable source asset
// usable, but calibrate its floor to the runtime tube radius during deformation.
constexpr float kProductionAuthoredFloorPlaneZCm = 15.5f;

struct FPointDeformation
{
    FVector OffsetCm = FVector::ZeroVector;
    FVector OffsetGradientX = FVector::ZeroVector;
    FVector OffsetGradientY = FVector::ZeroVector;
    FVector ContactNormal = FVector::ZeroVector;
    FVector ContactCenterCm = FVector::ZeroVector;
    float CompressionRatio = 0.0f;
    float ContactWeight = 0.0f;
};

FPointDeformation EvaluatePointDeformation(
    const FVector& PointCm,
    float TubeCm,
    const TArray<FRaftSimFlexVisualSegmentState>* Deformation)
{
    FPointDeformation Result;
    if (Deformation == nullptr || Deformation->IsEmpty())
    {
        return Result;
    }

    // The D1-D4 layout is deliberately coarse. Blend every segment through a
    // compact Gaussian so the visible fabric bends continuously rather than
    // forming one hard dent per solver segment.
    const float SigmaCm = FMath::Max(TubeCm * 2.4f, 55.0f);
    const float InvSigmaSq = 1.0f / (SigmaCm * SigmaCm);
    const float InvTwoSigmaSq = 1.0f / (2.0f * SigmaCm * SigmaCm);
    float CompressionRatio = 0.0f;
    for (const FRaftSimFlexVisualSegmentState& Segment : *Deformation)
    {
        const FVector SegmentCm = Segment.LocalPositionM * kCmPerM;
        const FVector2D Delta(PointCm.X - SegmentCm.X, PointCm.Y - SegmentCm.Y);
        const float Weight = FMath::Exp(-Delta.SizeSquared() * InvTwoSigmaSq);
        if (Weight < 0.002f)
        {
            continue;
        }

        const FVector ContactNormal = Segment.ContactNormalLocal.GetSafeNormal();
        FVector SegmentOffsetCm = ContactNormal *
            static_cast<float>(Segment.IndentationM * kCmPerM);
        SegmentOffsetCm.Z -= static_cast<float>(Segment.FreeboardLossM * kCmPerM);
        if (Segment.bWrapping || Segment.bPinned)
        {
            // Multi-contact wraps lift the unsupported fabric while the
            // contacted wall follows the obstacle: the visible taco fold is
            // derived from the authoritative D4 state, not a visual trigger.
            SegmentOffsetCm.Z += static_cast<float>(
                Segment.IndentationM * kCmPerM * (Segment.bPinned ? 0.52 : 0.34));
        }
        Result.OffsetCm += SegmentOffsetCm * Weight;
        Result.OffsetGradientX += SegmentOffsetCm * (-Delta.X * Weight * InvSigmaSq);
        Result.OffsetGradientY += SegmentOffsetCm * (-Delta.Y * Weight * InvSigmaSq);
        Result.ContactNormal += ContactNormal * Weight;
        Result.ContactCenterCm += SegmentCm * Weight;
        Result.ContactWeight += Weight;

        const double RadialLossM = Segment.CompressionM + 0.35 * Segment.IndentationM;
        CompressionRatio = FMath::Max(
            CompressionRatio,
            static_cast<float>(RadialLossM * kCmPerM / FMath::Max(TubeCm, 1.0f)) * Weight);
    }
    Result.CompressionRatio = FMath::Clamp(CompressionRatio, 0.0f, 0.30f);
    Result.ContactNormal = Result.ContactNormal.GetSafeNormal();
    if (Result.ContactWeight > UE_SMALL_NUMBER)
    {
        Result.ContactCenterCm /= Result.ContactWeight;
    }
    return Result;
}

// Sweep a circular tube of radius TubeCm along a centreline (world cm). The
// cross-section lies in the plane spanned by the horizontal radial and world
// up, so the tube reads as a fat inflated tube lying flat. Normals point out
// from the axis. Appends into Out.
void SweepTube(
    const TArray<FVector>& Centerline, bool bClosed, float TubeCm, int32 RadialSegments,
    FMeshData& Out,
    const TArray<FRaftSimFlexVisualSegmentState>* Deformation = nullptr,
    const FRaftSimRaftVisualCondition* Condition = nullptr)
{
    const int32 N = Centerline.Num();
    if (N < 2)
    {
        return;
    }
    const int32 BaseVert = Out.Vertices.Num();
    const FVector Up(0.0f, 0.0f, 1.0f);

    for (int32 i = 0; i < N; ++i)
    {
        const FVector& RestP = Centerline[i];
        const FPointDeformation Shape = EvaluatePointDeformation(RestP, TubeCm, Deformation);
        const FVector P = RestP + Shape.OffsetCm;
        const FVector Prev = Centerline[(i - 1 + N) % N];
        const FVector Next = Centerline[(i + 1) % N];
        FVector Tangent;
        if (bClosed)
        {
            Tangent = (Next - Prev);
        }
        else
        {
            Tangent = (i == 0) ? (Next - P) : (i == N - 1 ? (P - Prev) : (Next - Prev));
        }
        Tangent = Tangent.GetSafeNormal();
        FVector Radial = FVector::CrossProduct(Up, Tangent).GetSafeNormal();
        if (Radial.IsNearlyZero())
        {
            Radial = FVector(1.0f, 0.0f, 0.0f);
        }
        const FVector RingUp = FVector::CrossProduct(Tangent, Radial).GetSafeNormal();

        for (int32 j = 0; j < RadialSegments; ++j)
        {
            const float A = 2.0f * PI * static_cast<float>(j) / static_cast<float>(RadialSegments);
            const FVector Dir = FMath::Cos(A) * Radial + FMath::Sin(A) * RingUp;
            FVector CrossSection = Dir;
            if (!Shape.ContactNormal.IsNearlyZero() && Shape.CompressionRatio > KINDA_SMALL_NUMBER)
            {
                FVector ContactAxis = Shape.ContactNormal -
                    Tangent * FVector::DotProduct(Shape.ContactNormal, Tangent);
                ContactAxis = ContactAxis.GetSafeNormal();
                if (!ContactAxis.IsNearlyZero())
                {
                    const FVector Perpendicular =
                        FVector::CrossProduct(Tangent, ContactAxis).GetSafeNormal();
                    const float CompressedScale = FMath::Clamp(
                        1.0f - 1.55f * Shape.CompressionRatio, 0.70f, 1.0f);
                    // Reciprocal axes conserve cross-sectional area: a local
                    // rock dent flattens and bulges an inflated tube instead
                    // of visually deleting air volume.
                    CrossSection =
                        ContactAxis * FVector::DotProduct(Dir, ContactAxis) * CompressedScale +
                        Perpendicular * FVector::DotProduct(Dir, Perpendicular) / CompressedScale;
                }
            }
            const float PressureScale = Condition
                ? FMath::Lerp(0.82f, 1.0f, FMath::Clamp(Condition->PressureFraction, 0.0f, 1.0f))
                : 1.0f;
            FVector Vertex = P + TubeCm * PressureScale * CrossSection;
            if (Condition && Condition->CreaseAmplitudeM > 0.0f)
            {
                const float WrinkleCm = Condition->CreaseAmplitudeM * kCmPerM *
                    FMath::Sin(0.071f * RestP.X + 0.113f * RestP.Y + 2.0f * A);
                Vertex += Dir * WrinkleCm * (1.0f - Condition->Integrity);
            }
            Out.Vertices.Add(Vertex);
            Out.Normals.Add(CrossSection.GetSafeNormal());
            Out.UVs.Add(FVector2D(
                static_cast<float>(i) / static_cast<float>(N),
                static_cast<float>(j) / static_cast<float>(RadialSegments)));
            Out.Tangents.Add(FProcMeshTangent(Tangent, false));
        }
    }

    const int32 Rings = N;
    const int32 LastRing = bClosed ? Rings : Rings - 1;
    for (int32 i = 0; i < LastRing; ++i)
    {
        const int32 i0 = i;
        const int32 i1 = (i + 1) % Rings;
        for (int32 j = 0; j < RadialSegments; ++j)
        {
            const int32 j1 = (j + 1) % RadialSegments;
            const int32 A = BaseVert + i0 * RadialSegments + j;
            const int32 B = BaseVert + i1 * RadialSegments + j;
            const int32 C = BaseVert + i0 * RadialSegments + j1;
            const int32 D = BaseVert + i1 * RadialSegments + j1;
            Out.Triangles.Add(A); Out.Triangles.Add(B); Out.Triangles.Add(C);
            Out.Triangles.Add(C); Out.Triangles.Add(B); Out.Triangles.Add(D);
        }
    }
}

// Rounded-rectangle centreline in the XY plane (cm), CCW, with an upturned
// bow/stern kick in z. Half-extents Ax/Ay are the centreline reach; the tube
// surface extends TubeCm beyond that.
TArray<FVector> RoundedRectLoop(
    float AxCm, float AyCm, float CornerCm, float TubeCm, float KickCm, float LengthCm)
{
    TArray<FVector2D> Path;
    const float Rc = FMath::Min(CornerCm, FMath::Min(AxCm, AyCm) * 0.95f);
    const float Sx = AxCm - Rc; // straight half-length in x
    const float Sy = AyCm - Rc; // straight half-length in y
    const float Spacing = 9.0f; // ~9 cm between samples

    auto AddStraight = [&](const FVector2D& From, const FVector2D& To)
    {
        const float Len = (To - From).Size();
        const int32 Steps = FMath::Max(1, FMath::RoundToInt(Len / Spacing));
        for (int32 s = 0; s < Steps; ++s)
        {
            Path.Add(From + (To - From) * (static_cast<float>(s) / static_cast<float>(Steps)));
        }
    };
    auto AddArc = [&](const FVector2D& Center, float StartDeg, float EndDeg)
    {
        const float ArcLen = FMath::DegreesToRadians(FMath::Abs(EndDeg - StartDeg)) * Rc;
        const int32 Steps = FMath::Max(2, FMath::RoundToInt(ArcLen / Spacing));
        for (int32 s = 0; s < Steps; ++s)
        {
            const float T = static_cast<float>(s) / static_cast<float>(Steps);
            const float Ang = FMath::DegreesToRadians(FMath::Lerp(StartDeg, EndDeg, T));
            Path.Add(Center + Rc * FVector2D(FMath::Cos(Ang), FMath::Sin(Ang)));
        }
    };

    // CCW from the +X (bow) right side.
    AddStraight(FVector2D(AxCm, -Sy), FVector2D(AxCm, Sy));
    AddArc(FVector2D(Sx, Sy), 0.0f, 90.0f);
    AddStraight(FVector2D(Sx, AyCm), FVector2D(-Sx, AyCm));
    AddArc(FVector2D(-Sx, Sy), 90.0f, 180.0f);
    AddStraight(FVector2D(-AxCm, Sy), FVector2D(-AxCm, -Sy));
    AddArc(FVector2D(-Sx, -Sy), 180.0f, 270.0f);
    AddStraight(FVector2D(-Sx, -AyCm), FVector2D(Sx, -AyCm));
    AddArc(FVector2D(Sx, -Sy), 270.0f, 360.0f);

    TArray<FVector> Loop;
    Loop.Reserve(Path.Num());
    const float HalfLen = LengthCm * 0.5f;
    for (const FVector2D& P : Path)
    {
        // Upturned ends: rise as |x| approaches the bow/stern.
        const float T = FMath::Clamp((FMath::Abs(P.X) / HalfLen - 0.55f) / 0.45f, 0.0f, 1.0f);
        const float Z = TubeCm + KickCm * T * T;
        Loop.Add(FVector(P.X, P.Y, Z));
    }
    return Loop;
}

void AppendOvalTube(
    const FVector& CenterCm,
    const FVector& AxisACm,
    const FVector& AxisBCm,
    float TubeCm,
    int32 PathSegments,
    int32 RadialSegments,
    FMeshData& Out,
    const TArray<FRaftSimFlexVisualSegmentState>* Deformation)
{
    TArray<FVector> Centerline;
    Centerline.Reserve(PathSegments);
    for (int32 Index = 0; Index < PathSegments; ++Index)
    {
        const float Angle = 2.0f * PI * static_cast<float>(Index) /
            static_cast<float>(PathSegments);
        Centerline.Add(
            CenterCm + AxisACm * FMath::Cos(Angle) + AxisBCm * FMath::Sin(Angle));
    }
    SweepTube(
        Centerline,
        /*bClosed=*/true,
        TubeCm,
        RadialSegments,
        Out,
        Deformation);
}

void AppendValve(
    const FVector& RestCenterCm,
    float RadiusCm,
    float HeightCm,
    float MainTubeCm,
    int32 Sides,
    FMeshData& Out,
    const TArray<FRaftSimFlexVisualSegmentState>* Deformation)
{
    const FPointDeformation Shape =
        EvaluatePointDeformation(RestCenterCm, MainTubeCm, Deformation);
    const FVector CenterCm = RestCenterCm + Shape.OffsetCm;
    const int32 BaseVertex = Out.Vertices.Num();
    for (int32 Ring = 0; Ring < 2; ++Ring)
    {
        const float Z = (Ring == 0 ? -0.5f : 0.5f) * HeightCm;
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const float Angle = 2.0f * PI * static_cast<float>(Side) /
                static_cast<float>(Sides);
            const FVector Radial(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            Out.Vertices.Add(CenterCm + Radial * RadiusCm + FVector(0.0f, 0.0f, Z));
            Out.Normals.Add(Radial);
            Out.UVs.Add(FVector2D(
                static_cast<float>(Side) / static_cast<float>(Sides),
                static_cast<float>(Ring)));
            Out.Tangents.Add(FProcMeshTangent(-FMath::Sin(Angle), FMath::Cos(Angle), 0.0f));
        }
    }
    for (int32 Side = 0; Side < Sides; ++Side)
    {
        const int32 Next = (Side + 1) % Sides;
        const int32 A = BaseVertex + Side;
        const int32 B = BaseVertex + Next;
        const int32 C = BaseVertex + Sides + Side;
        const int32 D = BaseVertex + Sides + Next;
        Out.Triangles.Append({A, C, B, B, C, D});
    }

    const int32 BottomCenter = Out.Vertices.Num();
    Out.Vertices.Add(CenterCm - FVector(0.0f, 0.0f, HeightCm * 0.5f));
    Out.Normals.Add(-FVector::UpVector);
    Out.UVs.Add(FVector2D(0.5f, 0.5f));
    Out.Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 TopCenter = Out.Vertices.Num();
    Out.Vertices.Add(CenterCm + FVector(0.0f, 0.0f, HeightCm * 0.5f));
    Out.Normals.Add(FVector::UpVector);
    Out.UVs.Add(FVector2D(0.5f, 0.5f));
    Out.Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    for (int32 Side = 0; Side < Sides; ++Side)
    {
        const int32 Next = (Side + 1) % Sides;
        Out.Triangles.Append({BottomCenter, BaseVertex + Next, BaseVertex + Side});
        Out.Triangles.Append({TopCenter, BaseVertex + Sides + Side, BaseVertex + Sides + Next});
    }
}

void AppendOrientedTriangle(int32 A, int32 B, int32 C, FMeshData& Out)
{
    const FVector FaceNormal = FVector::CrossProduct(
        Out.Vertices[B] - Out.Vertices[A],
        Out.Vertices[C] - Out.Vertices[A]);
    const FVector DesiredNormal =
        (Out.Normals[A] + Out.Normals[B] + Out.Normals[C]).GetSafeNormal();
    if (FVector::DotProduct(FaceNormal, DesiredNormal) >= 0.0f)
    {
        Out.Triangles.Append({A, B, C});
    }
    else
    {
        Out.Triangles.Append({A, C, B});
    }
}

void AppendSideTubePatch(
    float CenterXCm,
    float CenterAngleRadians,
    float HalfLengthCm,
    float HalfAngleRadians,
    float SideTubeCenterYCm,
    float SideTubeCenterZCm,
    float MainTubeCm,
    float Side,
    int32 Sides,
    FMeshData& Out,
    const TArray<FRaftSimFlexVisualSegmentState>* Deformation)
{
    constexpr int32 RadialRings = 3;
    constexpr float StandOffCm = 0.55f;
    const int32 ClampedSides = FMath::Max(Sides, 12);
    const int32 CenterIndex = Out.Vertices.Num();

    auto AppendVertex = [&](float X, float TubeAngle, const FVector2D& UV)
    {
        const FVector RestNormal(
            0.0f,
            Side * FMath::Cos(TubeAngle),
            FMath::Sin(TubeAngle));
        const FVector RestVertex(
            X,
            Side * (SideTubeCenterYCm + MainTubeCm * FMath::Cos(TubeAngle)),
            SideTubeCenterZCm + MainTubeCm * FMath::Sin(TubeAngle));
        const FVector TubeCenterlineSample(
            X,
            Side * SideTubeCenterYCm,
            SideTubeCenterZCm);
        const FPointDeformation Shape =
            EvaluatePointDeformation(TubeCenterlineSample, MainTubeCm, Deformation);
        Out.Vertices.Add(RestVertex + RestNormal * StandOffCm + Shape.OffsetCm);
        Out.Normals.Add(RestNormal);
        Out.UVs.Add(UV);
        Out.Tangents.Add(FProcMeshTangent(FVector::ForwardVector, false));
    };

    AppendVertex(CenterXCm, CenterAngleRadians, FVector2D(0.5f, 0.5f));
    for (int32 RingIndex = 1; RingIndex <= RadialRings; ++RingIndex)
    {
        const float RingScale = static_cast<float>(RingIndex) /
            static_cast<float>(RadialRings);
        for (int32 SideIndex = 0; SideIndex < ClampedSides; ++SideIndex)
        {
            const float PatchAngle = 2.0f * PI * static_cast<float>(SideIndex) /
                static_cast<float>(ClampedSides);
            const float X = CenterXCm +
                HalfLengthCm * RingScale * FMath::Cos(PatchAngle);
            const float TubeAngle = CenterAngleRadians +
                HalfAngleRadians * RingScale * FMath::Sin(PatchAngle);
            AppendVertex(
                X,
                TubeAngle,
                FVector2D(
                    0.5f + 0.5f * RingScale * FMath::Cos(PatchAngle),
                    0.5f + 0.5f * RingScale * FMath::Sin(PatchAngle)));
        }
    }

    for (int32 SideIndex = 0; SideIndex < ClampedSides; ++SideIndex)
    {
        const int32 Current = CenterIndex + 1 + SideIndex;
        const int32 Next = CenterIndex + 1 + (SideIndex + 1) % ClampedSides;
        AppendOrientedTriangle(CenterIndex, Current, Next, Out);
    }
    for (int32 RingIndex = 1; RingIndex < RadialRings; ++RingIndex)
    {
        const int32 InnerBase = CenterIndex + 1 + (RingIndex - 1) * ClampedSides;
        const int32 OuterBase = CenterIndex + 1 + RingIndex * ClampedSides;
        for (int32 SideIndex = 0; SideIndex < ClampedSides; ++SideIndex)
        {
            const int32 NextSide = (SideIndex + 1) % ClampedSides;
            const int32 A = InnerBase + SideIndex;
            const int32 B = InnerBase + NextSide;
            const int32 C = OuterBase + SideIndex;
            const int32 D = OuterBase + NextSide;
            AppendOrientedTriangle(A, C, B, Out);
            AppendOrientedTriangle(B, C, D, Out);
        }
    }
}

void AppendSideChafeStrip(
    float HalfLengthCm,
    float SideTubeCenterYCm,
    float SideTubeCenterZCm,
    float MainTubeCm,
    float Side,
    FMeshData& Out,
    const TArray<FRaftSimFlexVisualSegmentState>* Deformation)
{
    // A real paddle raft carries replaceable wear fabric around the lower
    // outside tube where repeated rock contact would otherwise abrade the PVC.
    // Build it directly on the tube circumference so it follows D4 dents and
    // remains visibly bonded instead of floating over a wrapped tube.
    constexpr int32 LongitudinalSegments = 24;
    constexpr int32 CircumferentialSegments = 6;
    constexpr float LowerAngleDeg = -55.0f;
    constexpr float UpperAngleDeg = -15.0f;
    const int32 BaseVertex = Out.Vertices.Num();
    for (int32 LongIndex = 0; LongIndex <= LongitudinalSegments; ++LongIndex)
    {
        const float Along = static_cast<float>(LongIndex) /
            static_cast<float>(LongitudinalSegments);
        const float X = FMath::Lerp(-HalfLengthCm, HalfLengthCm, Along);
        for (int32 CircumferenceIndex = 0;
             CircumferenceIndex <= CircumferentialSegments;
             ++CircumferenceIndex)
        {
            const float Across = static_cast<float>(CircumferenceIndex) /
                static_cast<float>(CircumferentialSegments);
            const float Angle = FMath::DegreesToRadians(
                FMath::Lerp(LowerAngleDeg, UpperAngleDeg, Across));
            const FVector RestNormal(
                0.0f, Side * FMath::Cos(Angle), FMath::Sin(Angle));
            // The 0.45 cm stand-off prevents coplanar flicker while remaining
            // below the thickness of a commercial bonded chafe layer.
            const FVector RestVertex(
                X,
                Side * (SideTubeCenterYCm + MainTubeCm * FMath::Cos(Angle)),
                SideTubeCenterZCm + MainTubeCm * FMath::Sin(Angle));
            const FVector TubeCenterlineSample(
                X,
                Side * SideTubeCenterYCm,
                SideTubeCenterZCm);
            const FPointDeformation Shape =
                EvaluatePointDeformation(TubeCenterlineSample, MainTubeCm, Deformation);
            Out.Vertices.Add(RestVertex + RestNormal * 0.45f + Shape.OffsetCm);
            Out.Normals.Add(RestNormal);
            Out.UVs.Add(FVector2D(Along * 5.0f, Across));
            Out.Tangents.Add(FProcMeshTangent(FVector::ForwardVector, false));
        }
    }

    for (int32 LongIndex = 0; LongIndex < LongitudinalSegments; ++LongIndex)
    {
        for (int32 CircumferenceIndex = 0;
             CircumferenceIndex < CircumferentialSegments;
             ++CircumferenceIndex)
        {
            const int32 RowWidth = CircumferentialSegments + 1;
            const int32 A = BaseVertex + LongIndex * RowWidth + CircumferenceIndex;
            const int32 B = A + 1;
            const int32 C = A + RowWidth;
            const int32 D = C + 1;
            AppendOrientedTriangle(A, C, B, Out);
            AppendOrientedTriangle(B, C, D, Out);
        }
    }
}
} // namespace

bool ExtractProductionRaftRestMesh(
    const UStaticMesh* StaticMesh,
    TArray<FMeshData>& OutSections)
{
    constexpr int32 ExpectedMaterialSections = 5;
    OutSections.Reset();
    if (StaticMesh == nullptr || !StaticMesh->bAllowCPUAccess)
    {
        return false;
    }

    const FStaticMeshRenderData* RenderData = StaticMesh->GetRenderData();
    if (RenderData == nullptr || RenderData->LODResources.IsEmpty())
    {
        return false;
    }
    const FStaticMeshLODResources& Lod = RenderData->LODResources[0];
    if (Lod.Sections.Num() != ExpectedMaterialSections ||
        Lod.VertexBuffers.PositionVertexBuffer.GetNumVertices() == 0 ||
        Lod.VertexBuffers.StaticMeshVertexBuffer.GetNumVertices() == 0 ||
        Lod.IndexBuffer.GetNumIndices() == 0)
    {
        return false;
    }

    OutSections.SetNum(ExpectedMaterialSections);
    for (const FStaticMeshSection& SourceSection : Lod.Sections)
    {
        const int32 MaterialIndex = static_cast<int32>(SourceSection.MaterialIndex);
        if (!OutSections.IsValidIndex(MaterialIndex) || SourceSection.NumTriangles == 0)
        {
            OutSections.Reset();
            return false;
        }

        FMeshData& Section = OutSections[MaterialIndex];
        TMap<uint32, int32> SourceToLocalVertex;
        SourceToLocalVertex.Reserve(SourceSection.NumTriangles * 2);
        Section.Triangles.Reserve(SourceSection.NumTriangles * 3);
        for (uint32 Wedge = SourceSection.FirstIndex;
             Wedge < SourceSection.FirstIndex + SourceSection.NumTriangles * 3;
             ++Wedge)
        {
            const uint32 SourceVertex = Lod.IndexBuffer.GetIndex(Wedge);
            int32* Existing = SourceToLocalVertex.Find(SourceVertex);
            if (Existing != nullptr)
            {
                Section.Triangles.Add(*Existing);
                continue;
            }

            const int32 LocalVertex = Section.Vertices.Num();
            SourceToLocalVertex.Add(SourceVertex, LocalVertex);
            Section.Triangles.Add(LocalVertex);
            Section.Vertices.Add(static_cast<FVector>(
                Lod.VertexBuffers.PositionVertexBuffer.VertexPosition(SourceVertex)));
            Section.Normals.Add(static_cast<FVector>(
                Lod.VertexBuffers.StaticMeshVertexBuffer.VertexTangentZ(SourceVertex)));
            Section.UVs.Add(static_cast<FVector2D>(
                Lod.VertexBuffers.StaticMeshVertexBuffer.GetVertexUV(SourceVertex, 0)));
            Section.Tangents.Add(FProcMeshTangent(
                static_cast<FVector>(
                    Lod.VertexBuffers.StaticMeshVertexBuffer.VertexTangentX(SourceVertex)),
                false));
        }
        if (Section.Vertices.IsEmpty() ||
            Section.Vertices.Num() != Section.Normals.Num() ||
            Section.Vertices.Num() != Section.UVs.Num() ||
            Section.Vertices.Num() != Section.Tangents.Num())
        {
            OutSections.Reset();
            return false;
        }
    }
    return true;
}

bool ProductionDeformationCacheMatches(
    const FProductionRaftDeformationCache& Cache,
    const TArray<FMeshData>& RestSections,
    float TubeRadiusM,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation)
{
    if (!FMath::IsNearlyEqual(Cache.TubeRadiusM, TubeRadiusM, 1.0e-6f) ||
        Cache.SegmentPositionsCm.Num() != Deformation.Num() ||
        Cache.Sections.Num() != RestSections.Num())
    {
        return false;
    }
    for (int32 SegmentIndex = 0; SegmentIndex < Deformation.Num(); ++SegmentIndex)
    {
        if (!Cache.SegmentPositionsCm[SegmentIndex].Equals(
                Deformation[SegmentIndex].LocalPositionM * kCmPerM, 1.0e-4f))
        {
            return false;
        }
    }
    for (int32 SectionIndex = 0; SectionIndex < RestSections.Num(); ++SectionIndex)
    {
        if (Cache.Sections[SectionIndex].Starts.Num() !=
            RestSections[SectionIndex].Vertices.Num() + 1)
        {
            return false;
        }
    }
    return true;
}

void BuildProductionDeformationCache(
    const TArray<FMeshData>& RestSections,
    float TubeRadiusM,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation,
    FProductionRaftDeformationCache& Cache)
{
    Cache.Reset();
    Cache.TubeRadiusM = TubeRadiusM;
    Cache.SegmentPositionsCm.Reserve(Deformation.Num());
    for (const FRaftSimFlexVisualSegmentState& Segment : Deformation)
    {
        Cache.SegmentPositionsCm.Add(Segment.LocalPositionM * kCmPerM);
    }
    Cache.Sections.SetNum(RestSections.Num());

    const float TubeCm = FMath::Max(TubeRadiusM * kCmPerM, 1.0f);
    const float SigmaCm = FMath::Max(TubeCm * 2.4f, 55.0f);
    const float InvSigmaSq = 1.0f / (SigmaCm * SigmaCm);
    const float InvTwoSigmaSq = 0.5f * InvSigmaSq;
    for (int32 SectionIndex = 0; SectionIndex < RestSections.Num(); ++SectionIndex)
    {
        const FMeshData& Rest = RestSections[SectionIndex];
        FProductionRaftDeformationSectionCache& Section = Cache.Sections[SectionIndex];
        Section.Starts.Reserve(Rest.Vertices.Num() + 1);
        Section.Influences.Reserve(Rest.Vertices.Num() * 6);
        for (const FVector& RestVertex : Rest.Vertices)
        {
            Section.Starts.Add(Section.Influences.Num());
            for (int32 SegmentIndex = 0; SegmentIndex < Cache.SegmentPositionsCm.Num();
                 ++SegmentIndex)
            {
                const FVector& SegmentCm = Cache.SegmentPositionsCm[SegmentIndex];
                const FVector2D Delta(RestVertex.X - SegmentCm.X, RestVertex.Y - SegmentCm.Y);
                const float Weight = FMath::Exp(-Delta.SizeSquared() * InvTwoSigmaSq);
                if (Weight < 0.002f)
                {
                    continue;
                }
                FProductionRaftDeformationInfluence& Influence =
                    Section.Influences.AddDefaulted_GetRef();
                Influence.SegmentIndex = SegmentIndex;
                Influence.Weight = Weight;
                Influence.GradientXFactor = -Delta.X * Weight * InvSigmaSq;
                Influence.GradientYFactor = -Delta.Y * Weight * InvSigmaSq;
            }
        }
        Section.Starts.Add(Section.Influences.Num());
    }
}

FPointDeformation EvaluateCachedPointDeformation(
    const FProductionRaftDeformationCache& Cache,
    const FProductionRaftDeformationSectionCache& Section,
    int32 VertexIndex,
    float TubeCm,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation)
{
    FPointDeformation Result;
    if (!Section.Starts.IsValidIndex(VertexIndex + 1))
    {
        return Result;
    }
    float CompressionRatio = 0.0f;
    for (int32 InfluenceIndex = Section.Starts[VertexIndex];
         InfluenceIndex < Section.Starts[VertexIndex + 1]; ++InfluenceIndex)
    {
        const FProductionRaftDeformationInfluence& Influence =
            Section.Influences[InfluenceIndex];
        if (!Deformation.IsValidIndex(Influence.SegmentIndex))
        {
            continue;
        }
        const FRaftSimFlexVisualSegmentState& Segment =
            Deformation[Influence.SegmentIndex];
        const FVector ContactNormal = Segment.ContactNormalLocal.GetSafeNormal();
        FVector SegmentOffsetCm = ContactNormal *
            static_cast<float>(Segment.IndentationM * kCmPerM);
        SegmentOffsetCm.Z -= static_cast<float>(Segment.FreeboardLossM * kCmPerM);
        if (Segment.bWrapping || Segment.bPinned)
        {
            SegmentOffsetCm.Z += static_cast<float>(
                Segment.IndentationM * kCmPerM * (Segment.bPinned ? 0.52 : 0.34));
        }
        Result.OffsetCm += SegmentOffsetCm * Influence.Weight;
        Result.OffsetGradientX += SegmentOffsetCm * Influence.GradientXFactor;
        Result.OffsetGradientY += SegmentOffsetCm * Influence.GradientYFactor;
        Result.ContactNormal += ContactNormal * Influence.Weight;
        Result.ContactCenterCm +=
            Cache.SegmentPositionsCm[Influence.SegmentIndex] * Influence.Weight;
        Result.ContactWeight += Influence.Weight;

        const double RadialLossM = Segment.CompressionM + 0.35 * Segment.IndentationM;
        CompressionRatio = FMath::Max(
            CompressionRatio,
            static_cast<float>(RadialLossM * kCmPerM / FMath::Max(TubeCm, 1.0f)) *
                Influence.Weight);
    }
    Result.CompressionRatio = FMath::Clamp(CompressionRatio, 0.0f, 0.30f);
    Result.ContactNormal = Result.ContactNormal.GetSafeNormal();
    if (Result.ContactWeight > UE_SMALL_NUMBER)
    {
        Result.ContactCenterCm /= Result.ContactWeight;
    }
    return Result;
}

void DeformProductionRaftRestMesh(
    const TArray<FMeshData>& RestSections,
    float TubeRadiusM,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation,
    const FRaftSimRaftVisualCondition& Condition,
    TArray<FMeshData>& OutSections,
    FProductionRaftDeformationCache* ReusableCache)
{
    bool bOutputBuffersMatch = OutSections.Num() == RestSections.Num();
    for (int32 SectionIndex = 0;
         bOutputBuffersMatch && SectionIndex < RestSections.Num(); ++SectionIndex)
    {
        const FMeshData& Output = OutSections[SectionIndex];
        const FMeshData& Rest = RestSections[SectionIndex];
        bOutputBuffersMatch =
            Output.Vertices.Num() == Rest.Vertices.Num() &&
            Output.Triangles.Num() == Rest.Triangles.Num() &&
            Output.Normals.Num() == Rest.Normals.Num() &&
            Output.UVs.Num() == Rest.UVs.Num() &&
            Output.Tangents.Num() == Rest.Tangents.Num();
    }
    // The default one-shot API retains its value semantics. Runtime callers
    // opt into persistent buffers explicitly and keep immutable topology/UVs.
    if (ReusableCache == nullptr || !bOutputBuffersMatch)
    {
        OutSections = RestSections;
    }
    if (ReusableCache != nullptr &&
        !ProductionDeformationCacheMatches(
            *ReusableCache, RestSections, TubeRadiusM, Deformation))
    {
        BuildProductionDeformationCache(
            RestSections, TubeRadiusM, Deformation, *ReusableCache);
    }
    const float TubeCm = FMath::Max(TubeRadiusM * kCmPerM, 1.0f);
    const float ProductionFloorLiftCm =
        TubeCm - kProductionAuthoredFloorPlaneZCm;
    const float PressureScale = FMath::Lerp(
        0.82f,
        1.0f,
        FMath::Clamp(Condition.PressureFraction, 0.0f, 1.0f));

    for (int32 SectionIndex = 0; SectionIndex < OutSections.Num(); ++SectionIndex)
    {
        FMeshData& Deformed = OutSections[SectionIndex];
        const FMeshData& Rest = RestSections[SectionIndex];
        for (int32 VertexIndex = 0; VertexIndex < Deformed.Vertices.Num(); ++VertexIndex)
        {
            const FVector& RestVertex = Rest.Vertices[VertexIndex];
            const FVector RestNormal = Rest.Normals.IsValidIndex(VertexIndex)
                ? Rest.Normals[VertexIndex].GetSafeNormal()
                : FVector::UpVector;
            const FPointDeformation Shape = ReusableCache != nullptr
                ? EvaluateCachedPointDeformation(
                      *ReusableCache,
                      ReusableCache->Sections[SectionIndex],
                      VertexIndex,
                      TubeCm,
                      Deformation)
                : EvaluatePointDeformation(RestVertex, TubeCm, &Deformation);
            // Match the procedural fallback: the laced floor follows 55% of
            // tube displacement instead of inheriting the full accumulated
            // perimeter sag. The old production path applied 100%, which
            // depressed an already-low floor further under the seated crew.
            const float DeformationScale = SectionIndex == 1 ? 0.55f : 1.0f;
            FVector Vertex = RestVertex + Shape.OffsetCm * DeformationScale;
            if (SectionIndex == 1)
            {
                // Bring the production self-bailer onto the same tube-centre
                // plane as BuildInflatableRaft. This changes presentation only;
                // the six-point tube support and loaded mass remain authoritative.
                Vertex.Z += ProductionFloorLiftCm;
            }

            // The imported rest topology previously translated through the D4
            // field but ignored D4's actual radial compression. Apply the same
            // area-preserving squash/bulge used by the parametric fallback to
            // the chamber section only. This is presentation derived from D4;
            // collision, forces, pressure state and topology remain untouched.
            FVector ContactAxis = FVector::ZeroVector;
            FVector BulgeAxis = FVector::ZeroVector;
            float CompressedScale = 1.0f;
            if (SectionIndex == 0 &&
                Shape.ContactWeight > UE_SMALL_NUMBER &&
                Shape.CompressionRatio > KINDA_SMALL_NUMBER)
            {
                ContactAxis = Shape.ContactNormal.GetSafeNormal();
                BulgeAxis = (
                    FVector::UpVector -
                    ContactAxis * FVector::DotProduct(FVector::UpVector, ContactAxis))
                    .GetSafeNormal();
                if (BulgeAxis.IsNearlyZero())
                {
                    BulgeAxis = FVector::ForwardVector;
                }
                // The authored chamber is substantially denser than the
                // parametric fallback, so a shallow 10% squash was lost in
                // its rounded silhouette and wet highlight. Keep the exact
                // D4 contact field as authority, but project its calibrated
                // compression through a bounded 25% radial loss. Reciprocal
                // bulging retains the inflated-volume read during a wrap.
                CompressedScale = FMath::Clamp(
                    1.0f - 0.95f * Shape.CompressionRatio, 0.75f, 1.0f);
                const FVector RelativeToContact = RestVertex - Shape.ContactCenterCm;
                Vertex += ContactAxis *
                    FVector::DotProduct(RelativeToContact, ContactAxis) *
                    (CompressedScale - 1.0f);
                Vertex += BulgeAxis *
                    FVector::DotProduct(RelativeToContact, BulgeAxis) *
                    (1.0f / CompressedScale - 1.0f);
            }

            // Section zero contains the main chambers and thwarts. Contracting
            // along the authored surface normal preserves their silhouette far
            // better than shrinking the entire raft toward its origin.
            if (SectionIndex == 0)
            {
                Vertex += RestNormal * TubeCm * (PressureScale - 1.0f);
            }
            else if (SectionIndex == 1)
            {
                // The inflated floor loses less thickness than the chambers.
                Vertex += RestNormal * 8.0f * (PressureScale - 1.0f);
            }

            if (Condition.CreaseAmplitudeM > 0.0f)
            {
                const float Phase =
                    0.071f * RestVertex.X + 0.113f * RestVertex.Y +
                    0.037f * RestVertex.Z;
                Vertex += RestNormal * Condition.CreaseAmplitudeM * kCmPerM *
                    FMath::Sin(Phase) * (1.0f - Condition.Integrity);
            }
            Deformed.Vertices[VertexIndex] = Vertex;

            // Preserve the imported smooth tangent frame through both the
            // chamber squash and the spatial gradient of the D4 offset. Leaving
            // rest normals on moving geometry produced a rigid broad highlight
            // that hid the actual wrap. Transforming two tangent directions and
            // rebuilding N is bounded O(vertices * active D4 segments) and adds
            // no per-frame topology walk.
            if (Rest.Tangents.IsValidIndex(VertexIndex) &&
                Deformed.Normals.IsValidIndex(VertexIndex) &&
                Deformed.Tangents.IsValidIndex(VertexIndex))
            {
                const FVector RestTangent =
                    Rest.Tangents[VertexIndex].TangentX.GetSafeNormal();
                const FVector RestBitangent = FVector::CrossProduct(
                    RestNormal, RestTangent).GetSafeNormal();
                auto TransformDirection = [&](const FVector& Direction)
                {
                    FVector Transformed = Direction;
                    if (CompressedScale < 1.0f)
                    {
                        Transformed += ContactAxis *
                            FVector::DotProduct(Direction, ContactAxis) *
                            (CompressedScale - 1.0f);
                        Transformed += BulgeAxis *
                            FVector::DotProduct(Direction, BulgeAxis) *
                            (1.0f / CompressedScale - 1.0f);
                    }
                    constexpr float LightingGradientScale = 0.52f;
                    return Transformed + LightingGradientScale * DeformationScale * (
                        Shape.OffsetGradientX * Transformed.X +
                        Shape.OffsetGradientY * Transformed.Y);
                };
                FVector BentTangent = TransformDirection(RestTangent).GetSafeNormal();
                FVector BentBitangent = TransformDirection(RestBitangent).GetSafeNormal();
                FVector BentNormal = FVector::CrossProduct(
                    BentTangent, BentBitangent).GetSafeNormal();
                if (FVector::DotProduct(BentNormal, RestNormal) < 0.0f)
                {
                    BentNormal *= -1.0f;
                }
                BentTangent = (
                    BentTangent - BentNormal * FVector::DotProduct(BentTangent, BentNormal))
                    .GetSafeNormal();
                Deformed.Normals[VertexIndex] = BentNormal;
                Deformed.Tangents[VertexIndex] = FProcMeshTangent(
                    BentTangent,
                    Rest.Tangents[VertexIndex].bFlipTangentY);
            }
        }
    }
}

void BuildInflatableRaft(
    float LengthM, float WidthM, float TubeRadiusM,
    FMeshData& OutTubes, FMeshData& OutFloor,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation,
    const FRaftSimRaftVisualCondition& Condition,
    FMeshData* OutRigging,
    FMeshData* OutMetalFittings,
    FMeshData* OutRubberDetails)
{
    const float L = LengthM * kCmPerM;
    const float W = WidthM * kCmPerM;
    const float Tr = TubeRadiusM * kCmPerM;
    const float Ax = L * 0.5f - Tr;
    const float Ay = W * 0.5f - Tr;
    const float Corner = FMath::Min(Ay, Tr * 2.4f);
    const float Kick = Tr * 1.15f;

    // Outer tube loop.
    const TArray<FVector> Loop = RoundedRectLoop(Ax, Ay, Corner, Tr, Kick, L);
    SweepTube(
        Loop, /*bClosed=*/true, Tr, /*RadialSegments=*/18, OutTubes,
        &Deformation, &Condition);

    if (OutRigging)
    {
        // Commercial paddle rafts carry a perimeter grab line just outside
        // the main tube crown. It follows the same D4 deformation field, so a
        // wrap or pin bends the rigging with the fabric instead of leaving a
        // rigid cosmetic hoop behind.
        constexpr float RiggingRadiusCm = 1.45f;
        TArray<FVector> RiggingLoop = RoundedRectLoop(
            Ax + Tr * 0.88f,
            Ay + Tr * 0.88f,
            Corner + Tr * 0.55f,
            RiggingRadiusCm,
            Kick * 0.88f,
            L);
        for (FVector& Point : RiggingLoop)
        {
            Point.Z += Tr * 1.50f;
        }
        SweepTube(
            RiggingLoop, /*bClosed=*/true, RiggingRadiusCm,
            /*RadialSegments=*/8, *OutRigging, &Deformation);
    }

    // Two cross thwarts (seats), slightly thinner, tucked between the side tubes.
    const float ThwartR = Tr * 0.72f;
    const float ThwartInset = Ay - Tr * 0.3f;
    const float ThwartZ = Tr * 0.95f;
    for (const float ThwartX : {L * 0.14f, -L * 0.16f})
    {
        TArray<FVector> Bar;
        const int32 Steps = 10;
        for (int32 s = 0; s <= Steps; ++s)
        {
            const float Y = FMath::Lerp(-ThwartInset, ThwartInset, static_cast<float>(s) / Steps);
            Bar.Add(FVector(ThwartX, Y, ThwartZ));
        }
        // Thwarts share the same D1/D4 field, coupling them to lateral and taco
        // folds rather than leaving rigid bars through a deforming raft.
        SweepTube(
            Bar, /*bClosed=*/false, ThwartR, /*RadialSegments=*/10, OutTubes,
            &Deformation, &Condition);
    }

    if (OutMetalFittings)
    {
        // Four load-rated D-rings sit on the outer side tubes where a real
        // paddle raft carries bow/stern rigging and recovery attachments.
        // The rings are deliberately modest at gameplay scale but keep enough
        // radial topology for a metallic highlight instead of reading as cards.
        const float RingY = Ay + Tr * 1.02f;
        const float RingZ = Tr * 1.42f;
        for (const float Side : {-1.0f, 1.0f})
        {
            for (const float RingX : {-L * 0.23f, L * 0.23f})
            {
                AppendOvalTube(
                    FVector(RingX, Side * RingY, RingZ),
                    FVector(7.5f, 0.0f, 0.0f),
                    FVector(0.0f, 0.0f, 5.5f),
                    /*TubeCm=*/0.78f,
                    /*PathSegments=*/16,
                    /*RadialSegments=*/6,
                    *OutMetalFittings,
                    &Deformation);
            }
        }
    }

    if (OutRubberDetails)
    {
        // Bonded lower-side chafe strips break up the broad tube surface and
        // identify the craft as a river-working boat rather than a pristine
        // pool inflatable. Both strips are evaluated point-by-point through D4.
        for (const float Side : {-1.0f, 1.0f})
        {
            AppendSideChafeStrip(
                L * 0.34f, Ay, Tr, Tr, Side, *OutRubberDetails, &Deformation);
        }

        // Transverse chamber weld/protection bands make the continuous sweep
        // read as a multi-chamber commercial inflatable. They are generated in
        // rest space and follow the exact contact field used by the main tube.
        const float BandRadius = Tr + 0.32f;
        for (const float Side : {-1.0f, 1.0f})
        {
            for (const float BandX : {-L * 0.24f, L * 0.24f})
            {
                AppendOvalTube(
                    FVector(BandX, Side * Ay, Tr),
                    FVector(0.0f, BandRadius, 0.0f),
                    FVector(0.0f, 0.0f, BandRadius),
                    /*TubeCm=*/0.48f,
                    /*PathSegments=*/14,
                    /*RadialSegments=*/5,
                    *OutRubberDetails,
                    &Deformation);
            }
        }

        // One low-profile inflation valve per side chamber, placed on the
        // protected inside crown. The capped cylinders follow local D4 offset.
        for (const float Side : {-1.0f, 1.0f})
        {
            for (const float ValveX : {-L * 0.27f, L * 0.27f})
            {
                AppendValve(
                    FVector(ValveX, Side * (Ay - Tr * 0.42f), Tr * 2.02f),
                    /*RadiusCm=*/3.4f,
                    /*HeightCm=*/2.8f,
                    Tr,
                    /*Sides=*/10,
                    *OutRubberDetails,
                    &Deformation);
            }
        }

        // Load-bearing fittings and grab-line keepers need broad bonded pads;
        // bare metal rings and rope emerging directly from tube fabric are a
        // strong miniature/model tell in close-range views.
        for (const float Side : {-1.0f, 1.0f})
        {
            for (const float RingX : {-L * 0.23f, L * 0.23f})
            {
                AppendSideTubePatch(
                    RingX,
                    /*CenterAngleRadians=*/0.40f,
                    /*HalfLengthCm=*/13.5f,
                    /*HalfAngleRadians=*/0.30f,
                    Ay,
                    Tr,
                    Tr,
                    Side,
                    /*Sides=*/20,
                    *OutRubberDetails,
                    &Deformation);
            }
            for (const float KeeperX : {-L * 0.39f, -L * 0.08f, L * 0.08f, L * 0.39f})
            {
                AppendSideTubePatch(
                    KeeperX,
                    /*CenterAngleRadians=*/0.34f,
                    /*HalfLengthCm=*/7.5f,
                    /*HalfAngleRadians=*/0.17f,
                    Ay,
                    Tr,
                    Tr,
                    Side,
                    /*Sides=*/16,
                    *OutRubberDetails,
                    &Deformation);
            }
        }

        // Each thwart terminates in a reinforced collar on the inside tube;
        // these pads remain soft and share the same deformation field as the
        // thwart and side chamber.
        for (const float Side : {-1.0f, 1.0f})
        {
            for (const float ThwartX : {L * 0.14f, -L * 0.16f})
            {
                AppendSideTubePatch(
                    ThwartX,
                    /*CenterAngleRadians=*/PI,
                    /*HalfLengthCm=*/12.0f,
                    /*HalfAngleRadians=*/0.44f,
                    Ay,
                    Tr,
                    Tr,
                    Side,
                    /*Sides=*/18,
                    *OutRubberDetails,
                    &Deformation);
            }
        }

        // Bow and stern carry handles arch above their attachment points. They
        // remain soft geometry so a pin does not leave rigid hardware floating.
        for (const float End : {-1.0f, 1.0f})
        {
            TArray<FVector> Handle;
            constexpr int32 HandleSteps = 6;
            for (int32 Step = 0; Step <= HandleSteps; ++Step)
            {
                const float T = static_cast<float>(Step) / HandleSteps;
                const float Y = FMath::Lerp(-15.0f, 15.0f, T);
                const float Lift = 7.0f * FMath::Sin(PI * T);
                Handle.Add(FVector(
                    End * (Ax + Tr * 0.86f),
                    Y,
                    Tr * 1.48f + Lift));
            }
            SweepTube(
                Handle,
                /*bClosed=*/false,
                /*TubeCm=*/1.15f,
                /*RadialSegments=*/6,
                *OutRubberDetails,
                &Deformation);

        }
    }

    // Inset self-bailing floor: a slightly dished grid spanning inside the tubes.
    const float FloorAx = Ax - Tr * 0.2f;
    const float FloorAy = Ay - Tr * 0.2f;
    // The previous 0.42 R plane sat 16 cm below the seats on a 56 cm tube and
    // remained visibly underwater even at correct hydrostatic equilibrium.
    // An inflated self-bailing floor rides at the side-tube centre plane.
    const float FloorZ = Tr;
    const int32 Nx = 16;
    const int32 Ny = 8;
    const int32 FloorBase = OutFloor.Vertices.Num();
    for (int32 iy = 0; iy <= Ny; ++iy)
    {
        for (int32 ix = 0; ix <= Nx; ++ix)
        {
            const float fx = static_cast<float>(ix) / Nx;
            const float fy = static_cast<float>(iy) / Ny;
            const float X = FMath::Lerp(-FloorAx, FloorAx, fx);
            const float Y = FMath::Lerp(-FloorAy, FloorAy, fy);
            // Dish: lowest in the centre.
            const float Dish = -Tr * 0.18f * (1.0f - FMath::Square(2.0f * fx - 1.0f)) *
                               (1.0f - FMath::Square(2.0f * fy - 1.0f));
            // Five low longitudinal I-beam crowns give the self-bailing floor
            // real inflated structure and controlled specular breakup.
            const float IBeamRelief = Tr * 0.095f *
                FMath::Square(FMath::Cos(4.0f * PI * fy));
            const FVector RestVertex(X, Y, FloorZ + Dish + IBeamRelief);
            FPointDeformation FloorShape = EvaluatePointDeformation(RestVertex, Tr, &Deformation);
            // The laced floor follows tube motion, but less than the contacted
            // tube wall so the raft visibly folds without shearing the deck.
            FloorShape.OffsetCm *= 0.55f;
            FVector FloorVertex = RestVertex + FloorShape.OffsetCm;
            if (Condition.CreaseAmplitudeM > 0.0f)
            {
                FloorVertex.Z += Condition.CreaseAmplitudeM * kCmPerM *
                    (1.0f - Condition.Integrity) * FMath::Sin(6.0f * fx + 4.0f * fy);
            }
            OutFloor.Vertices.Add(FloorVertex);
            OutFloor.Normals.Add(FVector::UpVector);
            OutFloor.UVs.Add(FVector2D(fx * 4.0f, fy * 2.0f));
            OutFloor.Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
        }
    }
    for (int32 iy = 0; iy < Ny; ++iy)
    {
        for (int32 ix = 0; ix < Nx; ++ix)
        {
            const int32 A = FloorBase + iy * (Nx + 1) + ix;
            const int32 B = A + 1;
            const int32 C = A + (Nx + 1);
            const int32 D = C + 1;
            OutFloor.Triangles.Add(A); OutFloor.Triangles.Add(C); OutFloor.Triangles.Add(B);
            OutFloor.Triangles.Add(B); OutFloor.Triangles.Add(C); OutFloor.Triangles.Add(D);
        }
    }

    // The dished and ribbed floor is no longer planar. Accumulated face
    // normals retain its inflated relief under lighting instead of falsely
    // presenting every vertex as a flat horizontal sheet.
    for (int32 VertexIndex = FloorBase; VertexIndex < OutFloor.Vertices.Num(); ++VertexIndex)
    {
        OutFloor.Normals[VertexIndex] = FVector::ZeroVector;
    }
    const int32 FloorTriangleIndex = OutFloor.Triangles.Num() - Nx * Ny * 6;
    for (int32 TriangleIndex = FloorTriangleIndex;
         TriangleIndex < OutFloor.Triangles.Num();
         TriangleIndex += 3)
    {
        const int32 A = OutFloor.Triangles[TriangleIndex];
        const int32 B = OutFloor.Triangles[TriangleIndex + 1];
        const int32 C = OutFloor.Triangles[TriangleIndex + 2];
        const FVector FaceNormal = FVector::CrossProduct(
            OutFloor.Vertices[C] - OutFloor.Vertices[A],
            OutFloor.Vertices[B] - OutFloor.Vertices[A]);
        OutFloor.Normals[A] += FaceNormal;
        OutFloor.Normals[B] += FaceNormal;
        OutFloor.Normals[C] += FaceNormal;
    }
    for (int32 VertexIndex = FloorBase; VertexIndex < OutFloor.Vertices.Num(); ++VertexIndex)
    {
        OutFloor.Normals[VertexIndex] = OutFloor.Normals[VertexIndex].GetSafeNormal();
    }
}

} // namespace RaftSimRaftMesh
