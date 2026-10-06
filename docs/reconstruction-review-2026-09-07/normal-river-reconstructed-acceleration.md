# Reconstructed acceleration and dry-row support — September 14 UTC

This turn made implementation progress, not playable acceptance. It located
the previously measured wet/dry kinematic jump, added a range-factored research
acceleration matrix and implemented its nonlinear pressure correction for a
stationary exact-dry set. The actual source still activates dry cells, so this
is NOT a completed original-history water model. No native solver, source
terrain, hydro transport, timestep, menu, pressure accuracy gate or physics
budget was changed.

## Locate the discontinuity before changing the equations

`tmp/south-fork-shared-bottom-dry-support-v1-20260914.json`
has SHA256 `7bcd72820929fe274ba53087b5aee0b012aec7f412142a2653368c798d540431`.
It preserves the same source, trace, binary and original wetting bracket as the
preceding reports. Session36505 EXITED1 after saving the unsupported mass
tangent, rather than turning the diagnostic into a pass.

At direction parameters1e-12,1e-20 and1e-28 seconds, the persistent raw D*u
change0.08469855809468334 is at the activating cell y123/x94. Already-wet-row
maximum changes are1.5706116962554972e-10,0,0; stationary dry rows remain zero.
The maximum change in h*D*u is9.8529379100043e-12,2.8670914993397734e-73 and
2.8670914993397736e-81. Thus the nonvanishing raw jump is localized to a cell
with vanishing column thickness in THIS source direction. This is not a theorem
for every wetting stencil, a valid D_t on the old dry row, or a license to drop
the original positive CPU mass rates. Frozen-pressure action still tends to
zero, as recorded previously.

The diagnostic now reports changes separately on already-wet, activating and
stationary-dry supports. Seven new tests cover that distinction, a simple
reproduction, source immutability, invalid directions and unrepresentable
positive-depth rejection. No cutoff, floor or native-rate substitution.

## Implemented normalized matrix

For the integrated/shared-bottom geometry with paired D and E, define H=diag(h)
and R=diag(sqrt(h)). The normalized acceleration unknown is x=R*a:

```
W = R (H D - 3/2 E) R^-1
V = R E R^-1
A = I + length * (W^T fraction W + 3/4 V^T fraction V)
```

`reconstructed_acceleration_system.py` assembles these coefficients directly
from the existing rounded geometry, combining coincident neighbors before
normalization. This matters on singleton and two-cell periodic axes. Exact
rational products followed by90-digit decimal square roots avoid forming an
overflowing h_i/h_j or underflowing h^(3/2) intermediate. A nonzero coefficient
outside final float storage is rejected, not silently zeroed. This is a slow
reference implementation, not an optimized native solver. It does not establish
range safety for all possible inputs to an entire future trajectory.

The same stored coefficients implement forward and transpose actions. The
preconditioner uses the actual diagonal and same-cell2x2 blocks, including
neighbor contributions. Exactly dry algebraic unknowns retain identity rows;
nonzero physical coefficients touching a dry unknown are rejected. The40-PCG-
iteration budget and recurrence are unchanged. Tests retain nonzero thin-film
coefficients through2^-1070, verify dense-matrix actions/blocks/solutions,
signed transposes, positive definiteness and explicit zero dispersion fractions.

## Nonlinear correction, with an explicit support restriction

`reconstructed_nonlinear_pressure.py` uses the actual supplied FV h_t and
momentum rate, original directional geometry derivative and BOTH D_t/E_t in
Q/C. On its currently supported stationary exact-dry set:

```
qbar = h*sqrt(h)*Q
cbar = sqrt(h)*C
base = (momentum_rate - u*h_t + h*Adv) / sqrt(h)
rhs = -length*(W^T*f*W*base + 3/4 V^T*f*V*base)
      +length*(W^T*f*(qbar+3/2*cbar) - 3/4 V^T*f*cbar)
A*correction = rhs
```

It constructs K*base directly rather than subtracting A*base-base. Reconstructed
pressure and bottom pressure are then applied using the SAME original D/E
force assembly. Rational poles retain the existing lengths and weights. No
velocity/acceleration division by h is introduced. The seven nonlinear tests
compare the fully wet flat-bed result to the old kinematic model, verify the
variable-bed material-pressure identities and force/correction balance, retain
zero-pressure stationary thin/dry lakes, and reject the actual type of dry
activation with its positive mass rate unchanged.

This module is NOT called by normal gameplay or the native water solver.
Dry activation remains explicitly unsupported. Prescribed pressure-boundary
lifts, a valid wetting-front forcing, original-start evolution, physical
pressure-column behavior, CPU/native agreement, stability and cost are still
required. A manufactured or stationary-set pass cannot replace those gates.

## Full captured-grid linear evidence

`tmp/south-fork-shared-bottom-acceleration-form-v1-20260914.json`
has SHA256 `49d8dc78d0815d08f9a5d10897def1464e0e793e0aa6e40f5b80bfd9cae534fd`.
Session38410 EXITED0. Each bracket side has16,384 scalar rows and32,768 vector
unknowns. Original velocity is ONLY a known TEST vector: rhs=A*sqrt(h)*u is
manufactured, then solved. It is NOT the nonlinear physical RHS.

The larger pole length0.4052787713439809 retains relative residuals about
5.54e-7 (diagonal) /5.55e-7 (block) at40 iterations, with maximum recovered
test-vector error about1.151e-5 /1.159e-5. The smaller pole length
0.03916567310046354 gives relative residuals about3.9e-16 and maximum test-
vector error below8.3e-15. Dry unknowns remain exactly zero. No iteration budget
or residual gate was relaxed, and these numbers are not physical acceptance.

Reference matrix construction takes4.98–5.27 seconds per pole; measured CPU
linear solves take49–109ms. These timings are NOT production GPU timings or a
30FPS/1.6ms-solver pass. Both original bracket sides and both preconditioners
are retained, including the non-roundoff larger-pole residual.

## Verification and remaining scope

The combined pressure, provenance, boundary and30FPS suite passes244 tests
in5.28s. It includes the new tests and overlaps earlier reported suites; do not
add these counts as independent physical validations. Focused tests were85
before the seven nonlinear checks were added.
The separate existing nonlinear/finite-depth pressure suite passes78 tests in
22.30s (session17059, exit0). All local test and diagnostic jobs are terminal.

NEXT derive a wet/dry-compatible weighted forcing and its directional limit
without freezing positive mass rates, and implement the original prescribed
pressure lifts. Keep checking whether newly enabled MC reconstruction changes
physical wet-row operators for other source directions. Then evaluate the
complete original-start candidate history, physical accuracy, pressure columns,
unchanged CFL gates and production capacity before native/playable promotion.

Both7300s/local26000 full-river audits remain the latest completed reviewed
checkpoint. The same cook74818/PID41820 is verified live, last observed at
7367.5s/local27350. NEXT complete7400s/local28000 needs BOTH audits. No restart.
Desktop30FPS/p9533.333ms, physics120Hz and solver1.6ms remain unchanged. The
last ordinary gameplay18.899245FPS/p9570.33ms still fails. Terrain, cresting,
froth, reference-motion matching, later rivers, crew, release and final commit
remain open. No new footage, screenshot, native build or playable acceptance.
