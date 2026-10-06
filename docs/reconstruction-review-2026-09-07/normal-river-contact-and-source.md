# Normal South Fork contact and rapid-source integration — September 12

## Current: steering experiments retained; actual froth sequence captured (19:31 UTC)

[Fixed-camera normal-map motion evidence](normal-river-froth-motion.md) now
includes60 actual frames and a decoded22.7s MP4. Froth/scenery remain visually
unaccepted. No material/terrain/water/crew-strength changes were made this turn.

Steering telemetry records actual yaw/rate/velocity/current alongside each
requested yaw/error/guide stroke/crew order. Build
`south-fork-guidance-telemetry-build-v1-20260912.log` succeeds20.71s.
Unchanged pivot-only run
`unreal/Saved/Automation/SouthForkNormalGuidedSegment_20260912_191402.json`:
8313.662261→8484.296368m/120.027523s, max line error28.679861m, zero grounding,
minimum tube clearance47.306067cm. Still fails endpoint and both tracking gates.
At60.02s near8448m, desired heading differs74.17degrees while yaw rate is
11.18deg/s. By64.25s the raft is7m from the line; sampled cross-current for the
needed recovery exceeds its unchanged2.2m/s effort model. The fallback points
upstream, and later speeds remain roughly0.2–0.8m/s while it drifts farther off.
This diagnoses the tested driver's off-line recovery, not a globally impossible
river line or a permission to increase paddle capability.

Planner now optionally restricts ground-track directions and cross-current
margin; original defaults remain unchanged. Seven Python tests cover defaults,
seams, missing data, footprint, endpoint and axis handling, plus rejection of
planning capability above2.2m/s. The stricter1.5m/s +65-degree direction trial
`tmp/south-fork-normal-clearance-line-turn-margin-v4-20260912.json` finds no path.
The direction-only2.2m/s trial
`tmp/south-fork-normal-clearance-line-gradual-turn-v5-20260912.json` also finds
none. Both failures are retained; neither replaces the testedv3 line.
These are restrictions of the sampled fixed-heading planner, not exhaustive
physical reachability proofs. CLI now exposes the two constraints separately.

Opt-in `-RaftSimGuidedTurnBrake` uses only the existing player Stop/brace command
while the stern guide turns, with speed/angle hysteresis; it does not modify
physics strengths. Default pivot-only driver and all original gates remain.
Build `south-fork-guidance-turn-brake-build-v1-20260912.log` passes16.72s.
Actual `SouthForkNormalGuidedSegment_20260912_192330.json`:
8313.498075→8490.701033m/120.075828s, max line error33.181071m,
axis offset18.251152m,14 grounded samples (numerical-zero post-contact tube
clearance), no missing ground, finite/progress/single-carrier pass. It still
fails rejoin/tracking and is NOT adopted as default. Its report and the prior
telemetry report each have one failed native guided test despite process exit0.
Current game DLL SHA256
`069df27a76fd16b43120d5b19ec1865e987825484c58a52f28868a277582cf1f`.

The earlier isolated natural-drift controller was inspected: it already uses
the same attainable-effort/coordinated-stroke approach, so do not assume copying
that older driver alone supplies missing full-map physical validation.
Guidance remains open; proceed with the independent local foam/shading/motion
and scenery work as well, rather than treating these failed driver experiments
as either scene acceptance or a reason to stop all South Fork work.

Offline1600s state/banks and exact next continuation pass their own checks:
[new live process71400/PID30636](full-river-expanded-checkpoint.md).
Old79428/PID37256 is terminal; old pause-template identity invalidated.
No editor/game/build is active. Save/map/source remain unchanged.

## Current guided-line and progress evidence (19:09 UTC)

Concrete progress, not acceptance. The menu clarification was already enforced;
this turn then changed progress instrumentation and exercised an independently
screened line through the actual normal map. No terrain, water, normal crew
strength, scenario catalog, saved profile or scoring coordinate changes.

`ARaftSimRunManager` now retains a transient station/actor-position/world-time
observation from the exact input used in its tick. Configure/restart/failed
sampling invalidate it. The guided diagnostic compares at that same pose with
the existing <1 m threshold, additionally requires sample age <=1 s, and retains
the asynchronous latest-physics difference separately. Build
`south-fork-progress-snapshot-build-v2-20260912.log` passes (23.91 s, no warning).
The initial v1 build passed with an uninitialized-local warning; initialization
was fixed before any gameplay run.

