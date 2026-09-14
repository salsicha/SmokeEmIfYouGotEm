# Scalar derivative: unchanged control-suite comparison — September 14

The candidate remains research-only. Separate original and candidate processes
ran the SAME94 tests from eight existing, unmodified suites, using
`physics/scripts/validate_difference_scalar_controls.py`. The context override
is local to that short process and restores the original class method on exit.
It does not alter any of the five continuing river/history jobs.

Original:94 PASS6.59s. Candidate:91 PASS,3 FAIL6.51s.
Reports `tmp/south-fork-difference-scalar-{original,candidate}-controls-v1-20260914.xml`.
No tests were skipped, thresholds relaxed, failures relabelled as passes, or
existing frozen test/operator files edited.

## Failure meanings and next derivation

- `test_nonlinear_material_identities_include_both_geometry_rates`: maximum
  reported difference0.11321323. Its independent time derivative uses pressure
  traction `G=-D.T` for scalar advection, while the candidate uses a constant-null
  ordinary derivative. This is a changed material identity, not roundoff.
- `test_affine_work_and_time_identity_on_original_variable_bed_geometry`:
  maximum reported difference0.01807808 in the time identity. The preceding
  physical pressure-work assertion passes; the failed scalar-advection identity
  again explicitly calls `gradient_traction`.
- `test_scalar_trace_and_physical_pressure_have_distinct_dry_domains`:
  residual1.5769120100. The test requires the ordinary scalar derivative itself
  to be `-D.T`, including a constant scalar on directional dry support. The
  candidate's constant-null derivative intentionally no longer has that adjoint.

These failures identify assumptions affected by separating ordinary scalar
transport from physical pressure work. They cannot simply be ignored because
constant derivatives improved or the short candidate replay has lower speeds.
Next independently derive the revised material/affine boundary work identities
and physical consistency requirements. Retain the original pressure-force
adjoint and actual evolving-geometry rates. Do not replace these controls with
self-consistency checks that merely repeat the candidate implementation.

The91passing checks include actual solitary-wave rate refinement, stationary
thin/dry pressure, force adjoints, pressure-system residuals, prescribed boundary
validation and directional geometry. They do NOT prove full moving history,
mechanical-energy balance, all wet/dry boundaries, native cost or playable waves.
The unchanged original and separate candidate full9.066667s/two-move replays
remain running and unqualified. No native or gameplay promotion follows.

Follow-up: [independent face-matrix identities and boundary consistency](normal-river-scalar-boundary-identities.md)
explain the changed scalar work term and finite-difference material identities,
but uncover a separate affine boundary failure: endpoint derivative0.5 instead
of1 at every tested refinement. Original three failures remain retained;
the candidate remains unqualified, now for an independently demonstrated
finite-window consistency defect as well.
