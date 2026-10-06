# Full-hull response and geometry-preserving query cost

2026-09-16 UTC. This is an opt-in integration checkpoint, not completed South
Fork, photographic acceptance, packaged qualification or a 30 FPS pass.

## Integrated contact, with explicit limits

Commit `15ea04a39` integrates all 26,610 authored vertices / 38,344 faces / five
sections through `RaftSimFullHullGroundReview`. The exact fixed-step hull drives
collision and the submitted render geometry. No six-support or roof-projection
fallback occurs in this mode. Original source triangles and source identities
remain intact; authored hull geometry is not a measured raft scan.

The rotating, linearly deforming hull is enclosed around each chord using
`(omega^2 * radius + 2 * omega * shape_speed) * interval^2 / 8`. Intervals refine
without discarding elapsed time or decreasing the 10-micrometre physical skin.
The tested maximum curved-path enclosure is 1.25 micrometres. Source witnesses
drive coupled rigid impulses. Prescribed shape work, dissipated energy and
kinetic change are recorded independently. This is NOT a closed D4 elastic
energy budget. Initial surface intersections refuse; closed-solid containment
and depenetration remain unfinished.

Failed raft substeps now latch the bridge until reconfiguration and cannot
silently commit the coupled clock or repeatedly advance the water. Water and
earlier raft substeps may already have advanced: this is NOT atomic rollback.
The failure latch also fixes the normal path's previously ignored return value.

## Native evidence

Final integration build succeeded, with the existing two D6 double-to-float
warnings. `tmp/full-hull-response-native-v4-20260915/index.json`: 27 successful
tests, zero failures, warnings, not-run or in-process results. SHA-256:
`b8bd850a54fdc8937e51d43e5d2c06059718c4ece4d1fc7476babf504cca6e89`.

Coverage includes 600-step sustained supports with and without initial spin,
deformation work balance, 8,181 independently sampled curved-path positions,
adapter publication refusal, coupled-clock failure latching, complete authored
surface queries and existing buoyancy/ground-contact regressions. Earlier v1/v2
runs each had one zero-time-contact failure; still-entering witness selection
and interval refinement resolved those cases without loosening assertions.

An endpoint-plane clearance proof avoids expensive feature distances only when
the complete swept linear convex enclosure is separated. Same-input proof
timings for 512 clear pairs were 0.063907 / 0.063401 ms versus reference 0.931293 /
0.941206 ms in opposite execution orders. Those are query microbenchmarks, NOT
game FPS. Native fixtures do not establish general visual/physical acceptance.

## Actual replay remains slow and visually unfinished

The source-matched 50-second landward hydraulic state and existing South Fork
scenario are unchanged. No new Troublemaker menu scenario was added. The full
hull baseline and plane-proof replay both exit normally without rejected hull
steps, latched failures or source/render mismatch entries. These statements do
not cover unrelated existing EditorToolset startup Python errors.

Plane-proof replay `tmp/full-hull-response-playable-v2-20260915.log`, SHA-256
`d82cbe45bdc9b7b021bb219dd9ef5ec66a51d13f471e57d71ba9f61fdde0afea`, reaches
station 8369.132 m at world time 72.534 s. Revision 1209 has exactly matching
source/render vertices and faces, maximum error zero; hull preparation averages
3.156847 ms per substep. The baseline reached 8369.714 m at 72.360 s. World time
is NOT consumed fixed-step simulation time; these do not prove full traversal.

Final video `unreal/Saved/VideoCaptures/RaftSim_20260915-211906.mp4`, SHA-256
`71e90dc92ae786257622dd48234851ea358d3b2b0daf62ba4aa401ebf1a1faaa`, contains
194 source frames over 72.406 seconds, decoded to 2,172 frames by the encoder's
duration-preserving repetitions. This is NOT measured physical/render FPS.
Baseline 36/60-second and plane-proof 60-second unmodified decoded frames were
inspected: broad blanket-like froth and faceted inferred rock sides persist.
Legacy ROI names belong to another camera and are not semantic foam evidence.

