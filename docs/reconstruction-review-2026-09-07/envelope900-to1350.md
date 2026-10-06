# South Fork: bounded 900-to-1350-second continuation

September28 UTC / September27 local. The previous turn made progress by
finishing and rejecting the crest-placement experiment, restoring the runtime
source and rebuilding it successfully. No new appearance improvement is claimed.

## Why advance this state

The completed450-to900s continuation is finite and its artificial bank faces
are dry, but the8-to9km attribution band changed from accumulation to increasing
drainage: +3.01883, -2.67729, -6.45027m3/s over successive150s intervals.
Whole-reach storage is still increasing. Neither a global volume number nor a
single local stage supplies a settled calibration target. Refitting the inferred
bed to those transient levels would confound geometry with initial-state evolution.

Advance the existing900s state by another450s, retaining1050/1200/1350s snapshots.
This is a bounded observation of the next three intervals, not a convergence
claim, an indefinite cook or a change to the installed450s water. Compare local
storage, stage and discharge after terminal audits; do not automatically promote
the latest state or call continued growth a pass. No new terrain or water is added.

## Completed continuation: local drainage persists

Session5446 is TERMINAL exit0; native28956 completed at
2026-09-28T02:10:38.452344Z. Its original wrapper finished every queued audit
and records `final_audits_completed=true`. Do not restart these owners.
All1050/1200/1350s snapshots pass finite/nonnegative-state checks across5,382,400
cells and all86,720 artificial-bank cells remain exactly dry. Maximum per-step
conservation residual is9.48411e-9m3. Final depth/speed maxima are2.998553m and
5.003005m/s; no clipping or state repair was introduced.

Troublemaker's nearest-route8..9km storage rates are-7.957974,-7.710275 and
-6.272571m3/s in900..1050,1050..1200 and1200..1350 respectively. Drainage is now
easing, but remains substantial. The final interval's common-wet median stage
change is-0.020748m. Over the full450s interval the band loses3,291.122971m3,
with common-wet median stage change-0.062744m. These are attribution regions,
not cross-section fluxes; do not label the band settled or fit its inferred bed
to this transient stage.

Whole-domain final outflow44.442450m3/s is closer to inflow45.306955m3/s,
but that aggregate does not eliminate opposing regional storage changes.
The discharge/bed report retains1,050 of6,782 bins with surface discrepancy
over0.25m and a0.963627 cooked-wet fraction of the captured mask. Those comparisons
are not a new measurement of discharge or underwater geometry. No fields are
promoted: normal v14 still uses the450s v8 bundle.

Reports: `tmp/troublemaker-envelope{1050,1200,1350}-{state,banks}-v1-20260928.json`,
`tmp/troublemaker-envelope1350-storage-v1-20260928.json`, and
`tmp/troublemaker-envelope1350-analysis-v1-20260928/report.json`. The durable
owner receipt below binds each state/bank report by hash. The already-owned
v14 validator11644 has advanced to normal Boot/menu profiling after the owner
exited; motion owner32388 remains queued behind validation. No new cook is
started while these actual-game checks run.

Storage-report SHA256:
`22f5c4cc87f56e74e2d7cc66970dca055830f24f49181a7c4819ee68e9a496f4`.
Discharge/bed-report SHA256:
`3945af928c348cd949b6dc2e6df9e0f0a18ff29b6aa29d4c1e1ed8ab12cf4f20`.

## Verified preparation and original owner

The existing restart preparer copied the original completed900s h/u/v fields
without resetting or smoothing them. Its source manifest is
`0da8f20062847aea0097084f0dab7791961ebeef2972d7eb39e91a9a4c3e7657`;
the new input manifest is
`cfa1e71d2b749b5d9210321b299c058107308fe3c7dc8d08e7ca5dbdd6647830`.
The original geometry manifest and immutable source-packet identity were checked
before launch. Available disk space was approximately18.3GB before preparing the
input; the owner additionally requires3GiB free before launching the native cook.

- Recipe: `tmp/continue-envelope900to1350-v1-20260928.py`.
- Durable receipt: `tmp/troublemaker-envelope900to1350-process-v1-20260928.json`.
- Input: `tmp/troublemaker-envelope-restart900-input-v1-20260928/manifest.json`.
- Output: `tmp/troublemaker-envelope900to1350-v1-20260928`.
- Live session5446, wrapper33852, native28956; start
  `2026-09-28T00:55:05.682548+00:00`.
- Same executable SHA256
  `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`;
  9,000 steps at0.05s, snapshots every3,000 steps, eight lanes,841 packages.

The independent native frame-zero restart audit has already PASSED:
all5,382,400 retained cells bit-exact, zero added cells/water, equal source/native
time899.9999999997292s, volume difference4.6566e-10m3 from summation order.
Grid, bed, roughness, boundaries, other physical settings, features and probes
remain unchanged. Report:
`tmp/troublemaker-envelope900to1350-restart-v1-20260928.json`.
This verifies restart identity, not future stability or settled flow.

The owner queues state AND artificial-bank audits for all three new snapshots,
regional storage analysis across0/3000/6000/9000, and final discharge/bed analysis.
It records audit failure separately from native completion. Observe this same
process/receipt; do not restart merely because a tool observation expires.
Avoid simultaneous game timing while it runs. No other build/cook/engine job
was live at launch.

## Breaking-model constraints retained

Current source inspection confirms the large shared crest is still a static
asymmetric profile; the roller velocity addition is presentation foam transport,
not depth-resolved recirculation. The existing stronger mean-strain/nonlinear
experiments have documented failures and remain disabled. Increasing noise or
moving a fixed profile does not supply the missing nonlinear breaking dynamics.

A primary literature cross-check found measurements of strong free-surface
fluctuations in the upstream part of jump rollers, including experiments at
Fr2.1-3.8. Those are controlled flume conditions, not this natural rapid's
observed detector pair nearFr1.66. Their dimensional fluctuation frequencies
cannot be copied into South Fork as measured wave motion. Sources:
[Characterisation of free-surface turbulence in hydraulic jump roller at low inflow Froude number](https://doi.org/10.1016/j.flowmeasinst.2025.103107)
and [Free-surface fluctuations in hydraulic jumps: Experimental observations](https://doi.org/10.1016/j.expthermflusci.2009.06.003).
These pages were consulted as technical references only. No figures, footage,
datasets or paper text were incorporated into game assets; no new shipping
license or measured South Fork bathymetry is asserted.

South Fork remains first unfinished. Dynamic breaking, holes, collision,
shoreline continuity, simulation-clock capacity and the20FPS/p95<=50ms/no>100ms
frame gates remain open, as do the complete queued rivers and other goal items.
