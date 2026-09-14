# Exact source-face coupling and a shallow-current timestep correction

September 14, 2026. The preceding turn committed the pending reference source
and tests as `12e83ea9d`; that was progress, not playable-scene acceptance.
This work addresses the exact-geometry coupling prerequisite exposed by the
[source/collision comparison](normal-river-subcell-geometry.md).
No normal map, captured terrain, material, native solver, menu or quality gate
changed. There is no new visible wave, froth or frame-rate improvement here.

## Shared geometry and independent hydrostatic balance

The reference now clips original terrain triangles to each finite-volume cell,
extracts their exact shared boundary sections, and verifies that both neighbors
see the same piecewise-linear bed, not merely the same average elevation.
Clipping intersections have their mathematical clipping coordinate assigned
exactly; original source vertices are not displaced. Missing, overlapping or
inconsistent face coverage fails closed.

`TriangleFaceSection` integrates wet face area and squared depth exactly.
`TriangleCellStorage.hydrostatic_bed_force` independently integrates
`-g * depth * grad(bed)` over the original clipped triangles. The bed force is
not defined by subtracting a face-pressure residual to manufacture equilibrium.
`SubcellGeometryPatch` evaluates each shared nondispersive Rusanov flux once,
then adds it to one cell and subtracts it from the other. Its reflecting and
periodic boundaries are test controls, not the actual river boundary conditions.

The real 16 by 16 patch uses the exact stored atlas lattice origin
`[-5438.999999998952, 3593]`, rather than rounding away its approximately 1 nm
offset. Source-center bed agreement is 1.42108547e-14 m. Four stationary stages
retain zero mass rate and maximum momentum residual 2.842170943e-14 m4/s2;
three include genuinely dry cells. These are component controls, not acceptance
of river hydrodynamics, inferred bathymetry, or internal wet-basin connectivity.

## The old timestep test missed counterflow

Baseline report `tmp/south-fork-subcell-base-transport-v2-20260914.json` is
retained unchanged. Ten steps from the real 600-second atlas covered only
0.031917192 simulated seconds. Maximum current decreased from 6.092580459 to
5.192007175 m/s; the shrinking timestep was **not** a demonstrated velocity
blow-up in this run. Closed-patch mass error stayed within 1.136868377e-13 m3.
Its negative nondispersive mechanical-energy rates do not establish the required
full two-pole energy balance or fully discrete energy stability.

An independent analytic counterexample nevertheless exposes an actual bug in
the old timestep bound. Two cells meet at the bottom of `bed = abs(normal)`.
Both have stage `eta`, volume `eta^2/2`, and shared wet face area `eta`.
Tangential velocities are +1 and -1 m/s; their normal velocities are zero.
Net water exchange is zero, but the Rusanov donors exchange tangential momentum.
The analytic tangential acceleration is
`du/dt = -2 * sqrt(g*eta) / eta * u`.

At eta = 1e-4 m, the previous net-draining/grid-wave bound permits a 0.218166815 s
step, turning the two currents into approximately -135.663705 and +135.663705
m/s without changing their positive water volumes. A nonnegative-depth test
alone therefore falsely accepts this update.

The corrected bound includes the **gross outgoing donor coefficient**:
on the left of an oriented face it is `(a + u_normal) * face_area / 2`, and on
the right `(a - u_normal) * face_area / 2`. Summing these coefficients per cell
and requiring `dt <= volume / sum` prevents negative retained transport weight.
This is the actual Rusanov decomposition, not a velocity cap, depth floor,
global rescale or post-update repair. Pressure, bed work and dispersion still
need their own stability proof. The existing net-draining and wave bounds also
remain in force.

The regression retains the old rejected update explicitly and checks the
independent analytic acceleration, both coordinate directions and stages
1e-2, 1e-4 and 1e-6 m. Corrected updates preserve volume and keep these currents
within the original velocity bounds. The combined original storage, new face,
patch, captured-registration and source-epoch run passes **29 tests**.

Reproduce the component tests with the physics/scripts, physics/tests and
unreal/Scripts directories on PYTHONPATH, plus NumPy:

