# Captured-ground rendering correction and remaining water gates — September 17

The preceding commit turn made progress: `9a1df91fd` records the reconstructed
ground integration and its regressions. It does not establish visual or physical
acceptance. This continuation corrects the actual captured bank's rendering in
installed South Fork, retains failed trials and timing evidence, and leaves
physical/foam/performance acceptance open.

## Installed outcome

The current captured-ground component now renders its complete source fallback
instead of its visibly inconsistent Nanite representation. The actual source is
`/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround`,
not the earlier survey-candidate asset. The policy requires both reconstruction
and physical-ground tags, this exact mesh identity, one fallback LOD and all
803,842 triangles. It changes the component render path only: no source asset,
collision, water geometry, optical coefficient, global Nanite setting or other
river is modified. The current water actor handles initial and streamed arrivals
and removes its delegate on EndPlay; ground arrival also invalidates cached misses.

Corrected candidate v2 compiled/linked, and all24 native shoreline/crest tests
passed with zero test warnings/failures/not-run. The captured-source test verifies
the current asset, scope exclusions and idempotency. Report SHA256
`8d4a3f87826b01688436da7d66669bd2dfe0ecdb68747147e5324a45eb512040`.
Actual candidate capture logs the policy on the SAME actor hit by the camera
rays, at game frame1, exactly once. Its frame000 shows the full rock bank in
place of the conspicuous angular green collar. Other Nanite geometry is retained.

Gameplay DLL/PDB were installed with exact rollback copies and a manifest at
`tmp/exact-ground-installed-backup-v1-20260917/`. Installed DLL SHA256 is
`e3b13f50993efda77683f9fb8ea9fff676b2a4325dadcfe01f80165ac376a8a6`;
PDB `88e854164e0b1d0749ef214973655f5eefcb2df36ef854ad0c3110115f575525`.
Project and WaterDetail modules are unchanged. No standalone/packaged build was
updated. Original current-ground, old survey-ground and material assets remain
unchanged; the rejected old-asset residency change was fully restored.

Normal installed startup `south-fork-exact-ground-installed-startup-v1-20260917`
uses NO module, optical, global Nanite or quality override. All24 images completed
exit0/no timeout, cook suspend/resume0. Frames000 and012 were inspected: the bank
correction is present, but later broad sheet-like foam and crew quality remain
unaccepted. This proves the visible startup correction, not whole-scene GPU-depth,
physical fidelity, continuous motion, full traversal or release acceptance.

Installed ordinary timing `south-fork-exact-ground-installed-perf-v1-20260917`:
**25.310283 FPS, mean39.509633 ms, p9546.2835 ms — FAIL30**. Same181 rows60–240,
1280x720 D3D12, no diagnostic overrides. This run is slower than the earlier
installed baseline; the visual correction does not excuse the failure. Game
thread39.176434 ms, GPU13.875505 ms, water Tick24.07 ms, SetMesh11.47 ms,
crest selection3.93 ms, StepWater6.98 ms (nested/overlapping, not additive).
CSV SHA256 `391bda241d934df2cf90ff99145c8f99b5b90de3911b9acda636d9167f60b3c9`;
audit `tmp/south-fork-exact-ground-installed-perf-v1-20260917-audit.json`, SHA256
`a94ec3ef53e7b1a04494421da35f679d9817257ed45278363a2865c95cb72c56`.
Next recover sustained frame budget while preserving the corrected source
surface, and resolve the actual current mesh's Nanite discrepancy if that can
retain exact appearance more efficiently. Its residency was NOT tested by the
wrong-target legacy trial below. Breaking/froth and full physical work stay open.

## Ground integration correction

The assembly tags reconstructed static meshes `RaftSimPhysicalGround`, but the
water trace helper accepted only `RaftSimFullReachTerrain`. Consequently all seven
camera terrain probes missed the actual ground. The common source predicate now
accepts legacy terrain plus actor/component-tagged physical-ground static meshes,
matching the contact registry. Streaming arrival invalidates cached misses for
both forms. An unrelated component no longer excludes a tagged sibling on the
same actor. The four-attempt limit, shared budget, and caller query remain intact.

The red native regression fails actor- and component-tagged reconstructed ground
with the old helper. The corrected native suite passes all 23 shoreline/crest
tests, zero failures/warnings/not-run (`tmp/captured-ground-probe-fixed-native-v1-20260917/index.json`).
Fixtures cover legacy ground, unrelated blockers, tagged siblings, budget
exhaustion, streaming recognition and unchanged caller ignore lists. Build output
still includes the pre-existing C4701 warning in the detail-source footprint test.

Actual corrected capture `south-fork-ground-probe-fixed-v1-20260917` completed
exit 0, all 24 images, no timeout, cook suspend/resume 0. All seven terrain rays
now hit. Frames 000 and 012 were visually inspected: the angular green collar
and later sheet-like white foam remain. Positive physical shallows were not
deleted, and no bed, source water, crest amplitude or default optics changed.

## What the current camera rays actually prove

