#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

/** Small procedural props (crew accessories, raft gear): tubes, lenses and
 * boxes, committed with both windings so they never vanish to winding. */
/** The v13 production vest's seated-torso taper (vest-local cm): the front
 * leans in above mid-chest, the back moves in over the lumbar curve, both
 * blended out across the flanks. The v14 vest is fitted to the torsos as the
 * crew visual places them with this reference, so it stays the fit's
 * reference surface. */
namespace RaftSimVestShape
{
inline float FrontTaperCm(float Z)
{
    const float T = FMath::Clamp((Z - 8.0f) / 13.0f, 0.0f, 1.25f);
    return 5.5f * FMath::Pow(T, 1.5f);
}

inline float BackTaperCm(float Z)
{
    return 4.3f * FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp((9.0f - Z) / 13.0f, 0.0f, 1.0f)) *
        (1.0f - 0.3f * FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp((-8.0f - Z) / 9.0f, 0.0f, 1.0f)));
}

/** A vest-local point moved the way the mesh's own vertices were. */
inline FVector ApplySeatedTaper(const FVector& P)
{
    const float X = static_cast<float>(P.X);
    const float Front = FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp(X / 10.0f, 0.0f, 1.0f));
    const float Back = FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp(-X / 10.0f, 0.0f, 1.0f));
    const float Z = static_cast<float>(P.Z);
    return FVector(X - Front * FrontTaperCm(Z) + Back * BackTaperCm(Z), P.Y, P.Z);
}
}

namespace RaftSimAccessoryMesh
{
struct FAccessoryMesh
{
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    TArray<FLinearColor> Colors;

    int32 Add(const FVector& P, const FVector& N, const FVector2D& UV)
    {
        Vertices.Add(P);
        Normals.Add(N.GetSafeNormal());
        UVs.Add(UV);
        Tangents.Add(FProcMeshTangent(FVector::CrossProduct(N, FVector::UpVector).GetSafeNormal(), false));
        Colors.Add(FLinearColor::White);
        return Vertices.Num() - 1;
    }

