# SmokeEmIfYouGotEm Game Concept

## Elevator Pitch

SmokeEmIfYouGotEm is a 3D white water raft guide game built in Unreal Engine. The player takes the role of the river guide seated in the back of the boat, reading rapids from a first-person perspective, steering a raft through dangerous currents, giving paddle commands, managing passenger safety, and chasing clean lines through increasingly technical river sections.

The initial camera goal is first-person from the guide's stern position: low and physical enough to feel the raft buck under the player, but readable enough to judge current, obstacles, eddies, waves, passenger timing, and raft angle before each decision matters.

## Core Fantasy

The game should make the player feel like a skilled guide threading a raft through controlled chaos. The best moments should come from spotting the right line early, setting the raft angle, calling the right paddle rhythm, and barely sliding past a rock or hydraulic with everyone still aboard.

## Target Platforms

The project should be designed as a multi-platform Unreal Engine game from day one.

Primary targets:

- Windows PC
- macOS
- Linux / Steam Deck

Future targets:

- PlayStation
- Xbox
- Nintendo hardware, if performance and certification constraints are realistic
- Cloud streaming builds

Possible later experiment:

- Mobile or tablet, only if the controls can be simplified without weakening the core game

## First-Person Camera And View

Initial prototype camera:

- First-person camera anchored to the guide position at the back of the raft
- Player can freely look left, right, forward, and slightly behind without losing the sense of being seated in the boat
- Camera motion should communicate raft hits, drops, and waves without causing discomfort
- The guide's paddle, hands, nearby passengers, raft tubes, and bow should remain visible as grounding references
- Optional quick-look or lean actions can help players check obstacles and passenger state without needing a third-person view

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

## Core Gameplay Loop

1. Read the next river feature from the guide's first-person seat in the stern.
2. Position the raft before the rapid.
3. Call paddle commands and use guide strokes to enter the line.
4. Adjust in real time as current, waves, rocks, and crew timing affect the raft.
5. Recover from mistakes or capitalize on clean execution.
6. Finish the section and receive feedback on safety, speed, control, and style.
7. Upgrade guide skills, raft handling, crew trust, or unlock harder river routes.

## Raft Controls

First prototype controls should be readable and gamepad-friendly.

Possible guide inputs:

- Forward paddle command
- Back paddle command
- Left side paddle
- Right side paddle
- Hard left / hard right guide stroke
- Hold on / brace command
- Rescue command when a passenger falls out

The player should feel like they are commanding a crew rather than directly moving a vehicle with arcade thrusters. The raft can still be responsive, but the response should come through paddle force, water current, and raft momentum.

The first-person view should make inputs feel like physical guide actions. Paddle strokes, command calls, brace warnings, and rescue actions should be readable through the player's hands, paddle, voice, and the crew's response.

## River Systems

The river is the main level design language.

Prototype systems:

- Spline-based river path
- Directional current volumes
- Surface waves and visual flow cues
- Rocks, strainers, holes, ledges, pour-overs, eddies, and calm pools
- Checkpoint gates for optional training and scoring

Longer-term systems:

- Procedural rapid generation from authored river chunks
- Dynamic water levels
- Weather and visibility changes
- River difficulty classes inspired by real white water ratings
- Rescue scenarios and guide certification challenges

## Physics Feel

The raft should feel buoyant, heavy enough to matter, and vulnerable to bad angles. The game does not need full simulation accuracy in the first draft, but the forces should be consistent and learnable.

Prototype physics priorities:

- Current pushes raft downstream
- Paddle calls add directional force and torque
- Rocks deflect, pin, or slow the raft
- Waves can lift, shove, or spin the raft
- Passenger weight distribution can slightly affect handling

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

Early game modes:

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

The game should feel energetic, outdoorsy, risky, and a little scrappy. It should respect real river guiding while still being playable and readable as a game.

Visual direction:

- Bright daylight river environments
- Clear diegetic water direction indicators through foam lines, bubbles, surface streaks, waves, and debris
- Strong silhouettes for rocks, raft, waves, and hazards
- Minimal first-person UI inspired by guide maps, safety checklists, and river notes
- Visible raft bow, tubes, paddle, hands, and passenger silhouettes to ground the player in the stern

Audio direction:

- Loud water near hazards
- Paddle thumps and raft rubber creaks
- Guide calls with short, punchy voice lines
- Passenger reactions that communicate risk without becoming noise

## Unreal Engine Direction

Recommended starting approach:

- Unreal Engine 5.x project
- C++ core systems with Blueprint-facing tuning where useful
- Enhanced Input for keyboard, mouse, and controller
- Common UI or a similarly portable UI approach for multi-platform menus
- World Partition only when the river scope grows large enough to need it
- Data assets for river sections, hazards, raft tuning, and scoring rules

Prototype map:

- One short river section
- One raft
- One guide input set
- A few rocks and wave hazards
- Start, finish, scoring, restart, and first-person look controls

## Open Questions

- Should the first playable prototype be realistic simulation, arcade tactics, or a middle ground?
- Should passengers be individual characters with traits, or mostly a visual representation of crew state?
- Should raft control be direct, command-based, or a hybrid?
- How much should the first-person camera prioritize downstream planning versus close physical impact?
- Should there be any optional third-person or scout camera, or should the game stay fully committed to the guide's viewpoint?
- Is the long-term fantasy a campaign, a roguelite river runner, a sports sim, or a creative river sandbox?
