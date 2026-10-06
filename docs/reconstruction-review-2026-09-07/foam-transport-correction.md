# Bounded presentation-foam transport — September 18

This is a review of transport accuracy, not completed South Fork reconstruction,
physical breaking, visual realism, traversal, 30 FPS or release acceptance.
South Fork is the scenario; Troublemaker remains a rapid within it.

## Implementation and limits

The existing CPU foam transport repeatedly bilinearly samples its previous
field. A new `-RaftSimFoamBFECCReview` option corrects that interpolation error
on the same carrier, using the same original backward coordinates and effective
roller/eddy velocity. It does not add noise, foam sources, a new water surface,
geometry, bathymetry, or a replacement momentum solver. Default remains OFF
pending actual visual and performance qualification.

The method follows the forward/reverse/source-correction/forward construction
in [Selle et al.](https://physbam.stanford.edu/papers/stanford2006-09.pdf).
Bounds come only from nonzero-weight original donors. Incomplete round trips,
dry history, paths whose node rectangle touches dry rock, and invalid or folded
inverse maps retain the original first-order result. Initialization, unchanged
water clocks and grid recentring also retain the original path. The original
generation, release, tongue and shore formulas apply once after transport.

The reverse trace solves the inverse of the **same discrete departure map**.
Simply reversing a varying velocity was wrong: the first implementation passed
the synthetic translation tests but failed the existing actual carrier ramp
regression (1.34049044015e-6 error against the unchanged 1e-6 limit). The inverse
map correction reduces that error to 4.22851019755e-8. The failed v1 report is
retained; neither its test tolerance nor the original expected ramp was changed.

This is bounded presentation concentration transport, not conservative air
volume. Frozen effective velocity still includes inferred surface-return flow;
the Euler forward characteristic and current source calibration are unchanged.
No temporal-order, mass-conservation or full dispersive-physics claim follows.
The older `RaftSimFoamEvolutionAudit` still compares the first-order
serial/parallel stage before this correction; it does not validate BFECC.

## Native verification

Editor builds v1/v2/v3 pass (251.92 / 58.68 / 59.52 s). The v1 build retains
existing C4701 detail-footprint and C4305 Chaos warnings; it is not warning-clean.
Final v3 native run: five successes, zero warnings/failures/unrun tests,
0.3910585 s. Tests include bounded transport, committed-clock evolution,
directional source, actual Cartesian boulder/carrier integration and grid history.

At 40 unchanged transport steps, three independently translated Gaussian
profiles in different directions have summed absolute errors:

| Direction (cells/step) | First order | Corrected |
| --- | ---: | ---: |
| (0.37, 0.23) | 24.2748123 | 2.42366159 |
| (-0.31, 0.19) | 22.4314690 | 2.54656508 |
| (0.17, -0.29) | 19.5232658 | 2.48112758 |

Every corrected value is checked against its original contributing donor bounds.
Additional checks cover a stationary field including border nodes, varying-flow
affine profiles, dry history, long traces across a dry wall, exterior history,
zero-weight donors, held/invalid time and orientation-reversing maps. These are
scoped operator checks, not proof that broad foam faces now look realistic.

## Reference access

Both original videos were accessible through ordinary browser playback again:
[Qweniden, bank view](https://www.youtube.com/watch?v=2XTbOCNDcZQ) at 0:55 and
[John Elkins, raft view](https://www.youtube.com/watch?v=ZEG1kvjNI30) at 0:35/0:40.
The bank tab was small; the raft frame was inspected after scrolling the player
fully into view. Dark water separates irregular white crests in the approach;
passengers obscure much of the close drop. These are qualitative observations,
not calibrated bed dimensions or flow/foam velocity measurements. No login,
downloaded reference media, security bypass or source-asset change was used.

## Hydraulic continuation

The existing PID13584/startUTC2026-09-18T12:17:39.4321093Z continuation remains
the same job. The completed 9050 and 9100 snapshots pass both all-cell and
artificial-bank audits: 5,382,400 cells and all 86,720 bank cells exactly dry.
At 9100 the max depth is 3.778027745 m, max speed 5.353059281 m/s, maximum step
conservation residual 1.3401946219460115e-8 m3. Outflow 102.1245371 m3/s versus
inflow 45.30695455 m3/s still does NOT establish settling. Installed 4950 water
is unchanged. Next checkpoint is 9150 / local3000, requiring its completion
marker and both audits.

9150/local3000 subsequently passes both audits too. Max depth 3.778598463 m,
speed 5.353093855 m/s, outflow 102.2528620 m3/s: still NOT settled. Next checkpoint
is 9200/local4000. Standalone Win64 Development build passes in 158.53 s; this
is not a cooked-package or release pass.

## Actual engine motion

Same editor binary, four solver lanes, ordinary lit FullReach at diagnostic
station8330, no authored-camera substitution. Both processes exit zero with
24 screenshots and no timeout; cook suspend/resume succeed. Baseline's recorded
cook CPU difference is 0.125 s during the suspend transition, corrected is 0 s;
do not describe both as exactly zero. No build or decoder overlaps these clips.
All four motion/timing runs also retain engine experimental-toolset Python
startup errors for missing `unreal.AgentSkill` and `unreal.PythonTestRunner`.
The same errors are present in the preceding wet-edge default capture, so they
are not introduced by this change. Zero game exit codes are not clean-log or
release acceptance; these startup errors remain an outstanding integration issue.

| Clip | Actual source frames | Duration | Fully decoded frames |
| --- | ---: | ---: | ---: |
| Baseline | 229 | 15.853 s | 476 |
| Correction | 194 | 15.991 s | 480 |

The encoder's 30 Hz output is NOT 30 FPS gameplay. Unmodified 3/9/13 s frames
from each clip were inspected. Both still show broad smooth foam sheets, steep
smooth water faces, block-like inferred rock flanks and angular repetitive
canopy. Camera/raft paths diverge, so matching movie timestamps are not matched
world-space samples. Fixed decoder image ROIs are not reliable semantic water
measurements as the camera moves. These frames do **not** establish convincing
froth or a significant visual improvement. The option remains OFF by default.

The candidate's verbose live log records 120 corrections over committed water
times 0.13333334–13.0000007 s: 836,976 corrected sample evaluations, 85,054
limited evaluations, sum of absolute final-density changes 64.007089693, largest
per-refresh summed change 0.649354313. Mean absolute change per corrected sample
is about 7.65e-5. Counts include evaluations whose output equals the baseline;
they are not unique vertices or air-volume measurements. This confirms actual
execution but cannot support a claim that interpolation blur explains the broad
white faces. Log SHA256:
`dccf0e939c432b9b423dc57fd7d011dbd536b4da1499d0c5c23bf98fe1f5c9c3`.

[Retained evidence](foam-transport-correction/) includes both original engine
movies, selected decoded frames, native reports including the initial failure,
capture process records, decoder reports and hydraulic audits. No reference
video was downloaded or added to the repository.

## Timing and decision

Separate 900-frame captures use the same binary, four lanes, 1280x720 D3D12,
all rows60–840 and verified default elapsed-frame mode with scope offset1.
No verbose logging, screenshots, builds, decoder or heavy audit overlaps them.
Both games exit zero, no timeout; cook suspend/resume succeed. Baseline records
0.015625 s CPU increase across the suspension transition, corrected zero.

| Mode | FPS | Mean frame ms | p95 frame ms | Foam mean active-refresh ms |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 24.937420 | 40.100380 | 49.3295 | 0.930997 |
| Correction | 23.798155 | 42.020064 | 52.9027 | 4.894937 |

Both FAIL30/p95<=33.333333 ms. This is one ordered comparison, not an ABBA
performance qualification or isolated causal estimate; differing trajectories
and shared-machine variation remain. Correction cost is included in the foam
scope, not hidden outside it. The worse timings and missing visual benefit do
not justify a reverse-pair promotion experiment. **No default promotion.**
The bounded operator and explicit review flag remain reproducible for further
model work; no numerical gate is relaxed and no default source/material changes.

FullReach map SHA256 remains
`c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`.
The full ordered remaining-work scope stays open and nonlinear runtime remains
OFF. Next prioritize coupled breaking geometry/entrainment and source-supported
rapid shape, not further scalar-transport polishing: this test does not explain
away the visibly unconvincing broad faces. Colorado -> Pacuare -> Futaleufu,
Chilko/Zambezi reviews, crew fit/animation, normalization, original storage/face
regression and remaining release checks are not closed by these results.
