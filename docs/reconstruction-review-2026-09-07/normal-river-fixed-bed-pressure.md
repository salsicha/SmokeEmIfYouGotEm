# Fixed-bed pressure geometry — September 12

This turn reproduced an exact velocity-spike update, identified a fictitious
moving-bed term, implemented fixed geometric slopes in CPU/GPU components and
verified the correction against that update. It does not finish playable
water, physical breaking/froth, reference comparison or 30 FPS acceptance.
The complete remaining-scene/terrain/crew/release/commit goal stays active.

## The previous long replay is terminal, not live

Kinematic v2 session 28187 / PID 36084 ended **failed** at 4.189974479 s:
555 accepted steps, 82 rejected trials, minimum-step exhaustion. Fastest cell
(y127,x6), h = 2.722174308e-19 m, speed = 21,746,216,187 m/s; maximum depth
4.524499 m. Report and state remain:
`tmp/south-fork-kinematic-pressure-bank-twenty-second-v2-20260912.json` and
its `.last-admissible-state.npy` (SHA-256
`ae0d8c48398297966e05f713db9b301950dcb82931efb97c6efd35426d7e35e9`).
The report's successful shell exit does not mean the replay passed.

## Exact accepted update reproduced

Added an optional copy-isolated per-step observer and
`probe_nonlinear_velocity_spike.py`. Its speed threshold only stops the
diagnostic and preserves before/after states. It never caps velocity, repairs
mass/momentum or labels an event as completed simulation. The observer cannot
modify the evolving arrays, as a dedicated regression verifies.

Starting from the saved 3.501517376 s checkpoint, the first >30 m/s event occurs
52 accepted steps / 0.433333333 s later, without retries. It reproduces the
recorded 505.375156655 m/s transient exactly. The same single step was then
replayed from its preserved preceding state, with zero difference between the
reconstructed SSP-RK2 update and the observed accepted state.

Detailed one-step evidence:
`tmp/south-fork-kinematic-spike-probe-v2-20260912.json`.
The preceding-state hash is
`2865d8ca03ef364bfa071a831bff70bf9e0b576842bb8990aaf06d5c3546ff9d`.
The event-state hash is
`b9931b8e2fc109e9e8465ac072e6e46f2cb033970995063cf3e25af19d12727c`.
The hot cell is (y119,x43), bed 8.528518677 m. Before the step, its depth is
7.759073767e-15 m and velocity (-1.67208,-0.102991) m/s. The intermediate RK
state still has bounded velocity. Its hydrostatic y-momentum derivative is
-4.652344832e-16, but the pressure contribution jumps to -9.439421980e-10.
That pressure impulse creates the accepted y-velocity -505.372379 m/s.

## Cause: depth-weighted derivatives made fixed bed geometry move

The pressure operator used `G_h(bed)` as bed slope, where G_h depends on water
depth. Differentiating its changing weights produces a time derivative of that
slope even though the captured riverbed is fixed. At the exact failing stage:

- Weighted slope is (0,0.01558914637).
- Its computed time derivative is (0,-75,436,265.7552) per second.
- The resulting fictitious bottom acceleration u·b_t is 7,781,373.39755 m/s².
- Weighted bottom-curvature forcing is 7,781,373.39859 m/s²; using a fixed
  geometric slope yields 0.00563608113 m/s² on the **same state**.
- The y pressure derivative changes from -9.439421980e-10 to
  3.325950446e-19; no water depth or momentum is clipped.

