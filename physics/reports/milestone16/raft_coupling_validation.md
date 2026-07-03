# Milestone 16 Raft Coupling Validation

Schema: `raftsim.milestone16.raft_coupling_validation.v0`

Decision: **BLOCKED**

Comparisons: 50

| Suite | Gate scenario | Mode | Case | Status | Ref outcome | C++ outcome | Force ratio | Velocity delta |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| rafting | boulder_garden | reduced | boulder_impacts | FAIL | scraped | scraped | 0.000 | 0.000 |
| rafting | boulder_garden | finite_volume | boulder_impacts | FAIL | scraped | scraped | 0.578 | 0.094 |
| rafting | cascading_wave_train | reduced | wave_train_surf_flush | FAIL | surf | clear | 1.223 | 0.200 |
| rafting | cascading_wave_train | finite_volume | wave_train_surf_flush | FAIL | surf | clear | 0.427 | 0.070 |
| rafting | hydraulic_hole_downstream_boil | reduced | hydraulic_hole_surf_flush | FAIL | flush | flush | 0.386 | 0.063 |
| rafting | hydraulic_hole_downstream_boil | reduced | downstream_boil_recovery | FAIL | upwelling | flat | 2.403 | 0.393 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | hydraulic_hole_surf_flush | FAIL | flush | flush | 0.303 | 0.050 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | downstream_boil_recovery | PASS | upwelling | upwelling | 0.541 | 0.088 |
| rafting | lateral_wave | reduced | lateral_wave_side_impulse | FAIL | clear | clear | 0.402 | 0.066 |
| rafting | lateral_wave | finite_volume | lateral_wave_side_impulse | FAIL | clear | side_surf | 2.492 | 0.408 |
| rafting | eddy_line_shear | reduced | eddy_recovery | PASS | eddy_coupled | eddy_coupled | 0.521 | 0.085 |
| rafting | eddy_line_shear | finite_volume | eddy_recovery | FAIL | eddy_coupled | eddy_coupled | 0.339 | 0.055 |
| rafting | shallow_shelf | reduced | shallow_shelf_pivot_release | PASS | pivoted | pivoted | 0.326 | 0.053 |
| rafting | shallow_shelf | finite_volume | shallow_shelf_pivot_release | FAIL | pivoted | pivoted | 2.757 | 0.451 |
| cascading | south_fork_cascading_low_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.005 | 0.328 |
| cascading | south_fork_cascading_low_runnable | reduced | drop_entry | FAIL | flushed | stalled | 2.484 | 0.406 |
| cascading | south_fork_cascading_low_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 4.276 | 0.699 |
| cascading | south_fork_cascading_low_runnable | reduced | eddy_recovery | FAIL | clear | clear | 1.965 | 0.321 |
| cascading | south_fork_cascading_low_runnable | reduced | boulder_garden_impacts | FAIL | clear | grounded | 18.056 | 2.952 |
| cascading | south_fork_cascading_low_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 2.639 | 0.432 |
| cascading | south_fork_cascading_low_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | boulder_garden_impacts | FAIL | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.003 | 0.328 |
| cascading | south_fork_cascading_median_runnable | reduced | drop_entry | FAIL | flushed | stalled | 2.260 | 0.370 |
| cascading | south_fork_cascading_median_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 5.191 | 0.849 |
| cascading | south_fork_cascading_median_runnable | reduced | eddy_recovery | FAIL | clear | clear | 2.214 | 0.362 |
| cascading | south_fork_cascading_median_runnable | reduced | boulder_garden_impacts | FAIL | clear | grounded | 5.314 | 0.869 |
| cascading | south_fork_cascading_median_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 3.376 | 0.552 |
| cascading | south_fork_cascading_median_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | boulder_garden_impacts | FAIL | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | pool_entry | FAIL | clear | stalled | 2.050 | 0.335 |
| cascading | south_fork_cascading_high_runnable | reduced | drop_entry | FAIL | flushed | stalled | 2.590 | 0.424 |
| cascading | south_fork_cascading_high_runnable | reduced | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 7.856 | 1.284 |
| cascading | south_fork_cascading_high_runnable | reduced | eddy_recovery | FAIL | clear | clear | 2.395 | 0.392 |
| cascading | south_fork_cascading_high_runnable | reduced | boulder_garden_impacts | FAIL | clear | grounded | 2.848 | 0.466 |
| cascading | south_fork_cascading_high_runnable | reduced | transition_boundary_crossing | FAIL | flushed | stalled | 5.302 | 0.867 |
| cascading | south_fork_cascading_high_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | hydraulic_hole_surf_flush | FAIL | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | boulder_garden_impacts | FAIL | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |

## Notes

- Distinct pin/release closure evidence is tracked separately in the Milestone 18 pin_release_fixture report; this report only compares raft coupling over GeoClaw-derived and C++ water fields.
