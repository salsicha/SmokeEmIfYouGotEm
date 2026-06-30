# Milestone 16 Geometry Validation

Schema: `raftsim.milestone16.geometry_validation.v0`

Decision: **BLOCKED**

| Case | Status | Scenarios | Notes |
| --- | --- | --- | --- |
| Hydrostatic And Sloping Balance | PASS | flat_pool, sloping_manning_channel | none |
| Wet/Dry Shorelines | FAIL | wet_dry_shoreline | Threshold failures remain in: wet_dry_shoreline. |
| Bed Steps | FAIL | bed_step | Threshold failures remain in: bed_step. |
| Constrictions | FAIL | constriction | Threshold failures remain in: constriction. |
| Drops, Ledges, And Tailwater | FAIL | drop_ledge, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable, south_fork_cascading_high_runnable | Threshold failures remain in: drop_ledge, south_fork_cascading_high_runnable, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable. |
| Stitched Reach/Drop Boundary Handoffs | PASS | south_fork_cascading_low_runnable, south_fork_cascading_median_runnable, south_fork_cascading_high_runnable | none |
