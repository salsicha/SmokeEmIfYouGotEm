# Milestone 16 Regression Promotion

Schema: `raftsim.milestone16.regression_promotion.v0`

Decision: **PASS**

Promoted entries: 40

| Category | Gate scenario | Mode | Case | Artifact |
| --- | --- | --- | --- | --- |
| geoclaw_cpp | flat_pool | reduced | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_flat/reduced |
| geoclaw_cpp | flat_pool | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_flat/finite_volume |
| geoclaw_cpp | uniform_channel | reduced | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_uniform/reduced |
| geoclaw_cpp | uniform_channel | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_uniform/finite_volume |
| geoclaw_cpp | dam_break | reduced | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_dam/reduced |
| geoclaw_cpp | dam_break | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_dam/finite_volume |
| geoclaw_cpp | bed_step | reduced | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_step/reduced |
| geoclaw_cpp | bed_step | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_step/finite_volume |
| geoclaw_cpp | constriction | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_constrict/finite_volume |
| geoclaw_cpp | wet_dry_shoreline | reduced | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_wetdry/reduced |
| geoclaw_cpp | wet_dry_shoreline | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_wetdry/finite_volume |
| geoclaw_cpp | sloping_manning_channel | reduced | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_slope/reduced |
| geoclaw_cpp | sloping_manning_channel | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_slope/finite_volume |
| geoclaw_cpp | drop_ledge | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/c_drop/finite_volume |
| geoclaw_cpp | south_fork_cascading_low_runnable | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/cg_low/finite_volume |
| geoclaw_cpp | south_fork_cascading_median_runnable | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/cg_med/finite_volume |
| geoclaw_cpp | south_fork_cascading_high_runnable | finite_volume | n/a | regression_fixtures/milestone16/geoclaw_cpp/cg_high/finite_volume |
| geometry_validation | wet_dry_shoreline | finite_volume | wet_dry_shoreline | regression_fixtures/milestone16/geometry_validation/wet_dry_shoreline/c_wetdry/finite_volume |
| geometry_validation | wet_dry_shoreline | reduced | wet_dry_shoreline | regression_fixtures/milestone16/geometry_validation/wet_dry_shoreline/c_wetdry/reduced |
| geometry_validation | bed_step | finite_volume | bed_step | regression_fixtures/milestone16/geometry_validation/bed_step/c_step/finite_volume |
| geometry_validation | constriction | geoclaw_package | constriction | regression_fixtures/milestone16/geometry_validation/constriction/c_constrict |
| geometry_validation | drops_ledges_tailwater | geoclaw_package | drops_ledges_tailwater | regression_fixtures/milestone16/geometry_validation/drops_ledges_tailwater/drops_ledges_tailwater |
| geometry_validation | south_fork_cascading_low_runnable | geoclaw_package | stitched_reach_drop_handoffs | regression_fixtures/milestone16/geometry_validation/stitched_reach_drop_handoffs/cg_low |
| geometry_validation | south_fork_cascading_median_runnable | geoclaw_package | stitched_reach_drop_handoffs | regression_fixtures/milestone16/geometry_validation/stitched_reach_drop_handoffs/cg_med |
| geometry_validation | south_fork_cascading_high_runnable | geoclaw_package | stitched_reach_drop_handoffs | regression_fixtures/milestone16/geometry_validation/stitched_reach_drop_handoffs/cg_high |
| raft_coupling | hydraulic_hole_downstream_boil | finite_volume | downstream_boil_recovery | regression_fixtures/milestone16/raft_coupling/r_hole/finite_volume/downstream_boil_recovery |
| raft_coupling | eddy_line_shear | reduced | eddy_recovery | regression_fixtures/milestone16/raft_coupling/r_eddy/reduced/eddy_recovery |
| raft_coupling | shallow_shelf | reduced | shallow_shelf_pivot_release | regression_fixtures/milestone16/raft_coupling/r_shelf/reduced/shallow_shelf_pivot_release |
| raft_coupling | south_fork_cascading_low_runnable | finite_volume | pool_entry | regression_fixtures/milestone16/raft_coupling/cg_low/finite_volume/pool_entry |
| raft_coupling | south_fork_cascading_low_runnable | finite_volume | drop_entry | regression_fixtures/milestone16/raft_coupling/cg_low/finite_volume/drop_entry |
| raft_coupling | south_fork_cascading_low_runnable | finite_volume | eddy_recovery | regression_fixtures/milestone16/raft_coupling/cg_low/finite_volume/eddy_recovery |
| raft_coupling | south_fork_cascading_low_runnable | finite_volume | transition_boundary_crossing | regression_fixtures/milestone16/raft_coupling/cg_low/finite_volume/transition_boundary_crossing |
| raft_coupling | south_fork_cascading_median_runnable | finite_volume | pool_entry | regression_fixtures/milestone16/raft_coupling/cg_med/finite_volume/pool_entry |
| raft_coupling | south_fork_cascading_median_runnable | finite_volume | drop_entry | regression_fixtures/milestone16/raft_coupling/cg_med/finite_volume/drop_entry |
| raft_coupling | south_fork_cascading_median_runnable | finite_volume | eddy_recovery | regression_fixtures/milestone16/raft_coupling/cg_med/finite_volume/eddy_recovery |
| raft_coupling | south_fork_cascading_median_runnable | finite_volume | transition_boundary_crossing | regression_fixtures/milestone16/raft_coupling/cg_med/finite_volume/transition_boundary_crossing |
| raft_coupling | south_fork_cascading_high_runnable | finite_volume | pool_entry | regression_fixtures/milestone16/raft_coupling/cg_high/finite_volume/pool_entry |
| raft_coupling | south_fork_cascading_high_runnable | finite_volume | drop_entry | regression_fixtures/milestone16/raft_coupling/cg_high/finite_volume/drop_entry |
| raft_coupling | south_fork_cascading_high_runnable | finite_volume | eddy_recovery | regression_fixtures/milestone16/raft_coupling/cg_high/finite_volume/eddy_recovery |
| raft_coupling | south_fork_cascading_high_runnable | finite_volume | transition_boundary_crossing | regression_fixtures/milestone16/raft_coupling/cg_high/finite_volume/transition_boundary_crossing |

## Notes

- Only passing GeoClaw/C++ threshold runs were copied as regression fixtures.
- Passing stitched reach/drop geometry checks were promoted as artifact manifests that preserve seam-visible handoff diagnostics.
- Passing raft-coupling cases were promoted as artifact manifests that point back to the generated frame outputs.
