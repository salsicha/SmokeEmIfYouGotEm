# Source activation and successive-state failures

September 14, 2026. **Research-only progress; actual finite-time water still fails.**

The preceding source-region work supplied internal faces but no water transfer
onto unowned terrain. Commit `ca59414cb` added that transfer. This review records
the actual activation evidence, subsequent-step failures, and the conservative
velocity-exchange correction. None changes the normal playable solver or proves
breaking, froth, visual realism, or the 30 FPS target.

## Source-supported activation

One-sided nondispersive dry-bed Riemann flux integrates each original linear
source edge. The dry side has exactly zero water, not an artificial stage.
Four-point Gauss integration in wave speed integrates each branch polynomial.
Equal and opposite volume and XY momentum transfers identify receiving support
by `(parent cell, original source triangle)`; disconnected water is not pooled.

The original Cartesian source-face cuts now use exact rational intersections of
the represented mesh and box coordinates, followed by one float conversion.
This removes independently rounded overlapping trace fragments without welding,
moving terrain, dropping positive intervals, or weakening ownership checks.
The original snapshot has 1,812 shared pressure subsegments and 248 wall pieces.

Updated support may release only zero-water source faces or split into exact
wet connected components. Split volumes come from original triangle integrals;
each component inherits its input region's velocity. Remapping errors are
measured, never normalized away. Both base and original two-pole finite energy
are checked after the transition. A steep-bed test retains rejection when base
energy falls but full-model energy rises.

On the actual 600-second South Fork snapshot, 56 positive front entries feed 54
new source regions across 18 parent cells. All five independent probes from the
same original snapshot (20 ms through 1 microsecond) pass their finite budgets.
The 20 ms probe changes 258 regions to 313, including one wet-support split.
Its mass error is zero, momentum balance error is 2.3271e-13, base energy change
is -72.78697913, and full energy change is -115.12344843 in model units. Those
energy losses are **not measured physical breaking dissipation**.

Independent probes are not a history. The new successive-state audit advances
only an actually returned candidate state and stops on its first rejection;
there is no retry, automatic timestep reduction, clipping, or state repair.
At the second 20 ms explicit step, **11 regions would become negative**. Some
have incoming as well as outgoing water. Parent 204 / source 597140 would change
from 0.0013277681 to -0.0114449642 cubic metres. The reported net-only volume
limit is 0.0020790666 seconds, not a production stability bound.

Report: `tmp/south-fork-source-history-explicit-v3-20260914.json`, exit 1.
SHA256: `caa603912981c10fedf792e38ecf59c2f35640b2e795e7844d3a31530d140a3b`.
This report predates the velocity-exchange correction below; its source hashes
identify that version explicitly.

## Conservative coupled transfer and its first failure

The optional `coupled-frozen` path builds a conservative donor generator `G`
from the same actual face transfers. Its off-diagonal entries are nonnegative
and its columns sum to zero. It solves `(I - dt G) V_new = V_old`, including
initially zero-volume receiving regions, without capping a face or adding water.

The first version used the same matrix for both momenta and left the residual
momentum rate explicit. Positive mass alone was insufficient: zero-net-mass
faces can exchange momentum, so their stiff velocity diffusion remained in
that explicit residual. On the actual history, local speeds reached 755 m/s at
step 6 and 2.098 million m/s at step 7 while global energy still decreased.
Step 8 finally failed the unchanged finite energy gate. The earlier candidate
budget passes are therefore **not physically acceptable states**.

Report: `tmp/south-fork-source-history-coupled-v3-20260914.json`, exit 1.
SHA256: `04777eb8cdcf90ed0fd5e52f05f4b92c22dd08536b19f681082890819c414b50`.

## Velocity-exchange correction

For an interior face the original momentum flux is decomposed as
`F_mass * u_upwind + D * (u_left - u_right) + pressure * normal`.
Positive `D` contributes a conservative symmetric velocity-exchange graph `K`.
Any negative exchange and all pressure/bed terms remain in the explicit
remainder; no original instantaneous force is discarded or replaced.

