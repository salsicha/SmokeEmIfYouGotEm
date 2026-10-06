# Paired foam current installed — 2026-09-17

This corrects a transport inconsistency on the existing South Fork playable
carrier. It does **not** accept its froth appearance, physical hydraulics,
continuous motion, performance, or release. Troublemaker remains a rapid within
the South Fork scenario, not a menu entry. Subsequent rivers remain ordered
Colorado, Pacuare, Futaleufu; the all-scene/crew/regression scope is unchanged.

## Observed mismatch, not a calibrated river measurement

The original submitted CPU UV3 backtrace and the captured mean current used by
the displayed GPU foam frame were different. Capture
`tmp/south-fork-paired-foam-flow-v1-20260917.json` has SHA256
`e326cd0d92692b5742ce19484db8349b39edceba4799526a66a5acbca80c6780`.
At game frame244/detail sequence241, all11,226 wet, fully GPU-owned interior
vertices were retained, including refined vertices. Their RMS difference was
1.138376m/s, maximum5.562463m/s, with432 opposed vectors. Among3,310 vertices
with resolved coverage>0.1, RMS was2.001822m/s and355 vectors were opposed.

The independent row/summary validator passed. Its report SHA256 is
`4799d9f58cc359c329539c02fa9ee15d23b22345e34213f20913bd1e48093923`.
These are shader-input differences, **not measured river velocities or pixel
motion**. The original audit compares raw submitted UV3; after this correction
UV3 is the CPU fallback and no longer the final interior material flow. Do not
interpret a repeated raw-UV3 audit as a post-fix material-motion measurement.

## Implemented correction

- Each asynchronous readback slot retains an owned copy of its exact H/U/V/source
  input, with the same origin and committed-clock row as its completed density.
- A single render command uploads both immutable payloads using the production
  `RaftSimUploadDetailFrame` helper. Incomplete texture pairs are rejected before
  either upload. The normal loop neither adds GPU waits nor changes PDE steps.
- The material helper validates dimensions, origin and split clock, samples the
  paired U/V field, and uses the existing4m ownership blend. Outside/disabled/
  invalid pairs use CPU UV3. There is no second surface or momentum modification.
- South Fork FullReach enables the paired texture normally. A diagnostic
  `RaftSimLegacyFoamFlow` option disables it; no such option was used in the
  installed capture. Other rivers are not silently promoted.
- The current material changes only `FrothFlow` on the existing coverage node.
  All other preexisting nodes, density, clock, WPO, normal and mask remain exact.
  The C++ material generator is updated and its translation unit compiles.
  Its editor DLL was not replaced; full-project/editor-regeneration checks remain
  part of the outstanding normalization work.

## Verification and deployment

The isolated candidate compiled all five gameplay units. Candidate native26 PASS;
the default-enabled build passes32 native tests with zero test warnings/failures,
including production paired upload/readback, registered sampling, foam clock,
committed-water clock, shoreline and crest checks. Default native report:
`tmp/paired-foam-optics-default-native-v1-20260917/index.json`, SHA256
`522e58a15c13d801ecbcc6fda36f401d70fd922a724400261081abd4987d174d`.
The preexisting C4701 compiler warning in DetailSourceFootprintTest remains.

The standalone runner executes the actual production HLSL helper on hardware
and WARP: each backend checks900 queries/3,600 output words across10 variants,
with zero wrong words and zero maximum error. Cases include full/intermediate/
outside ownership, fractional coordinates, stale origin/high-clock/low-clock,
invalid clock marker, nonfinite flow, disabled/half-enabled flow, mismatched
dimensions and both supported clock markers. Configured Python GPU/audit/graph/
frame-time tests:27 PASS, no skips.

The adjacent historical suites `test_south_fork_transported_foam_optics.py` and
`test_shared_flow_advected_foam.py` give3 PASS/6 FAIL. Executing their unchanged
assertions with the changed sources read from committed HEAD gives the same
3/6 result; the first hash failure is in unchanged MaterialsBase.cpp. These
failures remain open, not edited away or counted as passing.

