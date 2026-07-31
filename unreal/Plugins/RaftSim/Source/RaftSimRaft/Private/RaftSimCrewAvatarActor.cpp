#include "RaftSimCrewAvatarActor.h"

#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimMannyCrewVisualActor.h"
#include "RaftSimMetaHumanCrewVisualActor.h"

#include "Components/ChildActorComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "ProceduralMeshComponent.h"

namespace
{
constexpr float kBaseRadiusCm = 50.0f;
const FVector kProductionHelmetSkullCenterOffsetCm(0.0f, 0.0f, 12.0f);
const FVector kProductionHelmetShellOffsetCm(2.5f, 0.0f, 0.0f);
const FVector kProductionHelmetRetentionOffsetCm(0.0f, 0.0f, 3.0f);

void BuildUnitOrganicMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // Smooth enough for a close guide-camera silhouette while remaining small
    // enough to rebuild deterministically for every project-owned body part.
    constexpr int32 Rings = 10;
    constexpr int32 Sides = 14;
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        const float Phi = PI * V;
        const float Z = FMath::Cos(Phi);
        // Slightly relax the perfect sphere so limbs read as soft tissue.
        const float R = FMath::Pow(FMath::Max(FMath::Sin(Phi), 0.0f), 0.92f);
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            const FVector Normal(R * FMath::Cos(Theta), R * FMath::Sin(Theta), Z);
            Vertices.Add(Normal * kBaseRadiusCm);
            Normals.Add(Normal.GetSafeNormal());
            UVs.Add(FVector2D(U, V));
            Tangents.Add(FProcMeshTangent(-FMath::Sin(Theta), FMath::Cos(Theta), 0.0f));
        }
    }
    for (int32 Ring = 0; Ring < Rings; ++Ring)
    {
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 A = Ring * (Sides + 1) + Side;
            const int32 B = A + 1;
            const int32 C = A + Sides + 1;
            const int32 D = C + 1;
            Triangles.Append({A, C, B, B, C, D});
        }
    }
}

void BuildUnitHeadMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // The animated body stays deliberately economical, but the face occupies
    // enough guide-camera pixels to justify a denser, anatomically conditioned
    // surface. This remains a deterministic project-owned parametric mesh.
    constexpr int32 Rings = 20;
    constexpr int32 Sides = 28;
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        const float Phi = PI * V;
        const float SphereZ = FMath::Cos(Phi);
        const float Radius = FMath::Sin(Phi);
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            FVector Point(
                Radius * FMath::Cos(Theta),
                Radius * FMath::Sin(Theta),
                SphereZ);

            const float Front = static_cast<float>(
                FMath::SmoothStep(0.18, 0.92, Point.X));
            const float LowerFace = static_cast<float>(
                FMath::SmoothStep(0.08, 0.88, -Point.Z));
            const float ChinCenter = FMath::Pow(
                FMath::Clamp(1.0f - FMath::Abs(Point.Y) * 1.9f, 0.0f, 1.0f),
                2.0f);
            const float CheekBand = FMath::Exp(
                -FMath::Square((Point.Z - 0.02f) * 3.2f));
            const float CheekSide = FMath::Exp(
                -FMath::Square((FMath::Abs(Point.Y) - 0.42f) * 4.0f));

            // Narrow the jaw and temples, establish cheekbones, flatten the
            // facial plane, and project a modest chin. The attached nose,
            // eyelids, ears, and lips then sit on a recognizably human base
            // instead of an unconditioned sphere.
            Point.Y *= FMath::Lerp(1.0f, 0.76f, LowerFace);
            Point.Y *= FMath::Lerp(1.0f, 0.91f, FMath::Max(Point.Z - 0.42f, 0.0f));
            Point.X = FMath::Lerp(Point.X, 0.93f + Point.X * 0.07f, Front * 0.52f);
            Point.X += Front * CheekBand * CheekSide * 0.045f;
            Point.X += Front * LowerFace * ChinCenter * 0.055f;
            Point.Z *= FMath::Lerp(1.0f, 1.04f, FMath::Max(Point.Z, 0.0f));

            const FVector ApproximateNormal = Point.GetSafeNormal();
            Vertices.Add(Point * kBaseRadiusCm);
            Normals.Add(ApproximateNormal);
            UVs.Add(FVector2D(U, V));
            FVector Tangent(-FMath::Sin(Theta), FMath::Cos(Theta), 0.0f);
            Tangent = (Tangent - ApproximateNormal *
                FVector::DotProduct(Tangent, ApproximateNormal)).GetSafeNormal();
            Tangents.Add(FProcMeshTangent(Tangent, false));
        }
    }
    for (int32 Ring = 0; Ring < Rings; ++Ring)
    {
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 A = Ring * (Sides + 1) + Side;
            const int32 B = A + 1;
            const int32 C = A + Sides + 1;
            const int32 D = C + 1;
            Triangles.Append({A, C, B, B, C, D});
        }
    }
}

void BuildUnitSafetyPanelMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // A rounded superellipsoid gives flotation foam a sewn-panel silhouette
    // instead of reusing the soft-tissue sphere used by anatomy and limbs.
    // The PFD is frequently close to the guide camera. A coarse 8x12 shell
    // exposed individual facets and unstable self-shadow penumbrae on the
    // high-visibility fabric. This remains inexpensive for five occupants but
    // gives the sewn foam a continuous production silhouette.
    constexpr int32 Rings = 20;
    constexpr int32 Sides = 32;
    constexpr float ShapeExponent = 0.54f;
    constexpr float GradientExponent = 2.0f / ShapeExponent - 1.0f;
    const auto SignedPower = [](float Value, float Exponent)
    {
        return FMath::Sign(Value) * FMath::Pow(FMath::Abs(Value), Exponent);
    };
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        const float Phi = PI * V;
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            const FVector SpherePoint(
                FMath::Sin(Phi) * FMath::Cos(Theta),
                FMath::Sin(Phi) * FMath::Sin(Theta),
                FMath::Cos(Phi));
            const FVector Point(
                SignedPower(SpherePoint.X, ShapeExponent),
                SignedPower(SpherePoint.Y, ShapeExponent),
                SignedPower(SpherePoint.Z, ShapeExponent));
            const FVector Gradient(
                SignedPower(Point.X, GradientExponent),
                SignedPower(Point.Y, GradientExponent),
                SignedPower(Point.Z, GradientExponent));
            Vertices.Add(Point * kBaseRadiusCm);
            Normals.Add(Gradient.GetSafeNormal());
            UVs.Add(FVector2D(U, V));
            Tangents.Add(FProcMeshTangent(-FMath::Sin(Theta), FMath::Cos(Theta), 0.0f));
        }
    }
    for (int32 Ring = 0; Ring < Rings; ++Ring)
    {
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 A = Ring * (Sides + 1) + Side;
            const int32 B = A + 1;
            const int32 C = A + Sides + 1;
            const int32 D = C + 1;
            Triangles.Append({A, C, B, B, C, D});
        }
    }
}

void BuildUnitHelmetShellMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // An open river helmet is a top/back shell, not a closed ellipsoid. The
    // polar extent is shortest above the face and longest at the rear, leaving
    // the eyes and brows unobstructed while preserving temple/occipital cover.
    constexpr int32 Rings = 10;
    constexpr int32 Sides = 24;
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            const float FacingFront = FMath::Max(FMath::Cos(Theta), 0.0f);
            // Extend the rear and temples just below the skull equator. The
            // front remains shorter to expose the eyes, but still reaches the
            // brow instead of leaving a detached crown cap.
            const float MaxPhi = FMath::Lerp(1.66f, 1.43f, FacingFront);
            const float Phi = MaxPhi * V;
            const FVector Normal(
                FMath::Sin(Phi) * FMath::Cos(Theta),
                FMath::Sin(Phi) * FMath::Sin(Theta),
                FMath::Cos(Phi));
            Vertices.Add(Normal * kBaseRadiusCm);
            Normals.Add(Normal.GetSafeNormal());
            UVs.Add(FVector2D(U, V));
            Tangents.Add(FProcMeshTangent(
                -FMath::Sin(Theta), FMath::Cos(Theta), 0.0f));
        }
    }
    for (int32 Ring = 0; Ring < Rings; ++Ring)
    {
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 A = Ring * (Sides + 1) + Side;
            const int32 B = A + 1;
            const int32 C = A + Sides + 1;
            const int32 D = C + 1;
            Triangles.Append({A, C, B, B, C, D});
        }
    }
}

void AppendMeshInstance(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    const TArray<FProcMeshTangent>& SourceTangents,
    const FVector& CenterCm,
    const FQuat& Rotation,
    const FVector& RadiusCm,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    const int32 VertexOffset = Vertices.Num();
    const FVector Scale = RadiusCm / kBaseRadiusCm;
    for (int32 Index = 0; Index < SourceVertices.Num(); ++Index)
    {
        Vertices.Add(CenterCm + Rotation.RotateVector(SourceVertices[Index] * Scale));
        const FVector NormalScale(
            SourceNormals[Index].X / Scale.X,
            SourceNormals[Index].Y / Scale.Y,
            SourceNormals[Index].Z / Scale.Z);
        const FVector Normal = Rotation.RotateVector(NormalScale).GetSafeNormal();
        Normals.Add(Normal);
        UVs.Add(SourceUVs[Index]);
        FVector Tangent = Rotation.RotateVector(SourceTangents[Index].TangentX * Scale);
        Tangent = (Tangent - Normal * FVector::DotProduct(Tangent, Normal)).GetSafeNormal();
        Tangents.Add(FProcMeshTangent(Tangent, SourceTangents[Index].bFlipTangentY));
    }
    for (const int32 TriangleIndex : SourceTriangles)
    {
        Triangles.Add(VertexOffset + TriangleIndex);
    }
}

void AppendTaperedSafetyPanelInstance(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    const TArray<FProcMeshTangent>& SourceTangents,
    const FVector& CenterCm,
    const FQuat& Rotation,
    const FVector& RadiusCm,
    float SideSign,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // Commercial rescue-PFD cells taper into the shoulder and hem instead of
    // reading as two identical vertical cushions. Warp the reusable sewn-foam
    // panel before instancing it so the vest keeps a continuous fitted
    // silhouette without adding a draw call per cell.
    TArray<FVector> TaperedVertices;
    TArray<FVector> TaperedNormals;
    TaperedVertices.Reserve(SourceVertices.Num());
    TaperedNormals.Reserve(SourceNormals.Num());
    for (int32 Index = 0; Index < SourceVertices.Num(); ++Index)
    {
        FVector Point = SourceVertices[Index] / kBaseRadiusCm;
        const float Shoulder = FMath::SmoothStep(
            0.30f, 0.96f, static_cast<float>(Point.Z));
        const float Hem = FMath::SmoothStep(
            0.62f, 0.98f, static_cast<float>(-Point.Z));
        const float WidthScale = 1.0f - Shoulder * 0.30f - Hem * 0.12f;
        Point.Y = Point.Y * WidthScale + SideSign * Shoulder * 0.08f;
        Point.X *= 1.0f - Shoulder * 0.17f;
        TaperedVertices.Add(Point * kBaseRadiusCm);

        FVector Normal = SourceNormals[Index];
        Normal.Y /= FMath::Max(WidthScale, 0.2f);
        Normal.X /= FMath::Max(1.0f - Shoulder * 0.17f, 0.2f);
        TaperedNormals.Add(Normal.GetSafeNormal());
    }
    AppendMeshInstance(
        TaperedVertices,
        SourceTriangles,
        TaperedNormals,
        SourceUVs,
        SourceTangents,
        CenterCm,
        Rotation,
        RadiusCm,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Tangents);
}