    /** Closed tube from A to B (radius R, Sides around). */
    void Tube(const FVector& A, const FVector& B, float R, int32 Sides = 6)
    {
        const FVector Axis = (B - A).GetSafeNormal();
        if (Axis.IsNearlyZero())
        {
            return;
        }
        const FVector U = FVector::CrossProduct(Axis, FMath::Abs(Axis.Z) < 0.9f ? FVector::UpVector : FVector::ForwardVector)
            .GetSafeNormal();
        const FVector V = FVector::CrossProduct(Axis, U);
        const int32 Base = Vertices.Num();
        for (int32 Ring = 0; Ring < 2; ++Ring)
        {
            for (int32 Side = 0; Side < Sides; ++Side)
            {
                const float Angle = UE_TWO_PI * Side / Sides;
                const FVector Out = U * FMath::Cos(Angle) + V * FMath::Sin(Angle);
                Add((Ring ? B : A) + Out * R, Out, FVector2D(float(Side) / Sides, float(Ring)));
            }
        }
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 Next = (Side + 1) % Sides;
            Triangles.Append({Base + Side, Base + Sides + Side, Base + Next});
            Triangles.Append({Base + Next, Base + Sides + Side, Base + Sides + Next});
        }
        const int32 CapA = Add(A, -Axis, FVector2D(0.5f, 0.0f));
        const int32 CapB = Add(B, Axis, FVector2D(0.5f, 1.0f));
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 Next = (Side + 1) % Sides;
            Triangles.Append({CapA, Base + Next, Base + Side});
            Triangles.Append({CapB, Base + Sides + Side, Base + Sides + Next});
        }
    }

    /** Thin elliptical lens: front and back faces plus a rim. */
    void Lens(const FVector& Center, const FVector& Right, const FVector& Up, float Rx, float Rz, float Thickness,
              int32 Segments = 24)
    {
        const FVector Normal = FVector::CrossProduct(Right, Up).GetSafeNormal();
        for (int32 Face = 0; Face < 2; ++Face)
        {
            const FVector Offset = Normal * (Face ? -0.5f : 0.5f) * Thickness;
            const FVector FaceNormal = Face ? -Normal : Normal;
            const int32 Hub = Add(Center + Offset, FaceNormal, FVector2D(0.5f, 0.5f));
            const int32 First = Vertices.Num();
            for (int32 Segment = 0; Segment < Segments; ++Segment)
            {
                const float Angle = UE_TWO_PI * Segment / Segments;
                // Slightly squared-off sport lens rather than a perfect ellipse.
                const float C = FMath::Cos(Angle), S = FMath::Sin(Angle);
                const float Squircle = FMath::Pow(FMath::Abs(C), 0.8f) * FMath::Sign(C);
                const FVector P = Center + Offset + Right * (Rx * Squircle) + Up * (Rz * S);
                Add(P, FaceNormal, FVector2D(0.5f + 0.5f * C, 0.5f - 0.5f * S));
            }
            for (int32 Segment = 0; Segment < Segments; ++Segment)
            {
                const int32 A = First + Segment, B = First + (Segment + 1) % Segments;
                if (Face)
                {
                    Triangles.Append({Hub, A, B});
                }
                else
                {
                    Triangles.Append({Hub, B, A});
                }
            }
        }
    }

    /** Box from a centre, three axes and half extents. */
    void Box(const FVector& Center, const FVector& X, const FVector& Y, const FVector& Z, const FVector& Half)
    {
        const FVector Axes[3] = {X.GetSafeNormal(), Y.GetSafeNormal(), Z.GetSafeNormal()};
        for (int32 Axis = 0; Axis < 3; ++Axis)
        {
            for (int32 Sign = -1; Sign <= 1; Sign += 2)
            {
                const FVector N = Axes[Axis] * float(Sign);
                const FVector A = Axes[(Axis + 1) % 3] * Half[(Axis + 1) % 3];
                const FVector B = Axes[(Axis + 2) % 3] * Half[(Axis + 2) % 3];
                const FVector C = Center + N * Half[Axis];
                const int32 V0 = Add(C - A - B, N, FVector2D(0, 0));
                const int32 V1 = Add(C + A - B, N, FVector2D(1, 0));
                const int32 V2 = Add(C + A + B, N, FVector2D(1, 1));
                const int32 V3 = Add(C - A + B, N, FVector2D(0, 1));
                if (Sign > 0)
                {
                    Triangles.Append({V0, V2, V1, V0, V3, V2});
                }
                else
                {
                    Triangles.Append({V0, V1, V2, V0, V2, V3});
                }
            }
        }
    }

    /** Surface of revolution about Axis through Base. Profile holds (height,
     * radius) pairs from bottom to top; a zero radius closes that end. */
    void Lathe(const FVector& Base, const FVector& Axis, const TArray<FVector2f>& Profile, int32 Sides = 16)
    {
        const FVector A = Axis.GetSafeNormal();
        const FVector U = FVector::CrossProduct(A, FMath::Abs(A.Z) < 0.9f ? FVector::UpVector : FVector::ForwardVector)
            .GetSafeNormal();
        const FVector V = FVector::CrossProduct(A, U);
        const int32 Base0 = Vertices.Num();
        for (int32 Ring = 0; Ring < Profile.Num(); ++Ring)
        {
            // Normal from the profile's local slope (outward, tipped along the axis).
            const FVector2f Below = Profile[FMath::Max(Ring - 1, 0)], Above = Profile[FMath::Min(Ring + 1, Profile.Num() - 1)];
            const float Rise = Above.X - Below.X, Spread = Above.Y - Below.Y;
            for (int32 Side = 0; Side <= Sides; ++Side)
            {
                const float Angle = UE_TWO_PI * Side / Sides;
                const FVector Out = U * FMath::Cos(Angle) + V * FMath::Sin(Angle);
                Add(Base + A * Profile[Ring].X + Out * Profile[Ring].Y, Out * Rise - A * Spread,
                    FVector2D(float(Side) / Sides, float(Ring) / FMath::Max(Profile.Num() - 1, 1)));
            }
        }
        for (int32 Ring = 0; Ring + 1 < Profile.Num(); ++Ring)
        {
            for (int32 Side = 0; Side < Sides; ++Side)
            {
                const int32 P = Base0 + Ring * (Sides + 1) + Side, Q = P + Sides + 1;
                Triangles.Append({P, Q, P + 1, P + 1, Q, Q + 1});
            }
        }
    }

    /** Rope or cord swept along a polyline, rings shared between spans and
     * carried along without twisting; open ends are capped. */
    void Sweep(const TArray<FVector>& Points, float R, int32 Sides = 6, bool bClosed = false)
    {
        const int32 Count = Points.Num();
        if (Count < 2)
        {
            return;
        }
        auto TangentAt = [&](int32 I)
        {
            const FVector Prev = bClosed ? Points[(I - 1 + Count) % Count] : Points[FMath::Max(I - 1, 0)];
            const FVector Next = bClosed ? Points[(I + 1) % Count] : Points[FMath::Min(I + 1, Count - 1)];
            return (Next - Prev).GetSafeNormal();
        };
        FVector T = TangentAt(0);
        FVector U = FVector::CrossProduct(T, FMath::Abs(T.Z) < 0.9f ? FVector::UpVector : FVector::ForwardVector).GetSafeNormal();
        const int32 Base0 = Vertices.Num();
        const int32 Rings = bClosed ? Count + 1 : Count;
        float Along = 0.0f;
        for (int32 Ring = 0; Ring < Rings; ++Ring)
        {
            const int32 I = Ring % Count;
            const FVector NewT = TangentAt(I);
            // Parallel transport: rotate the previous frame onto the new tangent.
            U = (U - NewT * FVector::DotProduct(U, NewT)).GetSafeNormal();
            T = NewT;
            const FVector V = FVector::CrossProduct(T, U);
            if (Ring > 0)
            {
                Along += float(FVector::Distance(Points[I], Points[(Ring - 1) % Count]));
            }
            for (int32 Side = 0; Side <= Sides; ++Side)
            {
                const float Angle = UE_TWO_PI * Side / Sides;
                const FVector Out = U * FMath::Cos(Angle) + V * FMath::Sin(Angle);
                Add(Points[I] + Out * R, Out, FVector2D(Along / 6.0f, float(Side) / Sides));
            }
        }
        for (int32 Ring = 0; Ring + 1 < Rings; ++Ring)
        {
            for (int32 Side = 0; Side < Sides; ++Side)
            {
                const int32 P = Base0 + Ring * (Sides + 1) + Side, Q = P + Sides + 1;
                Triangles.Append({P, P + 1, Q, P + 1, Q + 1, Q});
            }
        }
        if (!bClosed)
        {
            for (int32 End = 0; End < 2; ++End)
            {
                const int32 Ring = End ? Count - 1 : 0;
                const FVector Normal = TangentAt(Ring) * (End ? 1.0f : -1.0f);
                const int32 Hub = Add(Points[Ring], Normal, FVector2D(0.5f, 0.5f));
                for (int32 Side = 0; Side < Sides; ++Side)
                {
                    Triangles.Append({Hub, Base0 + Ring * (Sides + 1) + Side, Base0 + Ring * (Sides + 1) + Side + 1});
                }
            }
        }
    }

    void Commit(UProceduralMeshComponent* Component, int32 Section) const
    {
        // Both windings: whichever faces the camera renders with the outward
        // normal, so the props never vanish to a winding mistake.
        TArray<int32> BothSides = Triangles;
        for (int32 Index = 0; Index + 2 < Triangles.Num(); Index += 3)
        {
            BothSides.Append({Triangles[Index], Triangles[Index + 2], Triangles[Index + 1]});
        }
        Component->CreateMeshSection_LinearColor(Section, Vertices, BothSides, Normals, UVs, Colors, Tangents, false);
    }
};

}
