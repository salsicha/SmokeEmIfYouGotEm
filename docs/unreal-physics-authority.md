# Unreal Physics Authority

The raft and river physics are not authored as Unreal Chaos gameplay physics.

## Authoritative Systems

- Custom C++ shallow-water solver owns water state.
- Project Chrono/custom raft runtime owns raft kinematics, contact impulses, rock impacts, bed grounding, and paddle-force transfer.
- Unreal consumes fixed-step states for rendering, VR camera motion, audio/VFX cues, debug overlays, replay, and UI.

## Chaos Policy

Unreal Chaos may be used for:

- Visual splash debris.
- Loose props that do not affect raft outcome.
- Background ropes, paddles, gear, and shore clutter.
- Non-authoritative breakables or incidental set dressing.

Chaos must not own:

- The raft transform.
- Raft/rock collision response.
- Raft/riverbed grounding.
- Water force integration.
- Scoring-critical passenger or rescue outcomes.

Any Chaos object that affects gameplay must emit an intent or hazard event into the authoritative bridge instead of directly moving the raft.
