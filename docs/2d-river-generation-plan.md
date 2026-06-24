# Procedural 2D River Generation Plan

## Goal

Start with a deterministic 2D top-down river simulator before modeling vertical water surfaces, 3D raft motion, Chrono FSI, Unreal, or VR.

The first target is a plan-view river map that can answer:

- Where are the banks?
- Where is the main current?
- Where are eddies, rocks, waves, holes, shallows, and hazards?
- What force does the boat feel at each hull sample point?
- Can a generated rapid produce repeatable, testable boat behavior?

This is intentionally simpler than the full simulator. It should be good enough to generate playable, physically interpretable 2D rapids and regression scenarios.

## Core Representation

Use a 2D world coordinate system:

- `x, y`: world position
- `s`: downstream distance along the river centerline
- `n`: lateral distance from centerline
- `theta`: boat yaw

Generated river data should include:

- Centerline curve
- Left and right bank boundaries
- Width along the centerline
- Depth field
- Flow velocity field
- Vorticity / rotational flow proxy
- Shear field
- Turbulence intensity
- Feature tags
- Collision geometry
- Spawn, finish, and validation checkpoints

The first implementation should avoid a grid-only design. Generate a centerline and cross-sections first, then sample them onto a grid or queryable field. That keeps the river editable and easier to reason about.

## River Generation Pipeline

### 1. Seed And Parameters

Every generated river must be reproducible from a seed and parameter set.

Initial parameters:

- Seed
- Length
- Average width
- Width variance
- Bend frequency
- Bend amplitude
- Gradient / steepness
- Water volume
- Rock density
- Feature density
- Difficulty target
- Safety margin near start and finish

### 2. Centerline

Generate a smooth downstream path.

Recommended first method:

- Start with a straight downstream axis.
- Add low-frequency noise for broad bends.
- Add smaller noise for local wiggle.
- Smooth the path.
- Reject self-intersections and bends tighter than the boat can plausibly navigate.

The centerline should expose tangent and normal vectors at sampled `s` positions.

### 3. Width And Banks

Generate river width as a function of downstream distance.

Rules:

- Constricted sections increase speed and hazard density.
- Wide pools reduce speed and turbulence.
- Banks must remain smooth enough for collision and flow-field queries.
- Start and finish regions should be wide, calm, and readable.

Build bank boundaries by offsetting the centerline along its local normal by half-width.

### 4. Depth And Gradient

Generate a depth profile:

- Deeper thalweg near the fastest current
- Shallow shelves near inside bends
- Shallow tongues above rocks
- Deeper pools below drops or wave trains

Generate a slope/gradient profile:

- Gentle gradient for pools
- Steeper gradient for rapids
- Local gradient spikes for drops, ledges, and constrictions

In 2D, depth and gradient are not visual decoration. They drive speed, drag, grounding, and hazard placement.

### 5. Base Flow Field

Compute a base velocity field from:

- Downstream tangent direction
- Local gradient
- Width constriction
- Depth
- Roughness
- Bend curvature

First approximation:

- Main current follows the centerline tangent.
- Speed increases in constrictions and steep sections.
- Speed decreases in wide/deep pools.
- Flow shifts toward the outside of bends.
- Near-bank flow is slower.

This does not need to be a full shallow-water solver at first. It needs to be deterministic, inspectable, and easy to validate.

### 6. Feature Placement

Place features after base flow exists.

Feature categories:

- Rocks
- Gravel bars
- Eddies
- Eddy lines
- Standing waves
- Holes / hydraulics
- Pour-overs / ledges
- Lateral waves
- Boils / upwellings
- Strainers
- Gates / scoring markers

Placement constraints:

- Avoid impossible clusters in beginner rivers.
- Put eddies behind rocks and inside bends.
- Put wave trains below constrictions and drops.
- Put holes below ledges or steep local gradient changes.
- Put pillows upstream of large rocks.
- Keep at least one plausible line through every generated rapid.

### 7. Feature Composition

Features should modify the field, not just add labels.

Examples:

- A rock adds collision geometry, upstream pillow flow, side acceleration, downstream eddy, and eddy-line shear.
- A constriction increases current speed and can spawn wave trains.
- A ledge adds a hole/hydraulic and downstream turbulence.
- An inside bend creates a slower eddy or shallow shelf.

Each feature should return:

- Flow delta
- Turbulence delta
- Collision geometry
- Boat interaction effects
- Debug visualization data
- Validation metadata

### 8. Difficulty Scoring

Compute difficulty from generated features:

- Peak current speed
- Shear strength
- Obstacle density
- Navigable channel width
- Required turn angle
- Recovery eddy availability
- Hole/wave density
- Pinning risk
- Grounding risk

Use this score to reject or retune generated rivers that do not match the requested difficulty.

## 2D Boat Model

The first boat should be a top-down rigid body:

- Position `x, y`
- Yaw `theta`
- Linear velocity `vx, vy`
- Angular velocity `omega`
- Mass
- Moment of inertia
- Hull sample points
- Paddler force points

