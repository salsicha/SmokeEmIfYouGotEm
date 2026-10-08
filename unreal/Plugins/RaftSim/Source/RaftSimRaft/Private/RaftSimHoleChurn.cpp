#include "RaftSimHoleChurn.h"

#include "Components/AudioComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "RaftSimSynthVoice.h"
#include "Sound/SoundAttenuation.h"

namespace
{
constexpr int32 kAcrossSegments = 56;
/** Points along each stretch of the wave's cross-section between its
 * control points (boil line, back, crest, lip, tip, curtain, plunge). */
constexpr int32 kPointsPerStretch = 6;
constexpr int32 kProfilePoints = 7 * kPointsPerStretch + 1;
/** Rows of the churned band where the curtain lands. */
constexpr int32 kSeamRows = 10;

float Hash(int32 X, int32 Y, int32 Z)
{
    uint32 H = uint32(X) * 73856093u ^ uint32(Y) * 19349663u ^ uint32(Z) * 83492791u;
    H = (H ^ (H >> 13)) * 1274126177u;
    H ^= H >> 16;
    return float(H & 0xffffffu) / float(0xffffffu);
}

/** Smooth value noise in -1..1. */
float Noise(float X, float Y, float Z)
{
    const int32 IX = FMath::FloorToInt(X), IY = FMath::FloorToInt(Y), IZ = FMath::FloorToInt(Z);
    const auto Fade = [](float T) { return T * T * (3.0f - 2.0f * T); };
    const float FX = Fade(X - IX), FY = Fade(Y - IY), FZ = Fade(Z - IZ);
    const auto Corner = [&](int32 DX, int32 DY, int32 DZ) { return Hash(IX + DX, IY + DY, IZ + DZ); };
    const float X00 = FMath::Lerp(Corner(0, 0, 0), Corner(1, 0, 0), FX);
    const float X10 = FMath::Lerp(Corner(0, 1, 0), Corner(1, 1, 0), FX);
    const float X01 = FMath::Lerp(Corner(0, 0, 1), Corner(1, 0, 1), FX);
    const float X11 = FMath::Lerp(Corner(0, 1, 1), Corner(1, 1, 1), FX);
    return 2.0f * FMath::Lerp(FMath::Lerp(X00, X10, FY), FMath::Lerp(X01, X11, FY), FZ) - 1.0f;
}

FVector2D CatmullRom(const FVector2D& P0, const FVector2D& P1, const FVector2D& P2, const FVector2D& P3, float T)
{
    const float T2 = T * T, T3 = T2 * T;
    return 0.5f * ((2.0f * P1) + (P2 - P0) * T + (2.0f * P0 - 5.0f * P1 + 4.0f * P2 - P3) * T2 +
        (3.0f * P1 - P0 - 3.0f * P2 + P3) * T3);
}
}

FRaftSimHoleChurnLook FRaftSimHoleChurnLook::Preset(const FString& Name)
{
    FRaftSimHoleChurnLook Look;
    const FString Key = Name.ToLower();
    if (Key == TEXT("plunge"))
    {
        // A plunging breaker: the lip throws further out and falls steeply.
        Look.WaveHeightCm = 85.0f;
        Look.ThrowCm = 65.0f;
        Look.ThrowVariation = 0.3f;
        Look.RollCmPerSecond = 200.0f;
    }
    else if (Key == TEXT("big"))
    {
        // A big, retentive hole: a taller, longer wave breaking harder.
        Look.WaveHeightCm = 100.0f;
        Look.WaveLengthCm = 460.0f;
        Look.CrestPosition = 0.48f;
        Look.ThrowCm = 60.0f;
        Look.ThrowVariation = 0.3f;
        Look.RollCmPerSecond = 220.0f;
        Look.Turbulence = 0.14f;
    }
    return Look;
}

URaftSimHoleChurnComponent::URaftSimHoleChurnComponent(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    PrimaryComponentTick.bCanEverTick = false;
    SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetCastShadow(false);
    bUseAsyncCooking = true;
}

