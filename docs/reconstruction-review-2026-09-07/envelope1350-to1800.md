# South Fork: bounded 1350-to-1800-second continuation

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
