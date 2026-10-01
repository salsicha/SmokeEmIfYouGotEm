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

### Fresh manifold-transport component (2026-09-30)

The rejected eddy's cached phases are preserved; none is lifted or relabeled.
`water_feature_surface_manifold.py` now provides a new surface-constrained
marker timestep: tangent acceleration, previous tangent-speed correction and
a bounded implicit normal intersection. Missing fields, buried initial markers,
nonconvergence and large corrections fail explicitly, without clamped paths or
invented tangent directions. Success/failure leaves the input state unchanged.

This component is motivated by the constraint approach in sections6.6--6.7 of
[Wretborn, Flynn and Stomakhin (2022)](https://www.wetafx.co.nz/assets/Uploads/PDFs/2022-Guided-Bubbles-and-Wet-Foam-for-Realistic-Whitewater-Simulation.pdf).
It is NOT their complete wet-foam/SPH or guided two-way bubble implementation.
Those forces, transitions and interaction terms remain required; the control
does not reproduce foam morphology, persistence, drainage or rupture.
No source figures, footage or code were copied into the scene.

Eight independent numerical tests pass: exact unsteady moving plane, sphere
geodesic refinement/no speed loss, tangent acceleration/normal-force removal,
input-state preservation and rejected invalid/unsupported inputs. The moving
plane's prescribed motion is a manufactured control, not a new fluid solve.

New `surface-manifold-control-v1` uses fresh numerical markers on imposed
30mm spheres at90mm/s,2s,24Hz. At equal timestep the constraint method keeps
tangent speed; a separately defined free-flight/closest-point position and
velocity-projection control falls to75.593% of initial speed. This is a
comparison of two integration schemes, NOT evidence that Mantaflow uses the
projection baseline. The first baseline mistakenly reused the same implicit
normal solve and its expected speed-loss assertion failed (session31758).
That failure exposes the distinction: on a static sphere the old-normal solve
already preserves tangent speed without rotation correction. The baseline
is now explicitly a different closest-point/velocity-projection algorithm;
no physical model gate was relaxed to force the desired image.

Constraint trajectory error versus the independent exact great circle is
472.07/117.39/29.31 micrometres at48/96/192 steps (second-order refinement).
Native full/half-frame playback is checked at97 poses for8 markers, then
rechecked after reopening the saved scene. Positions agree with the numerical
curve/chord interpolation within7.04nm. However, native half-frame chord
interpolation misses the curved manifold by up to58.89 micrometres. Do NOT
confuse the much smaller native readback error with physical trajectory or
continuous surface error. Native animation is not exact surface tracking
between its24Hz keyframes; finer keys/nonlinear evaluation remain required.

The scene is labeled imposed geometry and nonphysical markers, not a water
feature completion. No original source mesh, cache, phase or delivered clip
is changed. Native preferences/temp/thumbnail/OptiX-cache warnings remain;
source edits, case creation and native rendering nevertheless succeed.
No access blocker prevents this scoped feature work. All eight features remain
unaccepted; the full isolated-feature objective is not reduced to this control.

Next validate interface/velocity boundary support before applying the new
component to real moving liquid, then implement the tangential wet-foam
constitutive/interaction dynamics and bubble transition model. The existing
strict dense-MAC sampler requires all neighbouring centres inside liquid, so
it cannot supply a zero-level surface sample; do not loosen that interior
sampler or substitute zero velocity. A separate justified surface/boundary
sampling model is needed. Formation, breakup, film dynamics, physical optical
scale, the froth animation and the other feature requirements remain open.

Builder28267, reopened native audit/render13399 and encoder finish terminal0.
The fresh control APNG is delivered in `surface-manifold-control-v1/feature.png`:
24 native frames1..47,stride2,800x450,12fps normal-speed playback,2s, no seamless
loop. Every decoded RGB frame matches its native PNG and no adjacent duplicate
occurs. Actual first/middle/last views show the markers moving around and being
occluded by the imposed surfaces, with different final travel distances.
The caption/studio view is diagnostic and still not a foam appearance example.
The second render makes caption objects camera-only without changing marker,
sphere, camera or light geometry; text presentation remains unqualified.
Its measured render time349.39s is not game FPS. Native scene, trajectories,
dynamics, reopened animation audit and capture receipts are copied and
hash-verified alongside the clip.62 pure numerical/regression tests pass this
turn; no claim that the earlier16 native geometry tests were rerun here.
Previous eddy phase scene and delivered animation are rehashed unchanged.
Native source SHA:
`11d39c80b3796a34653f4143333e681f44367f214a287e05ac68580300334e11`.
APNG SHA:
`f2d6b27b4eb59f7a8209440197bfc0034765ce2098861448b012d08d1adced0a`.
Capture SHA:
`3c9aa8b33beffe684049d3b3550927ca731e6594f85a227bd94f3c2550b638e4`.
All owned processes are terminal; no original data deleted or pushed. A receipt
copy command hit constrained-language .NET-method restrictions and temporarily
placed five fresh duplicates at the repository root. Native Split-Path and
fail-fast guards copied them to the intended delivery; identical hashes,
creation timestamps and untracked status verified ownership before removing
only those duplicates. Every original and delivery copy remains recoverable.
The isolated
feature goal remains incomplete. This is an integration component, not a
replacement success criterion for surface foam or the other seven features.

### Separate surface-MAC sampling and native interface audit (2026-09-30)

New `water_feature_surface_mac.py` leaves the existing strict interior sampler
untouched. It reconstructs an interface velocity by a bounded local weighted
affine fit, using ONLY faces whose two adjacent centres are fluid/non-solid.
All three components need enough independent samples and a conditioned full
rank fit; a sampled positive-solid path must separate neither source nor
query. Missing support, flat/unknown level sets, out-of-domain queries and
non-interface queries remain missing, never zero/clamped flow. Its level-set
gradient is the exact derivative of the checked trilinear interpolant. Native
phi in grid cells is mapped by the calibrated isotropic spacing into metres;
that scaled phi is not asserted to be exact geometric signed distance.
The snapshot adapter explicitly rejects nonzero time. No temporal support or
new dynamics is invented from a frozen cache.

This is an INFERRED one-sided affine continuation model, NOT native Manta
velocity extrapolation, an exact interface velocity, a pressure/mass fix or
physical acceptance. Positive sampled solid paths are not exact collider
proof. Residuals and radius sensitivity are exposed rather than fitted away.
Nine independent tests pass: staggered affine fields at horizontal/slanted
interfaces, exact trilinear gradient, ignored arbitrary air velocities, local
quadratic refinement, invalid/missing/solid support and no fake time support.
The first quadratic test changed the subcell phase with refinement and failed:
errors0.675/0.493/0.149mm/s did not decrease by four on its first step. The
current refinement test holds local phase fixed and reduces spacing; this is
LOCAL stencil convergence, not domain-wide/native-liquid convergence. The
phase-sensitive failure is not reinterpreted as accepted physical convergence.

New `audit_water_feature_surface_mac.py` samples the preserved aligned eddy
at frames168/192/214. It checks cached staggered velocity against native engine
readback, applies the matched gravity-calibrated units, and compares phi-zero
crossings with the actual closed collider-consistent liquid render extraction.
All three geometry hashes match prior rendered evidence exactly. The original
scene, setup, calibration and six data/mesh files are rehashed unchanged.
Eighty prespecified regular columns/frame produce78 topmost phi crossings;
76/75/76 give conditioned fits at BOTH2.5 and3.5-cell source radii. Missing
columns/fits are recorded, not selected away. This audit has no animation,
secondary phase change, marker projection or cache write.

It exposes an important compatibility problem, not a solved foam delivery:
nearest rendered-surface distance from the base phi-zero has median
15.50/14.13/14.98mm, with maximum42.79mm. Sampled top rendered height minus
base phi-zero has median-16.74/-14.67/-16.72mm and reaches-57.87mm.
Nearest-surface and top-height differences are different quantities; neither
proves enclosed-volume classification. Existing mesh construction uses a
separately reconstructed particle level set, rather than simply rendering
the base phi unchanged, as confirmed in the installed build's
[liquid mesh pipeline](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/intern/mantaflow/intern/strings/liquid_script.h).
Consequently surface markers constrained to the base field would NOT
automatically lie on the currently rendered water. Do not mask that with
marker offsets or claim the small Newton residual establishes visible contact.

The inferred velocities are also unaccepted: changing source radius gives
median differences0.0845/0.0913/0.1051m/s, maximum0.5982m/s. Worst component
weighted RMS fit residuals at radius2.5 are0.4756/0.3960/0.3819m/s. Analytic
affine exactness does not make these nonlinear real-cache fits accurate.
Next establish a shared rendered/constraint interface and independently bound
surface velocity and temporal support, then integrate fresh interacting foam.
Do not enable this candidate as physical foam solely because it returns a fit.
The manifold, SPH/interaction, formation/breakup, persistence and optical
requirements remain open; all eight feature cases remain unaccepted.

Native audit9415 completed the measurements and unchanged-input checks but
failed to write its receipt into the existing case directory (PermissionError).
Rerun49634 with a NEW explicitly permitted visualization-root destination
finishes0 and preserves a complete829038-byte receipt at:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/eddy-surface-mac-audit-20260930-v1.json`.
Receipt SHA256:
`2ecdb3354596ed05ade7f999be6749c6c9df823a6599d1791131e36364da51d9`.
Do not repeatedly rerun the denied destination. Source edits succeed. The first
70-test regression run had three temporary-directory access errors (not
numerical failures); using the explicitly permitted visualization root for
temporary tests gives71/71 passes, including the later slanted-interface test.
Three new source modules compile without SyntaxWarnings. Native preference
and default-temp warnings persist. No new visible feature clip, acceptance,
normal-game integration or20FPS result is claimed from this supporting work.
No original data is deleted, committed or pushed.

### Actual-render interface component and limits (2026-09-30)

New `water_feature_mesh_interface.py` represents the unchanged rendered liquid
triangles themselves, rather than offsetting markers from the base grid phi.
Its signed nearest distance uses face, edge and angle-weighted vertex normals,
following the sign construction in
[Baerentzen and Aanaes (2005)](https://www2.imm.dtu.dk/pubdb/edoc/imm3578.pdf).
No source code, figures or footage are copied. That construction requires a
closed consistently outward-oriented non-self-intersecting surface. The new
component checks oriented edge incidence, single-cycle vertex links and
positive total signed volume; these do NOT prove absence of self-intersections
or outward orientation of every disconnected component. Signed geometric
volume here is NOT physical conserved liquid mass.

Nearest candidates from the native BVH are refined against the unchanged
float64 world triangles. The observed BVH coordinate-rounding bound is0.2384
micrometres; candidate searches use a1micrometre padding. No vertices are
welded, reoriented, smoothed or shifted. Neither these candidate bounds nor
float64 calculations establish global exact-arithmetic distance proofs.
On-surface true creases/vertices have no unique gradient and remain unsupported.
An internal coplanar triangulation edge, however, is not a physical crease.
The first analytic shared-MAC test exposed that distinction by querying a
cube face's internal diagonal; recognizing coplanar incident normals fixes
that test without treating real cube edges as differentiable.

Ten independent pure controls pass: face/edge/vertex signed distance and
finite-difference gradient, a concave prism/reentrant edge, retessellation
invariance, exact face contact, undefined crease gradients, rejected open/
inverted/bowtie topology, immutable geometry and a manufactured affine flow
on a render interface10mm distinct from the base phi. `RenderMeshMacField`
retains strict native source-face support and narrow-band/solid checks; the
new mesh is the EXPLICIT constraint interface, not a relaxed native interior
sample. Its velocity fit remains inferred/unaccepted and its frozen adapter
rejects nonzero time. No temporal field/mesh correspondence is invented.
All81 pure numerical/regression tests pass, including these10. Three new
modules compile without SyntaxWarnings; no additional native geometry-suite
rerun is implied by that pure-test count.

New `audit_water_feature_mesh_interface.py` checks preserved native frames
168/192/214 against the prior surface-MAC receipt. Contact-material faces are
excluded from free-surface queries. All three actual rendered geometry hashes
match prior evidence. Source data, scene, mesh, calibration, setup and the
prior receipt (10 files) are independently rehashed unchanged, as are the
three executed source modules. No cache, old particle position/type, liquid
geometry, source material or delivered animation is changed.

Two initial native attempts30064/27713 fail a fixed50-micrometre local normal
distance control. Diagnostic27713 identifies column[16,3], frame168: a BVH
ray-derived plane point is2.00nm from its actual nearest triangle, ray face
19635 differs from nearest19634, and inward distance differs from the assumed
50micrometres by1.4266micrometres. The rounded ray location must not be assumed
to lie in its reported float64 triangle, nor its ray-face normal assumed to
be the actual interface normal. This is a geometric-query/normal-neighborhood
issue, not another claim that source write access or the entire solver fails.
No existing marker is projected to make this pass.

Revised audit60293 verifies actual float64 triangle membership and at most
0.1nm zero residual, then uses the supported actual nearest gradient. It
records missing/failed queries rather than aborting the remaining diagnostics.
The original50micrometre displacement and10nm local-distance tolerance remain
unchanged. Of78 prespecified regular columns/frame,23/24/22 are explicitly
missing (rounded triangle-boundary queries or undefined surface normals).
The remaining55/54/56 mesh-interface queries have maximum zero residual
3.33e-16/2.22e-16/2.36e-16m. This demonstrates sampled shared geometry, NOT
physical foam transport, temporal accuracy or whole-surface coverage.

Normal-neighborhood controls STILL fail32/35/28 of those queries; worst
distance errors are0.406/4.020/1.646micrometres. Those queries get NO fitted
velocity or transport qualification in this audit. Only22/18/26 queries have
both radius2.5/3.5 velocity fits after the geometric controls. Their median
radius differences0.1084/0.0937/0.0755m/s, maxima0.3076/0.4334/0.3477m/s, remain
unaccepted. A tiny contact residual does not imply a reliable force normal,
velocity fit or a stable surface particle timestep near these facets/creases.
The generic snapshot sampler is NOT globally qualified by these filtered
audit results; do not enable it as a finished foam solver.

Next establish evolving shared-interface/velocity support and explicit
normal-reach/crease handling, then the requested constrained interacting
wet-foam/SPH and phase transitions. Do not hide unsupported locations with
offsets, invent zero velocities, smooth only the renderer or remove failed
queries from coverage accounting. This is supporting component work, not a
replacement for foam gathering/breakup/persistence, liquid coupling, physical
optics, a new short animation or any of the other seven feature deliverables.
The full isolated-feature goal remains active/incomplete; all8 cases remain
unaccepted. No normal-game integration or20FPS result is claimed.

Audit60293 is terminal0 (44.82s measured diagnostic cost, NOT game FPS).
Complete431238-byte receipt:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/eddy-shared-mesh-interface-20260930-v1.json`.
SHA256:
`7bf8c3c1cd486fff5b2ead4b184ce434bc11ade4d6ccd6f60bbf347e2ffeac92`.
Source and explicitly permitted receipt writes succeed; no owned native job
remains live. Default Blender preference/temp warnings occurred during these
audits but did not prevent the scoped work. No files deleted, committed or
pushed, and no new visual delivery/physical acceptance is claimed.

## September30: facet transport, complete nearest candidates and native keys

The preceding component turn is progress: new static facet-edge transport
and its tests changed authoritative source, and native failure31713 identified
an endpoint timestamp error. It is terminal1, not a live bake or access blocker.
On resumption, independent multi-edge cube controls reproduce accumulated end
times one ulp short/long of the requested duration in15 of36 cases. Completed
integration now records the exact requested endpoint timestamp; positions and
speed are not clamped or advanced. Partial/contact stops retain unconsumed time.

`water_feature_facet_transport.py` crosses actual shared edges by dihedral
parallel transport. It preserves event points, rejects unsupported initial
contact/normal velocity, and stops explicitly at unresolved vertices,
contact/non-free-surface boundaries and declared crossing limits. No average
crease normal, cached-marker projection, speed damping or arbitrary outgoing
vertex direction is used. Eight independent controls cover coplanar motion,
exact cube unfolding, step partition invariance, facet contact, explicit stops,
invalid inputs, zero velocity, immutability and exact terminal time coverage.

Native audits61852/43538 finish0 using the old float BVH distance oracle:
51 of54 frame192 paths pass, two contact stops remain and one segment fails
the fixed10nm geometric distance gate. The v2 audit retains that failed path
and its measured distance, instead of dropping its trace through a generic
exception. It reports2.449608micrometres at column[12,15], segment7 midpoint.
A separate native read-only comparison finds the point on the unchanged
positive-area triangle17078, distance1.570092e-16m; the float BVH reports17077
and omits17078 even from its1micrometre-padded candidate set. This is an oracle
omission, not a reason to smooth/retriangulate the water or loosen contact.

`water_feature_triangle_nearest.py` replaces that candidate oracle locally in
the facet audit. Its float64 all-triangle AABB lower bounds include all possible
nearer facets, followed by independent point/plane and bounded-edge distances.
No float-BVH face retention is assumed. Five controls compare80 random cube
queries with independent all-triangle enumeration, reproduce the actual thin
facet, check displaced normal distances, misleading box seeds, duplicate ties,
extreme aspect ratio, invalid inputs and original-geometry immutability. This
is not an exact-arithmetic or global self-intersection/orientation proof. Older
normal/velocity audits remain preserved and have NOT been silently requalified.

The new native coverage reveals a separate animation issue. Initial audit57084
fails the fixed2micrometre readback gate; instrumented99860 preserves a complete
FAILED v3 receipt and exits1. All52 geometric free-surface paths complete, but
native individual insertion merges11 event keys into10 on each location curve
for row4. Its two crossing frames35.791773515 and35.794347313 are only
0.002573798frames apart. Native frame36 differs from the correct path by
5.262578micrometres despite near-zero geometric contact residual. Do not hide
that time/speed error behind the smaller distance-to-water measurement.

The native audit now creates channels once and fills complete ordered arrays
through keyframe-points.add/foreach_set, retaining close float-resolvable events
without deduplication. Non-distinct float frame times fail explicitly. The
documented key allocation/sort/handle methods are checked against actual5.2
native playback, rather than assuming that insertion preserves all events.
See [Blender keyframe-point API](https://docs.blender.org/api/main/bpy.types.FCurveKeyframePoints.html).

Final native audit61346 finishes0 with the original frame192 mesh hash
569081c358790f82d4d592f671255856dbb64216db8527c89d5159bded1b161c.
52 of54 prespecified fresh paths complete, including34 prior failed-normal
queries; two collider-contact stops remain explicit. Every location channel
retains every event key. All52 paths pass97 native full/half-frame poses over2s.
Maximum native position error4.717727e-7m and nearest distance3.063449e-7m
remain below the unchanged2e-6m allowance. The formerly merged row4 retains
all11 keys per channel and has maximum readback error7.719268e-8m.
Maximum speed error3.469447e-17m/s and whole/20-step endpoint disagreement
6.220036e-15m.6179 float64 queries use at most12 AABB candidates in this case;
15.92s total audit cost is measured offline work, not real-time performance.

94 combined pure tests pass, and five new source modules compile without
SyntaxWarnings. Eleven original inputs/receipts and three executed modules
are independently rehashed unchanged after the final native run. No captured
particle, collision source, liquid mesh/cache or delivered clip is changed.
Temporary in-memory audit objects/actions are removed; no blend or new animation
is saved. Source and receipt writes succeed; preference warnings are not a
blanket source-access blocker. All owned native jobs are terminal.

Final375117-byte receipt:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/eddy-facet-transport-20260930-v4.json`.
SHA25699a2cae9bd19b170363d19e47d00d87788bb2b5bdf9b3b3cd169972e75767799.
Failed native-key evidence remains in the same root's v3 receipt,
SHA2560229de2efbb5b9c2f5d1628e6a30e9ecb1028f0fadd3a160b9f6cb220dae5d5e.
Earlier diagnostic receipts v1/v2 are also preserved; their executed audit
source hashes differ by design as failure instrumentation/repairs were added.

This is a STATIC captured-mesh prescribed50mm/s numerical marker component,
not native water velocity, a time-evolving liquid interface or interacting
foam. Passing facet transport does NOT make failed normal neighborhoods valid
for forces, nor accept radius-sensitive surface velocity fits. Next build
consistent evolving interface/velocity support, then liquid-coupled interacting
wet-foam/SPH, gathering/breakup/persistence, phase changes and physical optics
before delivering the requested foam animation. All8 physical/visual feature
deliverables remain open. No full-river acceptance, new movie,20FPS claim,
commit, deletion or push is implied; the full isolated-feature goal is active.

## September30: actual evolving interface versus captured liquid velocity

The previous goal turn is progress: it repairs thin-facet nearest queries and
coalesced native event keys and verifies52 fresh static paths. Those successful
components do NOT supply moving-water/velocity agreement. This continuation
measures that missing condition using actual five captured meshes, not a
prescribed evolving surface or a projection of old particles.

`water_feature_surface_kinematics.py` evaluates the material-interface
condition `dphi/dt + velocity.dot(gradient(phi)) = 0` at an actual current
interface query. Separate centered differences use frame offsets +/-1 and
+/-2; their discrepancy is reported, not removed through Richardson correction,
retiming or adjusted velocities. Gradient normalization accounts for a scaled
level set without changing the input velocity. This is a local finite-time
diagnostic, not temporal interpolation or a qualified foam force sampler.
The underlying requirement is consistent with advecting a level-set interface
by fluid velocity; see the primary
[PhysBAM fluid-interface formulation](https://physbam.stanford.edu/papers/stanford2012-07.pdf).

Six independent controls cover a translating plane with tangential motion,
a stationary plane with deliberately inconsistent normal flow, a scaled/tilted
level set, an expanding sphere, known second-order cubic-time stencil error,
and missing/invalid geometry/time/vector support.100 combined pure regression
tests pass; three new modules compile without SyntaxWarnings. No test result
is used to declare actual foam or liquid physics accepted.

Native audit13048 completes0 in42.02s. It loads preserved frames190..194,
checks closed manifold topology and positive total volume through MeshInterface,
uses complete float64 triangle candidates, and preserves central frame192's
known render hash. Current raw MAC data is bitexact with native RNA readback;
gravity calibration supplies the same0.1871782892479084 raw-grid-to-m/s scale.
The actual playback clock is24fps,fps_base1 and domain time_scale1; it is not
multiplied by a guessed internal Mantaflow time factor. Probe distances use
an explicitly declared3-cell/0.225m search band, NOT a contact-error allowance.
The largest measured neighboring-frame distance is only0.0362027m. No temporal
geometry interpolation, vertex correspondence or updated surface particle
position is manufactured.

All54 prior frame192 query locations have signed-distance support in all five
meshes.52 have both radius2.5/3.5 one-sided velocity fits. Two near-collider-contact
locations, columns[32,12] and[32,15], retain missing fits, not zero velocities.
The24 missing prior columns out of78 remain explicit in prior_missing. Old
failed-normal-neighborhood labels are retained; their new temporal diagnostics
do NOT qualify those normals for constrained forces/transport.

The measured normal-velocity discrepancy is substantial. Quantiles at minimum,
5th,50th,95th and maximum respectively:

| Measurement, m/s | Minimum | 5th | Median | 95th | Maximum |
|---|---:|---:|---:|---:|---:|
| Absolute mismatch, radius2.5 | 0.0000422 | 0.004667 | 0.083398 | 0.355155 | 0.602119 |
| Absolute mismatch, radius3.5 | 0.000955 | 0.005475 | 0.095600 | 0.332493 | 0.663615 |
| Fine/coarse temporal stencil difference | 0.0000404 | 0.002118 | 0.016564 | 0.098253 | 0.152024 |

Two temporal intervals alone do not prove convergence or bound the continuum
error. This mismatch combines moving rendered geometry, temporal sampling
and inferred surface velocity; it is NOT evidence identifying one unique
engine defect, invalidating the whole liquid solver or establishing a usable
foam-driving field. Do not silently replace the fluid's normal velocity with
the surface speed and call the discrepancy solved.

Audit48453 adds a distinct diagnostic comparison and finishes0 in43.37s.
Direct trilinear staggered cache reads are explicitly UNQUALIFIED: each
component records how many of its8 interpolation faces have strict two-liquid,
non-solid source support. None of the52 common-cohort probes has8 strict
source faces in ALL3 components; some have0 in the vertical component. This
does not prove that native extrapolation is wrong, but its validity/support
must be reconstructed from the matched engine stages before these values can
be used. Raw readings are never substituted into the strict interior sampler
or used for particle transport.

For the same52 locations with both fitted velocities, direct-cache absolute
normal mismatch quantiles are0.002095,0.010183,0.063593,0.415788,0.533467m/s.
The raw comparison has54 available readings overall, including the two missing
fits, but that different cohort is not used to claim a paired improvement.
A simple surface-sampler substitution has not established consistency; the
cache comparison still leaves sizable disagreement and unknown ghost support.
Next establish native extrapolated-face validity and actual stage/time
provenance, and reconcile shared moving mesh/velocity support before fresh
liquid-coupled foam interactions, breakup/persistence and physical rendering.
Do not rerun this unchanged measurement as a fix or enable unknown air faces
just to animate foam. The full physical/visual objective remains unchanged.

Five actual render hashes, frames190..194:

- 190: b522219728cabcfa14c7785d428ade643302d610c9a229cb0b678c117006715c
- 191: 1545f0068abfc46e46bb2f6a91d57637554d2f75caf6afd4a30383834a6a3898
- 192: 569081c358790f82d4d592f671255856dbb64216db8527c89d5159bded1b161c
- 193: 668d536b4eacb942bb9b3e520ac23c94ab44c1f6037341f0ed7251b60c318672
- 194: 1f37ecbf2cc4013dec4def8866a76f66f73e18f1612857db809d226d31012944

Final366415-byte receipt:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/eddy-surface-kinematics-20260930-v2.json`.
SHA256fc622114ddf011997995d4f4fbfcc59eda18f7e75210879a8558da7fd172a2c0.
All19 original captured inputs/receipts and three executed source modules
are independently rehashed unchanged after the run. Earlier v1 evidence is
preserved. All owned native jobs are terminal; preference warnings did not
prevent source/receipt work. Offline diagnostic cost is not20FPS/game cost.

No cache, authored solid, existing particle, geometry, material, delivered
animation or normal game is changed. No new clip or physically accepted
feature is claimed; all8 feature cases remain open and the goal remains active.

## Native extension provenance, not a velocity correction (September30)

The new `water_feature_native_mac_extension.py` reconstructs the **interior**
component-wise simple MAC extension independently. Native flag bit tests mark
a lower face as a seed when either adjacent cell is fluid; the strict existing
DenseMacField still requires both. The two support definitions are not
interchangeable. Extension advances four synchronous neighbor layers, with
native float32 summation order and no within-layer recursive propagation.
Unsupported values remain numeric in the private copy but explicitly have
layer0. Domain boundary-copy behavior and obstacle-normal unprojection are
not implemented or qualified. Algorithm/flags were checked against this
installed build's primary
[fastmarch.cpp](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/fastmarch.cpp)
and [grid.h](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/grid.h).
Read-only source SHA256:
60013aabf3632d8a599a11885c3050fa7d44fc6e4d4b04c94b0a875596cd5c3a.
No source asset was downloaded into the case, and no native code was modified.
The matched fastmarch.cpp header is verified as Apache License2.0, copyright
2011 Tobias Pfaff/Nils Thuerey; the new NumPy implementation is independently
written and does not copy the generated native source.

The native algorithm can propagate into/through obstacle-adjacent faces even
with intoObs=false. The separate provenance records obstacle contact in any
contributing seed/extension ancestry rather than silently rejecting or changing
those values. Contact ancestry alone does not prove a face physically wrong:
a wall-normal zero can be valid. A future force/transport policy still needs
actual boundary and normal-neighborhood qualification.

Eight pure tests cover planar reach and exact layer labels, either-adjacent
fluid and combined flag bits, arbitrary unsupported cache values, synchronous
layer barriers, float32 sum order, obstacle-contact propagation, staggered
stencil/boundary coverage, and input immutability/invalid inputs.108 combined
pure regressions pass. Native `audit_water_feature_native_mac_extension.py`
compares all interior components, not just a selected acceptable subset:
20 manufactured grid/distance/intoObs comparisons and captured frames168,
192,214 pass bitexact across512406 scalar comparisons. Actual cached flags
and velocity are loaded independently through OpenVDB and native Manta,
with payload equality checked **before** private-grid extension. Central
velocity also matches actual scene RNA bitexact. No cache writer or full
liquid-step/bake runs; the comparison is final-extension replay only.

The first blank-scene invocation failed: importing bare Manta did not install
base-grid methods on FlagGrid/MACGrid; its retained child during error teardown
also produced a native exception. No receipt or original-cache change resulted.
Evaluating the preserved actual fluid domain initializes Blender's grid
inheritance methods. The audit now explicitly requires this initialized API
and matching scene/clock, clears child-retaining error tracebacks, and releases
grids before solvers. Corrected runs785d31 and a2aaa1 both exit0. The preference
read warning did not prevent this source/receipt work; this is not a permission
repair or evidence of continuing write-access failure.

All54 prespecified frame192 query stencils now have four-layer native extension
support for every component corner. Four have obstacle-contact lineage:
[32,12],[32,15],[40,12],[40,15]. The35 old normal-neighborhood failures within
these54 queries remain failures for force/transport qualification; the prior
24 missing regular columns are retained through the unchanged reference.
Numeric/native support does not qualify same-time interface motion or foam.

The stored cache is not bitexactly idempotent under extension replay. Seed
values are unchanged; replayed extension differences across the three grids
reach0.00146233m/s. Serialization of seeds and extension values is a possible
source of this difference, not independently bounded/proved here. At the54
actual stencils maximum individual-corner change is0.000731165m/s. The audit
uses the same actual object-derived grid origin,75mm cell size, calibrated
velocity scale, normals, distances and playback clock as the earlier receipt;
raw interpolated cache values must reproduce that receipt within1e-12m/s.
Interpolation remains audit-only, not an enabled field/particle driver.

| Prespecified cohort | Count | Cached median absolute normal mismatch, m/s | Replayed median, m/s |
|---|---:|---:|---:|
| Both prior affine fits supported | 52 | 0.0635931 | 0.0635641 |
| No obstacle-contact lineage | 50 | 0.0615915 | 0.0616113 |
| Prior normal neighborhood supported | 19 | 0.0985683 | 0.0985683 |

These are separately declared coverage cohorts, not filtered by measured error.
For the52 common queries, maximum replay/cache normal-speed change is only
0.0000976924m/s; maximum velocity-vector difference is0.000176961m/s. Thus
replaying this extension does not explain or remove the measured mismatch.
This is not an accepted sampler, proof of continuous-time convergence, or a
unique engine-cause diagnosis. Next establish the exact case-specific velocity
stage/time used to advect liquid and extract the evolving mesh. In particular,
do not substitute velocity_previous using current flags or shift its time to
fit the residual: previous-stage flags/time support are not established.

Final332288-byte receipt:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/eddy-native-mac-extension-20260930-v2.json`.
SHA256e7b8f7aa3d157b212d00ea18b71838dec3afd2edea23bb71c372f125f4b3cbfe.
All20 original inputs/receipts and4 executed modules independently rehash
unchanged after the run. Earlier v1 receipt remains preserved, SHA256
28dac7d70a15de5bf544ea6e547fb77c0f68663a8fb65f82d62e7ad9f5b9c661.
Current audit/component/test SHA256 respectively:
217c8e98b68aae3ff87d35e3a1b0d45353815dce056dd8e43fb2b2773d04a651,
e92c2884bbf56ab5d15006b4f7ca1399428afed7a9597915b8d5224137570aab,
bdc4150648258995a8b2b93d50719444567e4507bd8b9ade2796906a117a0d87.
All owned jobs are terminal.2.04s measured native audit cost is not gameFPS.
No original mesh/cache, authored scene, existing particle, delivered animation
or normal game was changed. No new clip or accepted feature is claimed;
liquid-coupled foam motion and all8 physical/visual cases remain open.
