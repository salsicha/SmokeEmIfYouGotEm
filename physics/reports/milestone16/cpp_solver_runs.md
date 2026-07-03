# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.082 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.097 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.073 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.096 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.073 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.102 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.069 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.104 | no |
| canonical | constriction | reduced | 9 | PASS | 0.066 | no |
| canonical | constriction | finite_volume | 9 | PASS | 5.061 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.063 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.115 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.069 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.098 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.069 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.107 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.421 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.779 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.432 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.774 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.435 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.783 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.429 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.780 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.439 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.789 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.439 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.810 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.128 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.202 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.123 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.201 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.127 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.201 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.213 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.393 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.217 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.396 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.219 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.403 | 7 reaches / 1 drops |
