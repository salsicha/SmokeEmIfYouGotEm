# Milestone 16 C++ Solver Runs

Schema: `raftsim.milestone16.cpp_solver_runs.v0`

Decision: **PASS**

Run count: 40

| Suite | Gate scenario | Mode | Frames | Validation | Runtime (s) | Cascading |
| --- | --- | --- | ---: | --- | ---: | --- |
| canonical | flat_pool | reduced | 9 | PASS | 0.206 | no |
| canonical | flat_pool | finite_volume | 9 | PASS | 0.227 | no |
| canonical | uniform_channel | reduced | 9 | PASS | 0.206 | no |
| canonical | uniform_channel | finite_volume | 9 | PASS | 0.227 | no |
| canonical | dam_break | reduced | 9 | PASS | 0.209 | no |
| canonical | dam_break | finite_volume | 9 | PASS | 0.236 | no |
| canonical | bed_step | reduced | 9 | PASS | 0.205 | no |
| canonical | bed_step | finite_volume | 9 | PASS | 0.234 | no |
| canonical | constriction | reduced | 9 | PASS | 0.188 | no |
| canonical | constriction | finite_volume | 9 | PASS | 0.189 | no |
| canonical | wet_dry_shoreline | reduced | 9 | PASS | 0.198 | no |
| canonical | wet_dry_shoreline | finite_volume | 9 | PASS | 0.255 | no |
| canonical | sloping_manning_channel | reduced | 9 | PASS | 0.203 | no |
| canonical | sloping_manning_channel | finite_volume | 9 | PASS | 0.230 | no |
| canonical | drop_ledge | reduced | 9 | PASS | 0.189 | no |
| canonical | drop_ledge | finite_volume | 9 | PASS | 0.244 | no |
| rafting | boulder_garden | reduced | 9 | PASS | 0.408 | no |
| rafting | boulder_garden | finite_volume | 9 | PASS | 0.399 | no |
| rafting | cascading_wave_train | reduced | 9 | PASS | 0.399 | no |
| rafting | cascading_wave_train | finite_volume | 9 | PASS | 0.405 | no |
| rafting | hydraulic_hole_downstream_boil | reduced | 9 | PASS | 0.410 | no |
| rafting | hydraulic_hole_downstream_boil | finite_volume | 9 | PASS | 0.399 | no |
| rafting | lateral_wave | reduced | 9 | PASS | 0.401 | no |
| rafting | lateral_wave | finite_volume | 9 | PASS | 0.399 | no |
| rafting | eddy_line_shear | reduced | 9 | PASS | 0.399 | no |
| rafting | eddy_line_shear | finite_volume | 9 | PASS | 0.807 | no |
| rafting | shallow_shelf | reduced | 9 | PASS | 0.514 | no |
| rafting | shallow_shelf | finite_volume | 9 | PASS | 0.813 | no |
| real_world | south_fork_low_runnable | reduced | 9 | PASS | 0.248 | no |
| real_world | south_fork_low_runnable | finite_volume | 9 | PASS | 0.312 | no |
| real_world | south_fork_median_runnable | reduced | 9 | PASS | 0.248 | no |
| real_world | south_fork_median_runnable | finite_volume | 9 | PASS | 0.314 | no |
| real_world | south_fork_high_runnable | reduced | 9 | PASS | 0.251 | no |
| real_world | south_fork_high_runnable | finite_volume | 9 | PASS | 0.314 | no |
| cascading | south_fork_cascading_low_runnable | reduced | 9 | PASS | 0.325 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_low_runnable | finite_volume | 9 | FAIL | 0.477 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | reduced | 9 | PASS | 0.325 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_median_runnable | finite_volume | 9 | FAIL | 0.487 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | reduced | 9 | PASS | 0.325 | 7 reaches / 1 drops |
| cascading | south_fork_cascading_high_runnable | finite_volume | 9 | FAIL | 0.486 | 7 reaches / 1 drops |
