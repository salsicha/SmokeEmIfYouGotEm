# First full-history divergence: shoreline reconstruction — September 14 UTC

Desktop remains 30 FPS / p95 33.333 ms, physics 120 Hz. No visual-quality,
geometry, source, CFL, pressure, memory or accuracy gate is relaxed. The new
solver remains diagnostic; normal playable water and the full project are NOT
qualified. The GPU candidate below is opt-in; no normal-map promotion or commit.

## Latest: opt-in GPU transport and both RK2 stages

The continuous reconstruction now has native GPU component coverage. The new
`RaftSimScaledHydrostatic.ush` uses portable 18-limb arithmetic at quantum2^-300
for represented MC-slope/factor products. The same factor is carried through
depth and surface offsets, exact cancellation fallback, momentum and source
terms. Transport and both transactional RK2 stages accept an optional flag,
false by default. Bounded advance and the persistent owner do not yet expose
this choice; ordinary playable water is unchanged.

Evidence retained under `tmp/` (September14 UTC):

- `south-fork-scaled-polynomial-fixtures-v1-20260914.bin`:4317 independent
  rational cases; SHA256
  `ac2d927e45fbb47bf1b25c1e5d24717b6e434f68548583cc04e4e803045c7c9f`.
  Native report `south-fork-scaled-polynomial-native-v1-20260914/index.json`
  passes cleanly, including extreme factors and positive values rounding to zero.
- `south-fork-continuous-transport-fixtures-v3-20260914.bin`:ten cases,
  including closed-boundary11x11 crops of BOTH actual interval10/trial15 stages.
  SHA256 `4011e25f3368a4f90be48be2e24812881c22e67eb353b0a18ce59f5139641626`.
  Native `south-fork-continuous-transport-native-v2-20260914/index.json`
  passes cleanly with unchanged gates and no graph mismatches. These crops
  are operator tests, not the original live boundary/history evolution.
- The earlier v2 fixture/native-v1 run FAILED: the CPU lake reference had a
  1.58831277e-16 residual while GPU returned exact zero. The independent rational
  reference now refines near-equal reduced faces as well as near-zero faces
  when factors are used. It evaluates the actual polynomial; it does not force
  equal faces, floor state or change tolerances. Failed artifacts are preserved.
- `south-fork-continuous-step-fixtures-v1-20260914.bin`, SHA256
  `161fcf7f9fbac0b800cd30e5d0dc1611f4cb0ae3bff031699e1e99ecea54db25`:
  eleven base cases plus nine native transaction/clock fault cases. Combined
  report `south-fork-continuous-step-native-v1-20260914/index.json` passes all
  three tests cleanly in0.842977s. Includes both stages, conservative foam,
  pressure residuals, accepted/rejected state and clocks; not full live breaking.
- Unchanged-default native report
  `south-fork-continuous-default-native-v1-20260914/index.json`:123 clean,
  one passing WITH WARNING, zero failures,45.226879s. The warning is an engine
  connectivity probe timeout to `https://www.google.com/generate_204` during
  TotalDepthAdvanceGPU.Case0, not a numerical failure. Retained capture SHA256
  `5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`
  is identical to the original binary-control capture.
- Focused Python runs passed56,116 and117 tests; the step-specific run passed
  seven tests. These overlapping suites are not additive unique-test counts.

Next: carry an immutable reconstruction choice through bounded advance and
the persistent owner, then independently evolve the complete original moving
history from its original start. Do not initialize the reference from GPU
interior checkpoints or switch models mid-history. Broader variable-bed lake,
physical/stability and warmed-cost checks remain, followed by normal playable
terrain/waves/froth/contact captures against the30FPS target. No performance
qualification follows from these component tests.

Both6500s/local10000 full-river snapshot and artificial-bank audits now PASS:
`south-fork-expanded-6500s-state-v1-20260914.json` and
`south-fork-expanded-6500s-banks-v1-20260914.json`. All5,382,400 cells are finite;
86,720 artificial-bank cells are exactly dry. Outflow121.7061 versus
inflow45.3070m3/s means the source is still settling. Cook74818/PID41820 remains
live without restart. Next COMPLETE6600s/local12000 requires BOTH audits;
no runtime source promotion.

