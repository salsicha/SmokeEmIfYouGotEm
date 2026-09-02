#include "RaftSimCrewAvatarActor.h"

#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimMannyCrewVisualActor.h"
#include "RaftSimMetaHumanCrewVisualActor.h"
#include "RaftSimRaftActor.h"

#include "Components/ChildActorComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "ProceduralMeshComponent.h"

namespace
{
constexpr float kBaseRadiusCm = 50.0f;
const FVector kProductionSeatedPelvisReferenceExtentCm(15.0f, 23.0f, 15.0f);
constexpr float kProductionHipThighBridgeStartFraction = -0.15f;
constexpr float kProductionHipThighBridgeEndFraction = 1.06f;
constexpr float kProductionHipThighBridgeRadiusCm = 8.0f;
constexpr float kProductionShoulderSleeveRadiusCm = 5.2f;
constexpr float kProductionShoulderSleeveArmFraction = 1.0f;
// Z was 0.68 while the seated shins were short and near-horizontal; with the
// anatomical fold's ~28 cm shin drop a taller cuff swallows the lower shin
// so the ankle reads as wetsuit-into-bootie instead of a bare tube meeting a
// squat ring ("their ankles look like cylindars", 2026-09-02). X/Y widened
// the same day: at 0.88/0.92 the boot body barely exceeded the shin's own
// diameter, so from the guide seat the whole lower leg still stacked into
// one uniform tube ("the boots are still cylindars") — a chunkier bootie
// lets heel and toe break the silhouette.
// Z back to 1.0 with boot generator v2 (2026-09-02): the source now carries
// a short tapered cuff, so the squash that kept the old 15 cm cuff below the
// flexed knee is no longer needed.
const FVector kProductionRiverBootPresentationScale(0.98f, 1.04f, 1.0f);
// 2026-08-06 named human review: helmets read as off-center caps. Seat the
// shell lower on the skull and nearly centred so per-head measurement
// variance is absorbed instead of amplified.
// Rearward bias re-tuned 2026-08-08 under the corrected face frame: with
// the shell no longer worn backwards, the pure Z lift left the occiput
// exposed behind the rim (first South Fork playtest).
const FVector kProductionHelmetSkullCenterOffsetCm(-2.0f, 0.0f, 6.0f);
const FVector kProductionHelmetShellOffsetCm(0.8f, 0.0f, 0.0f);
const FVector kProductionHelmetRetentionOffsetCm(0.0f, 0.0f, 3.0f);
constexpr float kProductionHelmetReferenceFit = 0.96f;

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

void BuildUnitAnatomicalShoulderSleeveMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // The retained V2 taper fixed the missing-shoulder gap, but a perfectly
    // circular surface still read as a glossy molded tube. Keep the solved
    // shoulder-to-elbow axis authoritative while adding a denser, softly
    // elliptical shell with two incommensurate fold fields, gathered cloth at
    // the cuff, and one restrained under-arm seam. This is visual garment
    // topology only: it never changes the body pose, collision, mass, or grip.
    constexpr int32 Rings = 28;
    constexpr int32 Sides = 36;
    const auto BaseRadiusAt = [](float V)
    {
        const float SafeV = FMath::Clamp(V, 0.0f, 1.0f);
        const float Deltoid = FMath::Exp(
            -FMath::Square((SafeV - 0.18f) / 0.24f));
        const float CuffRoll = FMath::Exp(
            -FMath::Square((SafeV - 0.88f) / 0.095f));
        return 0.88f - 0.22f * SafeV + 0.16f * Deltoid +
            0.035f * CuffRoll;
    };
    const auto SurfacePoint = [&BaseRadiusAt](float V, float Theta)
    {
        const float SafeV = FMath::Clamp(V, 0.0f, 1.0f);
        const float EndEnvelope = FMath::Pow(
            FMath::Max(FMath::Sin(PI * SafeV), 0.0f),
            1.15f);
        const float DiagonalFold =
            0.055f * EndEnvelope *
                FMath::Sin(7.0f * PI * SafeV + 2.0f * Theta) +
            0.028f * EndEnvelope *
                FMath::Sin(13.0f * PI * SafeV - 3.0f * Theta + 0.70f);
        const float CuffGather =
            0.034f *
            FMath::Exp(-FMath::Square((SafeV - 0.80f) / 0.16f)) *
            FMath::Sin(5.0f * Theta + 9.0f * PI * SafeV);
        const float UnderArmDelta = FMath::FindDeltaAngleRadians(
            Theta,
            -0.5f * PI);
        const float UnderArmSeam =
            0.018f * EndEnvelope *
            FMath::Exp(-FMath::Square(UnderArmDelta / 0.12f));
        const float Radius = FMath::Max(
            BaseRadiusAt(SafeV) + DiagonalFold + CuffGather + UnderArmSeam,
            0.52f);
        const float AxialDrape =
            0.012f * EndEnvelope *
            FMath::Sin(9.0f * PI * SafeV + 4.0f * Theta);
        return FVector(
                   1.035f * Radius * FMath::Cos(Theta),
                   0.965f * Radius * FMath::Sin(Theta),
                   -1.0f + 2.0f * SafeV + AxialDrape) *
            kBaseRadiusCm;
    };
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            Vertices.Add(SurfacePoint(V, Theta));
            constexpr float DifferentialStep = 0.0025f;
            const FVector CircumferentialTangent =
                SurfacePoint(V, Theta + DifferentialStep) -
                SurfacePoint(V, Theta - DifferentialStep);
            const FVector AxialTangent =
                SurfacePoint(FMath::Min(V + DifferentialStep, 1.0f), Theta) -
                SurfacePoint(FMath::Max(V - DifferentialStep, 0.0f), Theta);
            Normals.Add(
                FVector::CrossProduct(CircumferentialTangent, AxialTangent)
                    .GetSafeNormal());
            UVs.Add(FVector2D(U, V));
            Tangents.Add(
                FProcMeshTangent(
                    CircumferentialTangent.GetSafeNormal(),
                    /*bInFlipTangentY=*/false));
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

    const int32 ShoulderCenter = Vertices.Num();
    Vertices.Add(FVector(0.0f, 0.0f, -kBaseRadiusCm));
    Normals.Add(-FVector::UpVector);
    UVs.Add(FVector2D(0.5f, 0.5f));
    Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 CuffCenter = Vertices.Num();
    Vertices.Add(FVector(0.0f, 0.0f, kBaseRadiusCm));
    Normals.Add(FVector::UpVector);
    UVs.Add(FVector2D(0.5f, 0.5f));
    Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 CuffRing = Rings * (Sides + 1);
    for (int32 Side = 0; Side < Sides; ++Side)
    {
        Triangles.Append({ShoulderCenter, Side + 1, Side});
        Triangles.Append(
            {CuffCenter, CuffRing + Side, CuffRing + Side + 1});
    }
}

void BuildUnitHipThighBridgeMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // The production body needs only the wetsuit-covered transition from the
    // retained pelvis through the assembled knee. A circular swept tube reads
    // as a synthetic capsule in profile and as two round lobes from the rear.
    // This closed mesh keeps the proven overlap, but gives the cross-section a
    // stable anterior axis plus bounded quadriceps, hamstring, and adductor
    // envelopes. The denser topology keeps those changes smooth at review FOV.
    constexpr int32 Rings = 20;
    constexpr int32 Sides = 32;
    const auto SurfacePoint = [](float V, float Theta)
    {
        const float SafeV = FMath::Clamp(V, 0.0f, 1.0f);
        const float LongitudinalEnvelope = FMath::Pow(
            FMath::Max(FMath::Sin(PI * SafeV), 0.0f),
            0.72f);
        const float ProximalBlend = FMath::Exp(-FMath::Square(SafeV / 0.22f));
        const float DistalAlpha = FMath::Clamp((SafeV - 0.64f) / 0.36f, 0.0f, 1.0f);
        const float DistalBlend = DistalAlpha * DistalAlpha * (3.0f - 2.0f * DistalAlpha);
        const float BaseRadius =
            0.69f + 0.31f * LongitudinalEnvelope +
            0.055f * ProximalBlend - 0.065f * DistalBlend;

        const float CosTheta = FMath::Cos(Theta);
        const float SinTheta = FMath::Sin(Theta);
        const float FrontWeight = FMath::Square(FMath::Max(CosTheta, 0.0f));
        const float RearWeight = FMath::Square(FMath::Max(-CosTheta, 0.0f));
        const float Quadriceps =
            FMath::Exp(-FMath::Square((SafeV - 0.46f) / 0.27f));
        const float Hamstring =
            FMath::Exp(-FMath::Square((SafeV - 0.34f) / 0.30f));
        const float Adductor =
            FMath::Exp(-FMath::Square((SafeV - 0.28f) / 0.30f));

        // Keep the authored overlay just outside the assembled wetsuit body so
        // the shape reads as one garment volume instead of intersecting it.
        const float DepthRadius = BaseRadius * 0.94f;
        const float WidthRadius = BaseRadius * (0.98f + 0.035f * Adductor);
        const float DirectionalDepth =
            1.0f + 0.105f * Quadriceps * FrontWeight +
            0.060f * Hamstring * RearWeight;
        return FVector(
            DepthRadius * DirectionalDepth * CosTheta,
            WidthRadius * SinTheta,
            -1.0f + 2.0f * SafeV);
    };
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            const float SampleV = 0.0025f;
            const float SampleTheta = 0.0025f;
            const FVector Position = SurfacePoint(V, Theta);
            const FVector TangentV =
                SurfacePoint(FMath::Min(V + SampleV, 1.0f), Theta) -
                SurfacePoint(FMath::Max(V - SampleV, 0.0f), Theta);
            const FVector TangentTheta =
                SurfacePoint(V, Theta + SampleTheta) -
                SurfacePoint(V, Theta - SampleTheta);
            Vertices.Add(Position * kBaseRadiusCm);
            Normals.Add(FVector::CrossProduct(TangentTheta, TangentV).GetSafeNormal());
            UVs.Add(FVector2D(U, V));
            Tangents.Add(FProcMeshTangent(TangentTheta.GetSafeNormal(), false));
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

    const int32 BottomCenter = Vertices.Num();
    Vertices.Add(FVector(0.0f, 0.0f, -kBaseRadiusCm));
    Normals.Add(-FVector::UpVector);
    UVs.Add(FVector2D(0.5f, 0.5f));
    Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 TopCenter = Vertices.Num();
    Vertices.Add(FVector(0.0f, 0.0f, kBaseRadiusCm));
    Normals.Add(FVector::UpVector);
    UVs.Add(FVector2D(0.5f, 0.5f));
    Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 TopRing = Rings * (Sides + 1);
    for (int32 Side = 0; Side < Sides; ++Side)
    {
        Triangles.Append({BottomCenter, Side + 1, Side});
        Triangles.Append({TopCenter, TopRing + Side, TopRing + Side + 1});
    }
}

void BuildUnitSeatedPelvisMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // A seated wetsuit silhouette needs a full waist-to-glute-to-thigh bridge,
    // not the short narrow trunk used by V1. Keep broad finite cross-sections
    // at both caps, carry more depth below the hip joint, and bias the lower
    // volume rearward so the profile reads as a seated pelvis rather than a
    // pointed crotch wedge between a floating torso and two thighs.
    constexpr int32 Rings = 18;
    constexpr int32 Sides = 32;
    const auto SurfacePoint = [](float V, float U) -> FVector
    {
        const float Z = 1.0f - 2.0f * V;
        const float MidVolume = FMath::Pow(
            FMath::Max(FMath::Sin(PI * V), 0.0f), 0.58f);
        const float UpperFit = FMath::Max(Z, 0.0f);
        const float LowerFit = FMath::Max(-Z, 0.0f);
        const float Depth = 0.72f + 0.28f * MidVolume - 0.02f * UpperFit;
        const float Width = 0.72f + 0.28f * MidVolume;
        const float SeatBulge =
            FMath::Exp(-FMath::Square((Z + 0.35f) / 0.5f));
        const float PosteriorBias = 0.06f * MidVolume + 0.18f * SeatBulge;
        const float Theta = 2.0f * PI * U;
        const float CosTheta = FMath::Cos(Theta);
        const float SinTheta = FMath::Sin(Theta);
        const float SaddleLift = LowerFit *
            FMath::Square(1.0f - FMath::Abs(SinTheta)) * 0.28f;
        return FVector(
            Depth * CosTheta - PosteriorBias,
            Width * SinTheta,
            Z + SaddleLift);
    };
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const FVector Point = SurfacePoint(V, U);

            // Numeric surface normals: the former analytic ellipse normal
            // ignored the saddle and posterior displacements, so the shadow
            // terminator disagreed with the real surface and the PFD's cast
            // shadow cut across the sunward glute as a hard "gash" (player
            // report, 2026-08-30). Central differences follow whatever the
            // position formula does.
            constexpr float E = 0.004f;
            const FVector DPdU =
                SurfacePoint(V, U + E) - SurfacePoint(V, U - E);
            const FVector DPdV =
                SurfacePoint(FMath::Clamp(V + E, 0.0f, 1.0f), U) -
                SurfacePoint(FMath::Clamp(V - E, 0.0f, 1.0f), U);
            FVector Normal = FVector::CrossProduct(DPdV, DPdU).GetSafeNormal();
            if (Normal.IsNearlyZero())
            {
                Normal = FVector(Point.X, Point.Y, 0.0f).GetSafeNormal();
            }
            // Outward orientation: the surface wraps counter-clockwise, but
            // guard against degenerate rows at the caps.
            if (FVector::DotProduct(
                    Normal, FVector(Point.X, Point.Y, 0.0f)) < 0.0f)
            {
                Normal = -Normal;
            }
            const float Theta = 2.0f * PI * U;
            Vertices.Add(Point * kBaseRadiusCm);
            Normals.Add(Normal);
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

    const int32 TopCenter = Vertices.Num();
    Vertices.Add(FVector(0.0f, 0.0f, kBaseRadiusCm));
    Normals.Add(FVector::UpVector);
    UVs.Add(FVector2D(0.5f, 0.5f));
    Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 BottomCenter = Vertices.Num();
    Vertices.Add(FVector(
        -0.04f * kBaseRadiusCm,
        0.0f,
        -0.68f * kBaseRadiusCm));
    Normals.Add(FVector::DownVector);
    UVs.Add(FVector2D(0.5f, 0.5f));
    Tangents.Add(FProcMeshTangent(1.0f, 0.0f, 0.0f));
    const int32 BottomRing = Rings * (Sides + 1);
    for (int32 Side = 0; Side < Sides; ++Side)
    {
        Triangles.Append({TopCenter, Side, Side + 1});
        Triangles.Append({BottomCenter, BottomRing + Side + 1, BottomRing + Side});
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
            const float FacingSide = FMath::Abs(FMath::Sin(Theta));
            // 2026-08-06 named human review: the former high scallop read as
            // a cap, not a helmet. A whitewater dome covers occiput and ears:
            // drop the rear to the nape, keep the brow clear in front, and
            // pull the sides down over the ears.
            const float MaxPhi = FMath::Min(
                FMath::Lerp(1.90f, 1.38f, FacingFront) +
                    0.16f * FacingSide * (1.0f - FacingFront),
                2.05f);
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

} // pause the internal namespace: the blade builder is shared with the
  // guide pawn's first-person paddle (RaftSimPaddleBladeMesh.h).

namespace RaftSimPaddleBladeMesh
{
void BuildCommercialPaddleBladeMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    // A moulded whitewater-paddle blade in centimetres: local +Z runs from
    // the throat (z -5, where the shaft enters) to the tip (z 39), +Y is the
    // power face. The old eleven-point flat slab with 1.2 cm square edges
    // and per-cap constant normals read as a cut-out ("the blades look
    // blocky and unrealistic", 2026-09-02). This is a smooth spoon outline
    // over a lens cross-section — a 1.4 cm spine at the throat thinning to
    // 0.5 cm at the tip and 0.2 cm at the rim — with true surface normals.
    constexpr int32 RowCount = 18;
    constexpr int32 ColumnCount = 9;
    constexpr float ThroatZCm = -5.0f;
    constexpr float TipZCm = 39.0f;
    constexpr float RimHalfThicknessCm = 0.2f;

    const auto HalfWidthCm = [](float Along)
    {
        // Throat 3 cm half-width, shoulders 9.2 cm by 45 % of the length,
        // then a superellipse tip.
        constexpr float ThroatHalfWidth = 3.0f;
        constexpr float ShoulderHalfWidth = 9.2f;
        constexpr float TipStart = 0.6f;
        if (Along <= TipStart)
        {
            const float Rise = FMath::Clamp(Along / 0.45f, 0.0f, 1.0f);
            const float Smooth = Rise * Rise * (3.0f - 2.0f * Rise);
            return FMath::Lerp(ThroatHalfWidth, ShoulderHalfWidth, Smooth);
        }
        const float TipAlpha = FMath::Clamp((Along - TipStart) / (1.0f - TipStart), 0.0f, 1.0f);
        constexpr float Exponent = 2.4f;
        return ShoulderHalfWidth *
            FMath::Pow(FMath::Max(1.0f - FMath::Pow(TipAlpha, Exponent), 0.0f), 1.0f / Exponent);
    };
    const auto SpineHalfThicknessCm = [](float Along)
    {
        return FMath::Lerp(1.4f, 0.5f, Along);
    };
    // Surface point for a face: Along in [0,1] down the blade, Across in
    // [-1,1] rim to rim, Side +1 for the power face and -1 for the back.
    const auto SurfacePoint = [&](float Along, float Across, float Side)
    {
        const float Z = FMath::Lerp(ThroatZCm, TipZCm, Along);
        const float HalfWidth = HalfWidthCm(Along);
        const float Lens = 1.0f - Across * Across;
        const float HalfThickness =
            RimHalfThicknessCm + (SpineHalfThicknessCm(Along) - RimHalfThicknessCm) * Lens;
        return FVector(Across * HalfWidth, Side * HalfThickness, Z);
    };
    const auto SurfaceNormal = [&](float Along, float Across, float Side)
    {
        constexpr float Step = 0.01f;
        const FVector AlongTangent =
            SurfacePoint(FMath::Min(Along + Step, 1.0f), Across, Side) -
            SurfacePoint(FMath::Max(Along - Step, 0.0f), Across, Side);
        const FVector AcrossTangent =
            SurfacePoint(Along, FMath::Min(Across + Step, 1.0f), Side) -
            SurfacePoint(Along, FMath::Max(Across - Step, -1.0f), Side);
        FVector Normal = FVector::CrossProduct(AlongTangent, AcrossTangent).GetSafeNormal();
        if (Normal.IsNearlyZero())
        {
            Normal = FVector::RightVector * Side;
        }
        if (FVector::DotProduct(Normal, FVector::RightVector * Side) < 0.0f)
        {
            Normal = -Normal;
        }
        return Normal;
    };

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
        return Vertices.Num() - 1;
    };
    // UE front faces wind clockwise seen from the side the normal points
    // to, which in this left-handed frame means cross(B-A, C-A) must point
    // AGAINST the outward normal (the 2026-09-02 black-slab lesson, now
    // enforced numerically instead of by hand).
    const auto AddTriangle = [&](int32 A, int32 B, int32 C, const FVector& Outward)
    {
        const FVector Winding = FVector::CrossProduct(
            Vertices[B] - Vertices[A], Vertices[C] - Vertices[A]);
        if (FVector::DotProduct(Winding, Outward) > 0.0f)
        {
            Swap(B, C);
        }
        Triangles.Append({A, B, C});
    };

    int32 FaceStart[2] = {0, 0};
    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? 1.0f : -1.0f;
        FaceStart[SideIndex] = Vertices.Num();
        for (int32 Row = 0; Row < RowCount; ++Row)
        {
            const float Along = static_cast<float>(Row) / (RowCount - 1);
            for (int32 Column = 0; Column < ColumnCount; ++Column)
            {
                const float Across = -1.0f + 2.0f * Column / (ColumnCount - 1);
                AddVertex(
                    SurfacePoint(Along, Across, Side),
                    SurfaceNormal(Along, Across, Side),
                    FVector2D(0.5f + 0.5f * Across, Along));
            }
        }
        for (int32 Row = 0; Row + 1 < RowCount; ++Row)
        {
            for (int32 Column = 0; Column + 1 < ColumnCount; ++Column)
            {
                const int32 A = FaceStart[SideIndex] + Row * ColumnCount + Column;
                const int32 B = A + 1;
                const int32 C = A + ColumnCount;
                const int32 D = C + 1;
                const FVector Outward = Normals[A];
                AddTriangle(A, B, D, Outward);
                AddTriangle(A, D, C, Outward);
            }
        }
    }

    // Rim strip: the two faces meet along a 0.4 cm edge on both flanks.
    for (int32 Flank = 0; Flank < 2; ++Flank)
    {
        const int32 Column = Flank == 0 ? 0 : ColumnCount - 1;
        const float Across = Flank == 0 ? -1.0f : 1.0f;
        for (int32 Row = 0; Row + 1 < RowCount; ++Row)
        {
            const float Along = static_cast<float>(Row) / (RowCount - 1);
            const float NextAlong = static_cast<float>(Row + 1) / (RowCount - 1);
            const FVector FrontA = SurfacePoint(Along, Across, 1.0f);
            const FVector FrontB = SurfacePoint(NextAlong, Across, 1.0f);
            const FVector BackA = SurfacePoint(Along, Across, -1.0f);
            const FVector BackB = SurfacePoint(NextAlong, Across, -1.0f);
            const FVector Outward = FVector(Across, 0.0f, 0.0f);
            const int32 IA = AddVertex(FrontA, Outward, FVector2D(0.0f, Along));
            const int32 IB = AddVertex(FrontB, Outward, FVector2D(0.0f, NextAlong));
            const int32 IC = AddVertex(BackB, Outward, FVector2D(1.0f, NextAlong));
            const int32 ID = AddVertex(BackA, Outward, FVector2D(1.0f, Along));
            if (!FrontA.Equals(FrontB) || !BackA.Equals(BackB))
            {
                AddTriangle(IA, IB, IC, Outward);
                AddTriangle(IA, IC, ID, Outward);
            }
        }
    }
    // Throat end cap so the shaft junction is closed.
    {
        const FVector Outward(0.0f, 0.0f, -1.0f);
        const int32 Center = AddVertex(FVector(0.0f, 0.0f, ThroatZCm), Outward, FVector2D(0.5f, 0.0f));
        for (int32 Column = 0; Column + 1 < ColumnCount; ++Column)
        {
            AddTriangle(Center, FaceStart[0] + Column, FaceStart[0] + Column + 1, Outward);
            AddTriangle(Center, FaceStart[1] + Column, FaceStart[1] + Column + 1, Outward);
        }
    }
}
} // namespace RaftSimPaddleBladeMesh

