#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr float MinimumBankDistanceM = 14.0f;
constexpr float FullBankDistanceM = 23.0f;
constexpr float OuterBankFadeStartM = 100.0f;
constexpr float MaximumBankDistanceM = 112.0f;
constexpr float MaximumSourceSlope = 0.58f;
constexpr float MaximumWetMask = 0.10f;
constexpr float FullPatchEdgeDistanceM = 36.0f;
constexpr float MaximumDisplacementCm = 42.0f;
}

FSouthForkBankMicroreliefSample ComputeSouthForkBankMicroreliefSample(
    double WorldXM,
    double WorldYM,
    float StationM,
    float LateralM,
    float SourceSlope,
    float WetMask,
    float PatchEdgeDistanceM)
{
    FSouthForkBankMicroreliefSample Sample;
    const float BankDistanceM = FMath::Abs(LateralM);
    if (!FMath::IsFinite(WorldXM) || !FMath::IsFinite(WorldYM) ||
        !FMath::IsFinite(StationM) || !FMath::IsFinite(LateralM) ||
        WetMask > MaximumWetMask || BankDistanceM < MinimumBankDistanceM ||
        BankDistanceM > MaximumBankDistanceM ||
        SourceSlope > MaximumSourceSlope || PatchEdgeDistanceM <= 0.0f)
    {
        return Sample;
    }

    const float ShoreFade = FMath::SmoothStep(
        MinimumBankDistanceM, FullBankDistanceM, BankDistanceM);
    const float OuterFade = 1.0f - FMath::SmoothStep(
        OuterBankFadeStartM, MaximumBankDistanceM, BankDistanceM);
    const float SlopeFade = 1.0f - FMath::SmoothStep(
        0.44f, MaximumSourceSlope, SourceSlope);
    const float EdgeFade = FMath::SmoothStep(
        0.0f, FullPatchEdgeDistanceM, PatchEdgeDistanceM);
    const float WetFade = 1.0f - FMath::SmoothStep(
        0.02f, MaximumWetMask, WetMask);
    Sample.CombinedFade = ShoreFade * OuterFade * SlopeFade * EdgeFade * WetFade;
    if (Sample.CombinedFade <= 0.08f)
    {
        Sample.CombinedFade = 0.0f;
        return Sample;
    }

    // World-space, incommensurate fields retain the same phase across patch and
    // source-tile seams. Their positive relief envelope keeps the presentation
    // derivative above the authoritative collision mesh while internal valleys
    // read as drainage cuts relative to adjacent raised mineral fabric.
    const FVector2D WorldM(
        static_cast<float>(WorldXM), static_cast<float>(WorldYM));
    const float Broad = 0.5f + 0.5f * FMath::PerlinNoise2D(
        WorldM / 12.5f + FVector2D(13.17f, -7.91f));
    const float Detail = 0.5f + 0.5f * FMath::PerlinNoise2D(
        FVector2D(
            static_cast<float>(WorldXM + 0.21 * WorldYM),
            static_cast<float>(WorldYM - 0.17 * WorldXM)) /
            4.7f + FVector2D(-23.61f, 18.47f));
    const float DrainageSignal = FMath::Abs(FMath::PerlinNoise2D(
        FVector2D(StationM / 9.0f, LateralM / 5.6f) +
            FVector2D(5.29f, -11.83f)));
    const float DrainageShoulder = FMath::Clamp(
        (DrainageSignal - 0.10f) / 0.90f, 0.0f, 1.0f);
    const float ReliefSignal = FMath::Pow(
        FMath::Clamp(
            Broad * 0.38f + Detail * 0.34f + DrainageShoulder * 0.28f,
            0.0f, 1.0f),
        0.82f);
    const float SlopeAlpha = FMath::SmoothStep(0.02f, 0.40f, SourceSlope);
    const float ReliefAmplitudeCm = FMath::Lerp(52.0f, 74.0f, SlopeAlpha);
    Sample.VerticalDisplacementCm = FMath::Clamp(
        Sample.CombinedFade * (3.0f + ReliefAmplitudeCm * ReliefSignal),
        0.0f, MaximumDisplacementCm);
    Sample.bEligible = Sample.VerticalDisplacementCm > 0.5f;
    return Sample;
}

TSharedRef<FJsonObject> BuildSouthForkBankMicroreliefManifest()
{
    TSharedRef<FJsonObject> Manifest = MakeShared<FJsonObject>();
    Manifest->SetStringField(
        TEXT("algorithm"),
        TEXT("source_registered_world_space_multiscale_dry_bank_microrelief_v1"));
    Manifest->SetStringField(
        TEXT("authority"),
        TEXT("visual-only procedural completion over authoritative terrain; no collision, navigation, wetness, hydraulics, bathymetry, buoyancy, or raft-force authority"));
    Manifest->SetNumberField(TEXT("presentation_spacing_m"), 2.0);
    Manifest->SetNumberField(TEXT("source_spacing_m"), 4.0);
    Manifest->SetNumberField(TEXT("minimum_bank_distance_m"), MinimumBankDistanceM);
    Manifest->SetNumberField(TEXT("maximum_bank_distance_m"), MaximumBankDistanceM);
    Manifest->SetNumberField(TEXT("maximum_wet_mask"), MaximumWetMask);
    Manifest->SetNumberField(TEXT("maximum_source_slope"), MaximumSourceSlope);
    Manifest->SetNumberField(
        TEXT("maximum_vertical_displacement_cm"), MaximumDisplacementCm);
    Manifest->SetNumberField(
        TEXT("full_patch_edge_fade_distance_m"), FullPatchEdgeDistanceM);
    Manifest->SetBoolField(TEXT("world_space_phase_continuity"), true);
    Manifest->SetBoolField(TEXT("wet_cells_emitted"), false);
    Manifest->SetBoolField(TEXT("affects_gameplay_collision"), false);
    Manifest->SetBoolField(TEXT("affects_hydraulics"), false);
    return Manifest;
}
} // namespace RaftSimEditorEnvironment
