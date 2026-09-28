# Selected-site full-surface profiles — September 28 UTC

Supporting diagnostic progress only. No new playable appearance, water physics,
collision or performance improvement is claimed. South Fork remains unfinished;
normal play and the packaged v13 retain the 450s fields. No later river advanced.

## Corrected observation, not a river datum repair

The new non-shipping `-RaftSimBreakingProfileAudit=PATH` observer samples three
straight transects through each selected breaking site: across -2/0/+2m, along
-12 to +12m at 0.25m spacing. It compares current native raw samples with the
actual submitted CPU triangles and barycentrically interpolated per-vertex
displacement from ONE immutable, already-presented detail frame. It neither
commits a newer GPU frame nor changes the solver or geometry. Render lift is
removed. Other shader displacement and ground/rock occlusion are not included.
These are straight local-axis sections, not streamlines or measured bathymetry.

The existing `RaftSimCarrierShapeAudit` already exports submitted vertices,
triangles, detail and cached bed/depth. This additional observer provides fresh
native samples and explicitly selected-site sections; it does not replace that
existing full-mesh evidence or establish synchronized source/presentation ages.

The first capture (v1) exposed a bug in THIS NEW diagnostic: it passed an
already datum-relative adapter height to `RiverToWorldPosition`, which expects
absolute elevation and subtracts the datum. That reported an erroneous extra
220m offset. This is not evidence of a 220m gameplay-water defect. The actual
`SampleWaterFieldAtRiverCoordinates` contract subtracts the datum once already.
The corrected Cartesian observer uses that sample directly as world Z meters,
exports absolute-height companions and the datum explicitly, and records the
presented detail sequence and both clocks. No adapter behavior was changed.

The analyzer now requires schema v2, rejects obsolete v1 captures and checks
absolute-minus-datum against world height. It validates finite fields, complete
unique transects, flow-frame coordinates, flags and combined heights; it never
bridges dry/unavailable gaps or substitutes zero for missing detail. Five
unittest cases PASS, including double subtraction and v1 rejection. Six existing
height-audit function tests also PASS via direct runpy invocation. An earlier
pytest invocation was unavailable, not a pytest pass.

Keep the failed v1 capture and summary as diagnostic history, NOT accepted
measurements: `tmp/sf-breaking-profile-v1-20260928.json` and
`tmp/sf-breaking-profile-summary-v1-20260928.json`. Do not reuse their absolute
height differences. No source evidence or captured data was removed.

## Built and observed in the actual normal scene

Corrected editor build session34518: PASS, 68.45s, two compile actions maximum;
log `tmp/breaking-profile-editor-build-v3-20260928.log`. Earlier v1 build warned
about potentially uninitialized diagnostic interpolation outputs; they were
initialized before the v2/v3 builds. This is not packaged-v13 delivery.

Capture session18990 / wrapper25664 / engine30620 TERMINAL exit0, receipt
`tmp/sf-breaking-profile-v2-20260928-process.json`, from
01:13:43.1964750Z to 01:14:36.2336240Z. Normal FullReach `-game`, passive8310m
approach, ordinary boat camera, ephemeral profile, 1280x720/D3D12; no experimental
water mode or quality override. This targeted scene launch does not repeat or
replace the previously recorded Boot/menu launch validation.

- Frozen actor SHA256: `d60bfc71ebe1aa6e49ca5b7d30cb3e6733686b41e42057eab119110524cebfcc`.
- Frozen DLL SHA256: `09ac30350ff19edb85e56542b6b1ec680206a9aaa019f9e81f23a26a484f6d28`.
- Profile: `tmp/sf-breaking-profile-v2-20260928.json`, SHA256
  `99d8269184d2f07a80940cc28a6fa50ae2b8ad8a45986dd35b0c835e3e5bcf56`.
- Independent summary: `tmp/sf-breaking-profile-summary-v2-20260928.json`.
- Video: `unreal/Saved/VideoCaptures/RaftSim_20260927-181414.mp4`, SHA256
  `3ca9d9cd854e17aa32dd2591902f12c102d5629066105270a7a4c14f447e5ed1`.

Fourteen sites were sampled. World time10.003753s, committed water4.733334s;
presented detail sequence68, simulation4.533334s, elapsed9.764417s. Different
ages are explicit, not silently equated. The existing hydraulic cook28956 ran
concurrently: this is NOT an FPS benchmark or isolated clock-capacity result.

At selected site(-5428,3607)m, centerline97/97 probes are wet. Raw surface range
is1.854965m; submitted macro range1.856988m. Maximum adjacent slopes are0.676697
(raw),0.713667 (macro),0.720358 (macro plus detail). Maximum absolute presented
detail is0.058017m; selected analytic additional crest is0.046763m. The largest
macro-minus-raw magnitude is0.254446m. That residual contains interpolation,
temporal/source-age and other submitted relief; it is NOT established to be a
crest bug or missing hydraulic energy. Whole-transect range includes reach
gradient and cannot be called a 1.85m standing-wave height.

At along0, raw stage is about7.74m and macro7.70m. Around along1.75m, raw8.10m
and macro7.95m, with approximately-0.06m presented detail. The downstream rise
exists in both native and rendered geometry. The snapshot does not justify
blind amplitude gain, a datum change or enabling a previously broken solver.
If pursuing this local residual, attribute the submitted interpolation/source
ages and other relief using the existing full-mesh observer before changing
crest dimensions; do not repeat the rejected static-anchor-only experiment.

Video decoded to474 frames over15.7667s,36 exact adjacent duplicates; recording
frame rate is not engine FPS. Inspected original01s and09s boat-camera frames
show the raft advancing alongside the same right-bank rocks. Broad smooth
water/flat white patches and separated spray remain. No convincing breaking
roller, collision, shoreline stability or surface-continuity acceptance follows
from these two views. Existing failed performance/realism gates remain open.

## Ongoing hydraulic owner

No duplicate cook started. Existing wrapper33852/native28956 remains live;
observed step2290/time1014.5s in the same 900-to1350s continuation. Its owner will
audit all three snapshots and regional storage after completion. Do not promote
these transient states or refit inferred bed to their stages. No FPS run while
this workload remains active. See `envelope900-to1350.md` for restart identity.