Same centreline driver at review station8330:
`unreal/Saved/Automation/SouthForkNormalGuidedSegment_20260912_185804.json`.
747 observations, maximum pose-aligned station error0.000487204448 m and
sample age0 s; latest-physics difference max0.591229577 m. This verifies the
current scoring projection, not the exact cause of every historical mismatch.
Actual start8332.965544, end8430.125074 m, elapsed120.148124 s;
97.159529 m travelled, route error10.132828 m, no missing ground and numerical
zero tube clearance. The run still fails traversal and5m tracking. Native report
`south-fork-progress-snapshot-gameplay-v1-20260912/index.json`: coordinate test
passes, guided test fails. Engine exit0 is not acceptance.

### Source-bound line planning

New `physics/scripts/plan_south_fork_normal_segment.py` checks the actual current
600 s atlas hashes and registered mesh SHA8bdf1a58…, uses original triangle
sampling (not raster replacement of the rocks), and never changes source state.
Six Python tests cover atlas seam interpolation, exact missing-corner rejection,
tile gaps, footprint rotation/bounds, endpoint rejoin without source mutation,
and scoring-axis segment distance. Local numeric dependencies require the host
permission path; the initial sandbox attempt could not import SciPy. No packages
were downloaded or installed.

The observed8332.699 start has centre depth2.613100 m, but the all-yaw envelope
has0 m clearance and the downstream +/-15-degree screen only0.372752 m, below
the retained0.55 m planning minimum. Earlier centreline8310 also fails that
screen (0.106951 m). A candidate seed1.000140 m to its south passes; it is explicitly
marked as a planning seed, not an observed start or a validated approach.

Retained failed/limited reports:
`tmp/south-fork-normal-clearance-line-v1-20260912.json`,
`tmp/south-fork-normal-clearance-line-downstream-v1-20260912.json`,
`tmp/south-fork-normal-clearance-line-approach8310-v1-20260912.json`.
The first successful candidate allowed any row at its final grid column;
inspection found it ended20.86 m from the scoring axis. It was NOT promoted.
The planner now requires rejoining within5 m of the intended endpoint.

Actually tested candidate:
`tmp/south-fork-normal-clearance-line-approach8310-rejoin-v3-20260912.json`,
SHA256 `504972bdb7398fb30ebc02764813faaad9ce297143c660d8037581e024f0373d`.
294 points,158.926407 m line length, endpoint global East/North[-5540,3629.5]m.
Its fixed-heading sampled envelope minimum is0.843786 m. Independent original
triangle checks at flow-compensated outgoing headings:67,914 samples, minimum
0.834989 m, zero sub0.55 m points. These checks do NOT prove intermediate turns,
continuous collision, settled hydraulics or real-river navigation safety.
The planned line itself departs13.460727 m from the provisional scoring axis.
An additional unchanged-depth screen constrained to within5 m of that axis
finds no connected route (`south-fork-normal-clearance-line-axis-constrained-v1-20260912.json`).
This is evidence under the screen's fixed-heading assumptions, not proof that
every physically possible yawed trajectory is impossible.

### Actual normal-input candidate run — improves passage, still fails

The diagnostic accepts an explicit `-RaftSimGuidedLine=...` file, follows its
polyline using the existing12 m lookahead and normal crew/guide inputs, records
line error separately, and requires both120 m progress and endpoint rejoin.
No mid-run teleports/manual physics steps/forces or water overrides. The original
5 m scoring-axis gate is still present alongside the5 m planned-line gate.
Build `south-fork-planned-guidance-build-v1-20260912.log` passes,21.01 s.
Source-locked launch verifies map, rapid asset, line, atlas and progress-map
hashes, review station8310, ephemeral profile. The normal checkpoint places
the raft on its unchanged scoring axis, not at the offset planning seed.

`unreal/Saved/Automation/SouthForkNormalGuidedSegment_20260912_190554.json`:
start8313.286121, end8483.556725 m,120.058284 s, **170.270604 m travelled**.
Zero grounded samples; minimum actual six-tube clearance44.299271 cm;
no missing ground, finite state, exactly one Cartesian carrier and aligned
progress throughout. It passes the rocks but misses the intended rejoin and
overshoots downstream. Max planned-line error27.748054 m, max scoring-axis
offset19.387603 m. First planned-line error>5 m occurs at16.411337 s, station
8346.208604—not solely after the endpoint. At55.5 s it is still moving3.03 m/s
and only2.37 m from the line; by63.5 s it misses the rejoin and error is6.87 m.
Do not count travelled distance as an endpoint or tracking pass.

