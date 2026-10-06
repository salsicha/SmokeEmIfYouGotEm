# Startup water edge: camera-paired source evidence — September 17

The preceding turn made progress by committing the screenshot-request carrier
observation. This turn captures the actual startup scene and narrows the visible
green-edge investigation to shallow base geometry at wet/dry boundaries. It does
**not** fix the appearance, alter the physical source, or accept South Fork.

## Observation and independent checks

`-RaftSimCaptureFirstCarrierShape` now also exports the local player's actual
world-centimetres-to-clip row matrix and constrained viewport. Camera and carrier
must have identical game frame AND world time. No guessed FOV/aspect ratio is
used. The original 13-second carrier audit remains available and unchanged.

`audit_carrier_camera_rays.py` independently unprojects screenshot coordinates
with UE reversed Z and intersects every exported CPU triangle, including its
already presented vertex detail. It reports the nearest two-sided hit, source
corners, base/crest/detail gradients and CPU vertex-normal/face disagreement.
Only fully wet source cells receive interpolated source/target comparisons;
dry-boundary values are never extrapolated. Missing water stays a missing hit.

This is a **game-thread request pairing, not a render-thread/GPU fence**. The
probes do not resolve terrain/crew occlusion, material displacement beyond the
exported detail, temporal jitter, refraction, or actual optical normals. They
locate CPU counterparts of screenshot features, not proven visible GPU fragments.

Isolated v3 build94810 compiled/linked successfully. Normal map capture70287
completed exit0, no timeout; all24 1280x720 startup images exist. Both v2 and v3
capture wrappers resumed the same hydraulic cook successfully (suspend/resume0).
No installed module or material was replaced.

Native regression10152/PID36744 is terminal0:22 succeeded, zero failures,
warnings or not-run,2.097041s. Report:
`tmp/startup-carrier-shape-native-v3-20260917/index.json`, SHA256
`d65c9046f1800ddc657d4707242d142c6948d603814acfe6419007de185da95b`.
Python21 tests pass,0.48s; report
`tmp/carrier-camera-rays-tests-v2-20260917.xml`. Coverage includes independent
orthographic translation, perspective homogeneous division/reversed Z, viewport
Y, nearest hit, reversed winding, behind-camera/parallel/missing intersections,
epoch mismatch, singular projection, invalid pixels, reordered normals and dry
source exclusion, plus the original14 source/target-gradient tests.

## Actual startup probes

Image: `unreal/Saved/Screenshots/south-fork-startup-carrier-shape-v3-20260917_000.png`.
Its `.carrier.json` and `.view.json` both record game frame2,
world0.6277529065846466s, detail sequence0. The image was visually inspected.
The ordinary downstream guide view still shows a dark-green angular collar
around exposed terrain at screen right; the defect is not claimed repaired.

Final analysis: `tmp/south-fork-startup-camera-rays-v2-20260917.json`, SHA256
`6af6a07ef8823d21dbf010879c01377e95e3b6d111f6d5b64418a8025253d46f`.
The report hashes all six input files and retains exact source-cell rows.

| Screen probe | CPU triangle | Slope | Finding |
| --- | ---: | ---: | --- |
| 965,490; left collar face | 24945 | 32.261169 degrees | Entire gradient from base; crest/detail exactly zero; dry-boundary source comparison unavailable |
| 1220,548; right collar face | 24973 | 42.204378 degrees | Entire gradient from base; crest/detail exactly zero; dry-boundary source comparison unavailable |
| 1150,466; upper green band | 27346 | 2.620294 degrees | Fully wet; cached source closely matches submitted base |
| 1100,510; exposed interior | none | unavailable | No exported CPU water intersection, not filled in by the analysis |
| 400,475; open river | 18898 | 1.468060 degrees | Fully wet; small crest contribution, no presented detail at this epoch |

The steep-face CPU interpolated-normal versus face-normal angles are only
0.439937 and6.835802 degrees. This does not diagnose an optical shader normal,
but it rules out a large CPU-normal disagreement at these two particular probes.

The high wet source vertices actually retained by these triangles are:

