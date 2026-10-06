# Registered-scene spray attachment

September 7, 2026 local time. South Fork candidate only; not photographic,
geographic, collision or release acceptance. The preceding transport review
showed little visible change in the smooth foam face. This pass found and fixed
two integration mismatches instead of increasing forcing or particle counts.

## Implementation and retained failed integration

The existing `-RaftSimSouthForkBallisticSpray` option selected falling roller and
droplet profiles only on `L_SouthForkAmerican_FullReach`. Consequently it could
not affect `SouthForkRegisteredRockPlayable`. The same obsolete map restriction
also guarded source anchoring. Both now use one explicit map-eligibility helper,
covering these two names (including numeric PIE prefixes/package paths) and
rejecting unrelated, old-suffix or similarly named maps. The option is still
opt-in. Existing Chilko assets and all particle budgets remain unchanged.

Build15253 exited0 (14 actions,36.81s). Four focused engine tests passed in
`engine-registered-spray/index.json`, process96316 exit0. Initial capture53049
exit0 selected the intended assets, but all six sources were rejected. Retained
log `RegisteredSprayMotion.log` and video
`unreal/Saved/VideoCaptures/RaftSim_20260907-191730.mp4`: 696source frames,23.836s.
This is the FAILED intermediate integration, not the corrected final result.

`SampleVisibleCarrierAtRiverCoordinates` required a visible legacy volume-core
mesh and its cached vertices. The registered scene instead renders the main GPU
carrier, with that legacy mesh intentionally hidden. The query now recognizes
the visible GPU carrier only when its atlas and section exist, samples its
actual coarse vertex source in world coordinates, and substitutes the same
continuous shared crest for the coarse crest component exactly once. The
substitution reconstructs physical sites from the current atlas metadata and
uses the original CPU support evaluator with the same shore weight and scale.

Existing wet/depth and measured buried-bank checks remain. The source centre and
four footprint extents must still pass. No terrain probes or GPU readback were
added. This is a bounded presentation anchor, NOT exact particle collision:
GPU perturbation height and fine-triangle interpolation error are not captured
by this CPU query, and testing five points does not prove every particle stays
over water. The approximation remains explicit rather than silently claiming
all material displacement is covered.

## Verification

Build84439 exited0 (4 actions,26.60s). Corrected capture38552 exited0:
`RegisteredSprayCarrierMotion.log` and
`unreal/Saved/VideoCaptures/RaftSim_20260907-192406.mp4`.
At10s, six published/ranked sites, budget6, three emitting. Wet sources at
station/lateral (7.5,-3), (7.5,3), (13.5,-7.5) have sampled carrier heights
6.804m,7.540m,6.475m. The remaining three fail wet source-footprint checks.
No inference that all six were supposed to emit, and no relaxed shore gate.

New `RaftSim.M4.VisibleSprayCarrier` fixture verifies both triangle halves,
nonidentity world transform, single crest substitution, interpolated shore
weight, hidden legacy mesh, dry contributing corner, harmless zero-weight dry
corner, buried measured bank, outside domain, hidden carrier and missing atlas.
This is a CPU anchor fixture, not a GPU particle test. Final build73912 exited0
(21 actions,82.52s). Process13789 exit0; final report
`engine-registered-spray-carrier/index.json`: **5 clean successes,0 failures**.
Other tests: map eligibility, horizontal source plane, hydraulic classifier,
existing falling-profile asset parameters. The attempted `WaterDetail.Crest`
filter matched no test (actual name is `WaterDetail.SharedFineCrestGPU`); do not
claim a fresh GPU crest test here. That shader was unchanged.

The complete corrected clip was decoded by the existing local analysis helper:
696captured source frames over23.843s,715encoded frames, monotonic timestamps.
Unmodified1/8/16/23s PNGs and numerical per-frame data are under `detail-motion/`,
label `RegisteredSprayCarrierMotion`. The8s frame and prior second-order8s frame
were inspected side by side. The broad white face remains too smooth; spray
still reads as detached puffs. No photographic improvement is accepted from
this comparison. Encoded30Hz and duplicate counts are not measured game FPS;
numerical full-stream decoding is not a claim of visually watching every frame.

Engine game-mode recordings include the existing experimental EditorToolset
Python startup errors (`unreal.AgentSkill` and `PythonTestRunner` absent).
They nevertheless finalized with exit0. These external plugin errors were not
fixed or counted as a clean project-wide release run.

## Performance and next work

Isolated process28338 exit0, same1280x720/87%,RTX3060Laptop, Development offscreen,
5s warmup/20s measurement; no concurrent build, recorder or decoder:
`survey_performance_registered_spray_carrier.json`.

- Mean14.021158ms; p9519.111999ms; GPUmean6.880067ms.
- Solvermean8.919443ms; one33.896999mswall-clock hitch.
- Final detail backlog0.003400s.

Prior second-order p9519.499399ms. This single run does not establish a robust
speedup; frame16.667ms and solver1.6ms gates still FAIL. No packaged qualification.

Registered map, crest material and native solver archive hashes remain unchanged
(81f31bec...df705ad7,52194d11...858438f,d91b779b...a64155). No survey data, material,
particle asset, physical forcing amplitude, production scene or later river was
changed/promoted. All owned processes in this pass are terminal.

Next: measure resolved GPU height/slope specifically under the smooth foam face
and compare its variation with source/coverage, then change the deficient surface
behavior. Do not repeat the obsolete-map diagnosis or unchanged transport tuning.
Exact spray landing/perturbation coupling, actual rapid identity/rock silhouettes,
shared raft support, robust traversal, CPU cost and the full remaining queue stay
open. No commit/push; full goal active.
