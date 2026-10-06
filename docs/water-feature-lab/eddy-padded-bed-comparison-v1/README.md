# Eddy: computational bed-boundary control

October 1 continuation of the current **isolated water-feature goal**, not
full-river acceptance. All eight features and eventual river integration remain
unfinished. No case accepted. Preserve the old scenes, caches and clips.

## Visible delivery

`feature.png` is a verified two-second lossless animated PNG: 24 frames at
12 fps, 1280 x 476. Both panels show actual native FLIP evolution at simulation
frames 145..191, stride 2 (6.000..7.917 seconds). Playback speed is unchanged;
the restart is explicitly not a seamless loop.

Left: original computational boundary. Right: three additional grid cells
below the **unchanged** authored bed. These are different evolved liquids,
not different meshing of the same motion. Both use copied fluid/obstacle
zero-field meshes at 2x extraction refinement, the same physical flume,
lights, fixed camera and original water shader (IOR 1.333, transmission and
absorption). Flat triangle normals, no smoothing/displacement/contact clipping,
no invented foam, spray or whitewater. Specular highlights are not foam.

48 actual Cycles/OptiX views at 32 samples were rendered; first/middle/last
native views and the final composed view were inspected. Every decoded
animation frame matches its composed source exactly. Motion checks exclude
captions: adjacent mean absolute RGB changes range 0.875..1.139 in the old
panel and 0.850..1.142 in the padded panel. Both liquids visibly move, but this
is still a coarse, faceted synthetic-flume study, not realistic accepted foam
or water optics. Clip SHA256:
`008e75180f1d4c61bc27a52297c52b3bcb3b81da344f2b0b74f54607f8a5554e`.

## Actual boundary repair, not a cosmetic surface correction

The old downstream bed surface at (4.05, 0, 0) has cached obstacle value
approximately **+5 cells**, rather than zero. Its center-line bottom obstacle
column is `[-1, 5, 5, ...]`; the first interior row is fluid. This persists
across all 192 inspected old frames. An enabled floor object alone does not
establish that the solver represents its physical surface.

Six independent installed-native-kernel controls locate the loss in obstacle
preparation. A plane at grid coordinate 1.5 has negative values only in the
excluded bottom row and zero/slightly positive values in the first interior
row. Native inside/outside extrapolation loses that interface. The same
plane at coordinate 4.5, with three extra cells beneath it, preserves it for
all tested phases (-1e-6, zero, +1e-6 cells). These are owned analytic grids;
the controls do not alone establish a full scene fix.

The fresh actual scene now confirms the mechanism through a full 192-frame
DATA bake: downstream obstacle rows are `[-0.5, -3, -2, -1, ~0, 1, 2, 5, ...]`.
The authored bed value remains approximately 9.54e-7 cells throughout all
192 frames. Interior cell centers below it are marked solid. An intersected
cell is not entirely solid in this non-fractional discretization; do not
interpret its categorical flag as exact pointwise collision geometry.

Physical effector/source mesh hashes, transforms, settings, initial water,
inlet, drain and gravity match the preserved source. Resolution remains 80
on the 6 m longest dimension, 75 mm cells, FLIP ratio 0.95, adaptive bounds
2/8, 24 fps. Only computational bottom padding changes: allocation
80 x 21 x 39 -> 80 x 21 x 42. The lower origin moves from approximately
-0.1125 to -0.3375 m. Original world-grid knots agree within 47.7 nanometres
(stored float32 transform rounding), **not bit-exact world coordinates**.
The physical bed and its collision thickness are not moved or inflated.

## Physical/contact evidence and remaining failures

Primary particle positions and velocities were independently loaded through
the native typed cache reader and matched against Blender's actual particle
display at frames 145, 169 and 191 in both controls: 672,313 point records
in total. All points are included; no particle/contact projection or culling
was used. These are point-center tests, not liquid-sphere or mesh clearance.

| Measurement | Original | Padded |
|---|---:|---:|
| Worst sampled primary-center floor intrusion, three frames | 37.288 mm | 0.604 mm |
| Worst sampled primary-center approach-bed intrusion, three frames | 37.288 mm | 8.588 mm |
| Worst sampled native particle-mesh floor intrusion, 24 frames | 53.749 mm | 54.726 mm |
| Worst sampled field-derived mesh floor intrusion, 30 extractions | 62.500 mm | 0 mm |
| Worst sampled padded field-mesh approach-bed intrusion | -- | 8.139 mm |
| Worst sampled padded field-mesh bank-spur intrusion | -- | 20.833 mm |

The field-derived floor surface improves and primary floor penetration is
substantially reduced; **the stock particle mesh does not become correct**.
Contact near the slope/spur also remains wrong. Do not silently use the
derived surface as proof of a corrected solver, or enable a known broken
stock mesh in the game.

