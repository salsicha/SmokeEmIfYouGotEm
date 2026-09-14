# Current playable wave regime and 30 FPS checks — September 12

The previous turn made progress: the user-authorized 30 FPS target was updated
and tested, and the rejected rectangular-froth experiment was restored. This
turn measures the current build; it does not claim a new visual implementation.

## Fresh actual-game performance

Isolated CSV run `south-fork-30fps-current-profile-v2-20260912` exited 0. The
verified hydraulic cook PID29104 was suspended and resumed successfully, with
its original start time checked. The earlier sandboxed v1 attempt failed to
obtain the process handle before suspension or game launch; its report remains.

At 1280x720, Development/D3D12, the unchanged warmed rows100–250 average
19.492874 FPS, with frame p95 70.4635 ms. Crest update averages16.371928 ms;
GPU time averages13.480803 ms. This fails30 FPS /33.333 ms. These overlapping
timings must not be summed or compared as a controlled optimization A/B.
The prior20.569411 FPS capture is historical, not the current-build measurement.

Report: `tmp/south-fork-30fps-current-performance-v1-20260912.json`.
Screenshot actually inspected:
`unreal/Saved/Screenshots/south-fork-30fps-current-profile-v2-20260912.png`.
It still shows broad smooth whitewater and excessive merged whiteness. It is
not convincing breaking/froth acceptance or a continuous motion review.

## Native gate execution and launcher correction

The profiling script now has an explicit `-NativePerformanceGate` mode:
10-second warmup,20-second soak, required FullReach map, fresh dedicated report,
and director-owned exit instead of screenshot auto-exit. It preserves the
existing CSV mode. This short development test is not packaged release acceptance.

Native v1 emitted target30, frame budget33.333332 ms, hitch budget66.666664 ms.
Its report says `passed:false`,424 frames, p9556.376301 ms,4 hitches, and solver
average4.582 ms. Three diagnostic GPU snapshots were captured in this run;
therefore its timings are NOT a clean performance qualification. The engine
requested exit9 but the host reported0. The wrapper now requires a Boolean
`passed` from the fresh gate report and fails if that result is false or missing.
PowerShell parsing passed. Clean v2 (without snapshots) has453 frames,
workload p9553.226101 ms, wall-clock p9553.471901 ms, and solver average
4.361625 ms. It reports failure and the corrected wrapper exits1, even though
the host game status is0. Cook suspension/resumption both return0. This
verifies failure propagation and native30 FPS budget execution, not acceptance.
Reports are `unreal/Saved/RaftSimValidation/south-fork-30fps-native-gate-v2-20260912-gate.json`
and the same prefix's `-process.json`.

The v3 report retained a misleading `hitches_over_33ms` key even though the
counter used66.667 ms. Native schema v4 now names it `hitches_over_budget`.
The release-report reader handles both v3/v4 and still requires representative
player-presentation qualification. All17 release-candidate tests pass. Pytest
was installed in a task-local temporary directory; sandbox access to that
installation failed, then the approved test run completed successfully.

Build71801 succeeds in15.21 seconds. Fresh native v4 run reports460 frames,
workload p9550.014801 ms, wall p9550.895603 ms,1 hitch over66.667 ms, solver
average4.251047 ms, `passed:false`; the wrapper correctly exits1 and resumes
the cook. No snapshots were requested. Main DLL SHA256 is now
`934a871433696b6455fdd823cb7a36509487463bcc8c4c96a900e22ecbcb16f1`.
The CSV measurement above precedes this reporting-only rebuild. No physics or
rendering code changed. The CSV still records a historical60 Hz display-derived
metadata target; the script now passes `-csv.TargetFrameRateOverride=30`, which
engine source confirms affects metadata, not a frame cap. A subsequent CSV
capture must verify that label; native v4 already explicitly verifies30 FPS.

## Physical-model diagnosis from actual GPU state

`physics/scripts/audit_detail_wave_regime.py` checks complete snapshot arrays,
hashes inputs, and evaluates explicitly declared wavelength probes. Four tests
cover shallow/deep limits, scale invariance, wavelength dependence, quiet/dry
state, and invalid input. All four pass.

Three current playable128x128 GPU snapshots at10/15/20 seconds,0.5 m cells,
contain10,490–11,437 wet cells. Median depths are1.41–1.49 m. Raw detail-height
RMS is5.32–6.10 mm; maximum absolute perturbations are5.88–10.02 cm. The latter
is surface state, NOT the pressure-head parameter (which remains0.06 m).
Inputs: `tmp/south-fork-30fps-detail-v1-20260912/live_00.json` through02;
report: `tmp/south-fork-detail-wave-regime-v1-20260912.json`.

Equations2/3 of [Jeschke and Wojtan, 2023](https://doi.org/10.1145/3592098)
give finite-depth Airy frequency `sqrt(g*k*tanh(k*h))` versus shallow-water
frequency `k*sqrt(g*h)`. At these captured depths, the current continuum model
predicts a median intrinsic phase speed51–55% too high for a4 m probe wave
(eight cells),17–19% for8 m, and about5% for16 m. These are model comparisons,
NOT measured runtime propagation speeds or wavelengths identified in footage.
They exclude numerical dispersion, damping, current advection, variable beds,
and finite-amplitude breaking. Airy theory alone cannot establish overturning.

The actual shader still uses `sqrt(9.81*depth)` for all wavelengths; SHA256
`2493df90063ca5185eb293b869e85b903df92799234504c177899eb80497bf8a`.
Given fixed site inputs, the macro crest branch is a fixed Gaussian profile
with authored toe/tail terms. The current detail state does not make that
large crest physically overturn. This identifies a model limitation that
further foam-mask sharpening cannot repair.

Next implementation should validate finite-depth dispersive wave propagation
on the existing shared detail/contact surface, with a real GPU frequency test,
then source-coupled finite-amplitude crest breakup. Preserve wet boundaries,
mass/momentum accounting, registration, raft contact, and the30 FPS target.
Do not promote an isolated flat-depth Fourier demonstration as full-river
integration. The existing3D liquid experiments also remain unaccepted.

An independent numerical retry of higher-order foam advection did not meet
the existing2 mm centroid tolerance (MC error3.76 mm); no transport change was
installed and the tolerance was not loosened. No materials, maps, terrain,
save data, physics rates or rendering quality settings changed this turn.
South Fork remains the scenario; Troublemaker remains only a rapid.

All terrain/collision/hydraulic traversal, later-river, crew, normalization,
release and final-commit requirements remain active.

The same live cook reached2500 seconds/local step10000. Both independent state
and exterior-bank audits pass:5,382,400 finite cells, max depth4.165785 m,
max speed7.191116 m/s, volume2,961,849.884212 m3, driver-volume error magnitude
1.86e-9 m3, and all86,720 artificial-bank face cells exactly dry. Outflow is
95.898610 versus45.306955 m3/s inflow, so it is STILL SETTLING and has not
replaced the600-second runtime data. Reports are
`tmp/south-fork-expanded-2500s-state-v1-20260912.json` and
`tmp/south-fork-expanded-2500s-banks-v1-20260912.json`.
Next snapshot2600/local step12000 needs both audits; do not restart the cook.
