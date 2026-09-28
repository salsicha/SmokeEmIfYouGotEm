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

## Verified preparation and live owner

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
