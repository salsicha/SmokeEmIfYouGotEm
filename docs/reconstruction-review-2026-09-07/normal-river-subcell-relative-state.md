# Coupled thin-cell transport and datum-relative hydraulic state

September 14, 2026. The previous goal turn made progress: commit `b72f5f600`
fixed the demonstrated counterflow timestep defect and preserved the remaining
drying-cell failure. This continuation identifies that failure more precisely,
tests a coupled transport control, and fixes a represented-volume/pressure
mismatch. **This remains offline research, not new playable water.**

## The limiting cell is not an isolated draining puddle

The instrumented explicit run reproduces the previous 100-step trajectory:
0.067411202 simulated seconds. The limiting cell is row 9, column 12 for 98
steps (row 8/column 13 and row 9/column 14 each limit one step). At the start
of step 100 it contains 2.896552096e-14 m3, with stage 8.233892621 m above the
rapid datum and minimum original terrain elevation 8.233870005 m. Its wet
area is 3.842108979e-9 m2 and velocity approximately (-0.161597, 0.160455) m/s.

It receives 5.125925550e-10 m3/s and sends out 7.664046381e-10 m3/s. Incoming
flow is therefore material to its balance; an isolated-puddle drain shortcut
would be wrong. The first limiting cell is actually filling, not draining:
the gross donor restriction cannot be inferred from net volume loss alone.

`subcell_drain_event.py` provides an independent exact **isolated** last-wet-
interval oracle. Original triangle wet area and outgoing face area give local
polynomials; integrating wet-area/outflow distinguishes finite extinction from
asymptotic drainage and trapped water. It never deletes a thin film using a
threshold. Analytic strip/corner, semigroup, trapped-pool and independent
quadrature checks pass. **It is not applied to the captured cell**, because the
no-inflow/frozen-outgoing-coefficient premises do not hold there.

Report: `tmp/south-fork-subcell-donor-local-100steps-v1-20260914.json`, SHA256
`bb3cadd1c918353dc7be606156ee3d98126c3d041f8c01724c25fb7f9a1016c6`.

## Coupled transport exposed a second, independent failure

`subcell_implicit_transport.py` assembles the same face-donor generator used by
the explicit mass and momentum rates. Off-diagonal transfers are nonnegative;
one shared interface adds and subtracts the same amount. Backward Euler applies
that same generator to volume and both momentum components. Reflecting walls
return mass and tangential momentum and reverse the normal momentum. Bed and
hydrostatic pressure remain explicit; this is not a fully implicit pressure
method or a replacement for the required reversible two-pole solver.

Independent tests match the existing semidiscrete mass/momentum rates and
their small-dt limit, conserve closed-patch mass and reproduce the analytic
two-cell implicit counterflow solution. An initial new test wrongly required
bitwise equality from a floating linear solve (6.776e-21 m3 difference); it now
checks relative error even at 5e-13 m3, with no absolute volume floor. Existing
physical gates and original rejected counterflow controls were not changed.

The first actual trial nevertheless failed. At step 16, a cell containing
3.717530275e-53 m3 was assigned absolute stage 8.233870004582506 m, one ULP
above its minimum. Its computed bed force then corresponded to roughly
1e-44 m3, not the stored volume. The absolute stage stopped changing as stored
volume fell further. Velocity rose to 2.1304e7 m/s, then approximately 1.089e51
m/s; step 19 was rejected with nonzero momentum in four exactly zero-volume
components. Mass positivity and negative global instantaneous energy rates
were plainly insufficient acceptance evidence.

This failure is retained in
`tmp/south-fork-subcell-implicit-frozen-100steps-v2-20260914.json`, SHA256
`cc815508c773d6b06240984565580ead596ffad8549bb531fb5841fa2b5a688c`.
It is not restarted as a supposedly unfinished successful history.

## Keep local water height separate from terrain elevation

`TriangleCellStorage.relative_stage_for_volume` now returns a height above the
original cell minimum. The minimum and the height stay separate through cell
storage, face wet-area/pressure integration, wave-speed evaluation, donor
transport and independently integrated bed force. Absolute stage is combined
only for human-readable diagnostics. No source vertex, terrain diagonal,
datum registration, water volume or momentum is adjusted to make them agree.

The inverse bracket also uses the exact leading power of the first wet
interval. Merely performing 128 bisections of a metre-sized interval cannot
represent arbitrarily small local height. Flat, edge and corner minima provide
linear, quadratic and cubic volume scales. Logarithms form the starting root
without intermediate underflow; bounded bisection then inverts the unchanged
volume function. Unrepresentable positive stages fail rather than becoming a
fabricated minimum depth.

Independent tests reproduce the old absolute-stage error and recover volumes
from 1e-300 to 2 m3 without an absolute tolerance floor. Bed force divided by
volume remains the exact plane-gradient acceleration. Shared face pressure and
the original donor generator retain their analytic thin-water behavior. The
legacy absolute-stage control remains available for comparisons; this research
patch requires `relative_stages=True` or the audit's `--relative-stages` flag.

## Actual 100-step result, still not a river acceptance test

