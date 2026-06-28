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
- Playable real-world river sections built from geospatial terrain, hydrography, imagery, and seasonal flow data
- Physically grounded raft buoyancy, drag, collision response, flex, and passenger weight transfer
- Water behavior that represents current, eddies, standing waves, hydraulics, holes, pour-overs, and turbulent seams
- Paddle strokes that produce plausible force and torque based on blade position, angle, depth, and timing
- Local AI voice interaction so the guide can speak paddle, brace, rescue, and safety commands to the crew
- Crew conversation that reacts to river state, trust, fear, fatigue, skill, scenery, weather, and the guide's recent decisions
- VR presence that makes the player feel seated in the stern, holding a paddle, calling commands, and reacting with their body
- Fully immersive 3D audio that places rapids, hydraulics, rocks, raft contacts, crew, voice chat, rescue cues, weather, canyon reflections, and shore noise in stable world positions
- Training-grade feedback that explains why the raft moved, flipped, pinned, surfed, or missed a line

## First Technical Milestone

The first active implementation milestone is not Unreal, rendering, VR, or full 3D physics. It is a headless 2.5D dual-solver modeling system.

The first active physics slice should build:

- A deterministic 2.5D procedural scenario generator
- A GeoClaw shallow-water/geophysical-flow reference model
- A custom C++ reduced shallow-water / height-field solver
- A comparison and tuning harness that runs both solvers on the same scenario package
- A solver-neutral 6-DoF raft coupling layer for buoyancy, drag, grounding, wave climb, surf/flush, and paddle forces
- Telemetry for water fields, solver error, raft forces, and scenario outcomes

See [Physics Engine Plan](physics-engine-plan.md) for the detailed implementation strategy.
See [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md) and [GeoClaw Reference Solver Transition Plan](geoclaw-transition-plan.md) for the GeoClaw/C++ validation workflow.
See [Real-World River Content And Seasonal Flow Plan](real-world-river-content-plan.md) for the real river, geospatial, imagery, season, flow, difficulty, and Unreal photoreal content pipeline.
See [Free And AI Asset Policy](free-and-ai-asset-policy.md) for the current art and sound sourcing decision, and [Audio Asset Sourcing Plan](audio-asset-sourcing-plan.md) for audio-specific research notes.

## Full Engine Physics Runtime

Project Chrono is the planned authoritative physics runtime for the full Unreal Engine simulator. The Python `raftsim` package remains the research and validation harness, but the shipped game should use Chrono for raft dynamics, rock/contact response, compliant raft behavior, paddle force transfer, and fluid-solid interaction experiments.

Unreal should own rendering, VR input, audio, UI, asset streaming, and platform packaging. Chrono should own the physical raft state and expose transforms, contacts, force telemetry, and debug vectors back to Unreal.

See [Chrono And Unreal Integration Plan](chrono-unreal-integration.md) for the runtime architecture.
See [Unreal Engine Full Game Plan](unreal-engine-game-plan.md) for the production roadmap that begins after Python modeling, validation, and profiling are complete.

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
- Spoken commands through local speech recognition and constrained intent parsing
- Hard left / hard right guide stroke
- Hold on / brace command
- Rescue command when a passenger falls out
- VR paddle grip, blade angle, stroke depth, and pull path
- Flat-screen analog paddle stroke controls for non-VR play

The player should feel like they are commanding a crew rather than directly moving a vehicle through abstract input. The raft can still be responsive, but the response should come through paddle force, water current, and raft momentum.

The first-person view should make inputs feel like physical guide actions. Paddle strokes, command calls, brace warnings, and rescue actions should be readable through the player's hands, paddle, voice, and the crew's response.

Voice commands should be local/offline for privacy, latency, and platform control. Gameplay-critical commands should resolve to explicit deterministic intents before affecting the crew, with confidence thresholds, subtitles, accessibility fallbacks, and manual input parity.

## River Systems

The river is the main level design language.

Prototype systems:

- Headless Python simulation before Unreal integration
- 2.5D procedural and real-world scenario packages with bed, surface, depth, velocity, wet/dry state, features, source manifests, seasonal flow presets, and raft parameters
- GeoClaw reference simulation for shallow-water/geophysical-flow behavior
- Custom C++ reduced shallow-water / height-field solver tuned against GeoClaw
- Solver-neutral raft hull/contact sampling for buoyancy, drag, grounding, wave, hole, and paddle forces
- Recorded telemetry for water fields, solver comparison, raft forces, contacts, and passenger events

Longer-term systems:

