# Shared crew command and weight-shift correction

Work in progress, September24 UTC. This is a normal-play command-path correction,
not acceptance of the crew poses, reconstructed river or release.

## Evidence and intended boundary

The pre-change `ARaftSimRaftActor::UpdateCrew` sent high-side/get-down actions
only to physical seat `guide` while animating all attached crew. The flexible
model keys actions by seat; a guide action does not broadcast to passengers.
The guide's independent stroke could also visually override a command while
the guide-only physical shift continued. The dedicated high-side key called a
second guide-only handler whose action could be erased by the next crew tick.

The correction uses each attached avatar's resolved action for its matching
physical seat, clears old actions at rest, and retains the guide-stroke override
in both representations. A standing high-side order must not automatically
swap sides whenever roll crosses zero. A new explicit call can choose a new
side. The dedicated high-side input must publish through the same update path.

[NRS: Guide School, Damage Control](https://community.nrs.com/duct-tape/2019/04/19/guide-school-damage-control/)
is dated April19,2019, with July10,2023 also displayed. It distinguishes seated
leaning, crouched get-down, and cross-raft upper-body transfer for high-side.
This is qualitative animation reference only, not motion capture or surveyed
coordinates. Image shipping rights are not verified; no source image is added
to game assets. The existing tube-standing review target is not thereby accepted.

Physical offsets remain the existing coarse model: high-side0.45m lateral with
0.04m brace drop; get-down0.15m vertical. These are not measured body centers of
mass. Exact body/seat alignment, upstream/downstream posture, continuous step
trajectories, limb/hull clearance and recovery remain open. Excluding a detached
avatar from an action is not proof that the physical seat occupancy/mass has
been removed; that separate lifecycle must still be qualified.
Likewise, the default physical seat positions and visual seat positions still
have different longitudinal layouts and guide offsets. Correct logical seat
participation does not prove that their base centers of mass coincide.

## Validation

Editor v3 rebuild is terminal success (19.72s); Game build is terminal success
(197.45s). Logs: `tmp/crew-command-weight-editor-v3-20260924.log` and
`tmp/crew-command-weight-game-v1-20260924.log`. Existing unrelated uninitialized
`Current`/Chaos float warnings remain. Do not read a build as visual acceptance.

The first native run (`tmp/crew-command-weight-default-native-v1-20260924/`)
fails the new suite, with five existing suites passing. It catches five
dispatched actions but only one participating physical mass: the initial edit
used render ids `paddler_1..N`, while `BuildDefaultCrewSeats` expects physical
ids `passenger_0..N-1`. The corrected mapping retains the five-mass assertion;
the failure artifact is preserved. Process exit0 alone did not establish pass.

Corrected default native v2 passes6/fails0 in8.5066s; contact-review native v1
passes6/fails0 in6.5301s. Both invocations are terminal exit0. Reports:
`tmp/crew-command-weight-default-native-v2-20260924/index.json` and
`tmp/crew-command-weight-review-native-v1-20260924/index.json`.
The new suite exercises the actual `UpdateCrew` and dedicated-key response
handler, checks generated physical actions through the native weight evaluator,
and steps the real flexible adapter. It covers delayed acceptance, both sides,
holding a side across roll reversal, explicit reselection, guide override and
expiry, detached-avatar exclusion, get-down/rest, and immediate persistent
dedicated-key commands. Existing production-body, paddle, vest, planted-foot
and exact support-index suites also pass. This is not river-force calibration
or proof of full-body animated collision clearance.

## Normal launch, motion and cost

All three guarded engine invocations are terminal exit0 with no timeout and
suspend/resume status0 for the exact original cook36692. They use the normal
FullReach map and `south_fork_full_descent` scenario,1280x720, four solver lanes,
and the unchanged solver archive. No contact-review flag, shadow override,
field promotion or nonlinear activation. These are editor-hosted game runs;
the rebuilt Game target is separate, not packaged-release acceptance.

Process receipts in `unreal/Saved/RaftSimValidation/`:

- `south-fork-crew-command-weight-cost-v1-20260924-process.json`
- `south-fork-crew-command-weight-motion-v1-20260924-process.json`
- `south-fork-crew-command-weight-default-cost-v1-20260924-process.json`

Independent900-frame cost runs use confirmed elapsed timing offset1, samples
60–840 inclusive (781 samples), unchanged30FPS/p9533.333333ms gate:

| Input | Mean frame ms | p95 ms | Max ms | Short first-pool gate |
| --- | ---: | ---: | ---: | --- |
| Normal high-side command |25.403031|34.7539|40.4166|FAIL |
| Ordinary launch, no command |23.228491|31.4449|38.4547|PASS |

Reports: `tmp/crew-command-weight-frame-v1-20260924.json` and
`tmp/crew-command-weight-default-frame-v1-20260924.json`. Their source CSV hashes:
`89c511d75c14f33e62458aeff11471092ec1186fce7e5e3036afbd7d6f6bf405` and
`a8d6ba71bf20fa6314e1a64bbc66da6e2d32de5bc6c44a6fb385f82c79db0a79`.
The ordinary run has9,000 solved/attempted foot poses,8,995 cache hits and10
support queries. It does not qualify high-side foot placement. These different
input workloads are not an isolated speedup comparison; neither establishes
rapid/full-route performance. The high-side workload remains over budget.

The motion run confirms the normal high-side command and produces24 distinct
stills plus `unreal/Saved/VideoCaptures/RaftSim_20260923-181045.mp4`, SHA256
`019ea2ab8b4bf924e8ef538f6e28eaa9c277dddc67ed5fb1aca8524d541ca60d`.
Full decode is terminal exit0:465 frames through15.4667s,18 exact adjacent
duplicates. Report: `tmp/crew-command-weight-motion-v1-20260924/report.json`.
Inspected original3s/9s frames show progression0.12→0.13km, changing water and
the same held crew side, with no incident/swimmer reported at those samples.
Lower limbs are largely occluded; awkward leaning/standing bodies, coarse
canopy and smooth water remain. This is not continuous foot/limb clearance,
both-direction transition, obstacle-contact, shoreline or river acceptance.
The recording frame rate is not a performance measurement.

## Remaining work

This is a delivered normal command-participation/held-direction correction,
not new terrain detail or accepted crew realism. Next reconcile actual seat
and body geometry with physical loads and replace the provisional high-side
pose with evidence-informed cross-raft motion; do not polish the old tube-
standing target as though it were measured. Qualify overboard mass removal,
continuous transitions and limb/hull clearance, then remeasure real motion and
cost. South Fork and the ordered river queue remain open. All validation jobs
are terminal; the original cook alone continues with unchanged captured data,
geometry/collision, installed4950 fields and native nonlinear mode OFF.
