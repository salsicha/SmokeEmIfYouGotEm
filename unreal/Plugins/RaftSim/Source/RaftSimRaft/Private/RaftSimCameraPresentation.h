#pragma once

#include "Camera/CameraComponent.h"

namespace RaftSimCameraPresentation
{

/**
 * Apply the shipping South Fork photographic response to a runtime camera.
 *
 * A fixed manual exposure keeps repeatable rapid framing while bounded local
 * exposure compresses wet highlights and recovers shadowed faces. This is
 * presentation-only and does not affect weather, water, or raft simulation
 * state.
 */
inline void Configure(UCameraComponent* Camera, float ExposureBias = 1.25f)
{
    if (Camera == nullptr)
    {
        return;
    }

    FPostProcessSettings& Settings = Camera->PostProcessSettings;
    Settings.bOverride_AutoExposureMethod = true;
    Settings.AutoExposureMethod = AEM_Manual;
    Settings.bOverride_AutoExposureBias = true;
    Settings.AutoExposureBias = ExposureBias;
    Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
    Settings.AutoExposureApplyPhysicalCameraExposure = 0;

    Settings.bOverride_LocalExposureMethod = true;
    Settings.LocalExposureMethod = ELocalExposureMethod::Bilateral;
    Settings.bOverride_LocalExposureHighlightContrastScale = true;
    Settings.LocalExposureHighlightContrastScale = 0.78f;
    Settings.bOverride_LocalExposureShadowContrastScale = true;
    Settings.LocalExposureShadowContrastScale = 0.72f;
    Settings.bOverride_LocalExposureDetailStrength = true;
    Settings.LocalExposureDetailStrength = 1.0f;
    Settings.bOverride_LocalExposureBlurredLuminanceBlend = true;
    Settings.LocalExposureBlurredLuminanceBlend = 0.50f;
    Settings.bOverride_LocalExposureBlurredLuminanceKernelSizePercent = true;
    Settings.LocalExposureBlurredLuminanceKernelSizePercent = 50.0f;

    Settings.bOverride_ColorSaturation = true;
    Settings.ColorSaturation = FVector4(1.03f, 1.03f, 1.03f, 1.0f);
    Settings.bOverride_ColorContrast = true;
    Settings.ColorContrast = FVector4(1.04f, 1.04f, 1.04f, 1.0f);
    Settings.bOverride_Sharpen = true;
    Settings.Sharpen = 0.18f;
    Settings.bOverride_VignetteIntensity = true;
    Settings.VignetteIntensity = 0.04f;
    Settings.bOverride_FilmGrainIntensity = true;
    Settings.FilmGrainIntensity = 0.0f;
}

} // namespace RaftSimCameraPresentation
