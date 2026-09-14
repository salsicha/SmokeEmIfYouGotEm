# Original-MC reconstruction control — September 14 UTC

The previous goal turn made progress by locating the non-self-monotone
survival-ratio reconstruction and its stiff local hydro mode. This continuation
implements/tests a replacement control without that extra shoreline operation.
All terrain, water, later-river, crew, platform, release and final-commit work
remains in scope. Desktop30FPS/p9533.333ms and physics120Hz are unchanged.

## What changed, and what did not

Explicit CPU `shoreline_limiter='unscaled'` preserves the original MC depth,
surface and velocity polynomials. It applies the same hydrostatic face reduction,
momentum-conserving velocity reconstruction, shared mass/foam flux, centered bed
source, breaking closure, pressure solver and RK2/CFL rules. It does not apply
either the binary shoreline flattening or the continuous survival-ratio scaling.
Default remains binary. No source sample, conserved average, geometry resolution,
pressure tolerance, accuracy gate, source time or timestep is replaced.

The existing centered source and reconstruction in depth/surface are consistent
with the classical second-order hydrostatic strategy; that strategy explicitly
allows derived subcell bed polynomials to vary with water even though supplied
bed averages are fixed. Requiring a water-independent *subcell polynomial* is
therefore not necessary to preserve the captured terrain samples. The project's
wet stencil, momentum reconstruction and coupled pressure remain separately
qualified implementation choices, not a claim that every theorem for the paper
automatically applies. See [Audusse et al., section3](https://publications.imp.fu-berlin.de/478/1/file_2004_siam.pdf).

## Actual failing inputs: local stiffness removed

Source: `tmp/south-fork-continuous-owner-history-v2-20260914.json`, SHA256
`03978a0630ec7db6f29f966303bb586203ce8752468cedfef0ad67dd2096ae5e`.
Trace: `tmp/south-fork-continuous-first-divergence-v1-20260914.json/.bin`.
Independent CPU stage archive:
`tmp/south-fork-continuous-first-control-states-v1-20260914.npz`, SHA256
`09b682f7b6a09b130001546992c00a118f28d8e2c7faf33316b549d4c9e071cc`.

`tmp/south-fork-unscaled-hydro-response-v1-20260914.json` evaluates BOTH nearby
trial10 second-stage states using unscaled reconstruction. It explicitly labels
the captured/evaluated models and leaves native parity unavailable, because the
old capture's native arithmetic used the different continuous model.

- Nearby-state maximum hydro difference decreases0.035251847378→0.000517099637.
- Owning depth derivatives at y100/x19 are[2,0], rather than[137.02275,-135.02275].
  Three perturbation sizes agree; neighboring hu-rate sensitivity decreases in
  magnitude from2314.29 to22.93.
- Radius1 frozen local hydro block most negative eigenvalue is-22.3331752/s,
  versus-1283.7147145/s. All decaying modes have RK2 gain below1 at the unchanged
  recorded0.008333333768s; largest gain0.97653259.

These are local sensitivity/stiffness checks, not a global nonlinear stability
proof or complete-history accuracy result.

## Independent paired evolution through the failing interval

CPU98791 completes exit0:
`tmp/south-fork-unscaled-first-interval-pair-v1-20260914.json`.
Two independent unscaled controls begin at the actual independently evolved CPU
and represented GPU starts of interval13. Each then retains its own interior,
using unchanged observed boundaries, default CPU timestep, nonlinear pressure
and breaking through1.533333413303→1.666666753590s. No intermediate resets.

Initial difference5.48327610872e-6 decreases to4.44328695348e-6; zero cells exceed
1e-4. Both take17 steps/no rejects. Mass-balance errors are-2.6290e-13 and
1.3323e-13m3, worst pressure residual approximately7.6129e-8. This replaces the
local continuous-model burst, but is NOT a GPU comparison or original-start
full-history qualification. The continuous full-history FAIL remains preserved.

## Physical and native transport checks

Existing physical tests now also exercise unscaled reconstruction: exact rough
closed/periodic lakes with emergent islands and shifted datum; thin-film gravity
down to2^-300 depth; dry-bed dam break; conservation; second-order finite-amplitude
wave accuracy and smooth variable-bed consistency. CPU48847:43 pass27.85s.
Additional actual-operator checks prove no second polynomial pass, unchanged
inputs/default, nonnegative owning faces and preserved average depth;1024 wet
stencils have owning-depth self derivatives in[0,2]. Combined baseline/provenance/
lake/30FPS suite passes58 in6.57s. Suites overlap; do not sum them as unique tests.

Native transport adds `bUnscaledShoreline=false`, mutually exclusive with the
existing continuous flag. Unscaled phase2 only copies raw polynomials and clears
the flattening mask; no survival-ratio work or extra factor buffer is needed.
Native rejection test covers selecting both models simultaneously. The evolution
step, persistent owner and normal playable callers do NOT select this model yet.

Build62448 succeeds76.29s. Native23903 completes one clean test0.6284s:
`tmp/south-fork-unscaled-transport-native-v1-20260914/index.json/.log`.
Fixture `tmp/south-fork-unscaled-transport-fixtures-v1-20260914.bin`, SHA256
`4c81f24988e743529033eae53cb74252c49040ccf3e2c52d5f6686d994702d9e`, contains
18 cases: original eight, eight rough lakes, both actual first-failure stage
crops. All eight rough native hydro rates and coupled pressure forces are
EXACTLY zero. Actual stage crops pass unchanged gates: hydro max errors
2.28881836e-5/1.54972076e-5 and coupled-force relative errors3.07e-7/3.33e-7.
This includes the GPU transport's OWN graph/rate as pressure inputs, not uploaded
CPU intermediates. Fixture v3 explicitly identifies the distinct model; v1/v2
and default callers retain previous behavior.

Full default native regression76759 completes exit0:126 clean tests plus one
descriptor-warning pass, zero failures,67.6531s. Report:
`tmp/south-fork-unscaled-default-native-v1-20260914/index.json/.log`.
Original binary-model history replay remains final-state-byte-exact. Retained
default capture SHA256 remains
`5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`.
All local build/test/diagnostic jobs are terminal.

Cook74818/PID41820 remains verified LIVE past6904s. Both complete6900s/local18000
state and artificial-bank audits pass: all5,382,400 cells finite,86,720 artificial
bank cells exactly dry. Outlet112.824760954 versus inlet45.306954547m3/s is still
settling; no source promotion. Next complete7000s/local20000 needs BOTH audits.
The cook was not paused or restarted this continuation.

## Required next steps

Carry immutable unscaled model identity through BOTH RK2 stages, bounded advance,
interval/move ownership and source-exact native replay; test attempts to switch
models. Then run the complete independent original-start history and validate
nonlinear physical behavior, no thin-state stalls, warm cost and moving-window
capacity before normal frame/contact integration. No smaller time step, blanket
flattening, state reset or threshold relaxation is accepted as the fix.

Actual playable breaking/froth, terrain/collision integration and30FPS still need
validation. No screenshot or new gameplay FPS result this continuation. The
previous18.899245FPS/p9570.33ms measurement still fails30FPS. Reference videos
were not newly accessed here; no inferred observation of footage is claimed.