Each control has 30 extracted meshes: all 24 animation frames at 2x, plus
1x/4x at first/middle/last. Every padded derived mesh passes the closed-edge,
nonmanifold-edge and exact-zero-area checks after exact duplicate-coordinate
merging only. This does not test self-intersection. All 30 still FAIL authored
sampled collision acceptance. Contact tests use closed-solid ray parity at
vertices and triangle centers (1 micrometre tolerance), not exhaustive
triangle intersection. No collider is hidden to improve the result.

The complete original 54-column interface cohort is retained. Frame 147's
column [24, 15] is ambiguous and explicitly unsupported; the other animation
frames have all 54 columns supported. Do not fill that column or discard it.
At frame 145, worst mesh/field column gap changes 22.961 -> 3.447 -> 0.000329 mm
at 1x/2x/4x extraction; at frame 191 it is 23.581 -> 3.327 -> 0.000409 mm.
Small residuals are float32 BVH/trilinear agreement, not physical submicron
accuracy. Increasing mesh refinement is **not** fluid spatial convergence.

Both native C01 clocks measure 1.999991 seconds over frames 144..192, compared
with 2.000000 playback seconds. No changed time scale or retiming. Full
trajectories, conserved mass/section budget, temporal/spatial convergence,
foam/froth transport, shoreline stability and water optics remain open.

## Reproducibility and preservation

New native scene/cache, not an old-cache edit:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/eddy-padded-bed-v3/`.
`feature.blend` is the completed DATA scene; `feature-mesh.blend` is the
separate completed native stock-mesh scene. Native DATA and stock MESH both
cover 192 frames. Mesh baking verified DATA/config hashes unchanged.
The new cache occupies about 528.69 MiB. No old cache was freed or deleted.

Reproduction scripts are in `unreal/Scripts/`: `build_water_feature_padded_eddy.py`,
`bake_prepared_water_feature_data.py`, `bake_water_feature_padded_eddy_mesh.py`,
`audit_water_feature_padded_eddy.py`, `audit_water_feature_padded_particles.py`,
`render_water_feature_padded_eddy.py`, `encode_water_feature_padded_eddy.py`.
The two native bed probes are `probe_water_feature_obstacle_fields.py` and
`probe_water_feature_bed_preparation.py`. Successful receipts hash-pin sources;
do not change pinned helpers and pretend old receipts validate new code.

Native bindings in this build must be initialized by starting Blender with
the exact `-b` panel scene before importing the native helper modules. Opening
a different blend after importing manta invalidated inherited methods in the
first audit attempt; that attempt wrote no accepted report and is preserved.
Do not monkeypatch native classes to bypass the failure. Simple playback
also does NOT imply that live solver grids contain the cached DATA fields;
the original obstacle probe records those mismatches rather than hiding them.

Two preparation attempts stopped before padding: v1 rejected baked/unbaked
metadata differences, v2 measured evaluated liquid dimensions rather than
the authored domain cage. Both are marked REJECTED-BEFORE-PADDING and were
not baked. v3 passes the corrected guard. No unchanged failing simulation
was rerun. Thumbnail/user-preference/OptiX-cache permission warnings did not
prevent native baking or any of the 48 renders; no broad ACL/cache deletion
was attempted.

This folder preserves the clip, native render/mesh/contact reports, original
obstacle profiles, six analytic native preparation controls, preflight and
DATA/MESH receipts. Source caches and large derived arrays remain in their
original dedicated directories, not duplicated here. Every copied file was
hash-verified. Independent final verification rehashes all 3,292 unique pinned
dependencies and outputs across the eleven delivered JSON reports, with no
conflicts or changes; the delivered clip hash also matches. Existing 156 pure
tests pass; eight new/continued script files
compile with SyntaxWarning treated as an error. These are supporting checks,
not feature acceptance.

Native DATA took 41.11 seconds; guarded MESH stage 28.16 seconds including
verification/save, and 48 transparent-water renders took 245.82 seconds.
Timings are offline and not isolated benchmark runs or game FPS. No normal
playable scene/build was modified in this isolated-feature continuation.
All owned Blender jobs have finished. No Git/ref/history/remote changes.

All flume geometry is synthetic authored laboratory geometry, not a measured
river or inferred underwater survey. No external captured media or new river
dataset is bundled or given an invented license. Native implementation
reference is the exact installed Blender build fbe6228777e7; the captured
compiled obstacle-preparation instructions and executable controls are the
evidence for the behavior reported here.

Next: independently resolve authored slope/spur versus cached obstacle zero
surfaces and primary contact, then collider-consistent meshing without radius
fitting or cosmetic clipping. Retain the padded scene as a real boundary
control, not an accepted final eddy. Continue all eight feature validations
and eventual river work under the current goal.
