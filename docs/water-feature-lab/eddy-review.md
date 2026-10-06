# Bank-spur eddy prototype

## Setup and evidence

`tmp/water-feature-lab/eddy-v1` is a separate synthetic 6 m flume, not a river
reconstruction. Its bank-attached rectangular spur occupies x=2.45..3.00 m,
y=0.05..0.95 m, z=-0.20..1.10 m. Visible geometry and collision use the same
mesh, and a Boolean excludes the obstacle from the initial water volume.
The approach height is 0.45 m, newly emitted inlet speed 2 m/s, inlet depth
0.35 m, and artificial level-drain threshold 0.30 m. This is not a prescribed
discharge or a true fixed downstream water elevation.

The 80-resolution, 288-frame bake finished in 229.50 seconds. Fractional
obstacles remain off; the boulder comparison did not justify promoting that
option. Mesh, liquid and secondary-particle caches are present.

`eddy-late.json` measures predefined regions with the matching 80-resolution
free-fall velocity calibration. At frames 240, 264 and 288:

- Main-current mean downstream velocity: 1.50, 1.58, 1.72 m/s.
- Bank-return mean downstream velocity: -0.96, -0.99, -1.03 m/s.
- Behind-spur lateral velocity: -0.29, -0.34, -0.31 m/s (away from the bank).
- Downstream-turn lateral velocity: +0.045, +0.106, +0.190 m/s (toward bank).

No primary particles were found deep inside the spur in the five sampled
frames. This is not a millimetre-scale collision clearance check. Earlier
frame 192 still has positive bank-region mean velocity: the flow is evolving.
These narrow-band particle means are not volume averages or tracked paths.
Counterflow alone does not prove sustained circulation or a closed trajectory.

## Visual review and remaining work

The high-oblique frame-240 preview exposes the sheltered return without hiding
the collider. The liquid shape is visible but excessive, sheet-like whitewater
coverage persists. Spray uses dielectric water; foam and bubbles still use
unvalidated white scattering approximations and rendering radii.

The first 36-frame motion sequence (frames 216..286, stride 2) is delivered
in `docs/water-feature-lab/eddy-prototype-v1/feature.mp4` and `feature.png`.
Playback is 12 fps, three seconds at normal simulation speed. All APNG frames
match the rendered sources exactly; the MP4 decodes 36 frames with zero
adjacent duplicate source images. First/middle/last frames were visually
inspected. Playback repeats but is not a seamless simulation loop.
MP4 SHA256: `8a7eda48b4b4592dda038d0db4cb130e94f1afca037cef86b30c4bf7aab8e906`.
Render session 73831 and encoder 72826 are terminal.
Circulating paths, seam exchange, longer-time persistence, boundary sensitivity,
mass balance and whitewater appearance remain unaccepted. No game integration
or real-time FPS claim is made.

## Reconstructed pathline check

`pathlines-v1.json` reconstructs 48 seeded paths from frames 168..288, using
inverse-distance interpolation of up to 12 calibrated primary-particle velocity
samples within 0.15 m. It requires at least four neighbors. The velocity field
is interpolated between consecutive cached frames; midpoint integration is
repeated at four and eight substeps per frame. These are not persistent FLIP
particle identities, and no missing path is clamped or projected into water.

At eight substeps, 31 paths stop for insufficient local/midpoint support,
16 leave bed/domain/drain bounds, and only one lasts all five seconds. That
survivor travels downstream rather than demonstrating a closed loop. Median
step-halving difference over common supported samples is 0.86 mm; the maximum
is 49.76 mm. Thus the reconstruction is not strong evidence of persistent
eddy circulation. Sparse narrow-band support is a diagnostic limitation,
not proof that the underlying solver has no eddy. A better-supported velocity
field and a longer settled interval are required; do not repeatedly rerun this
unchanged pathline test expecting acceptance.

`test_water_feature_pathlines.py` passes all five checks: constant velocity,
linear time interpolation, circular motion with second-order step refinement,
missing support, and solid entry. These verify the integrator, not the fluid.

## Dense-MAC reconstruction and short tracer preview

