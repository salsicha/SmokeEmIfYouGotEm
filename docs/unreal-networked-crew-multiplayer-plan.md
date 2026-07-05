# Unreal Networked Crew Multiplayer Plan

## Gate

Networked human crew play starts after the single-player guide loop, authoritative physics bridge, local voice-command path, rescue loop, and AI crew fallback systems are stable enough to replay and debug. Milestone 24 makes that gate explicit in `unreal/Content/RaftSim/Network/networked_crew_evaluation_gate.json`.

The gate currently blocks human crew evaluation until these evidence artifacts are stable:

- Single-player guide loop: `unreal/Content/RaftSim/VerticalSlice/first_rapid_vertical_slice.json`.
- Raft/contact authority: `unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json`.
- Local voice/manual parity: `unreal/Content/RaftSim/AI/local_ai_runtime_manifest.json`.
- Rescue loop: `unreal/Content/RaftSim/Crew/swimmer_rescue_gameplay.json`.
- Replay/debug tools: `unreal/Content/RaftSim/Debug/debug_overlay_validation.json`.
- Mixed crew validation: `unreal/Content/RaftSim/Network/mixed_crew_validation.json`.

Until those pass, multiplayer work is limited to contract design and local lab planning. Internet play, relay sessions, and public playtests stay blocked.

## Architecture Decision

Use an authoritative host model for the first multiplayer playable after the evaluation gate opens:

- Primary first pass: listen server with the stern guide or lobby host owning authoritative fixed-step raft/water state.
- LAN/offline co-op: supported as a low-friction testing mode.
- Relay/session service: planned for internet play once account/session policy is chosen.
- Dedicated server: keep compatible with the contracts, but defer until physics budgets and replay tooling are proven.
- Rollback/prediction: limited to player inputs, paddle poses, brace/hold-on/rescue intents, and VR/controller smoothing; the raft transform remains authoritative.

## Human Crew

Every raft seat can be occupied by a human or an AI fallback. Seat assignment must be explicit, visible, and recoverable after disconnects.

Roles:

- Stern guide: command authority, route reading, voice commands, rescue calls, raft setup, and optional host authority.
- Bow paddlers: hazard callouts, paddle timing, rescue spotting, and line execution.
- Left/right paddlers: power, draw, brace, high-side, and recovery actions.
- Safety/rescue: throw rope, swimmer awareness, pull-in, and stabilize.
- Spectator/scout: optional non-raft observer for training, replay, or coaching.

## Replication Policy

Replicate deterministic inputs and intent events first, then replicate authoritative state for correction and debugging.

Replicated gameplay:

- Guide commands.
- Human paddle strokes and blade/controller poses.
- Brace, hold-on, high-side, rescue, and recovery actions.
- Crew animation state.
- Passenger/seat state.
- Raft contacts and hazard events.
- Scoring and outcome telemetry.

Authoritative raft/water physics should emit frame ids, hashes, and correction data so multiplayer replays can diagnose divergence.

## Voice Communication

Integrated boat voice supports push-to-talk and open-mic, mute, per-player volume, subtitles/transcription options, moderation hooks, and privacy settings. Voice should spatialize to raft seats when enabled, but gameplay-critical commands must retain manual input parity.

## Validation

Validate mixed desktop/VR crews, accessibility fallbacks, comfort settings, voice readability, latency, packet loss, reconnects, AI takeover, host migration/session recovery, scoring fairness, and replay/debug telemetry before internet play is considered shippable.
