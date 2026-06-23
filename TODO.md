# TODO

## Rough First Draft Outline

This project is starting as a 3D white water raft guide game built in Unreal Engine with a first-person camera from the guide's position in the back of the raft and multi-platform goals. The first playable milestone should prove that guiding a raft through current feels physical, readable, and fun before the project expands into campaign, progression, or large river systems.

## Milestone 0: Project Foundation

- [ ] Choose the exact Unreal Engine 5.x version for the first project.
- [ ] Create the Unreal project with a clean multi-platform folder structure.
- [ ] Add a proper Unreal `.gitignore`.
- [ ] Decide whether the initial project uses C++, Blueprint, or a hybrid.
- [ ] Set up Enhanced Input actions for keyboard, mouse, and gamepad.
- [ ] Add basic build targets for desktop platforms.
- [ ] Add initial README with setup and build instructions.

## Milestone 1: First-Person Guide Prototype

- [ ] Create a simple test river map.
- [ ] Add a raft pawn or actor with basic movement.
- [ ] Add a first-person guide camera anchored to the stern of the raft.
- [ ] Add mouse, keyboard, and gamepad look controls.
- [ ] Keep the raft bow, tubes, guide hands, paddle, and passengers visible enough to ground the player.
- [ ] Implement forward, back, left, right, and brace commands.
- [ ] Make current push the raft downstream.
- [ ] Add simple raft rotation from paddle force and current.
- [ ] Add restrained camera motion for waves, drops, and collisions.
- [ ] Add restart and reset controls for rapid iteration.

## Milestone 2: River Readability

- [ ] Add visible current direction cues.
- [ ] Add rock hazards with collision and deflection.
- [ ] Add eddies or slower current zones.
- [ ] Add wave or hydraulic hazard placeholders.
- [ ] Establish a visual language for safe water, risky water, and danger water.
- [ ] Test first-person camera height, field of view, motion, and obstruction at multiple screen sizes.
- [ ] Make foam lines, surface streaks, debris, and wave shapes communicate current direction from inside the raft.

## Milestone 3: Scoring And Game Loop

- [ ] Add start and finish gates.
- [ ] Track time through the rapid.
- [ ] Score clean lines, collisions, passenger safety, and recovery.
- [ ] Add a run summary screen.
- [ ] Add quick retry.
- [ ] Add basic audio feedback for water, collisions, and paddle calls.

## Milestone 4: Crew And Passenger Layer

- [ ] Add placeholder passenger characters.
- [ ] Place passengers in front of the guide so their paddle timing and panic states are readable from first person.
- [ ] Make passengers paddle in response to guide commands.
- [ ] Add passenger brace state.
- [ ] Add simple trust or panic meter.
- [ ] Add passenger fall-out event after major hits.
- [ ] Add rescue interaction placeholder.

## Milestone 5: Multi-Platform Readiness

- [ ] Keep all gameplay actions controller-friendly.
- [ ] Test mouse and keyboard, Xbox-style controller, and Steam Deck-style controls.
- [ ] Avoid platform-specific assumptions in UI, save data, and input.
- [ ] Add scalable graphics settings.
- [ ] Define performance budgets for desktop and handheld targets.
- [ ] Check packaging on at least one target platform before adding large systems.

## Milestone 6: Content Direction

- [ ] Design the first short rapid.
- [ ] Design three beginner hazards.
- [ ] Design one rescue scenario.
- [ ] Define river difficulty classes for the game.
- [ ] Sketch campaign structure or challenge progression.
- [ ] Decide whether the first vertical slice is a guided tutorial, a timed challenge, or a short river run.

## Technical Notes To Revisit

- [ ] Evaluate Unreal Water plugin versus custom simplified river flow.
- [ ] Evaluate Chaos buoyancy needs versus custom raft force model.
- [ ] Decide how river currents are authored: spline fields, volumes, flow maps, or a hybrid.
- [ ] Decide how much simulation accuracy is necessary for fun and readability.
- [ ] Investigate multiplayer feasibility only after the single-player raft loop feels good.

## Immediate Next Steps

- [ ] Create the Unreal project.
- [ ] Add initial source control ignores and project README.
- [ ] Prototype raft movement on a flat plane before adding complex water.
- [ ] Add a single downstream current volume.
- [ ] Tune the first-person guide camera until the raft, line, passengers, and hazards are readable.