Analysis `tmp/south-fork-ground-probe-fixed-analysis-v1-20260917.json`, SHA256
`edb9f8fdf84602d090958a29eabf66cf7eea2c563e5839500afbda5c8a973364`,
hashes all six source files. Camera and carrier share game frame 2 and world time
0.6546956961392425 seconds. Independent Python and UE rays agree within
2.84e-9 metres in origin and 2.30e-8 in direction.

| Pixel | Signed camera-depth gap, cm | Meaning |
| --- | ---: | --- |
| 965,490 | +7.843307 | Steep CPU water face is close to collision ground |
| 1015,467 | -355.297515 | Collision ground is in front of nearest CPU water |
| 1150,466 | -218.574800 | Collision ground is in front of nearest CPU water |
| 1220,548 | +0.913964 | Steep CPU water face is very close to collision ground |
| 950,550 | +56.844516 | Positive separation |
| 1100,510 | unavailable | Ground hit, no CPU water hit |
| 400,475 | +1397.468250 | Open-river ray |

Negative gaps are retained, not clamped. These are unrefracted complex-collision
rays, NOT GPU scene depth or proof of which triangle produced a visible pixel.
There is no GPU fence, temporal-jitter matching or optical-normal measurement.
The small gaps at the two steep faces contradict an explanation based solely on
metres of separation from collision ground. Rendered depth remains to be resolved.

## Optical controls, not appearance fixes

All controls are explicit process-local flags; no material asset was saved.
The prior baseline/zero-opacity/hidden-carrier/zero-extinction captures completed
24 images each, exit 0 and cook resume 0. The saved graph audit confirms that
shallow opacity is connected. Actual live shallow/deep opacity is 0.30/0.54.

- Zero shallow opacity leaves the green faces visible.
- Hiding only CartesianShorelineMesh removes the river and collar. This is a
  visibility ablation, not gameplay/contact qualification.
- Zero scattering/absorption plus zero shallow opacity makes the collar
  terrain-transmitting, while removing body colour from the rest of the river.
  It is not an acceptable final material.
- New `-RaftSimCaptureZeroWaterSpecular` zeros the four connected specular inputs
  before the first image. Unreal derives the water IOR from dielectric specular;
  this control removes its refraction AND specular reflection, not just one term.
  `south-fork-zero-specular-v1-20260917` completed 24 images, exit 0, resume 0.
  Frame 000 visibly loses surface reflections but retains the green collar.
  Refraction alone therefore does not explain the feature. Geometry and
  extinction defaults were retained, and no appearance acceptance follows.

Zero-specular isolated DLL SHA256:
`76d2df22a0150be40e8462d08ae9ab99f9729c6f0f0bb63d6fe84b98694eec2e`.
The saved optical graph report is `tmp/south-fork-optical-graph-v1-20260917.json`.
Its scope is saved topology/defaults, not evaluated GPU inputs.

## Nanite discrepancy and rejected residency trial

The original-asset `south-fork-nanite-off-v1-20260917` capture sets only the
process-local `r.Nanite=0` device-profile override, retaining original water
optics. Frame 000 shows full rock terrain replacing the angular green collar.
This is a decisive renderer-path difference, not proof of a specific Nanite bug.
Its camera matrices differ slightly from the earlier run; it is not a pixel-exact
paired capture. No global Nanite-off setting is retained.

Correction: the residency trial initially selected the OLD survey-candidate
mesh from the assembly manifest. The actual hit actor was subsequently identified
in the source-alignment code and collision report as using
`SM_TroublemakerCapturedGround` (current SHA256
`687d05c5fabd9482f02cf15683fa29f238304f2738d0f435c5c306f0b44e174b`).
The old survey-candidate has one full 803,842-triangle fallback LOD, Nanite
enabled, zero trimming, and minimum residency 0 (one root page). A guarded
single-asset residency trial changed only TargetMinimumResidencyInKB to
MAX_uint32. The first commandlet lacked StaticMeshEditorSubsystem and failed
before any asset edit. Full-editor rebuild v2 succeeded; v3 repeated from the
verified original backup with an exact native geometry witness:
403,200 vertices/803,842 triangles, identical positions, indices, normals and UVs,
SHA256 `958c9924c2b0be3684cf4bb86d5117219790cb30b586d8af3ef696f5a72d67ca`.
All 407 Nanite pages became root-resident (13,112,436 GPU bytes; zero streaming
bytes). Native collision policy and all source geometry remained unchanged.

The normal installed startup capture `south-fork-resident-ground-startup-v1-20260917`
still shows the collar in frame 000. This wrong-target trial is rejected and
does NOT rule out residency on the actual current source. Its
candidate asset `f1ad598b660ef490dcf2b70299fe54b56a3b9dc7e4d11f7d8b9a0d2f734bdbe5`
was restored from the exact original backup, with original hash verified. The
intended follow-on performance run did not launch; no timing is claimed for it.
Trial report `tmp/rapid-nanite-resident-v3-20260917/report.json` SHA256
`c1cce2807a1be0a54efb6a6629e2b708143c668bf4039d0571edbeb6963c7e2b`.

