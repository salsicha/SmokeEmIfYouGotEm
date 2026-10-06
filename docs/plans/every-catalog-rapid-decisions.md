# Every catalog rapid implementation and calibration

The October 6 scope includes all 99 indexed catalog entries: calibrate the 72
existing trial sections and build the 27 missing playable sections. Badger's
addition brings the current inventory to 73 test sections and 26 still missing;
this is construction coverage, not calibration acceptance. Upper Gorge
duplicates and named aggregate reaches remain identified; they are not 99
distinct surveyed rapids. No all-entry class-match conclusion is established.

## Completion requirements

Each entry needs registered whole-rapid bounds, its documented decisions in the
normal playable map, and native production-raft comparisons covering:

- Successful approach tolerance and continuous full-hull route clearance.
- Early, late and absent steering from genuinely different approaches.
- Actual consequences of mistakes, including downstream carry-over.
- Recovery with normal strokes, high-side and rescue controls, without resets.

A broad wave-train line or legitimate bypass is not a defect merely because it
is easier. A catalog class does not prescribe a flip probability. Grand Canyon
1–10 ratings must not be treated as I–VI equivalents. Distinguish catalog/source
grade disagreements and flow dependence from game defects.

Complete real rendered descents, normal launch and packaged 20 FPS checks before
final acceptance. Fixed-time/NullRHI trials cannot establish measured FPS. Commit
and push the scoped implementation after completion; preserve other work.

## Playable code already changed

`build_named_rapid_profiles.py` generates named hydraulic sites for Hance,
Upper Huacas, Terminator, Lava Canyon and Batoka. The production shared
render/foam/hull-current kernel consumes them by default; existing verified
reference sites are retained without duplication. Heights, spacing and
underwater effects are authored hypotheses, not measured bathymetry. This does
not build missing solid obstacles or missing map sections. Suicide remains
commercial portage.

Nine targeted native tests passed in `tmp/rapid-decisions-native-v3/index.json`.
The five-map initial controls are in `tmp/rapid-decisions-playable-v1`.
Those checks establish execution, not class agreement.

## Verified control corrections

Oblivion's 12 m steering lookahead stalled even without rock contact. In matched
fresh processes, 45 m lookahead cleared in 65.4 seconds with no full-hull contacts;
the 12 m control stalled at 101.4 seconds. This is a driver correction, not a
water-force change. Receipts: `tmp/rapid-driver-isolated-v3`.

Bidwell's old 1015 m finish cut through its exit contact zone. Trials now extend
to 1080 m. The initial centred-exit hypothesis changed the upstream interpolation
and hit terrain at 850–870 m; it is rejected as a clean control. The corrected
comparison preserves the same upstream route and changes only exit timing:

| Exit input | Finish | Hull impulses | Contact-bearing fixed-step time |
| --- | --- | ---: | ---: |
| Old right-side exit | 148.4 s | 482 | 3.65 s |
| Move beginning at 930 m | 137.2 s | 0 | 0 s |
| Move beginning at 980 m | 158.8 s | 1392 | 10.43 s |

All three finished without swimmers or checkpoint recovery. The matched early
route is now the campaign's prepared control. Late recovery here means the
normal route driver regained progress; it is not proof of a high-side or rescue.
Receipts: `tmp/bidwell-exit-isolated-v2/index.json`. These are fixed-time native
runs, not a Class IV certification. Small initial vertical/roll differences
remain, so repeat timing brackets before claiming a precise threshold.

Poor-heading trials now use ordinary steering inputs to hold the bad approach
through the decision, then release it. Merely setting initial yaw let the driver
correct long before the hazard and was not a useful poor-approach test.

Lower Pinball rendered controls (`tmp/pinball-decision-render-v1` and
`tmp/pinball-linked-followup-v1`) separate finish arrival from a clean line.
Prepared steering cleared in 68.2 s with zero full-hull impulses. Steering only
through the first rock cleared in 74.0 s but accumulated 1538 impulses, drifting
to +25.28 m lateral at the second rock. Omitting steering from 2010 to 2038 m
then resuming cleared in 74.4 s with 124 impulses. Both omission controls passed
the first measuring plane near -3 m without prior contact; no crew washed out.
This demonstrates bank-contact consequences and an ordinary steering recovery,
not a forced flip, exact route width, or completed Class III agreement. A
powered/no-steering approach also cleared cleanly; do not hide that favorable
approach or mistake it for a no-input drift. The separate hands-off run recorded
zero guide strokes and crew-command changes, 2635 impulses, and stalled at
2069.45 m after 385.8 s; it missed the second gate (+7.38 m versus +9 m minimum).
The rendered guide's moving arm partially occludes the finish camera;
these captures do not establish unobstructed visual acceptance.