namespace
{
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

void ApplyMirroredPaddleGrip(
    FRaftSimCrewAvatarPose& Pose,
    float SeatSide,
    float LowerHandAlpha = 0.43f)
{
    const FVector LowerHandCm = FMath::Lerp(
        Pose.PaddleTopCm,
        Pose.PaddleBottomCm,
        FMath::Clamp(LowerHandAlpha, 0.0f, 1.0f));

    // Paddlers face +X. On port (-Y), the left hand is the outboard/lower
    // shaft hand and the right hand owns the inboard T-grip. Starboard is the
    // anatomical mirror. Keeping this assignment side-aware prevents the
    // starboard arms and paddle from crossing through the raft.
    if (SeatSide < 0.0f)
    {
        Pose.LeftHandCm = LowerHandCm;
        Pose.RightHandCm = Pose.PaddleTopCm;
    }
    else
    {
        Pose.LeftHandCm = Pose.PaddleTopCm;
        Pose.RightHandCm = LowerHandCm;
    }
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
    // Head raised from 91 (2026-08-30): the PFD's shoulder foam tops out
    // near world Z 81 while the head's underside sat at 78, so helmet, vest,
    // and suit interpenetrated and no neck could ever show. Five centimetres
    // opens a real collar gap the neck ellipsoid fills.
    Pose.HeadCenterCm = FVector(6.0f, 0.0f, 96.0f);
    // Shoulders dropped from 76 (2026-09-02, then again the same day): the
    // CC0 wetsuit's shoulder crest rides the joint targets, and its
    // scalloped neckline kept flapping above the PFD's shoulder line
    // ("shoulders still covered with black material"). 71 plus the raised
    // vest shell finally puts the neoprene under the vest; the collar gap
    // beneath the raised head widens rather than shrinks.
    Pose.LeftShoulderCm = FVector(4.0f, -17.0f, 71.0f);
    Pose.RightShoulderCm = FVector(4.0f, 17.0f, 71.0f);
    Pose.LeftHandCm = FVector(28.0f, -25.0f, 55.0f);
    Pose.RightHandCm = FVector(42.0f, 12.0f, 42.0f);
    Pose.LeftHipCm = FVector(-4.0f, -10.0f, 40.0f);
    Pose.RightHipCm = FVector(-4.0f, 10.0f, 40.0f);
    // Seated legs drop INBOARD, not straight ahead (2026-08-31): the seat
    // origin rides the tube crest at raft |Y| 62, so the former side-blind
    // targets (feet 34 cm forward at lateral +/-15) landed at raft |Y|
    // 47-77 — the whole lower leg folded ON TOP of the tube ("the crew's
    // legs should be in the boat with their feet on the floor of the
    // boat"). A tube-sitting paddler's thighs cross the tube's inner
    // shoulder and the feet plant on the self-bailing floor toward the
    // centreline. Measured raft frame (seat log floor probe): tube top
    // ~27, interior cushion/floor tops ~21 in the foot zone; seat origin
    // ~raft 0. Knees hold just inside the tube at |Y|~35-57, feet reach
    // the floor at |Y|~22-40 with soles at the cushion surface.
    // The leg skin squashes between explicitly placed bone heads (the foot
    // bone is pinned at the pose target), so spans need not match the
    // source rig — but they DO have to clear the production boot: its cuff
    // stands ~12 cm tall, and the previous 10 cm knee-to-foot drop left the
    // boot swallowing the whole shin, reading as a foot sprouting mid-shin
    // ("the feet seem to be coming out of the shins"). Sit the fold the way
    // a paddler actually does on a low tube: knees drawn up, heels pulled
    // back under them, soles planted on the interior floor — a ~28 cm shin
    // drop that enters the boot cuff from clearly above it.
    const float InboardSign = -Side;
    Pose.LeftKneeCm = FVector(26.0f, InboardSign * 15.0f - 11.0f, 34.0f);
    Pose.RightKneeCm = FVector(26.0f, InboardSign * 15.0f + 11.0f, 34.0f);
    Pose.LeftFootCm = FVector(20.0f, InboardSign * 32.0f - 9.0f, 6.0f);
    Pose.RightFootCm = FVector(20.0f, InboardSign * 32.0f + 9.0f, 6.0f);
    // The T-grip belongs inboard of the tube and the blade belongs outboard
    // in the water. The previous signs were reversed, so both blades aimed at
    // the raft centre; perspective happened to hide the error on port while
    // making the starboard paddles visibly cross the boat.
    Pose.PaddleTopCm = FVector(25.0f, -25.0f * Side, 67.0f);
    Pose.PaddleBottomCm = FVector(65.0f, 42.0f * Side, -7.0f);
    ApplyMirroredPaddleGrip(Pose, Side);

    switch (Action)
    {
        case ERaftSimCrewAvatarAction::SeatedIdle:
        {
            // At rest the paddle comes OUT of the water: the shaft lies
            // across the tops of the thighs just behind the knees — forward
            // of the PFD belly so it never threads through the torso — with
            // the T-grip inboard and the blade hanging outboard above the
            // tube, hands loosely on the shaft ("when they aren't paddling
            // the paddles should be out of the water in a neutral position
            // with the shaft resting on the thigh", 2026-08-31). The base
            // catch-ready paddle below stays untouched for the strokes.
            Pose.PaddleTopCm = FVector(18.0f, -30.0f * Side, 36.0f);
            Pose.PaddleBottomCm = FVector(30.0f, 52.0f * Side, 40.0f);
            // Resting hands drape over the SHAFT, not the T-grip: an exact
            // T-grip anchor selects the crossbar-axis grip solve, and with
            // the shaft laid laterally the crossbar points fore-aft, so the
            // relaxed wrist wrenched 90 degrees around it ("the hands on
            // the t-grip look twisted"). Off the 2 cm T-grip window both
            // hands take the along-shaft grip: knuckles down the shaft,
            // palms resting on it from above.
            {
                const FVector RestUpperHandCm = FMath::Lerp(
                    Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.15f);
                const FVector RestLowerHandCm = FMath::Lerp(
                    Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.45f);
                if (Side < 0.0f)
                {
                    Pose.LeftHandCm = RestLowerHandCm;
                    Pose.RightHandCm = RestUpperHandCm;
                }
                else
                {
                    Pose.LeftHandCm = RestUpperHandCm;
                    Pose.RightHandCm = RestLowerHandCm;
                }
            }
            break;
        }
        case ERaftSimCrewAvatarAction::ForwardStroke:
        {
            const float Reach = 14.0f * Wave;
            const float PowerAlpha = 0.5f * (1.0f - Wave);
            Pose.TorsoRotation.Pitch = -8.0f - 7.0f * Wave;
            Pose.TorsoRotation.Yaw = Side * (4.0f + 3.0f * Wave);
            Pose.TorsoRotation.Roll = -Side * (2.0f + 1.5f * PowerAlpha);
            Pose.TorsoCenterCm.X += 5.0f * Wave;
            Pose.PaddleTopCm.X += Reach;
            // Blade travels WITH the top hand: forward at the catch, back
            // through the power phase. The former negated term swept the
            // blade forward through the water during power — a back-paddle
            // in mirror (2026-08-10 playtest: "their forward paddle looks
            // like a back paddle").
            Pose.PaddleBottomCm.X += 20.0f * Wave;
            Pose.PaddleBottomCm.Z += StrokeRecoveryLiftCm(NormalizedPhase);
            ApplyMirroredPaddleGrip(Pose, Side);
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
            Pose.PaddleBottomCm.X += 20.0f * BackWave;
            Pose.PaddleBottomCm.Z += StrokeRecoveryLiftCm(NormalizedPhase);
            ApplyMirroredPaddleGrip(Pose, Side);
            Pose.TorsoRotation.Pitch *= -0.7f;
            break;
        }
        case ERaftSimCrewAvatarAction::TurnLeft:
        case ERaftSimCrewAvatarAction::TurnRight:
        {
            const float Turn = Action == ERaftSimCrewAvatarAction::TurnLeft ? -1.0f : 1.0f;
            // A paddle-raft pivot uses opposing forward/back strokes. Both
            // blades remain outside their own tubes instead of every paddler
            // reaching across the boat toward the commanded turn direction.
            const float StrokeDirection = -Turn * Side;
            Pose.TorsoRotation.Yaw = Turn * (18.0f + 8.0f * Wave);
            Pose.PaddleTopCm.X += 12.0f * StrokeDirection * Wave;
            Pose.PaddleBottomCm.X += 18.0f * StrokeDirection * Wave;
            Pose.PaddleBottomCm.Z += StrokeRecoveryLiftCm(NormalizedPhase);
            ApplyMirroredPaddleGrip(Pose, Side, 0.42f);
            break;
        }
        case ERaftSimCrewAvatarAction::Brace:
            Pose.TorsoCenterCm.Z -= 15.0f;
            Pose.HeadCenterCm.Z -= 15.0f;
            Pose.TorsoRotation.Pitch = 18.0f;
            Pose.PaddleTopCm = FVector(38.0f, -24.0f * Side, 44.0f);
            Pose.PaddleBottomCm = FVector(38.0f, 58.0f * Side, 16.0f);
            ApplyMirroredPaddleGrip(Pose, Side, 0.55f);
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
            // The body still translates toward the commanded tube, but each
            // paddle remains outside its assigned seat. A shared Shift-based
            // paddle direction put the opposite-side blades inside the raft.
            const FVector InboardHand(24.0f, -Side * 18.0f, 58.0f);
            const FVector OutboardHand(40.0f, Side * 18.0f, 30.0f);
            if (Side < 0.0f)
            {
                Pose.LeftHandCm = OutboardHand;
                Pose.RightHandCm = InboardHand;
            }
            else
            {
                Pose.LeftHandCm = InboardHand;
                Pose.RightHandCm = OutboardHand;
            }
            Pose.PaddleTopCm = InboardHand;
            const FVector OutboardPaddleDirection =
                (OutboardHand - InboardHand).GetSafeNormal();
            Pose.PaddleBottomCm = OutboardHand + OutboardPaddleDirection * 73.0f;
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
        default:
            // Resting crew sit still. The former +/-1.5/2.0 cm stroke-cadence
            // bob ran ungated by any water state, telescoping the upper body
            // out of a fixed pelvis on flat water (2026-08-07 playtest).
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
float URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseStart()
{
    return 0.24f;
}

float URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseEnd()
{
    return 0.48f;
}

bool URaftSimCrewAvatarPoseLibrary::IsPaddleBladeInPowerPhase(
    float NormalizedPhase)
{
    const float Wrapped =
        FMath::Frac(1.0f + FMath::Frac(NormalizedPhase));
    return Wrapped >= GetPaddlePowerPhaseStart() &&
        Wrapped <= GetPaddlePowerPhaseEnd();
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
    UpdatePfdMaterialResponse(DeltaSeconds);
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
    // The gap-fill overlay set (torso/pelvis/thigh/sleeve shells) depends
    // on whether the CC0 body is READY, and readiness can flip after the
    // one-shot visibility pass at spawn. That race left shoulder sleeves
    // rendering over the finished body on some launches — anchored to the
    // procedural elbow, they burst out of the CC0 forearm mid-stroke
    // ("a strange black shape pops up out of the fore arm", 2026-09-02;
    // the empty-helmet neck race was the same class). Re-apply the pass
    // whenever readiness changes.
    if (bUsingProductionVisual)
    {
        const ARaftSimCC0CrewVisualActor* CC0Visual =
            Cast<ARaftSimCC0CrewVisualActor>(GetProductionVisualActor());
        const bool bBodyReadyNow = CC0Visual && CC0Visual->IsBodyReady();
        if (bBodyReadyNow != bLastAppliedCC0BodyReady)
        {
            bLastAppliedCC0BodyReady = bBodyReadyNow;
            SetProceduralVisualVisible(false);
        }
    }
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

bool ARaftSimCrewAvatarActor::ResolveProductionHeadFit(
    FVector& OutSolvedHeadWorldLocation,
    FVector& OutFaceForwardWorld,
    FVector& OutFaceUpWorld,
    float& OutHelmetScale) const
{
    if (const ARaftSimMetaHumanCrewVisualActor* MetaHumanVisual =
            Cast<ARaftSimMetaHumanCrewVisualActor>(GetProductionVisualActor()))
    {
        OutSolvedHeadWorldLocation = MetaHumanVisual->GetSolvedHeadWorldLocation();
        OutFaceForwardWorld = MetaHumanVisual->GetSolvedFaceForwardWorldVector();
        OutFaceUpWorld = MetaHumanVisual->GetSolvedFaceUpWorldVector();
        OutHelmetScale = MetaHumanVisual->GetRecommendedWhitewaterHelmetScale();
    }
    else if (const ARaftSimCC0CrewVisualActor* CC0Visual =
                 Cast<ARaftSimCC0CrewVisualActor>(GetProductionVisualActor());
             CC0Visual && CC0Visual->IsBodyReady())
    {
        OutSolvedHeadWorldLocation = CC0Visual->GetSolvedHeadWorldLocation();
        OutFaceForwardWorld = CC0Visual->GetSolvedFaceForwardWorldVector();
        OutFaceUpWorld = CC0Visual->GetSolvedFaceUpWorldVector();
        OutHelmetScale = CC0Visual->GetRecommendedWhitewaterHelmetScale();
    }
    else
    {
        return false;
    }
    return !OutSolvedHeadWorldLocation.ContainsNaN() &&
        !OutFaceForwardWorld.ContainsNaN() &&
        !OutFaceForwardWorld.IsNearlyZero() &&
        !OutFaceUpWorld.ContainsNaN() &&
        !OutFaceUpWorld.IsNearlyZero() &&
        FMath::IsFinite(OutHelmetScale) && OutHelmetScale > 0.0f;
}

float ARaftSimCrewAvatarActor::GetProductionHelmetHeadErrorCm() const
{
    if (!Helmet || !Root)
    {
        return TNumericLimits<float>::Max();
    }
    FVector SolvedHeadWorldLocation;
    FVector FaceForwardWorld;
    FVector FaceUpWorld;
    float HelmetScale = 0.0f;
    if (!ResolveProductionHeadFit(
            SolvedHeadWorldLocation,
            FaceForwardWorld,
            FaceUpWorld,
            HelmetScale))
    {
        return TNumericLimits<float>::Max();
    }
    const FVector SolvedHeadRelativeCm =
        Root->GetComponentTransform().InverseTransformPosition(
            SolvedHeadWorldLocation);
    const USceneComponent* FittedHelmet = HasProductionWhitewaterHelmet()
        ? static_cast<const USceneComponent*>(ProductionHelmet.Get())
        : static_cast<const USceneComponent*>(Helmet.Get());
    const FQuat HelmetRotation = FittedHelmet->GetRelativeRotation().Quaternion();
    const float LiftScale = HasProductionWhitewaterHelmet()
        ? FittedHelmet->GetRelativeScale3D().Z / kProductionHelmetReferenceFit
        : 1.0f;
    const FVector AssetShellOffset = HasProductionWhitewaterHelmet()
        ? FVector::ZeroVector
        : kProductionHelmetShellOffsetCm;
    const FVector FittedHeadCenterCm = FittedHelmet->GetRelativeLocation() -
        HelmetRotation.RotateVector(
            kProductionHelmetSkullCenterOffsetCm * LiftScale + AssetShellOffset);
    return FVector::Distance(FittedHeadCenterCm, SolvedHeadRelativeCm);
}

float ARaftSimCrewAvatarActor::GetProductionHelmetForwardAlignment() const
{
    if (!HasProductionWhitewaterHelmet())
    {
        return -1.0f;
    }
    FVector SolvedHeadWorldLocation;
    FVector FaceForwardWorld;
    FVector FaceUpWorld;
    float HelmetScale = 0.0f;
    if (!ResolveProductionHeadFit(
            SolvedHeadWorldLocation,
            FaceForwardWorld,
            FaceUpWorld,
            HelmetScale))
    {
        return -1.0f;
    }
    return FVector::DotProduct(
        ProductionHelmet->GetForwardVector().GetSafeNormal(),
        FaceForwardWorld.GetSafeNormal());
}

float ARaftSimCrewAvatarActor::GetProductionHelmetFitScale() const
{
    return HasProductionWhitewaterHelmet()
        ? ProductionHelmet->GetRelativeScale3D().X
        : 0.0f;
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

bool ARaftSimCrewAvatarActor::HasVisibleWaistHipSilhouette() const
{
    if (!bUsingProductionVisual || !Pelvis || !LeftThigh || !RightThigh ||
        !Pelvis->IsVisible() || !LeftThigh->IsVisible() || !RightThigh->IsVisible())
    {
        return false;
    }
    const FProcMeshSection* Section = Pelvis->GetProcMeshSection(0);
    const FProcMeshSection* LeftBridgeSection = LeftThigh->GetProcMeshSection(0);
    const FProcMeshSection* RightBridgeSection = RightThigh->GetProcMeshSection(0);
    const FVector ExtentCm = GetWaistHipExtentCm();
    const FVector ThighExtentCm = GetMinimumHipThighBridgeExtentCm();
    return Section && Section->ProcVertexBuffer.Num() >= 500 &&
        LeftBridgeSection && LeftBridgeSection->ProcVertexBuffer.Num() >= 650 &&
        RightBridgeSection && RightBridgeSection->ProcVertexBuffer.Num() >= 650 &&
        ExtentCm.X >= 14.0f && ExtentCm.Y >= 21.0f && ExtentCm.Z >= 13.8f &&
        ThighExtentCm.X >= 6.2f && ThighExtentCm.Y >= 6.2f &&
        ThighExtentCm.Z >= 9.5f && IsWaistHipMaterialOpaque() &&
        GetMaximumHipThighBridgeCoverageErrorCm() <= 0.25f;
}

FVector ARaftSimCrewAvatarActor::GetWaistHipExtentCm() const
{
    return Pelvis
        ? Pelvis->GetRelativeScale3D().GetAbs() * kBaseRadiusCm
        : FVector::ZeroVector;
}

float ARaftSimCrewAvatarActor::GetWaistHipCenterErrorCm() const
{
    if (!Pelvis)
    {
        return TNumericLimits<float>::Max();
    }
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            CurrentAction, AnimationPhase, SeatSide);
    const FVector SolvedHipCenter = (Pose.LeftHipCm + Pose.RightHipCm) * 0.5f;
    return FVector::Distance(Pelvis->GetRelativeLocation(), SolvedHipCenter);
}

bool ARaftSimCrewAvatarActor::IsWaistHipMaterialOpaque() const
{
    const auto HasOpaqueMaterial = [](const UProceduralMeshComponent* Component)
    {
        const UMaterialInterface* Material = Component ? Component->GetMaterial(0) : nullptr;
        return Material && Material->GetBlendMode() == BLEND_Opaque;
    };
    return HasOpaqueMaterial(Pelvis) &&
        HasOpaqueMaterial(LeftThigh) && HasOpaqueMaterial(RightThigh);
}

FVector ARaftSimCrewAvatarActor::GetMinimumHipThighBridgeExtentCm() const
{
    if (!LeftThigh || !RightThigh)
    {
        return FVector::ZeroVector;
    }
    const FVector LeftExtentCm =
        LeftThigh->GetRelativeScale3D().GetAbs() * kBaseRadiusCm;
    const FVector RightExtentCm =
        RightThigh->GetRelativeScale3D().GetAbs() * kBaseRadiusCm;
    return FVector(
        FMath::Min(LeftExtentCm.X, RightExtentCm.X),
        FMath::Min(LeftExtentCm.Y, RightExtentCm.Y),
        FMath::Min(LeftExtentCm.Z, RightExtentCm.Z));
}

int32 ARaftSimCrewAvatarActor::GetMinimumThighMeshVertexCount() const
{
    if (!LeftThigh || !RightThigh)
    {
        return 0;
    }
    const FProcMeshSection* LeftSection = LeftThigh->GetProcMeshSection(0);
    const FProcMeshSection* RightSection = RightThigh->GetProcMeshSection(0);
    return LeftSection && RightSection
        ? FMath::Min(
            LeftSection->ProcVertexBuffer.Num(),
            RightSection->ProcVertexBuffer.Num())
        : 0;
}

float ARaftSimCrewAvatarActor::GetMinimumThighForwardAlignment() const
{
    if (!LeftThigh || !RightThigh)
    {
        return -1.0f;
    }
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            CurrentAction, AnimationPhase, SeatSide);
    const FVector TorsoForward =
        Pose.TorsoRotation.RotateVector(FVector::ForwardVector).GetSafeNormal();
    const auto ForwardAlignment = [&](const UProceduralMeshComponent* Thigh,
                                      const FVector& HipCm,
                                      const FVector& KneeCm)
    {
        const FVector ThighAxis = (KneeCm - HipCm).GetSafeNormal();
        const FVector ExpectedForward =
            FVector::VectorPlaneProject(TorsoForward, ThighAxis).GetSafeNormal();
        const FVector MeshForward = Thigh->GetRelativeRotation()
            .RotateVector(FVector::ForwardVector)
            .GetSafeNormal();
        return ExpectedForward.IsNearlyZero()
            ? -1.0f
            : FVector::DotProduct(MeshForward, ExpectedForward);
    };
    return FMath::Min(
        ForwardAlignment(LeftThigh, Pose.LeftHipCm, Pose.LeftKneeCm),
        ForwardAlignment(RightThigh, Pose.RightHipCm, Pose.RightKneeCm));
}

float ARaftSimCrewAvatarActor::GetMaximumHipThighBridgeCoverageErrorCm() const
{
    if (!LeftThigh || !RightThigh)
    {
        return TNumericLimits<float>::Max();
    }
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            CurrentAction, AnimationPhase, SeatSide);
    const auto DistanceToBridgeCentreline = [](
        const UProceduralMeshComponent* Thigh,
        const FVector& HipCm)
    {
        const FVector Axis = Thigh->GetRelativeRotation().RotateVector(FVector::UpVector);
        const float HalfLengthCm =
            Thigh->GetRelativeScale3D().GetAbs().Z * kBaseRadiusCm;
        const FVector StartCm = Thigh->GetRelativeLocation() - Axis * HalfLengthCm;
        const FVector EndCm = Thigh->GetRelativeLocation() + Axis * HalfLengthCm;
        const FVector Segment = EndCm - StartCm;
        const float SegmentLengthSquared = Segment.SizeSquared();
        const float Alpha = SegmentLengthSquared > UE_SMALL_NUMBER
            ? FMath::Clamp(
                FVector::DotProduct(HipCm - StartCm, Segment) / SegmentLengthSquared,
                0.0f,
                1.0f)
            : 0.0f;
        return FVector::Distance(StartCm + Segment * Alpha, HipCm);
    };
    return FMath::Max(
        DistanceToBridgeCentreline(LeftThigh, Pose.LeftHipCm),
        DistanceToBridgeCentreline(RightThigh, Pose.RightHipCm));
}

bool ARaftSimCrewAvatarActor::HasContinuousThighKneeSilhouette() const
{
    if (!bUsingProductionVisual || !LeftThigh || !RightThigh ||
        !LeftThigh->IsVisible() || !RightThigh->IsVisible())
    {
        return false;
    }
    const FProcMeshSection* LeftBridgeSection = LeftThigh->GetProcMeshSection(0);
    const FProcMeshSection* RightBridgeSection = RightThigh->GetProcMeshSection(0);
    const FVector ThighExtentCm = GetMinimumHipThighBridgeExtentCm();
    return LeftBridgeSection && LeftBridgeSection->ProcVertexBuffer.Num() >= 650 &&
        RightBridgeSection && RightBridgeSection->ProcVertexBuffer.Num() >= 650 &&
        ThighExtentCm.X >= 7.2f && ThighExtentCm.Y >= 7.2f &&
        ThighExtentCm.Z >= 15.5f && IsWaistHipMaterialOpaque() &&
        GetMinimumThighForwardAlignment() >= 0.98f &&
        GetMaximumThighKneeBridgeCoverageErrorCm() <= 0.25f;
}

float ARaftSimCrewAvatarActor::GetMaximumThighKneeBridgeCoverageErrorCm() const
{
    if (!LeftThigh || !RightThigh)
    {
        return TNumericLimits<float>::Max();
    }
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            CurrentAction, AnimationPhase, SeatSide);
    const auto DistanceToBridgeCentreline = [](
        const UProceduralMeshComponent* Thigh,
        const FVector& KneeCm)
    {
        const FVector Axis = Thigh->GetRelativeRotation().RotateVector(FVector::UpVector);
        const float HalfLengthCm =
            Thigh->GetRelativeScale3D().GetAbs().Z * kBaseRadiusCm;
        const FVector StartCm = Thigh->GetRelativeLocation() - Axis * HalfLengthCm;
        const FVector EndCm = Thigh->GetRelativeLocation() + Axis * HalfLengthCm;
        const FVector Segment = EndCm - StartCm;
        const float SegmentLengthSquared = Segment.SizeSquared();
        const float Alpha = SegmentLengthSquared > UE_SMALL_NUMBER
            ? FMath::Clamp(
                FVector::DotProduct(KneeCm - StartCm, Segment) / SegmentLengthSquared,
                0.0f,
                1.0f)
            : 0.0f;
        return FVector::Distance(StartCm + Segment * Alpha, KneeCm);
    };
    return FMath::Max(
        DistanceToBridgeCentreline(LeftThigh, Pose.LeftKneeCm),
        DistanceToBridgeCentreline(RightThigh, Pose.RightKneeCm));
}

FVector ARaftSimCrewAvatarActor::GetMinimumShoulderSleeveExtentCm() const
{
    if (!LeftShoulderSleeve || !RightShoulderSleeve)
    {
        return FVector::ZeroVector;
    }
    const FVector LeftExtentCm =
        LeftShoulderSleeve->GetRelativeScale3D().GetAbs() * kBaseRadiusCm;
    const FVector RightExtentCm =
        RightShoulderSleeve->GetRelativeScale3D().GetAbs() * kBaseRadiusCm;
    return FVector(
        FMath::Min(LeftExtentCm.X, RightExtentCm.X),
        FMath::Min(LeftExtentCm.Y, RightExtentCm.Y),
        FMath::Min(LeftExtentCm.Z, RightExtentCm.Z));
}

int32 ARaftSimCrewAvatarActor::GetMinimumShoulderSleeveVertexCount() const
{
    if (!LeftShoulderSleeve || !RightShoulderSleeve)
    {
        return 0;
    }
    const FProcMeshSection* LeftSection =
        LeftShoulderSleeve->GetProcMeshSection(0);
    const FProcMeshSection* RightSection =
        RightShoulderSleeve->GetProcMeshSection(0);
    if (!LeftSection || !RightSection)
    {
        return 0;
    }
    return FMath::Min(
        LeftSection->ProcVertexBuffer.Num(),
        RightSection->ProcVertexBuffer.Num());
}

float ARaftSimCrewAvatarActor::GetMaximumShoulderSleeveAnchorErrorCm() const
{
    if (!LeftShoulderSleeve || !RightShoulderSleeve)
    {
        return TNumericLimits<float>::Max();
    }
    const FRaftSimCrewAvatarPose Pose =
        URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            CurrentAction, AnimationPhase, SeatSide);
    const auto ProximalEndpoint = [](const UProceduralMeshComponent* Sleeve)
    {
        const FVector Axis = Sleeve->GetRelativeRotation().RotateVector(FVector::UpVector);
        const float HalfLengthCm =
            Sleeve->GetRelativeScale3D().GetAbs().Z * kBaseRadiusCm;
        return Sleeve->GetRelativeLocation() - Axis * HalfLengthCm;
    };
    return FMath::Max(
        FVector::Distance(
            ProximalEndpoint(LeftShoulderSleeve), Pose.LeftShoulderCm),
        FVector::Distance(
            ProximalEndpoint(RightShoulderSleeve), Pose.RightShoulderCm));
}

