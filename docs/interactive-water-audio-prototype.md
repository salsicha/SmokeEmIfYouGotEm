# Interactive Water Audio Prototype

The first interactive audio prototype should be Unreal-native and MetaSounds-driven. It uses `RaftSimAudio::BuildWaterAudioParameters` as the bridge between simulation telemetry and audio controls.

## Prototype Layers

- River roar: looping recorded bed controlled by flow speed.
- Nearby rapid features: crossfaded hydraulic, standing wave, hole, and eddy-line recordings controlled by aeration and turbulence.
- Spray and foam: granular near-field variation driven by local aeration.
- Paddle catch: one-shot variation pool driven by paddle impulse.
- Raft scrape and rock impact: contact loops and impact one-shots driven by Chrono collision telemetry.
- Weather: rain, wind, spray wash, and wet-gear detail controlled by weather wetness.
- Canyon reflections: send-level control driven by enclosure and river loudness.
- Crew voice layering: ducking, priority, and intelligibility control driven by crew voice activity.

## Data Contract

The C++ bridge exposes normalized layer values for MetaSound graphs:

- `RiverRoar`
- `RapidFeatureIntensity`
- `SprayAndFoam`
- `ImpactLayer`
- `PaddleLayer`
- `ScrapeLayer`
- `WeatherLayer`
- `CanyonReflection`
- `CrewVoiceDuckAmount`

The canonical Unreal-facing manifest is `unreal/Content/RaftSim/Audio/interactive_water_audio_prototype.json`.

## Middleware Gate

FMOD or Wwise should only be evaluated if MetaSounds and Unreal Audio Mixer cannot support the needed authoring workflow, profiling visibility, memory control, localization pipeline, or platform routing.