With `R = Pdot - G P_old - K u_old`, the corrected solve is
`[(I - dt G) diag(V_new) - dt K] u_new = P_old + dt R`.
The exchange acts on **new** velocities and **new** volumes, so constant
velocity is preserved even while mass moves. Both XY components are retained.
The original infinitesimal face rates are verified on dry-front and moving
wet/wet fixtures. This remains a first-order frozen-coefficient research update,
not the complete rational transport or a qualified pressure integrator.

An independent two-region exchange case first failed the required nonincreasing
energy gate: with rate 1000/s and dt 0.02, the old explicit remainder multiplied
velocity by -39. The corrected result is the independently derived backward
Euler factor 1/41. The energy assertion was preserved, not relaxed or replaced
by an assertion approving the previous unstable result.

## Actual corrected history: still rejected

Report: `tmp/south-fork-source-history-exchange-v1-20260914.json`, exit 1.
SHA256: `21814769379595b97771f06f01b49279d33b19c415f25b1586b087e0a19cbb66`.

The requested 20-step, 0.4-second run does **not** complete. The first ten 20 ms
steps retain maximum speeds between 5.33 and 4.50 m/s, rather than the previous
million-fold blow-up. At step 11, parent 159 / source 600739 reaches 157.7059 m/s
with only 5.2623e-18 cubic metres. The smallest other region contains 1.9996e-51
cubic metres. Step 12 fails the coupled true-residual gate. The audit records
11 finite-budget candidate passes / 0.22 seconds, **not an accepted physical
history**. Global energy still decreasing at step 11 does not establish local
velocity correctness.

Across those 11 candidates, maximum per-step mass error is 1.1369e-13,
momentum boundary/bed balance error is 1.9718e-12, and original pressure residual
is 4.1807e-16. None excuses the local instability or the failed final solve.
Original pressure poles, 40-CG budget, and acceptance thresholds are unchanged.

Next isolate the remaining tiny-region force/conditioning failure using local
momentum budgets and a stable coupled pressure/velocity solve. Do not delete
tiny water, lower the timestep until a short report turns green, or interpret
global dissipation as physical breaking. Complete full rational auxiliary
transport and exact-terrain bed-force coupling, drying/topology behavior,
finite-time/open-boundary/refinement qualification, and native shared-surface
integration before considering promotion.

All 464 protected source/capture/map/profile/actor hashes were unchanged in the
preservation check. Original mixed provenance is retained: submerged priors and
inferred connecting flanks are not measured bathymetry. No normal map, native
solver, scenario, water state, render quality, or performance setting changed.
Troublemaker remains a rapid inside South Fork, not a standalone menu scenario.

## Verification and reproduction

Final subcell/triangle suite: **162 passed** in 12.60 seconds, report
`tmp/subcell-source-history-tests-v6-20260914.xml`. The independent stiff-exchange
energy gate was first recorded failing in `tests-v4`, then passed after the
implicit exchange correction. Constant velocity under changing volume, original
wet/wet and dry-front rate limits, and stop-without-retry behavior are covered.

Retained original paired-base stress, conservative stress, and constant-velocity
files: **25 passed, 12 failed** in 7.75 seconds, exit 1, report
`tmp/subcell-source-history-retained-v1-20260914.xml`. The same eight nonlinear
energy and four legacy constant-velocity failures remain unwaived. This is the
three-file retained selection, not the larger prior 34-pass selection.

The final actual report's 34 source hashes were rechecked against the current
files, with no mismatch. Generated JSON/XML remains ignored local evidence;
this document records results and hashes. Reproduce the actual failed run with
the local NumPy dependencies available to the Python environment:

```powershell
python -B physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/source-history-new-run.json --pool-history-steps 20 --pool-history-scheme coupled-frozen
```

The report path must not already exist. Exit 1 is the correct result for the
failed requested history; do not replace it with the first five passing steps.

Full South Fork visual/30 FPS acceptance, then Colorado, Pacuare and Futaleufu,
all-scene Chilko/Zambezi reviews, crew realism/fit/animation, normalization,
outstanding regressions and release checks remain open. Full goal active.
