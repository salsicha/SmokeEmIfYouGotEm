# Initial containment against original collision triangles

2026-09-16 UTC. South Fork contact qualification, not completed reconstruction,
normal-mode promotion, photographic acceptance, or a 30 FPS pass.

## Runtime change

The full-surface ground query previously could report clear when a connected
hull sheet started wholly inside a closed source rock. No triangle faces cross
in that configuration. The reverse configuration (ground entirely inside a
closed hull) also needs a volume test, not just surface-to-surface distance.

The source cache now classifies closed edge-connected components using exact
position aliases for split seams. It never rewrites, averages, simplifies or
moves collision vertices, faces, source identities, render geometry or beds.
Open terrain remains an open sheet, not an invented closed or extruded volume.
Every indexed connected moving component has a representative; an initial
crossing between that representative and another part is still covered by the
complete original-triangle narrow phase. Exact face-array comparison invalidates
the moving connectivity cache when topology changes.

Reverse containment checks all wholly bounds-enclosed source components,
including open source sheets, against closure rebuilt from the current deformed
hull pose. It cannot inherit closed seams from a previous pose. Source bounds
only reject impossible containment candidates; they are not collision geometry.
Confirmed containment returns initial intersection, with no fabricated normal,
impulse, position shift or penetration depth. Ambiguous closed winding refuses.
Existing adapter/bridge refusal behavior is retained; this is not depenetration,
atomic coupled rollback, or general certification of nonmanifold/self-intersecting
solids or invalid starts below an open terrain sheet.

The first implementation used a full compensated solid-angle sum for every
query. Actual replay v1 exposed severe near-rock stalls (several seconds between
rendered frames). That run was stopped by verified PID20660 / exact command and
start time, leaving its evidence intact; the separate hydraulic cook was not
stopped. Final queries use an original-triangle BVH and signed ray crossings.
Edge/parallel/near-surface numerical ambiguity falls back to the independent
full solid-angle calculation. Multiple winding is not reduced to odd/even parity.
The reference calculation remains available to tests. No skin, timestep, source
triangle, numerical acceptance criterion or quality gate was reduced.

## Native evidence

Final editor build succeeds. Fresh report
`tmp/source-containment-native-v3-20260916/index.json` has 48 successes, zero
failures, warnings, not-run or in-process tests. SHA-256:
`e669291b3f007ae4b7e337c19697f1f1f4ee76c2a75df8da908fab6d3eb34f7e`.
The earlier v1/v2 suites also passed 48 tests; they do not erase the v1 replay's
performance failure.

New coverage includes exact split seams, reversed and inconsistent winding,
disconnected moving sections, unreferenced vertices, topology replacement,
rotated/reflected/nonuniformly scaled world transforms, containment in both
directions, open surfaces and nested independently oriented solids. Another
2,048 fixed-seed points compare accelerated classification, full solid angles
and an independently defined concave L-prism volume. Existing full authored-hull,
source-BVH equivalence, sustained-contact, clock and water/foam tests remain in
the same 48-test suite. The actual 803,842-face ground cache reports zero closed
components, as intended; the engine cube reports one.

## Actual playable verification and remaining packaging failure

The rebuilt accelerated replay exits zero. At world time 72.218 s the raft is
at station 8388.416 m / lateral -7.861 m, with 149 full-hull response entries and
zero refused hull substeps, bridge latches or source/render mismatch entries.
Revision 2409 matches all 26,610 vertices / 38,344 triangles exactly, maximum
error zero. The same 6,404-face original rock solid reports one closed component;
the 803,842-face terrain and 3,214-face join remain open sheets. Source cache
build times are 23.752 ms, 3907.195 ms and 4.943 ms respectively. Large startup
cost is still unresolved. The initial several-second/frame containment stall
does not recur in this run; this is NOT an uncontended performance comparison.

