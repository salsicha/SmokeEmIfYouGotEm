# Local AI Crew Conversation Plan

Milestone 24 expands crew conversation with a local bark catalog:

- `unreal/Content/RaftSim/AI/crew_conversation_bark_catalog.json`
- `URaftSimCrewConversationCatalog`

The catalog covers calm water, eddies, scouting, recovery pools, swims, rescues, and debriefs. It is meant for local selection or generation support, not for gameplay authority.

## Priority Rules

Conversation uses four priority lanes:

- `deterministic_command_ack`: explicit acknowledgments from guide command routing.
- `safety_bark`: swimmer, hazard, hold-on, brace, high-side, and rescue cues from deterministic safety state.
- `rapid_short_bark`: very short emotion or effort barks that can play during rapids without masking commands.
- `ambient_conversation`: calm-water, eddy, scout, recovery-pool, and debrief chatter.

Command acknowledgments and safety barks can interrupt lower-priority dialogue. Ambient chatter is blocked during unresolved rescue and must duck under command audio.

## State Coverage

The first bark bank covers:

- Calm water: confidence, river reading, reassurance.
- Eddies: reset, readiness, fatigue, next-rapid anticipation.
- Scouting: line confirmation and hazard summary.
- Recovery pools: relief, fatigue, trust repair.
- Swims: non-swimmer priority and visible-swimmer callouts.
- Rescues: throw-line readiness and pull-in progress.
- Debriefs: successful lines and failed-rescue reflection.

## Determinism Boundary

Local AI can choose or lightly vary non-critical lines using persona, trust, fear, fatigue, skill, river state, recent events, and weather. It cannot create command intents, override the command router, hide safety telemetry, or delay rescue/control audio.
