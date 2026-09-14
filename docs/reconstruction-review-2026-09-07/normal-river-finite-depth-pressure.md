# Finite-depth pressure candidate — September 12

Current status: the verified linear finite-depth correction is now enabled by
default for South Fork Full Reach. This is a physical-model integration step,
NOT full-scene, nonlinear breaking, convincing-froth or30 FPS acceptance.
Historical opt-in verification and failures are retained below.

The preceding goal turn made progress by verifying native30 FPS budgets,
correcting failed-gate reporting, and measuring the wave-regime mismatch. This
turn implements a correction in the existing detail solver, not another foam
mask. Full scene, physical breaking, performance, and release acceptance remain
unproven. South Fork is the scenario; Troublemaker is only a rapid.

## Model and integration boundary

The linear detail momentum flux now has an optional finite-depth pressure.
It retains the existing conservative height/foam flux, source terms, RK2 clock,
wet mask, shared rendered/contact payload, and exact moving-window transfer.
There is no extra water surface or optical-only displacement. During verification
the playable component selects it with `-RaftSimFiniteDepthDetailReview`; normal
play remains unchanged until tests and actual-game review establish suitability.

The pressure multiplier approximates `tanh(k*h)/(k*h)`. The four-level truncation
of [DLMF4.39.1](https://dlmf.nist.gov/4.39.E1), ending at denominator9, gives
`(1+x²/9+x⁴/945)/(1+4x²/9+x⁴/63)`. It splits into two positive Helmholtz filters
plus a1/15 local residual. Its intrinsic-speed error is below3% for `0<=k*h<=8`;
it is not exact in arbitrarily deep water. This derivation is NOT an
implementation of the FFT/decomposition algorithm in Jeschke and Wojtan.

The pressure filters use local depth and reflecting wet-neighbour boundaries.
This is a variable-depth approximation, not the exact variable-bathymetry
potential-flow operator. Chebyshev iteration uses Gershgorin spectral bounds
from the maximum captured depth; no tuned overrelaxation or state clipping.
Pressure is recomputed for each RK stage, so it adds no stale historical state
to a remap. Runtime quality/geometry/contact limits and the30 FPS target stay
unchanged. Linear dispersion alone does not produce overturning crests.

## Evidence in progress

Build90200 succeeds in106.47 seconds, retaining existing D6 damping-conversion
warnings. The first CPU direct-matrix test found32 iterations insufficient for
the predeclared3e-5 potential-error gate: maxima4.76423e-5 and5.72223e-5 for
nonperiodic/periodic uneven-bed fixtures. Independent40-iteration checks give
1.06294e-5 and1.03194e-5;48 gives3.37616e-6 and2.93601e-6. The tolerance is not
being widened. The first native run uses the built32-iteration candidate to
measure actual wave behavior before selecting the final solve work.

New native coverage measures travelling-wave phase against finite-depth Airy
theory at depths1.5/3m, wavelengths4/8/16m, both axes, and0.4m/s current. It also
checks amplitude, signed volume, unchanged foam, doubled-iteration convergence,
uneven-bed rest, dry cells, batch equivalence, and invalid solve settings.
The existing exact moving-window test now exercises the new mode as well.
Tests do not constitute visual, nonlinear breaking, or full-river acceptance.

Native77848 exits0 but report has61 passes and1 failure; exit status alone is
not acceptance. All twelve actual GPU phase measurements are within1.94% of
Airy theory. Amplitude retention is0.666–0.999, signed-volume/foam/dry/batch
checks pass, and variable-bed rest error is5.27691e-8. The failure is pressure
convergence: max component difference1.96381e-4 when going from32 to64
iterations, exceeding the unchanged1e-4 limit. The report is retained at
`unreal/Saved/RaftSimValidation/south-fork-finite-depth-regressions-v1-20260912/index.json`.

Default solve work is now40, with the native test doubling it to80. The
independent direct-matrix test passes the original3e-5 limit. Combined pressure,
wave-regime, CSV and release-report Python suite:31 passed. No normal-play
promotion is justified yet; the corrected build and actual-game checks follow.

Build81348 succeeds70.28 seconds; the added forced-wave/mode-change test build
77637 succeeds13.73 seconds. Final native51793 exits0 with62 successes, zero
warnings/failures/unrun. Report:
`unreal/Saved/RaftSimValidation/south-fork-finite-depth-regressions-v2-20260912/index.json`.
Actual intrinsic phase error is at most1.756873%; doubling40 to80 iterations
changes state by at most6.22881e-5, within the unchanged1e-4 gate. Rest error
3.65544e-8, dry and batch errors0. Source forcing produces max9.4155 cm relief
without a height clamp, within the existing10 cm fixture bound. The forcing
itself remains the authored depth-integrated excitation, not a measured
turbulence field or a new atmospheric-pressure boundary model.

Current Raft DLL `b2eb6f2d78416304ae51f20318e1b15eae2ec2d57b09004d956d573cccbc01e1`;
WaterDetail DLL `ef1d7f749590eae3d928340a1308d10de280b75f1af1358ae3d1c9abdc0f8215`.
Actual-game capture12270 is the next verification, with the candidate enabled
on the existing South Fork carrier and paired GPU/contact audit paths.

Actual-game12270 exits0. The initialization log confirms moving Cartesian,
finite_depth=1 and40 iterations. All40 PNGs were produced; frames000/039 were
inspected. Broad macro crests are still smooth and froth patches too soft;
this is NOT convincing breaking/froth acceptance. No continuous movie/reference
playback is claimed. The scene remains on its original material.

At paired sequence101,956 of2,021 contact points contain nonzero detail, up to
6.65838 cm. Maximum actual support/submitted-carrier error is4.76785e-5 cm.
The4,226-query GPU payload audit matches the same sequence with maximum RGBA
error2.98023e-8 and passes. Shared crest1,550,016 samples: maximum target error
0.600681 cm (unchanged2 cm gate), source-vertex change0. All50,625 source UV3
transport/UV1 bulk values match their own authorities exactly. These do not
establish calibrated momentum, full traversal, or render-latency acceptance.

Reports use `tmp/south-fork-finite-depth-{contact,gpu,crest,transport}-v1-20260912.json`
(crest mesh report additionally ends `.cartesian-mesh.json`). Capture images:
`unreal/Saved/Screenshots/south-fork-finite-depth-v1-20260912_000.png` through039.
The recording run logged184 commits/1 hold and max queue age0.4 seconds;
ordinary isolated timing and warmed presentation latency still need assessment.

## Isolated comparison and default integration

Both same-binary profiles exit0 and safely resume the cook. Candidate64309:
19.785737 FPS, frame p9565.7996 ms, GPU mean16.158807 ms. Prior-pressure mode
46438:20.217905 FPS, p9570.2056 ms, GPU mean13.685309 ms. Both FAIL30 FPS.
Trajectory/refresh-count differences preclude attributing the full difference
to pressure work. Candidate ordinary PDE backlog is3.263 ms,653 commits/1 hold,
max queue age0.4 s including startup/screenshot (not warmed latency acceptance).

The tested correction is enabled by default only when the moving component is
in `L_SouthForkAmerican_FullReach`. Other maps remain unchanged unless explicitly
reviewed. `-RaftSimShallowPressureReview` preserves the comparison path; no
quality, timestep, or contact tolerance was lowered. Default-integration build
29042 succeeds14.15 seconds. Raft DLL is now
`0d0622c6f680cd65fc156cdce2fb5dcfc34b6a7aaeb4c39e2d34dc65287ae761`;
WaterDetail remains ef1d7f74… and main remains934a8714….

The prior CSV metadata override unexpectedly produced0 because the engine's
command-line parser matches the key without its equals sign. The audit target
was independently30 throughout. The script now sets the actual CSV CVar to30
in ExecCmds before starting capture; a fresh default-mode run verifies this.
No old capture metadata is rewritten or treated as a performance pass.

Fresh ordinary-play50264 exits0, with no finite-depth review flag. Its log
confirms finite_depth=1/40 iterations; CSV metadata now correctly says30.
Warmed rows100–250 average20.043179 FPS, frame p9558.8251 ms, GPU mean16.163983 ms:
still FAIL30 FPS. CSV SHA256
`2024648202f41f769a3c5ea4f8045164895f7bedef65b102450dfeaa8910730b`.
Report: `tmp/south-fork-finite-depth-default-performance-v1-20260912.json`.
Screenshot `unreal/Saved/Screenshots/south-fork-finite-depth-default-profile-v1-20260912.png`
was inspected. Ordinary PDE backlog1.427 ms,644 commits/1 hold, max queue age
0.4 s still includes startup/screenshot and is not warmed render-latency proof.

This closes neither the smooth macro-crest problem nor convincing froth. Next
is source-coupled finite-amplitude crest breakup and its actual motion review,
while continuing the larger CPU crest/publish cost reductions needed for30 FPS.
The full terrain/collision traversal, settled full-river data, Colorado/Pacuare/
Futaleufu, Chilko/Zambezi, crew, normalization, release, and final commit remain
required. Reference videos have not been newly viewed during this turn.

Final exact-default-build native run65533 exits0 and its actual JSON report
records62 successes,0 warnings,0 failures and0 unrun tests (15.9134 seconds).
Report: `unreal/Saved/RaftSimValidation/south-fork-finite-depth-default-regressions-v1-20260912/index.json`.
This verifies the enabled-default binary, not only the earlier opt-in build.
The hydraulic cook remains live at local step11330/time2566.5 seconds;
2500 seconds remains the last independently audited snapshot, with2600 next.
No hydraulic snapshot was promoted; runtime data remains the audited600s set.
