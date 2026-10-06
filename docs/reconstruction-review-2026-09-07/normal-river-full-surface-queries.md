# Full indexed-surface queries and actual-play verification

Reviewed 2026-09-16 UTC. Query infrastructure is verified below; full-hull
collision response, default promotion and release acceptance remain unfinished.

## Complete surface query

`RaftSimSurfaceSweep` computes double-precision triangle distance with both
vertex/face directions, all edge pairs, and crossing-edge/face tests. Degenerate
triangles retain their edge/point geometry. Conservative advancement uses source
separating planes and the fastest projected vertex motion, not sampled times.
Every vertex may move independently between endpoints. The numerical skin is
10 micrometres, distance roundoff allowance 1e-10 m, and iteration bound 128.
Invalid input, initial intersection and unresolved queries are distinct from
clear results. Exhaustion never grants permission to pass through a surface.

The ground registry queries the same original collision-provider triangles and
BVH as existing contact. Moving/source face identities, barycentric coordinates,
world-metre witness positions and source component identity are retained. All
five authored raft sections remain included: 26,610 vertices / 38,344 triangles.
No hull fitting, section omission, asset edit or terrain substitution is used.

After an impact is known, other pairs need only prove clearance up to that time.
Their bounds and linear paths are restricted accordingly; every possible earlier
impact remains in scope. This is earliest-event pruning, not timestep deletion.

These are **linear vertex-path surface queries**, not exact rotational CCD,
solid containment/depenetration, a contact manifold or an impulse integrator.
They are not yet bound into playable dynamics. A clear surface query alone does
not prove that a hull starting entirely inside a closed solid is outside it.
Curved rigid rotation, deformation/contact work, initial overlap, full-step
response and packaged source availability still require integration and tests.

## Failures retained, then corrected

Initial native report `tmp/full-surface-native-v1-20260915/index.json` had 16
passes and three failures (SHA-256
`d2d0465b6af0708058aec7f505a3db7c64a8556f078572b1b33fe91c21c1bd0e`).
Near-contact witness subtraction lost direction precision against large faces.
Source face/edge separating axes fixed this without changing tolerances. The
next full-hull failure came from irrelevant events beyond an already-known
earlier impact; interval pruning fixed that. A remaining contact-normal test
then required using the robust source axis for the returned normal too.

Final Win64 Development Editor build succeeds. Final suite has **19 passes,
zero test warnings, failures or unrun cases**, including all previous 16 tests.
New coverage includes edge interiors, reverse vertex/face contact, face piercing,
coplanarity, degeneracy, changing shape, 128 analytic plane cases including a
million-metre sweep, transformed/reflected source geometry, and BVH agreement
with enumeration of every source-cube face. No existing assertion was relaxed.

All authored vertices/faces are tested in three complete-hull cases: nominal,
deformed, and a nominal-to-deformed transition during translation. Independent
analytic earliest times over every vertex agree within the unchanged 1e-9
normalized-time assertion; outward contact normals pass too.

| Full hull case | Time of impact | Analytic time | Triangle pairs | Query ms |
| --- | ---: | ---: | ---: | ---: |
| Nominal | 0.40299750190331868 | 0.40299750190734862 | 512 | 7.085703 |
| Deformed | 0.40025130589739311 | 0.40025130590139557 | 134 | 3.397498 |
| Changing shape | 0.40236467847107132 | 0.40236467847509499 | 192 | 4.077900 |

These are synthetic-ground query timings, not gameplay FPS or actual-terrain
full-hull traversal acceptance. Report `tmp/full-surface-native-v5-20260915/index.json`,
SHA-256 `fb157bd0ceddaee351122541bef13609f4c68f7ad849cadee10669ee871d0371`.
All 464 protected source/package hashes remain unchanged.

## Optimized shared hull in actual South Fork play

The fresh `shared-hull-playable-v2-20260915` replay uses the same source-matched
50-second landward preview, continuous six-support review and shared hull review.
It reaches station 8421.218 m at world time 72.159 s. Zero rejected contact-step
or hull/source/submitted-buffer mismatch entries. All 26,610 vertices and 38,344
indices/faces agree at the sampled verification events (maximum error zero).
Preparation mean reaches 3.060653 ms/substep, versus about 5.754 ms in the dense
baseline. Both recordings ran alongside the hydraulic cook; no FPS claim follows.

