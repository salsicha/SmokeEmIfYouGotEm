# South Fork: bounded 1350-to-1800-second continuation

## Terminal result (supersedes live-owner notes below)

September28 UTC: session14006 exited0. Native39708 finished at05:25:13.601689UTC
after5704.7672 wall seconds; wrapper33552 completed the final audits and exited.
Receipt `completed=true`, `native_exit_code=0`, `final_audits_completed=true`.
All six checkpoint report hashes were independently rechecked against the
receipt:1500/1650/1800s state checks PASS on5,382,400cells; all86,720 artificial
bank-face cells remain exactly dry at each checkpoint. Final maximum depth
3.0417565m, speed5.0040558m/s; maximum step conservation residual
1.19599215e-8m3. These are numerical state/boundary checks, not realism acceptance.

Troublemaker's nearest-route8..9km band continues to lose storage, but more
slowly. These are regional storage rates, NOT cross-section discharge:

| Interval (s) | Storage rate (m3/s) | Common-wet median stage change (m) |
| --- | ---: | ---: |
| 1350–1500 | -4.219076 | -0.016841 |
| 1500–1650 | -2.191877 | -0.010761 |
| 1650–1800 | -0.686734 | -0.005067 |

The whole domain gains769.980558m3 over450s, matching integrated exterior
volume within3.41e-13m3 in the storage audit. Last-interval whole-domain storage
gain is2.541457m3/s; instantaneous final inflow45.306955 versus outflow42.147057
m3/s. Local drainage easing does not demonstrate whole-reach equilibrium.

Captured-mask comparison covers1,632,290cells,96.3350% wet coverage, signed
median surface error+0.021535m and median absolute error0.089235m. However,
1127/6782station bins exceed0.25m surface error (previous1350s report:1050),
and only3534bins satisfy the existing0.85–1.25 discharge-ratio diagnostic.
Largest listed bin8348 has approximately0.66m error despite0.96ratio. Do not
fit inferred bathymetry to these still-changing stages or promote on aggregate
median error. No source capture, bed, boundary, rendered or collision geometry
was changed by this continuation. Generated `bias.npz` is diagnostic only.

Authoritative receipts (SHA256):

- Owner `tmp/troublemaker-envelope1350to1800-process-v1-20260928.json`:
  `3d59d7c7b4b1a0843c9ed469b63f8639ffced56f3a2f4c7937d4c9e772a32233`.
- Storage `tmp/troublemaker-envelope1800-storage-v1-20260928.json`:
  `dcacfea24f95fcb4649ba6001befc7c627a33b553c69581f7530ee46b715f643`.
- Comparison `tmp/troublemaker-envelope1800-analysis-v1-20260928/report.json`:
  `0219f60e192284608c60f2440f838691cacd0188af5fa47646d17fe6e6ded920`.

No further cook was launched. Normal v15r2 retains450s v8 fields. The existing
publication owner4504/session60320 has advanced to `isolated_8310_capture`;
spray-build owner15924/session71849 still waits for that capture. Do not overlap
new hydraulic work with its timing. Next inspect publication attribution and
the queued spray native result, then actual motion/cost and normal playable
delivery. Settling, geometry consistency and realistic breaking remain open.

## Historical launch record

September28 UTC. Hydraulic work in progress, NOT a new playable or visual
delivery. The preceding goal turn completed v15r2 packaging, normal launch,
motion review and isolated timing; both rapid timing gates still fail. That
normal game retains450s v8 fields and the repaired hydraulic normal.

## Purpose and preserved scope

The completed900-to1350s run's Troublemaker8..9km storage losses eased from
-7.957974 to-7.710275 to-6.272571m3/s. They remain substantial; the final150s
common-wet median stage change is-0.020748m. Whole-domain outflow nearing
inflow does not cancel these local transients. Continue the exact1350s state
another450s, retaining1500/1650/1800s, to evaluate whether drainage continues
to decay or persistent geometry/boundary problems emerge. This is not an
indefinite cook, equilibrium declaration or authorization to promote fields.
See [prior terminal state and audits](envelope900-to1350.md).

No captured source, rendered/collision geometry, inferred bed, discharge,
roughness, numerical step, lanes or boundary is changed. No context cells or
water are added. The source-state preparation verifies serialized h/u/v and
the launcher rechecks all previous checkpoint-report hashes and original
1350s array hashes before launch. The packet/geometry identity gate is retained.

## One live owner

- Session14006, Python wrapper33552, native cook39708.
- Start UTC `2026-09-28T03:50:06.466000+00:00`.
- Recipe: `tmp/continue-envelope1350to1800-v1-20260928.py`.
- Receipt: `tmp/troublemaker-envelope1350to1800-process-v1-20260928.json`.
- Input: `tmp/troublemaker-envelope-restart1350-input-v1-20260928/manifest.json`.
- Output: `tmp/troublemaker-envelope1350to1800-v1-20260928`.
- Input SHA256: `b01c7d0f2e65782e564830582a57f0c8a9f83b58bf781463b39f43b364505f8d`.
- Same native executable SHA256:
  `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
- 9,000 steps at0.05s, snapshots every3,000 steps, eight lanes,841 packages.

Engine/build/cook inventory was empty before launch. Approximately9.9GB was
free before input preparation; the owner requires3GiB free before native start.
One pre-launch attempt stopped on a missing SciPy import before starting any
solver or creating an owner receipt. The hash helper now uses hashlib directly;
the existing local SciPy1.18.1/NumPy2.5.3 dependencies and storage analyzer import
were verified before the successful launch. No package installation or rerun of
the already-completed previous solve occurred.

Independent native frame-zero restart audit PASSES: all5,382,400 original
cells bit-exact, zero new cells/water, matching time1349.99999999932s, and
9.313225746154785e-10m3 summation-order volume difference. All original grid,
bed, roughness, boundaries, other physical settings, features and probes are
unchanged. Receipt: `tmp/troublemaker-envelope1350to1800-restart-v1-20260928.json`.
Actual PID39708 was observed advancing beyond1351s; final results are pending.

The same owner queues finite/nonnegative state AND artificial-bank audits at
all three checkpoints, regional storage analysis across0/3000/6000/9000 and
the final captured-surface/discharge-bed comparison. Native completion and
final audit completion are recorded separately. Observe this SAME owner;
do not launch duplicates or infer termination from a tool observation timeout.
Avoid simultaneous game timing. No fields will be installed automatically.

## Breaking-water work remains

Source review confirms the existing distinction: the large shared crest is a
static asymmetric profile; roller return is a presentation-foam approximation,
not a depth-resolved circulation model. The GPU detail uses captured mean flow
and a persistent perturbation model. Rewiring an authored return velocity into
that hydraulic flow would not supply the missing conservative breaking law.
Prior optical/characteristic trials remain rejected; no new shader or solver
switch was enabled. This continuation supplies a less-transient hydraulic
baseline, not overturning geometry or a solution to flat foam.

Next inspect terminal regional changes without fitting inferred bathymetry to
unsettled stage. Dynamic breaking, holes, collision, shoreline/surface
continuity, rapid20FPS performance and all reconstruction/release requirements
remain open. South Fork stays first; Colorado, Pacuare and Futaleufu stay queued.
