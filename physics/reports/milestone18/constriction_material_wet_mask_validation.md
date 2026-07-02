# Milestone 18 Constriction Material Wet-Mask Validation

Schema: `raftsim.milestone18.material_wet_mask_validation.v0`

Decision: **RETAIN**

Scenario: `constriction_seed_16`
Comparison manifest: `physics/outputs/m18cmp/c_constrict_material_wet_mask_validation/finite_volume_roe/dual_solver_manifest.json`
Threshold report: `physics/outputs/m18cmp/c_constrict_material_wet_mask_validation/finite_volume_roe/threshold_evaluation.json`

## Summary

- Material wet-depth floor: `0.15` m
- Previous raw wet-mask mismatch fraction: `0.256944`
- Material wet-mask mismatch fraction: `0.00347222`
- Wet-mask threshold: `0.02`
- Feature forcing scale: `0`
- Passing checks after this validation change: wet-mask, cross-section, mass, energy, Froude, feature location, and feature strength.
- Remaining failed checks: field, slope, and point probe.

## Rationale

GeoClaw's final-frame raw wet flags include many very shallow numerical film cells; in the retained constriction comparison, all GeoClaw-only raw-wet cells are below the `0.15` m velocity/Froude depth floor. Milestone 18 focused geometry diagnostics already use the same material depth threshold for wet-width, bank-row, and face-state checks.

The dual-solver wet-mask threshold now scores material wetness from depth using `h >= velocity_depth_floor`, so raw sub-floor films no longer count as geometry failures. This keeps true shoreline/shelf mismatches visible when they are deep enough to affect velocity, Froude, raft sampling, or field errors.

This is not a constriction promotion. The current retained finite-volume Roe lane still fails `field_linf=3.27416`, `slope_linf=0.704668`, and `probe_linf=0.384041` with feature forcing off.
