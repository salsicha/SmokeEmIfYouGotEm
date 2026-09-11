# Registered-rock gameplay traversal — bounded pass, not scene acceptance

## Driver correction

Inspection of `SouthForkGuidedTraversal_20260908_055031` shows the older
automated driver requesting heading reversals exceeding 100 degrees while
withholding the guide's stern stroke during crew turns. Maximum departure
occurs around station 59.36 m, lateral 11.80 m, at 60.52 seconds. That is a
driver limitation, not evidence that the byte-equivalent native optimization
changed the water field.

The test driver now defaults to the already implemented attainable-current
heading calculation and coordinated crew/guide strokes. These use existing
catch-timed gameplay APIs; no direct velocity, pose, yaw, force-strength or
water modifications. **Player controls were not changed.**

`-RaftSimSurveyLegacyGuidanceReview` restores the older driver for explicit
comparison. The older coordination/attainable flags can still enable either
component individually alongside that flag. Four mode-selection checks were
added to `RaftSim.Survey.AttainableGuidance`; its existing effort-bound,
rotation, and unattainable-current checks remain.

Build 19250 exited 0. Test 12603 exited 0, both tests successful; the map run
retains engine warnings. `engine-guided-coordinated-default/index.json` and
raw `SouthForkGuidedTraversal_20260908_060345` record a **single bounded pass**
on the older `SouthForkSurveyPlayable`: outlet 62.752 s, maximum route error
3.921 m, minimum sampled tube clearance 30.641 cm, no missing ground queries.
Earlier failures are retained. This does not establish repeated robustness.

## First registered-rock full diagnostic traversal

Generated `guided-route-registered-rock.json` with the existing planner using
the current registered-rock fields, verified against their manifest hashes.
It has 173 points from (-60,-9) to (112,20) m. The downstream-aligned planning
envelope is 4.7×2.4 m, minimum required depth 0.55 m, planned minimum 0.631 m.
It uses attainable-current travel time with the existing 2.2 m/s paddle-speed
limit. It is **not a measured real-river navigation line**; bed inference and
registration provenance remain explicit, with no data promotion.

New `RaftSim.Survey.SouthForkRegisteredRockGuidedTraversal` reloads the actual
`SouthForkRegisteredRockPlayable` map, checks the exact registered terrain
asset, and retains the existing geometry/depth-hash and field provenance
checks. The report now records map name, terrain asset and registered-map
identity. Original-map tests remain available. Missing terrain meshes fail
explicitly rather than being dereferenced.

The build succeeded. Run 95762 exited 0, report
`engine-registered-rock-guided/index.json`: **one success with one warning**.
All current breaking/lit foam/GPU detail/fine crest/second-order/ballistic
spray/unified optics/activity-memory flags were enabled, plus station captures.

| Unchanged criterion | Measured registered run |
| --- | ---: |
| Reach outlet within 120 s | 64.429 s |
| Route error ≤5 m | 3.802 m maximum |
| Sampled tube clearance ≥−0.1 cm | 33.816 cm minimum |
| Missing terrain queries | 0 |
| Finite state | Pass |
| One visible carrier/shared relief checks | Pass |
| Local hydraulic breaking sites | 8 maximum |
| Reviewed lit-foam parameters | Pass |

Raw report `registered-traversal/registered-run.json` is copied unmodified
from `SouthForkGuidedTraversal_20260908_061133`. It identifies
`UEDPIE_0_SouthForkRegisteredRockPlayable` and the exact
`SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate` asset.
The map hash remains
`81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.
The native archive is unchanged from the prior integrated primitive reuse:
`fd988c73f10f2f1423b421fc3b6e78928d9124acba789e9fae05b75f1a51a35c`.

The warning concerns `r.MotionVectorSimulation` being read on the render
thread without the render-thread-safe console-variable flag. No reference
to that variable was found in the project's C++ code. Inspection of installed
UE 5.8 source locates its registration at
`Engine/Source/Runtime/Engine/Private/Rendering/MotionVectorSimulation.cpp:9`
(an ordinary `FAutoConsoleVariableRef`) and the renderer read at
`Engine/Source/Runtime/Renderer/Private/PostProcess/TemporalSuperResolution.cpp:1884`
(`GetInt()` while configuring TSR). That identifies the warning's engine
source, **not** a measured cause of visible water instability. The engine is
not edited, the warning is not suppressed, and this is not a clean run.

## Images and remaining work

Thirteen station-labelled images were captured. Although 1280×720 was requested,
the actual PIE images are **954×468**; this is not a performance qualification.
Unmodified approach/crux/runout frames at approximately stations −14.88,
0.02 and 15.05 m are preserved in `registered-traversal/` and were inspected.
They still show broad smooth white sheets, angular exposed rock/terrain, and
insufficiently broken water. **No photorealism or real-rapid identity acceptance.**

The ledger now retains **26 runs**, including all earlier failures and both
new bounded passes, with each engine test path explicit. Six tube probes at
sample times are not a continuous swept-hull collision proof. One route and
one flow condition do not prove all headings, flows, starts or rivers. There
is no fresh performance claim, no shader/VFX change, no geography promotion,
and no final commit. Finish realistic surface/foam/spray, performance,
geographic verification and the full ordered queue.