void AppendColoredMeshInstance(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    const TArray<FProcMeshTangent>& SourceTangents,
    const FVector& CenterCm,
    const FQuat& Rotation,
    const FVector& RadiusCm,
    const FLinearColor& Color,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents,
    TArray<FLinearColor>& Colors)
{
    const int32 FirstVertex = Vertices.Num();
    AppendMeshInstance(
        SourceVertices,
        SourceTriangles,
        SourceNormals,
        SourceUVs,
        SourceTangents,
        CenterCm,
        Rotation,
        RadiusCm,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Tangents);
    Colors.Reserve(Vertices.Num());
    for (int32 Index = FirstVertex; Index < Vertices.Num(); ++Index)
    {
        Colors.Add(Color);
    }
}

void AppendRoundedLimbInstance(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    const TArray<FProcMeshTangent>& SourceTangents,
    const FVector& StartCm,
    const FVector& EndCm,
    float RadiusCm,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    const FVector Delta = EndCm - StartCm;
    const FVector Direction = Delta.GetSafeNormal(SMALL_NUMBER, FVector::UpVector);
    AppendMeshInstance(
        SourceVertices,
        SourceTriangles,
        SourceNormals,
        SourceUVs,
        SourceTangents,
        (StartCm + EndCm) * 0.5f,
        FRotationMatrix::MakeFromZ(Direction).ToQuat(),
        FVector(RadiusCm, RadiusCm, FMath::Max(Delta.Size() * 0.5f, RadiusCm)),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Tangents);
}

void AppendColoredRoundedLimbInstance(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    const TArray<FProcMeshTangent>& SourceTangents,
    const FVector& StartCm,
    const FVector& EndCm,
    float RadiusCm,
    const FLinearColor& Color,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents,
    TArray<FLinearColor>& Colors)
{
    const FVector Delta = EndCm - StartCm;
    const FVector Direction = Delta.GetSafeNormal(SMALL_NUMBER, FVector::UpVector);
    AppendColoredMeshInstance(
        SourceVertices,
        SourceTriangles,
        SourceNormals,
        SourceUVs,
        SourceTangents,
        (StartCm + EndCm) * 0.5f,
        FRotationMatrix::MakeFromZ(Direction).ToQuat(),
        FVector(RadiusCm, RadiusCm, FMath::Max(Delta.Size() * 0.5f, RadiusCm)),
        Color,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Tangents,
        Colors);
}

void ReplaceMeshSection(
    UProceduralMeshComponent* Component,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const TArray<FProcMeshTangent>& Tangents)
{
    if (!Component)
    {
        return;
    }
    Component->ClearAllMeshSections();
    TArray<FLinearColor> Colors;
    Component->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false);
}

void ReplaceColoredMeshSection(
    UProceduralMeshComponent* Component,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const TArray<FProcMeshTangent>& Tangents,
    const TArray<FLinearColor>& Colors)
{
    if (!Component || Colors.Num() != Vertices.Num())
    {
        return;
    }
    Component->ClearAllMeshSections();
    Component->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false);
}

void BuildCommercialPaddleBladeMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // A compact, convex whitewater-paddle profile in centimetres. The local
    // +Z axis follows the shaft toward the blade tip, while Y supplies a thin
    // beveled extrusion that still reads edge-on from the guide camera.
    static const FVector2D Outline[] = {
        FVector2D(-3.0f, -5.0f),
        FVector2D(-6.0f, 3.0f),
        FVector2D(-9.0f, 19.0f),
        FVector2D(-8.5f, 30.0f),
        FVector2D(-5.0f, 36.0f),
        FVector2D(0.0f, 39.0f),
        FVector2D(5.0f, 36.0f),
        FVector2D(8.5f, 30.0f),
        FVector2D(9.0f, 19.0f),
        FVector2D(6.0f, 3.0f),
        FVector2D(3.0f, -5.0f)};
    constexpr int32 OutlineCount = static_cast<int32>(UE_ARRAY_COUNT(Outline));
    constexpr float HalfThicknessCm = 1.2f;
    constexpr float CenterZCm = 17.0f;

    Vertices.Reset();
    Triangles.Reset();
    Normals.Reset();
    UVs.Reset();
    Tangents.Reset();

    const auto AddVertex = [&](const FVector& Position, const FVector& Normal, const FVector2D& UV)
    {
        Vertices.Add(Position);
        Normals.Add(Normal);
        UVs.Add(UV);
        Tangents.Add(FProcMeshTangent(FVector::ForwardVector, false));
    };

    const int32 FrontCenter = Vertices.Num();
    AddVertex(FVector(0.0f, HalfThicknessCm, CenterZCm), FVector::RightVector, FVector2D(0.5f, 0.5f));
    const int32 FrontStart = Vertices.Num();
    for (const FVector2D& Point : Outline)
    {
        AddVertex(
            FVector(Point.X, HalfThicknessCm, Point.Y),
            FVector::RightVector,
            FVector2D(Point.X / 20.0f + 0.5f, (Point.Y + 5.0f) / 44.0f));
    }
    for (int32 Index = 0; Index < OutlineCount; ++Index)
    {
        Triangles.Append({FrontCenter, FrontStart + Index, FrontStart + (Index + 1) % OutlineCount});
    }

    const int32 BackCenter = Vertices.Num();
    AddVertex(FVector(0.0f, -HalfThicknessCm, CenterZCm), -FVector::RightVector, FVector2D(0.5f, 0.5f));
    const int32 BackStart = Vertices.Num();
    for (const FVector2D& Point : Outline)
    {
        AddVertex(
            FVector(Point.X, -HalfThicknessCm, Point.Y),
            -FVector::RightVector,
            FVector2D(Point.X / 20.0f + 0.5f, (Point.Y + 5.0f) / 44.0f));
    }
    for (int32 Index = 0; Index < OutlineCount; ++Index)
    {
        Triangles.Append({BackCenter, BackStart + (Index + 1) % OutlineCount, BackStart + Index});
    }

    for (int32 Index = 0; Index < OutlineCount; ++Index)
    {
        const FVector2D& A = Outline[Index];
        const FVector2D& B = Outline[(Index + 1) % OutlineCount];
        const FVector Edge(B.X - A.X, 0.0f, B.Y - A.Y);
        const FVector SideNormal(-Edge.Z, 0.0f, Edge.X);
        const FVector SafeSideNormal = SideNormal.GetSafeNormal();
        const int32 SideStart = Vertices.Num();
        AddVertex(FVector(A.X, HalfThicknessCm, A.Y), SafeSideNormal, FVector2D(0.0f, 0.0f));
        AddVertex(FVector(A.X, -HalfThicknessCm, A.Y), SafeSideNormal, FVector2D(0.0f, 1.0f));
        AddVertex(FVector(B.X, -HalfThicknessCm, B.Y), SafeSideNormal, FVector2D(1.0f, 1.0f));
        AddVertex(FVector(B.X, HalfThicknessCm, B.Y), SafeSideNormal, FVector2D(1.0f, 0.0f));
        Triangles.Append(
            {SideStart, SideStart + 1, SideStart + 2,
             SideStart, SideStart + 2, SideStart + 3});
    }
}

float SmoothUnitInterval(float Alpha)
{
    const float Bounded = FMath::Clamp(Alpha, 0.0f, 1.0f);
    return Bounded * Bounded * (3.0f - 2.0f * Bounded);
}

float WrapNormalizedPhase(float Phase)
{
    return FMath::Frac(1.0f + FMath::Frac(Phase));
}

float StrokeWave(float Phase)
{
    // A guided paddle stroke spends more time driving a planted blade than
    // recovering it through the air. Keep the solve continuous at the cycle
    // seam, but replace the old perfectly symmetric sine with explicit catch,
    // power and recovery timing.
    constexpr float PowerEndPhase = 0.58f;
    const float Wrapped = WrapNormalizedPhase(Phase);
    if (Wrapped <= PowerEndPhase)
    {
        return FMath::Lerp(
            1.0f,
            -1.0f,
            SmoothUnitInterval(Wrapped / PowerEndPhase));
    }
    return FMath::Lerp(
        -1.0f,
        1.0f,
        SmoothUnitInterval((Wrapped - PowerEndPhase) / (1.0f - PowerEndPhase)));
}

float StrokeRecoveryLiftCm(float Phase)
{
    constexpr float PowerEndPhase = 0.58f;
    const float Wrapped = WrapNormalizedPhase(Phase);
    if (Wrapped <= PowerEndPhase)
    {
        return 0.0f;
    }
    const float RecoveryAlpha =
        (Wrapped - PowerEndPhase) / (1.0f - PowerEndPhase);
    return 26.0f * FMath::Sin(PI * RecoveryAlpha);
}

bool UsesWaistPivotedUpperBodyArticulation(ERaftSimCrewAvatarAction Action)
{
    // Falling, swimming, and re-entry use fully authored world-space body
    // landmarks. Their large rotations describe the whole body rather than a
    // seated waist articulation and must not be applied a second time.
    return Action != ERaftSimCrewAvatarAction::Falling &&
        Action != ERaftSimCrewAvatarAction::Swimming &&
        Action != ERaftSimCrewAvatarAction::Reentry;
}

void ApplyWaistPivotedUpperBodyArticulation(FRaftSimCrewAvatarPose& Pose)
{
    if (Pose.TorsoRotation.IsNearlyZero())
    {
        return;
    }
    const FQuat Rotation = Pose.TorsoRotation.Quaternion();
    const FVector Pivot = Pose.TorsoCenterCm;
    const auto RotateAroundPivot = [&Rotation, &Pivot](FVector& PointCm)
    {
        PointCm = Pivot + Rotation.RotateVector(PointCm - Pivot);
    };

    // The torso/PFD centre is the waist-pivot anchor. Rotate the shoulders
    // and head around it while leaving solved hand, paddle, hip, knee, and
    // foot targets authoritative. Arms then bend toward the grip and the
    // lower body remains planted against the raft instead of translating as
    // one rigid mannequin.
    RotateAroundPivot(Pose.LeftShoulderCm);
    RotateAroundPivot(Pose.RightShoulderCm);
    RotateAroundPivot(Pose.HeadCenterCm);
}
}

