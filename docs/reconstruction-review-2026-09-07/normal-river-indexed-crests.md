# Exact crest broad phase - September 12

The prior goal turn made progress: actual-bank failure captures and a two-cell
counterexample established that the proposed detail flux is not positivity
preserving over unequal bed levels. This turn rechecked current code and live
cook29104 rather than restarting it. The C++ hydraulic solver already uses
hydrostatic face reconstruction in `solver_numerics.cpp`; the detail update's
frozen mean and interpolated depth/velocity texture cannot simply substitute
that total-depth operator. Consistent bed, mean evolution, moving wet domain and
state-aware admissibility remain required before nonlinear integration.

## Production performance change

`FRaftSimIndexedBreakingProfile` builds an immutable8m spatial index of each
physical crest's existing compact support. The Cartesian actor captures it
with the same support-site records used previously. Queries still evaluate the
original continuous function, in original site order. No interpolated height,
quantization, dropped nonzero lobe, stale profile reuse, changed update cadence,
mesh density, wave dimensions or foam formula is introduced.

Nonlocal overlap caps include ALL owners, even those outside the query tile.
Local envelope caps still come from exact evaluation. Inverting the supplied
flow basis, with conservative support padding for float comparisons, handles
slightly non-unit directions. Legacy profiles, unsupported coordinates/bases
and index capacity overflow fall back to the complete scan. The index is read-
only during parallel sampling. `-RaftSimFullCrestScan` restores the full scan in
the same binary for comparison. It does not change the profile or physics.

Native test `RaftSim.P2.IndexedBreakingProfile` requires EXACT height and foam
equality to the full scan across random points, support boundaries, tile seams,
negative coordinates, non-unit directions, mixed/local/global caps, reversed
site order, empty profiles and fallback cases. This is correctness coverage for
the optimization, not proof of convincing breaking or30FPS.

Build77497 succeeded in140.27s. Existing D6 damping conversion warnings remain.
Raft DLL54517b007bade09e3cef7b7d251e18659080f41705e931ce029ec3b9d7c3de34;
Water48f9caf943402a94fae7346e38d8523b1f86dd59f105b99f8337c72bef6ecc45;
mainbdf4bcba4c823fa33d0f5e8118f91b63445a7c5931b59fca81fc4fe05219cc24.
WaterDetail615b55aa... unchanged; mapdb3080cc..., material26aa5029... and
save181d1e57... rehashed unchanged before gameplay.

## Hydraulic continuation

2700/local14000 passes both independent state and artificial-bank audits.
All5,382,400 cells finite and86,720 artificial-face cells dry; outlet93.857325467
versus inlet45.306954547m3/s still settling. Runtime600s unchanged. Next2800/
local16000 requires both audits after complete output exists.

## Acceptance remains open

Native45173 exits0. Its actual JSON report records65 successes,0 warnings,
failures or unrun tests. The new fixture compares149,679 points with EXACT
height and foam equality. Report:
`unreal/Saved/RaftSimValidation/south-fork-indexed-crest-regressions-v1-20260912/index.json`.
No overall speedup is inferred from source inspection or the build. The30FPS,
physical breaking/froth, reference comparison, terrain/collision traversal,
remaining rivers/crew/normalization/release and final commit scope stays active.

## Actual-game measurements and checks

Full-scan profile75997 and default-indexed48041 both exit0 and safely resume
the identified cook (suspend/resume status0, no timeout). Both use1280x720,
D3D12, Development, target metadata30,300CSV rows, audited rows100-250.

| Path | FPS | Frame p95 | Crest update mean | Selection mean | GPU mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full scan | 21.016691 | 56.9051ms | 14.277785ms | 6.698921ms | 15.644896ms |
| Indexed default | 21.571211 | 52.6052ms | 14.007118ms | 6.760436ms | 15.556737ms |

Both FAIL30FPS. Small differences between nondeterministic trajectories and
refresh counts do not establish a sustained or sole-cause speedup. Selection
time did not decrease in this comparison. The index is exact, but it has not
removed the dominant whole-surface work. Report:
`tmp/south-fork-indexed-crest-performance-v1-20260912.json`.
Full CSV SHA8157cad7ad18f22415d95298cef4bab2c02bb35dfbebcd78e8e26b5454ac21d0;
indexed SHA dda1efa83e072796e4606ed107466ac208b8a1f76698a5d15e1e3c3bf71febe6.
Indexed686 paired commits/1hold, final PDE backlog0.000912s. Max queue age0.4s
includes startup/capture and is not warmed latency acceptance.

Initial CSV audit rejected the indexed capture's late column. Inspection of
the installed UE5.8 `CsvProfiler.cpp` verified that `AddSeries` appends indices,
`FinalizeNextRow` writes the then-current width, and `Finalize` writes the full
trailing header. This file appends ONLY `Exclusive/GameThread/EventWait/Effects`
at data row85; the original358-column header remains an exact prefix of the
359-column final header. The parser now permits monotonic append-only widths,
requires exact initial-header prefix, unique final headers, final-row/header
width agreement and completed metadata. Truncation, reordered columns,
concatenation, invalid values and absent required metrics remain errors. It
does not pad missing metrics with zeroes or change the30FPS gate.47 focused
Python tests pass, including8 CSV tests. In-place writes to the two existing
parser/test files failed; apply_patch moved each to a scoped sibling and back,
preserving the original paths without changing ACLs or leaving temporary files.

Actual ordinary-game2992 exits0 and produces8PNGs.007 inspected: no trial bank
spike, but broad rounded crests and soft merged whitewater remain UNACCEPTED.
Paired sequence114:2,021 wet contacts/954 detail-affected, no dry/unavailable
points, support/carrier maxerror4.764629216e-5cm. GPU4,226queries maxRGBA
5.960464478e-8 passes on that same sequence. Submitted macro1,549,872samples:
max targeterror0.600509882cm<2cm, fine tracking0.000259280cm, sourcechange0.
UV3 transport and UV1 bulk errors0 over50,625source vertices. These checks
exclude physical calibration, full traversal, render latency and breaking/froth
acceptance. Reports:
`tmp/south-fork-indexed-crest-{contact,gpu,crest,transport}-v1-20260912.json`;
the crest mesh report appends `.cartesian-mesh.json` AFTER `.json`.

Three captured raw states retain positive total depth: minima0.009121723/
0.009952255/0.009989984m; max|eta|0.123086/0.101005/0.168619m. Hash-bound
report `tmp/south-fork-indexed-crest-input-audit-v1-20260912.json`. This bounded
smoke check does not validate the rejected nonlinear hybrid. Experimental
strain remains OFF and the finite-depth detail shader is unchanged.
Map, material and saved game rehash unchanged after play. No UE/build process
remains. Cook29104 live at local14370/time2718.5s;2700 last both audited,
2800/local16000 next. No new reference-video playback.

NEXT: prioritize the total-depth/bed/mean consistency needed for actual evolving
macro crests and froth. The detail flow texture currently stores interpolated
depth/velocity/activity, not a paired bed/mean-surface record; treating its
changing mean as a frozen equilibrium is not justified. Preserve actual-bank
failure cases when changing that contract. The complete terrain, other rivers,
crew, normalization, release and final-commit objective remains active.