The boat samples the river field at multiple hull points. Each sampled point contributes force and torque.

Do not model roll, pitch, buoyancy volume, tube deformation, or vertical motion yet. Represent those later as 2D interaction effects and outcome classifications until the 2.5D/3D model exists.

## Boat Interaction Effects

These effects should interact with the 2D boat.

### Current Push

The base water velocity pushes hull sample points downstream. The force depends on relative velocity between hull point and local water.

Telemetry:

- Local current vector
- Relative velocity
- Drag force
- Torque contribution

### Fast Tongue

A smooth fast channel pulls the boat into the main line. It should reward correct angle and early setup.

Telemetry:

- Tongue centerline distance
- Speed multiplier
- Lateral restoring or pulling force

### Eddy

An eddy is a recirculating or slow-water region. It can catch the boat, slow it, or help recovery.

Telemetry:

- Eddy membership
- Local recirculation vector
- Exit/entry force

### Eddy Line Shear

An eddy line is a sharp velocity gradient between fast current and slower or reverse current. It should yaw the boat when only part of the hull crosses the boundary.

Telemetry:

- Shear strength
- Hull samples on each side
- Yaw torque

### Rock Collision

Rocks apply collision impulses and friction. They can deflect, spin, stop, or pin the boat.

Telemetry:

- Contact normal
- Normal impulse
- Friction impulse
- Contact point
- Pinning score

### Rock Pillow

Large rocks create upstream pillow flow that pushes the boat away before contact if the approach is not too steep.

Telemetry:

- Pillow field strength
- Repulsion force
- Approach angle

### Downstream Eddy Behind Rock

Behind-rock recirculation can pull the stern, slow the boat, or create a recovery pocket.

Telemetry:

- Wake zone membership
- Recirculation force
- Yaw torque

### Standing Wave

In 2D, a standing wave is an energy barrier and instability zone rather than a rendered height surface.

Effects:

- Upstream deceleration
- Lateral instability
- Possible surf/stall outcome
- Increased angular disturbance if crossed at a bad angle

Telemetry:

- Wave crest crossing
- Required speed estimate
- Surf/stall score

### Wave Train

A wave train is a repeated sequence of standing waves. It should create rhythmic speed loss, yaw noise, and line discipline demands.

Telemetry:

- Wave index
- Cumulative speed loss
- Yaw disturbance

### Hole / Hydraulic

A hole is a retentive region. In 2D, it pulls the boat upstream or sideways and can classify the result as surfed, stuck, or flushed.

Telemetry:

- Retention force
- Escape vector
- Surf duration
- Flush/stuck classification

### Pour-Over / Ledge

A pour-over creates a downstream hydraulic and strong local acceleration into the feature.

Telemetry:

- Entry speed
- Retention score
- Downstream recovery force

### Lateral Wave

A lateral wave pushes the boat sideways across the current.

Telemetry:

- Lateral impulse
- Hit angle
- Yaw torque

### Boil / Upwelling Proxy

A boil/upwelling in 2D should be represented as a noisy radial or rotational flow patch with reduced predictable steering.

Telemetry:

- Upwelling strength
- Radial force
- Randomized but seeded disturbance

### Hypoviscous / Aerated Patch

A turbulent aerated patch reduces effective damping. The boat slides more and responds less predictably.

Telemetry:

- Local damping coefficient
- Drag reduction
- Steering authority reduction

### Shallow Shelf / Gravel Bar

Shallow areas add grounding drag and can rotate the boat if only part of the hull is shallow.

Telemetry:

- Depth under each hull sample
- Grounding drag
- Yaw torque

### Bank Contact

Banks behave like broad static collision boundaries with friction.

Telemetry:

- Bank normal
- Contact length estimate
- Friction impulse

### Strainer / Hazard Zone

A strainer is a lethal or run-ending hazard zone in early 2D simulation.

Telemetry:

- Hazard contact
- Entrapment score
- Run outcome

### Paddle Force

Paddle strokes apply forces at guide/passenger sample points.

Telemetry:

- Stroke side
- Stroke direction
- Force magnitude
- Torque contribution
- Local water velocity at blade

## Validation Scenarios

The generator should produce named, seedable scenarios:

- Straight current
- Gentle S-bend
- Single rock with pillow and downstream eddy
- Eddy-line ferry
- Wave train
- Hole escape
- Constriction with lateral wave
- Shallow shelf grounding
- Beginner rapid with one clean line

Each scenario should have regression checks:

- Deterministic generated fields
- At least one navigable route
- No invalid bank intersections
- Bounded current speed
- Feature count within expected range
- Boat outcome classification for scripted inputs

## First Deliverable

The first 2D river deliverable should run:

```bash
python -m raftsim.examples.generate_river_2d --seed 1
```

It should output:

- A generated river plot
- A sampled flow-vector plot
- A JSON or TOML parameter file
- A feature list
- A validation summary

The first boat deliverable should run a scripted raft through that generated river and export trajectory plus force telemetry.