FRaftSimCrewAvatarPose URaftSimCrewAvatarPoseLibrary::EvaluatePose(
    ERaftSimCrewAvatarAction Action,
    float NormalizedPhase,
    int32 SeatSide)
{
    const float Side = SeatSide < 0 ? -1.0f : 1.0f;
    const float Wave = StrokeWave(NormalizedPhase);
    FRaftSimCrewAvatarPose Pose;
    Pose.TorsoCenterCm = FVector(2.0f, 0.0f, 59.0f);
    Pose.HeadCenterCm = FVector(6.0f, 0.0f, 91.0f);
    Pose.LeftShoulderCm = FVector(4.0f, -17.0f, 76.0f);
    Pose.RightShoulderCm = FVector(4.0f, 17.0f, 76.0f);
    Pose.LeftHandCm = FVector(28.0f, -25.0f, 55.0f);
    Pose.RightHandCm = FVector(42.0f, 12.0f, 42.0f);
    Pose.LeftHipCm = FVector(-4.0f, -10.0f, 40.0f);
    Pose.RightHipCm = FVector(-4.0f, 10.0f, 40.0f);
    Pose.LeftKneeCm = FVector(22.0f, -14.0f, 21.0f);
    Pose.RightKneeCm = FVector(22.0f, 14.0f, 21.0f);
    Pose.LeftFootCm = FVector(45.0f, -17.0f, 8.0f);
    Pose.RightFootCm = FVector(45.0f, 17.0f, 8.0f);
    Pose.PaddleTopCm = FVector(25.0f, 25.0f * Side, 67.0f);
    Pose.PaddleBottomCm = FVector(65.0f, -42.0f * Side, -7.0f);

    switch (Action)
    {
        case ERaftSimCrewAvatarAction::ForwardStroke:
        {
            const float Reach = 14.0f * Wave;
            const float PowerAlpha = 0.5f * (1.0f - Wave);
            Pose.TorsoRotation.Pitch = -8.0f - 7.0f * Wave;
            Pose.TorsoRotation.Yaw = Side * (4.0f + 3.0f * Wave);
            Pose.TorsoRotation.Roll = -Side * (2.0f + 1.5f * PowerAlpha);
            Pose.TorsoCenterCm.X += 5.0f * Wave;
            Pose.PaddleTopCm.X += Reach;
            Pose.PaddleBottomCm.X -= 20.0f * Wave;
            Pose.PaddleBottomCm.Z += StrokeRecoveryLiftCm(NormalizedPhase);
            Pose.LeftHandCm = Pose.PaddleTopCm;
            Pose.RightHandCm = FMath::Lerp(
                Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.43f);
            break;
        }
        case ERaftSimCrewAvatarAction::BackStroke:
        {
            // Mirror the forward cadence without recursively returning an
            // already-articulated pose. Upper-body articulation is applied
            // exactly once after the action landmarks are complete.
            const float BackWave = -Wave;
            const float Reach = 14.0f * BackWave;
            const float PowerAlpha = 0.5f * (1.0f - BackWave);
            Pose.TorsoRotation.Pitch = -8.0f - 7.0f * BackWave;
            Pose.TorsoRotation.Yaw = -Side * (4.0f + 3.0f * BackWave);
            Pose.TorsoRotation.Roll = Side * (2.0f + 1.5f * PowerAlpha);
            Pose.TorsoCenterCm.X += 5.0f * BackWave;
            Pose.PaddleTopCm.X += Reach;
            Pose.PaddleBottomCm.X -= 20.0f * BackWave;
            Pose.PaddleBottomCm.Z += StrokeRecoveryLiftCm(NormalizedPhase);
            Pose.LeftHandCm = Pose.PaddleTopCm;
            Pose.RightHandCm = FMath::Lerp(
                Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.43f);
            Pose.TorsoRotation.Pitch *= -0.7f;
            break;
        }
        case ERaftSimCrewAvatarAction::TurnLeft:
        case ERaftSimCrewAvatarAction::TurnRight:
        {
            const float Turn = Action == ERaftSimCrewAvatarAction::TurnLeft ? -1.0f : 1.0f;
            Pose.TorsoRotation.Yaw = Turn * (18.0f + 8.0f * Wave);
            Pose.PaddleBottomCm.Y = Turn * 58.0f;
            Pose.PaddleTopCm.Y = Turn * 20.0f;
            Pose.LeftHandCm = Pose.PaddleTopCm;
            Pose.RightHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.42f);
            break;
        }
        case ERaftSimCrewAvatarAction::Brace:
            Pose.TorsoCenterCm.Z -= 15.0f;
            Pose.HeadCenterCm.Z -= 15.0f;
            Pose.TorsoRotation.Pitch = 18.0f;
            Pose.PaddleTopCm = FVector(38.0f, -55.0f, 28.0f);
            Pose.PaddleBottomCm = FVector(38.0f, 55.0f, 20.0f);
            Pose.LeftHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.28f);
            Pose.RightHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.72f);
            break;
        case ERaftSimCrewAvatarAction::HighSidePort:
        case ERaftSimCrewAvatarAction::HighSideStarboard:
        {
            const float Shift = Action == ERaftSimCrewAvatarAction::HighSidePort ? -1.0f : 1.0f;
            // High-side is a coordinated body translation with planted feet,
            // not a torso-only bend. The old pose moved torso/head by 32-34 cm
            // while shoulders, pelvis, knees, and feet stayed at the original
            // seat. That stretched the rig through its project-owned PFD and
            // helmet overlays and produced the doubled/intersecting silhouettes
            // visible in the v552 wrap review. Move the entire kinematic chain
            // toward the high tube, tapering only below the hips so the boots
            // retain a credible brace against the floor.
            const auto ShiftLaterally = [Shift](FVector& PointCm, float DistanceCm)
            {
                PointCm.Y += Shift * DistanceCm;
            };
            ShiftLaterally(Pose.TorsoCenterCm, 32.0f);
            ShiftLaterally(Pose.HeadCenterCm, 34.0f);
            ShiftLaterally(Pose.LeftShoulderCm, 30.0f);
            ShiftLaterally(Pose.RightShoulderCm, 30.0f);
            ShiftLaterally(Pose.LeftHandCm, 32.0f);
            ShiftLaterally(Pose.RightHandCm, 32.0f);
            ShiftLaterally(Pose.LeftHipCm, 28.0f);
            ShiftLaterally(Pose.RightHipCm, 28.0f);
            ShiftLaterally(Pose.LeftKneeCm, 22.0f);
            ShiftLaterally(Pose.RightKneeCm, 22.0f);
            ShiftLaterally(Pose.LeftFootCm, 14.0f);
            ShiftLaterally(Pose.RightFootCm, 14.0f);
            Pose.TorsoRotation.Roll = -Shift * 28.0f;

            // Keep the emergency paddle in the paddler's hands instead of
            // making it disappear for the duration of the high-side command.
            // The inboard hand stays high on the grip while the outside hand
            // plants the shaft toward the commanded tube. Extrapolating from
            // those two hand positions places the blade near the waterline and
            // keeps both production-mesh hands on the same visible shaft.
            const FVector InboardHand(24.0f, Shift * 18.0f, 58.0f);
            const FVector HighSideHand(42.0f, Shift * 58.0f, 34.0f);
            if (Shift < 0.0f)
            {
                Pose.LeftHandCm = HighSideHand;
                Pose.RightHandCm = InboardHand;
            }
            else
            {
                Pose.LeftHandCm = InboardHand;
                Pose.RightHandCm = HighSideHand;
            }
            Pose.PaddleTopCm = InboardHand;
            const FVector HighSidePaddleDirection =
                (HighSideHand - InboardHand).GetSafeNormal();
            Pose.PaddleBottomCm = HighSideHand + HighSidePaddleDirection * 28.0f;
            Pose.bShowPaddle = true;
            break;
        }
        case ERaftSimCrewAvatarAction::Falling:
            Pose.TorsoCenterCm = FVector(18.0f, 0.0f, 48.0f);
            Pose.TorsoRotation = FRotator(55.0f, 10.0f * Wave, 38.0f);
            Pose.HeadCenterCm = FVector(34.0f, 4.0f, 52.0f);
            Pose.LeftHandCm = FVector(0.0f, -48.0f, 62.0f);
            Pose.RightHandCm = FVector(22.0f, 46.0f, 67.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::Swimming:
            Pose.TorsoCenterCm = FVector(0.0f, 0.0f, 12.0f + 2.0f * Wave);
            Pose.TorsoRotation = FRotator(0.0f, 88.0f, 0.0f);
            Pose.HeadCenterCm = FVector(28.0f, 0.0f, 18.0f + 2.0f * Wave);
            Pose.LeftShoulderCm = FVector(10.0f, -14.0f, 13.0f);
            Pose.RightShoulderCm = FVector(10.0f, 14.0f, 13.0f);
            Pose.LeftHandCm = FVector(35.0f + 18.0f * Wave, -25.0f, 8.0f);
            Pose.RightHandCm = FVector(35.0f - 18.0f * Wave, 25.0f, 8.0f);
            Pose.LeftHipCm = FVector(-22.0f, -8.0f, 10.0f);
            Pose.RightHipCm = FVector(-22.0f, 8.0f, 10.0f);
            Pose.LeftKneeCm = FVector(-48.0f, -13.0f, 7.0f + 8.0f * Wave);
            Pose.RightKneeCm = FVector(-48.0f, 13.0f, 7.0f - 8.0f * Wave);
            Pose.LeftFootCm = FVector(-75.0f, -14.0f, 8.0f);
            Pose.RightFootCm = FVector(-75.0f, 14.0f, 8.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::ReachRescue:
            Pose.TorsoRotation.Pitch = -28.0f;
            Pose.TorsoCenterCm.X += 12.0f;
            Pose.LeftHandCm = FVector(65.0f, -16.0f, 43.0f);
            Pose.RightHandCm = FVector(65.0f, 16.0f, 43.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::ThrowLine:
            Pose.TorsoRotation.Yaw = 18.0f * Side;
            Pose.LeftHandCm = FVector(18.0f, -10.0f * Side, 70.0f);
            Pose.RightHandCm = FVector(58.0f, 30.0f * Side, 86.0f + 8.0f * Wave);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::Reentry:
            Pose.TorsoCenterCm = FVector(36.0f, 0.0f, 43.0f);
            Pose.TorsoRotation.Pitch = -58.0f;
            Pose.HeadCenterCm = FVector(55.0f, 0.0f, 57.0f);
            Pose.LeftHandCm = FVector(70.0f, -25.0f, 38.0f);
            Pose.RightHandCm = FVector(70.0f, 25.0f, 38.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::SeatedIdle:
        default:
            Pose.TorsoCenterCm.Z += 1.5f * Wave;
            Pose.HeadCenterCm.Z += 2.0f * Wave;
            break;
    }
    if (UsesWaistPivotedUpperBodyArticulation(Action))
    {
        ApplyWaistPivotedUpperBodyArticulation(Pose);
    }
    return Pose;
}

float URaftSimCrewAvatarPoseLibrary::GetDeterministicTimingOffset(
    int32 VariantIndex,
    bool bGuide)
{
    // At the 0.8 s production cadence these offsets span about 46 ms: enough
    // to break a cloned silhouette, still tight enough to read as a trained
    // crew responding to one guide call.
    static constexpr float PaddlerOffsets[] = {-0.026f, 0.018f, 0.032f, -0.012f};
    if (bGuide)
    {
        return 0.045f;
    }
    return PaddlerOffsets[FMath::Abs(VariantIndex) % UE_ARRAY_COUNT(PaddlerOffsets)];
}

ARaftSimCrewAvatarActor::ARaftSimCrewAvatarActor()
{
    PrimaryActorTick.bCanEverTick = true;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("AvatarRoot"));
    SetRootComponent(Root);
    ProductionVisual = CreateDefaultSubobject<UChildActorComponent>(TEXT("ProductionVisual"));
    ProductionVisual->SetupAttachment(Root);
    ProductionVisual->SetVisibility(false, true);
    ProductionPfd = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProductionPfd"));
    ProductionPfd->SetupAttachment(Root);
    ProductionPfd->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProductionPfd->SetCastShadow(true);
    ProductionPfd->SetVisibility(false, true);
    ProductionHelmet = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProductionHelmet"));
    ProductionHelmet->SetupAttachment(Root);
    ProductionHelmet->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProductionHelmet->SetCastShadow(true);
    ProductionHelmet->SetVisibility(false, true);
    ProductionLeftBoot = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProductionLeftBoot"));
    ProductionLeftBoot->SetupAttachment(Root);
    ProductionLeftBoot->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProductionLeftBoot->SetCastShadow(true);
    ProductionLeftBoot->SetVisibility(false, true);
    ProductionRightBoot = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProductionRightBoot"));
    ProductionRightBoot->SetupAttachment(Root);
    ProductionRightBoot->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProductionRightBoot->SetCastShadow(true);
    ProductionRightBoot->SetVisibility(false, true);
}

void ARaftSimCrewAvatarActor::BeginPlay()
{
    Super::BeginPlay();
    BuildVisual();
}

void ARaftSimCrewAvatarActor::InitializeAvatarVisual()
{
    BuildVisual();
}

AActor* ARaftSimCrewAvatarActor::GetProductionVisualActor() const
{
    return ProductionVisual ? ProductionVisual->GetChildActor() : nullptr;
}

void ARaftSimCrewAvatarActor::SetProductionBodyOnlyShadowMode(bool bEnabled)
{
    for (UProceduralMeshComponent* Part : BodyParts)
    {
        if (Part)
        {
            Part->SetCastShadow(!bEnabled);
        }
    }
    for (UStaticMeshComponent* Equipment : {
             ProductionPfd.Get(), ProductionHelmet.Get(),
             ProductionLeftBoot.Get(), ProductionRightBoot.Get()})
    {
        if (Equipment)
        {
            Equipment->SetCastShadow(!bEnabled);
        }
    }
    if (ARaftSimMetaHumanCrewVisualActor* MetaHumanVisual =
            Cast<ARaftSimMetaHumanCrewVisualActor>(GetProductionVisualActor()))
    {
        MetaHumanVisual->SetBodyOnlyShadowMode(bEnabled);
    }
}

void ARaftSimCrewAvatarActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float CyclesPerSecond = CurrentAction == ERaftSimCrewAvatarAction::Swimming ? 0.8f : 1.25f;
    const float PhaseStep = DeltaSeconds * CyclesPerSecond * ActionIntensity;
    AnimationPhase = FMath::IsFinite(PhaseStep)
        ? FMath::Frac(AnimationPhase + PhaseStep)
        : 0.0f;
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(CurrentAction, AnimationPhase, SeatSide);
    // The project-owned safety gear remains visible over the native rigged
    // fallback, so it must follow the same pose even when a production body is active.
    ApplyPose(Pose);
    DispatchProductionPose();
    AlignProductionHeadgearToSolvedHead();
}

