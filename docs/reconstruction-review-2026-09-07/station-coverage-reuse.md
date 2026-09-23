# Refresh-local station coverage — September23, unfinished acceptance

South Fork remains the first unfinished reconstruction. This work changes
computation of the existing coverage only, not captured terrain, collision,
hydraulic fields, shoreline thresholds, resolution, foam, crest geometry or
the disabled nonlinear solver. It does not qualify the other queued rivers.

## Reason for the change

The foot-contact counters rule out ongoing support scanning in the measured
warmed normal-start interval (see `crew-foot-fit.md`). Fresh instrumented
normal-start water-stage capture `south-fork-refresh-stages-v1-20260923` is
terminal exit0; exact cook36692 was safely suspended/resumed. Retained summaries
are `tmp/refresh-stages-v1-20260923.json` and
`tmp/refresh-crest-stages-v1-20260923.json`. In engine frames60–840,319 refreshes
average18.426729ms. Their base-vertex work averages2.652674ms and subsequent
foam/core preparation3.966554ms. These are instrumented component observations,
not ordinary frame-time acceptance; nested stages cannot be added across scopes.

Several vertex loops recomputed the same station-edge coverage, including a
corridor-end query, once per lateral vertex. The new local table evaluates the
original function once per station **after recentering on every refresh**.
There is no retained cache to go stale after a changed grid, corridor or spacing.
The existing experimental parallel-base branch remains unchanged. The retired
apron branch also remains unchanged; an initial compile failure from touching
its explicit-capture lambda is preserved in the v1 log. Corrected editor build
v1b succeeds in52.43s. No build failure or acceptance threshold was hidden.

`-RaftSimReferenceStationCoverage` selects the original computation in the same
binary. `-RaftSimStationCoverageAudit` compares every reused value against that
original computation at its actual use; it is excluded from cost runs.

## Actual runtime correctness and motion

Normal scenario start uses FullReach/full_descent, not a candidate map or review
station. Capture `south-fork-station-coverage-motion-v1-20260923` exits0 with
24 stills and a15.557s recorded clip. All4,348,737 coverage uses across137
refreshes agree exactly, including one recentered refresh. The independent
audit retains every record and reports no differences. This verifies only the
scalar coverage values, not all fields or collision/full-route behavior.

Fifteen native shoreline and interpolation suites pass (0 failures/not-run/
in-process), including moving banks, exact cache, fine crests, geometry, surface,
terrain probes and persistent proxy. Five audit-parser tests reject insufficient,
nonterminal, malformed and invalid measurements and retain mismatches. Evidence:
`tmp/station-coverage-native-v1-20260923/index.json`,
`tmp/station-coverage-equality-v1-20260923.json`.

Movie `unreal/Saved/VideoCaptures/RaftSim_20260923-155010.mp4`, SHA256
`d1be67beb369a627033adce7f2e1f68b87a872e5631a56f194f9070b6b158e7f`.
Full decode has467 frames over15.533333s,27 exact adjacent duplicates; this is
not engine FPS. The first restricted decode could not access local PyAV; its
empty output directory is retained. The completed decode uses existing local
dependencies with approved access, report `tmp/station-coverage-motion-v1b-20260923/report.json`.
Original3/9/11s frames were inspected: the raft advances from about0.13 to0.15km,
crew paddles and water changes. Coarse canopy, smooth/wide water detail and crew
silhouette limitations remain. No new visual realism, full shoreline continuity,
rapid traversal or reconstruction acceptance is claimed.

## Cost qualification

Same-binary original/reuse/reuse/original900-frame runs completed separately
without stage logging, equality audit, recording or paddle injection. All exit0,
confirm normal scenario start and default FrameTime mode, and successfully
suspend/resume exact cook36692. No competing build, native test or video decode
was active during these captures. All use4 solver lanes and the unchanged
installed solver archive. Zero-based elapsed rows60–840 retain781 samples each.

| Run (execution order) | Mean frame ms | p95 frame ms | Mean active refresh ms |
| --- | ---: | ---: | ---: |
| Original A | 31.434959 | 40.8828 | 18.604865 |
| Reuse A | 30.898149 | 40.5465 | 18.261404 |
| Reuse B | 30.379177 | 40.4197 | 18.291664 |
| Original B | 31.121000 | 40.7823 | 18.619104 |

Both reuse observations improve all three listed measurements versus both
original observations. Retain the exact refresh-local reuse on the normal path;
this is a small measured runtime improvement, not a new visual effect. ALL four
p95 measurements still FAIL33.333333ms. Short runs and their time-step-dependent
trajectories do not establish isolated/sustained/full-route FPS or acceptance.
Do not repeat this unchanged comparison or claim the river is complete.

Complete CSV hashes, metadata, metrics and phase-aligned water groups are retained
in `tmp/station-coverage-cost-v1-20260923.json`; four process receipts use prefix
`unreal/Saved/RaftSimValidation/south-fork-station-coverage-` and suffix
`-v1-20260923-process.json` for `reference-a`, `candidate-a`, `candidate-b` and
`reference-b`. Game rebuild is terminal success in101.84s, retained at
`tmp/station-coverage-game-v1-20260923.log`. Editor build, native suites, motion,
decode and all four cost jobs are terminal. Original cook36692 remains live.
The measured normal scenario is editor-hosted `-game`; rebuilding the Game
executable is not equivalent to validating a packaged release. Three existing
water-stage parser regressions also pass. The known unrelated uninitialized
`Current` compiler warning remains and is not waived.

The useful next step is reducing remaining refresh/publish cost without changing
the physical or visible outputs, alongside the outstanding captured-route and
crest/foam fidelity work. This local optimization leaves the full objective open.
