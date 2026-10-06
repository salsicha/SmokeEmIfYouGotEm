# Crest precomputation and canopy runtime binding

September 18, 2026. Binding repair verified; prefetch not promoted. No new FPS or visual acceptance.

The current instrumented normal South Fork rapid launch uses 1280x720 D3D12,
four solver lanes and all 181 engine frames60–240. It contains181 crest calls,
92 geometry/profile rebuilds and89 retained updates. Active hydraulic refresh
averages22.101136ms, publication11.932649ms per frame, and rebuilt crest work
11.789911ms. The nested scopes must not be added together. Midpoint expansion
averages only0.269982ms; another small midpoint scheduling change is not the
appropriate target. The actor module already compiles with /Ox and /fp:precise.

Raw capture: `unreal/Saved/Logs/south-fork-publication-stages-8800-v1-20260918.log`,
SHA256`df659c91b4979002e6ca893085dfa4191a1d08628031034f24857fc59b5d4ff5`.
Reports: `tmp/{crest,water}-publication-stages-8800-v1-20260918.json`.
The capture exits0 without timeout and resumes the exact cook. A previous launch
using an existing label was refused before any process suspension; its previous
evidence was not overwritten. Instrumented timings are not ordinary FPS evidence.

## Actual saved-map build defect

The first attempted editor build stops at the runtime bundle's unchanged
hash gate: the canopy commit changed the FullReach map but did not update its
saved-map binding. The guard correctly refuses the old map identity. No source
file compiled in that attempt; no acceptance gate is removed.

`audit_chili_bar_runtime_bindings.py` reloads the real saved map read-only using
the existing editor. It requires the independently verified canopy map hash,
checks the two original actor package hashes, reads all four native runtime
entrypoints and checks saved bytes again afterward. The fresh inventory is
[retained here](chili-bar-canopy/runtime-bindings.json), SHA256
`6ffa71304293ddbd5f71341fb6595eca44e9d38ede60f1076b0dd8e44960d2ee`.
The map is `c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`;
water and run-manager packages and the installed4950 state are unchanged.

The manifest now binds that independently inventoried map and inventory hash.
All2,405 runtime payloads and their full dependency closure verify unchanged.
`rebind_saved_map` returns a proposed manifest without writing anything and
rejects changed entrypoints, changed/missing/duplicate actors, stale map bytes,
non-read-only inventories and corrupt payloads. All38 runtime bundle tests pass;
[JUnit evidence](chili-bar-canopy/runtime-bundle-tests.xml). This is a map-only
binding repair, not a recook, new hydraulic state or packaged-game acceptance.

## Scheduling experiment — OFF by default

The experimental `RaftSimPrefetchCrestProfile` path snapshots only coordinates
used by the last adaptive build and evaluates the next immutable profile in
one owned background job. The callback and inputs are copied, not references
to actors or mutable water arrays. There is one pending job per owner, no
waiting during gameplay, and no queue of obsolete hydraulic states.

Adoption requires completion and exact profile-key equality. Every current
selection decision still executes; changed coordinates, new batch membership,
unfinished work and mismatched profiles use the current original sampler.
No stale height, rounded coordinate, lower detail, changed physics cadence or
second water surface is introduced. Alternate memo diagnostics cannot enable
this path. Default gameplay remains unchanged: accuracy checks pass, but the
both-order timing comparison below does not qualify the experiment.

Editor build after binding repair succeeds216.92s. The first seven native
D3D12 checks pass1.294s. A follow-up test-counter edit initially fails to compile
(`FetchAdd` is not Unreal's `TAtomic` API); its failure is retained. Changing
only that counter to supported atomic increment yields a successful19.87s
incremental build. All seven strengthened native checks pass1.339s, zero failed,
warning or not-run tests: CrestProfilePrefetch, CrestHistory, CrestMidpointExpansion,
CrestNormals, ShorelineCrestTargetCache, ShorelineFineCrest and RefinementTopologyCache.
The new test witnesses avoided synchronous evaluations and compares exact
topology across changed profiles/coordinates/membership, reset and crop changes.
An intentional bad-sample control proves whole-result rejection. Actual game
audit mode independently recomputes every adopted value and compares float bits.
The51 Python bundle/report controls pass; initial compiler warnings in existing
DetailSourceFootprint and D6Chaos code remain, not a warning-clean build claim.
Two complete 900-frame gameplay accuracy captures pass: 223 and 267 adopted
profiles, respectively 30,397,497 and 36,733,508 bit-exact sample comparisons.
That is 490 profiles and 67,131,005 comparisons with the current original
callback. This expensive audit mode is not used for performance qualification.
Reports are retained in [the evidence folder](crest-prefetch/).

The separate predeclared A/B/B/A sequence uses the same binary, four solver
lanes, FullReach station 8330 and 1280x720 D3D12. All four processes exit zero,
without timeout, and successfully suspend/resume the exact cook. All fixed
CSV sample rows 60–840 are included; verified default FrameTime mode uses
scope offset one. No expensive sample replay or stage instrumentation is on.

| Run | Prefetch | Elapsed FPS | Mean frame ms | p95 frame ms |
| --- | --- | ---: | ---: | ---: |
| A | Off | 24.751985 | 40.400800 | 48.8941 |
| B | On | 24.890203 | 40.176450 | 48.1693 |
| C | On | 23.674689 | 42.239203 | 52.3125 |
| D | Off | 25.742861 | 38.845721 | 46.2122 |

The slight first-pair improvement is not reproduced in reverse order. All four
fail the 30 FPS / p95 33.333333 ms target. Variable trajectories and machine
load also prevent a causal speedup claim. Prefetch remains an explicit diagnostic
opt-in, disabled in ordinary play. [Full timing report](crest-prefetch/timing-abba.json).
The final focused Python rerun passes all 51 tests in 3.16 seconds. No standalone
game rebuild or packaged acceptance is claimed for this checkpoint.

## Continuing physical work

8800/local22000,8850/local23000 and8900/local24000 pass the full5,382,400-cell state audit
and all86,720 artificial-bank checks (exactly dry). Maximum step residual stays
1.4754001131933592e-8m3. The8850 outflow99.3025692792m3/s still exceeds
inflow45.3069545472m3/s: NOT settled, installed4950 unchanged.
Same cook8900/start UTC2026-09-18T06:34:59.2598919Z remains live.
At8900 outflow103.4945256943m3/s still exceeds the same inflow; maximum depth
3.7783201705m and speed5.3528943751m/s. Next8950/local25000 requires its
completion marker and both audits.

Physical breaking/froth, 30FPS, full South Fork terrain/contact/traversal,
Colorado→Pacuare→Futaleufu, Chilko/Zambezi reviews, crew, normalization,
remaining regressions and release all remain open. Nonlinear runtime stays OFF.
