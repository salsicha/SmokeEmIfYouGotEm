# Alpha Systems Progression Plan

Milestone 24 adds a single tuning catalog for raft handling, passenger archetypes, crew progression, training lessons, challenge variants, and generated-rapid experiments:

- `unreal/Content/RaftSim/Raft/alpha_systems_progression_catalog.json`
- `URaftSimAlphaSystemsConfig`

The catalog is designer-facing, but it is not a shortcut around validation. Raft profiles and challenge variants must reference validated water, raft-contact, crew-weight, rescue, pin/release, flip, and generated-feature reports before they become playable content.

## Raft And Handling Profiles

Alpha tuning starts with these raft profiles:

- `standard_14ft_paddle_raft`: baseline guided paddle raft for South Fork and general training.
- `technical_13ft_paddle_raft`: quicker and less stable, intended for boulder gardens and tight ferries.
- `heavier_training_raft`: forgiving for first lessons, but slower to correct and more punishing if pinned.
- `sixteen_foot_oar_rig`: Colorado-style manual oar rig with large-volume momentum and longer rescue setup.
- `loaded_expedition_paddle_raft`: heavier paddle raft for Pacuare-style expedition/load tradeoffs.

Every profile records mass, dimensions, stability, maneuverability, momentum retention, gameplay tradeoffs, and the validation fixtures that must cover it. Tuning values are gameplay starting points, not solver authority.

## Passenger And Crew Progression

Passenger archetypes carry trust, fear, fatigue, skill, and gameplay traits. Progression rules update those values through validated run events such as clean lines, late commands, rescues, failed rescues, and scout/debrief moments.

The deterministic command and safety systems remain authoritative. AI dialogue can read trust, fear, fatigue, and skill, but it cannot override paddle, brace, high-side, rescue, or recovery commands.

## Lessons And Challenges

Training lessons are tied to a river, required systems, and completion telemetry. Early lessons cover:

- Forward/stop/brace on the South Fork.
- Eddy, scout, and recovery-pool work on the South Fork.
- Pull/back-row/lateral timing on the Colorado rowing route.
- Rain-fed flow and bank-hazard review for Pacuare.

Challenge variants must declare scoring axes and allowed rivers. They stay blocked unless the relevant water, raft, swimmer, and source-provenance fixtures are passing.

## Generated Rapids

Generated-rapid experiments are allowed only as validation-backed studies. The first experiments cover wave-train shuffles, boulder-garden seeds, and rain-fed bank-hazard studies. All are non-playable until the required reports pass; this keeps procedural variety from hiding conservation, coupling, source-rights, or guide-review failures.
