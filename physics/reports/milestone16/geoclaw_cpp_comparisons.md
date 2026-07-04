# Milestone 16 GeoClaw/C++ Comparisons

Schema: `raftsim.milestone16.geoclaw_cpp_comparisons.v0`

Decision: **BLOCKED**

Comparison count: 40

| Suite | Gate scenario | Mode | Tier | Thresholds | Failing checks | Reach/drop |
| --- | --- | --- | --- | --- | --- | --- |
| canonical | flat_pool | reduced | production_candidate | PASS | none | n/a |
| canonical | flat_pool | finite_volume | production_candidate | PASS | none | n/a |
| canonical | uniform_channel | reduced | production_candidate | PASS | none | n/a |
| canonical | uniform_channel | finite_volume | production_candidate | PASS | none | n/a |
| canonical | dam_break | reduced | unreal_prototype | PASS | none | n/a |
| canonical | dam_break | finite_volume | unreal_prototype | PASS | none | n/a |
| canonical | bed_step | reduced | unreal_prototype | PASS | none | n/a |
| canonical | bed_step | finite_volume | unreal_prototype | PASS | none | n/a |
| canonical | constriction | reduced | unreal_prototype | PASS | none | n/a |
| canonical | constriction | finite_volume | unreal_prototype | PASS | none | n/a |
| canonical | wet_dry_shoreline | reduced | unreal_prototype | PASS | none | n/a |
| canonical | wet_dry_shoreline | finite_volume | unreal_prototype | PASS | none | n/a |
| canonical | sloping_manning_channel | reduced | unreal_prototype | PASS | none | n/a |
| canonical | sloping_manning_channel | finite_volume | unreal_prototype | PASS | none | n/a |
| canonical | drop_ledge | reduced | unreal_prototype | PASS | none | n/a |
| canonical | drop_ledge | finite_volume | unreal_prototype | PASS | none | n/a |
| rafting | boulder_garden | reduced | research_accepted | PASS | none | n/a |
| rafting | boulder_garden | finite_volume | research_accepted | PASS | none | n/a |
| rafting | cascading_wave_train | reduced | research_accepted | PASS | none | n/a |
| rafting | cascading_wave_train | finite_volume | research_accepted | PASS | none | n/a |
| rafting | hydraulic_hole_downstream_boil | reduced | research_accepted | PASS | none | n/a |
| rafting | hydraulic_hole_downstream_boil | finite_volume | research_accepted | PASS | none | n/a |
| rafting | lateral_wave | reduced | research_accepted | PASS | none | n/a |
| rafting | lateral_wave | finite_volume | research_accepted | PASS | none | n/a |
| rafting | eddy_line_shear | reduced | research_accepted | PASS | none | n/a |
| rafting | eddy_line_shear | finite_volume | research_accepted | PASS | none | n/a |
| rafting | shallow_shelf | reduced | research_accepted | PASS | none | n/a |
| rafting | shallow_shelf | finite_volume | research_accepted | PASS | none | n/a |
| real_world | south_fork_low_runnable | reduced | research_accepted | PASS | none | n/a |
| real_world | south_fork_low_runnable | finite_volume | research_accepted | PASS | none | n/a |
| real_world | south_fork_median_runnable | reduced | research_accepted | PASS | none | n/a |
| real_world | south_fork_median_runnable | finite_volume | research_accepted | PASS | none | n/a |
| real_world | south_fork_high_runnable | reduced | research_accepted | PASS | none | n/a |
| real_world | south_fork_high_runnable | finite_volume | research_accepted | FAIL | field_linf, slope_linf, probe_linf, cross_section_linf, froude_delta, feature_location_delta | n/a |
| cascading | south_fork_cascading_low_runnable | reduced | unreal_prototype | FAIL | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta | PASS |
| cascading | south_fork_cascading_low_runnable | finite_volume | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_median_runnable | reduced | unreal_prototype | FAIL | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta | PASS |
| cascading | south_fork_cascading_median_runnable | finite_volume | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_high_runnable | reduced | unreal_prototype | FAIL | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta | PASS |
| cascading | south_fork_cascading_high_runnable | finite_volume | unreal_prototype | PASS | none | PASS |
