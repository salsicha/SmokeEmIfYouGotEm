# Terrain-coupled gravity waves: linear component, not river completion

September 14, 2026. This adds a pressure-wave component on the original
source-supported pool geometry. It does **not** implement full nonlinear
advection, moving wet support, breaking, a native solver or playable water.
The separate actual moving-water timestep comparison remains required.

## Compatible transport and pressure force

For a fixed lake-at-rest reference, let B map physical pool momentum to volume
rate. Each shared wet face transfers its integrated water column times the
mean normal physical velocity. Oblique internal source faces retain their
normal; disconnected pools have no shared hydraulic face. Exterior boundaries
are reflecting. B is assembled once, and its actual transpose supplies pressure
work; an unrelated gradient is not substituted.

Let R be the diagonal square root of reference volume, H=diag(g/wet_area),
and S the original two-pole pressure response. Define M=R S R. For volume
perturbation a and physical momentum p:

```text
a_t = B p
p_t = -M B^T H a
E = (p^T M^-1 p + a^T H a)/2
```

The energy rate cancels by transpose pairing. The implementation uses the
original inverse-factor positive kinetic energy to check that cancellation;
it does not replace energy with a convenient norm. Flat periodic frequencies
match the original two-pole response, and the pressure rate approaches the
existing full flat two-dimensional stage's small-amplitude limit quadratically.
This is the nondissipative linear pressure component, not the linearization
of the Rusanov-damped donor history or its nonlinear transport replacement.

## Local momentum requires actual bed and wall reactions

Global energy cancellation alone is insufficient. With q=R f, z=(I+lambda Q)^-1 q,
the identity R S R f = V f - sum(weight*lambda*R Q z) gives an independent
local force ledger. Expand Q using the original Gram jet:

```text
jet = (D auxiliary, auxiliary_x, auxiliary_y)
(Pi, tau_x, tau_y) = Gram * jet
R Q z = D^T Pi + tau
```

The divergence transpose becomes paired pressure-face tractions, plus its
explicit reflecting-wall contribution. The remaining two Gram components are
the dispersive bed reaction. Hydrostatic bed increments are independently
integrated as -potential times the original wet-triangle slope integral;
wall increments use the original wall water columns. Bed force is not a
leftover inferred by subtracting a final momentum divergence.

The local face/bed/wall sum must reproduce the independently evaluated
two-pole acceleration at 1e-10. Finite updates also compare total physical
momentum change with the integrated bed/wall impulse, rather than demanding
zero momentum change on sloping terrain with walls.

## Finite linear evolution and limitations

Implicit midpoint eliminates momentum into the symmetric positive Schur
operator I+dt^2/4 H^1/2 B M B^T H^1/2. This is matrix-free; the dense coupled
matrix appears only in an independent small test. The scalar solve is packed
into the existing range-CG interface's first component, with identity action
and zero RHS for the unused component. Each original pressure solve and the
new Schur solve retain 40 iterations and the 2e-5 true-residual gate. The
preconditioner uses a diagonal upper bound, not substituted pressure physics.

The original-equation residual, mass, physical momentum/external impulse and
quadratic energy are separately checked at 1e-10. No physical-state rescaling, velocity cap,
energy projection, automatic timestep reduction or water clipping is applied.
Finite perturbations that lose positive water or cross a source-topology
interval reject. Geometry probes enforce this limit; they do not silently turn
the fixed-reference equations into nonlinear evolution.

Nested pressure solves are reference work, not a qualified runtime strategy.
No 30 FPS claim follows from these controls. The full nonlinear metric-time,
advection and terrain work must still be derived and integrated with wet/dry
events, followed by open-boundary, spatial and native/shared-surface checks.

## Validation and registered-terrain provenance

Thirteen new tests pass, covering transport adjoints, energy work, original
axial/oblique wave frequencies, dry-ridge separation, dense coupled midpoint,
second-order finite phase refinement at a fixed 0.2s horizon, reference and
negative-water rejection, oblique internal source faces, the full flat model's
linear limit, hydrostatic bed derivatives and absence of invented flat-bed forces.

Two explicitly artificial lake controls use unchanged 4x4 blocks of the
registered South Fork source. The common level is the median reconstructed
stage from original source-cell volumes; velocities start at zero. The prescribed
perturbation is volume times 1e-6 times cos(pool index), with no amplitude retry.
These are **not the original river level, velocity or observed waves**.

- Channel block (column 6, row 6): 16 pools. Thirteen have authority code 2
  (uncalibrated submerged prior), three mix 2/5 (inferred flank). This block has
  no captured DEM/exposed-rock support and must not be called measured terrain.
- Rock-bank block (column 12, row 8): 14 pools. Two have code 3 (exposed-rock
  returns), four mix 3/4 (gap interpolation), eight mix 3/5 (inferred flank).
  Mixed groups are not wholly captured bathymetry.

Both controls complete six 20ms linear steps (0.12s), retaining their source
support. Maximum pressure residual is 6.78e-16 and local momentum-ledger error
6.44e-20. Energy changes are at roundoff relative to their small prescribed
perturbation energies; this is not a nonlinear finite-amplitude stability test.
All 522 recorded input/current-Python hashes match each final report:

- `tmp/south-fork-controlled-gravity-waves-channel-v2-20260914.json`, SHA256
  `efd7ef7084c82d7aac42e5516243bed2cfcabb5ce9e0fb543db65a4ade76908f`.
- `tmp/south-fork-controlled-gravity-waves-rock-bank-v1-20260914.json`, SHA256
  `6e2eeefdb9498176b72957c2b759ae1b26ee598b800a2638c0f0ae912ea0f345`.

Reproduce with `audit_south_fork_gravity_waves.py --source-report
tmp/south-fork-event-history-100-v3-20260914.json --report FRESH_PATH`; the channel
is the default. Add `--block-col 12 --block-row 8` for the rock-bank control.

Focused suite: **288 PASS / 1 retained geometry FAIL** in 42.06s, report
`tmp/subcell-gravity-wave-suite-v1-20260914.xml`. Retained energy suite:
**25 PASS / 12 FAIL**, report `tmp/subcell-gravity-wave-retained-v1-20260914.xml`.
No prior tests or gates were weakened or redirected to this linear path.
All 464 protected source, scene, actor and prior runtime evidence hashes were
also checked unchanged.
The full playable terrain/water/froth, 30 FPS, later rivers, crew, normalization
and release objectives remain open. No scene asset or native code changed.