RaftSimHoleWave::FShape URaftSimHoleChurnComponent::ShapeOf(const FRaftSimHoleChurnSite& Site)
{
    RaftSimHoleWave::FShape Shape;
    Shape.HeightM = Site.Look.WaveHeightCm * 0.01;
    Shape.LengthM = Site.Look.WaveLengthCm * 0.01;
    Shape.PlungeOffsetM = Site.PlungeOffsetCm * 0.01;
    Shape.CrestPosition = Site.Look.CrestPosition;
    Shape.ThrowM = Site.Look.ThrowCm * 0.01;
    Shape.HalfWidthM = Site.HalfWidthCm * 0.01;
    Shape.CrestBowPerSquareMeter = Site.CrestBowCmPerSquareMeter * 0.01;
    Shape.RollMps = Site.Look.RollCmPerSecond * 0.01;
    Shape.Intensity = Site.Intensity;
    // As deep as the wave is high, as for a site's own pile (ForCrest).
    Shape.ReturnDepthM = 0.8 * Shape.HeightM;
    return Shape;
}

void URaftSimHoleChurnComponent::ApplyFoamDensity(UMaterialInstanceDynamic* Material, float Density)
{
    if (!Material)
    {
        return;
    }
    // From a lacy aerated veil (the lip's own perforated foam) to dense,
    // clotted white water whose lace breaks it up without punching it open.
    const struct { const TCHAR* Name; float Lace, Dense; } Parameters[] = {
        {TEXT("BreakingWaterOpacity"), 0.10f, 0.25f},
        {TEXT("BreakingFoamOpacity"), 0.92f, 0.98f},
        {TEXT("BreakingFoamFloor"), 0.60f, 1.00f},
        {TEXT("BreakingFoamIntensityGain"), 0.90f, 1.00f},
        {TEXT("BreakingFoamCoreGain"), 0.70f, 1.00f},
        {TEXT("BreakingFoamCoreClotBlend"), 0.60f, 1.00f},
        {TEXT("BreakingFoamPrimaryCutBias"), 0.20f, 0.06f},
        {TEXT("BreakingFoamPrimaryCutGain"), 1.80f, 2.60f},
        {TEXT("BreakingFoamDetailCutBias"), 0.20f, 0.06f},
        {TEXT("BreakingFoamDetailCutGain"), 1.70f, 2.40f},
        {TEXT("BreakingFoamBubbleHoleFloor"), 0.15f, 0.60f},
        {TEXT("BreakingFoamPatchOutsideFloor"), 0.25f, 0.75f},
        {TEXT("PrimaryLaceGain"), 0.82f, 1.00f},
        {TEXT("DetailLaceGain"), 0.38f, 0.50f},
        {TEXT("BreakingFoamRoughness"), 0.85f, 0.88f}};
    const float T = FMath::Clamp(Density, 0.0f, 1.0f);
    for (const auto& Parameter : Parameters)
    {
        Material->SetScalarParameterValue(Parameter.Name, FMath::Lerp(Parameter.Lace, Parameter.Dense, T));
    }
    // Aerated water scatters light through itself and stays white in shade;
    // the lip material's grey-teal shadow tone made the sunless face of a
    // breaking wave read as dirty grey.
    Material->SetVectorParameterValue(TEXT("BreakingFoamShadowColor"), FLinearColor(0.78f, 0.84f, 0.88f, 1.0f));
    Material->SetVectorParameterValue(TEXT("BreakingFoamColor"), FLinearColor(0.98f, 0.99f, 1.0f, 1.0f));
}

