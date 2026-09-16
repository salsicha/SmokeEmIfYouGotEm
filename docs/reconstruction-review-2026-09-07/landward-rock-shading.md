# Source-preserving rock shading and the returning domain failure

September 16, 2026. Visible local shading improvement in the existing playable
South Fork scenario, **not reconstructed-shape, water, performance or release
acceptance**. Troublemaker remains a rapid inside South Fork, never a menu item.

## Attribution and reference

Inspected `spatial-range-default-playable-v1-20260916_002.png` at the actual
camera (-545900,-362700,2000) cm, pitch -35.27, yaw 46.85, horizontal FOV 90,
1280x720. Two-sided source-triangle rays through pixels (200,270), (300,230),
(400,315), (400,550), (520,620) first intersect the added landward cap at faces
361,798,2306,1753,2066 respectively. Pixel (120,420) hits original terrain face
162839. These are geometric rays, not GPU object-ID evidence; they omit water
and foliage. Unlike the earlier old-axis camera, the current dominant faceting
is on the added cap. Its exporter explicitly flat-shaded every triangle.

The [Qweniden bank-side video](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
remains accessible. Replayed and inspected the paused 0:27 image through the
in-app browser, without downloading. Exposed rocks have irregular fracture
faces, not a uniform triangulation pattern. This is qualitative evidence, not
camera registration, calibrated dimensions, measured normals or bathymetry.

## Implementation and unchanged geometry

`rock_corner_normals.py` builds angle-weighted, edge-connected normal fans.
Edges split at the authored crease angle, between provenance kinds, at
boundaries/nonmanifold edges and at inconsistent winding. Coincident source
positions are not welded. No smoothing, displacement, simplification or vertex
movement occurs. Invalid indices, degenerate triangles and invalid crease angles
are refused. A custom-normal FBX import explicitly disables normal recomputation.

The exporter retains its old flat default and exposes
`--crease-angle-degrees 45` for this candidate. This angle is an **authored
shading choice**, not a measured fracture criterion. It does not fix the
unmeasured vertical flank hypothesis or sparse/interpolated source geometry.
The unchanged source cap is
`tmp/troublemaker-source-connected-landward-v1-20260915/original_return_rock_cap.npz`,
SHA256 `78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb`.

Fresh export: `tmp/landward-crease45-export-v1-20260916`, all 3,202 vertices and
6,404 triangles; 8,262 smooth and 1,344 split edges, 4,742 normal fans. Blender
positions match the source converted to its float32 storage exactly, with exact
face order. `audit_rock_shading_pair.py` independently reads both native meshes:
all **6,404 directed triangles / 19,212 expanded positions are identical**,
including winding. **9,308 corner normals change**. Native vertex splitting or
reindexing is allowed; changing a position or reversing winding fails.

The existing native actual-map union audit passes all **30,403 probes** at the
unchanged 0.1 cm gate, and all **12,800 native initial-water queries**. This uses
the SAME landward 50-second water/bed/coordinate state, not the later wet-bank
checkpoint. Candidate bounds, complex collision, complete Nanite fallback and
triangle count are verified. The original material and world projection remain
unchanged. All **464 protected source/actor hashes match** after playback.

## Actual playable comparison

Generated candidate only:
`/Game/RaftSim/Environment/GeneratedLocalReview/LandwardCrease45Stage20260916/SM_OriginalReturnRockSolid`.
Bound descriptor: `tmp/landward-crease45-preview-v1-20260916.json` (3,256
dependencies). No saved map, scenario/profile, original asset or material changed.
All generated exports/assets/captures remain ignored.

Reproduction uses the existing joint-preview, full-hull and shared-hull flags,
scenario `south_fork_full_descent`, review station 8330, D3D12, 1280x720, and:

```text
-RaftSimJointReconstructionPreview=tmp/landward-crease45-preview-v1-20260916.json
RaftSim.CaptureSeries 12 3 10 landward-crease45-playable-v1-20260916 -545900 -362700 2000 -35.27 46.85 record
```

Log proves candidate installation before BeginPlay and one water surface.
Three capture requests occur at world 12.600 / 22.213 / 32.289 s, with identical
camera metadata. Final station is 8355.552 m, lateral -5.879 m. Shared hull/render
revision 1209 has 26,610 vertices / 38,344 triangles and zero position mismatch.
Inspected the new `_002.png` against the old camera-matched capture: much less
triangle-by-triangle lighting, retaining steep edges. Roof shading is smoother;
several inferred walls and abrupt geometric transitions remain unconvincing.
These are separately evolved runs, NOT identical animated-water states.

Recording `unreal/Saved/VideoCaptures/RaftSim_20260915-230456.mp4` finalized:
111 source frames over 25.059 s; all 752 encoded frames decoded through 25.0333 s.
Inspected extracted 8/16-second frames, not continuously watched full motion.
Raft and water change while rocks remain stable. Broad white cover and smooth
green wave faces remain unacceptable. Encoded 30 Hz / duplicated frames are NOT
game FPS. Legacy decoder ROI names do not identify this camera's physical regions.
No new uncontended FPS measurement: last 17.819710 FPS / p95 81.6343 ms still
FAILS the unchanged 30 FPS / p95 33.333333 ms target.

Final related Python selection: **114 passed**, including shading, native-pair
logic, preview binding, staging and source geometry. Initial test invocation
missed the local pytest path; a concurrent run printed a Windows WMI exception
despite completing 110 tests. Final standalone XML records 114/0. No C++ changed.
Runtime still logs the previously known experimental Toolset missing
`unreal.AgentSkill` / `unreal.PythonTestRunner` errors; not a clean release run.
The staging engine returned exit 1 despite its successful report and clean
shutdown log; subsequent independent mesh readback and gameplay both exit 0.

## New hydraulic domain failure

The SAME landward cook (session 84989 / PID 32068) was confirmed live, not
restarted on timeout. Its 1000 and 1050 s states pass finite/depth/speed/mass
audits for all 5,350,400 cells, but **fail the unchanged exact-dry bank gate**:

| Absolute time | Wet bank cells | Maximum bank depth |
| --- | ---: | ---: |
| 950 s | 0 | 0 m |
| 1000 s | 3 | 0.00000100624796688 m |
| 1050 s | 7 | 0.114371694740141 m |

All wet cells belong to `core_0201`, south edge. Core center is UTM
(675280,4295200); requested neighboring center is (675280,4295120), about
8.5 km from Troublemaker. The earlier September 12 reconstruction encountered
this exact edge and recovered a source-backed dry context tile. That old
evolved water must NOT replace the current landward state.

At 1050 s volume is 3,024,351.4993072255 m3, max depth 4.6138718801 m, max speed
6.9180775743 m/s. Outflow 67.6393094652 vs inlet 45.3069545472 m3/s also rejects
settling. Maximum step mass residual remains 1.43598699598e-8 m3. Successful
finite/mass checks do not repair a wet artificial wall.

Corrected continuation starts from this cook's last exactly dry 950-second
checkpoint (local 7000), selecting context with the later verified 1050-second
bank observation. Immutable input:
`tmp/south-fork-landward-dry950-context-input-v1-20260916/manifest.json`, SHA256
`ecd316f3ed8c1edab08a678cc232b9789a030437146bb4ae48653b21ad50d87b`.
One added tile `context_0836`, 6,400 source-exact cells, **zero added water**.
Every retained geometry record and terrain-union identity is exact. Applying
the current landward rock union to the added tile changes zero samples.

One-second native pilot FINISHED (session 55791, exit 0):
`tmp/south-fork-landward-dry950-context-pilot-v1-20260916`. All 5,356,800 state
cells pass and all 86,720 artificial-bank face cells are exactly dry at 951 s.
Six restart-metadata tests pass. Both pilot and actual continuation frame zero
independently prove all 5,350,400 retained h/u/v cells bit-exact, unchanged
original bed/grid/roughness/physical boundaries and clock; inventory error is
4.65661287308e-10 m3, with no added water.

**CURRENT LIVE: session 69275 / PID 27776**, started
2026-09-15T23:15:42.037981-07:00. Output:
`tmp/south-fork-landward-context950to1200s-v1-20260916`, 5,000 additional steps
at unchanged 0.05 s, snapshots every 1,000. Latest handle revalidation: local 60
/ absolute 953 s. NEXT complete local 1,000 / absolute 1,000 s state AND bank
audits. Native solver remains SHA256
`7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f`.
No settling/runtime promotion follows from the one-second pilot.

Only after pilot and actual restart verification, stopped superseded PID 32068
with exact executable/start-time checks. Session 84989 is terminal exit 1;
last logged step 9630 / absolute 1081.5 s. All old files retained. Later water
evolved against the affected bank was NOT transferred. This replacement corrects
an observed domain failure, not an observation timeout. No boundary clipping,
gate relaxation, invented elevations or old-geometry water-state transfer.

## Evidence SHA256

```text
export manifest e26561922fd1f2ea3c3c684ef521a5604c79c896fa9765f4916a7521ee8bf4eb
FBX f97d56325291d36291ef528dcbd21b5e22307908c0dc93b601d459f5fa91c98f
staged mesh 7870093f88fbbc37d539570dfd64b2c1bbb37430f64a44f9849b428743b135ff
native pair 508a6aaed064b99d4d80f3ba8b91bd096928207e2ebeefe2343658a0c583c75a
native union d7f903bca85eeb707c35a5d5eaef65200f09613947bd85326f30444909bdd9aa
tests XML 7b990e9f1ee6b40422fb435c4faf93116ad489bbc0db26fd13e7a993ed77bc06
descriptor 82956806b1476ebeaad3e5791616d6ccac181d9f5822ec60da0e337087e6afb2
playable log 53127f1ea774f8ad6dcead8f4c75e55e7cb05b371a0039f99bf740f197e4d1c8
still _002 1573d9e44009dc9ca37cb38e899e90d9d5b4ed83e25bbaafc1b0e4cdfca22a2c
recording d980330ca926f1f44c382f83ea8a0143553a9281a40992790a92a36c1a31a503
1000s bank audit 15ea93bc4e7ef65499fc5a08a0a3ad851de0f1eb7f6bf6daf9fe731447aa22e4
1050s bank audit 56859b24aecb1d5fc14c38f8f067ad7e0e7cea3c15643cb68e04db3cf108693e
corrected pilot bank audit 7d565e97450c998cec8253f5c5e5e1b9b7c96dd56774ff511fd722a261018221
actual corrected restart audit 9c900cca17947473074bd56fd696b38fb0cc7e4052cdab10d663804781230e96
```

South Fork remains OPEN: source-supported geometry/flanks, domain/settling,
breaking/froth motion, contact/default integration, performance and regressions.
Then Colorado -> Pacuare -> Futaleufu; Chilko/Zambezi/all-scene water, crew,
normalization and release remain OPEN. This does not reduce the full objective.