- Unreal visualization driven by validated simulation output
- Real-world river course and elevation extraction from geospatial sources
- Rapid identification from aerial/satellite imagery, DEM gradient, constrictions, boulder gardens, foam/whitewater texture, and guide review
- User-selectable river, section, season, flow level, difficulty, and raft/crew setup
- Seasonal flow levels from gauge history, modeled flow, snowmelt/rain/reservoir context, and local references
- Adaptive fluid parameters driven by season, flow percentile, channel geometry, roughness, and selected difficulty
- Procedural rapid generation from authored or extracted river chunks
- Dynamic water levels tied to validated seasonal presets
- Weather and visibility changes
- River difficulty classes inspired by real white water ratings
- Rescue scenarios and guide certification challenges
- Validation against reference footage, guide feedback, and measured river behavior when available

## Physical Accuracy

The raft should behave like a real inflatable raft within the limits of real-time simulation. The active research model is 2.5D: GeoClaw provides the reference water behavior, and the custom C++ reduced solver is tuned to match it before becoming a runtime candidate.

Prototype physics priorities:

- Depth-averaged water fields apply spatially varying forces to hull sample points and paddle blades
- Paddle strokes add directional force and torque based on blade interaction with water
- Rocks deflect, pin, slow, or flip the raft based on contact point, velocity, current, and raft angle
- Waves can shove, lift, surf, stall, destabilize, or spin the raft in the 2.5D model
- Shallows, aerated patches, and eddy lines alter drag, damping, and steering authority
- Raft material properties initially represent drag, friction, collision softness, and pinning tendency
- Every major force has debug visualization and telemetry for tuning and validation
- The initial active raft model should be 6-DoF over 2.5D water and leave room for XPBD-style compliant tubes and floor constraints

## Passengers And Crew

Passengers should be readable from the guide's seat as expressive crew members in front of the player.

First draft behaviors:

- Paddle when commanded
- Brace when warned
- Panic or miss strokes when trust is low
- Fall out after heavy impacts or bad wave hits
- Require rescue before the score or safety rating collapses
- Respond to spoken guide commands with short acknowledgments, hesitation, confusion, or urgency based on command clarity and crew state
- Hold lightweight conversations in calm water, eddies, scouting moments, loading screens, and recovery pools
- Keep conversation short and functional inside active rapids so it never hides urgent river audio or command feedback

Crew trust can become a core progression system. Clean guiding builds trust; repeated bad calls make passengers slower, more scared, and more likely to fail under pressure.

The full UE5 version should include a local AI crew layer with passenger personas, relationship memory, fatigue, fear, competence, and river knowledge. The AI can generate or select conversation and reactions, but it should not directly override the deterministic command executor that drives paddle timing, bracing, rescue behavior, and safety-critical outcomes.

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

- Photo-real river environments based on real canyon, forest, desert, and mountain reference, with the highest-value sections grounded in geospatial course/elevation data
- Clear diegetic water direction indicators through foam lines, bubbles, surface streaks, waves, and debris
- Physically plausible materials for raft rubber, wet rock, water, spray, foam, ropes, helmets, PFDs, and paddles
- Strong silhouettes for rocks, raft, waves, and hazards without stylizing away realism
- Minimal first-person UI inspired by guide maps, safety checklists, and river notes
- Visible raft bow, tubes, paddle, hands, and passenger silhouettes to ground the player in the stern
- Realistic exposure, reflections, shadows, mist, splash particles, and wetness effects
- Latest stable UE5 photoreal rendering features where supported, including Nanite rocks/terrain detail, Nanite foliage, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara spray/foam, and advanced material layering

Audio direction:

- Loud water near hazards
- Paddle thumps and raft rubber creaks
- Guide calls with short, punchy voice lines
- Passenger reactions and conversations that communicate risk, morale, trust, fatigue, and personality without becoming noise
- Local speech recognition for guide commands with clear acknowledgments, misrecognition handling, and subtitle feedback
- 3D spatial audio for VR/headphones, stereo speakers, and surround so current, impacts, passengers, rescue cues, multiplayer voice, and hazards are locatable from the stern guide seat
- Binaural/HRTF playback for VR/headphones where supported, panning/surround playback for speaker setups, ambisonic beds for canyon/forest/storm/river ambience, and occlusion/reverb behavior for rocks, banks, raft tubes, and canyon walls
- Current development art and sound should use free/open, first-party generated, procedural, and AI-generated assets.
- Paid art packs, paid sound libraries, marketplace packs, and subscription asset services are deferred until the release-readiness gate decides whether free/open and AI-generated assets are good enough.
- AI-generated audio can support development water, raft, paddle, rock, weather, ambience, UI, temp dialogue, and non-critical variations, but shipping use still requires explicit legal/audio approval and provenance review.
- Every imported or generated sound should carry source, license, attribution, processing, and approval metadata.