The sections below preserve the earlier CPU diagnosis and implementation plan.

## Complete endpoint history and exact first-failure capture

CPU endpoint job18242 exits0 with a valid FAILED accuracy report:
`tmp/south-fork-qualified-range-endpoint-history-v1-20260914.json`.
All72 endpoints were visited and saved in
`tmp/south-fork-qualified-range-endpoint-cpu-v1-20260914.npz`, SHA256
`1c26369a63fa982a760452b3d0cd527385bb4ba05ef1ab21218c115dd9d9e7d3`.
This is the independent default-timestep history, never refreshed from GPU
interior states. It reproduces the prior final error0.004130154590943097 and
1306 cells over1e-4. Source remains
`tmp/south-fork-qualified-range-owner-v1-20260914.json`, SHA256
`bf20b0b6c467b78d5d1b02a7174f502e1de3cba89996ee7f3b32cf0dfe5736ec`.

At1.1333333924412727s error is6.13330129262124e-6, zero failing cells.
At1.2666667327284813s it jumps to0.00931952188605134 in five cells, before
either window move. Error subsequently subsides before later bursts; this
is not a monotone accumulation or a transfer-only fault.

Native first-failure trace24361 exits0, one pass WITH descriptor-cache warning,
27.113363266s. Prefix `tmp/south-fork-qualified-range-first-divergence-v2-20260914`:
16 trials at interval10, both stages, all1080 original physical trials/two moves
still replayed; completed and final-state-byte-exact to live. Trace SHA256
`619c6fc49bd80547a082025d55b35bed140e9cf6969ab987f842c529ec036672`, binary
`2d8a6aede680d67eb69deb09e18e2dad3bd78037e8b5082b32fe9abc95d0a041`.
Earlier19883 exits1 before evolution because PowerShell split unquoted decimal
arguments. Quoting the WHOLE capture-begin/end arguments fixes invocation;
the failed log is preserved, and neither times nor gates were changed.

## Localize the discontinuity, not another floating-point implementation error

An isolated GPU-initialized interval control48511 passes locally, maximum
2.075742305e-6,17 CPU steps/no rejects. That reset is diagnostic only and does
not qualify history. New `--initial-checkpoints` instead validates source SHA,
exact native time/origin, unique endpoint, shape/dtype/finite/wet-state validity
and starts from the independently evolved CPU checkpoint. Retaining this control
through recorded contiguous dt is also explicitly diagnostic, not default-dt
history qualification.

Recorded-step audits54056 and70372 both exit0. Artifact prefix
`tmp/south-fork-first-divergence-full-control-v1/v2-20260914`:
trial15, second stage, input/Euler error stays around7.1e-6 but final error is
0.009319518606. Breaking fraction error is7.5547e-6 with zero graph mismatches.
The hydro rate differs2.2317358836, pressure force only0.0555667409. Pressure
residuals remain small. Same-input operator audit62018 exits0 with maximum
hydro error6.03896e-5 and pressure-force error1.65577e-5 over all32 stages.
This separates state sensitivity from an incorrect same-input GPU operator.

`tmp/south-fork-first-divergence-shoreline-v1-20260914.json` uses rational face
and slope decisions on BOTH actual nearby states. The decisive y90/x42,
axis0 cell has:

| Quantity | Independent CPU state | Represented GPU state |
| --- | ---: | ---: |
| Cell depth |0.20644867930234795 |0.20644834637641907 |
| Raw depth slope |-0.24292638369659172 |-0.24292632099241018 |
| Raw surface slope |0 |0 |
| Positive hydrostatic face |2.693317819051251e-8 |0 |
| Discard all slopes |false |true |
| Independent hydro hu rate |0.4138717040 |-1.8178639032 |

Both face decisions are correct for their represented inputs. The finite jump
comes from discarding an entire nonzero polynomial when a face crosses zero.
Other differing dry flags occur at vanishing depths far away; they do not explain
the worst-cell momentum jump. No epsilon, shared decision, CPU float quantization,
state repair or history reset is an acceptable substitute for fixing the rule.