bool ARaftSimCrewAvatarActor::HasFiniteVisualTransforms() const
{
    if (GetActorTransform().ContainsNaN())
    {
        return false;
    }
    if (bUsingProductionVisual)
    {
        const AActor* ChildActor = ProductionVisual ? ProductionVisual->GetChildActor() : nullptr;
        return ChildActor && !ChildActor->GetActorTransform().ContainsNaN() &&
            (!HasProductionWhitewaterPfd() ||
             !ProductionPfd->GetRelativeTransform().ContainsNaN()) &&
            (!HasProductionWhitewaterHelmet() ||
             !ProductionHelmet->GetRelativeTransform().ContainsNaN());
    }
    for (UProceduralMeshComponent* Part : BodyParts)
    {
        if (!Part || Part->GetRelativeTransform().ContainsNaN())
        {
            return false;
        }
        const FProcMeshSection* Section = Part->GetProcMeshSection(0);
        if (!Section)
        {
            return false;
        }
        for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
        {
            if (Vertex.Position.ContainsNaN() || Vertex.Normal.ContainsNaN() ||
                Vertex.Tangent.TangentX.ContainsNaN())
            {
                return false;
            }
        }
    }
    return !HasProductionWhitewaterPfd() ||
        !ProductionPfd->GetRelativeTransform().ContainsNaN();
}

float ARaftSimCrewAvatarActor::GetProductionHelmetHeadErrorCm() const
{
    const ARaftSimMetaHumanCrewVisualActor* MetaHumanVisual =
        Cast<ARaftSimMetaHumanCrewVisualActor>(GetProductionVisualActor());
    if (!MetaHumanVisual || !Helmet || !Root)
    {
        return TNumericLimits<float>::Max();
    }
    const FVector SolvedHeadRelativeCm =
        Root->GetComponentTransform().InverseTransformPosition(
            MetaHumanVisual->GetSolvedHeadWorldLocation());
    const USceneComponent* FittedHelmet = HasProductionWhitewaterHelmet()
        ? static_cast<const USceneComponent*>(ProductionHelmet.Get())
        : static_cast<const USceneComponent*>(Helmet.Get());
    const FQuat HelmetRotation = FittedHelmet->GetRelativeRotation().Quaternion();
    const FVector AssetShellOffset = HasProductionWhitewaterHelmet()
        ? FVector::ZeroVector
        : kProductionHelmetShellOffsetCm;
    const FVector FittedHeadCenterCm = FittedHelmet->GetRelativeLocation() -
        HelmetRotation.RotateVector(
            kProductionHelmetSkullCenterOffsetCm + AssetShellOffset);
    return FVector::Distance(FittedHeadCenterCm, SolvedHeadRelativeCm);
}

float ARaftSimCrewAvatarActor::GetProductionPfdTorsoErrorCm() const
{
    if (!HasProductionWhitewaterPfd())
    {
        return TNumericLimits<float>::Max();
    }
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            CurrentAction, AnimationPhase, SeatSide);
    return FVector::Distance(ProductionPfd->GetRelativeLocation(), Pose.TorsoCenterCm);
}

FVector ARaftSimCrewAvatarActor::GetBodyProportionScale() const
{
    // X is body depth, Y is shoulder/hip width, and Z is stature/bulk. The
    // restrained range preserves every authored joint target and animation.
    static const FVector Profiles[] = {
        FVector(1.00f, 1.00f, 1.00f),
        FVector(0.95f, 0.92f, 0.98f),
        FVector(1.05f, 1.07f, 1.03f),
        FVector(0.98f, 1.02f, 0.94f)};
    constexpr int32 ProfileCount = static_cast<int32>(UE_ARRAY_COUNT(Profiles));
    return Profiles[FMath::Clamp(VariantIndex, 0, ProfileCount - 1)];
}

FLinearColor ARaftSimCrewAvatarActor::GetSkinTone() const
{
    // Linear-space outdoor skin references. These stay deliberately varied but
    // bounded so the shared subsurface material remains plausible in every
    // authored weather preset.
    static const FLinearColor Tones[] = {
        FLinearColor(0.55f, 0.34f, 0.23f, 1.0f),
        FLinearColor(0.78f, 0.54f, 0.38f, 1.0f),
        FLinearColor(0.29f, 0.14f, 0.085f, 1.0f),
        FLinearColor(0.66f, 0.41f, 0.27f, 1.0f)};
    constexpr int32 ToneCount = static_cast<int32>(UE_ARRAY_COUNT(Tones));
    return Tones[FMath::Clamp(VariantIndex, 0, ToneCount - 1)];
}

bool ARaftSimCrewAvatarActor::HasLayeredCommercialSafetyGear() const
{
    const auto HasVertices = [](UProceduralMeshComponent* Component, int32 Minimum)
    {
        const FProcMeshSection* Section = Component ? Component->GetProcMeshSection(0) : nullptr;
        return Section && Section->ProcVertexBuffer.Num() >= Minimum;
    };
    const bool bCompletePfd = HasProductionWhitewaterPfd() ||
        (HasVertices(Pfd, 800) &&
         HasVertices(PfdRearWebbing, 1000) &&
         HasVertices(PfdBelt, 400) &&
         HasVertices(PfdBuckle, 300));
    return LeftBoot && RightBoot && bCompletePfd &&
        (HasProductionWhitewaterHelmet() ||
         (HasVertices(Helmet, 250) &&
          HasVertices(HelmetRim, 400) &&
          HasVertices(HelmetRetention, 800)));
}

bool ARaftSimCrewAvatarActor::HasProductionWhitewaterHelmet() const
{
    return ProductionHelmet && ProductionHelmet->GetStaticMesh() != nullptr;
}

bool ARaftSimCrewAvatarActor::HasProductionWhitewaterPfd() const
{
    return ProductionPfd && ProductionPfd->GetStaticMesh() != nullptr;
}

bool ARaftSimCrewAvatarActor::HasProductionRiverBoots() const
{
    return ProductionLeftBoot && ProductionLeftBoot->GetStaticMesh() != nullptr &&
        ProductionRightBoot && ProductionRightBoot->GetStaticMesh() != nullptr;
}

bool ARaftSimCrewAvatarActor::HasCommercialPaddleSilhouette() const
{
    const auto VertexCount = [](UProceduralMeshComponent* Component)
    {
        const FProcMeshSection* Section = Component ? Component->GetProcMeshSection(0) : nullptr;
        return Section ? Section->ProcVertexBuffer.Num() : 0;
    };
    return VertexCount(PaddleShaft) > 100 &&
        VertexCount(PaddleBlade) >= 60 &&
        VertexCount(PaddleGrip) > 100;
}

bool ARaftSimCrewAvatarActor::HasBatchedFacialFeatures() const
{
    if (!Head)
    {
        return false;
    }
    const FProcMeshSection* Section = Head->GetProcMeshSection(0);
    if (!Section || Section->ProcVertexBuffer.Num() < 3000)
    {
        return false;
    }
    TSet<FColor> FeatureColors;
    for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
    {
        FeatureColors.Add(Vertex.Color);
    }
    return FeatureColors.Num() >= 6;
}

void ARaftSimCrewAvatarActor::SetAvatarAction(
    ERaftSimCrewAvatarAction NewAction,
    float Intensity)
{
    if (CurrentAction != NewAction)
    {
        CurrentAction = NewAction;
        AnimationPhase = WrapNormalizedPhase(AnimationPhaseOffset);
    }
    ActionIntensity = FMath::Clamp(Intensity, 0.15f, 2.0f);
    if (bVisualBuilt)
    {
        // Action transitions can be observed before the actor's next Tick
        // (the rescue loop does this when a seated guest becomes a swimmer).
        // Publish the procedural PPE and exact body as one atomic pose so the
        // helmet cannot spend a frame at the previous action's head location.
        const FRaftSimCrewAvatarPose Pose =
            URaftSimCrewAvatarPoseLibrary::EvaluatePose(
                CurrentAction, AnimationPhase, SeatSide);
        ApplyPose(Pose);
        DispatchProductionPose();
        AlignProductionHeadgearToSolvedHead();
    }
    else
    {
        DispatchProductionPose();
    }
}

