# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.031 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.055 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.035 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.059 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.039 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.063 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.038 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.064 | no |
| canonical | constriction | reduced | 9 | PASS | 0.034 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.066 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.035 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.059 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.035 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.060 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.044 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.069 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.387 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.750 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.406 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.750 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.420 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.765 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.372 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.739 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.404 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.746 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.431 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.765 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.106 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.174 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.105 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.174 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.108 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.176 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.221 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.383 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.228 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.391 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.231 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.395 | 7 reaches / 1 drops |