## Missing playable sections

| River | Missing entries | Construction state |
| --- | ---: | --- |
| Colorado | 14 originally | Badger is now a saved playable construction map with a completed rendered integration descent; calibration remains open. All fourteen missing entries now have triangle-matched solver inputs. Granite and Unkar use wider captured source crops; existing Hance is unchanged. |
| Pacuare | 9 | Source-linked decisions and guide order; current geographic registration and obstacle construction still required. |
| Futaleufu | 1 | Asleep at the Wheel lies above the current crop; needs its own extension. |
| Chilko | 3 | Resolve the bounds of Lava Canyon, Green Mile and Miracle Canyon, distinguishing aggregate reaches from individual rapids. |

The exact per-entry source requirements are in
`unreal/Scripts/rapid_missing_entry_decisions.py`. Bobo is the lower-run Class III
feature below Rios Lodge and above Rodeo on its map, not Upper Pacuare's Class V
Leaping Bobo. Modern Bobito is only a candidate alias. Do not duplicate a nearby
rapid under an unresolved name.

## Colorado construction safeguards

The registered inputs combine CC0 USGS 2021 water profiles, classified water
outlines and surveyed pool bed with 3DEP dry terrain. Regional DEM values over
water are excluded: they are not bathymetry. Geoid conversion comes from the
profile, not a fitted water-pixel height offset. Missing rapid bed and low-bank
stabilization have separate inference masks. Surveyed pool bed is retained.

Badger's 1800-second native cook passed the construction screen: outlet flow
224.22 versus inlet 226.53 m3/s, depth-change p95 4.25 mm between the last frames,
water-height error p95 0.49 m, and classified-water overlap 0.904. The target is
8000 cfs versus the profile's approximate 8400 cfs. These are modelling checks,
not surveyed velocity or boat acceptance.

The first runtime export exposed a geometry handoff error: separate 1 m source
and Landscape interpolation produced a 0.98 m worst wet-bed disagreement despite
1.6 cm p95 agreement. Do not install `catalog_runtime_2026_10_v1/badger_creek`.
It also predates the runtime-boundary format correction. The exporter now refuses
over-10 cm wet-bed disagreement. `--match-landscape` cooks the same quantized
Landscape reference used by export; engine collision triangles still need direct
validation. A fresh native cook is required, not reusing the earlier flow field.

That terrain-matched cook has now completed:
`tmp/colorado-badger-landscape-review-v3/review.json`. Outlet/inlet discharge is
224.279/226.535 m3/s, depth-change p95 is 4.17 mm over the last 150 s, and surface
error p95 is 0.486 m. `catalog_runtime_2026_10_v2/badger_creek` exports this cook
with zero sampled bilinear terrain-reference/solver-bed disagreement. The native
import then found up to 39.34 cm difference at 48643 complex collision probes:
Unreal uses triangle interpolation, not bilinear interpolation. The importer
refused to save a map. V2 is now explicitly rejected too; preserve its evidence.
`landscape_sample` now follows Chaos's (0,0)-(1,1) diagonal. Triangle-matched
inputs are in `catalog_solver_inputs_2026_10_v3/badger_creek`. The fresh 1800 s
native cook completed at `tmp/colorado-badger-triangle-cook-v4`: outlet/inlet
224.324/226.535 m3/s, depth-change p95 4.17 mm, surface error p95 0.487 m.
The V3 runtime passed all 48635 actual complex collision probes with maximum
error 0.183594 cm. The new `/Game/RaftSim/Maps/Catalog/L_Colorado_BadgerCreek`
was saved. The earlier rejected candidates remain unchanged.