void ARaftSimCrewAvatarActor::ConfigureAppearance(
    int32 InVariantIndex,
    int32 InSeatSide,
    bool bInGuide)
{
    VariantIndex = FMath::Abs(InVariantIndex) % 4;
    SeatSide = InSeatSide < 0 ? -1 : 1;
    bGuide = bInGuide;
    AnimationPhaseOffset =
        URaftSimCrewAvatarPoseLibrary::GetDeterministicTimingOffset(VariantIndex, bGuide);
    AnimationPhase = WrapNormalizedPhase(AnimationPhaseOffset);
    if (!bVisualBuilt)
    {
        return;
    }
    static const TCHAR* PfdPaths[] = {
        TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Red.M_RaftSim_PFD_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Blue.M_RaftSim_PFD_Blue")};
    const int32 PfdVariant = bGuide ? 2 : VariantIndex;
    UMaterialInterface* PfdMaterial =
        LoadObject<UMaterialInterface>(nullptr, PfdPaths[PfdVariant]);
    if (Pfd && PfdMaterial)
    {
        Pfd->SetMaterial(0, PfdMaterial);
    }
    if (ProductionPfd && PfdMaterial)
    {
        ProductionPfd->SetMaterial(0, PfdMaterial);
    }
    static const TCHAR* HelmetPaths[] = {
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_White.M_RaftSim_Helmet_White"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_Red.M_RaftSim_Helmet_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_Yellow.M_RaftSim_Helmet_Yellow")};
    const TCHAR* VisibleHelmetPath = bGuide
        ? TEXT("/Game/RaftSim/Materials/M_RaftSim_GuideHelmet.M_RaftSim_GuideHelmet")
        : HelmetPaths[VariantIndex];
    UMaterialInterface* VisibleHelmet =
        LoadObject<UMaterialInterface>(nullptr, VisibleHelmetPath);
    if (VisibleHelmet)
    {
        Helmet->SetMaterial(0, VisibleHelmet);
        HelmetRim->SetMaterial(0, VisibleHelmet);
        if (ProductionHelmet)
        {
            ProductionHelmet->SetMaterial(0, VisibleHelmet);
        }
    }
    if (ProductionHelmet)
    {
        if (UMaterialInterface* Webbing = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Materials/M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing")))
        {
            ProductionHelmet->SetMaterial(1, Webbing);
            ProductionHelmet->SetMaterial(2, Webbing);
        }
        if (UMaterialInterface* Hardware = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft")))
        {
            ProductionHelmet->SetMaterial(3, Hardware);
        }
    }
    if (ProductionPfd)
    {
        if (UMaterialInterface* Webbing = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Materials/M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing")))
        {
            ProductionPfd->SetMaterial(1, Webbing);
            ProductionPfd->SetMaterial(4, Webbing);
        }
        if (UMaterialInterface* Hardware = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft")))
        {
            ProductionPfd->SetMaterial(2, Hardware);
        }
        if (UMaterialInterface* Reflective = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_White.M_RaftSim_Helmet_White")))
        {
            ProductionPfd->SetMaterial(3, Reflective);
        }
    }
    RebuildSafetyGearMeshes();
    RebuildHeadMesh();
    ApplyPose(URaftSimCrewAvatarPoseLibrary::EvaluatePose(CurrentAction, AnimationPhase, SeatSide));
    TryActivateProductionVisual();
}

FString ARaftSimCrewAvatarActor::GetProductionVisualClassPath() const
{
    FString Candidate;
    if (bGuide)
    {
        if (ProductionGuideVisualClassPath.IsValid())
        {
            Candidate = ProductionGuideVisualClassPath.ToString();
        }
        else
        {
            Candidate = TEXT(
                "/Game/RaftSim/Characters/Production/BP_RaftSim_Guide.BP_RaftSim_Guide_C");
        }
    }
    else if (ProductionCrewVisualClassPaths.IsValidIndex(VariantIndex) &&
             ProductionCrewVisualClassPaths[VariantIndex].IsValid())
    {
        Candidate = ProductionCrewVisualClassPaths[VariantIndex].ToString();
    }
    else
    {
        Candidate = FString::Printf(
            TEXT("/Game/RaftSim/Characters/Production/BP_RaftSim_Crew_%02d.BP_RaftSim_Crew_%02d_C"),
            VariantIndex + 1,
            VariantIndex + 1);
    }

    const FString CandidatePackage = FPackageName::ObjectPathToPackageName(Candidate);
    if (!CandidatePackage.IsEmpty() && FPackageName::DoesPackageExist(CandidatePackage))
    {
        return Candidate;
    }
    // Select the native adapter only for a complete roster. It instantiates
    // each optimized Blueprint internally so face RigLogic, grooms and
    // wardrobe remain intact while the host keeps deterministic pose authority.
    if (ARaftSimMetaHumanCrewVisualActor::AreAllProductionCharactersAvailable())
    {
        return ARaftSimMetaHumanCrewVisualActor::StaticClass()->GetPathName();
    }
    // The local blank MetaHuman archetype remains an offline diagnostic. It is
    // never auto-promoted when the reviewed optimized roster is incomplete.
    const FString CC0MeshPackage = bGuide
        ? TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Guide")
        : FString::Printf(
              TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Crew%02d"),
              VariantIndex + 1);
    if (FPackageName::DoesPackageExist(CC0MeshPackage))
    {
        return ARaftSimCC0CrewVisualActor::StaticClass()->GetPathName();
    }
    if (FPackageName::DoesPackageExist(
            TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")))
    {
        return ARaftSimMannyCrewVisualActor::StaticClass()->GetPathName();
    }
    return Candidate;
}

void ARaftSimCrewAvatarActor::TryActivateProductionVisual()
{
    bUsingProductionVisual = false;
    if (!ProductionVisual)
    {
        SetProceduralVisualVisible(true);
        return;
    }

    const FString ClassPath = GetProductionVisualClassPath();
    const bool bNativeClass = ClassPath.StartsWith(TEXT("/Script/"));
    const FString PackageName = bNativeClass
        ? FString()
        : FPackageName::ObjectPathToPackageName(ClassPath);
    if (ClassPath.IsEmpty() ||
        (!bNativeClass && (PackageName.IsEmpty() || !FPackageName::DoesPackageExist(PackageName))))
    {
        ProductionVisual->SetChildActorClass(nullptr);
        ProductionVisual->SetVisibility(false, true);
        SetProceduralVisualVisible(true);
        return;
    }

    const FSoftClassPath SoftClassPath(ClassPath);
    UClass* VisualClass = SoftClassPath.TryLoadClass<AActor>();
    if (!VisualClass || !VisualClass->ImplementsInterface(URaftSimCrewProductionVisual::StaticClass()))
    {
        ProductionVisual->SetChildActorClass(nullptr);
        ProductionVisual->SetVisibility(false, true);
        SetProceduralVisualVisible(true);
        return;
    }

    ProductionVisual->SetChildActorClass(VisualClass);
    AActor* VisualActor = ProductionVisual->GetChildActor();
    if (!VisualActor)
    {
        ProductionVisual->SetVisibility(false, true);
        SetProceduralVisualVisible(true);
        return;
    }

    bUsingProductionVisual = true;
    ProductionVisual->SetVisibility(true, true);
    SetProceduralVisualVisible(false);
    IRaftSimCrewProductionVisual::Execute_ConfigureCrewAppearance(
        VisualActor,
        VariantIndex,
        SeatSide,
        bGuide);
    if (const ARaftSimMetaHumanCrewVisualActor* MetaHumanVisual =
            Cast<ARaftSimMetaHumanCrewVisualActor>(VisualActor);
        MetaHumanVisual && !MetaHumanVisual->IsBodyReady())
    {
        bUsingProductionVisual = false;
        ProductionVisual->SetChildActorClass(nullptr);
        if (TryActivateCC0FallbackVisual())
        {
            DispatchProductionPose();
            return;
        }
        ProductionVisual->SetVisibility(false, true);
        SetProceduralVisualVisible(true);
        return;
    }
    DispatchProductionPose();
    AlignProductionHeadgearToSolvedHead();
}

bool ARaftSimCrewAvatarActor::TryActivateCC0FallbackVisual()
{
    if (!ProductionVisual)
    {
        return false;
    }
    const FString CC0MeshPackage = bGuide
        ? TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Guide")
        : FString::Printf(
              TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Crew%02d"),
              VariantIndex + 1);
    if (!FPackageName::DoesPackageExist(CC0MeshPackage))
    {
        return false;
    }

    ProductionVisual->SetChildActorClass(ARaftSimCC0CrewVisualActor::StaticClass());
    AActor* FallbackActor = ProductionVisual->GetChildActor();
    if (!FallbackActor)
    {
        ProductionVisual->SetChildActorClass(nullptr);
        return false;
    }
    IRaftSimCrewProductionVisual::Execute_ConfigureCrewAppearance(
        FallbackActor,
        VariantIndex,
        SeatSide,
        bGuide);
    const ARaftSimCC0CrewVisualActor* CC0Visual =
        Cast<ARaftSimCC0CrewVisualActor>(FallbackActor);
    if (!CC0Visual || !CC0Visual->IsBodyReady())
    {
        ProductionVisual->SetChildActorClass(nullptr);
        return false;
    }

    bUsingProductionVisual = true;
    ProductionVisual->SetVisibility(true, true);
    SetProceduralVisualVisible(false);
    return true;
}

void ARaftSimCrewAvatarActor::SetProceduralVisualVisible(bool bVisible)
{
    if (!bVisible && Neck)
    {
        if (UMaterialInterface* ProductionWetsuit = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit")))
        {
            Neck->SetMaterial(0, ProductionWetsuit);
        }
    }
    const bool bHasProductionHelmet = HasProductionWhitewaterHelmet();
    const bool bHasProductionPfd = HasProductionWhitewaterPfd();
    const bool bHasProductionBoots = HasProductionRiverBoots();
    for (UProceduralMeshComponent* Part : BodyParts)
    {
        if (Part)
        {
            // The MetaHuman body now owns the single fitted wetsuit layer.
            // Keep only equipment overlays that are not part of that body.
            const bool bProductionOverlay =
                Part == Pfd || Part == PfdRearWebbing || Part == PfdBelt ||
                Part == PfdBuckle || Part == Helmet ||
                Part == HelmetRim || Part == HelmetRetention ||
                Part == Torso || Part == Neck ||
                Part == LeftBoot || Part == RightBoot ||
                Part == PaddleShaft || Part == PaddleBlade || Part == PaddleGrip;
            const bool bReplacedHelmetLayer = bHasProductionHelmet &&
                (Part == Helmet || Part == HelmetRim || Part == HelmetRetention);
            const bool bReplacedPfdLayer = bHasProductionPfd &&
                (Part == Pfd || Part == PfdRearWebbing ||
                 Part == PfdBelt || Part == PfdBuckle);
            const bool bReplacedBootLayer = bUsingProductionVisual &&
                bHasProductionBoots && (Part == LeftBoot || Part == RightBoot);
            Part->SetVisibility(
                (bVisible || bProductionOverlay) &&
                    !bReplacedHelmetLayer && !bReplacedPfdLayer && !bReplacedBootLayer,
                true);
        }
    }
    if (ProductionPfd)
    {
        ProductionPfd->SetVisibility(bHasProductionPfd, true);
    }
    if (ProductionHelmet)
    {
        ProductionHelmet->SetVisibility(bHasProductionHelmet, true);
    }
    if (ProductionLeftBoot)
    {
        ProductionLeftBoot->SetVisibility(
            bUsingProductionVisual && bHasProductionBoots, true);
    }
    if (ProductionRightBoot)
    {
        ProductionRightBoot->SetVisibility(
            bUsingProductionVisual && bHasProductionBoots, true);
    }
}

void ARaftSimCrewAvatarActor::DispatchProductionPose()
{
    if (!bUsingProductionVisual || !ProductionVisual)
    {
        return;
    }
    AActor* VisualActor = ProductionVisual->GetChildActor();
    if (!VisualActor ||
        !VisualActor->GetClass()->ImplementsInterface(URaftSimCrewProductionVisual::StaticClass()))
    {
        bUsingProductionVisual = false;
        ProductionVisual->SetVisibility(false, true);
        SetProceduralVisualVisible(true);
        return;
    }
    IRaftSimCrewProductionVisual::Execute_ApplyCrewPose(
        VisualActor,
        CurrentAction,
        AnimationPhase,
        ActionIntensity,
        SeatSide);
}

void ARaftSimCrewAvatarActor::AlignProductionHeadgearToSolvedHead()
{
    ARaftSimMetaHumanCrewVisualActor* MetaHumanVisual =
        Cast<ARaftSimMetaHumanCrewVisualActor>(GetProductionVisualActor());
    if (!bUsingProductionVisual || !MetaHumanVisual || !Root || !Head ||
        !Helmet || !HelmetRim || !HelmetRetention)
    {
        return;
    }
    const FVector SolvedHeadRelativeCm =
        Root->GetComponentTransform().InverseTransformPosition(
            MetaHumanVisual->GetSolvedHeadWorldLocation());
    const FVector PoseHeadRelativeCm = Head->GetRelativeLocation();
    if (SolvedHeadRelativeCm.ContainsNaN() || PoseHeadRelativeCm.ContainsNaN())
    {
        return;
    }
    // ApplyPose owns the production PPE silhouette and resets it every frame;
    // the MetaHuman adapter then publishes the exact skeletal head solve. Move
    // all three helmet layers by only that measured delta so their authored
    // fit/rotation remains intact while non-seated/high-side poses cannot leave
    // the shell beside the face.
    const FVector HeadSolveDeltaCm = SolvedHeadRelativeCm - PoseHeadRelativeCm;
    Helmet->SetRelativeLocation(
        Helmet->GetRelativeLocation() + HeadSolveDeltaCm);
    HelmetRim->SetRelativeLocation(
        HelmetRim->GetRelativeLocation() + HeadSolveDeltaCm);
    HelmetRetention->SetRelativeLocation(
        HelmetRetention->GetRelativeLocation() + HeadSolveDeltaCm);
    if (HasProductionWhitewaterHelmet())
    {
        ProductionHelmet->SetRelativeLocation(
            ProductionHelmet->GetRelativeLocation() + HeadSolveDeltaCm);
    }
}

UProceduralMeshComponent* ARaftSimCrewAvatarActor::CreateOrganicPart(
    const TCHAR* Name,
    UMaterialInterface* Material,
    int32 MaterialSlot)
{
    UProceduralMeshComponent* Part = NewObject<UProceduralMeshComponent>(this, FName(Name));
    Part->SetupAttachment(Root);
    Part->RegisterComponent();
    Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Part->SetCastShadow(true);
    Part->bUseAsyncCooking = true;
    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    TArray<FLinearColor> Colors;
    BuildUnitOrganicMesh(Vertices, Triangles, Normals, UVs, Tangents);
    Part->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false);
    if (Material)
    {
        Part->SetMaterial(MaterialSlot, Material);
    }
    BodyParts.Add(Part);
    return Part;
}

void ARaftSimCrewAvatarActor::BuildVisual()
{
    if (bVisualBuilt)
    {
        return;
    }
    auto Mat = [](const TCHAR* Path)
    { return LoadObject<UMaterialInterface>(nullptr, Path); };
    UMaterialInterface* Wetsuit = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"));
    UMaterialInterface* Jacket = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_SplashJacket.M_RaftSim_SplashJacket"));
    UMaterialInterface* Skin = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Skin.M_RaftSim_Skin"));
    UMaterialInterface* HelmetMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"));
    UMaterialInterface* Webbing = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing"));
    UMaterialInterface* BootRubber = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_BootRubber.M_RaftSim_BootRubber"));
    UMaterialInterface* Shaft = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"));
    UMaterialInterface* Blade = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade"));
    UMaterialInterface* DefaultPfd = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"));

    if (ProductionHelmet)
    {
        ProductionHelmet->SetStaticMesh(LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterHelmet.SM_RaftSim_WhitewaterHelmet")));
    }
    if (ProductionPfd)
    {
        ProductionPfd->SetStaticMesh(LoadObject<UStaticMesh>(
            nullptr,
            TEXT("/Game/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterRescuePfd."
                 "SM_RaftSim_WhitewaterRescuePfd")));
    }
    UStaticMesh* ProductionRiverBoot = LoadObject<UStaticMesh>(
        nullptr,
        TEXT("/Game/RaftSim/Equipment/Production/SM_RaftSim_WhitewaterRiverBoot."
             "SM_RaftSim_WhitewaterRiverBoot"));
    if (ProductionLeftBoot)
    {
        ProductionLeftBoot->SetStaticMesh(ProductionRiverBoot);
    }
    if (ProductionRightBoot)
    {
        ProductionRightBoot->SetStaticMesh(ProductionRiverBoot);
    }

    Pelvis = CreateOrganicPart(TEXT("Pelvis"), Wetsuit);
    Torso = CreateOrganicPart(TEXT("Torso"), Jacket ? Jacket : Wetsuit);
    Pfd = CreateOrganicPart(TEXT("PFD"), DefaultPfd);
    PfdRearWebbing = CreateOrganicPart(TEXT("PFDRearWebbing"), Webbing ? Webbing : Wetsuit);
    PfdBelt = CreateOrganicPart(TEXT("PFDBelt"), Webbing ? Webbing : Wetsuit);
    PfdBuckle = CreateOrganicPart(TEXT("PFDBuckle"), Shaft);
    Neck = CreateOrganicPart(TEXT("Neck"), Skin);
    // Preserve the detailed batched face geometry and vertex data, but use the
    // stable skin shader for the fallback. The generated face material remains
    // available to production wrappers; its current Metal path crushes large
    // regions to black and is not an acceptable runtime fallback.
    Head = CreateOrganicPart(TEXT("Head"), Skin);
    Helmet = CreateOrganicPart(TEXT("Helmet"), HelmetMat);
    HelmetRim = CreateOrganicPart(TEXT("HelmetRim"), HelmetMat);
    HelmetRetention = CreateOrganicPart(TEXT("HelmetRetention"), Webbing ? Webbing : Wetsuit);
    LeftUpperArm = CreateOrganicPart(TEXT("LeftUpperArm"), Jacket ? Jacket : Wetsuit);
    LeftLowerArm = CreateOrganicPart(TEXT("LeftLowerArm"), Jacket ? Jacket : Wetsuit);
    LeftHand = CreateOrganicPart(TEXT("LeftHand"), Skin);
    RightUpperArm = CreateOrganicPart(TEXT("RightUpperArm"), Jacket ? Jacket : Wetsuit);
    RightLowerArm = CreateOrganicPart(TEXT("RightLowerArm"), Jacket ? Jacket : Wetsuit);
    RightHand = CreateOrganicPart(TEXT("RightHand"), Skin);
    LeftThigh = CreateOrganicPart(TEXT("LeftThigh"), Wetsuit);
    LeftShin = CreateOrganicPart(TEXT("LeftShin"), Wetsuit);
    LeftBoot = CreateOrganicPart(TEXT("LeftBoot"), BootRubber ? BootRubber : Wetsuit);
    RightThigh = CreateOrganicPart(TEXT("RightThigh"), Wetsuit);
    RightShin = CreateOrganicPart(TEXT("RightShin"), Wetsuit);
    RightBoot = CreateOrganicPart(TEXT("RightBoot"), BootRubber ? BootRubber : Wetsuit);
    PaddleShaft = CreateOrganicPart(TEXT("PaddleShaft"), Shaft);
    PaddleBlade = CreateOrganicPart(TEXT("PaddleBlade"), Blade);
    PaddleGrip = CreateOrganicPart(TEXT("PaddleGrip"), Shaft);
    bVisualBuilt = true;
    RebuildPaddleMeshes();
    RebuildSafetyGearMeshes();
    ConfigureAppearance(VariantIndex, SeatSide, bGuide);
    if (!bUsingProductionVisual)
    {
        ApplyPose(URaftSimCrewAvatarPoseLibrary::EvaluatePose(CurrentAction, 0.0f, SeatSide));
    }
}

void ARaftSimCrewAvatarActor::RebuildPaddleMeshes()
{
    if (!PaddleBlade)
    {
        return;
    }
    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    BuildCommercialPaddleBladeMesh(Vertices, Triangles, Normals, UVs, Tangents);
    ReplaceMeshSection(PaddleBlade, Vertices, Triangles, Normals, UVs, Tangents);
}

void ARaftSimCrewAvatarActor::RebuildSafetyGearMeshes()
{
    if (!Pfd || !Helmet || !HelmetRim || !HelmetRetention)
    {
        return;
    }
    TArray<FVector> OrganicVertices, OrganicNormals;
    TArray<int32> OrganicTriangles;
    TArray<FVector2D> OrganicUVs;
    TArray<FProcMeshTangent> OrganicTangents;
    BuildUnitOrganicMesh(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents);

    TArray<FVector> PanelVertices, PanelNormals;
    TArray<int32> PanelTriangles;
    TArray<FVector2D> PanelUVs;
    TArray<FProcMeshTangent> PanelTangents;
    BuildUnitSafetyPanelMesh(
        PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents);

    TArray<FVector> HelmetVertices, HelmetNormals;
    TArray<int32> HelmetTriangles;
    TArray<FVector2D> HelmetUVs;
    TArray<FProcMeshTangent> HelmetTangents;
    BuildUnitHelmetShellMesh(
        HelmetVertices,
        HelmetTriangles,
        HelmetNormals,
        HelmetUVs,
        HelmetTangents);
    ReplaceMeshSection(
        Helmet,
        HelmetVertices,
        HelmetTriangles,
        HelmetNormals,
        HelmetUVs,
        HelmetTangents);

    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    const FVector Profile = GetBodyProportionScale();
    const FQuat Identity = FQuat::Identity;
    // Two anatomically tapered front cells preserve the centre zip and arm
    // clearance of a Type-V rescue PFD. A joined high-back cell, fitted side
    // wings, and shoulder foam make this read as one wearable shell rather
    // than a collection of floating capsules.
    AppendTaperedSafetyPanelInstance(
        PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
        FVector(12.7f, -7.4f * Profile.Y, 1.5f), Identity,
        FVector(2.35f, 6.8f * Profile.Y, 15.8f * Profile.Z), -1.0f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendTaperedSafetyPanelInstance(
        PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
        FVector(12.7f, 7.4f * Profile.Y, 1.5f), Identity,
        FVector(2.35f, 6.8f * Profile.Y, 15.8f * Profile.Z), 1.0f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendMeshInstance(PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
                       FVector(-12.4f, 0.0f, 3.0f), Identity,
                       FVector(2.35f, 13.7f * Profile.Y, 17.2f * Profile.Z),
                       Vertices, Triangles, Normals, UVs, Tangents);
    AppendMeshInstance(PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
                       FVector(0.0f, -16.3f * Profile.Y, -1.5f), Identity,
                       FVector(9.3f * Profile.X, 1.65f, 12.0f * Profile.Z),
                       Vertices, Triangles, Normals, UVs, Tangents);
    AppendMeshInstance(PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
                       FVector(0.0f, 16.3f * Profile.Y, -1.5f), Identity,
                       FVector(9.3f * Profile.X, 1.65f, 12.0f * Profile.Z),
                       Vertices, Triangles, Normals, UVs, Tangents);
    AppendMeshInstance(
        PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
        FVector(-0.5f, -11.5f * Profile.Y, 18.4f * Profile.Z),
        FRotator(0.0f, -20.0f, 0.0f).Quaternion(),
        FVector(8.6f * Profile.X, 3.1f, 3.2f),
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendMeshInstance(
        PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
        FVector(-0.5f, 11.5f * Profile.Y, 18.4f * Profile.Z),
        FRotator(0.0f, 20.0f, 0.0f).Quaternion(),
        FVector(8.6f * Profile.X, 3.1f, 3.2f),
        Vertices, Triangles, Normals, UVs, Tangents);
    ReplaceMeshSection(Pfd, Vertices, Triangles, Normals, UVs, Tangents);

    // Batch the webbing system separately from the foam so the fitted shell
    // has continuous shoulder straps, load-bearing side belts, a centre zip,
    // and two chest-adjustment runs. These details stay attached to the same
    // torso transform for every gameplay pose and production-body variant.
    Vertices.Reset();
    Triangles.Reset();
    Normals.Reset();
    UVs.Reset();
    Tangents.Reset();
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-9.5f, -11.7f, 17.5f), FVector(10.8f, -10.4f, 14.0f), 0.72f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-9.5f, 11.7f, 17.5f), FVector(10.8f, 10.4f, 14.0f), 0.72f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-14.7f, -13.7f, -7.0f), FVector(-14.7f, 13.7f, -7.0f), 0.68f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-10.5f, -18.1f, -6.2f), FVector(11.8f, -18.1f, -6.2f), 0.74f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-10.5f, 18.1f, -6.2f), FVector(11.8f, 18.1f, -6.2f), 0.74f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(15.3f, 0.0f, -11.5f), FVector(15.3f, 0.0f, 14.2f), 0.48f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(15.2f, -10.0f, 6.0f), FVector(15.2f, -10.0f, 11.0f), 0.68f,
        Vertices, Triangles, Normals, UVs, Tangents);
    ReplaceMeshSection(PfdRearWebbing, Vertices, Triangles, Normals, UVs, Tangents);

    Vertices.Reset();
    Triangles.Reset();
    Normals.Reset();
    UVs.Reset();
    Tangents.Reset();
    for (const float Height : {-7.0f, 1.0f})
    {
        AppendRoundedLimbInstance(
            OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
            FVector(15.2f, -13.5f, Height), FVector(15.2f, -1.5f, Height), 0.62f,
            Vertices, Triangles, Normals, UVs, Tangents);
        AppendRoundedLimbInstance(
            OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
            FVector(15.2f, 1.5f, Height), FVector(15.2f, 13.5f, Height), 0.62f,
            Vertices, Triangles, Normals, UVs, Tangents);
    }
    ReplaceMeshSection(PfdBelt, Vertices, Triangles, Normals, UVs, Tangents);

    Vertices.Reset();
    Triangles.Reset();
    Normals.Reset();
    UVs.Reset();
    Tangents.Reset();
    for (const float Height : {-7.0f, 1.0f})
    {
        AppendMeshInstance(
            PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
            FVector(15.9f, 0.0f, Height), Identity, FVector(0.7f, 1.9f, 1.45f),
            Vertices, Triangles, Normals, UVs, Tangents);
    }
    AppendMeshInstance(
        PanelVertices, PanelTriangles, PanelNormals, PanelUVs, PanelTangents,
        FVector(15.8f, -9.0f, 8.6f), Identity, FVector(0.45f, 2.8f, 2.2f),
        Vertices, Triangles, Normals, UVs, Tangents);
    ReplaceMeshSection(PfdBuckle, Vertices, Triangles, Normals, UVs, Tangents);

    Vertices.Reset();
    Triangles.Reset();
    Normals.Reset();
    UVs.Reset();
    Tangents.Reset();
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-2.0f, -8.0f, 5.0f), FVector(2.0f, -4.5f, -9.0f), 0.48f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-2.0f, 8.0f, 5.0f), FVector(2.0f, 4.5f, -9.0f), 0.48f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(2.0f, -4.5f, -9.0f), FVector(2.0f, 4.5f, -9.0f), 0.48f,
        Vertices, Triangles, Normals, UVs, Tangents);
    // Low-profile black inserts read as the drainage/vent slots found in a
    // real river helmet without cutting unstable holes into the shell mesh.
    for (const float Lateral : {-5.2f, 0.0f, 5.2f})
    {
        AppendRoundedLimbInstance(
            OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
            FVector(-5.0f, Lateral, 12.0f), FVector(3.8f, Lateral, 12.5f), 0.30f,
            Vertices, Triangles, Normals, UVs, Tangents);
    }
    ReplaceMeshSection(HelmetRetention, Vertices, Triangles, Normals, UVs, Tangents);

    // Three disconnected rounded strips form a U-shaped helmet edge around
    // the temples and rear skull in one mesh section. A flattened ellipsoid
    // cannot represent a rim: it becomes a solid visor across the face.
    Vertices.Reset();
    Triangles.Reset();
    Normals.Reset();
    UVs.Reset();
    Tangents.Reset();
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-6.0f, -10.0f, -0.5f), FVector(-6.0f, 10.0f, -0.5f), 0.68f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-6.0f, -10.0f, -0.5f), FVector(7.0f, -10.0f, 2.0f), 0.68f,
        Vertices, Triangles, Normals, UVs, Tangents);
    AppendRoundedLimbInstance(
        OrganicVertices, OrganicTriangles, OrganicNormals, OrganicUVs, OrganicTangents,
        FVector(-6.0f, 10.0f, -0.5f), FVector(7.0f, 10.0f, 2.0f), 0.68f,
        Vertices, Triangles, Normals, UVs, Tangents);
    ReplaceMeshSection(HelmetRim, Vertices, Triangles, Normals, UVs, Tangents);
}

