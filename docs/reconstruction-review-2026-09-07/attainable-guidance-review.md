# Current-aware guided traversal: bounded steering correction

South Fork remains incomplete. This change concerns the automated guide in the
isolated captured review, not a new water solver, measured navigation line or
production steering assistance. Colorado, Pacuare and Futaleufu remain queued.

## Reproduced cause and experiment

The depth-limited candidate's baseline reaches the outlet but deviates 12.329 m
at station 58.99 m / lateral 14.26 m, around 67.18 seconds. Its control log shows
the desired heading reversing from -151 to +104 degrees between 40.28 and
42.95 seconds. The raft cannot make that turn immediately. During large errors
the test also suppresses the guide's stern sweep while the crew pivots, leaving
only slow crew turning as the current transports the raft laterally.

Allowing the existing catch-timed guide stroke during crew turns alone is not
enough: maximum error is still 10.216 m. Preserve that failed experiment.

A second opt-in computes the paddling velocity required for a ground track
toward the existing lookahead point. Given unit track direction `d`, current
`u` and the existing 2.2 m/s paddle-speed limit `p`, remove the cross-track
current `c = u - d * dot(u,d)`. The requested relative-water velocity is
`d * sqrt(p*p - dot(c,c)) - c`. This has magnitude `p` and its resulting ground
velocity is parallel to the target track. Impossible cross-current/upstream
progress is explicitly flagged rather than exceeding the effort limit.

This replaces only the experimental guide's heading demand. It does not inject
velocity, increase stroke strength, teleport, change collision, alter route
points or relax the 5 m / 120 s / 1 mm sampled-penetration criteria. Actual
acceleration and yaw still come from normal crew and guide paddle actions.

## Actual-engine results

| Same package and route | Outlet | Max route error | Minimum sampled tube clearance | Verdict |
| --- | --- | --- | --- | --- |
| Prior baseline | 98.891 s | 12.329 m | 36.456 cm | Fail |
| Guide sweep during crew pivot | 86.542 s | 10.216 m | 38.598 cm | Fail |
| Attainable track + coordinated strokes | 66.980 s | 3.869 m | 36.752 cm | Bounded pass |
| Fresh map in combined four-test suite | 67.145 s | 4.712 m | 36.046 cm | Bounded pass |

The passing traversal reports zero missing ground queries, grounded samples or
unattainable-track control samples. The one-carrier/shared-relief and lit-foam
material checks pass. Raw report:
`unreal/Saved/Automation/SouthForkGuidedTraversal_20260907_153340.json`.
The mathematical engine regression verifies cross-current cancellation,
rotation invariance, bounded impossible-current responses and a zero target.
Both engine tests succeed; traversal retains an engine warning about
`r.MotionVectorSimulation` render-thread access. It is not suppressed.

The final combined suite passes all four: attainable-guidance mathematics,
candidate-specific water replay, captured-ground contact and fresh-map guided
traversal. Its raw report is
`unreal/Saved/Automation/SouthForkGuidedTraversal_20260907_153742.json`, with
616 wet samples, zero missing/grounded samples and zero unattainable targets.
The small start difference (-55.012 versus -55.367 m) and variation in maximum
error are retained. Two bounded passes with only 0.288 m margin on the second
are not broad robustness across releases, starts or control disturbances.
Final engine evidence is `engine-attainable-steering-combined/index.json`.

Use both additional flags to reproduce the new controller:

```
-RaftSimSurveyCoordinatedSteeringReview
-RaftSimSurveyAttainableTrackReview
```

Also retain the existing breaking/lit-foam flags and quote the entire native
`-RaftSimSurveyGuidedRoute=docs/reconstruction-review-2026-09-07/guided-route-depth-limited.json`
argument in PowerShell. Baseline behavior remains available without the new
flags. Reports are separate under `engine-coordinated-steering` and
`engine-attainable-steering`; failures remain in `guided-review.json`.

## Unchanged identity and limitations

- Map SHA: `2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd`.
- Engine native archive SHA: `83f35ddf4e6ab28fc07999804e63d3ccfcd5d0d78d8f0775c96e909913910f03`.
- Field manifest SHA: `0cbd69e885c9a40050e17b0df7a1d1884d91c30070fb55fbd5fdda5fca4bcee4`.

Build succeeds. Twelve Python route/ledger tests and nine subtests pass,
recorded in `guidance-regressions.xml`. Actual boat-height image
`SouthForkGuidedTraversal_20260907_153340_001.png` was examined: plain captured
terrain and mostly smooth reflective water still fail photographic acceptance.
No visual improvement or new performance result follows from a steering fix.
Six sampled tube probes are not continuous swept-hull proof; one route and
one discharge are not robust full-rapid acceptance. Fine-grid convergence,
crest/foam animation, performance, source registration and coordinated full
route migration remain open. No production assets are promoted or committed.
All owned build and engine processes have exited. The evidence ledger retains
all 16 runs, including the coordinated-only failure, without converting earlier
field versions into acceptance of the current candidate.
