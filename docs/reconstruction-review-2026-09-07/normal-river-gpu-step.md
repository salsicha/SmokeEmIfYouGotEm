# Transactional GPU water trial — September 13

Supporting implementation, not playable-scene acceptance. South Fork remains
the first unfinished river. The 30 FPS desktop target and all visual, physical,
terrain, crew, later-river and release requirements remain unchanged.

## Implemented

`RaftSimTryTotalDepthStepGPU` now performs one SSP-RK2 trial on total state
(h,hu,hv,foam). Each stage computes its own native finite-volume rate, wet graph,
fixed bed slope and nonlinear pressure. The fraction callback receives the
actual stage state and transport outputs separately; a future state-dependent
breaking mask must not be frozen across stages. No CPU readback is used.

The trial qualifies the true pressure residual independently for both rational
poles at relative tolerance 2e-5, checks both stages' CFL and finite/nonnegative
candidate state, and either publishes the candidate or preserves the original
state bit for bit. It does not clip depth, momentum or velocity. Maximum step
1/120 s and minimum retry 1e-9 s retain the CPU policy; an exact final remainder
can be smaller. Later rejection halves the proposed trial; first-stage errors
and exhausted/unrepresentable progress stop it. Callers must inspect flags,
enforce their total trial budget and publish state/progress together only after
the completed graph. This is a single-trial API, not a complete retry driver.

Time is a compensated float hi/lo pair. Rejection preserves both clock words
and remaining time exactly. Tests start at 1048576 s, where float-only addition
would lose the 0.001 s step. Exact tiny final remainder, zero remaining time,
maximum step, invalid/overflowing clock and retry exhaustion are covered.

`RaftSimCheckPressureResidualGPU` reduces per-pole maxima, then scaled squared
norms. Integer max ordering and exponent/mantissa normalization preserve even
subnormal SRV inputs before division, avoiding a false zero-residual pass from
GPU flush-to-zero. Zero RHS requires exactly zero residual. NaN/Inf count as
errors; the caller also combines transport, pressure and solver diagnostics.
Eight native cases cover ordinary, 1e-30, 1e30 and 1e-40 scales, exact zero,
nonzero subnormal residual with zero RHS, and nonfinite inputs. This does not
qualify arbitrary subnormal state evolution.

## Pressure symmetry correction

Initial native trials 83841 and 45879 failed the one-dimensional dam cases:
tiny false transverse momentum, with relative errors amplified by an almost
zero CPU reference. No tolerance was relaxed. Equal depth weights used
`sqrt(.5)*sqrt(.5)` instead of the exact equal-weight identity .5; separately,
contracted multiply-adds could leave a residue for equal opposing products.

CPU and both GPU pressure coefficient stencils now use the equal-weight
identity when the weights match, retaining square roots for unequal weights.
Precise transpose/RHS products preserve cancellation. This is the same
operator, with an exact one-dimensional nullspace. Both CPU and GPU dam cases
now require exactly zero transverse momentum; CPU rows must also match exactly.
Native 99131 passed both new test filters after the fix. Final strengthened
assertion build 32793 succeeded in 13.95 s; final suite evidence follows below.

## Fixtures and scope

`physics/scripts/export_total_depth_step_fixtures.py` quantizes source inputs to
float32, computes independent CPU double rates and pressure, rounds the Euler
stage to float32, then reevaluates before the RK combination. Nine 0.001 s cases
cover dry/resting water, MC and first-order dam breaks, thin water, moving and
periodic flow, a single column, and captured 128x128 South Fork. Native gates
remain relative 2e-5 and absolute 1e-4 per state component, exact dry/lake state,
exact dam transverse momentum and unchanged foam. Nine additional control/
fault cases exercise first/second-stage failure, zero/tiny/max time, clock
overflow, second-stage CFL rejection and negative candidate rejection. Fault
buffer mutations occur only inside the test callback, not production options.

Current step fixture `tmp/south-fork-total-step-fixtures-v2-20260913.bin`:
SHA256 `69d798178845b608e1f7486ee06daa2f550017c8c4a4a8243bd622f0d07edf3f`.
v1 and failed native logs remain as history. The suite requires explicit
`-RaftSimStepFixture`, `-RaftSimTransportFixture` and
`-RaftSimNonlinearPressureFixture` absolute paths; the pressure/transport
component fixtures remain their separately recorded historical references.
The selected 14-file CPU suite (session 86258) passed 137 tests in 29.72 s.

Final actual D3D12 suite 89225 CLOSED exit0: 71 passes, zero warnings, failures
or unrun tests, 17.858295 s. Report:
`unreal/Saved/RaftSimValidation/south-fork-total-step-regressions-v1-20260913/index.json`.
Both dam fixtures have exactly zero transverse momentum. Captured step
component relative errors are 4.46020e-8, 4.05737e-8 and 4.25443e-8. Existing
career/catalog migration and rendered/contact-support regressions also pass;
this does not constitute actual playable animation or visual acceptance.

Final water-detail DLL SHA256:
`0e2103cb88efb48db66f51467a4f97b9fded674c3f715ccd2928d77be1d4ff9c`.
Shader SHA256s (residual, step, pressure, acceleration respectively):

- `d0b2784b9958050a3bad10eedca4e7a0a494a46e5b741524fe61be20cefc40fd`
- `b8b4ac388bf6b0a81b35ddde7ab8d91e9069a92a09bec72373a2de807b377f5d`
- `4dfabd661059c17b18bce8ff8111d544112c137174530d9ca1bef33fc9669cd3`
- `e33448e9fd15f8cc914062891b1f5cc7aaa28f40219ec3eeb28fc67f7194845d`

Current CPU pressure SHA256:
`4551f5c7a9b34e25f348ef26b3bed89b693003ba251987f1f8cbab605c8f8e21`.
Prior 20 s replay and cost captures predate this arithmetic correction. They
are not fresh evolution/performance evidence for the new implementation.

## Remaining integration

Foam is held unchanged: no transport or production yet. Physical open-river
boundaries, mean/window exchange, runtime bed uploads, GPU breaking detection,
bounded retry ownership and a shared completed render/contact frame remain
required. The new total-depth path is not enabled in normal play. Existing
finite-depth pressure remains enabled and the known-broken strain experiment
stays off. No new game motion, reference playback or FPS acceptance is claimed;
latest ordinary-play measurement remains 21.571211 FPS / p95 52.6052 ms, below
the requested 30 FPS / 33.333 ms target. Whole-step cost is not qualified.
Map, water material and career save hashes were rechecked and remain unchanged.

Cook 96057/PID29104 continues without restart. Both 3400 s / local 28000 audits
passed, all 86,720 artificial-face cells dry, but discharge still indicates
settling. Latest observed progress was 3434.5 s; next complete 3500 s / local
30000 snapshot needs both independent audits. Runtime field remains 600 s.
