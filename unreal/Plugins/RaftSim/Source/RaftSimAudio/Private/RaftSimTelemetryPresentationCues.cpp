#include "RaftSimTelemetryPresentationCues.h"

namespace
{
float Clamp01(const float Value)
{
    return FMath::Clamp(Value, 0.0f, 1.0f);
}
}

FRaftSimTelemetryPresentationCueFrame URaftSimTelemetryPresentationCueLibrary::BuildPresentationCues(
    const FRaftSimPresentationTelemetrySample& Telemetry)
{
    const float Depth = Clamp01(Telemetry.WaterDepthMeters / 2.0f);
    const float Velocity = Clamp01(Telemetry.FlowSpeedMetersPerSecond / 6.0f);
    const float Froude = Clamp01(Telemetry.FroudeNumber / 1.6f);
    const float Aeration = Clamp01(Telemetry.Aeration);
    const float Turbulence = Clamp01(Telemetry.Turbulence);
    const float SurfaceShear = Clamp01(Telemetry.SurfaceShear);
    const float Wetness = Clamp01(Telemetry.Wetness);
    const float ContactImpulse = Clamp01(Telemetry.RaftContactImpulse / 2500.0f);
    const float ContactEnergy = FMath::Max(ContactImpulse, Clamp01(Telemetry.RockScrapeStrength));
    const float PaddleEnergy = Clamp01((Telemetry.PaddleCatchStrength * 0.7f) + (Telemetry.PaddleBladeDepth * 0.3f));
    const float Weather = Clamp01(Telemetry.WeatherWetness);
    const float Canyon = Clamp01(Telemetry.CanyonEnclosure);
    const float ReverbZone = Clamp01(Telemetry.ReverbZoneStrength);
    const float Occlusion = Clamp01(Telemetry.OcclusionStrength);
    const float Hazard = Clamp01(Telemetry.HazardProximity);
    const float BoatSubmersion = Clamp01(Telemetry.BoatSubmersion);
    const float Rescue = Clamp01((Telemetry.SwimmerUrgency * 0.55f) + (Telemetry.SwimmerVisibility * 0.25f) +
                                 (Telemetry.RescueInteraction * 0.2f));
    const float RapidEnergy = Clamp01((Velocity * 0.25f) + (Froude * 0.3f) + (Aeration * 0.25f) +
                                      (Turbulence * 0.2f));

    FRaftSimTelemetryPresentationCueFrame Frame;

    Frame.Visuals.FoamAmount = Clamp01((Aeration * 0.6f) + (Turbulence * 0.25f) + (Froude * 0.15f));
    Frame.Visuals.SprayAmount = Clamp01((Aeration * 0.35f) + (Turbulence * 0.25f) + (Froude * 0.3f) +
                                        (Weather * 0.1f));
    Frame.Visuals.WetRockAmount = Clamp01((Wetness * 0.55f) + (Weather * 0.25f) +
                                          (Frame.Visuals.SprayAmount * 0.2f));
    Frame.Visuals.SurfaceStreakAmount = Clamp01((Velocity * 0.45f) + (SurfaceShear * 0.35f) +
                                                (Turbulence * 0.2f));
    Frame.Visuals.AeratedWaterAmount = Clamp01((Aeration * 0.75f) + (Frame.Visuals.FoamAmount * 0.25f));
    Frame.Visuals.HazardContrast = Clamp01((Hazard * 0.5f) + (RapidEnergy * 0.3f) + (ContactEnergy * 0.2f));
    Frame.Visuals.RaftContactCue = ContactEnergy;
    Frame.Visuals.PaddleCue = PaddleEnergy;
    Frame.Visuals.WeatherCue = Weather;
    Frame.Visuals.RescueCue = Rescue;
    Frame.Visuals.WaterReadability = Clamp01((Frame.Visuals.SurfaceStreakAmount * 0.35f) +
                                             (Frame.Visuals.FoamAmount * 0.25f) +
                                             (Frame.Visuals.HazardContrast * 0.25f) +
                                             ((1.0f - Depth) * 0.15f));
    Frame.Visuals.DebugContrast = Clamp01((Frame.Visuals.HazardContrast * 0.45f) +
                                          (Frame.Visuals.WaterReadability * 0.35f) +
                                          (Frame.Visuals.RescueCue * 0.2f));

    Frame.Audio.RiverBed = Clamp01((Velocity * 0.55f) + (Depth * 0.2f) + (Turbulence * 0.25f));
    Frame.Audio.LargeRapid = RapidEnergy;
    Frame.Audio.NearWaterDetail = Clamp01((Frame.Visuals.FoamAmount * 0.35f) +
                                          (Frame.Visuals.SprayAmount * 0.35f) + (BoatSubmersion * 0.3f));
    Frame.Audio.RaftContact = Frame.Visuals.RaftContactCue;
    Frame.Audio.Paddle = Frame.Visuals.PaddleCue;
    Frame.Audio.Weather = Weather;
    Frame.Audio.AmbisonicBed = Clamp01((Canyon * 0.45f) + (Weather * 0.2f) + (Frame.Audio.RiverBed * 0.35f));
    Frame.Audio.ReverbSend = Clamp01((ReverbZone * 0.5f) + (Canyon * 0.35f) + (Weather * 0.15f));
    Frame.Audio.OcclusionAmount = Occlusion;
    Frame.Audio.RescueCallout = Rescue;
    Frame.Audio.UnderwaterNearWater = Clamp01((BoatSubmersion * 0.65f) + (Rescue * 0.2f) +
                                              ((1.0f - Depth) * 0.15f));

    if (Frame.Visuals.RescueCue > 0.45f)
    {
        Frame.PrimaryCue = TEXT("rescue");
    }
    else if (Frame.Visuals.RaftContactCue > 0.5f)
    {
        Frame.PrimaryCue = TEXT("raft_contact");
    }
    else if (Frame.Visuals.PaddleCue > 0.5f)
    {
        Frame.PrimaryCue = TEXT("paddle");
    }
    else if (RapidEnergy > 0.55f)
    {
        Frame.PrimaryCue = TEXT("rapid");
    }

    return Frame;
}
