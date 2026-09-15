# Typed crest selection — September 15

This is a measured candidate for the existing playable crest reconstruction,
not a new wave/froth model or scene acceptance. It targets the last ordinary
11.130556 ms/frame crest-selection scope without reducing visual quality.

`FRaftSimSurfaceRefinement::BuildSelected` can now retain the concrete selection
predicate type through its triangle loop. The original erased `TFunctionRef`
path remains available in the same binary. The candidate avoids an indirect
predicate call per triangle and permits compiler inlining; it does not change
the predicate's arithmetic or evaluation order. It preserves all quarter-grid
samples, 0.5 cm selection tolerance, three refinement levels, nonzero-region
tests, detail windows, per-build profile epochs, 128-triangle batch schedule,
memo limits, ordered parent/triangle assembly and source-cell ownership.

The candidate starts opt-in with `-RaftSimInlineCrestSelection`. Rejected older
shared-corner, region-index, batch and flat-memo variants remain disabled.
There are no terrain, collision, material, solver, water-state or cadence edits.

`-RaftSimCrestInlineAudit=ABSOLUTE_PATH` records 64 actual changed-input pairs
after two warm builds, alternating which implementation runs first. It compares
ordered parents, indices, owners and expanded coordinates, plus production
topology. Diagnostic arrays never replace production output. Timing includes
the complete adaptive build with independent retained histories, not just its
inner predicate. Extra diagnostic reconstructions make that run unsuitable as
ordinary FPS evidence. The strict Python parser retains repeated calls within
a frame, requires all 64 pairs and both orders, and rejects malformed counts,
timings, frame history and any claimed non-boolean exactness result.

## Verification

Initial editor build succeeded in 98.06 seconds; the two pre-existing D6 damping
double-to-float warnings remain. Native `CrestInlineSelection` passed, comparing
21,021 expanded vertices over 24 moving profiles/crops, winding changes, region
and detail windows, and cache epochs against the original and serial paths.
The Python pair/CSV/relief evidence suite has 23 passes.

The first broad native invocation omitted required GPU fixture arguments:
75 PASS / nine FAIL. That is an invalid regression setup, retained at
`tmp/crest-inline-native-v1-20260915/index.json`, not a pass or waived gate.
The rerun supplies the original fixtures and adds Cartesian surface and career/
progression coverage: **91 PASS / 0 FAIL / 0 not run**, 28.205648 seconds,
`tmp/crest-inline-native-v2-20260915/index.json`. All nine missing-fixture
failures are resolved by supplying inputs, not changing tests or their gates.
Final native report SHA256:
`2996ae902128639f2c593a84adf8a70392a5d25a430bf57771bea1d15c379ca7`.

## Actual-input result: reject promotion

The ordinary South Fork full-descent scenario at station 8330 completed all
64 pairs on frames 122–185. Ordered topology, ownership and expanded coordinates
match exactly across **4,299,524 vertices / 3,116,342 triangles**, including
production topology. No diagnostic output was substituted into play.

| Call order | Pairs | Original erased mean ms | Typed candidate mean ms |
| --- | ---: | ---: | ---: |
| All | 64 | 11.465912 | 11.397789 |
| Original first | 32 | 11.168825 | 10.569222 |
| Candidate first | 32 | 11.763000 | 12.226356 |

The 0.068124 ms overall mean advantage is order-sensitive. The candidate is
slower by 0.463356 ms when it runs first, and wins only 33/64 individual pairs.
It **fails** the both-order qualification. Keep the original erased selector
as the ordinary default; do not claim a latency or FPS improvement. This is a
different candidate from the previously rejected memo/region/scheduling trials,
but it does not resolve the crest hotspot either.

Complete native pair:
`tmp/south-fork-crest-inline-pair-v1-20260915.json`, SHA256
`2ec0190344308ea652cf129d2981a3283aa5035affc6ecb564933b7cfc21a4e8`.
Strict analysis: `tmp/south-fork-crest-inline-analysis-v1-20260915.json`, terminal
exit 1 for the failed timing qualification (exactness is separately true).
The paired game's 300-frame CSV is diagnostic overhead, not ordinary FPS.

Build, both native-test jobs, paired-game and ordinary-game jobs are terminal.
A separate ordinary-default capture has no inline flag or paired diagnostics:
300 frames, rows 120–250, 1280x720 D3D12 Development/WindowsEditor. It measures
**12.361760 FPS**, mean frame **80.894628 ms**, p95 **93.2314 ms** — FAIL 30 FPS.
Crest selection remains 10.995881 ms/frame (11.080465 on positive rows); water
step 16.721307 ms/frame and surface tick 53.053412 ms/frame. These scopes nest
or overlap; do not sum them. This short capture does not prove sustained,
packaged, traversal, physical or visual acceptance, nor a causal FPS improvement
over a different run. The rejected candidate is disabled in this capture.

Ordinary CSV: `unreal/Saved/Profiling/CSV/south-fork-crest-inline-default-v1-20260915.csv`,
SHA256 `bbb22472af2fcd180ea67d0074a96c83c526b9c2aa9b720767e2766c0b451fd8`.
Strict performance report: `tmp/south-fork-crest-inline-default-performance-v1-20260915.json`,
SHA256 `bd886e68fe15cbf1627c532b717ded13606f608755e79995eb523ca9e1a8fee3`.
Tested raft DLL SHA256:
`005b54b29930b1f250d73f5b30ca1370c530b2d4fb544d891d174e9097014e84`.

All 464 protected hashes matched before native testing and after both game runs. No measured/inferred
geometry authority changed. Full-metric front evolution, actual visual and
30 FPS qualification, later rivers, crew, normalization and release remain open.
Do not repeat this predicate experiment as a presumed speedup. Required next
work remains physical front work/forces and actual wave/froth integration, plus
the unresolved larger solver/surface costs; scene acceptance is not advanced by
the exactness of an unqualified scheduling/compiler candidate.
