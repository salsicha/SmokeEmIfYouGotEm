# Surface foam: transport and cap/contact prototypes

Status: **not accepted** as physically or visually accurate foam. These are
separate small scenes, not material changes to the full-river project. They
advance the surface-foam case without satisfying its gathering, breakup,
formation, persistence or optical-calibration requirements.

## Continuum control

`build_surface_foam_lab.py` prepares a 30 x 12 cm tray, 25 mm water depth and
a 3 mm effective scattering layer. The prescribed velocity is
`u = 0.018 + 0.75*y` m/s, `v = 0`, and the inverse map exactly advects a compact
density patch. No fluid solver or two-way interaction is implied. The static
side-wall render geometry does not simulate the idealized driven boundaries.

Two quadrature resolutions give a maximum relative weighted-area error of
3.60e-7 and centroid error of 2.54e-9 m over 0..3 seconds. The linked shader
math was evaluated at 2,048 world-space sample positions per preview frame;
maximum discrepancy was 0.00133 /m against the 1,800 /m reference scale.
This checks linked math, not the GPU's optical integration.

The actual frames 1, 37 and 73 were rendered and inspected. The patch moves
and stretches but looks like a smooth white spot. **Rejected as a foam visual
representation.** Do not make a full beauty clip of this unchanged control.
Outputs remain in `tmp/water-feature-lab/surface-foam-shear-v1/preview`.

## Discrete contact/film study

`build_surface_bubble_lab.py` creates 220 unequal bubble footprints with
0.7..1.4 mm radii in the same prescribed flow. An overdamped equal-mobility
hard-disk projection prevents overlap. This is a simplified contact model,
not surface-tension hydrodynamics. No artificial white volume is shown.

Above-surface spherical caps have **assumed** height/footprint ratio 0.4 and
450 nm thin-film thickness. The installed Blender 5.2 Principled shader's
Thin Wall and Thin Film inputs are used with water IOR 1.333. These parameters
are exposed assumptions, not a measured surface-bubble shape or lifetime.
The renderer uses cap geometry and light reflection, not opaque white beads.
The water plane is not cut into submerged air cavities: this is explicitly an
above-surface optical study, not complete bubble geometry.

Numerical contact evidence, 73 frames / 3 seconds:

- Timestep 1/480 s; comparison with 1/240 s changes positions by at most
  4.13e-7 m (0.413 micrometres).
- Maximum residual disk overlap is 1.00e-8 m.
- Centroid follows the exact affine shear within 2.23e-16 m.
- Fixed projected bubble area is 0.000659098 m2; this is not gas-volume or
  water-mass conservation.
- Patch remains within the tray; pairwise contact corrections are equal and
  opposite. No gathering attraction or burst/merge events are modeled.
- Executed `test_surface_bubble_lab.py` checks isolated analytic advection,
  contacting pair non-overlap, timestep refinement, centroid transport, cap
  dimensions and upward normals.

The first preview exposed a distracting area-light reflection across the
patch. A lighting-only revision removes that flat-surface glare. Bubble
footprints and their motion are unchanged. Individual film reflections are
visible, but neither a contact test nor a more legible render establishes
accurate foam. The current geometric model lacks submerged cavities, menisci,
capillary attraction, drainage, coalescence, rupture, formation and fluid
feedback. Multi-layer froth is a separate remaining case.

`render_surface_foam_lab.py` installs linear keyframes from the hashed audited
trajectory, checks native Blender timeline positions, and saves a fresh
animated `feature.blend` with its setup, trajectory and contact audit.
Playback does not depend on a command-line-only position override. Source
blends and previous render folders are preserved.

### Delivered study animation

