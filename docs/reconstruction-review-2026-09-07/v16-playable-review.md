# South Fork v16: packaged spray-anchor increment reviewed; full gates open

## Terminal package, runtime and motion review

September28 UTC follow-through80167/wrapper25420 completed exit0 at05:51:23UTC.
Validation40292 and motion32404/game41924 are terminal too. No job needs to be
restarted. Workflow completion does NOT clear either failed rapid timing gate.
All three packaged1200-frame runs used normal configuration, exited0 and
reported zero runtime errors; rows30..1169 were audited at1280x720D3D12.

| Launch | Mean ms | p95 ms | Maximum ms | Frames >100ms | 20FPS gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot/menu | 39.5200 | 47.6728 | 60.1784 | 0 | PASS |
| 8310 | 44.2020 | 56.8952 | 111.2170 | 5 | FAIL |
| 11520 | 72.6533 | 87.1912 | 144.3344 | 8 | FAIL |

11520 CSV SHA256
`9f22d1c7f630bc35c318e119e99829b4910946918f7736744f2923fc5ffdbd2d`.
Its GameThread mean70.5150ms versus GPU20.5064ms indicates a CPU-bound capture;
water-clock backlog grows0.9951 to7.8seconds, with all1140sampled frames using
four fixed ticks. Zero failed steps and matching adapter commits do NOT imply
real-time capacity. Do not discard elapsed time, raise fixed steps, weaken
gates or label this capture healthy timing. This was not a matched causal A/B
against v15r2, so the change alone is not established as the source of the cost.

### Actual anchoring and approach evidence

The packaged normal-camera approach recorded80telemetry samples from8313.254
to8487.254m (174.000m), world2.405 to81.007s. All six active sites logged all
three emitter types at the10.025s checkpoint:18sampled/enabled records with
exact printed6/3/3cm clearance above independently sampled carrier positions.
The strict parser passes all six complete triplets. This is a ONE-checkpoint
source-centre check, not continuous particle collision or spawn-plane evidence.
At slot4 the old centre-Z formula would have placed the roller/crest8.858268cm
lower at this same sampled state; this is a formula comparison, not visual A/B.

- Log `tmp/sf-v16-spatial-approach-20260928.log`, SHA256
  `ffe2df6bd1f3847fdd2a79a9728fa1d2c6701c4eeadf56ffce2fddfec677d8e0`.
- Anchor report `tmp/sf-v16-spatial-approach-20260928-anchors.json`, SHA256
  `911b995535db90e08f775e0d08c23e08b7451d6348648aa05c8832fd265d1e78`.
- Video inside v16 stage `SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-224955.mp4`,
  SHA256 `a4b98667179e3a52a03b310fa3a8ed87670db1df1acc6df003e87c0573f65cf0`.
- All2,489encoded frames decoded with increasing timestamps0..82.933333s;
  53exact adjacent duplicates. Encoder rate is NOT actual game FPS. Recorder
  reported1,310source frames over82.951s. Unmodified frames at1/6/11/20/40/60/80s
  and decode receipt are in `tmp/sf-v16-motion-decoded-20260928/`; report SHA256
  `953363b1873c5d5463cb57e51cd50e0f14f74cf42681dadd061116eba010a8c5`.

Inspected6/11/20/40/60/80s views: the raft passes the right-bank rocks and reaches
quieter water; white foam remains broad/flat and ribbon-like, crest geometry
still lacks convincing breaking, and detached-looking spray puffs remain near
the crew at11s. Boulders remain visibly coarse. No pixel-matched visual
improvement, complete shoreline continuity, boulder collision or realistic
holes/recirculation acceptance is established. The requested ground-contact
JSON was not produced, so it is NOT collision evidence. Fourteen selected-site
profile checks pass and legacy plunge remainsfalse; those analytic checks are
not a complete rendered-surface/motion pass.

The normal packaged increment and its source-centre correction are delivered
and narrowly verified. Overall South Fork visual/physics/performance gates
remain OPEN; later rivers remain queued. Next address actual CPU work without
altering cadence/coverage/history, while replacing flat foam and detached spray
with physically credible breaking behavior. Existing publication attribution
identifies recenter publication costs; VFX sampling cost is not separately
measured yet. Do not repeat these unchanged captures as a substitute for a fix.
This terminal section supersedes the historical live notes below.

## First actual packaged result

8310 rapid result is now COMPLETE and FAILS timing: mean44.2020ms,
p9556.8952ms, max111.2170ms, five>100ms, with normal configuration, exit0
and zero runtime errors. Same1,200frames/30..1169audited. Raw CSV SHA256
`f4cd3ea28fc27ca0e62dd6192a7738bac59d849e807005c147d0f22cb7b70ce1`;
report `unreal/Saved/RaftSimValidation/sf-v16-rapid8310-20260928-frame-audit.json`.
This does not establish a causal cost difference from v15r2 without matched
conditions; it does establish this candidate misses the rapid acceptance gate.
Validation40292 is now running11520, then the queued motion capture. The
preserved user's WaterSurfaceTest file still has SHA256
`d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3`.

