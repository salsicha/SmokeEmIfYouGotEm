# Conforming liquid pressure/gravity impulse and free-flight calibration

October 1 continuation of the isolated-water-feature goal. A new small 3D
conforming-liquid pressure reference now couples geometric faces, kinetic
inertia, pressure and gravity, including explicit free liquid boundaries and
prescribed solid/inlet flux. A moving free-flight parcel also exercises that
pressure step and translation transport against an exact physical reference.
**These are calibration controls, not accepted waterfalls, holes, waves, eddies,
foam, froth, spray or playable river/FPS delivery.** All earlier scenes and
native checkpoints remain unchanged.

[Calibration animation](gravity-control.png) · [Embedded Blender playback](gravity-control.blend)

## Coupled representation

`unreal/Scripts/water_feature_rt0_step.py` uses conforming tetrahedra of actual
authored liquid geometry, not voxel center flags or a guessed ghost distance.
The unit-flux basis opposite tetrahedron vertex `a_i` is
`b_i(x) = (x-a_i)/(3 V)`. Its normal integral is one on that opposite face and
zero on the other three. One globally oriented face flux belongs to both
neighboring tetrahedra with opposite signs. Local divergence is the sum of
outward fluxes divided by the actual volume. Normal velocity is continuous;
tangential velocity is not generally continuous in this low-order space.
The [DefElement definition](https://defelement.org/elements/raviart-thomas.html)
documents this element's normal-facet degrees of freedom and continuity.
No external implementation, asset or code is copied into this reference.

The entire consistent kinetic matrix is integrated from `rho * b_i dot b_j`
using exact quadratic tetrahedral moments. Off-diagonal inertia is retained;
face areas and dual volumes are NOT interchanged as weights, and there is no
diagonal mass lumping or small-cell deletion. The divergence matrix `B` and
pressure response `B transpose` are constructed from the same physical faces.
Pressure is piecewise constant in each tetrahedron. The gravity/pressure
impulse is solved together with `B q_new = 0`; prescribed wall/inlet fluxes
are eliminated without fitting the right-hand side.

Nonprescribed external liquid faces have zero ambient pressure. A component
with no free-pressure boundary is explicitly rejected: this prototype does
not hide an arbitrary pressure anchor or mean/source adjustment. Density is
1,000 kg/m3 and gravity is 9.80665 m/s2. Kinetic energy, projection metric
loss and prescribed-boundary impulse work close the same discrete identity.
That projection identity is NOT a complete advective/physical source-energy
budget or a time-resolved emitter model.

This dense reference has an explicit 1,200-face size bound. It is neither a
scalable full-river solver nor a complete Euler/Navier-Stokes implementation.
Conforming nonoverlapping input tetrahedra are required; the constructor
rejects repeated/degenerate cells and inconsistent shared faces, not every
possible nonlocal mesh intersection. Authored tank topology is separately
checked by the full independent readback.

## Fixed-geometry physical controls

Four cases run at three mesh refinements: an inclined-bed hydrostatic tank,
an all-free ballistic impulse, release of a tilted free surface, and a
prescribed inlet balanced by the explicit free liquid boundary. Tanks are
1 x 0.6 m with horizontal water height 0.5 m and bed rise 0.2 m; tilted-surface
height adds `0.06 * (x-0.5)`. Each contains 0.24 m3. Meshes have 6 / 48 / 162
tetrahedra and 18 / 120 / 378 faces. All twelve runs use the same 4 ms step.

Independent qualification checks all 864 tetrahedra and 2,064 faces, reconstructs
the full mass matrix with separate four-point degree-two cubature, and checks
fresh gravity-pressure, divergence, normal-trace, boundary and energy equations.
It imports no constructor helpers and does not execute the constructor solver.
Maximum relative mass-matrix difference is 8.88e-16; hydrostatic pressure
difference from `rho*g*(water_height-centroid_z)` is 1.09e-11 Pa. Still water
has no meaningful velocity; all-free motion matches uniform gravity exactly
to floating-point precision. Tilted surfaces produce inward and outward local
free-surface flux with zero net flux. Prescribed inlet flux -0.006 m3/s balances
free-boundary flux +0.006 m3/s with exactly prescribed wall/port values.

These twelve controls are **fixed-geometry impulses**. Inlet water is NOT yet
emitted as advancing particles/volume, and the tilted surface is not yet moved.
Their low residuals do not prove interface transport or flow convergence.
Tilted-surface and inlet spatial responses still change with refinement;
analytic hydrostatic/ballistic agreement is not general CFD convergence.

The retained first trial at 10 ms failed the existing 0.1 inradius-Courant gate
on the finest ballistic mesh. Its arrays remain at the C: `rt0-coupled-impulse-v1`
artifact directory; worker exited 1. The successful `v2` uses smaller physical
time step on ALL refinements, not relaxed gates, speed caps or removed water.
Construction/audit takes 1.26 s and writes approximately 7.47 MB of arrays at
C: artifact paths, not duplicated here. Dense per-control step times range
0.00038--0.00902 s for these tiny meshes, not Blender fluid or game FPS.

## Moving free-flight control and animation

`build_water_feature_rt0_ballistic.py` advances a 0.25 x 0.12 x 0.06 m parcel
for 0.4 s using 4,000 actual 0.1 ms gravity/pressure impulses. All liquid
boundaries are free. Initial velocity is [0.1,0,-0.2] m/s; mass is 1.8 kg.
Every substep checks that ALL one-sided vertex velocities agree before shared
vertices are translated. General discontinuous tangential traces are rejected,
not averaged into an invented transport velocity. Trapezoidal transport is
exact for uniform constant acceleration; the kinetic matrix is invariant
under translation. This is deliberately translation-only transport.

Independent qualification recomputes actual moving tetrahedral geometry at
all 21 stored poses (126 moving tetrahedra), together with velocities, flux,
mass, energy, pressure and ground clearance. It does not claim independent
readback of 4,000 unstored intermediate substeps. Maximum position difference
from free flight is 6.81e-14 m, volume difference 1.21e-16 m3, velocity difference
7.73e-12 m/s and mechanical-energy difference 2.69e-11 J. Minimum parcel
height remains 0.235468 m above z=0: no collision/impact is represented.

The parcel assumes inviscid liquid, zero surface tension and no air drag.
Its rectangular outline intentionally persists in that ideal solution: it
does NOT establish realistic rounding, continuous waterfall sheet thinning,
breakup, plunge-pool impact, entrainment or spray. Do not call this a physically
and visually accepted waterfall simply because gravity is correct.

Blender renders the actual stored boundary geometry with water IOR 1.333,
without beveling, expanded skin or invented foam. Shape keys encode computed
poses, not hand-authored liquid trajectories. The saved playback uses 50 FPS
for its discrete 20 ms samples; between-sample shape-key interpolation is
presentation, not additional solver output. The annotated APNG shows 5x slow
motion and an end hold, with physical timestamps and exclusions on every frame.
The first overexposed rendering is retained but not the delivered presentation;
the second changes lights/background material only, preserving physical poses.
Offline rendering time is not physical step cost or game FPS.

The delivered second rendering has 21 actual engine views, taking 142.95 s;
all match saved physical poses within 5.64e-8 m (Blender float32 coordinates).
A fresh read-only Blender process reopens the DELIVERED D: playback and
independently checks all 21 poses, embedded boundary topology, physical sample
FPS, water IOR and absence of fluid domains/external images. Its maximum pose
difference is the same 5.64e-8 m. The APNG is read back frame-by-frame with
pixel equality, dimensions 640 x 700, declared 100 ms frame durations and
500 ms end hold, and one playback. Initial/middle/final engine views and the
annotated frame are visually inspected. The sharp outline remains a deliberate
idealization, not visually accepted water breakup or froth.

## Preservation and unfinished work

The original full-stencil solid/phase fields, native velocities/pressure,
source meshes and prior animation/playbacks are unchanged. This reference
uses NEW authored conforming-liquid tank/parcel meshes; it has NOT tessellated
or repaired the older cached eddy checkpoint. In particular the prior 227
uncertain wet cells and 0.126 m3 quadrature interval are not silently resolved
by the new tank tests. No original Mantaflow primary particle or cache advances.

Next implement conservative moving-interface transport, solid contact and
source/outflow chronology on the conforming representation beyond uniform
translation. Resolve/discretize actual solid/liquid geometry consistently,
then check spatial/time refinement, topology/volume change and pressure/contact
energy before another feature bake. General overturning, breakup and impact
remain required; do not substitute a heightfield-only method or a parcel-only
success criterion. All eight feature animations and later normal playable
river reconstruction at 20 FPS remain open. Keep the full goal active.

## Delivered evidence and final checks

`pressure-step.json` and `pressure-qualified.json` record the twelve controls;
`motion.json` / `motion-qualified.json` record translation and independent
physical qualification; `render.json`, `animation.json` and
`playback-qualified.json` record actual engine/animation/reopened-playback
checks. The animation and embedded playback are copied here with hash equality
and no overwrites. Large numerical arrays and failed/overexposed artifacts stay
at their original C: locations; no evidence is deleted.

All 224 numerical regressions pass, including twelve new RT0 tests. The initial
unfiltered stock-Python discovery reports eight import errors in Blender-only
tests; these require their engine/scene contexts and are not counted as stock
Python successes. This continuation does not claim all legacy Blender-scene
tests pass. New rendering and reopened playback ARE tested in actual Blender.
Ten new scripts compile with SyntaxWarning treated as an error. Scoped Git
whitespace checks pass. Previous full-field evidence and original eddy animation/
both playbacks rehash unchanged. All owned workers finish terminal; no duplicate
native cook, Blender/UnrealEditor job, Git/automation mutation or access blocker
remains. Blender's optional preferences/thumbnail-cache warnings do not prevent
the successful owned saves, renders and read-only playback validation.