This is a demonstrated numerical geometry error, not proof that every remaining
instability or wave-breaking issue has been solved. The continuum distinction
between fixed bed geometry and evolving water variables is consistent with the
[SGN governing-equation documentation](https://numericalmathematics.github.io/DispersiveShallowWater.jl/stable/overview/#Serre-Green-Naghdi).
The discrete raster derivative and failure diagnosis are our implementation and
measured evidence, not a source-provided validation of this river model.

## Implemented fixed geometry option and verified counterfactual

`--pressure-bed-slope geometry` computes slope from the actual captured bed,
using centered differences internally and one-sided derivatives at nonperiodic
outer edges. Periodic fixtures wrap only when explicitly requested. No water
depth or wet-mask weights enter this geometric derivative. Dry normalized
operator rows remain identity rows; no artificial water film is added.
Kinematic water-divergence weight derivatives remain, but the fixed bed has no
fictitious b_t. Historical `weighted` slope remains an explicit default control.

From the exact preceding state and identical 1/120 s step, the fixed-slope
counterfactual has maximum speed 7.236158 m/s rather than 505.375157 m/s:
`tmp/south-fork-fixed-bed-one-step-v1-20260912.json`.
A separate one-second continuation of the saved 3.501517376 s checkpoint also
completes without the 30 m/s event:
`tmp/south-fork-fixed-bed-continuation-v1-20260912.json`.
It has 149 steps / 33 retries, final maximum speed 7.969316 m/s, retained peak
18.644108 m/s and volume error -4.54747e-13 m³. That peak and the hydrostatic-only
energy increase are retained for physical review, not hidden by the final speed.
This continuation is not a replacement for a full unsplit trajectory.

CPU suite 96215: **132 passed in 27.49 s**, including constant fixed-slope
invariance under rapidly changing depth weights, SPD/dry rows, observer
isolation, still lake and periodic momentum preservation. The earlier focused
63-test run also passed. Existing tolerances and the 40-iteration limit remain.

Pressure implementation SHA-256:
`ea0a95f1882ab38103fda2aecc28051cb7433ed8cd29f81208442698cda44a45`.
Bank driver SHA-256:
`e0728d72c635142e606c2c88f2a35e4afd901722482a2f782af46a02ad1df269`.

## GPU operator now accepts physical bed slope

The existing GPU acceleration API accepts an explicit float2 physical-bed-slope
buffer. Null retains the historical weighted-bed control; a future playable
owner must supply fixed geometry. Invalid stride/count/nonfinite slopes are
rejected or diagnosed. No gameplay owner or nonlinear forcing was enabled.

Build 23771 succeeds in 15.44 s. Full actual-device suite 91652 records
**67 successes, zero warnings/failures/unrun tests**, 17.383396 s test duration:
`unreal/Saved/RaftSimValidation/south-fork-fixed-bed-regressions-v1-20260912/index.json`.
The GPU manufactured reference independently builds derivatives in CPU double
precision and covers both weighted and fixed slopes, periodic/closed boundaries,
dry/1e-20 m cells, 17x13 and 128x128 grids, invalid slopes and invalid graph bits.
For fixed slopes, maximum acceleration error is 1.90777652e-7 and true relative
residual 1.90370419e-7; the largest observed iteration count remains 30, below 40.
CareerCatalog and progression tests still pass: South Fork is the scenario;
Troublemaker is a rapid, not a standalone menu entry.

GPU shader SHA-256:
`52af9bc1185ac3f241e406806e8b8b13f6f3c7fb73a6a7667edccda1b61e6a95`.
The initial fixed-slope DLL hash is
`91d881f8caf9123f4bcc3b8df1dfa50b424c257d103377e34065e68442965c34`.
The subsequent timing-only test rebuild 12520 succeeds in 15.96 s; DLL hash
`a042bcb8f7518466948dff6a8e16c6049106a6668d64d107e1071463ff91a6fb`.
Shader/operator executable logic is unchanged by that test instrumentation.

## Performance evidence: single-group solve is not ready for 30 FPS

Added actual GPU timestamp intervals to the 128x128 fixed-slope fixture. Inputs
are uploaded before the intervals and readback follows them; each interval
includes diagnostic clear, coefficient preparation and the two-pole solve.
Extracted diagnostics keep the repeated dispatches from being culled by RDG.
The fixture warms the same shader before eight samples. This is component
evidence, not full-scene frame time, maximum-grid qualification or release proof.

Single-test 28438 passes:
`unreal/Saved/RaftSimValidation/south-fork-acceleration-timing-v1-20260912/index.json`.
GPU intervals are 29.557, 28.969, 28.874, 28.769, 28.779, 28.938, 28.889 and
9.787 ms. CPU cook/replay jobs were active, so shared-memory contention and
pipeline bubbles may influence these intervals; do not infer a clean intrinsic
kernel cost. Even these preliminary numbers warn against integrating the
single-workgroup implementation as a 30 FPS solution. Preserve them and measure
an isolated repeat before assessing the scheduling change.

Added `unreal/Scripts/profile_nonlinear_acceleration.ps1` to verify exact process
IDs/start times and paths, temporarily suspend only the owned cook/replay,
run the same test, and resume both in a finally block. It records suspension,
resume and editor status independently of the native test report. The isolated
repeat, session 81718, completed with editor exit zero, no timeout, and both
suspend/resume status pairs zero. The exact same cook and replay processes were
resumed, not restarted. Process report:
`unreal/Saved/RaftSimValidation/south-fork-acceleration-timing-isolated-v1-20260912-process.json`.
The corresponding native index records the GPU test passing.

All isolated samples are retained: 31.431, 31.363, 31.314, 31.300, 16.186,
4.462, 4.425 and 4.071 ms. The large warmup/pipeline variation means these must
not be relabelled as a stable per-frame p95 or a pure kernel throughput figure.
Do not discard the slower samples to claim a pass. Even the shorter late
intervals do not establish adequate cost for repeated RK-stage solves plus
rendering within the 30 FPS frame budget. The single-group implementation
remains unqualified; use the same isolated fixture and preserve these controls
when evaluating the parallel implementation.

Next performance implementation: distribute the same coupled operator/PCG
across GPU groups with proper global reductions between dispatches, rather
than making one group loop over the entire grid. Retain both pressure poles,
physical slopes, whole-grid coupling, residual checks and the 40-iteration
maximum. Do not substitute independent tiles, reduced physics or lower quality.

## Full trajectory and remaining acceptance

Fixed-bed 20-second replay 8377 / PID 40392 started local 23:02:49
(UTC 2026-09-13T06:02:49.9073529Z), from the original paired capture, with
0.5-second checkpoints. It is not split or restarted. Destination:
`tmp/south-fork-fixed-bed-pressure-bank-twenty-second-v1-20260912.json`.
Session 8377 is now CLOSED, completed at 20 s with 2,888 accepted steps and
874 stage-CFL retries. Final maximum depth is 3.368724782 m, final maximum
speed 9.146565858 m/s, retained peak 20.756189560 m/s, volume error
4.547473509e-13 m3, worst correction residual 2.865809937e-6 (40 iterations).
It passes the previous 4.19 s and 11.49 s terminal points without their runaway
spikes. Final state SHA256 is
`e67358bb938dab055a5aa2ff95f235ab65eaf6921163e4261b1a2edc85083892`.
Hydrostatic-only energy falls from 107363.25094 to 95153.33259; this excludes
nonlocal pressure energy and is not a full energy-stability claim. At ten seconds the
12.646534 m/s maximum was in a 0.007711956 m cell; the maximum among cells
deeper than 0.01 m was 7.534261 m/s. Those depth bands are diagnostics only,
not masks or exclusions from acceptance. The thin-cell speed still needs
physical review. Saved-checkpoint probe44374 completed:
`tmp/south-fork-fixed-bed-peak-probe-v1-20260912.json`.
From the14.500554884s checkpoint, the first20m/s crossing occurs0.271098536s
later (82steps/82retries), at cell(y28,x48), depth0.102459690m and speed
20.052424985m/s. This is NOT a negligible near-dry film. Reconstructed SSP-RK2
update error is exactly0. Its stage pressure momentum rate(23.74763552,
12.20175093) opposes hydrostatic transport(-22.37337765,-11.17604609), leaving
positive total(1.37425786,1.02570484) while depth falls. Fixed-bed quadraticQ is
4078.913745 and curvatureC192.280558; this is no longer the fictitious weighted
bed time-derivative mechanism. It remains an unresolved nonlinear steep-flow/
breaking/boundary-model question; do not hide it with a wet-depth mask or cap.
The saved event SHA256 is
`f149fe46b541e5c584bad64d4b632744c393bb7175be236388b65f1f7e856c63`.
No scene acceptance or production integration follows from replay completion.

Current fixed-slope wave comparison 93691 completed:
`tmp/south-fork-fixed-bed-pressure-comparison-v1-20260912.json`.
The three Airy checks pass with amplitudes 0.98785824/0.99151032/0.99268262 and
phase errors 0.00794282/0.00571191/0.00410562 cycles. Rational-versus-SGN solitary
differences remain 0.06824952/0.04639299 at dx .5/.25; these are not exact SGN
convergence errors for the rational model. Stage-CFL retries and finite-solve
residuals remain recorded. No analytical result establishes scene acceptance.

Cook 96057 / PID 29104 remains active; last BOTH-audited checkpoint is
3,200 s / local 24,000. Next 3,300/local26,000 requires its completion marker
and both audits. Runtime stays at audited 600 s; the larger cook is still settling.
Map, V4 material, saved game and Raft DLL rehash unchanged. No reference-video
playback or new ordinary-play FPS capture occurred. Last ordinary-play result
remains 21.571211 FPS / p95 52.6052 ms, below the 30 FPS target. Physical breaking,
froth, total-state evolution/mean/window integration, one completed render/contact
surface, terrain/source acceptance and the entire remaining goal stay open.