## Continuous CPU candidate and bounded validation

The candidate takes the minimum fraction of owning-polynomial face depth that
survives raw hydrostatic reduction, bounded geometrically to[0,1]. It multiplies
depth, free-surface and velocity slopes by this factor, then reconstructs ONCE
from those scaled polynomials. This is a convex blend toward the constant cell
polynomial. Original conserved cell averages, source bed samples, prescribed
boundaries, physical bed derivative, momentum-balanced face construction and
hydrostatic source cancellation are preserved. An unblocked uniform film keeps
factor1 even at tiny positive depth; approaching a blocked face sends factor
continuously to0. There is no absolute depth cutoff or recursive flattening.
The rational cancellation fallback now accepts the same represented factor;
it must not silently restore the unscaled MC polynomial.

Convex blending to avoid a sharp reconstruction switch has a primary-literature
precedent in [Skevington's reconstruction paper](https://arxiv.org/abs/2106.11273).
This particular hydrostatic survival-fraction limiter is a project-specific
candidate, NOT that paper's scheme or its proven self-monotonicity result.
The optional Python `shoreline_limiter='continuous'` leaves the existing binary
default and GPU untouched. Remaining physical/stability questions must be tested,
not assumed away from a passing nearby-state comparison.

`tmp/south-fork-first-divergence-shoreline-v2-20260914.json`:
same two stage inputs, binary rate difference2.23173560724; continuous candidate
9.10591698675e-5. This is CPU-versus-CPU sensitivity, not a GPU pass.

Paired complete interval2384 exits0:
`tmp/south-fork-first-divergence-reconstruction-pair-v1-20260914.json`.
Both initial states independently evolve with original boundaries, pressure,
breaking, default dt and40-iteration solves. Four runs each take17 steps/no
rejections over0.13333334028720856s. Initial difference6.1333e-6:

- Binary rule: final difference0.0093196673102, five cells over1e-4.
- Continuous candidate: final difference7.18223402396e-6, zero over1e-4.
- Maximum absolute mass-balance error across all four runs4.42313e-13m3.
- The candidate changes the numerical trajectory; no claim that agreement alone
  proves physical accuracy, full-history acceptance or scene integration.

105 focused Python checks pass in9.28s, including existing source/history and
30FPS tests. Candidate checks cover unchanged cell mass/momentum and neighboring
velocity bounds, exact scaled-polynomial fallback, no mutation/default change,
resting lake with emergent banks, dry-bed dam wetting/conservation, gravity in
uniform films down to2^-300m, second-order finite-amplitude steepening, and
second-order variable-bed differential consistency. Tolerances match the existing
wave/mass/balance requirements; no test substitutes for final game validation.

Default-mode regression62618 exits0:
`tmp/south-fork-first-divergence-default-regression-v1-20260914.json`.
All16 recorded-step results (including both hydro/pressure comparisons, pressure
statistics and final values) are exactly equal to the pre-candidate v2 audit.
Adding the optional reconstruction has not silently altered the binary control.

## Next real implementation work

Port the candidate to GPU with opt-in verification before changing defaults.
The current10-limb hydrostatic accumulator has quantum2^-160, which is sufficient
for the original affine MC polynomial but NOT arbitrary FP32 factor products.
Do not multiply a recovered slope by the factor and then reconstruct from the
unscaled exact fallback. The factor must be represented consistently in BOTH
depth/free-surface offsets, exact fallback, momentum faces and source terms.
Qualify extreme factors, cancellation, original fixtures, actual captured stages,
both RK2 stages and full original moving history before promotion. Then repeat
warmed cost/30FPS checks and normal playable terrain/waves/froth/contact capture.
All later rivers, crew, platforms, regressions and final project commit remain.

Cook74818/PID41820 was re-polled and independently verified live at6469s;
same6000→8000s continuation, no restart. BOTH6400s audits already passed,
still unsettled. Next COMPLETE6500s/local10000 requires both snapshot and
artificial-bank audits. Runtime600s source and terrain provenance are unchanged.
