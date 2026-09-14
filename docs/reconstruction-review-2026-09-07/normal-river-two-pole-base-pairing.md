# Base flux pairing inside the original two-pole operator — September 14

The previous goal turn made progress by deriving and testing an energy-consistent
mass/pressure flux over exact terrain. This turn connects its flat-face limit to
the existing full two-pole research operator. It removes the constant-velocity
base obstruction and reduces the nonlinear defect, but **does not pass the full
nonbreaking energy gate and must not enter gameplay**.

## Explicit comparison paths, unchanged physical response

`conservative_rational_stress.py` now accepts an explicit `flux_scheme`:

- `donor-stress` remains the original default and retains the old controls.
- `paired-base` uses `F_h=mean(h)*mean(u_normal)` and advects canonical momentum
  with `F_h*mean(v)`, where u is physical velocity and v is canonical velocity.

The hydrostatic and auxiliary stress terms are otherwise unchanged. Both original
poles, the reconstructed pressure operator, inverse physical-state preparation,
40-iteration solves and complete derivative of the physical/canonical momentum
map remain in use. One canonical face flux still yields one physical momentum
face flux through the existing auxiliary time-derivative correction; each owner
receives opposite contributions. There is no global energy/momentum projection,
velocity rescale, source geometry change or replacement pressure model.

The paired path reports its own mass-only forward-Euler bound based on its
actual face outflow. It no longer reports the unrelated donor bound. This is
not a pressure/velocity stability or wet-front qualification. The old report
field `donor_incremental_energy_rate` is null for paired mode; the neutral
`mass_scheme_incremental_energy_rate` and explicit `incremental_work_is_donor`
prevent new centered-reference work from being mislabeled as donor work.

## What now passes, and what still fails

Eleven new component controls pass: four constant-physical-velocity cases in
both axes/signs, four one-/two-dimensional local-conservation/ownership cases,
two full pressure-and-mass linear-response controls, and invalid-selector
rejection. The constant-velocity cases preserve mass and momentum while reducing
the original absolute energy defect >13 to <1e-10. They do not replace the
unchanged legacy obstruction tests, which still exercise the original default.

The pressure response retains the original rational multiplier at finite kh;
the mass response retains the original centered derivative at constant depth.
Testing pressure alone would not suffice to prove the linear wave system.

All eight original nonlinear profiles were evaluated using identical source
state hashes and the same physical-momentum preparation. Signed total energy
rates are:

| Cells | Seed | Original donor/stress | Paired base |
| --- | --- | ---: | ---: |
| 64 | 2200 | 0.007801814356 | 0.000829628143 |
| 64 | 2202 | -0.001985324442 | -0.000734457131 |
| 64 | 2204 | -0.004239074337 | -0.001027124750 |
| 64 | 2206 | 0.000786443511 | -0.000592879481 |
| 128 | 2200 | 0.001025279235 | 0.000105612569 |
| 128 | 2202 | -0.000206260205 | -0.000093952270 |
| 128 | 2204 | -0.000451879559 | -0.000130466099 |
| 128 | 2206 | 0.000132646682 | -0.000075632520 |

**Every paired nonlinear case still fails |energy rate| <1e-10.** Changing sign
or decreasing the magnitude is not conservation. The approximately eightfold
decrease in integrated error includes halving the one-cell-wide domain's width;
per-unit-width error decreases approximately fourfold. This supports a spatial
discretization-defect investigation, not acceptance by refinement or changing
the gate. It also shows that pairing the base alone is insufficient.

All eight paired total-momentum gates pass, net mass rates are zero, maximum
local physical-momentum flux residual is 1.3500311979e-13, maximum physical state
recovery error is 5.7731597281e-15, and maximum derivative solve residual is
1.1604073010e-14. These small solve/coordinate errors do not explain energy
defects of order 1e-4 to 1e-3.

Eight explicit required-energy tests were added for the new path; they currently
fail, rather than converting the successful component tests into full acceptance.
Final standalone test invocation exits **1**, with **25 PASS / 12 FAIL** in
6.99 seconds: eight paired nonlinear failures plus four retained legacy
constant-velocity failures. No skip, xfail or relaxed threshold was added.

```text
python -m pytest physics/tests/test_paired_base_rational_stress.py physics/tests/test_conservative_rational_stress.py physics/tests/test_constant_velocity_mass_energy.py
```

Final test evidence:
`tmp/two-pole-paired-base-required-gates-v2-20260914.xml`.
The first component-only run passed 21 tests; it is explicitly superseded as a
qualification claim by the complete required-gate result above. These targeted
counts do not supersede the broader historical 89 PASS / 29 FAIL suite.

## Reproducible source-locked comparisons

Both final-source audits completed with all eight records and implementation
hashes checked before/after. Audit exit 0 means a complete report, not energy
acceptance; each record's energy gate remains false.

```text
python physics/scripts/audit_conservative_rational_stress.py --metric-source primal --flux-scheme paired-base --report FRESH_PAIRED_PATH
python physics/scripts/audit_conservative_rational_stress.py --metric-source primal --flux-scheme donor-stress --report FRESH_ORIGINAL_PATH
```

Reports and SHA256:

- `tmp/two-pole-paired-base-eight-v2-20260914.json`:
  `d55d916bacb923662d9d3b386664874ca1ae0839a5091c2c868d1f7c7341223e`.
- `tmp/two-pole-original-donor-eight-v2-20260914.json`:
  `1abfee477a4a7efdfd420ac4114575d8569db791fcd678b345f72777cbdfb74f`.

The earlier v1 paired report retains its then-current source hashes; v2 clarifies
that its incremental mass work is not donor work and avoids constructing an
unused donor operator. The final numerical rates are unchanged.

## Next required work

Derive the compatible **discrete auxiliary-pressure work**, jointly with mass
and canonical advection, retaining local physical-momentum conservation and
the existing linear response. A momentum-only adjustment or simply attaching
the old auxiliary stress to the new base flux is not a qualified solution.
Do not use a global conservation projection or a small-denominator face repair
to manufacture passing totals. Full two-dimensional nonlinear, exact-terrain,
wet-front/time, open-boundary, refinement and native-budget qualification remain.

No Unreal runtime, scene geometry, collision, material, menu or quality setting
changed. All 464 protected source, scene and actor hashes were rechecked unchanged.
This turn therefore claims no new engine-motion, visual or 30 FPS
improvement. South Fork remains first, then Colorado, Pacuare and Futaleufu;
Chilko/Zambezi water, crew, normalization/regressions and release scope remain
open. Troublemaker remains a rapid within South Fork. The full goal stays active.
