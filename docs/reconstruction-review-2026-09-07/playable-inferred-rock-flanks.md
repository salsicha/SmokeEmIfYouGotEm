# Inferred connecting flanks in normal Troublemaker — September 12

The previous goal turn delivered the row-parallel solver and verified its
normal-game cost reduction. This turn addresses actual terrain shape. Full
reconstruction, breaking-water realism, performance and later rivers remain open.

## Source distinction and implementation

The original builder connects selected exposed-rock returns directly to a
generic submerged-depth prior. Those connecting triangles are not surveyed
rock walls. The new mesh retains every captured ground/rock XYZ, every existing
small-gap interpolation, all registered XY and the complete triangle topology.
Only authority-2 (already inferred) heights within two horizontal metres of
captured rock support are eligible for a bed-obstacle harmonic extension.
Positive inverse-square edge weights on actual registered XY produce a bounded
height extension, never lower the prior bed or exceed source heights. Fixed
nodes constrain the solution; failure to converge rejects the candidate.

**Two metres is an explicit, uncalibrated geometric prior, not a surveyed
boulder outline or measured submerged slope.** New cells are authority5,
separate from captured-return authority3. Shader classification stores inferred
flanks in blue; green combines rock-like appearance support, not measurement
provenance. No aerial color is applied to the inferred submerged cells.

3,896 vertices change (mean1.671m, maximum4.089m upward), within the stated
band.174 iterations, residual8.80e-7m. The same affected10,341 faces change
from3,016 faces steeper than60 degrees/2,405.85m² to666/188.10m². This is a
geometric diagnostic, not visual acceptance. All803,842 triangles remain in
both render and complex collision;403,200 vertices. Every triangle centroid,
asymmetric barycentric point and shared edge samples to2.05e-12m maximum error.
1,295 actual hydraulic bed cells change; delta0..3.766m. No numerical bed
sampler is substituted for the registered triangles.

Source mesh:
`tmp/troublemaker-inferred-rock-flanks-20260912/registered_mesh_source.npz`,
SHA`8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b`.
Parent sparse-support meshSHA
`41f92d72102dbc4140638eb9cf97aed3b58e1ffc55bf8b6abbbcd38df7bd4089`.
FBX source:
`unreal/SourceArt/RaftSim/TroublemakerInferredRockFlanks20260912`,
SHA`71125f518b7072bac299ad2387335bfb061e2bc7e699666086af220b2145c2d5`.

## Matching flow and playable installation

Same1m271×161 grid,6000×0.1s,HLL/MUSCL,CFL.2,Manning.035 and
45.3069545472m³/s prescribed inlet. Completed cook27895 exits0;
newly verified row solver is used, not a lower-fidelity numerical model.
All13 saved frames pass sanity. Tail section error2.3104%, storage
0.12093/−0.09269/0.02409m³/s and regional-stage<1cm settling gates pass.
Actual face flux45.30695455 in,45.23697516 out,zero side leakage;
volume-derivative discrepancy2.87e-6m³/s passes the unchanged conservation gate.
Flow review/flux/export72438 is terminal/exit0. These are not observed-discharge,
measured-bathymetry or visual acceptance claims.

Installed at the existing normal **Troublemaker Rapid Challenge** entry,
`/Game/RaftSim/Maps/L_SouthFork_Troublemaker`, same ground asset path and native
game mode. The corrected source, render, collision and active `playable_flow`
agree. Original start, guide points, coordinate reflection and graphics remain
unchanged. All previous flow/map/mesh/authority texture/route bytes are retained
in `tmp/troublemaker-playable-before-inferred-flanks-20260912`.

New mapSHA`ba16f2c92e003b2f72ad1ec6e1d35ff2c0fef69ab6a2e2a9cb74e9d7cc8ed66d`.
New mesh assetSHA`6aec899c1dad1d26b8410813637f705c4fdd2552d5b4db718bb974eb6fa51a4a`.
New authority textureSHA`74276bbfb1ed3ea53055d4fea3137ea1489baaa2b6d9fb7021cd6b6b8270fdc8`.
14,257 collision probes pass, maximum0.0040061cm against unchanged0.1cm gate.
Integration88202 produces its success report and no Python/fatal errors,
but command wrapper returns1; this is retained. Independent fresh-load
audit14972 exits0, verifying the explicit parent/child backup chain, unchanged
water/ground material graphs and24 package dependencies. It is not a packaged
release.13 focused source tests currently pass (six new flank,seven sparse).

## Actual gameplay checks

