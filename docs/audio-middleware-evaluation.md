# Audio Middleware Evaluation

As of June 28, 2026, RaftSim should stay Unreal-native for the first full audio implementation: Unreal Audio Mixer, MetaSounds, attenuation, source effects, submixes, AudioLink where useful, and the debug/profiling tools already planned in this repo.

## Sources Checked

- Epic MetaSounds documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-in-unreal-engine
- Epic Audio Mixer overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-mixer-overview-in-unreal-engine
- FMOD Unreal integration documentation: https://www.fmod.com/docs/2.03/unreal/welcome.html
- Wwise Unreal integration documentation: https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?id=index.html&source=UE4

## Decision

Do not integrate FMOD or Wwise yet. Use Unreal-native audio until a measured production problem appears.

## Why Unreal-Native First

- It keeps the UE5 prototype small and avoids a second authoring/runtime stack while physics, VR, networking, and river content are still changing.
- MetaSounds can cover the first interactive river prototype: river roar, nearby rapids, spray, foam, paddle catch, raft scrape, rock impact, weather, canyon reflections, and crew voice ducking.
- Audio Mixer gives us cross-platform rendering, submix routing, source effects, occlusion/filtering, procedural sources, and runtime profiling hooks without middleware licensing decisions.
- The current repo already defines C++ telemetry, spatial presets, debug data, storage rules, and validation matrices for Unreal-native implementation.

## When To Evaluate Middleware

Evaluate Wwise and FMOD only if Unreal-native audio fails a concrete requirement in one of these categories:

- Authoring: sound designers cannot build or maintain the required river behavior efficiently in MetaSounds.
- Mixing: large dynamic mixes, state transitions, or voice-priority workflows become brittle.
- Localization: dialogue, crew chatter, guide commands, or future language packs need a more mature audio localization pipeline.
- Memory: platform budgets require soundbank-style streaming, compression, or memory tooling beyond our Unreal workflow.
- Platform workflow: console, VR, or multiplayer voice requirements need middleware support that is faster or safer than custom Unreal work.
- Profiling: Unreal tools cannot expose enough runtime cost, voice, streaming, or bus-level detail for whitewater scenes.

## Fallback Ranking

1. Wwise: best candidate for a large production audio pipeline, complex state systems, localization, soundbank workflows, and mature authoring/profiling.
2. FMOD: strong candidate for a smaller team that wants fast designer iteration, event authoring, and broad Unreal platform support with a lighter authoring mental model.
3. Stay Unreal-native: preferred until one of the middleware gates is proven by profiling or production workflow friction.

## Evaluation Deliverable

If a gate triggers, build one rapid-scene audio slice three ways: Unreal-native MetaSounds, Wwise, and FMOD. Compare authoring time, runtime cost, memory footprint, VR spatial quality, multiplayer voice routing, localization workflow, build complexity, license cost, and team maintainability.
