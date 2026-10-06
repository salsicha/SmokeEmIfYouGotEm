# Common fluxes for the local affine-bed front predictor

2026-09-17. This extends the local finite-time component, not the playable
solver. Installed gameplay, geometry and materials are unchanged. No new
visual, motion or FPS acceptance is claimed.

## Implementation and scope

`subcell_affine_dry_fan.py` now integrates mass, both momentum components and
total-energy flux along each directed original source edge. It splits edges
exactly at the moving fan head and dry front, without a rounded unit normal
or edge length. Reversing an edge gives its exact opposite transfer; subdividing
an edge preserves the same total. Pressure and pressure work appear once.

Polygon rates sum those boundary fluxes and the original affine-bed force.
Total energy already contains bed potential, so no extra bed-energy source
is added. The boundary calculation does not derive its answer by differencing
the integrated state. Positive sub-float transfers remain positive internally.

This remains one uniform wet-half-plane state on one affine bed. It does not
solve different states/slopes across a junction, the actual varying inlet,
interacting fronts, dispersive evolution or a global conservative river step.
Exact arithmetic does not add survey precision to the original coordinates.

## Validation

65 focused tests PASS, zero skips. Controls include independent polynomial
quadrature, analytic boundary/bed budget derivatives, two-dimensional time
refinement, source partitions, winding, edge subdivision, energy datum shifts,
sub-float water and deliberate corruption of audit rates.

The first focused run retained one failed derivative probe: at divisor 400,
error 2.157561306117824e-5 exceeded the unchanged 2e-5 gate. Adding divisor 800
preserved the earlier probes and demonstrated second-order convergence. This
refines an independent derivative measurement, not a river solver timestep.

Focused JUnit: `tmp/affine-fan-flux-focused-v3-20260917.xml`, SHA256
`e314459e3c4fc43acc099f2025d36ec0da8c1ec493c9d052334cf82fdd6ce9b7`.

Broader suite: **731 PASS / 13 FAIL**, 744 tests, zero errors/skips, one existing
warning, 146.74 seconds. Failure identities match the preceding suite exactly:
four constant-velocity energy, eight nonlinear rational energy and one original
storage/face representation failure. These are unresolved, not waived.
JUnit: `tmp/affine-fan-flux-full-suite-v1-20260917.xml`, SHA256
`f315bd1d07a41d256e3a2d28add1399578c1f84dd2d8e45968d1d87589cf9d57`.

The actual-source audit retains all eleven supported original local predictors
and two unsupported receding/fan records. Each supported predictor has positive
dry-side receipt, exact whole/wet/dry rate partitions and independent centered
time-balance passes at both divisors 256 and 512. The unchanged relative gate
is 1e-10, scaled by gross boundary and bed-force rates, without a float floor.
Largest reported scaled error is approximately 3.711510798499365e-26. Zero-scale
controls reject even a 1e-400 ghost rate. All attempted probe sizes are retained.

Independent reload checks preserved 215 preceding predictor fields and verified
619 source/report/implementation hashes, serialized exact partitions and time
controls. Original source and water arrays remain untouched; captured-rock and
inferred-flank provenance remain distinct.
Report: `tmp/south-fork-affine-front-flux-v1-20260917.json`, SHA256
`4f228cdef8d45e076fb2af96416a633b08c65ccaee4e35c63f6f797852a643d5`.

## Hydraulic continuation and remaining work

The existing cook's completed 4550s/local19000 snapshot passes the state audit
and all 86,720 artificial dry-bank checks. Maximum depth 3.819190363 m, speed
5.513488122 m/s, volume 2,865,990.650265 m3, maximum step residual
1.521822357e-8 m3. Outflow 104.842435944 versus inflow 45.306954547 m3/s:
**not settled or promoted**. Reports:
`tmp/control-ablation-4550s-state-v1-20260917.json` and
`tmp/control-ablation-4550s-banks-v1-20260917.json`.
Depth SHA256: `3e9d26c81524bf71bd23413f0ab4faae924325608d50ac0a472f71bce062105e`.
Next 4600s/local20000 requires its completion marker and BOTH audits.

Actual varying-inlet evolution, bed-junction and multi-front coupling, and
dispersive metric/energy work remain prerequisites to native/playable
integration. Do not add these pressure terms to the old front pressure without
a consistent control volume. Breaking/froth, reference motion and sustained
30 FPS remain unqualified. South Fork through the remaining scene, crew,
normalization, regression and release queue remains open. Troublemaker is a
rapid within South Fork, never a separate menu scenario.

Generated evidence and Unreal build artifacts remain local under existing
`.gitignore` rules; only implementation, tests and this evidence summary belong
in the commit.
