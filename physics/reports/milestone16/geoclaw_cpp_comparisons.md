# Milestone 16 GeoClaw/C++ Comparisons

Schema: `raftsim.milestone16.geoclaw_cpp_comparisons.v1`

Decision: **BLOCKED**

Comparison count: 40

Solver parity: 6 of 40 rows

Reference playback: 34 of 40 rows

Raw threshold checks: 40 of 40 rows

| Suite | Gate scenario | Mode | Parity | Tier | Thresholds | Failing checks | Reach/drop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| canonical | flat_pool | reduced | solver | production_candidate | PASS | none | n/a |
| canonical | flat_pool | finite_volume | solver | production_candidate | PASS | none | n/a |
| canonical | uniform_channel | reduced | reference_playback | production_candidate | PASS | none | n/a |
| canonical | uniform_channel | finite_volume | solver | production_candidate | PASS | none | n/a |
| canonical | dam_break | reduced | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | dam_break | finite_volume | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | bed_step | reduced | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | bed_step | finite_volume | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | constriction | reduced | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | constriction | finite_volume | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | wet_dry_shoreline | reduced | solver | unreal_prototype | PASS | none | n/a |
| canonical | wet_dry_shoreline | finite_volume | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | sloping_manning_channel | reduced | solver | unreal_prototype | PASS | none | n/a |
| canonical | sloping_manning_channel | finite_volume | solver | unreal_prototype | PASS | none | n/a |
| canonical | drop_ledge | reduced | reference_playback | unreal_prototype | PASS | none | n/a |
| canonical | drop_ledge | finite_volume | reference_playback | unreal_prototype | PASS | none | n/a |
| rafting | boulder_garden | reduced | reference_playback | research_accepted | PASS | none | n/a |
| rafting | boulder_garden | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| rafting | cascading_wave_train | reduced | reference_playback | research_accepted | PASS | none | n/a |
| rafting | cascading_wave_train | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| rafting | hydraulic_hole_downstream_boil | reduced | reference_playback | research_accepted | PASS | none | n/a |
| rafting | hydraulic_hole_downstream_boil | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| rafting | lateral_wave | reduced | reference_playback | research_accepted | PASS | none | n/a |
| rafting | lateral_wave | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| rafting | eddy_line_shear | reduced | reference_playback | research_accepted | PASS | none | n/a |
| rafting | eddy_line_shear | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| rafting | shallow_shelf | reduced | reference_playback | research_accepted | PASS | none | n/a |
| rafting | shallow_shelf | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| real_world | south_fork_low_runnable | reduced | reference_playback | research_accepted | PASS | none | n/a |
| real_world | south_fork_low_runnable | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| real_world | south_fork_median_runnable | reduced | reference_playback | research_accepted | PASS | none | n/a |
| real_world | south_fork_median_runnable | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| real_world | south_fork_high_runnable | reduced | reference_playback | research_accepted | PASS | none | n/a |
| real_world | south_fork_high_runnable | finite_volume | reference_playback | research_accepted | PASS | none | n/a |
| cascading | south_fork_cascading_low_runnable | reduced | reference_playback | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_low_runnable | finite_volume | reference_playback | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_median_runnable | reduced | reference_playback | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_median_runnable | finite_volume | reference_playback | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_high_runnable | reduced | reference_playback | unreal_prototype | PASS | none | PASS |
| cascading | south_fork_cascading_high_runnable | finite_volume | reference_playback | unreal_prototype | PASS | none | PASS |
