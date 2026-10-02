# Eddy: explicit physical walls and standalone playback

October 1 continuation of the current isolated-water-feature goal. This
repairs the previously measured silent width mismatch, not all eddy physics.
All eight features and eventual river integration remain unfinished.

## Delivered animation and scenes

`feature.png`: a verified two-second lossless APNG, 24 frames at 12 fps,
1280 x 476. Left is standard FLIP; right is fractional FLIP with zero
artificial particle clearance. Both use the same explicit physical walls,
inlet/drain/initial water, existing floor/slope/spur, 75 mm grid and optics.
These are independently evolved liquids. Source frames 145..191, stride 2,
show 6.000..7.917 seconds; playback speed is unchanged and the restart is not
a seamless loop. Fixed frame-192 volume captions are not current-frame mass.

`standard-playback.blend` and `fractional-playback.blend` are self-contained
tiny laboratory **geometry playback** scenes. Open either in Blender and
play timeline 145..192 at 24 fps. Each actual audited surface pose is held
for two timeline frames, matching the 12 sampled frames/s of the animation.
The 24 meshes, materials, lights and synthetic flume are embedded; no external
CFD cache, linked library, image or active fluid modifier is required.
They are NOT new solvers, interpolated trajectories or accepted physics.
Metadata explicitly labels that scope and references the preserved CFD source.

Both files were reopened in independent native Blender processes. Every saved
pose/triangle matches its audited arrays (float32 coordinates bit-exact),
and 96 render/viewport visibility checks per scene include half-frame times.
Exactly one liquid pose is visible throughout each two-frame interval.
First/middle/last views were rerendered from both saved scenes and inspected.
Those six images differ from the original captures by at most one 8-bit RGB
value in a few channels; mean absolute differences are below 0.000057.
Images are therefore visually matching, not claimed bit-identical.

The animation uses 48 actual Cycles/OptiX 640 x 360 views at 24 samples,
fixed seed and denoising. Camera, lights and original water IOR 1.333,
transmission/absorption are unchanged. Actual copied 2x fluid/obstacle
zero-field meshes are checked against engine coordinate/triangle readback.
No cosmetic clipping, particle projection, smoothing/displacement or invented
foam is used. Bright reflections are not foam. Flat normals and coarse facets
remain visible; this is not accepted water/foam optics.
Every decoded APNG frame matches its composed input exactly. Caption-excluded
adjacent RGB changes span 2.259..2.546 (standard) and 2.165..2.739 (fractional).
Both surfaces visibly move. Rendering took 242.39 s, not a game-FPS benchmark.
Animation SHA256:
`81b75f23fee892995180ef52cce852425c90c1b24a0b5f4377479b845946627d`.

## Physical boundary change, not a fitted clearance

The previous study in `../eddy-fractional-controls-v1/` found implicit side
walls approximately 106 mm farther inward in fractional mode. Its initial
standard-minus-zero-clearance field-volume gap was already 0.515263 m3.
Identical authored objects had not produced equivalent effective boundaries.

This fresh pair replaces that ambiguity with explicit intended flume planes
x=0/6 m and y=-0.8/+0.8 m. The existing authored far wall's inner y=0.8 plane
is retained. New front/upstream/downstream slabs and an outer back fill provide
continuous physical boundaries inside a larger computational cage. The four
new slabs are intentionally invisible in the cutaway render/viewport; this
is the disclosed laboratory viewing boundary, NOT a hidden bank spur or
removed obstacle. All original visible solids remain visible. All eight
physical solids, including the cutaway slabs, are included in contact audits.

Five additional computational cells on EACH x/y side change allocation
80 x 21 x 42 -> 90 x 31 x 42, dimensions 6.75 x 2.325 x 3.15 m. Resolution
90 preserves 75 mm spacing; it is not a fluid-resolution refinement. Origin
is approximately (-0.375,-1.1625,-0.337499928) m. Integer padding preserves
the previous world-grid knots; domain center and the existing bottom padding
are unchanged. Existing source/collider mesh/transform/settings hashes match.
This deliberately changes the OLD effective physical enclosure; it is not
claimed identical to the previously narrowed flow.