- ID26206, field(-5424,3602)m: cached stage8.82828767m, depth0.0407815687m,
  target base8.82849121m. Its adjacent field(-5424,3601)m source stage is
  8.19735044m with depth0.363015115m.
- ID26209, field(-5421,3602)m: cached stage8.83695010m, depth0.044698514m,
  target base8.83694458m. Its field(-5421,3601)m neighbour has stage8.19148882m.

These are shallow wet source cells on elevated bed, not a fine-crest excursion.
Clipping copies the wet endpoint's height to a dry crossing; subsequent fine
geometry retains the coarse base. The reference captures do not calibrate these
submerged depths. Do not delete positive water, flatten source geometry or lower
crest detail to hide the defect.

The historical September14 combined-ground report contains the same two source
coordinates and bed values, with ground-minus-bed errors +0.00024414cm and
-0.00061035cm. That old report is NOT a fresh terrain/occlusion qualification;
its subcell discrepancies and different water epoch must not be silently ignored.

## Next correction, not another whole-scene slope inference

Inspect actual terrain coverage and live optical response at these exact
boundary faces. The capture log identifies the actual core parent as
`M_RaftSim_SouthForkRaftTransmissionWaterV4`. Source inspection shows shallow
opacity/depth-response/behind-water paths, but their mere existence does not
prove the current pixels' opacity or justify arbitrary parameter changes.
Resolve source-consistent subcell wet support and shading of positive shallow
water, then verify the changed installed scene with actual motion/reference
comparison. Fully wet neighbourhood averages do not settle the boundary cause.

Candidate Gameplay DLL SHA256:
`fc36591a50b1c48b1caa7a4179796ff092c493ca90ae6658ee7894ea99fb15f1`.
Installed Gameplay DLL remains
`8c0113680ce23823cda67bdb05762f6d87128426e52771efc89709628435dee6`.
Actual saved core material remains
`44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`.
Captures include the existing engine Python AgentSkill/PythonTestRunner startup
errors; game exit0 is not an error-free-project claim.

## Hydraulic process and full scope

Same PID36872/start2026-09-17T03:10:30.0811512Z was directly verified live.
Complete2700s/local18000 snapshot passes state AND86,720 exactly dry exterior
bank checks. Max depth4.198683396m, speed6.425125693m/s, volume2952091.333202m3,
max step mass residual1.647020742e-8m3. Outflow93.537185787 versus
inflow45.306954547m3/s: **not settled**, no promotion.

- State report: `tmp/control-ablation-2700s-state-v1-20260917.json`, SHA256
  `6e8c41872fac3685e645261f9e0d129b4601af2f8ced862373f235c39c62bff6`.
- Bank report: `tmp/control-ablation-2700s-banks-v1-20260917.json`, SHA256
  `7fcae59b3674e1add9e43ddc4421f1c8b9451b52cc3fae71408414172a909235`.

Before this commit,2750/local19000 completed and BOTH audits passed as well:
max depth4.202505911m, speed6.432756903m/s, volume2949732.071428m3; unchanged
maximum mass residual and86,720 exactly dry banks. Outflow92.809505552 versus
inflow45.306954547m3/s still does not establish settling.

- State: `tmp/control-ablation-2750s-state-v1-20260917.json`, SHA256
  `ddf01ab09605119529a752df76fc89cf716f867ccc49830b3dbc2c65defc1ce0`.
- Banks: `tmp/control-ablation-2750s-banks-v1-20260917.json`, SHA256
  `1ce0a460f945bb49f97ec4d8ac77bcba3adeff15b017132f712f1855f35ae08d`.

Next2800/local20000 requires the completion marker and BOTH audits. Preserve
the same live process; observation timeout is not permission to restart it.
Latest ordinary performance remains30.285471FPS/p9541.4455ms, failing the
unchanged30FPS/33.333333ms gate. Export overhead is not a performance sample.
South Fork terrain/hydraulics/breaking/froth, then Colorado/Pacuare/Futaleufu,
Chilko/Zambezi/all-scene reviews, crew, normalization, regressions and release
all remain open. Troublemaker is only a rapid within South Fork, never a menu
scenario. Temporary reports, captures and binaries remain ignored by Git.