void ARaftSimCrewAvatarActor::RebuildHeadMesh()
{
    if (!Head)
    {
        return;
    }
    TArray<FVector> SourceVertices, SourceNormals;
    TArray<int32> SourceTriangles;
    TArray<FVector2D> SourceUVs;
    TArray<FProcMeshTangent> SourceTangents;
    BuildUnitOrganicMesh(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents);

    TArray<FVector> HeadSourceVertices, HeadSourceNormals;
    TArray<int32> HeadSourceTriangles;
    TArray<FVector2D> HeadSourceUVs;
    TArray<FProcMeshTangent> HeadSourceTangents;
    BuildUnitHeadMesh(
        HeadSourceVertices,
        HeadSourceTriangles,
        HeadSourceNormals,
        HeadSourceUVs,
        HeadSourceTangents);

    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    TArray<FLinearColor> Colors;
    const FQuat Identity = FQuat::Identity;
    const FLinearColor Skin = GetSkinTone();
    // Outdoor eyes occupy very few gameplay pixels. Near-white detached
    // sclera produced a high-contrast mask/skull read, so use a warmer,
    // physically darker value and smaller embedded forms.
    const FLinearColor Sclera(0.30f, 0.285f, 0.25f, 0.0f);
    static const FLinearColor IrisTones[] = {
        FLinearColor(0.045f, 0.021f, 0.010f, 0.0f),
        FLinearColor(0.035f, 0.090f, 0.115f, 0.0f),
        FLinearColor(0.025f, 0.012f, 0.006f, 0.0f),
        FLinearColor(0.055f, 0.070f, 0.025f, 0.0f)};
    const FLinearColor Iris = IrisTones[FMath::Clamp(VariantIndex, 0, 3)];
    const FLinearColor Brow(
        FMath::Max(Skin.R * 0.10f, 0.012f),
        FMath::Max(Skin.G * 0.07f, 0.008f),
        FMath::Max(Skin.B * 0.05f, 0.005f),
        0.0f);
    const FLinearColor Lip(
        FMath::Clamp(Skin.R * 0.54f + 0.025f, 0.0f, 1.0f),
        FMath::Clamp(Skin.G * 0.19f + 0.012f, 0.0f, 1.0f),
        FMath::Clamp(Skin.B * 0.22f + 0.014f, 0.0f, 1.0f),
        0.0f);
    const FLinearColor Nostril(
        FMath::Max(Skin.R * 0.055f, 0.004f),
        FMath::Max(Skin.G * 0.035f, 0.003f),
        FMath::Max(Skin.B * 0.025f, 0.002f),
        0.0f);

    auto Append = [&](const FVector& Center, const FVector& Radius, const FLinearColor& Color)
    {
        AppendColoredMeshInstance(
            SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
            Center, Identity, Radius, Color,
            Vertices, Triangles, Normals, UVs, Tangents, Colors);
    };
    AppendColoredMeshInstance(
        HeadSourceVertices,
        HeadSourceTriangles,
        HeadSourceNormals,
        HeadSourceUVs,
        HeadSourceTangents,
        FVector::ZeroVector,
        Identity,
        FVector(kBaseRadiusCm),
        Skin,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Tangents,
        Colors);
    Append(FVector(47.0f, 0.0f, -1.0f), FVector(8.0f, 5.5f, 9.0f), Skin);
    Append(FVector(0.0f, -49.0f, 0.0f), FVector(6.0f, 4.0f, 9.0f), Skin);
    Append(FVector(0.0f, 49.0f, 0.0f), FVector(6.0f, 4.0f, 9.0f), Skin);
    Append(FVector(47.5f, -16.5f, 9.0f), FVector(4.2f, 4.6f, 3.2f), Sclera);
    Append(FVector(47.5f, 16.5f, 9.0f), FVector(4.2f, 4.6f, 3.2f), Sclera);
    Append(FVector(51.3f, -16.5f, 9.0f), FVector(1.55f, 2.0f, 2.0f), Iris);
    Append(FVector(51.3f, 16.5f, 9.0f), FVector(1.55f, 2.0f, 2.0f), Iris);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(50.5f, -22.5f, 13.2f), FVector(51.0f, -11.5f, 13.5f), 0.95f,
        Skin, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(51.0f, 11.5f, 13.5f), FVector(50.5f, 22.5f, 13.2f), 0.95f,
        Skin, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(50.2f, -22.0f, 5.8f), FVector(50.7f, -12.0f, 5.5f), 0.72f,
        Skin, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(50.7f, 12.0f, 5.5f), FVector(50.2f, 22.0f, 5.8f), 0.72f,
        Skin, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(49.5f, -23.0f, 17.0f), FVector(49.5f, -11.0f, 17.5f), 1.35f,
        Brow, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(49.5f, 11.0f, 17.5f), FVector(49.5f, 23.0f, 17.0f), 1.35f,
        Brow, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    AppendColoredRoundedLimbInstance(
        SourceVertices, SourceTriangles, SourceNormals, SourceUVs, SourceTangents,
        FVector(50.0f, -10.0f, -14.0f), FVector(50.0f, 10.0f, -14.0f), 1.25f,
        Lip, Vertices, Triangles, Normals, UVs, Tangents, Colors);
    Append(FVector(54.0f, -2.7f, -4.2f), FVector(1.15f, 1.25f, 0.85f), Nostril);
    Append(FVector(54.0f, 2.7f, -4.2f), FVector(1.15f, 1.25f, 0.85f), Nostril);
    ReplaceColoredMeshSection(Head, Vertices, Triangles, Normals, UVs, Tangents, Colors);
}

