# Milestone 17 Analytic Fixture Validation

Schema: `raftsim.milestone17.analytic_validation_report.v0`

Decision: **BLOCKED**

Candidate: `throat_lower_edge_streamwise` (`cpp`)

Fixture count: 7

| Fixture | Tier | Result | Max metric value | Failing metrics |
| --- | --- | --- | ---: | --- |
| lake_at_rest_balance | well_balanced | FAIL | 2.88417 | surface_linf, speed_linf |
| sloping_channel_friction | analytic | FAIL | 1.93069 | normal_velocity_linf, unit_discharge_linf |
| wet_dry_shoreline | well_balanced | FAIL | 476 | wet_mask_mismatch_count, shoreline_position_abs |
| bed_step_subcritical | analytic | FAIL | 2.6422e+16 | depth_linf, specific_energy_abs |
| dam_break_bore | diagnostic | FAIL | 2 | initial_depth_linf, mass_relative_drift |
| hydraulic_jump_conjugate_depth | analytic | FAIL | 768 | conjugate_depth_ratio_abs, froude_class_agreement |
| transcritical_bump | analytic | FAIL | 2.70521 | unit_discharge_linf, crest_froude_abs |