bool ARaftSimCrewAvatarActor::HasVisibleShoulderSilhouette() const
{
    const FVector ExtentCm = GetMinimumShoulderSleeveExtentCm();
    return bUsingProductionVisual && LeftShoulderSleeve && RightShoulderSleeve &&
        LeftShoulderSleeve->IsVisible() && RightShoulderSleeve->IsVisible() &&
        GetMinimumShoulderSleeveVertexCount() >= 1000 &&
        HasLiveSplashJacketMaterialResponse() &&
        ExtentCm.X >= 4.7f && ExtentCm.Y >= 4.7f && ExtentCm.Z >= 5.6f &&
        ExtentCm.Z > ExtentCm.X &&
        GetMaximumShoulderSleeveAnchorErrorCm() <= 0.25f;
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

float ARaftSimCrewAvatarActor::GetSeatedPelvisBottomLocalZCm() const
{
    // Every seated pose keeps the solved hip centre at local Z = 40
    // (URaftSimCrewAvatarPoseLibrary::EvaluatePose base skeleton); the
    // pelvis ellipsoid spans kProductionSeatedPelvisReferenceExtentCm.Z
    // scaled by this identity's stature below that centre.
    constexpr float SeatedHipCenterLocalZCm = 40.0f;
    return SeatedHipCenterLocalZCm -
        kProductionSeatedPelvisReferenceExtentCm.Z * GetBodyProportionScale().Z;
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

bool ARaftSimCrewAvatarActor::HasLivePfdMaterialResponse() const
{
    return PfdShellMaterialInstance != nullptr;
}

bool ARaftSimCrewAvatarActor::HasProductionRiverBoots() const
{
    return ProductionLeftBoot && ProductionLeftBoot->GetStaticMesh() != nullptr &&
        ProductionRightBoot && ProductionRightBoot->GetStaticMesh() != nullptr;
}

bool ARaftSimCrewAvatarActor::HasFittedUprightProductionRiverBoots() const
{
    const auto IsFittedAndSoleDown = [](const UStaticMeshComponent* Boot)
    {
        if (!Boot || !Boot->GetStaticMesh())
        {
            return false;
        }
        const FBox SourceBounds = Boot->GetStaticMesh()->GetBoundingBox();
        const FVector Scale = Boot->GetRelativeScale3D();
        const FVector LocalUp =
            Boot->GetRelativeRotation().RotateVector(FVector::UpVector);
        return SourceBounds.Min.Z < 0.0f && SourceBounds.Max.Z > 0.0f &&
            FVector::DotProduct(LocalUp, FVector::UpVector) >= 0.999f &&
            Scale.X > 0.0f && Scale.Y > 0.0f && Scale.Z > 0.0f &&
            // Bounds track kProductionRiverBootPresentationScale plus the
            // per-avatar profile headroom (ratio ~1.06 carried from the
            // original 0.68/0.72 pair): taller 0.85 cuff for the anatomical
            // seated fold, wider 0.98/1.04 body so the bootie breaks the
            // shin's cylinder silhouette (both 2026-09-02).
            Scale.X <= 1.06f && Scale.Y <= 1.12f && Scale.Z <= 1.08f;
    };
    return IsFittedAndSoleDown(ProductionLeftBoot) &&
        IsFittedAndSoleDown(ProductionRightBoot);
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
    if (NewAction == ERaftSimCrewAvatarAction::Swimming)
    {
        PfdPresentationWetness = FMath::Max(PfdPresentationWetness, 0.84f);
    }
    else if (NewAction == ERaftSimCrewAvatarAction::Reentry)
    {
        PfdPresentationWetness = FMath::Max(PfdPresentationWetness, 0.70f);
    }
    else if (NewAction == ERaftSimCrewAvatarAction::Falling)
    {
        PfdPresentationWetness = FMath::Max(PfdPresentationWetness, 0.52f);
    }
    ApplyPfdMaterialWetness();
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
    PfdShellMaterialInstance = PfdMaterial
        ? UMaterialInstanceDynamic::Create(PfdMaterial, this)
        : nullptr;
    UMaterialInterface* VisiblePfdMaterial = PfdShellMaterialInstance
        ? static_cast<UMaterialInterface*>(PfdShellMaterialInstance.Get())
        : PfdMaterial;
    if (Pfd && PfdMaterial)
    {
        Pfd->SetMaterial(0, VisiblePfdMaterial);
    }
    if (ProductionPfd && PfdMaterial)
    {
        ProductionPfd->SetMaterial(0, VisiblePfdMaterial);
    }
    UMaterialInterface* SplashJacketMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SplashJacket."
             "M_RaftSim_SplashJacket"));
    SplashJacketMaterialInstance = SplashJacketMaterial
        ? UMaterialInstanceDynamic::Create(SplashJacketMaterial, this)
        : nullptr;
    UMaterialInterface* VisibleSplashJacket = SplashJacketMaterialInstance
        ? static_cast<UMaterialInterface*>(SplashJacketMaterialInstance.Get())
        : SplashJacketMaterial;
    for (UProceduralMeshComponent* JacketPart : {
             Torso,
             LeftShoulderSleeve,
             RightShoulderSleeve,
             LeftUpperArm,
             LeftLowerArm,
             RightUpperArm,
             RightLowerArm})
    {
        if (JacketPart && VisibleSplashJacket)
        {
            JacketPart->SetMaterial(0, VisibleSplashJacket);
        }
    }
    ApplyPfdMaterialWetness();
    // 2026-08-06 named human review: hair-dark shells read as haircuts, not
    // equipment. Crew helmets cycle through safety colours only; the dark
    // base material is reserved for the guide variant.
    static const TCHAR* HelmetPaths[] = {
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_Red.M_RaftSim_Helmet_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_White.M_RaftSim_Helmet_White"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_Yellow.M_RaftSim_Helmet_Yellow"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet_White.M_RaftSim_Helmet_White")};
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

void ARaftSimCrewAvatarActor::UpdatePfdMaterialResponse(float DeltaSeconds)
{
    float TargetWetness = 0.0f;
    if (const ARaftSimRaftActor* OwningRaft = Cast<ARaftSimRaftActor>(GetOwner()))
    {
        // Seated crew inherit only bounded splash/dampness from the solver-owned
        // raft signal; a PFD above the tube must not look fully submerged merely
        // because the raft is floating in wet cells.
        TargetWetness = FMath::Clamp(
            OwningRaft->GetSurfaceWetness() * 0.46f,
            0.0f,
            0.52f);
    }
    if (CurrentAction == ERaftSimCrewAvatarAction::Swimming)
    {
        TargetWetness = FMath::Max(TargetWetness, 0.84f);
    }
    else if (CurrentAction == ERaftSimCrewAvatarAction::Reentry)
    {
        TargetWetness = FMath::Max(TargetWetness, 0.70f);
    }
    else if (CurrentAction == ERaftSimCrewAvatarAction::Falling)
    {
        TargetWetness = FMath::Max(TargetWetness, 0.52f);
    }

    const float InterpSpeed = TargetWetness > PfdPresentationWetness
        ? 5.5f
        : 0.10f;
    PfdPresentationWetness = FMath::FInterpTo(
        PfdPresentationWetness,
        TargetWetness,
        FMath::Clamp(DeltaSeconds, 0.0f, 0.25f),
        InterpSpeed);
    ApplyPfdMaterialWetness();
}

void ARaftSimCrewAvatarActor::ApplyPfdMaterialWetness()
{
    const float BoundedWetness =
        FMath::Clamp(PfdPresentationWetness, 0.0f, 0.84f);
    if (PfdShellMaterialInstance)
    {
        PfdShellMaterialInstance->SetScalarParameterValue(
            TEXT("Wetness"),
            BoundedWetness);
    }
    if (SplashJacketMaterialInstance)
    {
        SplashJacketMaterialInstance->SetScalarParameterValue(
            TEXT("Wetness"),
            BoundedWetness);
    }
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
    // Adapter-owned visibility can only be resolved after configuration. In
    // particular, the direct CC0 fallback path does not report a complete body
    // until its packaged skeletal mesh has loaded and accepted the pose buffer.
    SetProceduralVisualVisible(false);
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

bool ARaftSimCrewAvatarActor::ActivateCC0FallbackForValidation()
{
    if (!ProductionVisual)
    {
        return false;
    }
    bUsingProductionVisual = false;
    ProductionVisual->SetChildActorClass(nullptr);
    if (!TryActivateCC0FallbackVisual())
    {
        ProductionVisual->SetVisibility(false, true);
        SetProceduralVisualVisible(true);
        return false;
    }
    DispatchProductionPose();
    AlignProductionHeadgearToSolvedHead();
    return HasExclusiveCC0BodyOwnership();
}

bool ARaftSimCrewAvatarActor::HasExclusiveCC0BodyOwnership() const
{
    const ARaftSimCC0CrewVisualActor* CC0Visual =
        Cast<ARaftSimCC0CrewVisualActor>(GetProductionVisualActor());
    if (!bUsingProductionVisual || !CC0Visual || !CC0Visual->IsBodyReady())
    {
        UE_LOG(LogTemp, Display,
            TEXT("%s: CC0 ownership false (production=%d cc0=%d ready=%d)"),
            *GetName(), bUsingProductionVisual ? 1 : 0, CC0Visual != nullptr,
            CC0Visual && CC0Visual->IsBodyReady());
        return false;
    }
    // Neck is deliberately NOT in this list: the CC0 wetsuit renders no
    // visible skin between the PFD collar and the helmet's chin line, so
    // the skin neck band is production dressing (2026-08-30 collar-gap
    // design), not redundant anatomy — hiding it read as headless crew
    // ("there should be a skin tone head in the helmet", 2026-09-02).
    const UProceduralMeshComponent* RedundantBodyOverlays[] = {
        Pelvis,
        Torso,
        LeftThigh,
        RightThigh,
        LeftShoulderSleeve,
        RightShoulderSleeve};
    for (const UProceduralMeshComponent* Overlay : RedundantBodyOverlays)
    {
        if (!Overlay || Overlay->IsVisible())
        {
            UE_LOG(LogTemp, Display,
                TEXT("%s: CC0 ownership false (overlay %s visible)"),
                *GetName(), Overlay ? *Overlay->GetName() : TEXT("<null>"));
            return false;
        }
    }
    // The first-person guide deliberately hides its own helmet (and CC0
    // head) so the camera can sit in the eye socket; that presentation
    // choice still counts as exclusive ownership of a complete wardrobe.
    const bool bHelmetPresented =
        ProductionHelmet->IsVisible() || bFirstPersonHeadHidden;
    const bool bGearComplete =
        HasProductionWhitewaterPfd() && ProductionPfd->IsVisible() &&
        HasProductionWhitewaterHelmet() && bHelmetPresented &&
        HasProductionRiverBoots() && ProductionLeftBoot->IsVisible() &&
        ProductionRightBoot->IsVisible();
    if (!bGearComplete)
    {
        UE_LOG(LogTemp, Display,
            TEXT("%s: CC0 ownership false (pfd=%d/%d helmet=%d/%d/fp%d "
                 "boots=%d/%d,%d)"),
            *GetName(),
            HasProductionWhitewaterPfd() ? 1 : 0,
            ProductionPfd && ProductionPfd->IsVisible(),
            HasProductionWhitewaterHelmet() ? 1 : 0,
            ProductionHelmet && ProductionHelmet->IsVisible(),
            bFirstPersonHeadHidden ? 1 : 0,
            HasProductionRiverBoots() ? 1 : 0,
            ProductionLeftBoot && ProductionLeftBoot->IsVisible(),
            ProductionRightBoot && ProductionRightBoot->IsVisible());
    }
    return bGearComplete;
}

void ARaftSimCrewAvatarActor::SetProceduralVisualVisible(bool bVisible)
{
    // The neck gap-fill used to be repainted with the wetsuit material in the
    // production path, which made vest, suit, and helmet read as one unbroken
    // neoprene mass. It keeps its skin material now (2026-08-30): the band it
    // renders sits between the PFD collar and the helmet's chin line, exactly
    // where a rafter's bare neck shows, and the wetsuit torso tip still
    // supplies a short neoprene collar beneath it.
    const bool bHasProductionHelmet = HasProductionWhitewaterHelmet();
    const bool bHasProductionPfd = HasProductionWhitewaterPfd();
    const bool bHasProductionBoots = HasProductionRiverBoots();
    const ARaftSimCC0CrewVisualActor* CC0Visual =
        Cast<ARaftSimCC0CrewVisualActor>(GetProductionVisualActor());
    const bool bCompleteCC0Body =
        !bVisible && CC0Visual && CC0Visual->IsBodyReady();
    for (UProceduralMeshComponent* Part : BodyParts)
    {
        if (Part)
        {
            // The MetaHuman adapter still needs bounded pose-matched gap-fill
            // overlays around its cropped assembled body. The packaged CC0
            // adapter supplies a complete rigged body, so drawing those same
            // torso, pelvis, thigh, shoulder, and neck shells over it creates
            // duplicated anatomy. In that path retain only safety gear and
            // the paddle; the CC0 mesh owns the visible body continuously.
            const bool bSafetyGearOrPaddleOverlay =
                Part == Pfd || Part == PfdRearWebbing || Part == PfdBelt ||
                Part == PfdBuckle || Part == Helmet ||
                Part == HelmetRim || Part == HelmetRetention ||
                Part == LeftBoot || Part == RightBoot ||
                Part == PaddleShaft || Part == PaddleBlade || Part == PaddleGrip ||
                // The skin neck band is deliberate production dressing (it
                // fills the gap between the PFD collar and the helmet's chin
                // line, 2026-08-30) but sat in the CC0-not-ready gap-fill
                // list, so its visibility depended on load timing — when the
                // body readied first, every helmet read as empty ("there
                // should be a skin tone head in the helmet", 2026-09-02).
                Part == Neck;
            const bool bBodyGapOverlay = !bCompleteCC0Body &&
                (Part == Pelvis || Part == Torso ||
                 Part == LeftThigh || Part == RightThigh ||
                 Part == LeftShoulderSleeve || Part == RightShoulderSleeve ||
                 Part == Neck);
            const bool bProductionOverlay =
                bSafetyGearOrPaddleOverlay || bBodyGapOverlay;
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
    if (ARaftSimCC0CrewVisualActor* CC0Visual =
            Cast<ARaftSimCC0CrewVisualActor>(VisualActor))
    {
        CC0Visual->SetHeadHiddenForFirstPerson(bFirstPersonHeadHidden);
    }
}

FVector ARaftSimCrewAvatarActor::GetPoseHeadWorldLocationCm() const
{
    return Head ? Head->GetComponentLocation() : GetActorLocation();
}

void ARaftSimCrewAvatarActor::SetFirstPersonHeadHidden(bool bShouldHide)
{
    if (bFirstPersonHeadHidden == bShouldHide)
    {
        return;
    }
    bFirstPersonHeadHidden = bShouldHide;
    const bool bVisible = !bShouldHide;
    if (!bUsingProductionVisual)
    {
        // Procedural fallback: the head and helmet trio are ordinary parts.
        // (Production machines hide these through SetProceduralVisualVisible;
        // re-showing them here would stack a second head over the CC0 body.)
        if (Head) Head->SetVisibility(bVisible);
        if (Helmet) Helmet->SetVisibility(bVisible);
        if (HelmetRim) HelmetRim->SetVisibility(bVisible);
        if (HelmetRetention) HelmetRetention->SetVisibility(bVisible);
    }
    // The first-person camera must not render its own skull, but the sun
    // still should: the CC0 head bone is zero-scaled for the view, which
    // also removed it from the shadow pass, so the guide's shadow on the
    // water was headless ("the guide doesn't cast a full shadow, head is
    // missing", player screenshot 2026-08-30). The procedural head and
    // helmet shells stay posed every frame even while replaced by the
    // production layers, so while the first-person hide is active they
    // cast hidden-primitive shadows as stand-ins; the toggle is symmetric
    // so leaving first person never double-shadows the production helmet.
    for (UProceduralMeshComponent* ShadowProxy :
         {Head, Helmet, HelmetRim, HelmetRetention})
    {
        if (ShadowProxy)
        {
            ShadowProxy->SetCastHiddenShadow(bShouldHide);
        }
    }
    if (ProductionHelmet)
    {
        ProductionHelmet->SetVisibility(bVisible && HasProductionWhitewaterHelmet());
        // Same rule as the procedural shells: invisible to the wearer's
        // camera, present in the sun's.
        ProductionHelmet->SetCastHiddenShadow(bShouldHide);
    }
    if (ARaftSimCC0CrewVisualActor* CC0Visual =
            Cast<ARaftSimCC0CrewVisualActor>(GetProductionVisualActor()))
    {
        CC0Visual->SetHeadHiddenForFirstPerson(bShouldHide);
    }
}

void ARaftSimCrewAvatarActor::SetFirstPersonBodyHidden(bool bShouldHide)
{
    if (bFirstPersonBodyHidden == bShouldHide)
    {
        return;
    }
    bFirstPersonBodyHidden = bShouldHide;
    // Actor-level hiding leaves the layered per-component visibility state
    // (procedural parts vs production replacement layers) untouched, so
    // ending the glance restores exactly the pre-glance arrangement.
    SetActorHiddenInGame(bShouldHide);
    if (AActor* ProductionVisualActor = GetProductionVisualActor())
    {
        ProductionVisualActor->SetActorHiddenInGame(bShouldHide);
    }
}

void ARaftSimCrewAvatarActor::AlignProductionHeadgearToSolvedHead()
{
    if (!bUsingProductionVisual || !Root || !Head ||
        !Helmet || !HelmetRim || !HelmetRetention)
    {
        return;
    }
    FVector SolvedHeadWorldLocation;
    FVector FaceForwardWorld;
    FVector FaceUpWorld;
    float RecommendedHelmetScale = 0.0f;
    if (!ResolveProductionHeadFit(
            SolvedHeadWorldLocation,
            FaceForwardWorld,
            FaceUpWorld,
            RecommendedHelmetScale))
    {
        return;
    }
    const FVector SolvedHeadRelativeCm =
        Root->GetComponentTransform().InverseTransformPosition(
            SolvedHeadWorldLocation);
    const FVector PoseHeadRelativeCm = Head->GetRelativeLocation();
    if (SolvedHeadRelativeCm.ContainsNaN() || PoseHeadRelativeCm.ContainsNaN())
    {
        return;
    }
    // ApplyPose owns the production PPE silhouette and resets it every frame;
    // each complete production adapter then publishes its rendered face frame.
    // Position, orient, and size the asymmetric shell from that transform. A
    // torso-only rotation made the brow/rear profile look reversed whenever
    // the driven head and torso bases diverged, while one shared scale visibly
    // overfit the narrower identities.
    const FVector HeadSolveDeltaCm = SolvedHeadRelativeCm - PoseHeadRelativeCm;
    Helmet->SetRelativeLocation(
        Helmet->GetRelativeLocation() + HeadSolveDeltaCm);
    HelmetRim->SetRelativeLocation(
        HelmetRim->GetRelativeLocation() + HeadSolveDeltaCm);
    HelmetRetention->SetRelativeLocation(
        HelmetRetention->GetRelativeLocation() + HeadSolveDeltaCm);
    if (HasProductionWhitewaterHelmet())
    {
        const FTransform RootTransform = Root->GetComponentTransform();
        const FVector FaceForward = RootTransform.InverseTransformVectorNoScale(
            FaceForwardWorld).GetSafeNormal();
        const FVector FaceUp = RootTransform.InverseTransformVectorNoScale(
            FaceUpWorld).GetSafeNormal();
        if (!FaceForward.IsNearlyZero() && !FaceUp.IsNearlyZero())
        {
            const FQuat FittedRotation = FRotationMatrix::MakeFromXZ(
                FaceForward, FaceUp).ToQuat();
            const float FittedScale = RecommendedHelmetScale;
            const float LiftScale =
                FittedScale / kProductionHelmetReferenceFit;
            const FVector FittedLocation = SolvedHeadRelativeCm +
                FittedRotation.RotateVector(
                    kProductionHelmetSkullCenterOffsetCm * LiftScale);
            ProductionHelmet->SetRelativeLocationAndRotation(
                FittedLocation, FittedRotation);
            ProductionHelmet->SetRelativeScale3D(FVector(FittedScale));
        }
    }
    if (HasProductionWhitewaterPfd())
    {
        // ApplyPose seats the vest on the host waist-pivot frame; a rendered
        // CC0 spine leans and curves away from that abstraction, floating the
        // rear panels off the back and sinking the lower front panel into the
        // chest (2026-08-07 playtest). Re-seat it on the rendered spine in
        // the same pass that re-seats the helmet.
        if (const ARaftSimCC0CrewVisualActor* CC0Visual =
                Cast<ARaftSimCC0CrewVisualActor>(GetProductionVisualActor()))
        {
            FTransform ChestWorld;
            if (CC0Visual->GetSolvedChestWorldTransform(ChestWorld))
            {
                UE_LOG(LogTemp, VeryVerbose,
                    TEXT("[RaftSimPfdAlign] host=%s solved=%s hostFwd=%s ")
                    TEXT("solvedFwd=%s solvedUp=%s"),
                    *Root->GetComponentTransform()
                         .TransformPosition(ProductionPfd->GetRelativeLocation())
                         .ToCompactString(),
                    *ChestWorld.GetLocation().ToCompactString(),
                    *Root->GetComponentTransform()
                         .TransformVectorNoScale(
                             ProductionPfd->GetRelativeRotation()
                                 .RotateVector(FVector::ForwardVector))
                         .ToCompactString(),
                    *ChestWorld.GetRotation()
                         .RotateVector(FVector::ForwardVector)
                         .ToCompactString(),
                    *ChestWorld.GetRotation()
                         .RotateVector(FVector::UpVector)
                         .ToCompactString());
                ProductionPfd->SetWorldLocationAndRotation(
                    ChestWorld.GetLocation(), ChestWorld.GetRotation());
            }
        }
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
    {
        TArray<FVector> Vertices, Normals;
        TArray<int32> Triangles;
        TArray<FVector2D> UVs;
        TArray<FProcMeshTangent> Tangents;
        BuildUnitSeatedPelvisMesh(Vertices, Triangles, Normals, UVs, Tangents);
        ReplaceMeshSection(Pelvis, Vertices, Triangles, Normals, UVs, Tangents);
    }
    Torso = CreateOrganicPart(TEXT("Torso"), Jacket ? Jacket : Wetsuit);
    // The assembled MetaHuman body supplies the animated arms, but the PFD
    // terminates below the shoulder crest and the host previously hid every
    // pose-matched upper-arm overlay. Retain two short rounded splash-jacket
    // sleeves as anatomical bridges, not flotation or PFD shoulder pads.
    // These are garment sleeves, not flotation shoulder pads. They start at
    // the authoritative shoulder joint and continue to the elbow beneath the
    // PFD instead of floating as isolated caps beside the torso.
    LeftShoulderSleeve = CreateOrganicPart(
        TEXT("LeftShoulderSleeve"), Jacket ? Jacket : Wetsuit);
    RightShoulderSleeve = CreateOrganicPart(
        TEXT("RightShoulderSleeve"), Jacket ? Jacket : Wetsuit);
    {
        TArray<FVector> Vertices, Normals;
        TArray<int32> Triangles;
        TArray<FVector2D> UVs;
        TArray<FProcMeshTangent> Tangents;
        BuildUnitAnatomicalShoulderSleeveMesh(
            Vertices,
            Triangles,
            Normals,
            UVs,
            Tangents);
        ReplaceMeshSection(
            LeftShoulderSleeve,
            Vertices,
            Triangles,
            Normals,
            UVs,
            Tangents);
        ReplaceMeshSection(
            RightShoulderSleeve,
            Vertices,
            Triangles,
            Normals,
            UVs,
            Tangents);
    }
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
    {
        TArray<FVector> Vertices, Normals;
        TArray<int32> Triangles;
        TArray<FVector2D> UVs;
        TArray<FProcMeshTangent> Tangents;
        BuildUnitHipThighBridgeMesh(Vertices, Triangles, Normals, UVs, Tangents);
        ReplaceMeshSection(LeftThigh, Vertices, Triangles, Normals, UVs, Tangents);
        ReplaceMeshSection(RightThigh, Vertices, Triangles, Normals, UVs, Tangents);
    }
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
    RaftSimPaddleBladeMesh::BuildCommercialPaddleBladeMesh(
        Vertices, Triangles, Normals, UVs, Tangents);
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

void ARaftSimCrewAvatarActor::SetAnatomicalThigh(
    UProceduralMeshComponent* Component,
    const FVector& StartCm,
    const FVector& EndCm,
    float RadiusCm,
    const FVector& TorsoForward)
{
    const FVector Delta = EndCm - StartCm;
    const FVector SafeDirection = Delta.ContainsNaN() || Delta.IsNearlyZero()
        ? FVector::UpVector
        : Delta.GetSafeNormal();
    FVector SafeForward = FVector::VectorPlaneProject(
        TorsoForward.ContainsNaN() ? FVector::ForwardVector : TorsoForward,
        SafeDirection).GetSafeNormal();
    if (SafeForward.IsNearlyZero())
    {
        SafeForward = FVector::VectorPlaneProject(
            FVector::ForwardVector, SafeDirection).GetSafeNormal();
    }
    const FRotator Rotation = SafeForward.IsNearlyZero()
        ? FRotationMatrix::MakeFromZ(SafeDirection).Rotator()
        : FRotationMatrix::MakeFromZX(SafeDirection, SafeForward).Rotator();
    SetEllipsoid(
        Component,
        (StartCm + EndCm) * 0.5f,
        Rotation,
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
    // The V2 seated pelvis is deliberately comparable in width to the torso,
    // substantially deeper in profile, and tall enough to overlap both the
    // lower torso and the assembled upper thighs. Its mesh carries additional
    // rearward glute volume while the solved hip centre remains authoritative.
    SetEllipsoid(
        Pelvis,
        HipCenter,
        Pose.TorsoRotation,
        kProductionSeatedPelvisReferenceExtentCm * Profile);
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
        // The vest wears OVER the wetsuit: its shoulder line rises a few
        // percent and the shell lifts slightly so the CC0 wetsuit's
        // scalloped neckline tucks UNDER the vest instead of draping black
        // flaps across its top panel ("shoulders still covered with black
        // material", third report 2026-09-02).
        // Lift softened from 1.2/+5% (2026-09-02): the taller collar closed
        // the last visible sliver of neck between vest foam and helmet rim,
        // and every helmet read as empty ("the crew don't have heads").
        ProductionPfd->SetRelativeLocationAndRotation(
            Pose.TorsoCenterCm + FVector(0.0f, 0.0f, 0.5f),
            Pose.TorsoRotation);
        ProductionPfd->SetRelativeScale3D(
            Profile * FVector(1.0f, 1.0f, 1.02f));
    }
    const FVector CollarOffset = bUsingProductionVisual
        ? FVector(4.0f, 0.0f, 0.0f)
        : FVector::ZeroVector;
    const float CollarFit = bUsingProductionVisual ? 1.28f : 1.0f;
    // Lengthened with the raised head (2026-08-30) so skin spans the whole
    // opening between the PFD collar foam and the helmet's chin line, and
    // raised/tallened again (2026-09-02) so the skin column continues UP
    // into the helmet shell: from the guide's high-behind view the gap
    // under the rear rim showed hollow black ("there should be a skin tone
    // head in the helmet but it seems to be missing").
    SetEllipsoid(
        Neck,
        Pose.HeadCenterCm - TorsoRotation.RotateVector(FVector(0.0f, 0.0f, 11.0f)) +
            TorsoRotation.RotateVector(CollarOffset),
        Pose.TorsoRotation,
        FVector(5.8f, 5.8f, 10.5f) * CollarFit);
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

    // Elbow drop clamps to the SAME bound as the CC0 adapter
    // (RaftSimCC0CrewVisualActor::ApplyBodyPose): the two rigs solving
    // different elbows let the shoulder-sleeve capsule — anchored to THIS
    // elbow — burst out of the CC0 forearm at power phases ("a strange
    // black shape pops up out of the fore arm when the crew is paddling",
    // player recording 2026-09-02).
    const auto ClampProceduralElbowDrop =
        [](const FVector& ShoulderCm, FVector ElbowCm)
    {
        constexpr float kMaxElbowDropCm = 24.0f;
        ElbowCm.Z = FMath::Max(ElbowCm.Z, ShoulderCm.Z - kMaxElbowDropCm);
        return ElbowCm;
    };
    const FVector LeftElbow = ClampProceduralElbowDrop(
        Pose.LeftShoulderCm,
        FMath::Lerp(Pose.LeftShoulderCm, Pose.LeftHandCm, 0.48f) +
            FVector(0.0f, -5.0f, -2.0f));
    const FVector RightElbow = ClampProceduralElbowDrop(
        Pose.RightShoulderCm,
        FMath::Lerp(Pose.RightShoulderCm, Pose.RightHandCm, 0.48f) +
            FVector(0.0f, 5.0f, -2.0f));
    const FVector LeftShoulderSleeveEnd = FMath::Lerp(
        Pose.LeftShoulderCm, LeftElbow, kProductionShoulderSleeveArmFraction);
    const FVector RightShoulderSleeveEnd = FMath::Lerp(
        Pose.RightShoulderCm, RightElbow, kProductionShoulderSleeveArmFraction);
    const float ShoulderSleeveRadiusCm =
        kProductionShoulderSleeveRadiusCm * LimbBulk;
    SetRoundedLimb(
        LeftShoulderSleeve,
        Pose.LeftShoulderCm,
        LeftShoulderSleeveEnd,
        ShoulderSleeveRadiusCm);
    SetRoundedLimb(
        RightShoulderSleeve,
        Pose.RightShoulderCm,
        RightShoulderSleeveEnd,
        ShoulderSleeveRadiusCm);
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
    const FVector LeftThighBridgeStartCm = FMath::Lerp(
        Pose.LeftHipCm,
        Pose.LeftKneeCm,
        kProductionHipThighBridgeStartFraction);
    const FVector LeftThighBridgeEndCm = FMath::Lerp(
        Pose.LeftHipCm,
        Pose.LeftKneeCm,
        kProductionHipThighBridgeEndFraction);
    const FVector RightThighBridgeStartCm = FMath::Lerp(
        Pose.RightHipCm,
        Pose.RightKneeCm,
        kProductionHipThighBridgeStartFraction);
    const FVector RightThighBridgeEndCm = FMath::Lerp(
        Pose.RightHipCm,
        Pose.RightKneeCm,
        kProductionHipThighBridgeEndFraction);
    if (bUsingProductionVisual)
    {
        const FVector TorsoForward =
            TorsoRotation.RotateVector(FVector::ForwardVector);
        SetAnatomicalThigh(
            LeftThigh,
            LeftThighBridgeStartCm,
            LeftThighBridgeEndCm,
            kProductionHipThighBridgeRadiusCm * LimbBulk,
            TorsoForward);
        SetAnatomicalThigh(
            RightThigh,
            RightThighBridgeStartCm,
            RightThighBridgeEndCm,
            kProductionHipThighBridgeRadiusCm * LimbBulk,
            TorsoForward);
    }
    else
    {
        SetRoundedLimb(
            LeftThigh,
            Pose.LeftHipCm,
            Pose.LeftKneeCm,
            8.3f * LimbBulk);
        SetRoundedLimb(
            RightThigh,
            Pose.RightHipCm,
            Pose.RightKneeCm,
            8.3f * LimbBulk);
    }
    SetRoundedLimb(LeftShin, Pose.LeftKneeCm, Pose.LeftFootCm, 6.7f * LimbBulk);
    SetRoundedLimb(RightShin, Pose.RightKneeCm, Pose.RightFootCm, 6.7f * LimbBulk);
    const FVector LeftFootDirection = (Pose.LeftFootCm - Pose.LeftKneeCm).GetSafeNormal();
    const FVector RightFootDirection = (Pose.RightFootCm - Pose.RightKneeCm).GetSafeNormal();
    SetRoundedLimb(LeftBoot, Pose.LeftFootCm - LeftFootDirection * 3.0f,
                   Pose.LeftFootCm + LeftFootDirection * 11.0f, 5.8f);
    SetRoundedLimb(RightBoot, Pose.RightFootCm - RightFootDirection * 3.0f,
                   Pose.RightFootCm + RightFootDirection * 11.0f, 5.8f);
    if (HasProductionRiverBoots())
    {
        // The source boot is +X toe-forward and +Z cuff-up. Construct that
        // basis explicitly so no pose yaw can make the sole read above the
        // cuff. The authored 23.6 cm source height also overran the strongly
        // flexed seated knee when used at body scale. Fit it as footwear while
        // translating from the source sole bound so the tread remains on the
        // exact previously solved support plane. The solved foot points remain
        // the single animation authority.
        const FVector ProductionBootScale =
            kProductionRiverBootPresentationScale * Profile;
        const auto PlaceProductionBoot = [
            &Pose,
            &ProductionBootScale,
            &Profile](UStaticMeshComponent* Boot,
                      const FVector& SolvedFootCm,
                      float SplayYawDegrees)
        {
            // Seated feet splay outward: dead-ahead toes hid the boot's
            // whole length behind its round cuff from the guide seat, so
            // the footwear read as a plain tube ("the shoes are still
            // cylinders", 2026-09-02). The yaw also shows heel and toe
            // breaking the shin's silhouette.
            const FVector ToeForward =
                FRotator(
                    0.0f, Pose.TorsoRotation.Yaw + SplayYawDegrees, 0.0f)
                    .RotateVector(FVector::ForwardVector);
            const FRotator BootRotation =
                FRotationMatrix::MakeFromXZ(ToeForward, FVector::UpVector)
                    .Rotator();
            const float SourceSoleZCm =
                Boot->GetStaticMesh()->GetBoundingBox().Min.Z;
            FVector FittedLocationCm = SolvedFootCm;
            FittedLocationCm.Z += SourceSoleZCm * Profile.Z *
                (1.0f - kProductionRiverBootPresentationScale.Z);
            Boot->SetRelativeLocationAndRotation(
                FittedLocationCm, BootRotation);
            Boot->SetRelativeScale3D(ProductionBootScale);
        };
        PlaceProductionBoot(ProductionLeftBoot, Pose.LeftFootCm, -16.0f);
        PlaceProductionBoot(ProductionRightBoot, Pose.RightFootCm, 16.0f);
    }

    PaddleShaft->SetVisibility(Pose.bShowPaddle);
    PaddleBlade->SetVisibility(Pose.bShowPaddle);
    PaddleGrip->SetVisibility(Pose.bShowPaddle);
    if (Pose.bShowPaddle)
    {
        SetRoundedLimb(PaddleShaft, Pose.PaddleTopCm, Pose.PaddleBottomCm, 1.65f);
        const FVector Direction = (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
        // In the water the power face aims forward; a RESTING paddle lies
        // flat across the thighs. Deriving the face from ForwardVector left
        // the lap-rest blade standing edge-up like a knife — a sliver that
        // caught no skylight and read as unlit ("their paddles look like
        // they are in shade", 2026-09-02). Face up at rest, forward for
        // every working stroke.
        const FVector PreferredFaceAxis =
            CurrentAction == ERaftSimCrewAvatarAction::SeatedIdle
                ? FVector::UpVector
                : FVector::ForwardVector;
        const FVector PreferredBladeNormal = PreferredFaceAxis -
            Direction * FVector::DotProduct(PreferredFaceAxis, Direction);
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