void ARaftSimCrewAvatarActor::SetEllipsoid(
    UProceduralMeshComponent* Component,
    const FVector& CenterCm,
    const FRotator& Rotation,
    const FVector& RadiusCm)
{
    if (!Component)
    {
        return;
    }
    const FVector SafeCenter = CenterCm.ContainsNaN() ? FVector::ZeroVector : CenterCm;
    const FRotator SafeRotation = Rotation.ContainsNaN() ? FRotator::ZeroRotator : Rotation;
    const FVector SafeRadius(
        FMath::IsFinite(RadiusCm.X) ? FMath::Max(FMath::Abs(RadiusCm.X), 0.1f) : 1.0f,
        FMath::IsFinite(RadiusCm.Y) ? FMath::Max(FMath::Abs(RadiusCm.Y), 0.1f) : 1.0f,
        FMath::IsFinite(RadiusCm.Z) ? FMath::Max(FMath::Abs(RadiusCm.Z), 0.1f) : 1.0f);
    Component->SetRelativeLocationAndRotation(SafeCenter, SafeRotation);
    Component->SetRelativeScale3D(SafeRadius / kBaseRadiusCm);
}

void ARaftSimCrewAvatarActor::SetRoundedLimb(
    UProceduralMeshComponent* Component,
    const FVector& StartCm,
    const FVector& EndCm,
    float RadiusCm)
{
    const FVector Delta = EndCm - StartCm;
    const FVector SafeDirection = Delta.ContainsNaN() || Delta.IsNearlyZero()
        ? FVector::UpVector
        : Delta.GetSafeNormal();
    SetEllipsoid(
        Component,
        (StartCm + EndCm) * 0.5f,
        FRotationMatrix::MakeFromZ(SafeDirection).Rotator(),
        FVector(
            RadiusCm,
            RadiusCm,
            FMath::Max(Delta.ContainsNaN() ? RadiusCm : Delta.Size() * 0.5f, RadiusCm)));
}

