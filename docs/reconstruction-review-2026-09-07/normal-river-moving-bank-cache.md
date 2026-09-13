# Normal-river moving shoreline cache — September 12

This is a geometry-preserving performance change, not visual, traversal or
release acceptance. South Fork is the playable scenario; Troublemaker remains
an in-river rapid and is excluded from the scenario menu.

## Implementation and exactness

Previously any changed wet/dry edge crossing rebuilt every cell of the water
grid, even when triangle connectivity was unchanged. The cache now writes the
new, exact bank vertices and checks the original orientation/degeneracy decision
for every candidate triangle containing a bank vertex. Candidates omitted by
the existing `abs(cross.Z) <= 1e-8` rule are retained in that check: a newly
nondegenerate triangle must trigger a rebuild too. Entirely source-grid
triangles cannot change their XY decision while source XY remains identical.

A changed decision still rebuilds. So do changed source XY, wetness,
availability, dimensions or storage mode. No coordinate rounding, crossing
tolerance, geometry simplification, altered dry mask or reduced crest sampling
is introduced. All original attributes and exact crossing positions are
rewritten even on a connectivity reuse. Both dense and reserved edge storage
are covered.

Build `south-fork-moving-bank-cache-build-v1-20260912.log` succeeded in 87.66 s.
Raft DLL SHA256:
`e3e11f6b7f45d1e73631b036eb213db4d59f091d7fc7ca3a0575aabf8e9a2665`.
Native/D3D12 report
`unreal/Saved/RaftSimValidation/south-fork-moving-bank-cache-regressions-v1-20260912/index.json`
has **36 successes, zero warnings, failures or unrun tests**; process exited 0.
This includes catalog/save migration, actual raster membership, compact upload,
fine-crest accuracy, current history, source packing and streamed-ground tests.

The new moving-bank test makes 4,608 comparisons against fresh construction:
3,520 reuses, 304 membership changes and 36 same-count winding changes across
all 16 cell masks, rotated/reflected cells, concave cells, near-degenerate
coordinates and both storage layouts. Existing full 225x225 moving-bank tests
also retain 32 fresh-build comparisons. Drawn attributes, indices and cell
lookup must match exactly. Rebuild-count expectations changed to reflect the
optimization; no geometric acceptance check was removed or loosened.
Five strict CSV-parser unit tests also pass.

## Current-map baseline

The fresh baseline includes current source-aligned ground, the integrated
1,268-tree canopy and local-current froth material. Map SHA starts `db3080cc`,
water material `d55e5cdc`; pre-change Raft DLL starts `5b5edff1`.
The reusable `unreal/Scripts/profile_south_fork_current_map.ps1` verifies the
exact live cook PID, start time and executable before briefly suspending it;
`finally` resumes that same process. Game timeout and process exit are recorded.
No cook is restarted or duplicated for measurement.

Baseline CSV `south-fork-current-map-baseline-v1-20260912.csv` SHA256:
`b0bd8de40acbc302ec481e553a01708eb339c793850ec9a92178c0bbd9b9bd6b`.
Audit: `tmp/south-fork-current-map-baseline-v1-20260912.json`.
Development / D3D12 / WindowsEditor, 1280x720, ray tracing off, ordinary South
Fork full-map gameplay at review checkpoint 8330. Samples 100–250 inclusive
are 151 rows out of a completed 300-row capture. Screenshot at world 30 s
occurs outside the selected baseline interval. Suspend, resume and game exit
all returned 0; no timeout.

Baseline mean frame 45.679583 ms, p95 57.9902 ms, **21.891618 FPS**: FAIL 60 FPS.
Mean game-thread 45.360993 ms, render-thread 10.4230 ms, GPU 12.01258 ms.
Nested water means: surface tick 33.854068 ms, topology 4.850439 ms,
crest update 9.849265 ms, crest selection 4.721075 ms, source packing
3.071956 ms, solver step 4.573440 ms. Never sum nested or concurrent scopes.
Selection has 77 positive rows, not one rebuild every frame.

The baseline screenshot was inspected: normal-game terrain, canopy and raft
are visible. Broad bright, stretched froth patches remain visually unaccepted.
A screenshot cannot establish convincing breaking motion or reference fidelity.

## Post-change actual gameplay (20:29 UTC)

Profile command session 45067 exited 0, no timeout. Exact cook suspension/resume both
returned 0. Completed 300-row CSV
`south-fork-moving-bank-cache-profile-v1-20260912.csv` SHA256:
`e7cb3d3a5a5c837e79f87e5beb7a66d1f4b18cd0468920fdf7817be03fb5455e`.
The strict two-run audit passes with identical metadata and sample bounds:
`tmp/south-fork-moving-bank-cache-comparison-v1-20260912.json`.

| Mean scope, ms | Baseline | Moving-bank cache |
| --- | ---: | ---: |
| Whole frame | 45.679583 | 46.704141 |
| Shore topology | 4.850439 | 3.743277 |
| Crest update (includes selection) | 9.849265 | 10.926489 |
| Source packing | 3.071956 | 3.005488 |
| Solver step | 4.573440 | 4.821209 |

New frame p95 56.8277 ms, **21.411378 FPS: still FAIL 60 FPS**. The measured
topology scope falls about 22.8%, but the whole frame does not improve. Other
scopes and trajectories vary: do not attribute all differences to the cache
or call the short runs sustained packaged acceptance. Both selected intervals
end before the world-30-second screenshot. Post-change screenshot inspected:
normal terrain/canopy/raft remain visible, broad uniform and stretched white
froth is still rejected. No new continuous reference-motion comparison.

Map `db3080cc…`, water material `d55e5cdc…` and saved profile `181d1e57…`
rehash unchanged after both runs. No editor/game/build remains live. The same
expanded clean-restart cook (session 68098, PID 35952, start
20:09:56.4973049 UTC) is resumed and observed at local step 1070 / 1653.5 s,
maximum step conservation residual 1.2199898424825051e-8 m3. This is progress,
not a complete 1700 s snapshot/bank audit; normal gameplay still uses 600 s.

Next: local-normal versus local-froth transport mismatch, optical stretching,
physical crest/trough fidelity, remaining publish/crest CPU cost, guided
rejoin, whole-river scenery and all subsequent rivers/crew/release work.