The next check replaces sparse particle-neighbor interpolation with original
staggered velocity grids, not another bake. `water_feature_dense_mac.py` uses
trilinear lower-face component sampling and linear interpolation between cached
frames. It never extends support, clamps paths or projects them into water.
Both4/8 substeps and both RNA-engine/isotropic mappings are audited with the
same48 predeclared seeds over frames168..288. All121 original VDB hashes are
checked unchanged; native velocity arrays match VDBs at168/228/288.

The initial dense audit v1 checked eight surrounding liquid/solid centers but
not both neighbors of every interpolated MAC face. It leaves9/11 full-duration
paths in engine/isotropic mappings, but this is insufficient support validation
and **not a qualified circulation result**. V2 additionally requires both
liquid/outside-solid neighbors of every interpolation face. It leaves zero
engine-map paths and only one isotropic path for the full five seconds. The
isotropic group's median/max step-halving difference over common positions is
0.0732/1.371 mm; engine mapping0.0790/12.58 mm. Mapping sensitivity reaches
0.567 m (median35.7 mm), so the alternate mappings are not interchangeable.
Stopping near the bed/surface or leaving the drain does not prove absence of
an eddy; it does prevent a robust persistent-circulation claim.

Native resumed particles at168/216/288 independently resolve the **display
coordinate** mapping: all362,285 positions and velocities match the isotropic
object-centered mapping (max position-component difference0.477 micrometres).
RNA's anisotropic cell-size mapping disagrees by up to11.86 mm. The actual
particle spacing is0.075 m, origin[0,-0.7875,-0.1125] m; RNA uses approximately
[0.075,0.07619048,0.07435898] m, origin[0,-0.8,-0.1] m. This is native mapping
evidence, not a dense-grid hydraulic, mesh-collision or mass-conservation proof.
The small native loader initially used an unavailable Vec3 alias, then loaded
attached velocity attributes in the wrong order. Using public vec3 and the
generated-script order (Pdata before particle system) fixes those checks;
failed attempts exit cleanly and the completed three-frame check exits0.

A new **two-second diagnostic animation** is delivered in
`eddy-tracer-diagnostic-v1/feature.png`:24 rendered/decoded frames168..214,
stride2,12-fps normal-speed playback. Every decoded APNG frame matches its
native render exactly; no adjacent source frames are identical. First/middle/
last actual frames were inspected. It is a labeled liquid-only view with
12-mm orange emissive **diagnostic markers**, not foam, dye physics or FLIP
particle identities. Half-second marker histories follow available reconstructed
positions; unsupported subsequent positions disappear rather than being invented.
The first frame shows48 seeds, then36 retained positions at170,21 at192 and
15 at214. Do not describe the initial seeds as validated path support. The
first caption did that incorrectly; its preview/render remain preserved, while
the delivered version explicitly labels seed/path markers and unverified
circulation. A dark backing makes the corrected caption legible.

The original foam/bubble/spray samples remain in the cache but are hidden in
this diagnostic view. White streaks visible here are surface/light response,
not added foam. The water still looks overly pale, mesh/bed clearance remains
open, and this is **not** the final accepted eddy/foam feature. Five new MAC
sampler tests verify anisotropic staggered interpolation, rotation, full center/
face support and missing/invalid inputs. The five native midpoint-integrator
tests still pass. Across the new and existing volume/flux/stage/sampling suites,
36 checks pass, not hydraulic acceptance.

Audit3074(v1),61973(v2), preview84286, renders88233/61088, native mapping and
encoder are all terminal0 except the two repaired mapping preflights above.
The31 pure tests plus5 native tests finish successfully. Four small source
reports are hash-verified alongside the delivered APNG and clip receipt;
every prior scene/cache/clip remains preserved. No game integration or game-FPS
claim. Next make new scene domains grid-aligned and independently check field,
particle and mesh coordinates/collision before a longer settled circulation
study, with proper bed/surface stencil handling and original foam appearance
still in scope. Do not repeatedly rerun this unchanged five-second audit.

## Grid-aligned modular candidate (September 30)

`eddy-v2-grid-aligned-modular` is a new isolated candidate, not a replacement
accepted animation. The explicit builder option aligns shorter domain axes to
the installed solver's integer allocation while preserving its center and
longest dimension. Dimensions are now [6, 1.575, 2.925] m, allocated cells
[80, 21, 39], isotropic spacing 0.075 m and origin [0, -0.7875, -0.1125] m.
The default builder behavior is unchanged. All nine nondomain mesh vertex/
polygon arrays and unparented world-transform components match the original
eddy exactly; all other physical domain settings match. The original blend
hash is unchanged. Alignment is not a mass-conservation correction.