void URaftSimHoleChurnComponent::Configure(const FRaftSimHoleChurnSite& InSite, FSurfaceHeightCm InSurface, UMaterialInterface* WaveMaterial)
{
    Site = InSite;
    Site.Downstream = Site.Downstream.GetSafeNormal2D();
    if (Site.Downstream.IsNearlyZero())
    {
        Site.Downstream = FVector::ForwardVector;
    }
    Across = FVector(-Site.Downstream.Y, Site.Downstream.X, 0.0f);
    Surface = MoveTemp(InSurface);
    Random.Initialize(Site.Seed * 7919 + 1301);
    WaveTriangles.Reset();
    for (int32 A = 0; A < kAcrossSegments; ++A)
    {
        for (int32 B = 0; B + 1 < kProfilePoints; ++B)
        {
            // The profile runs upstream (back to front), so this winding
            // keeps the wave's outer side as its front face.
            const int32 I = A * kProfilePoints + B;
            WaveTriangles.Append({I, I + 1, I + kProfilePoints, I + 1, I + kProfilePoints + 1, I + kProfilePoints});
        }
    }
    SeamTriangles.Reset();
    for (int32 A = 0; A < kAcrossSegments; ++A)
    {
        for (int32 B = 0; B + 1 < kSeamRows; ++B)
        {
            const int32 I = A * kSeamRows + B;
            SeamTriangles.Append({I, I + kSeamRows, I + 1, I + 1, I + kSeamRows, I + kSeamRows + 1});
        }
    }
    UMaterialInstanceDynamic* Water = WaveMaterial ? UMaterialInstanceDynamic::Create(WaveMaterial, this) : nullptr;
    ApplyFoamDensity(Water, Site.Look.FoamDensity);
    SetMaterial(0, Water);
    SetMaterial(1, Water);
    bSectionsCreated = false;
    TimeSeconds = 0.0f;
}

void URaftSimHoleChurnComponent::EnableSound(uint32 Seed)
{
    if (Sound || !GetOwner())
    {
        return;
    }
    Sound = NewObject<UAudioComponent>(GetOwner());
    Sound->SetupAttachment(this);
    Sound->SetUsingAbsoluteLocation(true);
    Sound->bAutoActivate = false;
    Sound->bIsUISound = false;
    Sound->bAllowSpatialization = true;
    FSoundAttenuationSettings Settings;
    Settings.bAttenuate = true;
    Settings.bSpatialize = true;
    Settings.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
    Settings.AttenuationShape = EAttenuationShape::Sphere;
    Settings.AttenuationShapeExtents = FVector(800.0f, 0.0f, 0.0f);
    Settings.FalloffDistance = 7000.0f;
    Settings.dBAttenuationAtMax = -40.0f;
    Settings.bEnableReverbSend = true;
    Settings.ReverbSendMethod = EReverbSendMethod::Manual;
    Settings.ManualReverbSendLevel = 0.3f;
    Sound->bOverrideAttenuation = true;
    Sound->SetAttenuationOverrides(Settings);
    Sound->RegisterComponent();
    SoundWave = NewObject<URaftSimSynthSoundWave>(this);
    SoundWave->InitializeVoice(ERaftSimSynthVoiceKind::HoleChurn, Seed);
    Sound->SetSound(SoundWave);
    Sound->SetWorldLocation(Site.CrestCm + Site.Downstream * (Site.PlungeOffsetCm + Site.Look.CrestPosition * Site.Look.WaveLengthCm));
    Sound->Play();
}

void URaftSimHoleChurnComponent::SetRaftExclusion(const FTransform& RaftTransform, float HalfLengthCm, float HalfWidthCm)
{
    bHasExclusion = true;
    Exclusion = RaftTransform;
    ExclusionHalfLengthCm = HalfLengthCm;
    ExclusionHalfWidthCm = HalfWidthCm;
}

float URaftSimHoleChurnComponent::Outside(const FVector& PointCm) const
{
    if (!bHasExclusion)
    {
        return 1.0f;
    }
    // Only the boat's inside, under its floor and crew, is kept clear: the
    // white water runs right up to the tubes and piles against them. Kept
    // clear out to the raft's outline and beyond, the wave had a raft-shaped
    // hole in it wherever the boat sat ("a boat sized gap in the crashing
    // wave", 2026-10-08).
    const FVector Local = Exclusion.InverseTransformPositionNoScale(PointCm);
    const float Ellipse = FMath::Square(Local.X / FMath::Max(0.78f * ExclusionHalfLengthCm, 1.0f)) +
        FMath::Square(Local.Y / FMath::Max(0.7f * ExclusionHalfWidthCm, 1.0f));
    return FMath::SmoothStep(0.6f, 1.0f, Ellipse);
}

