# Fused GPU pressure reductions — September 13

The preceding turn verified the desktop30FPS gates (25 focused tests). This
continuation isolates the pressure cost on actual captured South Fork inputs,
implements a lower-dispatch solver with unchanged equations, and finishes the
existing20s hybrid replay. This is not playable-water or frame-rate acceptance.

## Measured bottleneck, not inferred from the old synthetic timing

Paired benchmark89574 CLOSED successfully after build1112 (15.77s). It retains
solution-dependent output AND true residual for both paths. The operator uses
the exact GPU-produced RHS, geometry, wet graph, fixed slope and fraction used
by the full pipeline. Full/operator order alternates each sample. Uploads,
readback, FV transport, RK and rendering are excluded.

`unreal/Saved/RaftSimValidation/south-fork-paired-pressure-timing-v1-20260913/index.json`
records1success/0warnings/0failures/0unrun. The process report confirms exact
cook29104 and replay40864 both resumed(status0); no timeout/editor failure.
All32 intervals remain in the matching Saved/Logs log. Nonbreaking operator
7.930–8.038ms versus full8.274–8.443ms establishes that the operator dominates
this interval, not the seven surrounding forcing/reconstruction phases. During
the subsequent hybrid case both paths abruptly become much faster (operator
1.399–1.507ms, full1.449–1.594ms after the transition). Cause of the timing
regime change is not established; do not label it a physical-model improvement
or discard the slow samples. The older1.2ms synthetic interval is not used as
a like-for-like baseline.

## Same whole-grid PCG, fewer dispatches

`RaftSimSolveNonlinearAccelerationGPU` now has a `bFusedReductions` option.
The existing one-workgroup and six-dispatch distributed implementations remain
comparison paths. The new default uses four dispatches per iteration:

1. Apply W to the full-domain search direction.
2. Apply A and reduce direction-dot-A-direction within each workgroup.
3. Each workgroup repeats the small global denominator reduction, calculates
   the same alpha and updates its segment of solution/residual, then writes
   its new residual/preconditioned-residual partial sums.
4. Each workgroup repeats the new global partial reduction, calculates the
   same beta and updates its segment of the search direction.

Separate NextPartial/NextControl buffers prevent read/write races between
workgroups; no grid-wide spinlocks, independently solved tiles, reduced
resolution, lowered iteration count or approximate operator are introduced.
Only group0/lane0 writes global diagnostics and control. Original normalization,
convergence criterion,40-iteration maximum and final true residual are retained.
Extra storage is16 bytes per workgroup plus32 bytes,1056bytes at128x128.
The full pressure pipeline forwards the option; fused is now its default too.
Neither helper is yet connected to playable state evolution.

## Verification and cost

Candidate build85813 succeeded17.45s. Actual-device full native92643 CLOSED
68successes/0warnings/0failures/0unrun in15.673629761s:
`unreal/Saved/RaftSimValidation/south-fork-fused-pressure-regressions-v1-20260913/index.json`.
Tests compare one-group, legacy distributed and fused distributed paths to
independent CPU manufactured solutions, including512x512,1x257, dry/thin cells,
nonperiodic/periodic edges, fixed slopes, zero/mixed fractions and invalid
inputs. Fused maximum observed acceleration error1.7011535e-7 and true residual
1.91257067e-7 remain far below the unchanged1e-4/2e-5 component gates.

Both full-pressure paths compare all seven fixtures, including captured128x128
states. Fused captured force errors/residuals equal the prior reported metrics:
nonbreaking0.000122785568 /2.29461549e-7; hybrid0.000153422356 /2.12536547e-7.
Pole iterations remain40/24 and40/23. Zero/lake force stays exactly zero.
Additional single-active-pole tests were then added, requiring an inactive
pole's solution and iteration count to remain exactly zero.

Isolated timing26042 CLOSED1success/0warnings/0failures/0unrun (0.837604105s):
`unreal/Saved/RaftSimValidation/south-fork-fused-pressure-timing-v1-20260913/index.json`.
Only cook29104 was suspended/resumed(status0); the replay had already exited0.
This benchmark rotates all four full/operator × legacy/fused modes across
16 samples per captured case. All128 intervals are retained in
`unreal/Saved/Logs/south-fork-fused-pressure-timing-v1-20260913.log`.

| Captured case/path | All 16 intervals, min–max ms | Interpretation |
| --- | --- | --- |
| Nonbreaking full legacy | 1.358–8.457 | Large within-run timing transition |
| Nonbreaking full fused | 1.211–7.720 | Transition retained, including2.306ms |
| Nonbreaking operator legacy | 1.317–8.085 | Same timing regimes |
| Nonbreaking operator fused | 1.148–7.351 | Same timing regimes |
| Hybrid full legacy | 1.321–1.358 | Mean1.333375ms |
| Hybrid full fused | 1.145–1.187 | Mean1.155500ms |
| Hybrid operator legacy | 1.275–1.309 | All later-case samples retained |
| Hybrid operator fused | 1.099–1.141 | All later-case samples retained |

The later hybrid block shows a13.34% mean full-pressure reduction on these
inputs. It does not establish all-scene cost or sustained gameplay improvement.
The slow initial regime still exists. Even the later1.1555ms is one pressure
evaluation, not a complete water step: RK stages/substeps, FV transport,
acceptance, foam and other work must fit the unchanged full solver budget.

Default/single-active-pole build65932 succeeded15.59s. Final full native11863
CLOSED68successes/0warnings/0failures/0unrun in15.690983772s:
`unreal/Saved/RaftSimValidation/south-fork-fused-default-regressions-v1-20260913/index.json`.
Single-active-pole fused cases report0/11 and30/0 iterations with exactly-zero
inactive solutions. Scoped tracked-document whitespace check passes. The
whole-worktree `git diff --check` hit sandbox-denied Git LFS temporary storage;
it is not recorded as a successful whole-worktree check.
Candidate timing DLL SHA256:
`b885751f3f81ffd10445721aa497576a9075c8159f12d291544e1d21c58fc656`.
Final-build DLL SHA256:
`b58794bf02b4bfe6f15a82f82c298bb9b0985126747c1ea637aa3099809d8f34`.
Acceleration shader SHA256 (both builds):
`7a0c073c7e8b520abc6a094646429e9d2791c7ae0eda1a385979ca4efe097a7f`.

## Other authoritative progress and next integration work

Hybrid replay23543 CLOSED20s,2903steps/957retries, volume error0, peak17.017388151m/s.
Its final state hash and physical caveats are recorded in
[hybrid-breaking evidence](normal-river-hybrid-breaking.md). The surge remains
unqualified; no speed/depth cap was added. Cook96057 is still live;3300/local26000
passed BOTH state and artificial-bank audits, still settling, runtime600s
unchanged.3400/local28000 is next after its completed marker.

Next implement conservative GPU FV transport and RK stage acceptance, including
true-residual qualification, physical boundary/mean/window exchange, front and
breaking-energy-to-froth evolution, and one completed render/contact surface.
Then verify actual motion against references and ordinary playable30FPS.
No reference playback, map/material/save change or fresh gameplay FPS occurred
in this turn. South Fork remains the scenario and Troublemaker a rapid only.
All terrain/river/crew/release/final-commit requirements remain active.
