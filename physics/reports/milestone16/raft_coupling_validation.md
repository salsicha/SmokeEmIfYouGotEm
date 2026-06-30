# Milestone 16 Raft Coupling Validation

Schema: `raftsim.milestone16.raft_coupling_validation.v0`

Decision: **BLOCKED**

Comparisons: 50

| Suite | Gate scenario | Mode | Case | Status | Ref outcome | C++ outcome | Force ratio | Velocity delta |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| rafting | boulder_garden | reduced | boulder_impacts | FAIL | scraped | scraped | 3.314 | 0.542 |
| rafting | boulder_garden | finite_volume | boulder_impacts | FAIL | scraped | scraped | 1.597 | 0.261 |
| rafting | cascading_wave_train | reduced | wave_train_surf_flush | FAIL | surf | clear | 0.896 | 0.146 |
| rafting | cascading_wave_train | finite_volume | wave_train_surf_flush | FAIL | surf | clear | 1.008 | 0.165 |
| rafting | hydraulic_hole_downstream_boil | reduced | hydraulic_hole_surf_flush | FAIL | flush | flush | 0.650 | 0.106 |
| rafting | hydraulic_hole_downstream_boil | reduced | downstream_boil_recovery | FAIL | upwelling | flat | 2.344 | 0.383 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | hydraulic_hole_surf_flush | FAIL | flush | flush | 0.861 | 0.141 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | downstream_boil_recovery | PASS | upwelling | upwelling | 0.614 | 0.100 |
| rafting | lateral_wave | reduced | lateral_wave_side_impulse | FAIL | clear | clear | 0.442 | 0.072 |
| rafting | lateral_wave | finite_volume | lateral_wave_side_impulse | FAIL | clear | side_surf | 2.380 | 0.389 |
| rafting | eddy_line_shear | reduced | eddy_recovery | PASS | eddy_coupled | eddy_coupled | 0.495 | 0.081 |
| rafting | eddy_line_shear | finite_volume | eddy_recovery | FAIL | eddy_coupled | eddy_coupled | 0.623 | 0.102 |
| rafting | shallow_shelf | reduced | shallow_shelf_pivot_release | PASS | pivoted | pivoted | 0.317 | 0.052 |
| rafting | shallow_shelf | finite_volume | shallow_shelf_pivot_release | FAIL | pivoted | pivoted | 2.750 | 0.450 |
| cascading | south_fork_cascading_low_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.005 | 0.328 |
| cascading | south_fork_cascading_low_runnable | reduced | drop_entry | FAIL | flushed | stalled | 2.482 | 0.406 |
| cascading | south_fork_cascading_low_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 4.271 | 0.698 |
| cascading | south_fork_cascading_low_runnable | reduced | eddy_recovery | FAIL | clear | clear | 1.971 | 0.322 |
| cascading | south_fork_cascading_low_runnable | reduced | boulder_garden_impacts | FAIL | grounded | grounded | 4.436 | 0.725 |
| cascading | south_fork_cascading_low_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 2.625 | 0.429 |
| cascading | south_fork_cascading_low_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.833 | 0.136 |
| cascading | south_fork_cascading_low_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.336 | 0.055 |
| cascading | south_fork_cascading_low_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 2.786 | 0.456 |
| cascading | south_fork_cascading_low_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.405 | 0.066 |
| cascading | south_fork_cascading_low_runnable | finite_volume | boulder_garden_impacts | FAIL | grounded | clear | 41.735 | 6.824 |
| cascading | south_fork_cascading_low_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.606 | 0.099 |
| cascading | south_fork_cascading_median_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.006 | 0.328 |
| cascading | south_fork_cascading_median_runnable | reduced | drop_entry | FAIL | flushed | stalled | 2.253 | 0.368 |
| cascading | south_fork_cascading_median_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 5.161 | 0.844 |
| cascading | south_fork_cascading_median_runnable | reduced | eddy_recovery | FAIL | clear | clear | 2.218 | 0.363 |
| cascading | south_fork_cascading_median_runnable | reduced | boulder_garden_impacts | FAIL | grounded | grounded | 4.765 | 0.779 |
| cascading | south_fork_cascading_median_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 3.362 | 0.550 |
| cascading | south_fork_cascading_median_runnable | finite_volume | pool_entry | FAIL | clear | clear | 1.101 | 0.180 |
| cascading | south_fork_cascading_median_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.197 | 0.032 |
| cascading | south_fork_cascading_median_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 2.485 | 0.406 |
| cascading | south_fork_cascading_median_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.537 | 0.088 |
| cascading | south_fork_cascading_median_runnable | finite_volume | boulder_garden_impacts | FAIL | grounded | clear | 50.661 | 8.283 |
| cascading | south_fork_cascading_median_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.212 | 0.035 |
| cascading | south_fork_cascading_high_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.006 | 0.328 |
| cascading | south_fork_cascading_high_runnable | reduced | drop_entry | FAIL | flushed | stalled | 2.595 | 0.424 |
| cascading | south_fork_cascading_high_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 7.817 | 1.278 |
| cascading | south_fork_cascading_high_runnable | reduced | eddy_recovery | FAIL | clear | clear | 2.480 | 0.405 |
| cascading | south_fork_cascading_high_runnable | reduced | boulder_garden_impacts | FAIL | grounded | grounded | 5.153 | 0.843 |
| cascading | south_fork_cascading_high_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 5.290 | 0.865 |
| cascading | south_fork_cascading_high_runnable | finite_volume | pool_entry | FAIL | clear | clear | 1.849 | 0.302 |
| cascading | south_fork_cascading_high_runnable | finite_volume | drop_entry | FAIL | flushed | flushed | 1.216 | 0.199 |
| cascading | south_fork_cascading_high_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 3.601 | 0.589 |
| cascading | south_fork_cascading_high_runnable | finite_volume | eddy_recovery | FAIL | clear | clear | 1.434 | 0.234 |
| cascading | south_fork_cascading_high_runnable | finite_volume | boulder_garden_impacts | FAIL | grounded | clear | 57.970 | 9.478 |
| cascading | south_fork_cascading_high_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.796 | 0.130 |

## Notes

- Distinct pin/release closure evidence is tracked separately in the Milestone 18 pin_release_fixture report; this report only compares raft coupling over GeoClaw-derived and C++ water fields.