void URaftSimHoleChurnComponent::Profile(float AcrossCm, float ToeLevelCm, TArray<FVector>& OutPoints,
    TArray<FVector>& OutNormals, TArray<float>& OutArc, FVector& OutPlungeCm) const
{
    const FRaftSimHoleChurnLook& Look = Site.Look;
    const float AcrossM = AcrossCm * 0.01f;
    const float Bow = Site.CrestBowCmPerSquareMeter * AcrossM * AcrossM;
    // The wave dies away toward the ends of the hole.
    const float Lateral = FMath::Exp(-FMath::Pow(FMath::Abs(AcrossCm) / (0.8f * Site.HalfWidthCm), 4.0f));
    const FVector Base = Site.CrestCm + Across * AcrossCm;
    const auto WaterAt = [&](float AlongCm)
    {
        const FVector Point = Base + Site.Downstream * AlongCm;
        return Surface ? Surface(Point) : Point.Z;
    };
    // The lip throws out and falls back in broad sections along the span,
    // smoothly enough that neighbouring sections stay joined.
    const float Throw = Look.ThrowCm * Lateral * FMath::Max(0.5f, 1.0f + Look.ThrowVariation *
        Noise(AcrossCm / 200.0f, TimeSeconds * 1.1f, 2.3f));
    const float Height = Look.WaveHeightCm * Site.Intensity * Lateral *
        (1.0f + 0.08f * Noise(AcrossCm / 120.0f, TimeSeconds * 0.4f, 5.7f));
    const float CrestAlong = Bow + Site.PlungeOffsetCm + Look.CrestPosition * Look.WaveLengthCm;
    const float BoilAlong = Bow + Site.PlungeOffsetCm + Look.WaveLengthCm;
    const float Top = ToeLevelCm + Height;
    const float TipAlong = FMath::Max(CrestAlong - Throw, Bow + Site.PlungeOffsetCm);
    const float PlungeAlong = FMath::Max(TipAlong - 12.0f, Bow + Site.PlungeOffsetCm * 0.5f);
    // Boil line, up the back, the crest, the curling lip, its tip, and the
    // curtain falling to where it lands on the incoming water.
    const FVector2D Control[] = {
        FVector2D(BoilAlong, WaterAt(BoilAlong)),
        FVector2D(BoilAlong - 0.3f * (BoilAlong - CrestAlong), FMath::Max(WaterAt(BoilAlong - 0.3f * (BoilAlong - CrestAlong)), ToeLevelCm + 0.45f * Height)),
        FVector2D(CrestAlong + 0.2f * (BoilAlong - CrestAlong), ToeLevelCm + 0.9f * Height),
        FVector2D(CrestAlong, Top),
        FVector2D(CrestAlong - 0.55f * Throw, Top - 0.02f * Height),
        FVector2D(TipAlong, Top - 0.25f * Height),
        FVector2D(TipAlong - 6.0f, ToeLevelCm + 0.35f * Height),
        FVector2D(PlungeAlong, WaterAt(PlungeAlong))};
    constexpr int32 ControlCount = UE_ARRAY_COUNT(Control);
    static_assert(ControlCount == 8, "seven stretches between eight control points");
    // The same number of points on each stretch in every cross-section, so
    // the back, crest, lip and curtain of neighbouring sections line up:
    // spaced by length over the whole curve, sections of different size
    // joined one's lip to the next one's back and tore the wave apart.
    TArray<FVector2D> Curve;
    TArray<float> CurveArc;
    for (int32 Segment = 0; Segment + 1 < ControlCount; ++Segment)
    {
        const FVector2D& P0 = Control[FMath::Max(Segment - 1, 0)];
        const FVector2D& P1 = Control[Segment];
        const FVector2D& P2 = Control[Segment + 1];
        const FVector2D& P3 = Control[FMath::Min(Segment + 2, ControlCount - 1)];
        for (int32 Step = 0; Step < kPointsPerStretch; ++Step)
        {
            const FVector2D Point = CatmullRom(P0, P1, P2, P3, float(Step) / kPointsPerStretch);
            CurveArc.Add(Curve.Num() == 0 ? 0.0f : CurveArc.Last() + FVector2D::Distance(Curve.Last(), Point));
            Curve.Add(Point);
        }
    }
    CurveArc.Add(CurveArc.Last() + FVector2D::Distance(Curve.Last(), Control[ControlCount - 1]));
    Curve.Add(Control[ControlCount - 1]);
    const float Length = CurveArc.Last();
    // The water rolls along the curve; lumps ride it, largest over the top
    // and on the falling curtain.
    const float Roll = Look.RollCmPerSecond * TimeSeconds;
    OutPoints.SetNum(kProfilePoints);
    OutNormals.SetNum(kProfilePoints);
    OutArc.SetNum(kProfilePoints);
    for (int32 Index = 0; Index < kProfilePoints; ++Index)
    {
        const float Arc = CurveArc[Index];
        const FVector2D Point = Curve[Index];
        const FVector2D Tangent = (Curve[FMath::Min(Index + 1, kProfilePoints - 1)] - Curve[FMath::Max(Index - 1, 0)]).GetSafeNormal();
        // Outward from the roller: up on the crest, downstream on the back,
        // upstream on the curtain.
        const FVector2D Normal2D(Tangent.Y, -Tangent.X);
        const float Along = Arc / FMath::Max(Length, 1.0f);
        const float Turbulent = FMath::SmoothStep(0.25f, 0.55f, Along);
        const float Lump = Look.Turbulence * Height * (0.35f + 0.65f * Turbulent) *
            (0.6f * Noise((Arc - Roll) / 38.0f, AcrossCm / 38.0f, TimeSeconds * 0.8f) +
             0.4f * Noise((Arc - Roll) / 16.0f, AcrossCm / 16.0f, TimeSeconds * 1.6f + 9.0f));
        const FVector2D Displaced = Point + Normal2D * Lump;
        const FVector World = Base + Site.Downstream * Displaced.X + FVector::UpVector * (Displaced.Y - Base.Z);
        OutPoints[Index] = FVector(World.X, World.Y, Displaced.Y);
        OutNormals[Index] = (Site.Downstream * Normal2D.X + FVector::UpVector * Normal2D.Y).GetSafeNormal();
        OutArc[Index] = Arc;
    }
    const FVector Plunge = Base + Site.Downstream * PlungeAlong;
    OutPlungeCm = FVector(Plunge.X, Plunge.Y, WaterAt(PlungeAlong));
}