The last uncontended ordinary profile still fails: 17.819710 FPS and p95
81.6343 ms versus the unchanged 30 FPS / 33.333333 ms requirement. No quality,
physics timestep, geometry or acceptance threshold has been lowered.

## Grouped exact-source broad phase

The next candidate shares upper BVH traversal across 64 consecutive authored
faces. Their union bounds contain every start/end vertex; every individual face
still uses its own bounds and original source-triangle narrow phase. Candidate
leaves retain the exact reference DFS order, including first-hit tie behavior.
There is no hull simplification, support subset, changed skin or timestep.

The original traversal remains selectable for same-input tests. Full production
hull comparisons use both the 48-face engine cube and all 803,842 captured ground
faces, with translated/rotated/reflected source transforms, clear paths,
crossings and independently changing endpoint vertices. In both timing orders,
status, pair count, source/component/face identity, TOI, witnesses, normals and
iteration count match exactly. This is fixture evidence, not every possible
input or initial-containment acceptance.

Three captured-ground queries total 17.373301 / 16.735900 ms in the reference
versus 8.353498 / 7.731702 ms grouped, in opposite execution orders. Cube queries
total 5.311895 / 5.773500 ms reference versus 4.804198 / 4.691601 ms grouped.
Build succeeded; 28 focused native tests pass with no warnings/failures/not-run.
Report `tmp/full-hull-grouped-native-v1-20260915/index.json`, SHA-256:
`49db1385371ad2f422e9e8a6a7bd8fe29518aa7d6ab4d53bb904f155862e1aad`.
The final candidate also computes identical source-local coordinates once per
original vertex, instead of repeatedly for each face/group. The original path
retains its repeated arithmetic for comparison. Final build succeeds and all
28 tests pass again; report `tmp/full-hull-grouped-native-v2-20260915/index.json`,
SHA-256 `b4fffbb3edb1f4ae1d08fa30f644797f65a9a284cb37f8987ae64b22e1b00cf1`.
Captured-ground totals in this run are 27.600102 / 28.186001 ms reference and
12.524202 / 11.865400 ms optimized. Different host contention prevents comparing
absolute times across runs; same-run pairs retain exact answers in both orders.
The additional temporary coordinate arrays use 1,277,280 payload bytes for the
26,610-vertex hull (two arrays of double-precision vectors), plus allocator
overhead. They are per-query, not temporal caches. No gameplay FPS claim.

The grouped-only extended replay v3 exits normally, reaching station 8429.857 m
at world time 132.137 s. Zero rejected full-hull steps, bridge latches or mesh
mismatch entries; sampled revision 4809 has zero source/render error. Log
`tmp/full-hull-response-playable-v3-20260915.log`, SHA-256
`416ed287df0802761214f7680fd0b3fdff5c172b8fdd7f396663654ec46bf0c7`.
Video `unreal/Saved/VideoCaptures/RaftSim_20260915-212657.mp4`, SHA-256
`a4053325c149ddbe6011487d395a9260268c1d8775e7ea88d96c269b3fde8c06`:
670 source frames / 124.946 s, 3,748 decoded frames. Inspected unmodified 20/60 s
frames show the raft moving beyond the static camera view; froth and inferred
flanks remain unaccepted. This is neither full-river traversal nor real-time
performance acceptance. All 464 protected asset hashes remain unchanged.