Final log `tmp/source-containment-playable-v2-20260916.log`, SHA-256
`00e443cdf41e7b7503a60a960098e05b9efd66a2f978e8818607f534dd8ab993`.
Retained interrupted v1 log SHA-256:
`25237d9097d5889a306c006110442f9b69f21eabcd4a69d161013356562d2aa6`.
Final recording `unreal/Saved/VideoCaptures/RaftSim_20260915-235018.mp4` has 308
source frames / 65.093 s; encoded target 30 Hz is NOT measured 30 FPS. SHA-256:
`7308cd7893180c955f2aadc288bd2764180e8cf1f0d7eed20281b504f849f172`.
The final unmodified `_002.png` under `unreal/Saved/Screenshots/` was inspected:
broad blanket-like froth, smooth crest faces and angular inferred flanks remain.
Image SHA-256 `a78f40bf6432dc2c6a13ed183efe1bcd05ab835d828e786f8be92bb23e88be49`.
This still inspection is not continuous-motion/reference acceptance. The known
startup Python `AgentSkill` / `PythonTestRunner` errors also remain.

All 464 protected asset/data/profile hashes were checked after playback and the
read-only packaging audit; all remain unchanged. No saved map, source mesh,
material, profile or menu scenario changed. Last uncontended ordinary performance
remains 17.819710 FPS / p95 81.6343 ms, failing the unchanged 30 FPS requirement.

Read-only native audit `tmp/source-cpu-access-audit-v1-20260916.json` proves
**all three actual source assets have CPU access disabled**, collision LOD zero,
and no alternate complex mesh. SHA-256:
`f14c7c57e0a0d8574c7221523662e6efb0ff067cbba7f93c0d665c6b17e94dc0`.
Thus their successful editor-mode triangle queries do not establish packaged
readiness. Next: retain source-exact CPU collision data through asset generation
and cooking, verify native readback/source identity and a real packaged run;
do not replace missing triangles with a simple collider or claim a flag alone
is packaged acceptance. This is an actionable project prerequisite, not a user
blocker, and not a reason to forget visible breaking/froth and normal integration.

## Corrected hydraulic domain

Same owned session69275 / PID27776, started 2026-09-15 23:15:42-07:00, output
`tmp/south-fork-landward-context950to1200s-v1-20260916`. Independently audited
completed absolute 1000 and 1050 s snapshots both pass all 5,356,800 cell checks
and all 86,720 exact-dry artificial-bank face checks. No restart on timeout and
no transfer from an older rock geometry. These are the checkpoint times that
failed in the superseded domain; its old evidence is retained.

At 1050 s maximum depth is 4.613871880 m, maximum speed 6.918077574 m/s, maximum
step conservation residual 1.350965151e-8 m3, and all artificial bank depths are
exactly zero. Storage has fallen 1,999.106752229 m3 from the exact 950 s restart;
net boundary flow is still about -22.332355 m3/s. This is NOT settled flow.

Reports in `tmp/`, with SHA-256:

- `south-fork-context1000-snapshot-v1-20260916.json`:
  `a03f94abd4ebfe7a6f73323d3b21250f8d65972e52a9b37ae22231ddcfa20869`.
- `south-fork-context1000-banks-v1-20260916.json`:
  `f1302e103fba14e846c39645f3e176a3dc7da4d2e11941b09bfb391bba150fa5`.
- `south-fork-context1050-snapshot-v1-20260916.json`:
  `1345696a6ba628d7cd1ab7a2428ced89c26ca92af2bc98240afc9b41ff614b97`.
- `south-fork-context1050-banks-v1-20260916.json`:
  `7e95e33b4025af3425dab78947e42dc621ccfe8e0c93aee8b402a0a51492c5c1`.

## Remaining delivery requirements

No default promotion follows from these fixtures. Full-river qualification,
packaged source-triangle availability, startup/runtime cost and the remaining
contact/physical gates must be verified. UE 5.8 `StaticMesh.cpp:9272` explicitly
requires CPU access outside editor builds; it also requires retained CPU data
on the selected collision LOD. Editor tests cannot substitute for a packaged run.
Source-supported flanks, convincing breaking/froth motion, ordinary 30 FPS,
normal playable integration and all later requested work remain open. Troublemaker
is still a rapid inside South Fork, never a separate scenario.