First native guided traversal is TERMINAL/SUCCESS,0 errors and the existing
MotionVectorSimulation warning.63.119s,outlet110.277m,561 wet samples,
2,244 fixed water checks,no missing/grounded samples,minclearance41.121cm.
One shared carrier and normal-game progress remain correct throughout.
Maximum route error4.98056m is narrowly below the unchanged5m gate, at
station−36.90m on the approach. **This narrow pass is not robustness evidence.**
The same-settings repeat subsequently FAILS at5.001737m; see below. Report:
`unreal/Saved/RaftSimValidation/troublemaker-inferred-flanks-traversal-20260912/index.json`;
samples`unreal/Saved/Automation/SouthForkGuidedTraversal_20260912_043850.json`.
Approach000/crux004 captures inspected. No guidance points or forces changed.

Separate normal-game capture is terminal at04:41:20UTC. Frame003 at
`unreal/Saved/Screenshots/troublemaker_inferred_flanks_playable_20260912_003.png`
was inspected: the abrupt column-like sides are replaced by broader sloping
flanks. This is a visible terrain change, not a claim of source-validated
submerged slopes, photorealism or solved breaking-water motion. The crux
still needs convincing breaking and froth behavior.

Independent performance is TERMINAL at04:42:24UTC:873 frames,mean14.184ms,
p9526.427ms,meanGPU7.482ms,solver5.022ms,3480.50MiB. The scene remains at
1280x720/87% with unchanged content/graphics; cost is near the row-solver
baseline. Frame16.667ms/solver1.6ms gates STILL FAIL, memory passes; this is
not a release qualification. Report`troublemaker_inferred_flanks_perf_20260912.json`.
58 focused Python tests pass after correcting a shell-quoting error in the
test invocation; no test or acceptance threshold was weakened.

All-scenario/full-route migration remains incomplete; full goal stays active.

## Retained route failure and current-flow replanning

The first same-settings repeat is TERMINAL/FAIL, one route-gate error plus
the existing warning.63-second run reaches110.126m with no grounding or
missing water/ground queries;2,208 fixed probes,minclearance39.191cm. Maximum
route error5.001737m occurs atstation−37.034m,lateral−3.998m. It is NOT rounded
to a pass. Report`troublemaker-inferred-flanks-traversal-repeat-20260912/index.json`;
samples`SouthForkGuidedTraversal_20260912_044407.json`.

The guide still used the path calculated from the previous terrain/flow.
Rather than change its5m gate or paddle strength, the existing independent
current-aware planner was rerun on the new hash-verified fields. Same4.7×2.4m
planning envelope,0.55m minimum depth,2.2m/s paddle effort and no diagonal dry
corner cutting. It yields173 points,same−60/−9 start and112/20 end,86 changed
interior points,minimum planned footprint depth0.62393m. This uses the current
flow, not the recorded raft trajectory or a fitted relaxed acceptance corridor.
An independent bilinear footprint and attainable-effort test passes on the new
line. The recorded failure remains associated with its byte-retained route in
`tmp/troublemaker-playable-before-inferred-flanks-20260912/guided-route-before-current-flow-replan.json`.
That routeSHA is`2f25fc896776fb323abad3bcba2a3f4b42a145a227b4be7e55c8d8a5cae62e78`.
New active routeSHA`0a6ecd118d6c7aa4a3c7e26f5585a5afccc2a98d35342bfaa45d9656867f7d3f`;
source`guided-route-inferred-flanks-20260912.json`.
The replanned native traversal is TERMINAL/FAIL: maximum error6.95817m at
station13.213m,lateral−4.955m. It reaches110.019m in68.527s,2,432 fixed water
checks,zero missing/grounded samples,minclearance34.072cm. Source-flow and
footprint feasibility did not establish dynamic trackability. Report:
`troublemaker-inferred-flanks-replanned-traversal-20260912/index.json`;
samples`SouthForkGuidedTraversal_20260912_044820.json`. No gate or force changed.

The failed replan is retained as both its original planned artifact and
`tmp/troublemaker-playable-before-inferred-flanks-20260912/guided-route-failed-current-flow-replan.json`.
The previous line's points are restored, leaving the visible terrain/flow fix
installed. Its footprint minimum is freshly recomputed on current fields as
0.629153m, not the stale parent0.631028m. An independent footprint/effort test
passes on the restored line, but its retained4.98056-pass/5.001737-fail runtime
results mean guidance robustness is STILL NOT accepted. Seven new flank/route
tests and the existing52 focused checks pass (59 total).

All owned runs are terminal. The next guidance change needs finite turning
response/trackability, not another static flow-only line or a relaxed error
threshold. Visible terrain fidelity, convincing breaking/froth motion, frame
and solver budgets, full-route and later-river work remain open. No final commit
or full-goal acceptance.
