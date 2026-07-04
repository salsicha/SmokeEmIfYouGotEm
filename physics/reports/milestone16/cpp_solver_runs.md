# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.152 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.175 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.153 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.288 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.157 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.182 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.162 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.195 | no |
| canonical | constriction | reduced | 9 | PASS | 0.143 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.140 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.151 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.202 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.160 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.186 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.141 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.319 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.383 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.382 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.382 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.380 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.503 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.870 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.511 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.982 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.523 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.973 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.559 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.865 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.207 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.310 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.229 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.288 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.211 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.282 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.295 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.537 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.298 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.472 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.298 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.553 | 7 reaches / 1 drops |