`unreal/Saved/RaftSimValidation/south-fork-planned-guidance-v1-20260912/index.json`:
**34 pass,1 fails**, zero unrun/warning tests. Failures: endpoint/timing condition,
original axis tracking, and explicit line tracking. Initial and final actual
screenshots (`SouthForkNormalGuidedSegment_20260912_190554_000/004.png`) inspected;
visible froth/scenery remains unaccepted. User save SHA181d1e57… unchanged.
Current game DLL SHA256
`1ce6acf31bc764f765ab97ab04f209edc7bbfb4a39ed8c3314be3af189be709a`.

NEXT: record yaw/angular rate/desired steering together with trajectory; address
line-following and downstream rejoin without increasing crew strength or
loosening gates. Keep guidance geometry distinct from scoring chainage and
retain the centreline baseline. Then actual froth motion, scenery and current
map performance; the entire other-river/crew/release queue remains open.
No editor/game/build remains live. Same cook79428/PID37256 verified live at
1574 s/local5480; next complete1600s/local6000, no restart or runtime promotion.

## Current post-alignment result (18:43 UTC)

The normal-game D3D12 capture `south-fork-normal-aligned-source-v1-20260912.png`
was inspected; the log confirms the new `SM_TroublemakerCapturedGround` loads.
At ~10 s the raft moves 2.854 m/s in sampled water moving 1.123 m/s, with zero
dry/grounded supports. Actual submitted crest v9 checks 712,296 samples:
maximum target error 1.428008269 cm (unchanged 2 cm gate), original vertices
unchanged. Other relief, froth motion and sustained performance remain outside
that narrow geometry check. The screenshot still has sparse scenery and
unaccepted froth appearance; it is not final visual acceptance.

Same guided driver after mesh alignment:
`unreal/Saved/Automation/SouthForkNormalGuidedSegment_20260912_183925.json`.
Station8332.699174 to8430.097039 m in120.057830 s; 97.397864 m, **fails**120m.
Minimum sampled clearance numerical zero, no missing ground queries, finite
state and one Cartesian carrier throughout. Ground contact/source consistency
improves, but route error10.096486 m exceeds5m. The progress-snapshot comparison
also fails; this compares actor-tick progress against the physics snapshot and
needs pose/time-aligned evidence before diagnosing a coordinate/scoring bug.
Native test report `south-fork-normal-guided-segment-aligned-source-v3-20260912/index.json`
has one failed test, despite the engine process exiting0. Do not infer success
from process exit status. No thresholds were relaxed and the correct mesh was
not rolled back to improve the diagnostic score.

NEXT: use the current hydraulic/collision geometry to assess a footprint-safe
guided line, distinct from the provisional centerline used for scoring chainage;
retain the baseline, measured-source/inferred-bed distinctions and ordinary
crew/guide effort. Add pose/time information to resolve progress snapshots.
Then rerun guided motion, froth/reference and current-map full-frame performance.
The earlier21.4291FPS capture predates the contact and mesh fixes.

Current physics DLL SHA256:
`51750d6387a72691acae23adbfa54233af35f79af615c9aff6ad0166065ab8b5`.
Actual crest v9 artifact SHA256:
`1540904a804cd194ecef3706e81490c9c716cdb908c06cebe3d8d5e8502e794a`.
Final scoped diff check passes;16 Python tests pass across assembly and timing
parsers. No build/editor/capture is left running. Separate cook1500s passes
state/dry banks, remains unsettled, and continues to1600s without promotion.

## Two concrete integration defects

1. `RaftSimPhysicsBridgeSubsystem.cpp` captured a fixed list of collision meshes
   while the raft was at the put-in. Later world-partition rapid terrain was
   missing from contact queries, allowing fallback to the coarse hydraulic bed.
   `FRaftSimGroundSourceRegistry` now invalidates membership on level addition,
   level removal and actor spawn. It retains weak references and the existing
   physical-ground opt-in; unchanged substeps do not scan the actor list again.
   Teardown releases the world delegates. No contact radius, solver bed, force,
   collision threshold or captured terrain was altered to mask the defect.

