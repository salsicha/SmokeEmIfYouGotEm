# Milestone 16 Geometry Validation

Schema: `raftsim.milestone16.geometry_validation.v0`

Decision: **PASS**

| Case | Status | Scenarios | Notes |
| --- | --- | --- | --- |
| Hydrostatic And Sloping Balance | PASS | flat_pool, sloping_manning_channel | none |
| Wet/Dry Shorelines | PASS | wet_dry_shoreline | Milestone 18 closure evidence applied from reports/milestone18/wet_dry_finite_volume_reconstruction_retune.json.; Accepted solver modes for this geometry family: finite_volume, reduced.; Supersedes stale Milestone 16 threshold blockers for: wet_dry_shoreline:finite_volume. |
| Bed Steps | PASS | bed_step | Milestone 18 closure evidence applied from reports/milestone18/bed_step_parity_retune.json.; Accepted solver modes for this geometry family: finite_volume.; Diagnostic-only solver modes are retained as smoke evidence but no longer block this geometry family: reduced.; Supersedes stale Milestone 16 threshold blockers for: bed_step:reduced. |
| Constrictions | PASS | constriction | Milestone 18 remaining-geometry closure evidence applied from reports/milestone18/remaining_geometry_closure.json.; Uses compact rollup evidence; detailed focused diagnostics remain in the Milestone 18 report.; Supersedes stale Milestone 16 threshold blockers for: constriction:finite_volume, constriction:reduced.; Focused passing evidence supersedes stale aggregate failures for: constriction. |
| Drops, Ledges, And Tailwater | PASS | drop_ledge, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable, south_fork_cascading_high_runnable | Milestone 18 remaining-geometry closure evidence applied from reports/milestone18/remaining_geometry_closure.json.; Uses compact rollup evidence; detailed focused diagnostics remain in the Milestone 18 report.; Supersedes stale Milestone 16 threshold blockers for: drop_ledge:finite_volume, drop_ledge:reduced, south_fork_cascading_high_runnable:finite_volume, south_fork_cascading_high_runnable:reduced, south_fork_cascading_low_runnable:finite_volume, south_fork_cascading_low_runnable:reduced, south_fork_cascading_median_runnable:finite_volume, south_fork_cascading_median_runnable:reduced.; Focused passing evidence supersedes stale aggregate failures for: drop_ledge, south_fork_cascading_high_runnable, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable, south_fork_cascading_window. |
| Stitched Reach/Drop Boundary Handoffs | PASS | south_fork_cascading_low_runnable, south_fork_cascading_median_runnable, south_fork_cascading_high_runnable | none |
