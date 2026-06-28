# Spatial Audio Debug Tools

Spatial audio needs debug visibility because failures are often invisible in the level viewport. The initial tooling contract should expose enough data for an editor overlay, a runtime VR-safe debug view, and automated capture logs.

## Debug Surfaces

- Emitter overlay: world position, preset id, attenuation radius, and source spread.
- Occlusion view: listener-to-source trace, blocked state, hit distance, and low-pass state.
- Reverb view: send level, active reverb zone, and canyon/shore transition state.
- Ambisonic view: bed id, rotation, order, and head-tracking status.
- Voice view: active voices, virtualized voices, priority, and bus routing.
- Runtime cost view: audio render cost, spatialization cost, and expensive emitters.

## Data Contract

`FRaftSimSpatialAudioDebugEmitterState` captures per-source state. `FRaftSimSpatialAudioDebugFrame` captures the per-frame summary for HUDs, captures, and validation runs.

The canonical debug manifest is `unreal/Content/RaftSim/Audio/spatial_audio_debug_tools.json`.