Log `tmp/shared-hull-playable-v2-20260915.log`, SHA-256
`2bb665d11b659e158683db8185305f70d16b5af1d246f737407e6dbd2969d21d`.
Finalized video `unreal/Saved/VideoCaptures/RaftSim_20260915-201348.mp4`, SHA-256
`d565a57ec1fbc2f7d43959dd310d5ba97a2cb0f2eca04d701fafa978d5fe1464`:
506 source frames over 64.405 seconds; 1,932 decoded frames. The unmodified
8- and 18-second frames were inspected. The raft passes the prior roof-jump
area, but broad froth and faceted inferred rock flanks remain unaccepted.
Encoded frame cadence and legacy image ROI labels are not physical/FPS evidence.
Existing experimental EditorToolset Python API errors occur at startup; this
record is not a claim of an error-free engine log.

## Ordinary performance still fails 30 FPS

After the cook exited normally, an ordinary 300-frame run used the same
1280x720/D3D12/Development settings, no recording, no shared-hull/contact review
flags and no background cook. Samples 120-250 yield **17.819710 FPS**, mean
**56.117637 ms**, **p95 81.6343 ms**, failing the unchanged 33.333333 ms budget.
This is worse than the older 24.225877 FPS sample; differing trajectories and
host conditions do not isolate a causal code regression or prove an improvement.
Water tick averages 32.593602 ms, publication 18.725893 ms and crest update
12.779653 ms; these scopes are nested and must not be summed.

Report `tmp/shared-hull-default-performance-v1-20260915.json`; CSV
`unreal/Saved/Profiling/CSV/shared-hull-default-ordinary-v1-20260915.csv`, SHA-256
`c3d20586a5eae6f318fb35f9345374990840cc0ded1d71bb26111f0e502f9094`.
No quality, timestep or acceptance gate was lowered.

## Completed landward cook; not settled

Original session75302/PID2344 exited zero after 11,000 additional steps from the
verified 50-second restart: absolute time 600 seconds. Independent 500/550/600 s
audits pass all 5,350,400 cells and retain all 86,720 artificial bank cells exactly
dry. At 600 s: depth max 4.777406207 m, speed max 11.952985593 m/s, maximum step
conservation residual 1.558858487e-8 m3. Instantaneous net flux is about -8.395445
m3/s and storage still changes: **not settled**, not promoted to normal play.

Final h/u/v SHA-256:

- `b35c69ea79fa9d125b9592b8dca63733dbc30fff1f3d9f9f5fcb84469a1b6c05`
- `bdec46a1731c84d18a9a322a4b1ec4f99f3f44dd8c20cf324bd74b7f4f1d1dc3`
- `9a254a3d37ed2f77338c2b7a355a50fb01416f1927f9a85922ce7d1ad77524d8`

An exact-state continuation is prepared in
`tmp/south-fork-landward-restart600s-input-v1-20260915/manifest.json`, SHA-256
`a4b29b3f8aaa0efba747aafdfa45a36740e22d5967f27e50c7c1b42df20b2b83`.
No context, water inventory, bed, boundary or timestep changes. The continuation
targets 1,200 absolute seconds, running as owned session84989 / PID32068, started
2026-09-15 20:41:34.944608-07:00. Output directory:
`tmp/south-fork-landward-cook600to1200s-v1-20260915`.
Independent native restart audit PASS: all 5,350,400 cells' h/u/v bit-exact,
absolute time unchanged, zero added inventory and volume error
4.656612873e-10 m3. Report:
`tmp/south-fork-landward-restart600s-native-audit-v1-20260915.json`.
Next completed checkpoint is local step 1000 / absolute 650 seconds. Revalidate
this same live process before polling; observation timeout is not solver exit.

NEXT: full-surface rigid/deforming contact response and failure handling, actual
terrain replay, initial-overlap and packaged qualification, performance and
visual correction, then safe default promotion. All later rivers, all-scene
water, crew, normalization, physical regressions and release remain open.
