# Current-oriented crest and froth integration — September 12

Status 09:51 UTC: rebuilt runtime, twenty native/D3D12 checks plus two actual-game
checks pass. Normal FullReach still uses the old terrain/flow; this is not a
completed visible reconstruction or photographic wave/froth acceptance. South
Fork is the scenario; Troublemaker is a rapid in it, not a menu entry.

## Shared physical/presentation frame

Added `RaftSimWaterFlowFrame.h`, a shared unit-downstream hydraulic-XY frame.
Cartesian north is converted through the map's world-Y reflection; legacy
station/lateral sites retain +X. Breaking sites carry this direction into CPU
support, coarse/shared surface relief, refined mesh reconstruction, visible
spray-carrier sampling and the GPU crest atlas. Atlas property W, previously
zero, stores the downstream angle; zero preserves existing atlases. GPU height
derivatives AND local-envelope cap derivatives rotate back into hydraulic XY.
The two-row atlas layout and amplitude/cap authority are unchanged.

Persistent site directions interpolate along the shortest angular arc rather
than collapsing through a zero vector during a reversal. Recorded crest audits
include direction components. Site buckets use an oriented envelope's full X
extent so north/west profiles cannot disappear from the optimized evaluator.

Plunge-pool, entry-tongue, downstream-boil and roller calculations evaluate in
the site's along/across frame. Roller velocity is transformed back before foam
backtracing. Boulder-eddy foam uses the local unmodified bulk-current direction
for its frame. This does not yet rotate all boulder *height/support* wakes.

Actual Cartesian breaking detection now looks upstream along signed flow, near
and far, retaining the same wet-live-solver and Froude thresholds. It samples
existing nearest render vertices at the analysis offsets; this is not a claim
of exact arbitrary-rotation equivalence of the detector. Tailwater walks along
the same direction, rejects grid exits and skips duplicate rounded vertices.

Cartesian shore damping/detection clearance uses all grid edges and internal
dry holes. An eight-neighbor distance is a conservative lower bound on Euclidean
clearance; it never grants more distance than is physically available. Existing
minimum breaking coverage/clearance gates are unchanged. The new two-dimensional
calculation is not inferred from the minimum/maximum wet rows of one X column.

Hydraulic curvature samples the cached wet field bilinearly along the current.
The adapter's corresponding support samples also follow the current. Cartesian
fields do not inherit the unrelated station-phased standing/grade wave. Legacy
river behavior is retained. The support gate now distinguishes disabled legacy
bake-wave motion from Cartesian shared crest relief, fixing the accidental
omission of visible crest lift from Cartesian raft support.

## Built and verified

Main build session3356: terminal exit0,37 actions,268.00s. Follow-up session58899:
terminal exit0,12 actions,58.34s. Logs:
`unreal/Saved/Logs/south-fork-flow-frame-build-20260912.log` and
`south-fork-flow-frame-support-build-20260912.log`. Two pre-existing C4305
damping-literal warnings remain in the main build; not a clean release gate.

Offscreen actual D3D12 test session33111 completed exit0 at09:48:35UTC. Report
`unreal/Saved/RaftSimValidation/south-fork-flow-frame-v1-20260912/index.json`:
20 successes,0 failures,0 test errors/warnings. New evidence:

- `CurrentOrientedBreakingRelief`:51,192 translated/rotated physical/legacy,
  local/global-cap samples:height error0m,foam error0,XY error5.066357257e-13m.
  Includes west/north/south/oblique directions, conservative envelope bounds,
  stencil edges, internal dry holes, bilinear wet sampling and heading seams.
- `CartesianCrestSupportCoupling`:actual hashed Cartesian loader, coordinate
  adapter and public world-space support API receive the oriented crest even
  with bake-wave disabled;maximum difference from shared profile3.78489494324e-6m.
- Expanded `SharedFineCrestGPU`:2,106 actual GPU queries,including west/south,
  oblique and differently oriented overlapping sites. Height error8.69623104e-5cm,
  slope error0.000233079117,coarse vertex change0cm,recovered subgrid relief
  17.098492cm. Existing0.001cm height/0.001slope gates unchanged. This is a
  bounded numerical fixture, not an actual full-river visual comparison.
- Previous crop,XY handoff/carrier,source coverage,menu/migration,spray and
  shared-water regressions also pass.

Actual-game session29325 completed exit0 at09:50:43UTC under an ephemeral
profile. Report `south-fork-flow-frame-gameplay-20260912/index.json`:two clean
passes (crew6.516s,scoring/saving28.328s including setup). All UE/build jobs are
terminal. Startup SDK/Toolsets/Python diagnostics remain separate from the test
results. No visual acceptance is inferred from the game-mode NullRHI checks.

## Full-river solve and saved-state audit

Same live cook session63136/PID36216 continues; no restart/duplicate or executable
overwrite. At step2000 /100simseconds, complete native h/u/v snapshot is retained
under `tmp/south-fork-coupled-flow-600s-v2-20260912/frame_002000`.

New independent `physics/scripts/audit_cartesian_cook_snapshot.py` checks copied
vs original input manifest hash, all package grids, complete-frame marker, all
5,286,400 float64 cells, finite/nonnegative state, depth/speed limits, volume and
driver conservation ledger. Fresh audit `frame_002000_audit.json` SHA256:
`e04059dfefd00e31b039ff7ca3abc6a46bab82e6eb04ccf882d57d9a74b03092`.
PASS, explicitly NOT settled or map-integrated. At100s:maxdepth4.077397654m,
speed12.168448361m/s;volume3,024,098.947044366m3;reader/driver difference
-3.7252903e-9m3;volume gain2016.927401107m3;maxstep residual1.3275345e-8m3.
Outlet24.193707909m3/s vs inlet45.3069545472m3/s remains transient. At09:51UTC
the same process is alive atstep2220 /111s, not complete.

Installed solver archive remains e69772d2...,normal map e77da92b...,user save
181d1e57...unchanged. Free space3,557,429,248bytes at09:51UTC. No deletion/commit.

## Next delivery work / remaining limitations

Export gameplay source fields from a complete coupled snapshot and independently
verify every packet's geometry/state overlap, full route and halo coverage. A
transient frame can test export correctness, not earn steady-flow acceptance or
be mislabeled for normal-map promotion. Evaluate section discharges/settling,
not just endpoint flow. Continue the existing solve; if more spin-up is needed,
add a verified conservative restart without overwriting its inputs or executable.

Remaining Cartesian integration includes boulder height/support wake frames,
two-axis baseline/live-source authority feathering and any remaining column-only
coverage behavior. Exercise the actual detector/carrier on real accepted fields
and inspect game motion, support/render agreement and cost; static formula and
GPU tests do not prove all these interactions. Coherently integrate full terrain,
materials,global route,starts,sections and finish in normal FullReach, then assess
breaking/froth realism against retained sources. Later rivers,crew,normalization,
release/commit requirements remain open in the active goal.
