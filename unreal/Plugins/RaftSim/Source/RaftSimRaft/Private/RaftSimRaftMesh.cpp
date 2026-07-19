#include "RaftSimRaftMesh.h"

namespace RaftSimRaftMesh
{
namespace
{
constexpr float kCmPerM = 100.0f;

// Sweep a circular tube of radius TubeCm along a centreline (world cm). The
// cross-section lies in the plane spanned by the horizontal radial and world
// up, so the tube reads as a fat inflated tube lying flat. Normals point out
// from the axis. Appends into Out.
void SweepTube(
    const TArray<FVector>& Centerline, bool bClosed, float TubeCm, int32 RadialSegments,
    FMeshData& Out)
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
        const FVector& P = Centerline[i];
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
            Out.Vertices.Add(P + TubeCm * Dir);
            Out.Normals.Add(Dir);
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
} // namespace

void BuildInflatableRaft(
    float LengthM, float WidthM, float TubeRadiusM,
    FMeshData& OutTubes, FMeshData& OutFloor)
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
    SweepTube(Loop, /*bClosed=*/true, Tr, /*RadialSegments=*/14, OutTubes);

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
        SweepTube(Bar, /*bClosed=*/false, ThwartR, /*RadialSegments=*/10, OutTubes);
    }

    // Inset self-bailing floor: a slightly dished grid spanning inside the tubes.
    const float FloorAx = Ax - Tr * 0.2f;
    const float FloorAy = Ay - Tr * 0.2f;
    const float FloorZ = Tr * 0.42f;
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
            OutFloor.Vertices.Add(FVector(X, Y, FloorZ + Dish));
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
}

} // namespace RaftSimRaftMesh
