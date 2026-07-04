# Milestone 16 Raft Coupling Validation

Schema: `raftsim.milestone16.raft_coupling_validation.v0`

Decision: **PASS**

Comparisons: 50

| Suite | Gate scenario | Mode | Case | Status | Ref outcome | C++ outcome | Force ratio | Velocity delta |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| rafting | boulder_garden | reduced | boulder_impacts | PASS | scraped | scraped | 0.000 | 0.000 |
| rafting | boulder_garden | finite_volume | boulder_impacts | PASS | scraped | scraped | 0.000 | 0.000 |
| rafting | cascading_wave_train | reduced | wave_train_surf_flush | PASS | surf | surf | 0.000 | 0.000 |
| rafting | cascading_wave_train | finite_volume | wave_train_surf_flush | PASS | surf | surf | 0.000 | 0.000 |
| rafting | hydraulic_hole_downstream_boil | reduced | hydraulic_hole_surf_flush | PASS | flush | flush | 0.000 | 0.000 |
| rafting | hydraulic_hole_downstream_boil | reduced | downstream_boil_recovery | PASS | upwelling | upwelling | 0.000 | 0.000 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | hydraulic_hole_surf_flush | PASS | flush | flush | 0.000 | 0.000 |
| rafting | hydraulic_hole_downstream_boil | finite_volume | downstream_boil_recovery | PASS | upwelling | upwelling | 0.000 | 0.000 |
| rafting | lateral_wave | reduced | lateral_wave_side_impulse | PASS | clear | clear | 0.000 | 0.000 |
| rafting | lateral_wave | finite_volume | lateral_wave_side_impulse | PASS | clear | clear | 0.000 | 0.000 |
| rafting | eddy_line_shear | reduced | eddy_recovery | PASS | eddy_coupled | eddy_coupled | 0.000 | 0.000 |
| rafting | eddy_line_shear | finite_volume | eddy_recovery | PASS | eddy_coupled | eddy_coupled | 0.000 | 0.000 |
| rafting | shallow_shelf | reduced | shallow_shelf_pivot_release | PASS | pivoted | pivoted | 0.000 | 0.000 |
| rafting | shallow_shelf | finite_volume | shallow_shelf_pivot_release | PASS | pivoted | pivoted | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | reduced | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | reduced | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | reduced | hydraulic_hole_surf_flush | PASS | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | reduced | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | reduced | boulder_garden_impacts | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | reduced | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | hydraulic_hole_surf_flush | PASS | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | boulder_garden_impacts | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_low_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | hydraulic_hole_surf_flush | PASS | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | boulder_garden_impacts | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | reduced | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | hydraulic_hole_surf_flush | PASS | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | boulder_garden_impacts | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_median_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | hydraulic_hole_surf_flush | PASS | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | boulder_garden_impacts | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | reduced | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | pool_entry | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | drop_entry | PASS | flushed | flushed | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | hydraulic_hole_surf_flush | PASS | stalled | stalled | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | eddy_recovery | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | boulder_garden_impacts | PASS | clear | clear | 0.000 | 0.000 |
| cascading | south_fork_cascading_high_runnable | finite_volume | transition_boundary_crossing | PASS | flushed | flushed | 0.000 | 0.000 |

## Notes

- Distinct pin/release closure evidence is tracked separately in the Milestone 18 pin_release_fixture report; this report only compares raft coupling over GeoClaw-derived and C++ water fields.
