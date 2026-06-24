# SmokeEmIfYouGotEm Simulator Concept

## Elevator Pitch

SmokeEmIfYouGotEm is a photo-realistic, physically accurate 3D white water rafting simulator built in Unreal Engine with first-class VR support. The player takes the role of the river guide seated in the back of the boat, reading rapids from a first-person perspective, steering a raft through dangerous currents, giving paddle commands, managing passenger safety, and chasing clean lines through increasingly technical river sections.

The initial camera goal is first-person from the guide's stern position in both VR and flat-screen play: low and physical enough to feel the raft buck under the player, but readable enough to judge current, obstacles, eddies, waves, passenger timing, and raft angle before each decision matters.

## Core Fantasy

The simulator should make the player feel like a skilled guide threading a raft through controlled chaos. The best moments should come from spotting the right line early, setting the raft angle, calling the right paddle rhythm, and barely sliding past a rock or hydraulic with everyone still aboard.

## Simulation North Star

The project should prioritize realism over arcade readability whenever the two conflict, then solve readability through better first-person cues, training tools, and environment design.

Core simulation goals:

- Photo-real river canyons, water, raft materials, paddles, spray, lighting, and weather
- Physically grounded raft buoyancy, drag, collision response, flex, and passenger weight transfer
- Water behavior that represents current, eddies, standing waves, hydraulics, holes, pour-overs, and turbulent seams
- Paddle strokes that produce plausible force and torque based on blade position, angle, depth, and timing
- VR presence that makes the player feel seated in the stern, holding a paddle, calling commands, and reacting with their body
- Training-grade feedback that explains why the raft moved, flipped, pinned, surfed, or missed a line

## First Technical Milestone

The first implementation milestone is not Unreal, rendering, or VR. It is a headless Python physics engine that can model a rubber raft moving across dynamic white water features.

The physics engine should simulate:

- A raft body moving over a 2.5D river surface and velocity field
- Buoyancy, drag, lift, added mass, and paddle impulses
- Rocks with impact, deflection, friction, and pinning behavior
- Standing waves that act as energy barriers
- Eddy lines that apply lateral shear and yaw torque
- Upwellings and low-damping turbulent surface regions
- Telemetry for every major force contribution

See [Physics Engine Plan](physics-engine-plan.md) for the detailed implementation strategy.

## Target Platforms

The shipped simulator should be designed as a multi-platform Unreal Engine product, with VR as a core design constraint rather than an optional late port. The first implementation work still starts in Python so the physics model can be validated before rendering and input complexity are added.

Primary targets:

- Windows PC flat-screen
- PC VR through OpenXR-compatible headsets
- macOS flat-screen
- Linux / Steam Deck flat-screen

Future targets:

- PlayStation and PlayStation VR2, if platform access and performance budgets allow
- Xbox
- Nintendo hardware, if performance and certification constraints are realistic
- High-end cloud streaming builds
- Standalone VR headsets only if physics, water, and visual quality can survive the performance budget

Possible later experiment:

- Mobile or tablet, only if the controls can be simplified without weakening the core simulator

## First-Person Camera And View

Initial prototype camera:

- First-person camera anchored to the guide position at the back of the raft
- Player can freely look left, right, forward, and slightly behind without losing the sense of being seated in the boat
- Camera motion should communicate raft hits, drops, and waves without causing discomfort
- The guide's paddle, hands, nearby passengers, raft tubes, and bow should remain visible as grounding references
- Optional quick-look or lean actions can help players check obstacles and passenger state without needing a third-person view
- VR uses tracked head pose with comfort options for motion intensity, horizon stabilization, vignette, and seated recentering
- Flat-screen mode uses mouse/gamepad look while preserving the same stern guide viewpoint

Design goals:

- Read river flow from inside the boat before entering a rapid
- See raft angle through the bow direction, passenger positions, paddle timing, and nearby hazards
- Make water height, splash, foam, and rocks feel close and dangerous without hiding gameplay-critical information
- Avoid motion sickness from camera shake, forced rotation, or overcorrection
- Preserve downstream visibility even when passengers, spray, or the raft bow fill the frame

## Player Role

The player is not the entire raft. The player is the guide.

Primary responsibilities:

- Choose the line through each rapid
- Control raft angle and steering
- Call paddle commands to the crew
- React to hazards, passengers falling out, stuck rafts, and changing river conditions
- Balance safety, speed, style, and score
- In VR, physically perform guide strokes and rescue gestures when hardware allows

## Core Gameplay Loop

1. Read the next river feature from the guide's first-person seat in the stern.
2. Position the raft before the rapid.
3. Call paddle commands and use physically modeled guide strokes to enter the line.
4. Adjust in real time as current, waves, rocks, paddle blade forces, raft flex, and crew timing affect the raft.
5. Recover from mistakes or capitalize on clean execution.
6. Finish the section and receive feedback on safety, line choice, physical efficiency, control, and style.
7. Review telemetry, improve technique, upgrade gear, or unlock harder river routes.

## Raft Controls

First prototype controls should support VR motion controllers, mouse and keyboard, and gamepad without changing the core stern-guide role.

Possible guide inputs:

- Forward paddle command
- Back paddle command
- Left side paddle
- Right side paddle
- Hard left / hard right guide stroke
- Hold on / brace command
- Rescue command when a passenger falls out
- VR paddle grip, blade angle, stroke depth, and pull path
- Flat-screen analog paddle stroke controls for non-VR play

The player should feel like they are commanding a crew rather than directly moving a vehicle through abstract input. The raft can still be responsive, but the response should come through paddle force, water current, and raft momentum.