Matched free-fall calibration passes at 0.2921% gravity error, with native
75-mm spacing on each axis. The guarded 288-frame base-liquid bake finishes
in 49.69 seconds, 546,014,550 cache bytes, terminal0 (guard37526, owned
Blender41296). Mesh and secondary phases are enabled but remain unbaked.
The post-bake alignment audit25092 checks actual native cells/origin/particles
at frames1/168/288. Native mapping audit83714 matches all287,134 primary
positions and velocities at168/216/288. Both RNA-engine and isotropic mappings
now have maximum position-component error 0.477 micrometres; the earlier
11.86-mm display-coordinate discrepancy is resolved in these sampled frames.

The new dense-MAC audit95335 reads/hashes all121 VDBs over168..288 and checks
native velocity arrays at168/228/288. Both coordinate mappings have identical
stop outcomes:44 unsupported local/midpoint paths,3 boundary exits,1 five-second
survivor. Maximum mapping sensitivity is now30.65 micrometres, versus0.567 m
in the old scene. Median/max step-halving disagreement is approximately
0.0389/2.355 mm. The survivor goes from [3.48,0.45,0.15] to approximately
[4.354,0.381,0.228] m; this does not establish a closed circulation path.
Strict liquid/solid center-and-face stencils still prevent robust near-bed/
surface trajectory coverage. Do not loosen support or invent missing paths
to claim acceptance. All tested VDBs remain unchanged.

Five sampled late frames show downstream main-current and upstream bank-return
primary-particle means, with zero particles more than75 mm inside the spur.
This is not a whole-volume average, particle/mesh contact-clearance proof,
mass/flux budget or persistent eddy demonstration. Collider-consistent surface
meshing, original foam/froth optics and a final short animation remain open.
No new rendered clip or playable integration is delivered by this candidate.

Three alignment tests plus the existing31 pure and5 native tests pass; source
compilation and scoped diff checks pass. The modular/all bake flag conflict is
now rejected by argument parsing before creating a scene/output. Earlier
preflight failures (library-ID name mutation and unlinked unevaluated matrices)
were repaired by matching saved library names and transform components, not
by relaxing geometry equality. All old scenes/caches/clips are preserved.
Small calibration/setup/bake/alignment/mapping/pathline/regional receipts are
hash-verified in `eddy-grid-alignment-v1`. No Blender job remains live. Next
validate controlled boundary/bed sampling and budgets, then guarded native
mesh/contact checks; grid alignment alone does not fix mesh/bed intrusion.

## Native mesh/contact extraction and two-second study

The aligned candidate now has a separate diagnostic `feature-mesh.blend`.
Native modular meshing finishes in30.12s,288 frames,116,835,287 mesh bytes
(guard80091, owned Blender41268, terminal0). The base blend and its existing
backup are preserved; all288 original VDB hashes match before/after this stage
and again after rendering. No secondary phase is baked. The first preflight
49094 stops before cache/marker writes because it incorrectly compares baked
state with pristine state. Native inspection finds exactly three expected
transitions: data-pause0->288, baked-data false->true, baked-any false->true.
The corrected guard permits precisely these values, not arbitrary cache/physics
changes; three tests reject partial data, other stage flags and physical changes.
Both failed logs remain. Attempt-numbered logs do not bypass stage/marker guards.

Actual raw native mesh audit64821 at168/192/216/240/264/288 finds closed edge
topology and no degenerate triangles, but substantial rendered-solid overlap:
53.75mm floor,54.82mm approach bed,69.83mm bank spur (maximum vertex/centroid
nearest depth). The far wall has zero sampled intrusion. This is a parity-ray
check against the actual closed authored collider meshes, not a formula chosen
to fit water. It samples every vertex and triangle centroid, not exhaustive
triangle-solid intersection or solver collision dynamics. Mesh volume is not
solver mass. Three native parity/topology tests pass, including a concave solid.

