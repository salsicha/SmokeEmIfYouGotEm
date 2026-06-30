# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.548 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.062 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.038 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.063 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.036 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.063 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.037 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.065 | no |
| canonical | constriction | reduced | 9 | PASS | 0.033 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.067 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.031 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.060 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.037 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.063 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.037 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.065 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.308 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.642 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.315 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.637 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.318 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.645 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.309 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.638 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.320 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.643 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.317 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.643 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.079 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.149 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.078 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.151 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.078 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.150 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.147 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.300 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.147 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.305 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.148 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.307 | 7 reaches / 1 drops |