On the restored original asset, `south-fork-nanite-fine-v1-20260917` sets the
process-local screen-space threshold to 0.1 pixels per edge instead of 1.0.
Frame 000 still shows the collar; this is not a retained quality setting.
All three captures completed 24 images, exit 0/no timeout, cook resume 0.
That finer global threshold did not fix the observed renderer mismatch; the
wrong-target residency trial cannot support an equivalent conclusion.

The first scoped-renderer candidate also used the stale source identity. All24
native tests passed against that old asset, but actual gameplay emitted no
application log and retained the collar. It was not installed. This demonstrates
why those narrow native passes were insufficient for playable integration.
The corrected candidate targets ONLY the actual source-identified captured mesh
and binds the live water actor's startup/level-arrival lifecycle as well as the
legacy streaming actor. Other terrain and foliage
must keep their existing renderer. A changed source/LOD contract must be rejected,
not silently replaced with a simplified fallback. No water-film deletion is needed.

## Earlier performance: terrain-probe-only candidate was not installed

All runs use actual 1280x720 D3D12 South Fork at station 8330, 300 CSV frames,
unchanged inclusive sample rows 60–240, target 30 FPS/p95 <=33.333333 ms.
No image export or optical controls are enabled in these timing runs. Candidate
runs use only the gameplay-module override; the baseline uses the installed DLL.

| Run label suffix | FPS | Mean frame ms | p95 ms | Gate |
| --- | ---: | ---: | ---: | --- |
| ground-probe-perf-v1 | 23.266427 | 42.980386 | 50.7846 | FAIL |
| ground-probe-baseline-perf-v1 | 30.899418 | 32.363069 | 40.3356 | FAIL |
| ground-probe-perf-v2 | 27.922477 | 35.813442 | 42.5975 | FAIL |

Full labels have `south-fork-` prefix and `-20260917` suffix. CSVs are in
`unreal/Saved/Profiling/CSV/`; corresponding `tmp/<label>-audit.json` reports
record exact hashes and per-scope times. All wrappers completed exit 0, no timeout,
cook suspend/resume 0. The candidate slowdown varies across runs; neither a
causal regression nor an improvement is isolated by these short trajectories.
It was not installed in that form. Do not select only its better run. The later
combined source-rendering/ground-integration installation is recorded above.

Before the combined installation, Gameplay DLL was
`8c0113680ce23823cda67bdb05762f6d87128426e52771efc89709628435dee6`.
Terrain asset remains `12ba8d8ac76f378cedfdb6c5cc8bd7e8708b0914a9aa43c9389e6753e0d90d56`;
water parent remains `44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`.
The continuation's camera/shape/CSV plus native-hash witness Python regression
run passes 34 tests in 0.98 seconds; no gate or tolerance changed. No packaged
executable was updated.

## Hydraulic continuation and full scope

Same live cook PID 36872/start 2026-09-17T03:10:30.0811512Z is preserved.
2800 and 2850 seconds pass state conservation AND all 86,720 exactly dry exterior
bank cells. At 2850: depth max 4.205288208 m, speed max 6.457759850 m/s, volume
2945098.271618 m3, maximum step mass residual 1.647020742e-8 m3. Outflow
91.246921233 versus inflow 45.306954547 m3/s: NOT settled or promoted.
2850 state/bank reports in tmp have SHA256 respectively
`977773cf045a08ce79af8ef211d967f6da3795f625ce0fad7ee9d38b6dc08441` and
`b65178b9b3b1c1183ed1dcdc68a70b52ec028c69dd1d2f324b24ae263fb239c2`.
2900/local22000 also completed and passed both audits: depth max4.204413267 m,
speed max6.461032560 m/s, volume2942823.788245 m3, unchanged maximum step residual,
and all86,720 banks exactly dry. Outflow91.013205207/inflow45.306954547 m3/s
remains NOT settled. State/bank report SHA256 respectively
`dd142234a281147f5169ff6a9d19909bd5ac5d97cc557d9bdafe543dc929d57e` and
`033bb639b2456164fd4987b3ad226fe0b609d39e62a3ef7364cd09c2d0167f19`.
2950/local23000 then completed and passed both audits: depth max4.202116827 m,
speed max6.353237339 m/s, volume2940575.645953 m3, unchanged maximum step residual,
all86,720 banks exactly dry. Outflow89.800956525/inflow45.306954547 m3/s remains
NOT settled or promoted. State/bank report SHA256 respectively
`a88b46343dd1be8a7687abe4510882571414a3f061e2399f8a48e340f6df0c06` and
`4fa042604f81493a23c2b0b03848010d55bef308a60d6d376ba0124d1ab62659`.
Next3000/local24000 requires its completion marker and both audits.

Next preserve the corrected captured-bank rendering while recovering timing,
then source-consistent subcell support, coupled physical front/energy/bed work,
actual motion and froth, and sustained 30 FPS. South Fork remains unaccepted.
Colorado then Pacuare then Futaleufu, Chilko/Zambezi/all-scene reviews, crew,
normalization, regressions and release remain open. Troublemaker is only a rapid
inside South Fork, never a menu scenario. Reports/binaries/captures remain ignored.