`water_feature_solid_clip.py` extracts the part of the native liquid mesh outside
the **same authored solids**, in memory only. It does not alter fields, particles,
colliders, free-surface motion or caches; it is not a conservation correction.
Sequential exact differences remove the large floor/spur overlap but create
three open edges in frames168/192/264; preserve that rejected extraction report
83186. Combining the overlapping solids before one difference avoids those open
edges in all six audited frames (82095), and in all24 rendered clip frames.
Zero sampled floor/spur intrusion remains; approach-bed numerical residuals
reach31.2 micrometres. However,100..109 triangles per clip frame fall below
1e-12m2 area. Closed edge counts alone are NOT mesh/physical acceptance; tiny
facets, residual contact, exact intersections and temporal continuity remain open.

The first union preview/full render assigns water material to contact caps,
creating an artificial dark band. The corrected extraction transfers the
original solid shader to those closures instead of a fictitious water-air
interface; the water's existing material and studio lights stay unchanged.
Native tests verify simple subtraction, disjoint solids, overlapping unions,
unchanged original geometry/materials, and identical synthetic geometry after
shader transfer. All24 rendered geometry metrics (counts, topology, bounds,
degenerate count and signed volume) match the prior union render exactly.
This is not a calibrated submerged-interface/absorption or lighting proof.
Both the dark preview/full sequence and all previous versions are retained.

A new labeled two-second **surface/contact study**, not an accepted eddy/foam,
is delivered in `eddy-solid-contact-study-v1/feature.png`. It contains24 native
frames168..214,stride2,640x360,12fps normal-speed APNG playback. Every decoded
frame exactly matches its native PNG; no adjacent duplicates. First/middle/last
actual frames were inspected. Caption says solver/foam are unqualified.
White patches are studio reflections, not simulated foam; overly pale water
and foam-like reflections still need visual calibration. The bank-wetted
surface moves, but sustained closed circulation is still unproven. Foam/bubble/
spray phases remain enabled, unbaked and hidden; do not replace their deliverables
with this liquid-only study. Corrected render66742 and encoder are terminal0;
24 frame evaluation/extraction/render times total122.06s, not real-time game FPS.

37 pure tests plus12 native tests pass (49 total, not feature acceptance).
Source compilation, PowerShell parsing and scoped diff checks pass. Five small
receipts are copied/hash-verified alongside the animation; original base blend,
all288 VDBs and all six sampled native mesh files are rechecked unchanged.
No Blender process remains live. Next resolve constructive-mesh degeneracy/
contact without moving the free surface or fitting mass, validate optical
appearance and settled boundary budgets/trajectories, then complete original
foam/froth phases. Keep all eight feature deliverables open; no game integration.

## Modeled daylight study and rejected triangulation repairs (September30)

A new two-second liquid-only animation is delivered in
`eddy-daylight-study-v1/feature.png`:24 native frames168..214,stride2,640x360,
12fps normal-speed playback. All decoded RGB frames exactly match their source
PNGs, with no adjacent duplicates; first/middle/last actual frames were viewed.
The broad white studio-reflection patches are largely absent and moving surface
ripples are easier to read. Local bright glints remain reflections, NOT foam.
Water still looks pale; this is improved readability, not photographic acceptance.

