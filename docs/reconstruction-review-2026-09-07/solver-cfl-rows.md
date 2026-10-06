# Exact parallel CFL scan

September 16, 2026. South Fork and the full remaining-work objective are still
incomplete. This change reduces native solver work; it is not visual or 30 FPS
acceptance. [The previous Game integration](solver-game-link-and-1350s.md)
records the protected baseline.

## Implementation and verification

The CFL maximum now evaluates independent rows through the existing bounded
executor. Shape and backing-storage validation precede dispatch. Every cell
retains the original depth-to-conserved-state conversion and both original
wave-speed calls. Per-row maxima start at positive zero; their reduction is
a maximum, not a reassociated sum. The final timestep formula, CFL parameter,
resolution, dry threshold, equations and boundary treatment are unchanged.
No field or maximum is cached between steps; no public solver ABI changes.

New tests compare against the original complete scan on 1x1, 7x19 and 131x129
grids, all four rounding modes, three dry thresholds, signed zero, unordered
and infinite samples, and malformed backing storage. Invalid samples in these
comparison controls are not claimed as valid physical states. Existing tests
also compare full serial/parallel evolving states across three flux schemes,
wet/dry films, roughness, state replacement and CFL subdivision.

All four native CTest cases PASS; final rerun takes 8.62 seconds:
`tmp/solver-cfl-rows-v1-20260916/Testing/Temporary/LastTest.log`.
Candidate solver executable SHA256:
`47fc97aa7585923253442f3a7c451537f715bcce5f6c3437f50b8ee252513c73`.
Unchanged baseline solver executable SHA256:
`81807880d5938784c7c3d38198df99106a22d650297f48022982c5a260215022`.

Two fixed, four-pair alternating-order comparisons run 600 steps per process.
All 44 paired saved frames in each comparison are byte-identical, including
derived fields, and the candidate is faster in every pair.

| Input | Baseline median solve/capture | Candidate | Reduction |
| --- | ---: | ---: | ---: |
| Current-source Cartesian crop | 3.324620 s | 3.055860 s | 8.08% |
| Registered replay | 3.242745 s | 2.814695 s | 13.20% |

Reports: `tmp/solver-cfl-{cartesian,registered}-pairs-v1-20260916/report.json`.
These are component timings under concurrent work, not game frame times. The
Cartesian recipe retains its documented limitation: native runtime-export
identity has not been independently established. No input is promoted by a
matching replay.

An earlier separate attempt used validated views in the RK combination loop.
It preserved frames but showed no reliable gain (Cartesian -0.45%, registered
+0.37% median reduction). That source change was removed before this candidate.
Its binaries and reports remain in `tmp/solver-combine-*v1-20260916`; it is not
silently counted as an accepted optimization.

## Engine integration

The normal UE static-library builder succeeded. Archive SHA256:
`2ce80e6f2c5d13ca75123deb16326bdee21a9048d6558de4703a0db138c8bdfe`.
The prior archive, Game executable and receipt are preserved in
`tmp/solver-cfl-game-baseline-v1-20260916`.

Game-only build session14368 completed successfully in 281.50 seconds. All
17 editor DLL hashes remain unchanged. New Game executable SHA256:
`18d9e4b24bc845192a26ca5f50212111ff6d4d2a8cf29d1bf23fd6576ef785d1`.
Independent binary inspection finds the new archive identity above. Build
report: `tmp/solver-cfl-game-build-v1-20260916.json`. Fresh verification passes
all 2,405 staged payloads / 916,906,778 bytes, with no external source fallback:
`tmp/solver-cfl-game-runtime-bundle-v1-20260916.json`. Seven layout tests PASS.
This saved-scene bundle is unchanged, not the newer hydraulic continuation.

No editor rebuild while cook16144 holds those DLLs. The final package must
contain this verified Game executable, not an earlier game with the same
target-receipt hash. Restage if needed after the same package cook completes;
do not restart a live cook on a timeout. Actual execution and game FPS of
the rebuilt executable are not yet qualified.

## Hydraulic continuation and remaining acceptance

Same PID18716 / session69416 reaches absolute1400 s at local4000. Finite/state
and conservation checks PASS over 5,369,600 cells; all 86,720 artificial-bank
face cells remain exactly dry. Maximum depth 4.545990272 m, speed 7.164308350 m/s,
volume 3,013,800.331194 m3, maximum per-step residual 1.378528425e-8 m3.
Outflow 82.238582414 m3/s still exceeds inflow 45.306954547 m3/s: NOT settled.
Reports: `tmp/south-fork-context3-1400-{snapshot,banks}-v1-20260916.json`.
The following absolute1450 s / local5000 checkpoint also passes both audits:
all 86,720 bank-face cells remain exactly dry. Maximum depth 4.537938850 m,
speed 7.186583787 m/s, volume 3,011,913.413235 m3; maximum per-step residual
unchanged. Outflow 83.804252817 m3/s versus inflow 45.306954547 m3/s remains
unsettled. Reports: `tmp/south-fork-context3-1450-{snapshot,banks}-v1-20260916.json`.
Next completed local6000 / absolute1500 s needs both audits.

Package cook PID16144/session80881 remains live. Verify all 444 distinct
non-editor ground-source identities and the complete staged bundle before
packaged play/contact qualification. No full-hull default promotion yet.
Rock flanks, breaking/froth and actual motion still require improvement.
Last uncontended ordinary 17.819710 FPS / p95 81.6343 ms still fails the
unchanged 30 FPS / p95 33.333333 ms target. Later rivers, all-scene water,
crew, outstanding physical regressions and release remain open.