## Unreal Engine Direction

The real Unreal Engine game project should start after the Python modeling and profiling gate is passed. Before then, Unreal work should be limited to disposable visual studies, reference scenes, material experiments, or telemetry playback prototypes that do not define the production architecture.

Recommended starting approach:

- Headless 2.5D GeoClaw reference model first, with a custom C++ reduced water solver tuned against it before Unreal runtime work
- Latest stable Unreal Engine 5.x project chosen at the readiness gate after re-checking current feature support
- Custom C++ reduced shallow-water / height-field solver as the primary runtime water candidate
- Project Chrono or custom C++ as the authoritative raft/contact runtime after the readiness report selects the split
- C++ core systems with Blueprint-facing tuning where useful
- OpenXR-based VR support with flat-screen input parity
- Enhanced Input for VR controllers, keyboard, mouse, and gamepad
- Local AI integration for voice commands, crew dialogue, passenger persona state, optional local speech synthesis, and privacy-preserving offline play
- Unreal-native audio and MetaSounds first for interactive water/raft/crew sound, 3D attenuation/spatialization, ambisonic ambience, reverb, occlusion, and voice-chat mix; evaluate Wwise/FMOD only if production needs outgrow the native toolchain
- Common UI or a similarly portable UI approach for multi-platform menus
- World Partition for long real-world river corridors once the content scope requires streaming
- Data assets for river sections, source manifests, gauges, seasons, flow levels, difficulty presets, hazards, raft tuning, water tuning, paddle forces, and scoring rules
- High-fidelity lighting, material, terrain, foliage, water, and particle pipelines aimed at photo-realism, including Nanite foliage and geospatial corridor import when practical
- Debug modes for Chrono force vectors, current fields, collision impulses, FSI state, and raft stability metrics

Prototype scenario:

- One generated 2.5D scenario package consumed by both GeoClaw and C++
- One GeoClaw reference run
- One custom C++ run tuned against the GeoClaw output
- One 6-DoF raft coupling test against both water outputs
- One telemetry output showing water fields, solver error, hull forces, paddle forces, and contact components
- One real-world river section scenario with source manifest, extracted terrain/course, rapid annotations, seasonal flow presets, and low/median/high runnable flow validation
- One audio source manifest and interactive water-audio prototype driven by solver telemetry
- One 3D audio validation pass for the guide-seat perspective, including rapids, hazards, crew positions, raft contacts, ambisonic ambience, occlusion/reverb changes, and VR/headphone localization
- Later Unreal visualization, VR input, local voice commands, AI crew dialogue, scoring, restart, first-person look controls, and VR recenter controls

## Open Questions

- What measurable accuracy targets define "physically accurate" for the first vertical slice?
- What GeoClaw-vs-C++ tolerances are acceptable for water fields and raft outcomes?
- Which physics features must be validated in GeoClaw and C++ before Unreal integration starts?
- Which Chrono modules and build configuration are required for each target platform?
- Which candidate rivers have the best combination of data quality, iconic white water, licensing clarity, and practical first-slice scope?
- How much rapid identification can be automated from terrain/imagery before manual river-domain review is required?
- Which gauge or modeled-flow sources are accurate enough for each selected river section and season?
- Should passengers be individual characters with traits, or mostly a visual representation of crew state?
- Which local AI runtime should power speech recognition, command parsing, crew conversation, and optional speech synthesis on each target platform?
- How strict should voice-command confidence be before the crew acts, especially in loud water and VR microphone conditions?
- How much crew conversation should be generated locally versus authored, recorded, or template-driven?
- Are free/open and AI-generated art and sound assets good enough for release, or do specific gaps justify buying professional libraries near release?
- Which binaural/HRTF plugin, ambisonic format, surround target, reverb/occlusion approach, and spatial-audio QA process are required for the first VR build?
- Which AI-generated audio use cases, if any, are allowed beyond development-only assets?
- Is Unreal-native audio/MetaSounds enough for full production, or does the project need Wwise/FMOD?
- Should flat-screen raft control be direct, command-based, or a hybrid while VR remains physical?
- How much should the first-person camera prioritize downstream planning versus close physical impact?
- Should there be any optional third-person or scout camera, or should the simulator stay fully committed to the guide's viewpoint?
- Which VR headsets are required for the first public build?
- Is the long-term fantasy a professional-grade simulator, a consumer outdoor sports sim, or both?