The two NEW scenes have identical physical objects and all domain settings
except `use_fractions`. Both store zero artificial clearance; that setting
is inactive in standard mode. FLIP ratio 0.95, adaptive bounds 2/8, CFL 2,
particle/mesh radii, gravity and 24 fps are retained. Neither radius, volume,
source velocity nor physical time is fitted to improve the result.

## Native analytical preflight and actual cached-wall verification

Before baking, owned native resources prepare five analytical planes using
the installed boundary/flood-fill/extrapolation kernels. Standard/fractional
variants agree at the five stations and give identical test volumes.
The test volume is 7.591021 m3 versus a 7.680000 m3 ideal rectangular liquid
box (about 1.16% low). Thus this preflight proves **paired preparation and
station equivalence only**, not exact global geometry/volume/conservation.
The supplied coarse trilinear corner representation still has error.
No engine resource or original cache was changed by the owned controls.

Each fresh scene then completes 192 actual Blender DATA frames and 192 native
stock MESH frames. The VDB/config allocations independently confirm 90 x 31
x 42. Actual Blender-mesh-voxelized obstacle fields are sampled at fixed
stations on the downstream bed, front/far wall and both end walls in EVERY
frame. Maximum interpolated surface residual in either mode is about
1.073e-7 m; signs at -25/+25 mm are correct in every frame. This is float32
agreement at five planar stations, NOT physical submicron accuracy or an
exhaustive wall/corner/pressure validation.

| Supplied-field volume | Standard | Fractional zero clearance |
|---|---:|---:|
| Frame 1, eight subdivisions | 3.499732 m3 | 3.499676 m3 |
| Frame 192, sixteen subdivisions | 3.878032 m3 | 3.936479 m3 |
| Supplied-field bounds, frame 192 | 3.785464..3.928521 m3 | 3.839848..3.988948 m3 |

The initial difference is now 0.0000552 m3 (about 0.00158%), compared with
0.515263 m3 before the explicit-wall repair. The late difference is 0.058447
m3 (about 1.51% of standard), but these are reconstructed trilinear fields,
NOT conserved mass or proof of hydraulic/spatial convergence. Transients
and late flow still differ. Nine complete requested field frames and all
192 wall-station frames are retained in the reports.

Physical MAC velocities use 0.075 m/cell times 2.5 native seconds per physical
second = 0.1875 m/s per native unit. The C01 clocks independently record
1.999991 physical seconds over 48 timeline frames, versus 2.000000 playback
seconds. Raw display normalization is now native velocity / 90, NOT physical
m/s. Native primary velocity/unit comparisons keep those conventions separate.
This cell/clock conversion is not an independently accepted full new flume
gravity/inlet calibration or source/drain budget.

Frame-192 five-section flux estimates at x=0.6,2.1,3.15,4.125,5.475 m are
0.4847,0.5422,0.7760,0.8601,0.7535 m3/s in standard and
0.6920,0.7645,0.8529,1.0965,0.9376 in fractional mode (32 subdivisions).
Section disagreement and differing evolution remain unresolved; partial
reconstructed face integrals are not an exact conserved budget. Nominal
emitter settings are not a measured inlet discharge.

## Contact and surface continuity: progress and remaining failures

Each new control has 30 extracted field meshes: 24 animation frames at 2x,
plus 1x/4x at frames 145,169,191. All 60 pass closed-edge/nonmanifold-edge/
exact-zero-area checks after exact duplicate-coordinate cleanup only. All
54 original world-column locations are preserved by +5/+5 index shifts.
Every column is supported in every extraction; no ambiguous gap is filled
or excluded. This does not establish spatial CFD convergence.

910,482 standard and 692,838 fractional primary point records at the three
frames independently match the native cache and actual Blender display.
All records/flags are retained; no culling, clipping or contact projection.
The physical speed maximum among these samples is 2.857 m/s in standard and
3.733 m/s in fractional mode, using the explicit cell/clock conversion above.

