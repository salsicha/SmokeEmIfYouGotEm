# Milestone 16 Raft Coupling Validation

Schema: `raftsim.milestone16.raft_coupling_validation.v0`

Decision: **BLOCKED**

Comparisons: 50

| Suite | Gate scenario | Mode | Case | Status | Ref outcome | C++ outcome | Force ratio | Velocity delta |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| rafting | boulder_garden | reduced | boulder_impacts | FAIL | scraped | scraped | 1.562 | 0.255 |
| rafting | boulder_garden | finite_volume | boulder_impacts | FAIL | scraped | scraped | 1.440 | 0.235 |
| rafting | cascading_wave_train | reduced | wave_train_surf_flush | FAIL | surf | flush | 2.559 | 0.418 |
| rafting | cascading_wave_train | finite_volume | wave_train_surf_flush | FAIL | surf | flush | 2.239 | 0.366 |
| rafting | hydraulic_hole_downstream_boil | reduced | hydraulic_hole_surf_flush | FAIL | flush | flush | 2.075 | 0.339 |
| rafting | hydraulic_hole_downstream_boil | reduced | downstream_boil_recovery | FAIL | upwelling | flat | 3.853 | 0.630 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | hydraulic_hole_surf_flush | FAIL | flush | flush | 4.167 | 0.681 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | downstream_boil_recovery | FAIL | upwelling | flat | 5.438 | 0.889 |
| rafting | lateral_wave | reduced | lateral_wave_side_impulse | FAIL | clear | clear | 0.503 | 0.082 |
| rafting | lateral_wave | finite_volume | lateral_wave_side_impulse | FAIL | clear | side_surf | 2.213 | 0.362 |
| rafting | eddy_line_shear | reduced | eddy_recovery | FAIL | eddy_coupled | eddy_coupled | 1.825 | 0.298 |
| rafting | eddy_line_shear | finite_volume | eddy_recovery | FAIL | eddy_coupled | eddy_coupled | 1.368 | 0.224 |
| rafting | shallow_shelf | reduced | shallow_shelf_pivot_release | PASS | pivoted | pivoted | 0.862 | 0.141 |
| rafting | shallow_shelf | finite_volume | shallow_shelf_pivot_release | FAIL | pivoted | pivoted | 3.034 | 0.496 |
| cascading | south_fork_cascading_low_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.007 | 0.328 |
| cascading | south_fork_cascading_low_runnable | reduced | drop_entry | FAIL | flushed | stalled | 1.873 | 0.306 |
| cascading | south_fork_cascading_low_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 6.074 | 0.993 |
| cascading | south_fork_cascading_low_runnable | reduced | eddy_recovery | FAIL | clear | clear | 2.016 | 0.330 |
| cascading | south_fork_cascading_low_runnable | reduced | boulder_garden_impacts | FAIL | grounded | grounded | 4.098 | 0.670 |
| cascading | south_fork_cascading_low_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 3.157 | 0.516 |
| cascading | south_fork_cascading_low_runnable | finite_volume | pool_entry | FAIL | clear | clear | 1.394 | 0.228 |
| cascading | south_fork_cascading_low_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.296 | 0.048 |
| cascading | south_fork_cascading_low_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 4.236 | 0.693 |
| cascading | south_fork_cascading_low_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.504 | 0.082 |
| cascading | south_fork_cascading_low_runnable | finite_volume | boulder_garden_impacts | FAIL | grounded | clear | 29.207 | 4.775 |
| cascading | south_fork_cascading_low_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.612 | 0.100 |
| cascading | south_fork_cascading_median_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.013 | 0.329 |
| cascading | south_fork_cascading_median_runnable | reduced | drop_entry | FAIL | flushed | stalled | 1.808 | 0.296 |
| cascading | south_fork_cascading_median_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 6.982 | 1.141 |
| cascading | south_fork_cascading_median_runnable | reduced | eddy_recovery | FAIL | clear | clear | 2.411 | 0.394 |
| cascading | south_fork_cascading_median_runnable | reduced | boulder_garden_impacts | FAIL | grounded | grounded | 4.937 | 0.807 |
| cascading | south_fork_cascading_median_runnable | reduced | transition_boundary_crossing | FAIL | flushed | flushed | 3.154 | 0.516 |
| cascading | south_fork_cascading_median_runnable | finite_volume | pool_entry | FAIL | clear | clear | 1.919 | 0.314 |
| cascading | south_fork_cascading_median_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.287 | 0.047 |
| cascading | south_fork_cascading_median_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | flushed | 4.748 | 0.776 |
| cascading | south_fork_cascading_median_runnable | finite_volume | eddy_recovery | FAIL | clear | clear | 1.002 | 0.164 |
| cascading | south_fork_cascading_median_runnable | finite_volume | boulder_garden_impacts | FAIL | grounded | clear | 36.926 | 6.037 |
| cascading | south_fork_cascading_median_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.950 | 0.155 |
| cascading | south_fork_cascading_high_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.023 | 0.331 |
| cascading | south_fork_cascading_high_runnable | reduced | drop_entry | FAIL | flushed | stalled | 1.700 | 0.278 |
| cascading | south_fork_cascading_high_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 9.737 | 1.592 |
| cascading | south_fork_cascading_high_runnable | reduced | eddy_recovery | FAIL | clear | stalled | 2.730 | 0.446 |
| cascading | south_fork_cascading_high_runnable | reduced | boulder_garden_impacts | FAIL | grounded | clear | 5.153 | 0.843 |
| cascading | south_fork_cascading_high_runnable | reduced | transition_boundary_crossing | FAIL | flushed | flushed | 4.481 | 0.733 |
| cascading | south_fork_cascading_high_runnable | finite_volume | pool_entry | FAIL | clear | clear | 2.922 | 0.478 |
| cascading | south_fork_cascading_high_runnable | finite_volume | drop_entry | FAIL | flushed | flushed | 1.659 | 0.271 |
| cascading | south_fork_cascading_high_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | flushed | 6.546 | 1.070 |
| cascading | south_fork_cascading_high_runnable | finite_volume | eddy_recovery | FAIL | clear | clear | 1.805 | 0.295 |
| cascading | south_fork_cascading_high_runnable | finite_volume | boulder_garden_impacts | FAIL | grounded | clear | 46.782 | 7.649 |
| cascading | south_fork_cascading_high_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.766 | 0.125 |

## Notes

- Pin/release remains represented by shallow-shelf pivot/release and high-flow boulder/pin proxies; a distinct strainer or wrap fixture is still needed before production acceptance.