The diagnostic hides the two existing area lamps in memory and uses the installed
Blender5.2 multiple-scattering sky model,35-degree sun elevation,60-degree
rotation, world strength1 and exposure0 with AgX. Atmospheric density, altitude,
sun intensity and angular size retain inspected native defaults. Orientation and
lighting are modeled, not dated river observations or measured exposure. The
actual installed RNA uses `aerosol_density`; older `dust_density` access failed
before any saved-scene changes. The
[upstream Cycles implementation](https://github.com/blender/blender/blob/main/intern/cycles/scene/shader_nodes.cpp)
corroborates the model/property naming, not the exact installed implementation.
No external imagery/code is bundled. The water material, colliders, cached
particles/fields and free-surface motion are unchanged; no source blend is saved.

All24 geometry metrics match the preceding studio/contact animation. Full
vertex/triangle hashes at168/192/214 also match the precision probe and a new
three-frame studio control rendered at the SAME48 samples as daylight. The
matched studio control retains broad white patches, ruling out sample count
as their explanation in this comparison. The earlier24-frame studio clip used
24 samples. The daylight receipt predates addition of explicit sample/denoising
metadata; its invocation used48 samples, while the new control records48.
Do not alter older capture receipts or pretend their source-code hash matches
the renderer after that metadata-only edit.

Native daylight render65195 and studio control88824 finish terminal0;24 daylight
evaluation/extraction/render times total138.97s, not real-time game performance.
The APNG SHA256 is
`c3275070f06551d93fd6b910dc354c2d952b4ae1ca94d99c28c3eec83010a97c`.
The animation is not a seamless loop. Secondary phases remain unbaked/hidden.
Closed edge counts at all24 frames still coexist with100..109 tiny triangles;
daylight changes neither those defects nor the unresolved circulation/budgets.

Precision probe82409 finds101/101/103 tiny triangles at168/192/214 in both
float32 and float64;101/101/102 have exactly zero area. Their parent polygons
have nonzero area. This locates a constructive polygon-triangulation defect,
not merely a float32 area-test artifact. Both water and solid-contact faces
are affected. A native BEAUTY candidate welds only endpoints of exactly
zero-length edges, preserving every distinct coordinate, with no smoothing or
nearby-point merging. Audit88396 remains closed at six frames, but still has
66/67/71/67/69/67 degenerate triangles. It is NOT promoted into the animation.

The constrained-ear candidate preserves collinear boundaries and rejects
unresolved polygons instead of discarding points. Native attempt58197 exits1
at frame192: `No valid constrained ear; self-touching or numerically unresolved
polygon`. No completed audit receipt exists for that attempt. Transient copies
are cleaned without saving source geometry/caches. Four pure polygon tests and
three native triangulation tests cover synthetic behavior, not this rejected
real mesh. Do not rerun the unchanged failure or enable either candidate to
claim repaired contact/physics.

41 pure plus16 native tests pass (57 total); compilation and scoped diff checks
pass. Four fresh small reports are copied/hash-verified beside the animation.
After all probes/renders, the original base blend, all288 original VDBs, six
sampled native mesh files and diagnostic mesh blend hashes are rechecked
unchanged. No Blender job remains live; roughly80.11GB disk capacity remains.
Next resolve the unresolved extracted polygons without moving the free surface,
validate optics against observations, then settled circulation/budgets and full
original foam/froth phases. All eight features remain open. No playable scene,
river acceptance or20FPS claim is made by this offline diagnostic.

## Vertex-preserving triangulation integrated into animation (September30)

The previous turn is concrete progress: a daylight clip was delivered and
the failed triangulation candidate preserved. The new polygon-boundary probe
34541 captures exact frame192 coordinates without saving a scene/cache. After
exact-zero-edge endpoint welding,24,717 polygons pass and one nine-vertex
solid-contact polygon fails the custom ear clipper. It has no duplicate 3D
coordinates; dropping the dominant coordinate collapses its distinct first/last
endpoints. The repaired custom projection uses an orthonormal area-normal
plane, retaining original 3D coordinates and collinear boundaries. The exact
native polygon is now a regression fixture, including reversed winding.
True self-touching/zero-area input still rejects. No near-point weld, smoothing,
threshold relaxation, field fitting or solver change is used.

**Correction to the preceding precision interpretation:** those earlier reports
cast vertices to float64 AFTER a native float32 world transform. Float64 area
arithmetic cannot recover separations lost by that transform. Native object-
space and double-precision affine measurements now distinguish the two effects.
The unrepaired extraction at168/192/214 has41/41/39 exact zero-area triangles
(41/41/40 below1e-12m2), not101/101/102 exact zeros. Additional reported failures
are transform-rounding artifacts, with maximum displacement0.238 micrometres.
Older receipts remain unchanged. Earlier BEAUTY/constrained failure counts are
not corrected-object-space qualification; the initial custom projection failure
is independent of that measurement artifact. Blender's upstream triangulation
[projects using face-normal matrices](https://github.com/blender/blender/blob/main/source/blender/geometry/intern/mesh_triangulate.cc);
the dominant-coordinate collapse discussed here belongs to our earlier custom
helper, not a demonstrated defect in that upstream projection. No external
source is bundled or copied into the repair.

Native corrected precision probe15480 and unrepaired comparison81491 both
finish terminal0. The repaired extraction has0 exact zeros at all three frames;
frame214 retains2 positive-area triangles below1e-12m2. Corrected six-frame
contact audit94975 also finishes terminal0, closed topology at all six samples,
0 exact-zero triangles and0/0/2/0/0/0 below1e-12m2. Every distinct coordinate
and every existing oriented triangular face is retained. Only native polygon
interior triangulation and exactly coincident edge endpoints change. New
diagonals can change the interpolation of slightly nonplanar contact polygons;
do not claim identical full mesh geometry or use reconstruction volume as mass.
Floor/spur/wall have zero sampled intrusion; bed centroid residual reaches
34.75 micrometres. Contact parity still uses native BVH precision, not exact
arithmetic or exhaustive intersection/collision-dynamics validation.

The repair is integrated into a fresh two-second native animation,
`eddy-preserved-vertex-study-v1/feature.png`, not just an offline audit.
Render89867 finishes terminal0:24 frames168..214,stride2,640x360,48 samples,
12fps normal-speed APNG playback. All24 are edge-closed with0 exact-zero
triangles and unchanged distinct coordinates/existing triangular faces. All
primary/secondary counts match the earlier same-frame daylight capture. They
still contain0..4 positive-area triangles below1e-12m2, minimum9.74e-15m2;
the tiny-facet gate remains OPEN. Float64 affine geometry measurements occur
before area/volume/hash calculation; hashes must not be compared indiscriminately
with older float32-transform receipts. Three complete repaired geometry hashes
match the independent precision probe. Render times total182.23s, not game FPS.

Every decoded RGB frame exactly matches its native PNG; no adjacent duplicates.
First/middle/last actual frames were viewed. The overall surface/motion remains
similar to the preceding pale daylight study: do not advertise a new realistic
eddy, calibrated optics or absence of all temporal artifacts. Water material,
modeled lighting and original liquid evolution are unchanged; foam/bubble/spray
are still unbaked and hidden. The native repair changes surface extraction, NOT
solver contact, conserved mass, sustained circulation or the missing phases.
APNG SHA256:
`be14da8a605f99ab7ab8ff7a68c828bdbe184f3d0802f7875d14b29e76f6690a`.

45 pure and16 native regressions pass (61 total), including the captured native
polygon and a transform-rounding regression. The latter initially used a
translation that did NOT collapse its endpoints and correctly failed; a verified
3m example replaces that incorrect fixture, not its preservation assertion.
Source compilation and scoped diff checks pass. Original base/mesh blends,
all288 VDBs and six sampled native mesh files are hash-checked unchanged after
all renders. Five fresh small receipts are copied/hash-verified beside the clip.
All owned probes/audits/tests/renders are terminal; no Blender process is live.
All eight feature deliverables remain unaccepted. Next address settled eddy
circulation, boundary/mass/flux evidence and real foam/froth motion/optics;
do not mistake further micron-scale mesh checks for completing those features.
Preserve all old clips, source data and failures; no river/playable20FPS claim.

## Native secondary phases: delivered diagnostic, rejected placement (September30)

The original aligned liquid/mesh cache is preserved. A fresh independent copy
in eddy-v3-secondary-modular takes662,849,837 bytes; only cache location changes,
not physical settings. Guarded native PARTICLES bake67539 completes in93.09s,
288 secondary VDBs/3,942,088,893 bytes. No duplicate liquid/mesh cook occurs.
Saved particle-format enum2 emits an invalid-value warning, but the native VDB
stage completes and independently loads. Blender preferences, thumbnail,
extension and GPU-cache warnings also remain; this is not clean-log acceptance
or a demonstrated source-write blocker. Existing caches/clips are not deleted.

Six-frame location audit55772 finds almost all spray/foam in negative liquid
phi with full interpolation support. To distinguish classification from display
mapping, audit70232 independently reads native secondary particles, velocities,
lifetimes and type flags from the same VDBs, rather than only Blender API arrays.
At168/192/214 all counts/types/positions/velocities match the API; maximum
position component discrepancy0.477 micrometres. Spray/bubble/foam flag bits
2/4/8 also agree with Blender's [particle type definitions](https://github.com/blender/blender/blob/main/source/blender/makesdna/DNA_particle_types.h).
Raw velocity equality is not an independently calibrated physical-speed claim.

Actual rendered-mesh audit59257 uses closed collider-consistent extraction and
4096 deterministically distributed samples per phase/frame, native BVH ray
parity and nearest-surface distance. At168/192/214 respectively, spray centres
inside liquid are94.65/95.36/95.26%; foam98.71/99.05/98.71%. Submerged spray
median distances are40.94/52.57/45.49mm; foam49.26/46.17/46.67mm. Spray deeper
than one75mm cell is9.72/9.59/7.32% of samples; foam25.56/13.75/17.11%.
Bubble samples are predominantly submerged, as expected for that phase; this
does not qualify bubble dynamics or conserved gas volume. Sampling/native BVH
precision is not exhaustive exact intersection proof. The submerged spray/foam
distances exceed mapping error and drawing radii substantially; their intended
airborne/surface placement is rejected, not fixed by a renderer offset.

Full render95349 finishes terminal0. A fresh two-second APNG is delivered in
`eddy-native-phases-diagnostic-v1/feature.png`:24 native frames168..214,stride2,
640x360,48 samples,12fps normal-speed playback, not a seamless loop. All decoded
RGB frames match native PNGs and no adjacent duplicates occur. Actual first,
middle and last frames were viewed: broad submerged white grain and paper-like
ribbons remain visually unconvincing. Native foam scattering and bubble/spray
dielectric surrogates are explicitly uncalibrated, one-way subgrid presentation,
not resolved films/gas pressure/entrainment coupling. Drawing radii preserve
native variation (foam/spray about1.58..2.92mm,bubbles0.63..1.17mm at5..95th
percentiles), not measured physical gas sizes. Cached positions/types/counts
are not changed to improve the image. This clip is failure evidence, not an
accepted visual improvement. Evaluation/render cost230.90s is not game FPS.

All24 full liquid geometry hashes and primary counts match the preceding
vertex-preserving liquid-only animation. Three full geometry hashes match the
independent mesh audit; rendered phase hashes/counts match the independent
native VDB read. All frames remain edge-closed with0 exact-zero triangles;
0..4 tiny positive facets remain unresolved. After all renders, original864
cache files, copied576 liquid-data/mesh files, original/staged source blends
and sampled audit inputs are rehashed unchanged. Six small receipts are copied
and hash-verified beside the animation. APNG SHA256:
`84e1dae5fb98c590a59c680ee888c291410dc7da7c9280d73e69c8e2356326e3`.
48 pure plus16 native regressions pass (64), not feature acceptance. All owned
bake/audit/render/test/preservation processes are terminal; about75.18GB free
after receipt copies. No physical-phase correction or normal playable update
is claimed. All eight cases and the isolated-feature goal remain open.

Next inspect installed secondary classification/transport against the actual
liquid interface with independent invariants, then correct the simulation if
the evidence supports it. Do not lift particles, relabel cached phases or fit
drawing density/radius to hide failure; do not repeat this completed bake.
Sustained eddy circulation, settled boundaries/mass/flux and optical validation
also remain open. Full-river progression is not resumed by this diagnostic.

## Boundary occupancy correction candidate (September 30)

Independent native/frozen-field probes now reproduce the installed secondary
occupancy kernel bit-for-bit at frames 168/192/214. The native classifier uses
the particle's floor cell, not nearest-cell sampling: ratios below 0.4 mean
spray, above 0.77 mean bubbles, otherwise foam. The radius-two calculation
leaves near-boundary fluid centres uncomputed at zero. About 53..66% of the
baseline spray centres lie in these omitted fluid cells. Sampling both current
and previous liquid fields does not explain away the submerged phases.
These are controlled local probes, not a replay of all generation/advection.

The exact installed-build primary sources are
[secondaryparticles.cpp](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/plugin/secondaryparticles.cpp),
[grid.h](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/grid.h),
[liquid_script.h](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/intern/mantaflow/intern/strings/liquid_script.h)
and [MANTA_main.cpp](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/intern/mantaflow/intern/MANTA_main.cpp).
The local independent probe receipts are `secondary-classifier-v1.json` and
`secondary-classifier-v2.json` in the preserved v3 case; no caches were edited.

New v4 case `eddy-v4-boundary-completed` completes occupancy only at omitted
interior-fluid centres, with bounded valid neighbours and no synthetic halo.
Every native interior value must match the independent reference before the
completion is permitted. Classification thresholds, kernel radius, liquid
motion, geometry, emission potentials and native forces remain unchanged.
This is applied before native generation/transport, not cached relabeling,
particle lifting or renderer density fitting. A controlled submerged particle
near a wall now correctly receives bubble rather than spray dynamics, while
the interior control and both positions remain unchanged.

Guard 39516 finishes the new 288-frame secondary bake in 131.91s, 4,694,090,306
bytes. All 288 callbacks verify the independent reference; 577,371 omitted
fluid-cell visits are completed. This costs more time/storage than v3's
93.09s/3.942GB and is not a performance improvement. Original caches and the
independently copied liquid/mesh data are unchanged by the bake.

Location audit 49750 and independent native mapping 68342 finish terminal0.
At 168/192/214 spray counts fall from 47,922/49,693/61,052 to
20,840/28,664/27,402 (42..57% reduction); foam and bubble counts increase.
Every mapped phase type/count/position/raw-API velocity agrees independently,
maximum position component error 0.477 micrometres. This is not independent
calibration of physical secondary velocities or conserved gas volume.

Mesh audit 30146 first stops on an unresolved ray at frame214. The diagnostic
now records unknown classifications rather than treating them as outside or
relaxing the ray limit. Audit 66868 finishes as `secondary-mesh-v2.json`:
4,096 distributed samples per phase/frame; spray inside fractions are
90.67%, 93.92%, and bounded 92.163..92.188% with one unresolved sample.
Foam inside fractions are 98.39%, 98.46%, 97.56%; submerged median depths
remain 43..47mm. These are sampled native BVH measurements, not exhaustive
exact collision proof. All three liquid geometry hashes match v3 exactly.
The new renderer and encoder retain the simulation-correction metadata and
reject an unverified correction receipt. Three matched 640x360/48-sample
previews finish in 30.10s; independent phase hashes/counts and liquid hashes
match. Viewed first/last frames still show excessive submerged white grain
and broad paper-like foam ribbons. Physical and visual acceptance is rejected.

Native harness cleanup initially crashes while exception tracebacks retain
Manta children; those failed runs are preserved, not hidden. Scoped cleanup
and loaded-domain initialization allow the two new native controls to pass.
54 pure plus16 original native and2 new native regressions pass (72); these
tests do not establish hydraulics. Native preference/cache permission and
renderer/deprecation warnings remain, but source edits, baking and rendering
succeed inside the workspace. No new authority is required for this work.

Next surface-interface generation/transport with independent invariants,
not lifting cached foam or fitting particle radii. Eddy circulation and settled
mass/flux budgets remain open. All eight isolated features remain unaccepted;
normal-game integration and 20FPS have not been demonstrated by offline renders.

Full render7577 and encoder finish terminal0. The new diagnostic animation is
`eddy-boundary-completed-study-v1/feature.png`: 24 native frames168..214,stride2,
640x360,48 samples,12fps normal-speed playback,2s, not a seamless loop.
Every decoded RGB frame equals the native PNG; no adjacent duplicates. Actual
first/middle/last views confirm the remaining white-grain/ribbon failure.
All24 liquid geometry hashes and primary particle counts match the prior v3
clip, with closed edges and0 exact-zero triangles;0..4 tiny positive triangles
remain. Three rendered phase hashes/counts match independent native mapping.
Evaluation/render cost238.84s is not real-time game performance.
Eight small input/audit/capture receipts are copied and hash-verified beside
the clip, including both causal classifier probes. Source864 cache files,
copied576 data/mesh files, staged/original blends and sampled audit inputs
are hash-verified; old delivered animation remains unchanged. Phase blend SHA:
`337f8d1626f2d47cd64cdff17dd237a5f90e2622d6b39b91682d235d6b2a8fdf`.
New APNG SHA:
`94768cac923c4bbb8c3473c72b3b97faca212024ca9dd9dc91c3dc71a37ff329`.
Capture SHA:
`b1c2f86aaf11bbbb06cce1241696e3bfbd9e55a92869b6eccfcb21578bf64097`.
All owned processes are terminal; measured disk free69.55GB. No files were
deleted, no installed solver/global settings changed, no Git write attempted.
