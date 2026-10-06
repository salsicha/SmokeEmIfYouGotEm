# Class-20 observations against the installed union — September 27

Supporting geometry verification only; no playable assets, source returns,
water fields, solver settings or packaged executable changed. South Fork is
not accepted and the queue has not advanced.

The prior registered-base screen's 17 original class-20 observations were
queried at their exact captured coordinates against the normal saved
`L_SouthForkAmerican_FullReach` map. Independently predicted heights use the
registered revised ground plus the **September 26 interpreted rock envelope**,
not the older September 17 source-exact roof. The operation replaces that old
roof before taking the maximum with ground; it must not retain the old roof
through a second maximum.

## Result

All 34 native vertical traces (17 simple and 17 complex) pass the existing
0.1 cm geometric comparison tolerance. Maximum source-prediction-to-hit
distance is **0.0015480518834347 cm**. This measures engine/source agreement,
not survey accuracy. Sixteen observations hit the registered ground and one,
original return **689294**, hits the currently installed envelope. Both trace
modes identify the expected physical-ground actors.

Return 689294 was 0.569660 m above the registered base alone, but is actually
**0.043473952 m below the installed envelope collision**. It therefore must not
be treated as a missing protrusion based on the base-only screen. The current
envelope happens to preserve the earlier roof height at this query. The other
16 positive residuals remain observations, not confirmed missing boulders.
The largest is 1.289624 m; that observation lacks classified-ground peers
within the prior 0.5 m neighborhood and must not be promoted automatically.

Directed float32 triangle/material hashes independently match native collision
providers, with no rounding concession:

| Current mesh | Triangles | Native/source SHA-256 |
| --- | ---: | --- |
| SourceMatched20260917/SM_SourceMatchedGround | 803842 | `f0d39b640592c1b2cbccf89c1ed07f01587f377de5b5d0db0bab9b254cf888c5` |
| RockEnvelope20260926/SM_CapturedRockEnvelope | 6404 | `57933ca768dc174d18f09b7661dd39ebcce0f3f1e1c86ea6b2faa8a7cb8aedb6` |

The fixture checks exact actor translation, reflected scale, zero rotation,
mesh package hashes, normal map identity, and before/after hashes of source
inputs, map, external actor packages and loaded ground meshes. It does not
save assets, replace actors, run PIE, cook, or change streaming defaults.
Seven Python tests cover source-index/coordinate/class preservation, finite
heights and frame, signed residuals, and envelope/bed union behavior.

## Evidence and failed preliminary fixtures

Successful engine run: September 27 approximately 08:18–08:19 UTC, process
36876, exit 0, report `passed=true`, no engine Error/Fatal records. Startup
warnings and a deprecated Python trace-enum warning remain; this is not a
warning-free run. NullRHI was used, so no visual or performance claim is made.

Two preliminary fixtures stopped on mesh-owner assertions because their
September 17 installation receipt referenced the superseded cap. Explicit
actor loading did not resolve that obsolete reference. The successful third
fixture instead verifies the documented September 26 envelope archive and
current binding. These failures did not establish a scene defect; no asset
was reverted. All preliminary logs remain under `tmp`.

| Fresh evidence under `tmp/` | SHA-256 |
| --- | --- |
| ignored-ground-union-probes-v3-20260927.json | `00b14e6fb9fdcfdeb27a58fb7836a96528bf309287da499a0aee625dad2e264e` |
| ignored-ground-installed-union-v3-20260927.json | `53b11d23b48b0cf5f323b216cbf769e44c8a9a959a85066f08df998086730469` |
| ignored-ground-installed-union-v3-20260927.log | `1c33d7349c8a2a261430369dec62f31bbcf95ae7ed1a5f6b39ddffa0a8eee0e7` |

## Limits / next work

This closes the base-versus-installed-union ambiguity for these 17 points;
do not rerun this unchanged snapshot. Class 20 is ignored ground, not a rock
label. Captured returns remain measured evidence; changed envelope roof
heights and vertical flanks remain inference. The source extractor already
excludes withheld returns. NOAA's [project metadata](https://www.fisheries.noaa.gov/inport/item/66639)
lists no access constraints and cautions about temporal applicability; the
project acquisition dates do not date every individual tile or observation.

Next geometry work should select a spatially supported residual cluster and
cross-check dated imagery before proposing a bounded normal-scene change.
Hydraulic consistency, underwater geometry, coarse flanks, motion, shoreline
and rendered continuity remain separate gates. The unchanged busy-rapid
packaged p95 of 85.2731 ms still fails the user's **20 FPS / 50 ms** goal.
No river or full collision-sweep acceptance follows from vertical point traces.