`build_catalog_map_contract.py` and `RaftSimEditorCatalogMap.cpp` add a fresh-map
import path: verified source hashes, actual quantized Landscape render/collision,
the production oar raft, reach-specific water/coordinates and explicit descent
bounds. Every wet cell is probed against Unreal's complex collision heightfield
before saving. No Hance geographic drape or backdrop is copied. The current
Badger construction descent is 300-1300 m; these are not claimed as surveyed
rapid bounds. The importer compiled and linked (`tmp/catalog-map-import-build-v2.log`).
The first rendered production-oar-raft descent (`tmp/badger-integration-native-v1`)
cleared 700-1050 m in 128.8 s with zero contact impulses, swimmers or resets;
maximum roll/pitch 22.06/21.12 degrees, all states finite. All 17 authored sites
loaded, 16 centre footprints crossed; these are not force-magnitude receipts.
Start, midpoint and exit frames were captured. Terrain currently has a basic
tiled material, not final canyon art. This fixed-time run does not prove 20 FPS.
Normal frontend and packaging entries now include Badger with inferred-geometry
and calibration-in-progress labels. The build succeeded; three native shared
kinematics/profile/menu-boundary tests passed (`tmp/badger-menu-native-v1`).
The shared production profile now has an authored upper-right entry hydraulic
and five following waves for Badger only, leaving a broad left tongue and no
profile foam at the 1050 m pool. This follows the [guide's qualitative decision](https://gorafting.com/united-states/arizona/grand-canyon/badger-creek-rapid/),
not measured obstacle footprints. The native entry-relief/clear-tongue/pool-release
tests passed. Seven separately launched rendered decision controls are running
under `tmp/badger-decisions-native-v1`, using `build_badger_decision_controls.py`.
Only their completed receipts may be used for comparison. Normal menu launch,
full construction descent, geometry finish and packaged cost remain to verify.

The first four decision controls completed on the same engine build. The tongue
cleared in 128.2 s (maximum roll 18.72 degrees). The -21 m right-side target
actually crossed the hydraulic plane at -30.81 m and rolled only 4.36 degrees:
this is an outer bypass, not a strong-hole impact. Early and late inward moves
crossed at -17.44/-25.80 m with approximately -101/-93 degree relative headings;
maximum rolls were 31.52/21.09 degrees and both cleared without contacts or
swimmers. The intended early move is not yet a clean, square control. Additional
-12 m interception controls are queued with the same DLLs. Do not enlarge the
hazard to catch an inaccurate driver or equate a broad observation footprint with
an immersed-current exposure.

House Rock's native cook passed all four construction gates: classified-water
overlap 0.9360, water-height p95 error 0.5917 m, settling p95 0.000238 m and
outlet/inlet discharge 226.590/226.535 m3/s. Its hash-verified map import is queued
after the Badger comparison. The authored shared hydraulic profile and six
ordinary-input decision controls exist; the House profile is not yet linked or
boat-validated. Its right passage is shallow in the cooked source, so an overdone
rightward move must be checked for real terrain contact, not just gate arrival.

Georgie, Sockdolager, Grapevine and Horn Creek also passed the four construction
gates and exported triangle-matched runtime candidates. Their overlap scores
are 0.9650/0.9808/0.9863/0.9827, with water-height p95 errors
0.7204/0.7650/0.8170/0.5225 m. Import contracts are ready; no boat or class
acceptance is implied. The missing solid obstacles must still be constructed and
verified in addition to hydraulic effects.

Soap Creek's first cook is rejected: wet overlap 0.8020, with 3441 wet cells more
than 4 m beyond the classified source outline. A fresh sensitivity run changes
only uniform roughness from 0.04 to 0.03, without moving measured bed or relaxing
acceptance thresholds. Neither value is a measured resistance. Granite/Unkar's
formerly truncated strip now fits actual 250 m-margin bathymetry/water crops;
no out-of-coverage terrain was extrapolated.

Source grids, accepted/rejected cooks and initial candidates remain separate.
Never promote initial Manning velocities as solved fields, falsify solver flags,
or hide a source-coverage failure by extrapolating unknown terrain.

## Latest verification and access handoff (2026-10-06)

All seven `badger-decisions-native-v1` controls completed. All cleared with zero
contacts and swimmers. The hands-off control used zero guide/crew/oar commands
and cleared in 184.8 s; this is retained as an observed outcome, not automatically
called Class I or a catalog mismatch. The first additional interception control
cleared in 156.8 s with maximum roll 20.88 degrees, no contacts or swimmers. Its
actual hydraulic-plane position was -19.57 m with a -50.79 degree relative
heading. The rendered gate frame was inspected; this does not establish a
square entry or a successful-route-width envelope.

Soap's roughness-only sensitivity still failed wet overlap (0.8071). A separate
explicitly inferred dry-shore correction (1 m clearance, original 0.04 roughness)
preserved measured/wet bed and passed construction screening: overlap 0.9848,
zero extra wet cells beyond 4 m, surface-error p95 0.7673 m. Its maximum local
settling change remains 0.2308 m and needs investigation before engine shoreline
acceptance. The failed candidates are preserved. Hermit, Crystal, Bedrock and
Upset also passed construction screens; Crystal's maximum local settling change
is 0.1271 m. Upset's surface-error p95 is 0.9914 m, close to the construction
limit. These are not boat, visual, class or packaged-performance acceptance.

Editing the existing tracked `unreal/Scripts/report_rapid_assessment.py` is
blocked: direct apply_patch and approved escalated patch-helper attempts fail to
write it. The app advertises a C: workspace that does not exist; the actual repo
is D:/repos/SmokeEmIfYouGotEm. Ordinary read access and an escalated non-mutating
ReadWrite handle check succeed, and disk space is available. The exact policy
cause is not established. Do not repeat identical attempts, alter broad ACLs or
bypass the patch tool. Correct the app workspace/write scope before continuing
tracked source integration. In particular, the legacy report's automatic Class I
and halved Grand Canyon rating shortcuts have NOT been repaired. The newer
decision report does not use them.

At this handoff the remaining Badger interception controls and Colorado cooks
are running, with House Rock and four other native map imports already queued.
Inspect their existing sessions/logs before launching any replacement work.
No final class comparison, packaged 20 FPS acceptance, commit or push is claimed.

## Commit checkpoint (2026-10-06)

The three additional Badger interception trials all completed with
`section_cleared`. The queued House Rock, Georgie, Sockdolager, Grapevine and Horn
Creek imports also finished. They remain local construction candidates, not
registered or accepted playable difficulty results. No solver/editor process was
active when the checkpoint rebuild began.

Verification for the checkpoint: 110 targeted Python tests passed; the Unreal
Editor Development build succeeded (`tmp/catalog-checkpoint-build-v1.log`); all
four fresh native tests passed (`tmp/catalog-checkpoint-native-v1/index.json`):
RapidChallengeProfiles, SharedFeatureKinematics, LinkedRunBoundaries and
TrialSteeringSchedule. Badger's 12 runtime dependency hashes were checked.
Native tests use NullRHI and do not establish rendering or performance. The
known legacy assessment-report limitations above are not claimed fixed.

The commit includes source, calibration tools, the playable Badger map/material
and its version-3 runtime dependencies. Raw acquisitions, rejected candidates,
five uncalibrated map imports and temporary trial/cook outputs remain local and
preserved. This is an incremental checkpoint, not all-99 acceptance or a packaged
20 FPS claim. Git staging/build access succeeded; that does not establish that
the earlier tracked-source patch access problem has been repaired.

## Local research exclusions (2026-10-06)

The proposed research-data archive was not committed or uploaded. At the user's
direction, exact `.gitignore` entries keep these captures, construction inputs
and five unaccepted map imports local. Files and source manifests remain on disk;
their checksums, attribution, coordinate systems and inference limitations are
preserved. The tracked playable Badger map and its v3 runtime are not ignored.

Interpret the retained local versions as follows:

- `catalog_runtime_2026_10_v1` and `v2` remain rejected Badger candidates, retained
  to explain the interpolation/collision mismatch. Only Badger v3 is registered
  in the normal frontend and packaging list.
- `water_boundaries_2021_capture` and `v2` through `v4` are incomplete acquisition
  records. Their `.partial` files are failed downloads, not usable geospatial
  inputs. The complete water-classification capture is `v5`.
- Earlier solver-input versions and terrain/evidence alternatives are preserved
  as research history, not silently substituted for current runtime inputs.
- House Rock, Georgie, Sockdolager, Grapevine and Horn Creek map imports and v3
  runtime files are construction candidates. Their presence does not establish
  gameplay calibration, final visuals, normal-menu availability or 20 FPS.

When a candidate becomes an accepted playable increment, remove only its exact
ignore entries and commit the map with all runtime dependencies. Do not force-add
raw acquisition trees or rejected versions. These exclusions change neither
gameplay nor difficulty acceptance and do not delete the local research.

## Next implementation steps

1. Finish Badger's matched native comparisons, including actual entry-hydraulic
   interception and uncontrolled drift. Quantify approach/timing tolerances and
   inspect the complete descent, not just intended route labels.
2. Import House Rock and the four accepted Colorado construction candidates with
   native collision probing. Register successful maps in the normal frontend,
   implement their documented solid obstacles and shared hydraulics, and run
   prepared/mistake/recovery controls before any class conclusion.
3. Extend the construction/import path to every missing entry, resolving the
   stated identity and coverage gaps rather than silently aliasing existing maps.
4. Run each existing section's prepared control before width/timing sweeps. Keep
   failures attributable to driver, route, terrain or hydraulics. Test linked
   descents and rescues, not only checkpoint-isolated cruxes.
5. Produce the complete per-entry comparison only from exercised native outcomes,
   then rebuild/test the package and commit/push. No completion by source-text
   tests, downloads or generated manifests alone.
