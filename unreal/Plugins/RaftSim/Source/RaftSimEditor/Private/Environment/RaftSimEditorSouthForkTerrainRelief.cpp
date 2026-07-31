#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
namespace
{
// The source DEM remains the geographic authority. These bounded wavelengths
// fill only the sub-DEM geomorphology that the source raster cannot resolve,
// and are applied exclusively to the non-colliding far-field underlay.
constexpr float InferredFarFieldReliefMinimumAmplitudeM = 0.12f;
constexpr float InferredFarFieldReliefMaximumAmplitudeM = 4.80f;
constexpr float InferredFarFieldReliefBroadWavelengthM = 180.0f;
constexpr float InferredFarFieldReliefDetailWavelengthM = 58.0f;
constexpr float InferredFarFieldReliefRidgeWavelengthM = 96.0f;
constexpr float InferredFarFieldReliefDomainWarpWavelengthM = 420.0f;
constexpr float InferredFarFieldReliefMaximumDomainWarpM = 32.0f;
constexpr float InferredFarFieldReliefBroadWeight = 0.42f;
constexpr float InferredFarFieldReliefDetailWeight = 0.25f;
constexpr float InferredFarFieldReliefRidgeWeight = 0.33f;

float StableReliefUnitRandom(int32 A, int32 B, int32 C)
{
    uint32 Value = static_cast<uint32>(A) * 73856093u;
    Value ^= static_cast<uint32>(B) * 19349663u;
    Value ^= static_cast<uint32>(C) * 83492791u;
    Value ^= Value >> 13;
    Value *= 1274126177u;
    Value ^= Value >> 16;
    return static_cast<float>(Value & 0x00FFFFFFu) / 16777215.0f;
}

float SampleStableValueNoise2D(
    double WorldXM,
    double WorldYM,
    float WavelengthM,
    int32 Salt)
{
    const double GridX = WorldXM / FMath::Max(WavelengthM, KINDA_SMALL_NUMBER);
    const double GridY = WorldYM / FMath::Max(WavelengthM, KINDA_SMALL_NUMBER);
    const int32 X0 = FMath::FloorToInt(GridX);
    const int32 Y0 = FMath::FloorToInt(GridY);
    const int32 X1 = X0 + 1;
    const int32 Y1 = Y0 + 1;
    const float FractionX = static_cast<float>(GridX - X0);
    const float FractionY = static_cast<float>(GridY - Y0);
    const float SmoothX = FractionX * FractionX * (3.0f - 2.0f * FractionX);
    const float SmoothY = FractionY * FractionY * (3.0f - 2.0f * FractionY);
    const auto LatticeValue = [Salt](int32 X, int32 Y)
    {
        return StableReliefUnitRandom(X, Y, Salt) * 2.0f - 1.0f;
    };
    const float North = FMath::Lerp(
        LatticeValue(X0, Y0), LatticeValue(X1, Y0), SmoothX);
    const float South = FMath::Lerp(
        LatticeValue(X0, Y1), LatticeValue(X1, Y1), SmoothX);
    return FMath::Lerp(North, South, SmoothY);
}
} // namespace