void ARaftSimCrewAvatarActor::ApplyPose(const FRaftSimCrewAvatarPose& Pose)
{
    if (!bVisualBuilt)
    {
        return;
    }
    const FVector HipCenter = (Pose.LeftHipCm + Pose.RightHipCm) * 0.5f;
    const FQuat TorsoRotation = Pose.TorsoRotation.Quaternion();
    const FVector Profile = GetBodyProportionScale();
    const float LimbBulk = FMath::Sqrt(Profile.X * Profile.Y);
    const float HeadScale = FMath::Lerp(0.97f, 1.03f, (Profile.Z - 0.94f) / 0.09f);
    const auto TorsoPoint = [&](const FVector& OffsetCm)
    {
        return Pose.TorsoCenterCm + TorsoRotation.RotateVector(OffsetCm);
    };
    SetEllipsoid(Pelvis, HipCenter, Pose.TorsoRotation,
                 FVector(14.0f * Profile.X, 18.0f * Profile.Y, 14.0f * Profile.Z));
    SetEllipsoid(Torso, Pose.TorsoCenterCm, Pose.TorsoRotation,
                 FVector(17.0f * Profile.X, 21.0f * Profile.Y, 27.0f * Profile.Z));
    Pfd->SetRelativeLocationAndRotation(Pose.TorsoCenterCm, Pose.TorsoRotation);
    Pfd->SetRelativeScale3D(FVector::OneVector);
    PfdRearWebbing->SetRelativeLocationAndRotation(Pose.TorsoCenterCm, Pose.TorsoRotation);
    PfdRearWebbing->SetRelativeScale3D(FVector::OneVector);
    PfdBelt->SetRelativeLocationAndRotation(Pose.TorsoCenterCm, Pose.TorsoRotation);
    PfdBelt->SetRelativeScale3D(FVector::OneVector);
    PfdBuckle->SetRelativeLocationAndRotation(Pose.TorsoCenterCm, Pose.TorsoRotation);
    PfdBuckle->SetRelativeScale3D(FVector::OneVector);
    if (HasProductionWhitewaterPfd())
    {
        ProductionPfd->SetRelativeLocationAndRotation(
            Pose.TorsoCenterCm, Pose.TorsoRotation);
        ProductionPfd->SetRelativeScale3D(Profile);
    }
    const FVector CollarOffset = bUsingProductionVisual
        ? FVector(4.0f, 0.0f, 0.0f)
        : FVector::ZeroVector;
    const float CollarFit = bUsingProductionVisual ? 1.28f : 1.0f;
    SetEllipsoid(
        Neck,
        Pose.HeadCenterCm - TorsoRotation.RotateVector(FVector(0.0f, 0.0f, 12.0f)) +
            TorsoRotation.RotateVector(CollarOffset),
        Pose.TorsoRotation,
        FVector(5.8f, 5.8f, 7.0f) * CollarFit);
    SetEllipsoid(Head, Pose.HeadCenterCm, Pose.TorsoRotation,
                 FVector(11.0f, 10.0f, 13.0f) * HeadScale);
    // The component now contains an explicitly open top/back shell. Keep it
    // centred on the skull; its compact front-cut polar topology—not a scale
    // trick—guarantees that it cannot become a visor over the face. In the
    // procedural fallback Pose.HeadCenterCm is the ellipsoid centre. The
    // MetaHuman face is rigidly aligned to the solved head bone. Seat the
    // helmet above that pivot and keep only a small shell-forward allowance;
    // the previous large X correction projected the crown over the face like
    // a visor in side/high-side poses.
    // Production hair is retained as audited source data but hidden under the
    // mandatory helmet. Fit the shell to the visible MetaHuman skull rather
    // than scaling it around two overlapping hair/helmet silhouettes.
    const float HelmetFit = bUsingProductionVisual ? 0.96f : 1.0f;
    const FVector ProductionSkullCenterOffsetCm = bUsingProductionVisual
        ? kProductionHelmetSkullCenterOffsetCm
        : FVector(0.0f, 0.0f, -4.0f);
    const FVector HeadGearCenter = Pose.HeadCenterCm +
        TorsoRotation.RotateVector(ProductionSkullCenterOffsetCm);
    const FVector HelmetShellOffsetCm = bUsingProductionVisual
        ? kProductionHelmetShellOffsetCm
        : FVector(5.2f, 0.0f, 0.8f);
    SetEllipsoid(Helmet, HeadGearCenter + TorsoRotation.RotateVector(HelmetShellOffsetCm),
                 Pose.TorsoRotation,
                 FVector(13.2f * HeadScale, 12.2f * HeadScale, 14.2f * HeadScale) * HelmetFit);
    HelmetRim->SetRelativeLocationAndRotation(
        HeadGearCenter, Pose.TorsoRotation);
    HelmetRim->SetRelativeScale3D(FVector(HeadScale * HelmetFit));
    const FVector HelmetRetentionCenter = bUsingProductionVisual
        ? Pose.HeadCenterCm +
            TorsoRotation.RotateVector(kProductionHelmetRetentionOffsetCm)
        : HeadGearCenter;
    HelmetRetention->SetRelativeLocationAndRotation(
        HelmetRetentionCenter, Pose.TorsoRotation);
    HelmetRetention->SetRelativeScale3D(FVector(HelmetFit));
    if (HasProductionWhitewaterHelmet())
    {
        ProductionHelmet->SetRelativeLocationAndRotation(
            HeadGearCenter, Pose.TorsoRotation);
        ProductionHelmet->SetRelativeScale3D(FVector(HeadScale * HelmetFit));
    }

    const FVector LeftElbow = FMath::Lerp(Pose.LeftShoulderCm, Pose.LeftHandCm, 0.48f) + FVector(0.0f, -5.0f, -2.0f);
    const FVector RightElbow = FMath::Lerp(Pose.RightShoulderCm, Pose.RightHandCm, 0.48f) + FVector(0.0f, 5.0f, -2.0f);
    SetRoundedLimb(LeftUpperArm, Pose.LeftShoulderCm, LeftElbow, 5.8f * LimbBulk);
    SetRoundedLimb(LeftLowerArm, LeftElbow, Pose.LeftHandCm, 5.0f * LimbBulk);
    SetEllipsoid(
        LeftHand,
        Pose.LeftHandCm,
        FRotationMatrix::MakeFromX((Pose.LeftHandCm - LeftElbow).GetSafeNormal()).Rotator(),
        FVector(7.0f, 3.7f, 2.8f) * LimbBulk);
    SetRoundedLimb(RightUpperArm, Pose.RightShoulderCm, RightElbow, 5.8f * LimbBulk);
    SetRoundedLimb(RightLowerArm, RightElbow, Pose.RightHandCm, 5.0f * LimbBulk);
    SetEllipsoid(
        RightHand,
        Pose.RightHandCm,
        FRotationMatrix::MakeFromX((Pose.RightHandCm - RightElbow).GetSafeNormal()).Rotator(),
        FVector(7.0f, 3.7f, 2.8f) * LimbBulk);
    SetRoundedLimb(LeftThigh, Pose.LeftHipCm, Pose.LeftKneeCm, 8.3f * LimbBulk);
    SetRoundedLimb(LeftShin, Pose.LeftKneeCm, Pose.LeftFootCm, 6.7f * LimbBulk);
    SetRoundedLimb(RightThigh, Pose.RightHipCm, Pose.RightKneeCm, 8.3f * LimbBulk);
    SetRoundedLimb(RightShin, Pose.RightKneeCm, Pose.RightFootCm, 6.7f * LimbBulk);
    const FVector LeftFootDirection = (Pose.LeftFootCm - Pose.LeftKneeCm).GetSafeNormal();
    const FVector RightFootDirection = (Pose.RightFootCm - Pose.RightKneeCm).GetSafeNormal();
    SetRoundedLimb(LeftBoot, Pose.LeftFootCm - LeftFootDirection * 3.0f,
                   Pose.LeftFootCm + LeftFootDirection * 11.0f, 5.8f);
    SetRoundedLimb(RightBoot, Pose.RightFootCm - RightFootDirection * 3.0f,
                   Pose.RightFootCm + RightFootDirection * 11.0f, 5.8f);
    if (HasProductionRiverBoots())
    {
        // The generated boot's ankle-centred local +X axis points toward the
        // toe. Keep seated/high-side footwear planted in the raft plane; only
        // yaw follows the solved torso. Swimming naturally rotates the same
        // visual with the body's 88-degree yaw. The solved foot points remain
        // the single animation authority.
        const FRotator ProductionBootRotation(0.0f, Pose.TorsoRotation.Yaw, 0.0f);
        ProductionLeftBoot->SetRelativeLocationAndRotation(
            Pose.LeftFootCm, ProductionBootRotation);
        ProductionLeftBoot->SetRelativeScale3D(Profile);
        ProductionRightBoot->SetRelativeLocationAndRotation(
            Pose.RightFootCm, ProductionBootRotation);
        ProductionRightBoot->SetRelativeScale3D(Profile);
    }

    PaddleShaft->SetVisibility(Pose.bShowPaddle);
    PaddleBlade->SetVisibility(Pose.bShowPaddle);
    PaddleGrip->SetVisibility(Pose.bShowPaddle);
    if (Pose.bShowPaddle)
    {
        SetRoundedLimb(PaddleShaft, Pose.PaddleTopCm, Pose.PaddleBottomCm, 1.65f);
        const FVector Direction = (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
        const FVector PreferredBladeNormal = FVector::ForwardVector -
            Direction * FVector::DotProduct(FVector::ForwardVector, Direction);
        const FVector BladeNormal = PreferredBladeNormal.GetSafeNormal(
            SMALL_NUMBER,
            FVector::RightVector);
        PaddleBlade->SetRelativeLocationAndRotation(
            Pose.PaddleBottomCm,
            FRotationMatrix::MakeFromZY(Direction, BladeNormal).Rotator());
        PaddleBlade->SetRelativeScale3D(FVector::OneVector);
        const FVector GripDirection = FVector::CrossProduct(Direction, FVector::UpVector)
            .GetSafeNormal(SMALL_NUMBER, FVector::RightVector);
        SetRoundedLimb(
            PaddleGrip,
            Pose.PaddleTopCm - GripDirection * 7.0f,
            Pose.PaddleTopCm + GripDirection * 7.0f,
            2.2f);
    }
}
