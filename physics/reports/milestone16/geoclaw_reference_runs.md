# Milestone 16 GeoClaw Reference Runs

Schema: `raftsim.milestone16.geoclaw_reference_runs.v0`

Decision: **PASS**

Scenario count: 20

| Suite | Gate scenario | Actual scenario | Frames | Full solution | Runtime (s) |
| --- | --- | --- | ---: | --- | ---: |
| canonical | flat_pool | flat_pool_seed_16 | 3 | yes | 1.065 |
| canonical | uniform_channel | uniform_channel_seed_16 | 3 | yes | 1.181 |
| canonical | dam_break | dam_break_seed_16 | 3 | yes | 0.853 |
| canonical | bed_step | bed_step_seed_16 | 3 | yes | 1.015 |
| canonical | constriction | constriction_seed_16 | 3 | yes | 0.949 |
| canonical | wet_dry_shoreline | wet_dry_shoreline_seed_16 | 3 | yes | 0.855 |
| canonical | sloping_manning_channel | sloping_manning_channel_seed_16 | 3 | yes | 0.929 |
| canonical | drop_ledge | drop_ledge_seed_16 | 3 | yes | 0.990 |
| rafting | boulder_garden | boulder_garden_seed_16 | 3 | yes | 1.147 |
| rafting | cascading_wave_train | cascading_wave_train_seed_17 | 3 | yes | 1.223 |
| rafting | hydraulic_hole_downstream_boil | hydraulic_hole_downstream_boil_seed_18 | 3 | yes | 1.226 |
| rafting | lateral_wave | lateral_wave_seed_19 | 3 | yes | 1.194 |
| rafting | eddy_line_shear | eddy_line_shear_seed_20 | 3 | yes | 1.183 |
| rafting | shallow_shelf | shallow_shelf_seed_21 | 3 | yes | 1.148 |
| real_world | south_fork_low_runnable | american_south_fork_chili_bar_to_coloma_low_runnable_beginner | 3 | yes | 1.091 |
| real_world | south_fork_median_runnable | american_south_fork_chili_bar_to_coloma_median_runnable_intermediate | 3 | yes | 0.973 |
| real_world | south_fork_high_runnable | american_south_fork_chili_bar_to_coloma_high_runnable_advanced | 3 | yes | 0.944 |
| cascading | south_fork_cascading_low_runnable | american_south_fork_chili_bar_to_coloma_low_runnable_beginner_cascading | 3 | yes | 0.920 |
| cascading | south_fork_cascading_median_runnable | american_south_fork_chili_bar_to_coloma_median_runnable_intermediate_cascading | 3 | yes | 0.937 |
| cascading | south_fork_cascading_high_runnable | american_south_fork_chili_bar_to_coloma_high_runnable_advanced_cascading | 3 | yes | 0.975 |
