#include "RaftSimWaterAudioParameters.h"

FRaftSimWaterAudioParameters RaftSimAudio::BuildWaterAudioParameters(const FRaftSimWaterAudioTelemetry& Telemetry)
{
    FRaftSimWaterAudioParameters Parameters;
    Parameters.RiverRoar = FMath::Clamp(Telemetry.FlowSpeedMetersPerSecond / 6.0f, 0.0f, 1.0f);
    Parameters.RapidFeatureIntensity = FMath::Clamp((Telemetry.Aeration + Telemetry.Turbulence) * 0.5f, 0.0f, 1.0f);
    Parameters.SprayAndFoam = FMath::Clamp(Telemetry.Aeration, 0.0f, 1.0f);
    Parameters.ImpactLayer = FMath::Clamp(Telemetry.RaftImpactImpulse / 2500.0f, 0.0f, 1.0f);
    Parameters.PaddleLayer = FMath::Clamp(Telemetry.PaddleCatchStrength, 0.0f, 1.0f);
    Parameters.ScrapeLayer = FMath::Clamp(Telemetry.RockScrapeStrength, 0.0f, 1.0f);
    Parameters.WeatherLayer = FMath::Clamp((Telemetry.WeatherWetness * 0.7f) + (Parameters.RiverRoar * 0.3f), 0.0f, 1.0f);
    Parameters.CanyonReflection = FMath::Clamp(Telemetry.CanyonEnclosure * (0.4f + Parameters.RiverRoar * 0.6f), 0.0f, 1.0f);
    Parameters.CrewVoiceDuckAmount = FMath::Clamp(Telemetry.CrewVoiceActivity * (0.35f + Parameters.RapidFeatureIntensity * 0.35f), 0.0f, 0.75f);
    return Parameters;
}
