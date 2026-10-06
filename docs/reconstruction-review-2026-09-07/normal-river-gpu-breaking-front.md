# Same-stage GPU breaking fronts — September 13, 2026

The preceding turn was progress: committed froth clocks were integrated into
the saved normal material,87 native tests and actual paired contact/GPU checks
passed, and ordinary play measured18.899245FPS/p9570.33ms (FAIL30). This turn
addresses a physical-model gap, not another optical threshold/color variant.

## Model and missing integration

Current normal legacy detail remains a perturbation model over fixed macro
crest profiles. Its finite-depth waves do not physically overturn those large
crests. The experimental nonlinear pipeline already has same-stage transport,
forcing, pressure and transactional RK2, but lacked GPU front classification.

`RaftSimBreakingFrontGPU` implements the existing CPU cardinal-front adaptation
of [Filippini, Kazolea and Ricchiuto, section6](https://www.math.u-bordeaux.fr/~mricchiu/GN1D.pdf).
It identifies contained monotone fronts, uses rise/slope and depth-ratio bore
criteria, and computes exact cell-band overlaps on the same wet component.
The existing gamma.6,30-degree slope,critical Froude1.3 and7.5-depth-difference
band are unchanged. Orthogonal bands combine by maximum coverage. This is a
2D raster adaptation, not the paper's validated1D scheme, a calibrated South
Fork law, a3D overturning surface or a foam-production/entrainment model.

Three GPU passes validate the source, classify and emit the nonbreaking
fraction. No depth/velocity/mass repair, readback or new runtime clock.
Nonfinite data, invalid wet graphs and unrepresentable bands produce error
diagnostics and NaN fractions; pressure/trial validation then rejects them,
instead of silently treating failure as a nonbreaking field. Disconnected
wet components do not share bands, and truncated fronts are counted rather
than invented. Periodic seams are considered only when actually connected.

`RaftSimTryHybridBreakingStepGPU` composes classification with the full existing
nonlinear RK2 trial. Each stage computes its own fraction from its own final
reconstructed wet graph and mass rate. That fraction enters nonlinear forcing,
the elliptic operator and pressure reconstruction together. Existing CFL,
40-iteration residual, positivity and state/time transaction gates remain.
This is NOT yet enabled as normal playable evolution: interval ownership,
moving/open boundary exchange, long-time/physical qualification and foam
production remain necessary. Do not replace the current playable solver merely
because a diagnostic passes.

## Actual input failure preserved

Trying to initialize a total-depth fixture from legacy snapshot
`tmp/south-fork-foam-source-observation-v1-20260913_02.json` fails positivity.
At(y86,x40), mean depth.011685390025377274m plus perturbation gives
total depth-.005519356578588486m. One cell is negative. Nothing was clamped or
altered; v1 export exits1 before creating output. This is a real limitation of
interpreting the existing linear perturbation state as total water depth.

The intended total-depth initialization source is the separately validated
native packet, not a repaired legacy detail array. The v2 fixture uses the
first actual source observation from
`tmp/south-fork-live-temporal-audit-v1-20260913.json.inputs.json`, SHA256
`b3ee6cb3b8b1c209613c85c2c5d15a7fe5dbc321ddf1434df9e7749f8304b9b5`.
It explicitly tests a CLOSED single step of that native state, not its observed
open-boundary interval, long trajectory or full river.

## Verification results

`tmp/south-fork-breaking-front-fixtures-v2-20260913.bin`, SHA256
`9a997b3f0d669c4e6b6db11900549476d57cfeb2c645f4e8d96362951599780f`, contains
16 float32-represented/CPU-double cases: lakes, dry state, weak/bore/subcell
fronts, genuine1e-30m troughs, disconnected components,512-cell front, periodic
translations/transposes and actual128x128 native source. Four cases include
full independent hybrid RK2 output. Source equations are not altered to match
GPU results. The new optional CPU fixture argument retains bit-identical
default/nonbreaking outputs. Sixteen focused Python tests pass in3.85s.

Initial build76939 failed on a duplicated shader-permutation access modifier;
corrected build46792 succeeds16.35s. New native test adds16 classifier cases,
five invalid-input cases, exact count comparisons and full-stage output checks
under the existing2e-5 relative/1e-4 absolute step gates.
The native suite now needs a seventh fixture flag, `RaftSimBreakingFrontFixture`.

First native24228 CLOSED1:87 existing passes, new test fails. Every classifier
field/count and RK2 state matches; diagnostic build88268 and focused31527
identify1.979060471e-9s error against the unchanged1e-9s clock gate. The test
supplies equivalent but non-normalized time3+.125; adding the small dt residual
to that large low word loses precision. Independent float32 arithmetic
reproduces the error. Normalize the compensated input pair before TwoSum;
canonical clocks retain their original words. No timestep/tolerance change.
Full native17596 CLOSED0:88 clean passes,19.975592s. GPU classifier maximum
fraction error4.87267971e-6; actual-source counts63 fronts/1411 truncated runs
match exactly. Four hybrid RK2 states pass, maximum absolute error9.53674316e-7.
All five invalid-input cases produce no finite fractions and report failure.

## Complete observed interval, not only a closed-source step

The existing temporal fixture format now has an explicit version2 hybrid-mode
word; version1 retains byte-identical nonbreaking layout. The GPU harness
recomputes the classifier for each stage and retains the existing comparisons
of split versus batched graphs and indirect versus direct pressure recurrence.
No normal-game opt-in or solver replacement is implied by a fixture mode.

Independent CPU hybrid replay completes the entire observed.01666666753590107s
interval in3 steps/0 rejections. Both stages use actual interpolated exterior
state and independently observed face velocity/rate; interior is never reset
to the second observation. Maximum depth3.235209404m, speed6.895004099m/s,
peak accepted speed6.965820824m/s; pressure residual7.989248369e-8 with unchanged
40iterations. Water change-.067829084800906m3 plus accepted outward flux
.067829084800853m3 leaves-5.268008252e-14m3 balance error. Hydrostatic energy
excludes nonlocal pressure and boundary energy: it is not a dissipation proof.
Report `tmp/south-fork-hybrid-temporal-evolution-v1-20260913.json`; fixture
SHA256 `3f5cc321dd82918bb53dd4a3b6811e1ae3ca181359a0da1544fa86463ee4f181`.
Thirty Python tests pass in3.95s. Harness build46761 succeeds14.41s.
Full native78112 CLOSED0:88 clean passes,21.010162s, explicit temporal breaking
mode1. Actual GPU completes the entire interval in2 accepted trials,0 errors,
remaining time0 and exact end.033333335071802139s. Split and batched graphs and
indirect/direct recurrence preserve state, compensated clock, summary,
diagnostics and boundary ledger bit-exactly. Maximum absolute state error
9.536743164e-7; h/hu/hv relative errors5.529277e-8/5.193387e-8/5.497928e-8 against
the independent double-storage control. Different accepted step count is allowed
by the existing state-error gates, not misreported as identical trajectory.
Water change-.0678304189976m3 plus outward.0678290765584m3 leaves float-storage
balance-1.34243922555e-6m3; reported, not repaired or called double-precision
conservation. Foam remains exactly0 because these source observations have0.

Final-harness compatibility run29687 CLOSED0: the original version1 nonbreaking
temporal fixture also passes cleanly (one focused test,0.233352s). Mode selection
has not silently changed the original fixture's model.

Shader SHA256 `3141791c85d5ee4ee258160f5637bb2ef6efe2d3a1f97e054f92fdfb2d9644dc`.
Clock/step shader SHA256 `5b5e11ec8ac95e88ff7c498d7a5260c65ae29fb2bebc26ab0d67b34760db6975`.
WaterDetail DLL SHA256 `6e4a622ce22cf4813308d4f16c57b850667f3db0b4789d066f591e378653c36e`.

This turn is progress, not completed South Fork: the missing GPU classification
and full-stage/open-interval coupling now exist and are verified on actual
source inputs. Next persistent interval ownership must retain evolved interior
state, observed boundary brackets and accepted ledgers across updates and
moving windows without resets, dropped time or extrapolation. Long-time
stability, model/reference qualification, foam entrainment and shared playable
publication remain necessary; the normal legacy perturbation's negative-depth
observation must not become a hidden state-clipping initialization path.

Both YouTube pages were retried via web during this turn and still return cache
misses. Neither video was viewed; no fresh browser/kernel retry or remote media
download occurred. Saved normal materialE0C961..., mapDB3080... and save181D1E...
are unchanged. Latest FPS remains18.899245; no new ordinary capture or native
performance qualification is inferred from these tests. Full terrain, crew,
remaining rivers, normalization, release checks and final commit remain open.
