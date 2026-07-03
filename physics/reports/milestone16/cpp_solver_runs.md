# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.354 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.097 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.081 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.107 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.084 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.120 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.085 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.157 | no |
| canonical | constriction | reduced | 9 | PASS | 0.130 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.076 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.084 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.143 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.088 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.115 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.083 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.124 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.482 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.846 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.593 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.854 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.477 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.985 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.632 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 1.024 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.547 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.882 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.480 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 1.008 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.142 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.227 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.139 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.224 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.135 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.228 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.239 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.424 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.355 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.461 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.244 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.452 | 7 reaches / 1 drops |