The material installer wrote its verified asset/report but returned
-1073741819 after its log reached shutdown/closed. That original run is NOT a
clean process pass. A separate read-only editor reload exited0, retained the
same asset hash, and matched the complete paired-flow graph plus all three
protected graphs exactly. The coverage input connects to the saved paired node.
Fresh graph report SHA256:
`25af9ea32b09c2c5eeca92c6a0fd37b5411b1703648d43929b8337aeae00e88f`.
The abnormal install-exit cause is not established.

Installed source parent
`/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4`
SHA256: `7164871356a26f5ad38dbde25fbde70c7d1d684e6c76ec856983415e0a4696cb`.
Exact previous material44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d
is retained in `tmp/south-fork-paired-foam-flow-install-v1-20260917.backup.zip`.
Gameplay DLL/PDB installed only after32 native passes, with verified old copies
and manifest in `tmp/paired-foam-optics-installed-backup-v1-20260917/`:

- DLL: `bb80e7c1222bfa027507904f368893f0ed25fb1fc5ce4e8a60889dc1b4e3442f`.
- PDB: `44246235f412e75b5f4d12062a7855c10c990a5983c919cc5bb44718d520a8f2`.

## Ordinary playable result — still not accepted

`south-fork-paired-foam-installed-startup-v1-20260917` is ordinary FullReach
South Fork at station8330,1280x720,D3D12, with no candidate-module, review-material,
quality, or optical override. It exits0, saves24 images, and resumes the exact
cook with status0. Runtime logs identify the ordinary parent, one carrier and
paired flow, with282 publications/two holds and no paired-publication error.
Installed image012 was inspected; SHA256
`3d07a73073816dd79d6dae8e84457c0b32cfe3feb906e33d9f11cb615677fd93`.
The corrected rock bank remains, but broad white sheets/smooth green water and
stylized crew remain unconvincing. Corresponding baseline/candidate stills have
different trajectories; they are not a controlled pixel-motion comparison.
The24 half-second-spaced stills are NOT continuous-motion acceptance.

All timing captures retain300 CSV rows; the unchanged gate uses inclusive
samples60–240,30FPS and p95<=33.333333ms. Results:

| Runtime | FPS | Mean frame ms | p95 ms | Result |
|---|---:|---:|---:|---|
| Isolated paired candidate |28.906446|34.594360|40.7597|FAIL30|
| Same build, old material/no paired flow |29.192404|34.255487|40.8805|FAIL30|
| Ordinary installed paired flow |27.565906|36.276697|42.8224|FAIL30|

Installed GPU mean12.621904ms; game/CPU work still dominates. These short,
variable-trajectory runs do not isolate a causal overhead or prove no regression.
The slower installed result is retained, not discarded. Installed CSV SHA256
`072bb954732f868f5b1cf429729dcd6bfaac3623dbc141fcaf469d77ce1791cb`;
audit SHA256 `5c95753848e92c57397880f440e1138f52e40db77200664fbc7e0c21cb84a0f7`.
No packaged executable/release acceptance follows.

## Hydraulic continuation

Same cook36872, start2026-09-17T03:10:30.0811512Z, was verified live and resumed
after every playable capture; no restart. Completed3100/3150/3200/3250 snapshots
pass state AND86,720 exactly dry artificial-bank checks. At3250/local29000,
max depth4.163404m, max speed5.540138m/s, volume2,927,527.716710m3,
maximum step residual1.647020742e-8m3. Outflow87.545168m3/s still exceeds
inflow45.306955m3/s: **NOT settled and not integrated**. Next3300/local30000
requires its completion marker and both audits.

NEXT: verify continuous engine/reference motion and address broad foam/crest
shape from source-consistent hydraulics, then recover actual whole-frame30FPS
without reducing detail. Full South Fork acceptance, ordered rivers, Chilko/
Zambezi, crew, normalization, existing regressions and release remain open.