The first-person view should make inputs feel like physical guide actions. Paddle strokes, command calls, brace warnings, and rescue actions should be readable through the player's hands, paddle, voice, and the crew's response.

## River Systems

The river is the main level design language.

Prototype systems:

- Headless Python simulation before Unreal integration
- 2.5D river field with surface height, velocity, shear, upwelling, damping, and feature tags
- Sampled raft hull/contact points for force accumulation
- Directional current fields, eddy lines, standing waves, holes, pour-overs, eddies, and calm pools
- Rock contact, deflection, pinning, and rubber contact softness
- Recorded telemetry for current velocity, raft velocity, paddle impulse, hull forces, collisions, and passenger events

Longer-term systems:

- Unreal visualization driven by validated simulation output
- Procedural rapid generation from authored river chunks
- Dynamic water levels
- Weather and visibility changes
- River difficulty classes inspired by real white water ratings
- Rescue scenarios and guide certification challenges
- Validation against reference footage, guide feedback, and measured river behavior when available

## Physical Accuracy

The raft should behave like a real inflatable raft within the limits of real-time simulation. The first draft can use simplified Python models, but every simplification should be chosen deliberately, documented, and tested against the physical behavior the simulator is trying to approximate.

Prototype physics priorities:

- Current applies spatially varying force to the raft hull, tubes, passengers, and paddle blades
- Paddle strokes add directional force and torque based on blade interaction with water
- Rocks deflect, pin, slow, or flip the raft based on contact point, velocity, current, and raft angle
- Waves can lift, shove, surf, swamp, or spin the raft
- Passenger weight distribution changes trim, stability, and recovery behavior
- Raft material properties represent buoyancy, drag, flex, friction, and collision softness
- Every major force has debug visualization and telemetry for tuning and validation
- The initial raft can be rigid, but the architecture must support later XPBD-style compliant tubes and floor constraints

## Passengers And Crew

Passengers should be readable from the guide's seat as expressive crew members in front of the player.

First draft behaviors:

- Paddle when commanded
- Brace when warned
- Panic or miss strokes when trust is low
- Fall out after heavy impacts or bad wave hits
- Require rescue before the score or safety rating collapses

Crew trust can become a core progression system. Clean guiding builds trust; repeated bad calls make passengers slower, more scared, and more likely to fail under pressure.

## Modes

Prototype mode:

- Single rapid time trial with safety scoring

Early simulator modes:

- River run campaign
- Challenge rapids
- Training school
- Daily generated rapid

Possible later modes:

- Co-op raft crew
- Asynchronous leaderboard runs
- Custom river editor
- Guide career mode

## Progression

Progression should reward mastery more than grind.

Possible progression tracks:

- Guide skill unlocks
- Raft types and handling tradeoffs
- Crew trust and passenger archetypes
- River permits / route unlocks
- Cosmetic raft, helmet, paddle, and outfitter gear

## Tone

The simulator should feel energetic, outdoorsy, risky, and a little scrappy. It should respect real river guiding while still being playable and readable.

Visual direction:

- Photo-real river environments based on real canyon, forest, desert, and mountain reference
- Clear diegetic water direction indicators through foam lines, bubbles, surface streaks, waves, and debris
- Physically plausible materials for raft rubber, wet rock, water, spray, foam, ropes, helmets, PFDs, and paddles
- Strong silhouettes for rocks, raft, waves, and hazards without stylizing away realism
- Minimal first-person UI inspired by guide maps, safety checklists, and river notes
- Visible raft bow, tubes, paddle, hands, and passenger silhouettes to ground the player in the stern
- Realistic exposure, reflections, shadows, mist, splash particles, and wetness effects

Audio direction:

- Loud water near hazards
- Paddle thumps and raft rubber creaks
- Guide calls with short, punchy voice lines
- Passenger reactions that communicate risk without becoming noise
- Spatial audio for VR so current, impacts, passengers, and rescue cues are locatable

## Unreal Engine Direction

Recommended starting approach:

- Headless Python physics engine first, with Unreal consuming validated simulation behavior later
- Unreal Engine 5.x project
- C++ core systems with Blueprint-facing tuning where useful
- OpenXR-based VR support with flat-screen input parity
- Enhanced Input for VR controllers, keyboard, mouse, and gamepad
- Common UI or a similarly portable UI approach for multi-platform menus
- World Partition only when the river scope grows large enough to need it
- Data assets for river sections, hazards, raft tuning, water tuning, paddle forces, and scoring rules
- High-fidelity lighting, material, terrain, water, and particle pipelines aimed at photo-realism
- Debug modes for force vectors, current fields, collision impulses, and raft stability metrics

Prototype scenario:

- One headless Python standing-wave test
- One rigid raft with sampled hull forces
- One eddy-line test with measurable yaw torque
- One rock contact test with deflection and pinning detection
- One telemetry output showing water, hull, paddle, and collision force components
- Later Unreal visualization, VR input, scoring, restart, first-person look controls, and VR recenter controls

## Open Questions

- What measurable accuracy targets define "physically accurate" for the first vertical slice?
- Which physics features must be validated in Python before Unreal integration starts?
- Should passengers be individual characters with traits, or mostly a visual representation of crew state?
- Should flat-screen raft control be direct, command-based, or a hybrid while VR remains physical?
- How much should the first-person camera prioritize downstream planning versus close physical impact?
- Should there be any optional third-person or scout camera, or should the simulator stay fully committed to the guide's viewpoint?
- Which VR headsets are required for the first public build?
- Is the long-term fantasy a professional-grade simulator, a consumer outdoor sports sim, or both?