Normal Boot/menu/FullReach launch COMPLETE:1,200actual frames, rows30..1169
audited, normal configuration, exit0, zero runtime errors. The Concert startup
error from the editor run was NOT observed here. Start-area timing PASS20FPS:
mean39.5200ms, p9547.6728ms, max60.1784ms, zero>100ms. This is only the
specified start-area sample, not a rapid, full-reach or visual acceptance.
Report `unreal/Saved/RaftSimValidation/sf-v16-normal-menu-20260928-frame-audit.json`;
raw CSV SHA256
`877173fde0bb1cde2b00b0fec35d5ce9270dd4aff60a084e9f86274b62f548af`.
Same validation owner40292 has advanced to8310; follow-through25420 remains
live. No new engine/cook/capture was started concurrently.

September28 UTC. Package session45681/wrapper33204 completed exit0 after
365.77s BuildCookRun (AutomationTool367s), with all recorded inputs unchanged.
Recipe `tmp/package-south-fork-v16-20260928.ps1`; receipt/log
`tmp/south-fork-v16-package-20260928.{json,log}`. Stage:
`tmp/south-fork-playable-v16-20260928/Windows`.
Inner game executable SHA256:
`dd2a34e1e4ca8d33b96a55f0429210135684b1c487dfcecda534921d6c2eb7bf`.
This is a new normal packaged candidate, NOT visual/performance acceptance.

## Included change and preserved evidence

The normal Cartesian South Fork spray path now queries visible carrier height
at each horizontally shifted emitter centre. It retains aerosol/roller/crest
6/3/3cm clearances, existing horizontal offsets, six-site budget, density,
assets and emission gating. Failed carrier queries disable that site's emission.
This does not conform an entire spawn plane or prove particle landing, overturn,
holes or returning circulation. See [implementation and native evidence](spray-shifted-emitter-anchors.md).

Editor build114.34s and all six native tests passed before packaging. Actual
editor Boot/menu then FAILED health on the engine Concert timestamp initializer
test and failed timing; motion never started. That failed evidence was retained,
not filtered. No engine changes or plugin disable were made. Packaged execution
is independently required and not assumed to fix that editor failure.

Material remains hydraulic-normal repair SHA256
`6e7884ed44c1f3a372cda6dd1aae675409031fd1c1fbdd3a73bcb5a2effbc96a`.
Runtime manifest remains450s v8 SHA256
`8190b5e81951986070664344a8a53c953a44961fc7d881f0633ba2cf9a7eb190`.
No captured terrain, inferred bed, collision, boulder geometry or discharge was
changed. Newly audited1800s fields were NOT promoted; nonlinear gameplay remains
OFF. Existing v14/v15r2 stages and recordings are preserved. Missing MetaHuman
texture dependencies still appear in cook logs and remain a release issue.

## Staged closure and live validation

Staged transitive runtime closure PASS:2,405files,917,995,570bytes, exact v8
manifest, no external-source fallback. Report:
`tmp/south-fork-v16-staged-payload-20260928.json`. This proves staged bytes,
not engine motion, collision or physical/visual acceptance.

Exactly one follow-through: session80167/wrapper25420, start05:44:45.0437460UTC,
receipt `tmp/south-fork-v16-follow-through-20260928.json`. Its existing build
wait is complete; validation child40292 started05:45:22.5784211UTC, receipt
`tmp/south-fork-v16-validation-20260928.json`. Normal-menu game32804 is live.
Do not duplicate validation/capture or modify its frozen package inputs.

The sequence is:

1. Isolated packaged1200-frame Boot/menu,8310 and11520 runs. Check actual
   runtime health and normal configuration; retain20FPS/p95<=50ms/no>100ms
   gates. Source-clock and nested CPU scopes use the existing strict parser;
   only an actually duplicated unmeasured header gets its explicit exception.
2. After these healthy runs, one normal-camera80-sample8310 approach with
   recorded video, physical-profile/spatial checks and source audit logging.
   The new parser checks actual enabled/sampled6/3/3cm centre clearances.
3. Decode all recorded frames and inspect actual spray/crest/shoreline motion.
   Encoded cadence, source-text/native tests and centre equality cannot prove
   the appearance is convincing or the spawn planes/particles clear the water.

Recipes: `tmp/validate-sf-v16-20260928.ps1`,
`tmp/capture-sf-v16-spatial-approach-v1-20260928.ps1`,
`tmp/follow-through-sf-v16-20260928.ps1`. Every timing/visual result remains
pending here. Workflow completion will NOT override a failed timing gate.
South Fork remains first; no subsequent river or release acceptance is claimed.