Final coordinate-reuse replay v4 also exits zero. It reaches station 8430.210 m
at world time 132.191 s, with 213 response entries, zero rejected hull steps,
zero bridge latches and zero hull mismatch entries. Log
`tmp/full-hull-response-playable-v4-20260915.log`, SHA-256
`f9ccf0e9579997dae2521d2e20465fb95b4dc90dbe4f9e920f7269f7a51ea503`.
Final video `unreal/Saved/VideoCaptures/RaftSim_20260915-213233.mp4`, SHA-256
`0e84820f82a509fd58799d55e3b4344f2b4a913df2728970019a0d5b68a70ce4`:
672 source frames over 125.041 seconds, decoded to 3,751 frames. Unmodified
20/60-second frames were inspected; the same broad froth and faceted inferred
flanks remain unaccepted. Both extended runs execute alongside
the same cook and recorder; neither is an uncontended ordinary FPS measurement.

## Live hydraulic continuation

The exact-state 600-to-1200-second continuation remains the same process,
PID32068 / owned session84989, started 2026-09-15 20:41:34-07:00. It was verified
live during this review; observation timeouts never trigger a restart.

Independent completed 650- and 700-second cell/bank audits pass. At 700 seconds,
all 5,350,400 cells are finite, maximum depth is 4.726705879 m, maximum speed
9.597563156 m/s, and all 86,720 artificial bank-face cells are exactly dry.
Maximum step mass residual is 1.435986996e-8 m3. Storage has fallen
1,006.188341497 m3 since the exact 600-second restart; net boundary flux is about
-10.751441 m3/s. Still evolving, NOT settled or promoted to normal play.

Reports: `tmp/south-fork-landward-700s-snapshot-v1-20260915.json` and
`tmp/south-fork-landward-700s-banks-v1-20260915.json`. Final 700-second h/u/v hashes:

- `e88ae919bbfb32789e13e271630ba1488580f3a85a3428407ac88b0c80a56f47`
- `52d405ddc2e51ccb3a1f4cf6943ec9d75fe3aef9e1450afdf399c9ed136a766e`
- `b8638f14354172cd94ce4c9113360e82af1ad1832b1ace026346f89789fc481f`

The subsequent completed 750-second snapshot/bank audits also pass, with all
5,350,400 cells checked and all 86,720 bank-face cells exactly dry. Maximum depth
4.704128709 m, speed 9.597578200 m/s, mass residual unchanged; storage has fallen
1,578.872593059 m3 since restart and net boundary flux is about -11.736194 m3/s.
NOT settled. Reports use the same `750s` naming. h/u/v hashes:

- `e06139d68d3cc21d65d149b6a3458807553f8c5e5a19a6cbac0187e965588bec`
- `7e2658e832e594b341e17a42b2ebe52dedd718ae208490fbcb79c918a82dc582`
- `5a15db95d5965b776a4f1af03827cf5a49f5c92786f5e06d605ce1ef6d7c46b5`

Next completed marker is local step 4000 / absolute 800 seconds, in the same
live continuation. Do not restart on timeout.

## Next foam evidence must use the active scene

The actual replay logs carrier=1, volumeCore=1, singleSurface=1 and the existing
South Fork transmission material, with moving 128x128 / 0.5 m finite-depth
detail. `FRaftSimDetailEntrainment::Build` replaces the preliminary Froude field
with empirical convergence/deceleration entrainment, then merges accepted crest
source by maximum (not addition). The live v4 startup samples 297 augmented wet
cells, maximum added source 0.841176093 and crest source 0.850000024. These are
not measured bubble-production rates or proof of the cause of every white pixel.
`RaftSimDetailWater.usf` transports density with source/decay; resolve maps it to
coverage. Next collect paired current-scene source/density/render coverage and
compare source-localized motion with reference video; do not reduce foam gain
to conceal an unresolved physical or optical cause. Earlier September 7 material
diagnostics alone cannot qualify this current scene.

NEXT: query/runtime cost and extended actual traversal; initial-overlap and
packaged-source qualification; source-supported rock sides and crest/froth
correction; then safe normal-play promotion. Colorado -> Pacuare -> Futaleufu,
Chilko/Zambezi and all-scene water, crew, normalization, physical regressions
and release remain open.