```text
python -m unittest test_triangle_cell_storage test_triangle_face_section test_subcell_geometry_patch test_captured_rock_vertex_registration test_carrier_source_epochs
```

## Extended captured-state result: drying-cell timestep collapse remains

Process 32784 completed exit 0 using the same real 600-second atlas, unchanged
16 by 16 footprint, four stationary controls and 100 evolving steps. Report:
`tmp/south-fork-subcell-donor-transport-100steps-v1-20260914.json`, SHA256
`bd5adc31906078a6c967d8a81aba0de682f719305cb58d6a6bf9b8ca1199ee5c`.
Reproduce with:

```text
python physics/scripts/audit_south_fork_subcell_transport.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report FRESH_PATH --steps 100
```

All states remain finite/nonnegative; closed-patch volume error is at most
1.136868377e-13 m3. Maximum current decreases from the initial 6.092580459 to
5.091335659 m/s. Nondispersive mechanical-energy rates remain negative, ranging
from -4589.036890 to -1951.788586 in the reference's unit-density energy units.
These rates are not a fully discrete or full two-pole energy acceptance test.

Crucially, **100 steps advance only 0.067411202 simulated seconds**, taking
221.661805 wall seconds in this Python reference. The first timestep is
0.001820580 s and the last only **0.000017007314 s**. Minimum cell volume falls
to 2.464885913e-14 m3. The final donor/net-draining limit is 0.000037794031 s,
while the grid-wave limit is still 0.061271579 s. Thus the tighter bound fixes
the analytic counterflow bug but leaves an impractical drying-cell restriction;
do not label this a successful long-history or production-ready run.

Next work must address wet-front/cut-cell transport and compatible pressure
work without silently deleting this water, clipping velocities or loosening
energy/refinement gates. Blindly extending this tiny-timestep run is not the
next acceptance step. No runtime promotion was performed. The audit rehashed
its source, geometry and state inputs unchanged; a separate current check also
verified all **464** protected saved-map/capture/mesh/profile/actor files against
the original combined collision audit.

## Remaining delivery requirements

The independent expanded-river cook remains live on handle 84168, directly
observed beyond native 9800/local 8000 without restarting or suspending it.
The completed 9800-second snapshot passes BOTH state and artificial-bank
audits: all 5,382,400 cells finite; all 86,720 artificial-bank cells exactly
dry; maximum step conservation residual 1.412245743e-8 m3. Outflow is still
104.772869 m3/s versus inflow 45.306955 m3/s, so settling is not accepted.
Reports: `tmp/south-fork-expanded-9800s-{state,banks}-v1-20260914.json`.
Snapshot h/u/v SHA256 values:

```text
h a20241194f9b59a0165b8a79d869d81dc4fb59a661da51e29b75e7d1709a954d
u 04204b3e49685b95e29a55dc1ebf2065295fe08ad2917d22c4d864f25150c38f
v 6321caed8b6f29fbd8295e439ab6508f40ec02e0995f8b0eaffff53623c09bf8
```

Next completed 9900/local 10000 needs both audits. This long cook uses the
existing native solver, not the experimental exact-subcell reference above.

This reference is first-order and dissipative. It is not a replacement for the
required nonbreaking energy/dispersion-preserving two-pole river solver. All
previous coupled physical-energy failures remain unresolved and authoritative;
no gate was relaxed or skipped. A single stage per cell can also connect
distinct subcell puddles incorrectly; exact storage alone does not prove flow
topology. Native cost, open boundaries, wet-front/refinement/full-history
qualification and shared rendered/contact geometry remain prerequisites.

The normal playable South Fork entry remains the delivery target. Latest actual
engine evidence is still 11.520818 FPS / p95 103.8838 ms, failing the unchanged
30 FPS / p95 33.333333 ms target, with unaccepted rapid shape, breaking and
froth. Do not promote this reference simply to produce a visible change.
After South Fork: Colorado, Pacuare, Futaleufu in that order; remaining
Chilko/Zambezi water, crew realism/fit/animation, normalization, regressions and
release checks. Troublemaker is a rapid within South Fork, never a menu scenario.
