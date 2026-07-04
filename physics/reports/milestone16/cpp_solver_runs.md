# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.241 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.258 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.236 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.258 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.241 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.264 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.235 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.265 | no |
| canonical | constriction | reduced | 9 | PASS | 0.222 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.229 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.228 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.273 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.233 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.259 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.218 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.266 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.435 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.440 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.429 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.430 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.428 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.434 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.426 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.428 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.430 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.426 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.429 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.837 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.279 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.345 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.278 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.346 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.281 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.346 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.354 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.536 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.356 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.513 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.356 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.518 | 7 reaches / 1 drops |