float ComputeSouthForkInferredFarFieldReliefM(
    double WorldXM,
    double WorldYM,
    float SourceSlope)
{
    // Preserve broad source landforms and avoid visibly corrugating flats.
    // Relief grows smoothly from centimetres on benches to a hard 4.8 m cap
    // on steep canyon walls. World-space sampling keeps overlapping source
    // windows on the same deterministic noise phase.
    float SlopeAlpha = FMath::Clamp((SourceSlope - 0.025f) / 0.35f, 0.0f, 1.0f);
    SlopeAlpha = SlopeAlpha * SlopeAlpha * (3.0f - 2.0f * SlopeAlpha);
    const float AmplitudeM = FMath::Lerp(
        InferredFarFieldReliefMinimumAmplitudeM,
        InferredFarFieldReliefMaximumAmplitudeM,
        SlopeAlpha);
    // Low-frequency domain warping avoids the axis-aligned cell rhythm of a
    // conventional value-noise heightfield while keeping a stable world-space
    // phase across overlapping source windows. The paired absolute-value
    // signals below form irregular shoulders and drainage incisions without
    // imposing a net elevation bias on the authoritative DEM.
    const float DomainWarpXM = InferredFarFieldReliefMaximumDomainWarpM *
        SampleStableValueNoise2D(
            WorldXM, WorldYM,
            InferredFarFieldReliefDomainWarpWavelengthM, 239);
    const float DomainWarpYM = InferredFarFieldReliefMaximumDomainWarpM *
        SampleStableValueNoise2D(
            WorldXM + 1379.0, WorldYM - 823.0,
            InferredFarFieldReliefDomainWarpWavelengthM, 241);
    const double WarpedWorldXM = WorldXM + DomainWarpXM;
    const double WarpedWorldYM = WorldYM + DomainWarpYM;
    const float BroadRelief = SampleStableValueNoise2D(
        WorldXM + DomainWarpXM * 0.35,
        WorldYM + DomainWarpYM * 0.35,
        InferredFarFieldReliefBroadWavelengthM, 211);
    const float DetailRelief = SampleStableValueNoise2D(
        WarpedWorldXM, WarpedWorldYM,
        InferredFarFieldReliefDetailWavelengthM, 223);
    const float RidgeA = SampleStableValueNoise2D(
        WarpedWorldXM, WarpedWorldYM,
        InferredFarFieldReliefRidgeWavelengthM, 227);
    const float RidgeB = SampleStableValueNoise2D(
        WarpedWorldXM + 47.0, WarpedWorldYM - 31.0,
        InferredFarFieldReliefRidgeWavelengthM, 229);
    const float RidgeAndDrainageRelief = FMath::Clamp(
        (FMath::Abs(RidgeB) - FMath::Abs(RidgeA)) * 1.65f,
        -1.0f,
        1.0f);
    const float ReliefM = AmplitudeM * (
        BroadRelief * InferredFarFieldReliefBroadWeight +
        DetailRelief * InferredFarFieldReliefDetailWeight +
        RidgeAndDrainageRelief * InferredFarFieldReliefRidgeWeight);
    return FMath::Clamp(ReliefM, -AmplitudeM, AmplitudeM);
}

TSharedRef<FJsonObject> BuildSouthForkInferredFarFieldReliefManifest()
{
    TSharedRef<FJsonObject> Relief = MakeShared<FJsonObject>();
    Relief->SetStringField(
        TEXT("algorithm"),
        TEXT("world_space_slope_conditioned_domain_warped_ridged_fractal_v2"));
    Relief->SetStringField(
        TEXT("authority"),
        TEXT("visual-only deterministic infill over source DEM; non-colliding; not for navigation"));
    Relief->SetNumberField(
        TEXT("minimum_amplitude_m"), InferredFarFieldReliefMinimumAmplitudeM);
    Relief->SetNumberField(
        TEXT("maximum_amplitude_m"), InferredFarFieldReliefMaximumAmplitudeM);
    Relief->SetNumberField(
        TEXT("broad_wavelength_m"), InferredFarFieldReliefBroadWavelengthM);
    Relief->SetNumberField(
        TEXT("detail_wavelength_m"), InferredFarFieldReliefDetailWavelengthM);
    Relief->SetNumberField(
        TEXT("ridge_wavelength_m"), InferredFarFieldReliefRidgeWavelengthM);
    Relief->SetNumberField(
        TEXT("domain_warp_wavelength_m"),
        InferredFarFieldReliefDomainWarpWavelengthM);
    Relief->SetNumberField(
        TEXT("maximum_domain_warp_m"),
        InferredFarFieldReliefMaximumDomainWarpM);
    Relief->SetNumberField(TEXT("broad_weight"), InferredFarFieldReliefBroadWeight);
    Relief->SetNumberField(TEXT("detail_weight"), InferredFarFieldReliefDetailWeight);
    Relief->SetNumberField(TEXT("ridge_weight"), InferredFarFieldReliefRidgeWeight);
    Relief->SetBoolField(TEXT("affects_gameplay_collision"), false);
    Relief->SetBoolField(TEXT("affects_hydraulics"), false);
    return Relief;
}

} // namespace RaftSimEditorEnvironment
