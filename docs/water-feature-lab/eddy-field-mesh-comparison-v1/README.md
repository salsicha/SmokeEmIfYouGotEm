# Moving eddy: copied-field mesh comparison (October1)

`feature.png` is a verified two-second,24-frame,12fps native-view animation.
Both panels show the SAME preserved FLIP motion193..239 at24fps,stride2.
Left: original particle mesh. Right: copied fluid/obstacle zero-interface mesh,
extraction refinement2. Both use opaque blue geometry-diagnostic material and
flat triangle normals,not accepted water/foam optics. The right surface is
visibly more faceted; this is not an accepted visual improvement or solver fix.
No foam projection,smoothing,vertex displacement,radius change,retiming or
source-cache mutation. First/middle/last actual views are inspected; complete
liquid bounds fit a fixed camera with3-percent margins. All24 composed frames
decode losslessly. All23 native-content adjacent comparisons differ per panel
(mean absolute ranges1.022..1.185 and1.284..1.448),excluding captions; not proof
of Lagrangian circulation. Loop is explicitly not seamless.

## Outcome: numerical interface agreement improves; contact FAILS

All30 moving extraction meshes (24 r2 plus r1/r4 at193/217/239) have zero
boundary/nonmanifold edges and exact zero-area faces after exact cleanup.
This does not certify orientation,component links,self-intersection or swept
collision. All54 previous columns remain supported in24 matching frames.
Original particle-mesh median absolute column gaps14.240956..19.123371mm;
copied-field median0.0000567..0.0001062mm,maximum frame p950.0003568mm.
These are float32-BVH numerical vertical-query residuals,NOT submicrometre
physical accuracy,normals or material velocities. Worst retained near-contact
column discrepancy6.376805mm; do not report only the favorable median.

ALL30 sampled authored-solid contact gates FAIL: floor/approach penetration
62.5mm; r2 bank-spur maximum20.833492mm; far-wall sampled intrusion0. Actual
closed colliders are geometry-hashed and independently checked by oblique-ray
parity at vertices/triangle centroids,1um tolerance. No sampled points are
projected out of a solid. At193 original particle mesh penetrates the floor
53.749mm/spur centroid63.456mm. Field matching reduces some spur errors but
deepens floor penetration; not an overall collision improvement. Native
phi_obstacle and actual authored bed are inconsistent. Matching native fields
does not establish physical collision consistency.

Signed mesh volumes also differ with meshing refinement:193 r1/r2/r4=
3.641280/3.708063/3.726019m3,original3.525436m3;239=
3.709559/3.775972/3.793813m3,original3.594727m3. These are surface integrals,
not conserved primary mass or spatial fluid convergence. Field-value obstacle
penetration over30 meshes reaches1.2398e-5cells at vertices/0.018539cells at
centroids; field-value residuals are not geometric penetration distances.

## Extraction definition and preserved control failures

Original cell-center knots are trilinearly refined onto `(n-1)*r+1` centers,
r1/2/4. Native fine-grid positions map to base coordinates by p/r plus
`0.5-0.5/r`. Original knots remain exact; no exterior clamping/ghost extension.
Ordinary resized-center upsampling was rejected for0.625mm field shift despite
passing affine-plane tests. Nonlinear field/phase controls caught that error.

Owned extraction copy = `max(phi,-phi_obstacle)` after refinement. Native
`LevelsetGrid.subtract` is not equivalent in positive air/obstacle branches;
the explicit maximum is independently read back. Native `createMesh` negates
its input before marching at1e-4,so copy offset -1e-4 targets original zero.
The opposite sign was rejected for -0.00020027-cell plane displacement.
Reference: [installed-build source](https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/levelset.cpp)
(Apache2.0 header). Public Node/Triangle payloads/counts/indices and native
normalized OBJ are independently checked using the pinned ABI and unchanged
5e-7 decimal-export allowance. No external river imagery/underwater evidence
is added by these synthetic checks.

`interp(max(samples))` differs from `max(interp(phi),-interp(obstacle))` near
contact; marching-cube triangles also approximate the trilinear interface.
Vertex AND centroid composite/liquid/solid residuals are retained in cell-value
units,not certified physical signed distances. Worst flat-control centroid
composite residual0.333333cells; do not claim exact continuous CSG/whole-face
contact from endpoints/centroids.