`docs/water-feature-lab/surface-bubble-study-v1` contains the MP4, lossless
APNG, editable animated Blender scene, trajectory and audit metadata. It is
36 frames (1..71, stride 2), three seconds at 12 fps and normal simulated
speed. Source hashes, all decoded APNG frames and the MP4 frame count passed;
zero adjacent duplicate frames. First, middle and final rendered frames were
inspected: the patch visibly translates and stretches without leaving the
view. The appearance remains sparse reflective cells, not accepted dense
foam. Playback repeats with a restart, not a seamless physical loop.
Render 34347 and encoder 95687 finished successfully. No real-time FPS claim.
MP4 SHA256: `2e9d82aca590d17dcc4b323c093b27950fc05b080a7f2108956206ef6f62ee2c`.
Copied delivery files were checked against their source hashes. Metadata
retains original generation paths; the Blender scene's animation is embedded
and needs no external cache to play.
The copied scene was reopened in a fresh Blender process and checked at all
73 native timeline frames against the trajectory. Maximum XY discrepancy was
7.48e-9 m; the rejected continuum layer remained hidden. Session 19074 is
terminal. This validates artifact playback, not missing foam physics.

## Next physical/visual work

Use a documented bubble-shape/film model with a stated Bond-number and
surfactant regime, then add meniscus/cavity geometry and compare to dated,
licensed macro reference imagery. Contact rearrangement alone does not
replace capillary gathering, merging, bursting and measured persistence.
Keep the continuum control for transport testing, not as a completed foam
substitute. The aerated froth/spray case and improvements to all six earlier
features remain required by the goal.

