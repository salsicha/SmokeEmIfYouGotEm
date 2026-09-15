# Source-resolved timestep refinement

September 14, 2026. Research validation of the opt-in nondispersive source-front
candidate; not full rational dynamics, native water or scene acceptance.

The earlier event-network controls conserve frozen transfers, and the evolving
candidate reassembles depth-dependent fluxes between steps. Neither fact proves
finite-time accuracy. Compare successive states at the **same physical horizon**,
starting each resolution from the same original water and physical momentum.
The new audit uses N, 2N and 4N fixed steps. A rejection stops that resolution;
it does not trigger a retry or a smaller replacement production timestep.
Incomplete runs cannot contribute endpoint differences or convergence ratios.

Region indices cannot identify corresponding water across resolutions because
regions activate, split and exhaust. The audit instead integrates the existing
storage over original source triangles, grouped by (parent cell, source ID),
and retains both physical momentum components using each region's velocity.
Storage inversion error is reported, not removed by renormalization. It also
reports parent-cell differences separately. A regression deliberately relocates
water between two source triangles with identical parent totals: parent error
is zero while source error remains nonzero. Thus a coarser aggregation cannot
silently qualify the more detailed reconstruction.

The tool reports L1 differences and adjacent-difference ratios. Zero differences
do not establish an observed order and produce a null ratio. Even decreasing
differences are self-consistency evidence, not proof of the correct continuum
model, spatial convergence, open boundaries or measured river behavior.

## Independent controls

Fifteen new tests cover source ordering, source versus parent correspondence,
volume and physical momentum reconstruction, requested scope validation, rejection
without retry, equal-horizon evolving dam/moving-water cases, and a first-order
moving-water refinement control, and actual-source CLI scope validation. The 0.04-second moving-water comparison uses
4/8/16 steps. Its water difference ratio is 2.0912; the two momentum ratios are
approximately 2.159 and 2.137. The dry-front comparison on the same interval also
completes, but its coarse source-water ratio 2.913 is not claimed to establish
an asymptotic order. Its parent-water ratio 5.877 differs materially, illustrating
why source-resolved checks matter.

Six successive 20ms steps also preserve a partially wet lake at rest over sloping
terrain, in both legacy and exact-source geometry, with source-water and both
momentum changes below 1e-12 and roundoff-level velocities. This checks repeated
body/pressure timing, not a moving-terrain or full nonlinear model.

The full focused suite reports **275 PASS / 1 retained geometry FAIL** in 19.23s.
Record: `tmp/subcell-time-refinement-controls-v3-20260914.xml`. The retained energy
selection is **25 PASS / 12 FAIL**, recorded in
`tmp/subcell-time-refinement-retained-v1-20260914.xml`. No existing test
or gate was relaxed. All 464 protected source, map, actor and prior runtime
evidence hashes were checked unchanged. Actual-source equal-horizon refinement
is required next; synthetic results cannot qualify the South Fork state.

## Completed two-second actual-source history

The existing 100-step run finished with exit 0 before its source files were
changed. All 42 recorded hashes matched at completion. It advanced 2.0 seconds
at fixed 20ms steps, ending with 425 regions and 2,173 exact regional exhaustion
events. Maximum stored-state speed over all candidates was 5.300635546245253 m/s
at step 1; final maximum speed was 1.7602920315029162 m/s. Neither previously
rejected 826/160 m/s spike recurred. Maximum per-step mass error was
2.2737367544323206e-13; maximum momentum error was 1.4797052472204086e-12.
Every base/full energy change was negative; the least-negative were
-3.464493847952326 and -2.5036158664133836 respectively.

Report: `tmp/south-fork-event-history-100-v3-20260914.json`, SHA-256
`a07e739f19156d417241580f1d61e1312555a36bb3fe04908b527503d3a5087d`.
This is a closed, reflecting-boundary nondispersive candidate. Decaying velocity
and energy are not a measured river current, correct wave dispersion or proof
of temporal accuracy. The completed report's audit-driver hash predates the
new refinement CLI; its physical solver sources were not changed in this turn.

The actual-source driver now supports the comparison directly and includes the
new module in its source lock (43 hashes). Full per-step records remain in JSON;
console output is compact, avoiding the prior 424,968-token history dump.
The dispatched comparison uses the original state, not the two-second endpoint:

```text
python -B physics/scripts/audit_south_fork_subcell_kinetic_geometry.py --atlas tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json --report tmp/south-fork-source-time-refinement-v1-20260914.json --exact-pool-geometry --pool-refinement-steps 20 --pool-refinement-levels 3 --pool-history-scheme coupled-events
```

It requests 20/40/80 steps of 20/10/5ms over the same 0.4 seconds. Its result
is pending, not accepted or inferred from the completed two-second run. Even
successful completion does not set the time-accuracy or full-model flag: source
differences and every intermediate velocity still require inspection.

## Delivery limitations

This adds no native solver switch or visual/performance improvement. Ordinary
South Fork remains the scenario; Troublemaker remains a rapid inside it.
Depth-dependent/full rational transport and terrain forces, wet-front and
open-boundary accuracy, native/shared-surface integration, convincing breaking
and froth, 30 FPS, later rivers, crew and release work remain required.