Cleanup merges ONLY exactly equal coordinates and removes ONLY exact zero
cross-product faces. No epsilon weld,movement,smoothing or fitting. Float64
signed-volume before/after must agree within1e-12*max(1,abs(before)); raw OBJ
is retained separately. Independent geometry gates are not bypassed.

All51 native control cases finish in34.1328s:15 plane/orientation/grid-phase
cases plus36 preserved flat cases at0/1/24/48,r1/2/4.910 dependencies/51 raw
outputs rehash unchanged. Maximum affine interior error4.120682e-7 base cells
below fixed2e-5 allowance.24 flat columns differ from phi <=3.701157e-8m,
no axis-box vertex intrusion. These are manufactured checks,not real-water
accuracy. OVERALL QUALIFICATION FALSE: calibrated f1/r2,f1/r4,f48/r4 retain
21/27/3 boundary edges. All failed cases remain in native-controls.json;
no tolerance weld,widened gates or omission. Native v1..v7 failures remain
preserved:factory bindings,native subtract mismatch,isovalue sign,ordinary
refinement shift,1448 exact zero-area faces,then21 open edges. v8 completes
the entire cohort with hard gates unchanged. Do not rerun unchanged failures.

## Preservation,measurements and next work

Standard scene `eddy-temporal-resume-v6-m2` stays FLIP,80x21x39,75mm,min/max2/8,
time_scale1,24fps. Source/cache/compiled-body hashes remain unchanged. Actual
nominal-h origin z=-0.112499976158m uses the object's float32 translation,
versus authored -0.1125m. VDB spacing0.07500000298m is separately recorded.
Render coordinate readback/triangle indices are independently verified.
Source48-frame endpoint span1.999987793s and integrated native dt2.001926422s
remain distinct; no clock changes. No live solver functions/resources are
patched; copied-source grids and actual phi/phiTmp fingerprints stay unchanged.

48 actual views use16-sample Cycles/OptiX,denoising,seed0,same preserved
studio lights and solids. Preference/OptiX cache warnings do not prevent
complete output. Native controls30127,audit4457,render29447,encode/QA/copy
finish0; no owned Blender job remains.156 pure tests pass (11 new).
Audit51.1892s/render266.7489s are offline costs,not game20FPS.

Five project files total14764302bytes (14.08MiB),copied/hash-verified:
feature.png,clip.json,native-frames.json,native-audit.json,native-controls.json.
Animation SHA256 ae971f852489355cccdbd6ceb02fc3006dd5703d83996f6daf0fd42080d7e6f3;
clip4cd5d32f819dfe46fa031540e382fef1110cbaf26e1164112f711077fb8db66a;
audit881a61149d27f85f276196ba4623532ab1598e46d6923f4f86a674a91be885f4;
frames0e488f78c668b9614869ba38a2a56c30318398b061c28a1d519e8834777e9242;
controls e36ebfe87d692686b4cd943db21d526a4a5a6197efcdaee652d8df8a0105ec78.
Moving audit1650 inputs/90 outputs;1793 combined inputs/outputs independently
rehash unchanged. Owned raw meshes/arrays remain under visualization-root
eddy-field-mesh-audit-v1. All prior clips/caches remain preserved. No Git,
permissions,branches/history,engine solver or river package is changed.

Next compare native obstacle/obstacle-inflow zeros,flags and authored bed/spur
in matched coordinates; separate boundary-field generation from extraction.
Then validate a controlled physical repair against hydrostatics,transport/
mass/contact and time/space controls before actual foam/froth optics. Do not
repeat this completed audit,promote a flat-only radius or hide contact errors
with particles/materials. ALL8 requested features and eventual river integration
remain unfinished; full user goal ACTIVE,not complete/paused/blocked.

The existing surface-foam-review.md append was rejected by the patch writer
(file is not ReadOnly). This separate verified-artifact handoff preserves the
new evidence without overwriting that review. Scheduler is updated; no broad
ACL or sandbox change is attempted.