Blender capability references (no external media or code bundled):
[thin-film support](https://developer.blender.org/docs/release_notes/4.2/cycles/),
[5.2 rendering changes](https://developer.blender.org/docs/release_notes/5.2/rendering/).
Search excerpts were accessible; full release-page retrieval failed. Actual
installed shader inputs and rendered outputs, not those excerpts, establish
that the local pipeline supports the selected inputs.

### Primary geometry/dynamics reference located during rendering

[Patel and Zhu, JFM 1026 A19 (2026)](https://doi.org/10.1017/jfm.2025.11003)
is available as full HTML under CC BY 4.0. Read the geometry derivation in
section 3.2 and migration discussion in section 4.2; no images/data bundled.
Their Bond number uses the original spherical bubble diameter:
`Bo = 4*rho*g*R0^2/sigma`, not the visible cap-footprint radius. Small-bubble
cap curvature approaches `Rc = 2*R0`; equation 3.8 improves the rim-radius
estimate, with cap/meniscus height addressed afterward. Equation 4.4 models
pairwise migration using meniscus slope and a calibrated drag coefficient;
it is not a parameter-free replacement for the contact projection. The authors
identify limitations near contact, and their model does not determine absolute
film lifetime. These give a concrete next route beyond the assumed 0.4 cap
height ratio. The present clip does **not** implement or validate their model.

### Connected bubble geometry checkpoint (2026-09-29)

The new `surface_bubble_shape.py` implements the isolated small-bubble
approximation from the cited reference: equations 3.8, 3.4 with zero rim
height in its first pressure estimate, 3.14 and the linear meniscus in 3.16.
It restricts Bo to at most 0.6. Bessel functions use integral quadrature;
doubling quadrature resolution, limiting behavior, rim force/pressure balance
and meniscus boundary slopes are checked by `test_surface_bubble_shape.py`.
This does not solve the full nonlinear Young-Laplace problem.

`build_surface_bubble_geometry.py` makes a **static** isolated checkpoint:
one connected closed water mesh with an actual submerged cavity and exterior
meniscus, plus a separate thin film. No flat plane crosses the gas cavity.
Nominal gas radius 1 mm gives Bo 0.54372, rim radius 0.39230 mm, rim elevation
0.18932 mm and cap rise above rim 0.04404 mm. Material density 998 kg/m3 and
surface tension 0.072 N/m are chosen scenario inputs, not measured river data.
Film thickness remains an assumed 450 nm. No source media were bundled.

Render 48650 finished; its 960 x 540 image was inspected. The cavity and rim
are visible through refracting water. This is no longer an above-plane cap
alone, but it is not an optical calibration or a foam animation. The saved
scene was reopened: ray hits find the cavity floor at -1.73052 mm and film
at +0.233365 mm; manifold and seam checks passed. Mesh gas-volume error versus
the analytic approximation falls from 0.0999% to 0.0250% on refinement.
The analytic gas volume itself is 0.214% below the nominal sphere volume.

Crucially, the spherical cavity approximation has a maximum hydrostatic/
Laplace pressure residual of **12.68%** of the gas pressure for this case.
This physical error is much larger than the mesh discretization error. Do
not promote it as validated equilibrium or simply relax the criterion.
The next geometry step is a nonlinear Young-Laplace cavity/meniscus solution
with fixed gas volume, followed by integration into the moving multi-bubble
scene. Capillary gathering, drainage/rupture and optical reference checks
remain open; the previous 220-bubble animation is unchanged.

Five delivered files in `bubble-geometry-study-v1` (image, editable static
blend and three metadata/audit files) are SHA-256 verified copies. The blend
is self-contained. All geometry render/audit processes are terminal. This
work adds only a small scene and does not require another large fluid cache.

### Nonlinear equilibrium and native drift study (2026-09-29)

`solve_surface_bubble_equilibrium.py` now solves the cavity and exterior
Young-Laplace equations with fixed gas volume. It follows Appendix B of the
same primary reference under its massless-film/negligible-gas-density model.
Three shooting unknowns enforce rim height, slope and volume. Fourth-order
integration and a damped Newton solve use NumPy only; no new dependency was
installed. Results and all sampled interfaces are retained in
`tmp/water-feature-lab/bubble-equilibrium-v1/equilibrium.json`.

For nominal gas radius 1 mm, the solved rim radius is 0.40656 mm, rim height
0.18540 mm, cap curvature radius 1.87225 mm and cavity depth 1.63667 mm.
The independent position-derived cavity-pressure residual is 0.000541%
(versus 12.68% for the old spherical approximation). Doubling integration
steps and moving the outer boundary from 12 to 16 capillary lengths change
the reported shape dimensions by less than 0.001 nm. An independent sampled
volume integral differs from the specified gas volume by 0.000129%.

`test_surface_bubble_equilibrium.py` also checks gas radii 0.5 and 0.7 mm.
All three pass volume, rim continuity, monotonic profiles and independent
curvature checks. The first low-order meniscus derivative test failed for
the smallest bubble due to cancellation between principal curvatures.
It was replaced by position-only fourth-order stencils on the actual uniform
log-radius grid; no physical solver setting or tolerance was relaxed.

The engine builder now accepts the solved profiles. The new rendered image
was inspected, and the saved scene reopened for topology, ray and volume
checks. Mesh gas-volume error improves from 0.1016% to 0.0255% on refinement;
the cap/water rim seam differs by less than 0.016 nm. The empty cavity is
retained, without an intervening flat surface. The earlier approximate
study and its evidence are unchanged.

`render_bubble_equilibrium_drift.py` embeds a 1 mm/s uniform translation of
both solved interfaces. This is a Galilean/uniform-advection study, not an
interacting foam simulation. The floor is a visual reference, not a simulated
no-slip boundary. Reopening the animated blend verified all 73 native frames,
identical mesh hashes and translation error below 0.2 nm. Camera and lighting
remain fixed. Film thickness is still assumed; physical appearance, drainage,
rupture and surface-foam interaction remain unaccepted.

Render session 32246 and encoder 73811 are DONE. The three-second uniform-drift
study is delivered in `bubble-equilibrium-drift-v1`: 36 frames (1..71, stride 2)
at 12 fps, 800 x 450, normal prescribed speed. First, middle and last renders
were inspected: the bubble stays framed and translates with its meniscus.
All source hashes, decoded APNG frames and MP4 frame count passed; no adjacent
duplicates. MP4 SHA256:
`adf18ccfd26466f69bcc2a3f14da3e4320cdce5c3151208878ae681a8cfdb03c`.
Ten copied delivery files are hash verified, including the embedded native
animation and numerical reports. The scene needs no external fluid cache.
The loop restarts rather than representing a seamless physical cycle.
The renderer maintained a 1 GiB free-disk reserve; no partial render remains.
The cached encoder required scoped access approval; encoding then succeeded.
No full froth bake is running; the broader disk shortage still precludes its
next comparison. This single-bubble study is not completion of surface foam,
and it does not replace gathering, breakup, persistence or appearance checks.

### Reduced capillary-pair reference study (2026-09-29)

`surface_bubble_pair.py` now implements the same primary reference's equations
4.2/4.4, with its Bo=1, Mo=1e-4 reference condition and Appendix E drag Cd=2.
With the scenario density, gravity and tension this gives gas radius
1.356159 mm and viscosity 44.147 mPa s. **This is not ordinary water.**
Transferring the fitted drag to 1 mPa s would give diameter Reynolds numbers
122--239, outside the Stokes assumption; that transfer is explicitly rejected.
The reference-condition trajectory has diameter Re 0.0627--0.1227.

Distance decreases from 4.88217 to 3.60201 mm across 12 poses at 24 fps
(sample times 0--0.458333 seconds). The clip therefore lasts half a second,
including its final displayed frame. It is not slowed down or extended to
force a three-second result. Near-contact deformation, drainage and rupture
are excluded; the integration stops before the excluded separation range.
An independent separated-variable integral and a finer time grid agree.

The isolated nonlinear equilibrium solver now supports Bo=1. Independent
position-derived pressure/volume checks pass at 1024 and 2048 steps, including
a far-boundary extension. `test_surface_bubble_pair.py` records these tests
in `tmp/water-feature-lab/bubble-pair-reference-v1/physics-tests.json`.
This validates the isolated reference shape and numerical migration, not the
pressure balance of the three-dimensional pair.

`build_bubble_pair_lab.py` makes a single closed water boundary, with two
cavities and separate films. A neighbor meniscus field vertically shears each
isolated interface. This is an approximate superposition, not a solved coupled
3D equilibrium. There is no buried internal water wall or overlapping full
water volumes. Film thickness remains an assumed 450 nm.

The first rectangular-edge sampling failed its unchanged 0.3% mesh gas-volume
gate (0.568% error). Angular sampling within each boundary sector fixes that
discretization issue: worst sampled error is 0.0956%, falling to 0.0244% on
refinement. Closed topology, symmetry and no interior partition pass.
The failed empty scene directory is preserved; no old cache was removed.

`audit_bubble_pair_animation.py` evaluates the production native shape-key rig
at 12 full frames and 11 intervening half frames, both in memory and after
reopening the saved scene. Coordinates match intended linear interpolation
within 1.38 nm; weights remain nonnegative and sum to one; films do not overlap.
Total water-volume range is 0.00213% of the domain's water volume, or 0.7044%
of one bubble's gas volume. This small nonzero drift is reported, not hidden.
The animation audit does not establish a liquid velocity field or momentum
conservation. No physical or visual acceptance is claimed.

Scene builder/render 50689 and saved-scene audit 58420 are terminal. Actual
first/middle/last preview frames show separated refracting cavities and
approach motion. Full 12-frame render 91062 and the encoder are DONE. The
normal-speed half-second MP4/APNG and self-contained native scene are delivered
in `docs/water-feature-lab/bubble-pair-reference-v1`. All 12 source hashes,
decoded APNG frames and MP4 frame count pass; no adjacent duplicate frames.
The copied scene matches the source blend hash recorded by the renderer;
copied physics/geometry test reports are also hash verified. All 22 delivery
files total 13,964,645 bytes. First/middle/last delivered frames were inspected.
MP4 SHA256: `afe3cca4b14d5632cd6d1b9e9e8d1f7fa3a18faaac5d0b466acb496c80fdc843`.
Offline render time is 4.63--9.46 seconds per frame (mean 5.29 seconds), not
real-time FPS. Playback is 24 fps. The repeating preview resets to its initial
separation, not a physically seamless loop. Disk briefly fell below 1 GiB and recovered above
the reserve; no access permission or deletion was needed to resume this small
render. A full froth bake still requires its separate 11 GiB preflight.
The pair remains groundwork for gathering foam, not a replacement for a foam
raft, breakup, persistence, the missing froth clip, or the other seven cases.