2. The assembled full-river rapid actor referenced the older registered mesh
   (geometry `4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`),
   although the composite hydraulic geometry already used the recovered-return/
   inferred-flank revision
   `8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b`.
   This left 4,316 changed vertex heights absent from the visible normal river;
   differences range from 0 to 4.592486382 m. Boundary heights are identical.
   These revisions preserve captured anchors and distinguish inferred connecting
   faces/submerged bed from measured returns; the new faces are not survey data.

## Contact fix verification

Final build `south-fork-streamed-ground-build-v2-20260912.log` exits 0 (24.98 s).
`south-fork-streamed-ground-regressions-v2-20260912/index.json`: 34 successes,
zero warnings/failures/unrun. The registry fixture checks post-binding actor
spawn, component-tagged membership on the level-change callback, foreign-world
isolation, retired membership and no repeated scan across unchanged substeps.
The first fixture crashed by broadcasting a synthetic null-world event into
unrelated editor delegates. It was corrected to exercise its own bound callback;
the failed run is retained and is not included in the passing count.

`RaftSim.Survey.NormalSouthForkGuidedSegment` uses the normal full map with an
ephemeral profile and diagnostic station 8330. Its 120 m/120 s centerline driver
uses only ordinary crew/guide inputs. No teleports/manual stepping/velocity or
water overrides are performed by the driver. Normal checkpoint placement occurs
before observation. This is not a complete river traversal or surveyed safe line.

Before the cache fix, `SouthForkNormalGuidedSegment_20260912_181808.json`:
start 8332.624086, end 8431.889903 m in 120.152449 s; stopped before 120 m.
Minimum sampled tube clearance -52.226196 cm, 492 grounded samples, no missing
ground queries. One Cartesian carrier remained visible and state stayed finite.
Route error 9.110617 m and a progress-snapshot mismatch also failed. The mismatch
was not independently diagnosed as a scoring defect.

After the cache fix, before mesh alignment, the second report reaches
8332.661461 to 8452.670826 m in 90.680420 s. Minimum tube clearance is numerical
zero (-1.14e-13 cm), no missing ground queries, 57 grounded samples. State,
single visible carrier and progress snapshot checks pass. Maximum route error
13.495584 m still fails the unchanged 5 m guidance tolerance. **The segment test
still fails overall.** Do not substitute its successful contact check for full
traversal/visual/60 FPS acceptance. Gameplay after mesh alignment remains next.

## Full-river mesh alignment saved and reloaded

Guarded operation: `unreal/Scripts/align_south_fork_rapid_source.py`.
Report: `unreal/Saved/RaftSimValidation/south-fork-rapid-source-alignment-v1-20260912.json`.
The one existing actor now uses
`/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround`.
It retains its transform, physical-ground tag and material override. Its 803,842
triangles match the source revision used by the hydraulic composite. 14,257
changed-triangle/anchor probes at full-river placement pass unchanged 0.1 cm
threshold (max 0.004006068 cm). Source-only collision checks, not combined
gameplay acceptance. The reference and transform survive a disk reload.

All other 454 actor packages, both source assets and user profile are unchanged.
The map and affected actor package are recoverable from
`unreal/Saved/RaftSimValidation/south-fork-rapid-before-source-alignment-v1-20260912.zip`
(SHA256 `17da4d43a8b926ad76e42ec7e4e29c5669d896bb198cb6023e29cffafe81bab1`).
No source assets were deleted, reimported or deformed.

Current map SHA256:
`3d52dd5bdfdf4fb9a3e0c57fa728e437cef16ccc0bf827892458e55ee8eade77`.
Affected external actor package:
`/Game/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach/3/LY/MFF59H58N6AWIGUAUQOON1`,
SHA256 `315f035f39e1293a1648ff82c925bb51bfce4c1bf837e03ce8bdc3839d4538b4`.
New mesh asset SHA256:
`6aec899c1dad1d26b8410813637f705c4fdd2552d5b4db718bb974eb6fa51a4a`.

The assembly preparer now selects that asset and explicitly compares render,
collision and hydraulic geometry revision IDs. Three independent unit tests
exercise this comparison directly, rejecting a mutually consistent but stale
render/collision pair and stale collision evidence for a new render mesh.
Eight assembly tests pass in total; the five historical preflight-rejection
tests do not independently prove every later gate because their map is stale.

South Fork is still the scenario. Troublemaker remains an in-river rapid, never
a menu option. Flow promotion, performance, scenery, guided route behavior,
convincing froth motion, other rivers, crew and release work remain open.
