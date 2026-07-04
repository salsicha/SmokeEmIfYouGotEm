# Unreal Physics Authority

The raft and river physics are not authored as Unreal Chaos gameplay physics.

## Authoritative Systems

- Custom C++ shallow-water solver owns water state.
- `CustomReducedRigidBody` owns first vertical-slice raft kinematics, contact impulses, rock impacts, bed grounding, and paddle-force transfer as the fallback selected by the Milestone 19 authority report.
- Unreal consumes fixed-step states for rendering, VR camera motion, audio/VFX cues, debug overlays, replay, and UI.

The current plan is a split/hybrid evaluation with a fallback authority choice. Chaos is the default Unreal-integrated path for visual and non-authoritative physics. Jolt is the leading portable candidate for a narrow authoritative raft/contact/swimmer gameplay island. `CustomReducedRigidBody` is selected for the first vertical slice until measured Chaos/Jolt fixture telemetry allows either candidate to replace it. Chrono remains a high-fidelity reference/research path. See [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md).

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

## Custom Reduced Fallback

`CustomReducedRigidBody` is the selected first vertical-slice raft/contact/swimmer authority because the Milestone 19 comparison report currently blocks Chaos or Jolt selection pending measured runtime telemetry.

The fallback may be replaced only after:

- Unreal Chaos automation fixtures are run with measured telemetry.
- The native Jolt SDK/plugin harness is run with measured telemetry.
- The Chaos-vs-Jolt comparison report allows scoring-critical authority selection.
