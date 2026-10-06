# Rebuilt v4 paired-contact check: completed narrow numerical pass

## Completed actual packaged check: September 27, 01:02 UTC

The next idle-host attempt completed successfully using the unchanged v4
inner executable identified below, normal FullReach map, review station
11,520 m, D3D12 at 1280x720, and the existing contact/GPU audit switches.
Fresh output paths, process exit 0, zero logged runtime errors and unchanged
before/after executable hash were verified. No other engine/build/cook was
present at launch; no other session's process was stopped.

The reports share published detail sequence **99**, at world time 10.0659 s.
Of 2,044 submitted-triangle probe points, 2,042 have wet raft support; 541
exercise nonzero detail, up to 6.7461 cm. Maximum numerical support/carrier
difference is **0.0000118977583 cm**, RMS 0.00000519300384 cm. Both remaining
probes are ground-occluded and correctly return dry support despite the raw
hydraulic sample being wet. They lie 0.2328 cm and 8.0698 cm below registered
ground. No support sample is unavailable and no wet support is ground-occluded.
These registered-ground results do not establish surveyed underwater geometry.

The actual uploaded GPU texture passes **4,226 queries**, maximum RGBA error
**2.98023224e-8**, under the existing 1e-6 gate. The fail-closed checker passes
all seven checks. At shutdown detail remained healthy through 81.117 s,
899 paired commits, two presentation holds, 482 flow preparations and zero
PDE backlog. Sparse drift logs show motion and zero reported ground penetration;
they are not a continuous collision test or a new rendered visual review.

Retained raw evidence (copied without alteration):

- [Contact report](south-fork-v4-paired-contact/contact.json), SHA256
  `8480495a2e9665f455b2c211dcfd0bbdda8267187990c697119ba0964ac52abb`.
- [GPU report](south-fork-v4-paired-contact/gpu.json), SHA256
  `0a1b3056f6acbd5635938f6170b965cbb9ee95d94a15bba78f845e06659f20a0`.
- [Process log](south-fork-v4-paired-contact/game.log), SHA256
  `44ecbb69dff1a0c03c4f7dd4bf53ac4952c6a6e6de88b56d5c4913c8753a23f0`.

The 900-frame capture terminates the process after the one-shot audit/readback;
its instrumented timing is not a new FPS qualification. No runtime code,
geometry, field, material, quality setting or installed executable changed.
Normal-menu traversal, swept collision, independent source-ground verification,
shoreline stability, wave appearance and the failed rapid frame budget remain
open. Do not repeat this unchanged snapshot. Return to a distinct CPU
optimization hypothesis or remaining physical reconstruction work.

## Earlier preparation and deferred attempt (historical)

September 27, 2026 UTC. Supporting validation work only; no new gameplay
delivery, performance claim, or river acceptance.

The healthy packaged 11,520 m rapid capture established runtime health and a
failed frame budget, but its short motion capture did not check support-height
agreement with the actual presented GPU water. Before further acceptance,
exercise the existing `RaftSimCarrierContactAudit` and
`RaftSimDetailContactAudit` together in the rebuilt v4 executable. Neither
switch changes solver/geometry quality. They inspect one published snapshot;
they do not prove swept collision, traversal, latency or shoreline stability.

The guarded attempt using output prefix
`tmp/sf-v4-rapid11520-paired-20260927` did **not launch**. Another session's
engine was active (PID 28976, then PID 31068). No test log or reports were
created, and no external process was interrupted. The 900-frame limit was
intended only to allow the ten-second audit and its readback to complete, not
to rerun the unchanged failed FPS qualification.

## Fail-closed report checker

`physics/scripts/audit_paired_water_contact.py` now checks the paired reports:

- same positive published sequence, actual detail present/audited and nonzero
  detail exercised in contact and GPU samples;
- all support probes available, maximum numerical support/carrier difference
  at most 0.001 cm, actual GPU parity below the existing 1e-6 RGBA gate;
- finite, correctly typed metrics and counters, consistent probe populations,
  independent reconstruction of the report's registered-ground occlusion
  counts, and no wet support below that registered ground.

The support threshold is a narrow numerical equivalence screen, not evidence
that inferred underwater ground is physically accurate. Dry ground-occluded
probes are not automatically treated as wet-support failures. Independent
source-triangle checks remain required for ground classification. Sequence
equality alone cannot establish freshness or same-process provenance; the
runner must enforce fresh output paths and retain the healthy process log.

Eight unit tests pass, covering missing fields, malformed/nonfinite values,
sequence mismatch, disabled detail, counters hiding probe changes, legitimate
dry occlusion, wet occlusion and falsified GPU `passed` flags. An older
September 14 contact report lacking per-probe ground data is correctly refused,
not reinterpreted as a current validation pass.

## Reproduction of the completed check

Verify the staged inner executable still has SHA256
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`, check
for active engine/build/cook processes, and use fresh output paths. Run the
normal FullReach map in the existing package at review station 11,520 m with
both audit paths specified; verify exit 0, no runtime errors, unchanged binary
hash, and then run:

```text
python physics/scripts/audit_paired_water_contact.py <fresh-contact.json> <fresh-gpu.json>
```

This direct station check is not normal-menu traversal and cannot supersede
the normal launch evidence or the existing 85.2731 ms p95 rapid failure.
Do not repeat rejected optimization candidates or launch a second engine
alongside the other session. South Fork remains first; later rivers remain
queued in this task.