| Worst sampled intrusion | Standard | Fractional zero |
|---|---:|---:|
| Primary floor / front / end / far-wall / outer-fill centers | 0 mm | 0 mm |
| Primary approach bed | 10.986 mm | 10.675 mm |
| Primary bank spur | 13.813 mm | 30.127 mm |
| Field-derived floor and viewing/end/far/outer walls | 0 mm | 0 mm |
| Field-derived approach bed | 10.080 mm | 10.080 mm |
| Field-derived bank spur | 20.833 mm | 20.833 mm |

The new enclosure/floor checks improve, but ALL 60 derived meshes still
FAIL authored contact overall. Neither solver mode is accepted. The stock
particle mesh is measured separately and is not promoted as a repaired
surface. Contact checks use closed-solid ray parity at vertices/triangle
centers or primary centers, 1 micrometre tolerance; not exhaustive triangle
intersection, self-intersection or finite liquid-sphere clearance. Saved
playback embeds these measured, still-unaccepted field surfaces faithfully.

## Preservation, cost and next work

The two independent source/cache directories remain under the C: artifact
root as `eddy-explicit-walls-standard-v1` and
`eddy-explicit-walls-fractional-zero-v1`. Original DATA scene is `feature.blend`;
completed stock-mesh source is `feature-mesh.blend`. DATA took 87.13/89.10 s;
guarded MESH took 46.35/45.67 s, including verification/save. These concurrent
offline timings are not isolated benchmark runs or game FPS. DATA/config
hashes are checked unchanged by meshing, extraction, rendering and packaging.
No old cache/scene/receipt/clip was overwritten or deleted. No game scene,
rebuilt launch path, Git history/branches/refs/remotes or automation was changed.

This folder contains the animation, two compressed standalone playback files
(20.31/20.71 MB) and seventeen reports. Large native caches and derived arrays
are preserved in their original directories, not copied into the repository.
Every copied file is hash-verified. Existing 156 pure numerical tests pass;
eight new Python scripts compile with SyntaxWarning treated as an error.
Those tests are supporting evidence, not feature acceptance.

Final independent preservation check rehashed 6,331 unique pinned files from
all seventeen new JSON reports and twenty-seven reports in the two previous
deliveries, with zero conflicting hashes and zero changed/missing pinned files.
The delivered APNG and both delivered playback blends were separately verified.
All owned Blender jobs have finished; no UnrealEditor process is running.
Playback SHA256 values:

- Standard: `b83b0b005caae2321e0ddeaebd7fc656d13219fd501f485339f9e1805bc51677`.
- Fractional zero: `7b6897bc8a8ba85d92ae6c531a9e5fb5303839b794ad77a582a6e06d3fb9d269`.

Scripts in `unreal/Scripts/`: `probe_water_feature_explicit_wall_preparation.py`,
`build_water_feature_explicit_walls.py`, `audit_water_feature_explicit_fields.py`,
`audit_water_feature_explicit_mesh.py`, `render_water_feature_mesh_controls.py`,
`encode_water_feature_mesh_controls.py`, `build_water_feature_mesh_playback.py`
and `audit_water_feature_mesh_playback.py`. Existing successful/pinned helpers
remain unchanged. Native checks start Blender with the exact `-b` control;
no monkeypatching or reopening a different blend after manta import.
Preference/thumbnail/OptiX-cache warnings did not prevent successful work;
no broad permission or cache deletion repair is attempted.

All geometry is synthetic authored laboratory geometry, not a measured river,
inferred underwater survey or newly licensed captured imagery. No new external
dataset/media is bundled. Keep the full goal active: coupled authored/solver/
rendered corner contact, independently qualified inlet/budgets, settled eddy
trajectories, spatial/time convergence, realistic foam/froth/optics, all eight
isolated feature animations, then realistic playable river integration.
Next resolve the slope/spur signed-field/corner discretization with a coupled
native geometry/pressure/contact treatment, not radius fitting or cosmetic
surface clipping. Do not rerun the completed boundary controls unchanged.