void URaftSimHoleChurnComponent::Advance(float DeltaSeconds, const FVector& ViewLocationCm)
{
    const FRaftSimHoleChurnLook& Look = Site.Look;
    const float Dt = FMath::Clamp(DeltaSeconds, 0.0f, 0.1f);
    TimeSeconds += Dt;
    // The trough's lowest water along the wave's centre line.
    float ToeLevelCm = TNumericLimits<float>::Max();
    for (int32 Step = 0; Step <= 24; ++Step)
    {
        const FVector Point = Site.CrestCm + Site.Downstream * (Site.PlungeOffsetCm + Step * Look.WaveLengthCm / 24.0f);
        ToeLevelCm = FMath::Min(ToeLevelCm, Surface ? Surface(Point) : Point.Z);
    }

    // The breaking wave's sound: a steady roar whose crashing never stops
    // but never repeats.
    if (RaftSimSynth::FVoice* Voice = SoundWave ? SoundWave->GetVoice() : nullptr)
    {
        const FVector SoundAt = Site.CrestCm + Site.Downstream * (Site.PlungeOffsetCm + Look.CrestPosition * Look.WaveLengthCm);
        Voice->GetControls().Level = 0.9f * FMath::Clamp(Site.Intensity, 0.0f, 1.0f);
        Voice->GetControls().Intensity = 0.6f + 0.4f * FMath::Clamp(Site.Intensity, 0.0f, 1.0f);
        Voice->GetControls().Surge = 0.55f + 0.35f * Noise(TimeSeconds * 0.7f, 1.7f, 4.2f);
        Voice->GetControls().Distance = FVector::Distance(ViewLocationCm, SoundAt) * 0.01f;
        if (TimeSeconds >= NextSoundCrashSeconds)
        {
            Voice->Trigger(ERaftSimSynthEvent::HoleCrash, float(Random.FRandRange(0.25f, 0.6f)) * Site.Intensity);
            NextSoundCrashSeconds = TimeSeconds - FMath::Loge(FMath::Max(Random.FRand(), 0.05f)) / 1.4f;
        }
    }

    // The wave: one cross-section per place across the span.
    const int32 Rows = kAcrossSegments + 1;
    TArray<FVector> Vertices, Normals, Analytic;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<float> Arcs;
    TArray<FVector> Plunges;
    Vertices.SetNum(Rows * kProfilePoints);
    Analytic.SetNum(Rows * kProfilePoints);
    Normals.SetNum(Rows * kProfilePoints);
    Uvs.SetNum(Rows * kProfilePoints);
    Colors.SetNum(Rows * kProfilePoints);
    Plunges.SetNum(Rows);
    const float Roll = Look.RollCmPerSecond * TimeSeconds;
    TArray<FVector> RowPoints, RowNormals;
    for (int32 A = 0; A < Rows; ++A)
    {
        const float AcrossT = float(A) / kAcrossSegments * 2.0f - 1.0f;
        const float AcrossCm = AcrossT * Site.HalfWidthCm;
        Profile(AcrossCm, ToeLevelCm, RowPoints, RowNormals, Arcs, Plunges[A]);
        const float Length = FMath::Max(Arcs.Last(), 1.0f);
        const float Edge = Noise(AcrossT * 4.0f, TimeSeconds * 0.3f, 1.3f);
        for (int32 B = 0; B < kProfilePoints; ++B)
        {
            const int32 I = A * kProfilePoints + B;
            const float Along = Arcs[B] / Length;
            // Squashed flat where the raft sits in the hole.
            const FVector Ground(RowPoints[B].X, RowPoints[B].Y, Surface ? Surface(RowPoints[B]) : RowPoints[B].Z);
            const float Clear = Outside(RowPoints[B]);
            Vertices[I] = FMath::Lerp(Ground, RowPoints[B], Clear);
            Analytic[I] = RowNormals[B];
            // The white water's texture rolls with it, over the lip and down.
            Uvs[I] = FVector2D(AcrossCm / 240.0f, (Arcs[B] - Roll) / 160.0f);
            const float BackFade = FMath::SmoothStep(0.0f, 0.22f + 0.06f * Edge, Along);
            const float SideFade = 1.0f - FMath::SmoothStep(0.62f + 0.15f * Edge, 1.0f, FMath::Abs(AcrossT));
            const float Alpha = BackFade * SideFade * (1.0f - FMath::SmoothStep(0.96f, 1.0f, Along)) * Clear;
            // Densest over the crest, lip and curtain; still white aerated
            // water down the back.
            const float Core = FMath::Lerp(0.78f, 1.0f, FMath::SmoothStep(0.15f, 0.45f, Along));
            Colors[I] = FLinearColor(FMath::Lerp(0.68f, 1.0f, Site.Intensity), 0.2f, Core, Alpha);
        }
    }
    for (int32 A = 0; A < Rows; ++A)
    {
        for (int32 B = 0; B < kProfilePoints; ++B)
        {
            const int32 I = A * kProfilePoints + B;
            const FVector AlongTangent = Vertices[A * kProfilePoints + FMath::Min(B + 1, kProfilePoints - 1)] -
                Vertices[A * kProfilePoints + FMath::Max(B - 1, 0)];
            const FVector AcrossTangent = Vertices[FMath::Min(A + 1, kAcrossSegments) * kProfilePoints + B] -
                Vertices[FMath::Max(A - 1, 0) * kProfilePoints + B];
            FVector Normal = FVector::CrossProduct(AlongTangent, AcrossTangent).GetSafeNormal();
            if (FVector::DotProduct(Normal, Analytic[I]) < 0.0f)
            {
                Normal = -Normal;
            }
            Normals[I] = Normal.IsNearlyZero() ? Analytic[I] : Normal;
        }
    }

    // The churned band where the curtain lands on the incoming water, from
    // just above the landing to under the lip.
    TArray<FVector> SVertices, SNormals;
    TArray<FVector2D> SUvs;
    TArray<FLinearColor> SColors;
    SVertices.SetNum(Rows * kSeamRows);
    SNormals.SetNum(Rows * kSeamRows);
    SUvs.SetNum(Rows * kSeamRows);
    SColors.SetNum(Rows * kSeamRows);
    for (int32 A = 0; A < Rows; ++A)
    {
        const float AcrossT = float(A) / kAcrossSegments * 2.0f - 1.0f;
        const float AcrossCm = AcrossT * Site.HalfWidthCm;
        const float Lateral = FMath::Exp(-FMath::Pow(FMath::Abs(AcrossCm) / (0.8f * Site.HalfWidthCm), 4.0f));
        for (int32 B = 0; B < kSeamRows; ++B)
        {
            const int32 I = A * kSeamRows + B;
            const float T = float(B) / (kSeamRows - 1);
            const float OffsetCm = FMath::Lerp(-35.0f, 75.0f, T);
            FVector Point = Plunges[A] + Site.Downstream * OffsetCm;
            const float Water = Surface ? Surface(Point) : Point.Z;
            const float Churn = 0.5f + 0.5f * Noise((OffsetCm + 90.0f * TimeSeconds) / 30.0f, AcrossCm / 30.0f, TimeSeconds * 1.8f);
            const float Hump = FMath::Sin(PI * T);
            Point.Z = Water + (4.0f + 16.0f * Churn * Hump) * Lateral * Site.Intensity;
            const float Clear = Outside(Point);
            Point.Z = FMath::Lerp(Water, Point.Z, Clear);
            SVertices[I] = Point;
            SNormals[I] = FVector::UpVector;
            SUvs[I] = FVector2D(AcrossCm / 240.0f + 0.37f, (OffsetCm + 90.0f * TimeSeconds) / 160.0f);
            const float Edge = Noise(AcrossT * 5.0f, OffsetCm / 40.0f, TimeSeconds * 0.5f);
            const float Alpha = FMath::Sin(PI * FMath::Clamp(T + 0.1f * Edge, 0.0f, 1.0f)) *
                (1.0f - FMath::SmoothStep(0.62f + 0.15f * Edge, 1.0f, FMath::Abs(AcrossT))) * Clear;
            SColors[I] = FLinearColor(FMath::Lerp(0.68f, 1.0f, Site.Intensity), 0.2f, 1.0f, Alpha);
        }
    }

    // The geometry above is in world space; the mesh is in the component's.
    const FTransform& ToWorld = GetComponentTransform();
    for (TArray<FVector>* Points : {&Vertices, &SVertices})
    {
        for (FVector& Point : *Points)
        {
            Point = ToWorld.InverseTransformPosition(Point);
        }
    }
    for (TArray<FVector>* Directions : {&Normals, &SNormals})
    {
        for (FVector& Direction : *Directions)
        {
            Direction = ToWorld.InverseTransformVectorNoScale(Direction);
        }
    }
    TArray<FProcMeshTangent> Tangents, STangents;
    Tangents.Init(FProcMeshTangent(Across, false), Vertices.Num());
    STangents.Init(FProcMeshTangent(Across, false), SVertices.Num());
    if (!bSectionsCreated)
    {
        CreateMeshSection_LinearColor(0, Vertices, WaveTriangles, Normals, Uvs, Colors, Tangents, false);
        CreateMeshSection_LinearColor(1, SVertices, SeamTriangles, SNormals, SUvs, SColors, STangents, false);
        bSectionsCreated = true;
    }
    else
    {
        UpdateMeshSection_LinearColor(0, Vertices, Normals, Uvs, Colors, Tangents);
        UpdateMeshSection_LinearColor(1, SVertices, SNormals, SUvs, SColors, STangents);
    }
}
