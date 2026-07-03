# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.348 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.083 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.059 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.086 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.063 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.092 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.063 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.118 | no |
| canonical | constriction | reduced | 9 | PASS | 0.088 | no |
| canonical | constriction | finite_volume | 9 | PASS | 4.866 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.055 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.157 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.061 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.091 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.064 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.100 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.350 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.768 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.369 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.710 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.367 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.783 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.353 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.767 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.363 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.805 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.364 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.780 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.109 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.185 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.108 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.185 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.106 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.256 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.182 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.358 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.180 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.369 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.183 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.424 | 7 reaches / 1 drops |
