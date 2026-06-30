# Unreal Physics Authority

The raft and river physics are not authored as Unreal Chaos gameplay physics.

## Authoritative Systems

- Custom C++ shallow-water solver owns water state.
- A selected raft/contact runtime owns raft kinematics, contact impulses, rock impacts, bed grounding, and paddle-force transfer only after passing the Chaos/Jolt shared fixture suite.
- Unreal consumes fixed-step states for rendering, VR camera motion, audio/VFX cues, debug overlays, replay, and UI.

The current plan is a split/hybrid evaluation. Chaos is the default Unreal-integrated path for visual and non-authoritative physics. Jolt is the leading portable candidate for a narrow authoritative raft/contact/swimmer gameplay island. Chrono remains a high-fidelity reference/research path. See [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md).

## Chaos Policy

Unreal Chaos may be used by default for:

- Visual splash debris.
- Loose props that do not affect raft outcome.
- Background ropes, paddles, gear, and shore clutter.
- Non-authoritative breakables or incidental set dressing.
- Visual crew ragdolls and physical animation when gameplay state is owned by the deterministic bridge.

Chaos must not own these scoring-critical systems until it passes the same evaluation fixtures as Jolt:

- The raft transform.
- Raft/rock collision response.
- Raft/riverbed grounding.
- Water force integration.
- Scoring-critical passenger or rescue outcomes.

Any Chaos object that affects gameplay must emit an intent or hazard event into the authoritative bridge instead of directly moving the raft.

## Jolt Candidate Policy

Jolt may become the authoritative raft/contact/swimmer gameplay island only if it passes:

- Raft-rock angle sweep.
- Shallow shelf grounding.
- Pin/release wrap proxy.
- Crew ejection to swimmer transition.
- 1000-step fixed replay determinism.
- Crowded runtime-cost fixture with one raft, eight crew, fifty rocks, and twenty loose props.

Jolt must consume the same custom-water query API and emit the same telemetry/replay schema as Chaos and the reduced custom runtime.