Process 28747 completed exit 0 on the original captured 600-second atlas and
the same 256-cell footprint. All 100 steps take 0.02 s and advance **2 seconds**,
instead of stalling at 0.0674 s or exploding at 0.32 s. Maximum current after
any step is 5.292561899 m/s, ending at 1.442895070 m/s. Maximum closed-patch mass
error is 1.250555215e-12 m3. Four original stationary controls still pass their
unchanged bounds; worst mass-rate residual is 2.471925678e-14 m3/s and momentum
residual 7.105427358e-14 m4/s2.

The first exactly zero minimum cell volume appears at step 22 through floating
linear arithmetic; **the isolated finite-event oracle was not used**. No
post-solve clamp, rescale, depth cutoff or dry-momentum cleanup was applied.
This is not proof of exact front-extinction timing or refinement convergence.
These are reflecting walls around a small patch, not the full river's open
boundaries. The decline in current and growth of maximum cell depth must not
be presented as real-rapid settling or convincing breaking waves.

Report: `tmp/south-fork-subcell-implicit-relative-100steps-v1-20260914.json`,
SHA256 `cd070c7afa46ffea3221613154d629f431d0c60bac020bc1b1da288e9474fe99`.
The report's legacy scope sentence says "explicit"; its `stepper` field and
the protected source identify the actual **implicit-frozen** control.
Wall time is 228.416558 s in the dense Python reference. This is emphatically
not a native performance or 30 FPS result.

## Finite-step energy across the first dry transitions

A separate final-source run, process 48747, completed 40 steps / 0.8 s with
exact nondispersive mechanical energy evaluated before and after every update.
Total unit-density energy decreases from 11174.529673 to 10373.436629; each
step decreases it, by 9.463200 to 73.125087. The unchanged 1e-9 positive-increase
rejection bound passes. Maximum mass error is 5.684341886e-13 m3; maximum speed
after any step is 5.292561899 m/s, ending at 2.995864415 m/s. Four cells transition
to floating zero, beginning at step 22; all four have exactly zero momentum.
Again, this is floating arithmetic, not an exact drain-event timing proof.

Report: `tmp/south-fork-subcell-implicit-relative-energy-40steps-v1-20260914.json`,
SHA256 `68b5a087b51f36f80dca538819cc9c4bc4038eba330d349cb89735dbeeaeb311`.
All recorded input/source hashes are rechecked after the run. The scope text is
now corrected to refer to the recorded stepper. Reproduce with:

```text
python physics/scripts/audit_south_fork_subcell_transport.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report FRESH_PATH --steps 40 --stepper implicit-frozen --relative-stages --energy-audit
```

The preceding 20-step/0.4 s energy report is retained separately; neither energy
run proves the unaudited later 1.2 seconds of the original 100-step run. Global
energy loss also cannot by itself exclude local velocity failure, as the earlier
absolute-stage run demonstrated. A physical breaking closure, full two-pole
nonbreaking energy conservation and refinement still require their own gates.

## Remaining full scope

The final combined component/source run passes **45 tests**, including original
captured-registration and source-epoch controls. Run with physics/scripts,
physics/tests and unreal/Scripts on PYTHONPATH and NumPy available:

```text
python -m unittest test_triangle_cell_storage test_triangle_face_section test_subcell_geometry_patch test_subcell_implicit_transport test_subcell_mechanical_energy test_subcell_drain_event test_subcell_relative_stage test_captured_rock_vertex_registration test_carrier_source_epochs
```

The independent native expanded cook remains directly live on handle 84168,
observed beyond native 9906/local 10120. COMPLETE 9900/local 10000 passes BOTH
state and artificial-bank audits: 5,382,400 cells finite, 86,720 artificial-bank
cells exactly dry, maximum step conservation residual 1.412245743e-8 m3.
Outflow 102.916980 m3/s versus inflow 45.306955 m3/s is still unsettled.
Reports: `tmp/south-fork-expanded-9900s-{state,banks}-v1-20260914.json`.
Next COMPLETE 10000/local 12000 requires both audits. No restart/suspension.
The completed snapshot h/u/v hashes are:

```text
h 093b6a47949757e995776771a7e2970103b54873b0797f9bbb560a1c934ff3da
u f433e1f3965e0fbf9085bd56c69eddea79db767f6a08eb1141eb6e1eb2caef9b
v cfc043c3de3f6607030d0e883197886f3a836b076c06e2d6a8582b8f0b7e1364
```

All **464** protected source-capture, saved-map, profile, mesh and actor files
were freshly rehashed unchanged against the combined collision audit.

The nondispersive energy helper integrates squared depth over original
triangles using stable positive expansions, checked against independent
clipped-triangle quadrature and energy derivatives. It is separate from the
required two-pole physical energy; no successful base test supersedes the
previous 89 PASS / 29 FAIL coupled control set. The current component is still
first-order and dissipative. Full pressure/energy pairing, moving wet fronts,
internal-basin connectivity, open boundaries, refinement, native cost and
shared rendered/contact integration remain prerequisites to promotion.

Normal playable South Fork is still the delivery target. Latest actual visual
evidence remains unaccepted; 11.520818 FPS / p95 103.8838 ms still fails the
unchanged 30 FPS / p95 33.333333 ms requirement. There is no new game capture or
visible wave/froth improvement from this work. Then Colorado, Pacuare, Futaleufu
in order; remaining Chilko/Zambezi water, crew realism/fit/animation,
normalization, regressions and release checks. Troublemaker remains a rapid
within South Fork, never a standalone menu scenario. The full goal stays open.
