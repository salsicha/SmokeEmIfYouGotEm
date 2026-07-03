# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.064 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.091 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.072 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.149 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.085 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.105 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.068 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.102 | no |
| canonical | constriction | reduced | 9 | PASS | 0.065 | no |
| canonical | constriction | finite_volume | 9 | PASS | 5.180 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.079 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.113 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.069 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.095 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.070 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.105 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.413 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.750 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.490 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.823 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.433 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.829 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.423 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.821 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.437 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.754 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.430 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.825 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.121 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.196 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.120 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.196 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.122 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.199 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.212 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.446 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.211 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.384 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.213 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.387 | 7 reaches / 1 drops |
