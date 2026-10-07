# Every catalog rapid implementation and calibration

The October 6 scope includes all 99 indexed catalog entries: calibrate the 72
existing trial sections and build the 27 missing playable sections. Badger's
addition brings the current inventory to 73 test sections and 26 still missing;
this is construction coverage, not calibration acceptance. Upper Gorge
duplicates and named aggregate reaches remain identified; they are not 99
distinct surveyed rapids. No all-entry class-match conclusion is established.

## Completion requirements

The user explicitly chose **one uninterrupted, geographically continuous
full-river descent** on October 6. Isolated rapid maps and marked travel
transitions do not fulfill this request. Preserve the raft, crew/swimmers,
rescue state and water clock across source/terrain streaming boundaries. The
Colorado route is the portfolio's Lees Ferry–Pearce Ferry run, not merely Hance
or a chain of independently launched rapid scenes. Retain the current playable
maps until the continuous replacement passes its integration checks.

The active goal also requires filling missing terrain, vegetation and other
environment content along every river, not only around catalog points. Keep
survey-derived geometry distinct from modelled bed and art-directed vegetation;
do not claim individual trees are measured without supporting imagery/lidar.
Environment streaming, solid collisions, water/foam, rescue state and normal
packaged launch must be validated together for each completed continuous run.

`build_colorado_continuous_assembly.py` registers the captured USGS profile and
rapid construction charts into a common east/north/ellipsoid frame. It preserves
each chart's local hydraulic station and explicitly lists uncovered connecting
reaches. Its output is a construction contract, not playable completion or
permission to concatenate independent flow grids. Native source-aware handoff,
connecting geometry/water and combined seam validation are still required.

### October 6 construction and geographic checks

#### Bounded terrain import and source-location follow-through

The native continuous importer now builds at most 32 terrain chunks per batch.
Each batch verifies its rendered heights, Chaos collision, assigned wet-bed
samples and grounded dressing before saving. It then reopens only its own fresh
construction world and checks that every saved spatial descriptor survives and
is unloaded, including earlier batches. This releases the editor's creation
references without deleting assets, simplifying collision, or disabling Nanite.
The material and dressing meshes retain explicit strong references across world
reloads. Native Nanite export and static-mesh compilation are synchronous only
during this offline import; the previous settings are restored afterwards.

Two preserved attempts (`colorado-continuous-map-batched-native-v1.log` and
`v2.log`) failed after saving a first batch: pin/unpin did not release newly
created actors, and Nanite export raised a compilation ensure. V3 safely refused
an unavailable console-variable spelling before map creation. After correction,
the fresh V4 import completed with no compilation ensure and `saved=1`:
`tmp/colorado-continuous-map-batched-native-v4.log`. Three batches released
49, 46 and 21 spatial actors at completed chunk counts 32, 64 and 76. All 76
Nanite proxies passed their build checks; 3,800 collision probes had maximum
error 0.317972 cm, 103,369 wet-bed probes 0.261719 cm, and 1,309 artistic
vegetation instances 0.273296 cm. Badger, House Rock and Hance registered 68
authored feature centres. This is the existing two-core construction coverage,
not a completed full-river map or proof of full-river memory/performance bounds.
The original NaniteStartV1 map's 204 files remain byte-identical to the earlier
fingerprint `d6da6611fce1f4e690c77f41b8bfc61a1ff408d2633e5d662ac0083ec68d6d8b`.

The matched rendered rescue drill on BatchedStartV4 passed in
`tmp/colorado-continuous-batched-rescue-v2/colorado_continuous`: 111.4 simulated
seconds, 208.86 wall seconds, ending at station 1,370.224871 m with one completed
guide reentry, 148 oar strokes, zero checkpoint restores, zero hull contacts and
zero dry-centre time. Motion remained finite; maximum roll was 1.041106 degrees,
pitch 0.409205 degrees and speed 2.766791 m/s. The production hull/render check
again reported 26,610 vertices, 38,344 triangles and zero discrepancy. The source
seam gate has one swimmer; the next gate shows the guide climbing in, and the
exit has no swimmer. Start, seam, climb and end captures were visually inspected.
Dependencies stayed unchanged during the run. This is controlled overboard
recovery on the short construction map, not natural washout, distant rescue
streaming, rapid-class calibration, normal packaged launch or 20 FPS acceptance.

The read-only saved-map check in
`tmp/colorado-continuous-saved-registration-v2.json` verifies all 68 serialized
features and their full-chart identity after reopening. Their stations span
12,772.741596-123,976.685451 m, outside this short rendered drill: retaining them
does not mean their downstream terrain or gameplay is complete. The first
verifier attempt encountered protected native struct fields; V2 reads their
native text export without changing field visibility or game behavior. The
separate native unload/reload check passed for all 76 proxies with exactly zero
collision-height change and no package saves:
`tmp/colorado-continuous-batched-terrain-residency-v1.log`. Colorado Python
regressions remain 128/128 passing. Both successful incremental editor builds
and these native checks apply to the current dirty workspace, not a pushed
release or an accepted full-river replacement.

The sequential source-composition job for cores 24-95 also finished. Tile 76's
33 flagged survey/profile cells all clamp to local station zero, outside its
91,200-92,400 m core. Actual `TerrainMosaic` queries over sources 74-78 selected
tile 75 for every flagged centre and preserved the measured elevation exactly
(maximum difference 0 m). No captured bed was edited. This is ownership evidence,
not general seam or hydraulic acceptance. The six-core solver continuation is
still separate and has not yet passed its final discharge review.

The Chilko source ledger rechecks the operator's public itinerary. Its
aggregate Lava Canyon-to-Taseko sequence supplies no Green Mile or Miracle Canyon
boundaries; its linked overview image could not be fetched and was not visually
inspected. Do not turn the operator's trip mileage into individual rapid bounds
or count shared ROAM provenance as independent confirmation. Eleven location
tests pass; `tmp/chilko-catalog-location-audit-v11.json` binds the deduplicated ledger.
No unsupported Chilko label was moved.

#### Chilko upstream terrain and imagery registration correction

The public 2023 LidarBC tile `bc_092o091_xli1m_utm10_20230918_20231006.tif`
does cover the published Bidwell points; the old archived game crop does not.
The bounded capture `tmp/chilko-bidwell-source-crop-v1.npz` contains 2,076,000
native one-metre pixels, all finite. Its actual compound CRS is EPSG:6653
(horizontal EPSG:3157, vertical EPSG:6647), and its catalogue record and OGL-BC
attribution are retained. Crop SHA-256 is
`33d0ebfdb3a25ab62ecff8c7e42cdfe5677daf595aba738f658b367c27732de2`.
Only the range-read crop is hashed; no full-tile checksum verification is claimed.

The Chilko builder now requires an explicit construction interval, verifies the
LiDAR and imagery hashes, and rejects out-of-coverage imagery rather than allowing
bilinear edge clamping. Inspection uncovered a further registration bug: the
requested Sentinel crop bounds differ from the actual raster origin. The builder
now uses each captured band's native origin/spacing/shape and explicitly
transforms EPSG:3157 terrain coordinates to EPSG:32610 imagery coordinates. It
also transforms the FWA route to EPSG:3157 rather than using WGS84 UTM as a
substitute. RGB alignment, radiometric encoding and nodata are checked. Twenty
capture/location tests pass, including regression controls for the displaced
origin and mixed coordinate systems. The inferred DEM-derived water surface and
shoreline are no longer described as measured hydraulic survey.

The preserved V1 candidate predates these registration corrections. Fresh
`tmp/chilko-bidwell-geographic-evidence-v2` covers FWA construction stations
38,000-39,200 m, not named rapid boundaries. Both published Bidwell points fall
in its channel, respectively 2.9215 m (BC Whitewater) and 0.9269 m (CalTopo) from
its sampled centreline. Its dominant four-connected channel has 38,938 cells;
117 cells occupy small disconnected components and still require hydraulic
review. Four submerged boulders are inferred from bright-water patches, not
surveyed rocks. The classes image was visually inspected; it is a source
diagnostic, not an engine screenshot or visual acceptance.

`tmp/chilko-bidwell-geographic-inputs-v1` builds a 596-by-33, two-metre unsolved
scenario spanning about 1.19 km at a 45 m3/s construction target. Wet-cell metric
ratios range from 0.9559 to 1.0913; the solver still lacks curved-grid metric
terms. No new cook, runtime export, map replacement, rapid acceptance or packaged
performance claim follows from this input. The existing playable map is preserved.
Green Mile/White Kilometer identity and Miracle Canyon boundaries remain
unresolved; the repeated public guide link resolves to the already indexed
CalTopo map, not independent new coordinate evidence.

The next range-read source crop, `tmp/chilko-post-bidwell-source-crop-v1.npz`,
is 2,590 by 1,900 pixels with 34,230 actual nodata pixels (99.3044% valid), despite
its rectangle lying inside the native tile's bounding box. Its SHA-256 is
`16ed304be497882dcbe47983d984ad53bf39f3f39752b7270015e2c84c0ad589`.
The 39,000-40,400 m construction window has no gaps and was built separately
with a 200 m overlap against the Bidwell candidate. The proposed 40,200-41,600 m
window has 4,170 missing terrain pixels along its eastern edge; it must obtain
adjacent source coverage before construction. No nodata was filled, edge-clamped
or described as valid terrain. Source extents alone are not coverage acceptance.
The legacy colour-report module still imports successfully; its independent old
sampling routine is not claimed corrected by the evidence-builder fix.

That downstream construction completed in
`tmp/chilko-post-bidwell-geographic-evidence-v1`. Comparing identical geographic
cell centres over the 200 m core overlap found exact agreement in captured DEM
and white-water brightness fraction, but not in independently inferred bed:
3,768 shared wet centres had bed differences of 0.06525 m median, 0.41045 m p95
and 0.79572 m maximum. Surface-reference maximum difference was 0.03955 m; 40 of
the upstream candidate's 3,808 wet centres were dry in the downstream candidate.
These independently generated beds must not be stitched into a claimed
continuous run. The combined 38,000-40,400 m evidence grid completed in
`tmp/chilko-bidwell-continuous-evidence-v1` from a single native capture:
`tmp/chilko-bidwell-continuous-source-crop-v1.npz`, 3,450,000 finite pixels,
zero nodata, SHA-256
`04b0793d79b1472a53e0579a6c50c9aad7dabb5b86b32c2cafbd8cde16ac8bf7`.
Its classes image was inspected. The single 1,190-by-33 input in
`tmp/chilko-bidwell-continuous-inputs-v1` spans 2,378 hydraulic metres without
an independent-grid splice. Wet metric ratios range 0.9481-1.1153; these remain
an explicit model limitation. This input supersedes the shorter construction
inputs for a connected-reach trial, not the production map.

A distinct small construction cook was then started in
`tmp/chilko-bidwell-continuous-cook-v1`: existing joined solver binary, finite
volume HLL/order 2, 24,000 fixed 0.05 s steps, frame interval 2,400, CFL 0.2,
bed-source scale 1, authored forcing 0, roughness scale 1, initial-mass
preservation and fixture calibrations disabled. The larger Colorado continuation
was left running and unchanged. The Chilko cook is now terminal, exit 1, with
all 24,000 steps and 11 frames preserved below the scenario-ID subdirectory.
Do not launch it again unchanged. The Colorado cook remains separate and live.

Chilko's diagnostic review is `tmp/chilko-bidwell-continuous-review-v1`.
All states remained finite, but this candidate is rejected: wet IoU 0.84868,
2,457 extra wet cells, depth-change p95 0.19845 m between the last two frames,
and final exact inlet/outlet fluxes 45.0/36.03286 m3/s. The initial-to-final mass
change was 65.8693%; this is not silently excused as open-boundary storage or
marked passed. Final wet speed maximum is 4.79169 m/s, distinct from the reported
32.2314 m/s peak in frame zero. The latter is traceable to initial station 494 m:
only one two-metre channel cell at depth 0.69808 m receives the whole 45 m3/s
target. Neighbouring sections are wider; nearby cells sit just above the inferred
surface's 0.15 m classification tolerance. This is a DEM-derived water-mask /
conveyance-initialization problem, not evidence of a real 32 m/s Bidwell current.
The source DEM remains untouched. Correct the inferred classification using
source support before another candidate; do not simply raise a velocity limit,
force an acceptance flag, or enable this rejected field in the game.

`compare_river_cook.py` now keeps all anchor comparisons under `reference_anchors`
and populates `measured_anchors` only for an explicitly measured source kind.
Inferred-method/measured-kind contradictions are rejected. The Chilko review
correctly records `inferred_dem_surface_reference` with no measured anchors;
the numeric surface comparisons are unchanged. No native map, packaged game,
difficulty acceptance, 20 FPS result, commit or push is claimed for these new
Chilko construction results.

#### Chilko mapped channel-core correction and matched cook review

The spectral-only V2 core-retention candidate added 83 low-relief interior
cells but left station 494 m with one wet solver cell and a 32.245 m/s initial
peak. It was not cooked. A separate official BC Freshwater Atlas river polygon
was captured through `capture_chilko_fwa_polygon.py`, layer 36 of the public
BCGW delivery service, WATERBODY_KEY 328961612 / group CHIR. The full 7,569-vertex
polygon is preserved in `tmp/chilko-fwa-planform-v1.geojson`, SHA-256
`b2566f482e3ca0b54b46088c0321e2d4a60c3d07a078b5ccac0190f73eafd7bb`,
with its query, identity, coordinate frame and OGL-BC attribution receipt. This
is mapped planform, not flight-day shoreline, water stage, bathymetry or named
rapid boundaries.

V3 retains additional channel core only where the three-metre-eroded mapped
interior or existing inferred interior has at least 0.5 multi-date spectral
water support and DEM height at most 0.25 m above the inferred surface. These
are explicit classification assumptions, not measurements of underwater bed.
The evidence contains 699 newly retained cells. Source DEM arrays and retained
dry-terrain bed values remain identical to V1. Station 494 m now has seven wet
solver cells and maximum initial speed 5.36772 m/s there, versus 32.2314 m/s in
V1. The complete initial grid's peak is 8.26344 m/s at station 580 m.

The distinct V3 cook completed 48,000 steps / 2,400 simulated seconds with 21
frames in `tmp/chilko-bidwell-continuous-cook-v3`. It still exits 1: the generic
initial-to-final mass-change test reports 64.1788%, and is not disabled or
overridden. The final exact face inflow/outflow is 45.0/44.97351 m3/s; interior
discharge p5/p95 is 44.94960/44.98940 m3/s. Last-frame depth-change p95 is
0.00002755 m, maximum 0.012676 m. Final wet speed maximum is 4.41963 m/s.
These demonstrate settling and transported discharge, not physical validation
of the inferred geometry. Wet IoU remains only 0.85850, with 2,295 extra wet
cells and four missed wet cells. The candidate is not promoted.

For a duration-matched comparison, `tmp/chilko-bidwell-continuous-review-v3-at1200`
uses frame 10 at 1,200 simulated seconds: wet IoU 0.86141, 2,240 extra wet cells,
outflow 37.66823 m3/s and settling p95 0.15844 m. The improvement from this frame
to the final V3 frame is additional warmup, not solely the source-mask change.
The final profile and depth/speed/overlap images were inspected: residual wet
expansion is visible along both margins and the surface remains above its
inferred reference. Next work must address the inferred conveyance/bed model,
including its variable 0.035-0.05 Manning assumption versus the scenario's
scalar 0.045, without altering captured terrain or weakening acceptance.

The runtime exporter's colour and water-classification sampling now uses the
same validated EPSG:3157-to-32610 native-pixel transform as the evidence builder.
It verifies captured array hashes/shapes, uses reflectance-scaled NDWI, includes
NIR nodata in validity and refuses out-of-coverage colour sampling rather than
clamping. This corrects exporter code only; no new runtime assets were exported
or existing drapes replaced. Twenty-three source-location/registration tests
pass, including exact runtime/evidence sampling agreement. The independent
legacy colour-report sampling path is still not claimed repaired.

Public literature and map links were rechecked without deriving new coordinates:
the SierraRios overview image remains unavailable through the browser, and its
annotated topo collection is not accessed without authorization. Green Mile /
White Kilometer identity and Miracle Canyon boundaries remain unresolved.
No guessed label, new normal-menu map, packaged FPS claim, commit or push follows
from this construction increment. The separate Colorado continuation remains
live; inspect its existing session before starting any replacement cook.

#### Chilko consistent roughness and downstream native-tile gap repair

V4 isolates the bed/solver roughness mismatch: both inference parameters now
use 0.045, matching the unchanged scalar solver coefficient. Captured DEM,
river mask and every dry-terrain bed cell remain identical to V3. Only inferred
bed changes (delta p5/median/p95: -0.27856/-0.11951/-0.00110 m). The fresh
48,000-step cook completed in `tmp/chilko-bidwell-continuous-cook-v4`, with
21 frames. Its generic validation reports true, but initial-to-final mass
change is still 48.4868%; that flag is not shoreline or physical acceptance.

`tmp/chilko-bidwell-continuous-review-v4` reports exact inlet/outlet discharge
45.0/44.98170 m3/s, interior p5/p95 44.94954/44.99076 m3/s, last-frame depth
change p95 0.000000431 m / maximum 0.0002016 m, and final wet speed maximum
4.54619 m/s. Wet IoU improves only to 0.86795 (2,118 extra wet cells; four missed).
Median signed surface residual against the inferred reference remains +0.46341 m,
with p90 absolute residual 0.58471 m. V4 is not promoted to the game.

One bounded inferred-bed calibration is being constructed as V5 using the
existing `calibrate_river_bed.py`: V4's settled residual, relaxation 0.7,
15 m smoothing and 0.75 m maximum step. The actual step ranges from -0.43663
to -0.01426 m in `tmp/chilko-bidwell-inferred-bed-step-v5.npz`. This is calibration
to an inferred DEM-derived reference, not new bathymetric measurement. The V5
builder completed, but was rejected before cooking: changing bed depth caused
the boulder-inference height threshold to admit an eighth seed (V4 has seven).
This is not a controlled depth-only comparison. V5 is preserved, not cooked.

`correct_inferred_bed` now applies calibration after boulder inference and only
to class-2 cells, preserving dry terrain, rock heights, rock classes and seed
selection. It validates correction coordinates/arrays and keeps the existing
minimum inferred water depth. Tests exercise immutability, rock preservation,
finite ordered corrections and the depth cap. The corrected V6 builder completed.
Actual V4/V6 comparisons verify equality of captured DEM, all class codes, every
non-class-2 bed cell and the complete boulder definitions (seven seeds). The V6
input has 1,190 by 33 cells and the same geographic frame and source reference.
Its distinct 48,000-step solver trial is live in session 72102, output
`tmp/chilko-bidwell-continuous-cook-v6/chilko_geographic_construction_38000_40400_v6`.
It uses the same HLL/order-2, CFL 0.2, 0.05 s step, 2,400-step frame spacing,
45 m3/s target, 0.045 roughness and disabled mass-fix/fixture calibration settings
as V4. Inspect this session before any replacement cook. It is not yet reviewed
or accepted for runtime export.

Official catalogue lookup at EPSG:3157 (445040, 5753300) identified the adjoining
2023 `bc_092o092_xli1m_utm10_20230918_20231006.tif` tile. Its native compound
CRS and one-metre float grid were checked. The bounded 293-by-1,700 capture in
`tmp/chilko-east-gap-source-crop-v1.npz` has 61,627 genuine nodata pixels;
its rectangle alone is not complete coverage. SHA-256:
`8e5b8169474c833686e549ccacb943cbd8ed045a261bd147463fe6c5f193d0ad`.

`mosaic_lidarbc_crops.py` verifies each source hash, native coordinate frame,
spacing and array geometry, preserves the first finite pixel, fills only gaps
from subsequent inputs, records per-pixel ownership, and leaves unresolved
gaps as NaN. It never averages source disagreements or resamples terrain.
The exact downstream window [443311,5752647,445044,5754155] now has all 2,613,364
native cells: 2,609,194 from the existing western capture and 4,170 from the
new eastern capture. Output `tmp/chilko-downstream-native-mosaic-v1.npz`, SHA-256
`b44d231be451c83d97bf81114012eef6e57f4af7c372e5e7407a4c484336f75e`.
The 148,565 overlapping valid cells differ by 0.03998 m p95 / 1.29993 m maximum;
the first source remains authoritative there. At the actual filled-gap boundary,
825 independent comparisons differ by 0.02002 m p95 / 0.09998 m maximum.

`tmp/chilko-downstream-geographic-evidence-v2` completed for construction
chainage 40,200-41,600 m. Its source-class image was inspected; there are 46,092
inferred wet cells, 293 retained core cells and no classified bright-water
patches or inferred foam boulders. This neither proves absence of rapids nor
locates Green Mile. Do not splice this independently inferred bed directly onto
the upstream one; a consistent connected model and seam validation remain
required. Twenty-eight capture/mosaic/location tests pass, including gap/ownership,
north-up crop alignment, source-tamper, coordinate-frame refusal and calibrated
bed/rock separation tests. No new playable scene,
packaged performance claim, commit or push is made by this source extension.

#### Continuous rapid registration and downstream source ownership

The continuous-map contract now binds existing Badger Creek, House Rock and
Hance profiles to their hash-verified, common-origin source charts. Native
registration projects each centre through world coordinates and rotates its
direction into the full-river chart. It preserves the authored height,
wavelength and spilling parameters; it does not survey new obstacles or prove
that finite feature footprints on differently curved charts are identical.
The serialized configuration is tied to the loaded chart fingerprint. A failed
chart reload must clear the fingerprint, and a mismatch must refuse the feature
set rather than falling back to a local map's stations. Both full and incremental
Editor Development builds succeeded. All four fresh native tests passed in
`tmp/continuous-rapid-registration-native-v1/index.json`, exercising the real
assembly and full-river chart: 17 Badger, 11 House Rock and 40 Hance sites.
Maximum centre errors were respectively 0.002615, 0.002810 and 0.909459 cm;
world-space directions and kernel parameters were preserved. The actual surface
construction regression also verifies that registered sites enable the shared
crest/foam path without an old-map-name match, and that an identity mismatch
disables feature kinematics and refuses surface readiness. This fixes a missed
legacy map-name gate. These NullRHI tests and the 128 passing Python Colorado
tests do not establish visual, boat, full-river or packaged-performance acceptance.

The fresh 36-core input build and join completed successfully in
`tmp/colorado-continuous-inputs-mixed-thirtysix-joined-v1`: core coverage
0-43,200 source metres, exterior halo through 43,501.466430 m, one 21,641 x 167
two-metre hydraulic grid. All 36 inputs were rebuilt against the same 1,036-chunk
terrain manifest, not reused from the smaller 24-core terrain. The join rejected
missing wet coverage by construction and classified 1,537,590 padding cells dry.
All output dependency hashes were verified; build-report SHA-256 is
`db28461c515d1ad2e74a0c91bc9c12dce7f6298c8253c56f6bdc92dee12f967e`.
This is an unsolved input, not another running cook or a playable 43.2 km run.
The six-core continuation remains the only live solver. Current Python regression
rerun: 128 Colorado and 11 Chilko source-location tests passed.

The disjoint source-composition job for cores 96-119 completed successfully.
Tiles 102 and 104 reported respectively 1 and 2,407 survey/profile conflicts,
all at endpoint-clamped local station zero outside their core intervals.
An actual five-source `TerrainMosaic` query over cores 101-105 checked every
flagged cell centre: owners were respectively tile 101 and tile 103, and the
selected heights matched the preserved survey values exactly (maximum error
0 m). Do not modify captured bed elevations to fix these outer-margin flags.
This resolves those particular ownership questions, not general downstream
seam validation or playable acceptance. The six-core continuation cook remains
the sole live solver; it has not yet passed its final discharge review.

- Native Colorado registration v2 passed 2,664 projection probes over the
  87,184-point route and all 15 reach charts, including Hance. Maximum route
  round-trip error was 0.000238 m. Receipt:
  `tmp/colorado-continuous-native-registration-v2.json`. This is coordinate
  verification, not connected water, a full-hull descent or FPS acceptance.
- The bounded Granite shore candidate remains rejected: stage p95 error
  1.114 m and water-mask IoU 0.8683. No failed candidate was promoted.
- The user rejected estimated Chilko placements. The October 6 source ledger
  records BC Whitewater's embedded map points, the corroborating public CalTopo
  Bidwell point, official BC naming, the NRCan map and DFO report, and eyewitness
  sequence evidence. Actual runtime-chart comparison places existing inferred
  Bidwell/White Mile starts about 6.08/4.84 km downstream of the published points.
  These representative points are not exact rapid boundaries. The previous
  September 29 geographic interpretation is explicitly superseded.
- Green Mile is bracketed by the source Bidwell and White Mile markers, upstream
  of the existing scene. Its endpoints and Miracle Canyon's location remain
  unresolved. No midpoint, elapsed-time conversion or unproven alias is accepted.
  `audit_chilko_catalog_locations.py` validates the runtime chart against its
  terrain-manifest hash before comparing locations. Receipt:
  `tmp/chilko-catalog-location-audit-v2.json` (supersedes raw-centreline v1).

### Extended Chilko identity review

Additional Chilko literature review (October 6) read the complete six-page
1987 Jerry Michalec expedition account and compared the September 2007 Wetcoast
descent, Florian Scharlock's 2011 trip report and SierraRios' guide. The 2007
account explicitly places White Kilometer between Bidwell and White Mile. The
2006 account puts Green Mile in that same broad bracket. This establishes neither
synonymy nor two separate sections; the evidence ledger now records that identity
question and the audit refuses flags that promote it to confirmed placement.
Miracle Canyon remains named in the 2025 eyewitness article but not registered
to a geographic point by the inspected sources. No runtime label was moved.
The historic BC OpenMaps link is a session URL, not a captured waypoint dataset.
The subsequent John Collins 2004 account independently supports White Kilometer
between Bidwell and White Mile and describes the White Mile canyon exit, sharp
right turn and leftward current into rock. These are useful qualitative clues,
not uniquely registered coordinates. The two Green Mile accounts share ROAM's
naming context and cannot be counted as independent proof of a separate rapid.
This is supporting research, not a newly delivered playable section. Eight
location-audit tests pass; the expanded receipt is
`tmp/chilko-catalog-location-audit-v5.json` supersedes v4 after further source
quality checks. Cecil Kuhne's 2025 public book preview adds historical naming
but no Green Mile/Miracle Canyon coordinates. Its reproduced opening arguments
are not measured terrain or independently verified hydraulic claims. A 1994
Usenet discussion misdates and misplaces the accident relative to the survivor
account; its approximate locations are explicitly rejected as geographic control.
Only the public preview text was accessible, not the full book or an inspectable
map image. Neither source justifies moving a runtime label.

The next research pass found an additional naming lead in the 2006 ROAM-trip
narrative: a narrow, boiling columnar-basalt gorge called **Magic Canyon** follows
White Mile and precedes the Taseko confluence. This may relate to the 2025
**Miracle Canyon** name, but the shared operator context, similar setting and
sequence do not prove an alias. The evidence ledger and ninth location test
preserve that distinction; `tmp/chilko-catalog-location-audit-v7.json` supersedes
v6. No runtime coordinates or catalog entries were changed. The older account's
incorrect confluence naming and conflicting accident recollection are explicitly
excluded from geographic control.

Parks Canada's 1978 *Wild Rivers: Central British Columbia* is a new historical
lead, not an inspected map: only indexed excerpts for printed pages 47 and 49
were available, describing the Chilcotin and the Chilko below the Taseko. The
PDF fetch failed (web 502; direct TLS certificate expired). No security checks
were disabled and no upper-Chilko rapid placement was inferred from those pages.

### Continuous Colorado source construction

`build_colorado_continuous_windows.py` partitions the full 453,334.028 m captured
profile into 378 consecutive 1,200 m core tiles, with 300 m source halos on each
side. Raw survey vertices, provenance flags and source stationing are preserved.
These are construction tiles, not 378 accepted playable map sections. Output:
`tmp/colorado-continuous-source-windows-v1`.

The first two tiles have actual classified shorelines and 3DEP terrain crops in
`tmp/colorado-continuous-water-start-v1` and
`tmp/colorado-continuous-terrain-start-v1`. The pool-bed source stops short of
part of the first crop. The importer now explicitly supports bounded partial
survey reads, retains missing cells as NaN and records off-raster coverage;
`tmp/colorado-continuous-bed-start-v2` contains 4,226 and 34,475 surveyed cells.
Other wet bed remains inferred, not measured.

The first geometry overlap comparison found a real construction seam: per-tile
depth bins restarted at local zero. Global-station bins reduce the maximum
shared wet-bed discrepancy at station 1,200 m from 0.245911 m to 0.000061 m
over 30,848 cells, without changing the shoreline or surveyed bed. Receipts:
`tmp/colorado-continuous-bed-seam-original-v1.json` and
`tmp/colorado-continuous-bed-seam-global-bins-v1.json`. The corrected second grid
is `tmp/colorado-continuous-evidence-start-v2/tile0001`; tile 0000 remains valid
in `tmp/colorado-continuous-evidence-start-v1/tile0000` because its origin is zero.
This is source-grid seam evidence, not Landscape/cooked-water seam acceptance.

Native control cooks for the original two inputs completed sequentially in
`tmp/colorado-continuous-cook-start-v1` (36,000 steps, 0.05 s, frames every 3,000;
finite volume/HLL/order 2/CFL 0.2, fixture calibration and authored forcing off).
Tile 0000 fails the unchanged shoreline screen (IoU 0.884628); tile 0001 passes
all four construction screens (IoU 0.928163, surface-error p95 0.531958 m,
discharge-error p95 1.7202%, settling-depth p95 0.004958 m). Reviews are in
`tmp/colorado-continuous-review-start-v1/tile0000` and `tile0001`. Neither result
establishes physical-space streaming continuity, engine acceptance or FPS.

The canonical terrain exporter produced 57 fully covered 127-by-127 vertex
chunks on a common 2 m geographic lattice; all shared encoded edges agree.
It reports 38 incomplete outer chunks rather than inventing their missing
terrain. Output: `tmp/colorado-continuous-terrain-chunks-start-v1`. One common
height encoding preserves shared edges; terrain and underwater inference remain
separately sourced. Native import saved the terrain-only construction map
`/Game/RaftSim/Maps/Continuous/L_Colorado_TerrainStartV1`: 2,850 actual collision
probes across all 57 chunks had maximum height error 0.253145 cm
(`tmp/colorado-continuous-terrain-native-v1.log`). This NullRHI check is not a
rendered descent; vegetation and connected water are not complete.

`build_colorado_catalog_scenario.py --terrain-chunks` now samples those exact
decoded Chaos-diagonal triangles, with verified heightfield hashes, geographic
corners and matching construction inputs. This replaces the independent
2017-height stretched reference for continuous candidates. Tile 0000's maximum
initial velocity changes from 5.956 to 2.607 m/s with unchanged discharge and
roughness. That is input geometry evidence, not a converged improvement. The
legacy runtime exporter refuses common-grid cooks rather than regenerating a
different terrain under them. Forty-eight targeted tests pass, including
triangle interpolation, seam agreement, tamper refusal and legacy-export refusal.

The unchanged-parameter tile 0000 cook completed from
`tmp/colorado-continuous-inputs-canonical-v1/tile0000` into
`tmp/colorado-continuous-cook-canonical-v1`. Its review in
`tmp/colorado-continuous-review-canonical-v1/tile0000` still fails shoreline
agreement (IoU 0.885300; 4,241 extra wet cells over 4 m from the source), despite
passing surface-error p95 0.568859 m, settling p95 0.015957 m and discharge-error
p95 3.1468%. Do not promote this candidate or relax the unchanged 0.9 threshold.
The finer 2021 DEM release was checked: public catalog
metadata identifies a 965,060,301-byte archive, but the manager download returns
HTML and the catalog-listed content bucket returns HTTP 403. No archive was
captured, no protected access bypassed, and no DEM water pixel used as bed.
This source limitation does not prevent common-grid/engine implementation with
the already captured terrain. The next required integration is common-frame
water streaming and water/terrain seam verification, not concatenation of local
curved charts.
Do not duplicate an active cook. Original inputs remain immutable in
`tmp/colorado-continuous-inputs-start-v1`. After the controls complete, review
their actual final fields, generate/cook the corrected second input, and compare
physical-space water and collision seams. Independent local hydraulic charts
still require source-aware handoff or a common geographic water grid; reusing
equal local station indices across tiles would copy water to the wrong place.
No normal map or launch entry has been replaced by these candidates.

### Shared frame and joined-water inlet repair

`tmp/colorado-shared-hydraulic-frame-v1` defines one geographic hydraulic frame
for the full captured route. Native adapter verification passed 7,806 probes
over its 225,296 points (0–450,578 m hydraulic station), with maximum round-trip
error 0.0000594 m: `tmp/colorado-shared-native-frame-v1.json`. Hydraulic station
differs from raw survey station after common smoothing/reparameterization; both
remain registered. This is coordinate verification, not solved curvilinear CFD.

The first two shared-frame inputs have exact common bed/state values over their
overlap. `join_colorado_continuous_scenarios.py` combines them into one 1,274 by
167 cell, 2 m native domain, preserving the initial discharge and inlet profile.
Only 16 incomplete terminal halo columns are removed; all 0–2,400 m source core
coverage remains. Lateral padding is explicitly classified dry, never invented
water. Terrain, source, frame and input hashes are checked before joining.

The first joined cook failed because the new join exporter saved its transposed
bed in Fortran order, while the production NumPy loader interpreted it as
row-major. At west face 70, intended bed 923.094530 m was read as 928.987686 m.
`tmp/colorado-continuous-cook-joined-diagnostic-v1` preserves the detailed native
failure. The exporter now writes contiguous row-major arrays; the shared native
loader refuses unsupported/missing storage order rather than silently scrambling
geographic cells. No inlet physics, wet/dry threshold or source height was changed.
Seven Python join tests and all six isolated native regression suites pass,
including float/bool storage-order refusal and row-major coordinate checks.

Corrected immutable inputs are `tmp/colorado-continuous-inputs-joined-v2`; the
36,000-step cook completed in `tmp/colorado-continuous-cook-joined-v2/`
`colorado_continuous_joined`, using the isolated current-source solver
`tmp/troublemaker-row-solver-colorado-joined-v1/raftsim_water_solver.exe`.
Native finite-state validation passes. The final construction review records
global shoreline IoU 0.915732, stage-error p95 0.535618 m and settling-depth p95
0.019686 m, but exact face discharge error p95 is still 8.4423% (outlet
207.190197 versus target 226.534773 m3/s). Do not export this unsettled baseline.

The per-core review `tmp/colorado-continuous-review-joined-cores-v1` additionally
shows first-core (0–1,200 m) shoreline IoU 0.887855 versus second-core 0.941633.
The joined average had hidden the local failure. Reviews now screen each
registered source core, and runtime export refuses stale joined reviews without
those passing core checks. No shoreline threshold has been loosened.

`continue_colorado_catalog_cook.py` prepares an immutable exact-state continuation,
not the existing bed-edit warm start that recalculates depths. Every saved depth,
velocity, momentum and wet-mask value is retained, including small dry films;
changed beds, nonfinite states and nonconstant boundaries are refused. Four
targeted tests pass. Constant boundaries, zero authored forcing and disabled
fixture calibrations permit restarting the native clock at zero, explicitly
recorded in provenance. The fresh inputs are
`tmp/colorado-continuous-inputs-joined-continue-v1`; the 18,000-step / 900-second
continuation in session 52619 completed successfully into
`tmp/colorado-continuous-cook-joined-continue-v1`. Its per-core review is
`tmp/colorado-continuous-review-joined-continue-v1`: discharge error p95 falls
to 0.78097% and settling p95 to 0.001620 m, but first-core shoreline IoU remains
0.887656 (second-core 0.938791). The candidate is still rejected; averaging the
two cores or waiting longer does not repair this local shoreline failure.

A bounded resistance-only sensitivity starts from that exact saved state in
`tmp/colorado-continuous-inputs-joined-n035-v1`, changing uniform Manning n from
0.04 to 0.035, the pool-depth inference hypothesis. Neither value is measured.
Bed, boundaries, saved water fields and all acceptance thresholds are unchanged;
the change is explicit in continuation provenance. The 18,000-step run completed
in session 96784, output `tmp/colorado-continuous-cook-joined-n035-v1`. Review
`tmp/colorado-continuous-review-joined-n035-v1` still rejects first-core shoreline
IoU 0.889453; second-core IoU is 0.939633. Global discharge-error p95 is 4.3520%
and settling p95 0.009118 m. Resistance reduction alone is not a demonstrated
shoreline repair; do not promote or repeatedly rerun it. Seven continuation
tests pass, including bounded parameter changes and source immutability.

### Continuous runtime integration path

`export_colorado_continuous_runtime.py` now carries a screened native cook into
runtime fields while copying its exact common-grid terrain chunks. It checks
the common coordinate frame, all decoded terrain triangles, native input/output
identities and the unchanged construction gates. It preserves global hydraulic
station in both arrays and the support-surface binary. Applying it to the actual
rejected canonical tile 0000 cook correctly refuses export before creating any
runtime directory. No failed candidate is silently usable through this path.

`build_colorado_continuous_map_contract.py` bounds launch/finish by actual cooked
coverage, not the much longer coordinate map, and requires the full production
raft footprint to be wet. The new `RaftSim.ImportContinuousMap` command imports
those shared chunks, queries every cooked wet-cell bed against native complex
collision, and adds the same production oar raft, water config and run manager
as the catalog importer. Existing catalog creation reuses the extracted runtime
setup. It does not reuse Hance's geographically specific foam mask. No normal
map, frontend choice or packaging entry has been changed yet.

The editor importer compiled and linked successfully in
`tmp/colorado-continuous-runtime-build-v2.log`, after correcting compiler-found
Unreal string conversions and a shadowed variable. Sixty combined Python tests
pass, including nonzero global launch station, support-binary layout, dependency
tampering, full-raft launch and uncooked-route refusal. These tests are not an
engine descent. The production solver archive was then rebuilt successfully:
SHA256 `db170c773524ae7d4e3e67063fa5a375064e9f8989039b144e12826166b17b17`.
All 174 Unreal consumer actions compiled/linked successfully in
`tmp/colorado-continuous-runtime-build-v3.log` (session 18489 complete). Five
fresh native tests passed in `tmp/colorado-continuous-runtime-native-v1/index.json`:
RapidChallengeProfiles, SharedFeatureKinematics, LinkedRunBoundaries,
TrialSteeringSchedule and CartesianWindowExactOverlap. The native test session
97269 exited successfully. These NullRHI regressions do not establish the new
map's rendered shoreline, full-hull descent, vegetation or packaged 20 FPS.

### Next continuous source tiles (0–7.2 km construction coverage)

While the first joined cook and engine rebuild run, the next four contiguous
tiles (0002–0005) were captured/constructed without altering the first inputs:

- Water: `tmp/colorado-continuous-water-next-v1`, 816,464 classified water cells
  from the retained CC0 2021 USGS polygons. All 114 profile samples in each tile
  fall in classified water. Topology-only repairs and their near-zero area
  differences remain recorded; no island buffering or removal was used.
- Bed: `tmp/colorado-continuous-bed-next-v1`, 209,628 surveyed pool cells across
  four crops; missing values stay missing. The composed construction grids in
  `tmp/colorado-continuous-evidence-next-v1` retain 209,390 supported survey cells,
  with zero measured-bed change and zero source bed/profile conflicts. Remaining
  underwater geometry and low shore remain explicitly inferred.
- Terrain: `tmp/colorado-continuous-terrain-next-v1`, bounded 10 m public USGS
  3DEP crops. Source metadata/attribution and the NAVD88-to-profile-ellipsoid
  conversion are retained. These are not measured boulder shapes.

Actual one-metre construction-grid overlap checks at 2,400, 3,600, 4,800 and
6,000 m pass with no classified-shoreline disagreement. Shared wet-cell counts
are 28,979 / 25,727 / 20,576 / 16,398. Maximum bed differences are zero except
0.000427 m at 4,800 m. Reference water levels match exactly. Receipts are
`tmp/colorado-continuous-bed-seam-{2400,3600,4800,6000}-v1.json`; these are source
geometry checks, not independent solved-flow seam acceptance.

The fresh six-tile assembly `tmp/colorado-continuous-terrain-chunks-7200-v1`
contains 105 complete chunks and explicitly reports 82 incomplete outer chunks.
Three old outer chunk hashes change as new source coverage becomes available;
the retained first assembly is untouched. Sampling all 212,758 existing joined
solver cells against the expanded encoded triangles found maximum difference
1.67e-10 m (wet cells 4.05e-11 m), with zero differences above 1e-8 m. No new
geometry has been substituted underneath the running cook. Neither acquisition
nor this assembly is a delivered full-river environment: native collision,
water, vegetation and descent testing remain required for the expansion.

Generating shared-frame inputs for this six-tile assembly stopped at tile 0002:
the 80 m construction margin leaves 3,064 requested cells outside the source
grid and 4,499 outside complete encoded terrain, affecting 63 of 593 core
columns. Do not split the river around these gaps or shrink the water strip to
hide them. The valid first two new inputs remain in
`tmp/colorado-continuous-inputs-7200-v1`; no tile 0002 package was produced.

The first six water/pool-bed crops have now been widened to 400 m in
`tmp/colorado-continuous-water-wide-v1` and
`tmp/colorado-continuous-bed-wide-v1`, inside the existing 400 m-or-greater 3DEP
coverage. This uses captured source data, not extrapolated heights. Composition
into `tmp/colorado-continuous-evidence-wide-v1/tile0000` through `tile0005`
completed (session 53634). All five source-bed seam reviews pass, with zero
shoreline disagreements and maximum shared wet-bed difference 0.000488 m.
The new canonical assembly `tmp/colorado-continuous-terrain-chunks-wide-v1`
has 189 complete chunks, 88 explicitly incomplete outer chunks and exactly
matching shared encoded edges. All six shared-frame inputs now build, resolving
the tile 0002 coverage failure. `tmp/colorado-continuous-inputs-wide-joined-v1`
joins them into one 3,739-by-167 domain covering all 0–7,200 m source cores,
without removing exterior halo columns or inventing wet padding. This is not a
converged flow, native descent or playable full-river acceptance.

Comparing wider encoded terrain with the preserved first joined cook found
160 wet cells changed by more than 1 cm (maximum 0.073243 m), confined to
hydraulic stations 0–16 m. Do not substitute the wider terrain under that cook.
A deterministic regression reproduced a crop-end depth-inference defect:
upstream/downstream water projected onto a finite profile endpoint was counted
as cross-section width, making the inferred bed depend on rectangular padding.
The fix excludes endpoint-clamped water from width/conveyance and excludes
incomplete edge bins from depth interpolation; survey cells remain unchanged.
The new failing-then-passing regression and 35 related tests pass; the expanded
combined construction/location/export suite has 91 passing tests. Corrected
composition completed successfully in session 28605 into
`tmp/colorado-continuous-evidence-endpoint-v1`, with zero changes to supported
survey cells in all six tiles. All five corrected source seam checks pass.
Terrain/input rebuild session 4873 completed successfully, producing fresh
`tmp/colorado-continuous-terrain-chunks-endpoint-v1` (189 complete chunks, exact
encoded shared edges), `tmp/colorado-continuous-inputs-endpoint-v1`, and joined
`tmp/colorado-continuous-inputs-endpoint-joined-v1` / `endpoint-start-v1` inputs.
The six-core joined grid has 3,739 by 167 cells; the bounded two-core start grid
has 1,344 by 167 cells. Native terrain import session 91198 completed with 9,450
actual complex-collision probes across all 189 chunks, maximum error 0.317972 cm.
Receipt: `tmp/colorado-continuous-terrain-native-endpoint-v1.log`; local map
`/Game/RaftSim/Maps/Continuous/L_Colorado_TerrainEndpointV1` remains explicitly
ignored and terrain-only. This is not a rendered water/boat descent or 20 FPS.
Old sources, grids,
terrain and native control cooks remain immutable and preserved.

### Actual fine-bank coverage and labelled fallback

The 3DEP catalog query at Lees Ferry identifies native one-metre datasets
AZ_NorthEast_D23 and AZ_CentralCoconino_B22 in NAVD88. The new `--cell-m 1`
acquisition locks only those native fine raster IDs; a finer export alone is
not accepted as evidence of finer survey. Catalog metadata and source IDs are
retained in `tmp/colorado-continuous-terrain-1m-start-v1`.

Those initial TIFFs contain 1,518,448 / 2,233,575 zero-filled pixels with no
nodata tag. A source identify query at [242949.5, 650511.5] EPSG:6404 confirms
both native fine sources return NoData there, while coarse data returns about
946.324 m NAVD88. The exports must not be composed as complete fine terrain.
The capture and composer now explicitly reject missing or zero-filled Colorado
terrain. This is a real valid-pixel coverage issue, not a reason to change datum
or replace water pixels with fabricated bathymetry.

Importantly, valid fine elevations cover 3,436 of the 3,455 first-core extra-wet
cells more than 4 m outside the captured shoreline. The new
`blend_colorado_terrain_coverage.py` uses those valid fine pixels, with the
existing captured coarse source only in missing areas. It preserves both inputs
and a per-cell source-resolution raster; no blended result is called uniformly
metre-surveyed. Output `tmp/colorado-continuous-terrain-mixed-start-v1` contains
1,786,352 / 1,923,125 valid fine cells and the above coarse-fallback counts.
Twelve acquisition/coverage tests pass, including zero fill, missing fallback,
datum rejection, native-source selection and preserved fine values.

Fresh mixed-source composition/terrain/input assembly completed successfully in
session 50510. It produced `tmp/colorado-continuous-evidence-mixed-start-v1`,
`tmp/colorado-continuous-terrain-chunks-mixed-start-v1`,
`tmp/colorado-continuous-inputs-mixed-start-v1` and
`tmp/colorado-continuous-inputs-mixed-joined-v1`. Both measured-bed maximum
changes are zero; shared bed/shore seam checks pass. This candidate retains
source water, survey bathymetry, endpoint fix and
original n=0.04. It is a new geometry candidate, not the earlier resistance-only
control. Do not substitute it under any existing cooked fields.

Native mixed-terrain import completed successfully in session 53786: 76 chunks,
3,800 actual complex-collision probes, maximum error 0.317972 cm. Receipt:
`tmp/colorado-continuous-terrain-native-mixed-start-v1.log`. The fresh map
`/Game/RaftSim/Maps/Continuous/L_Colorado_TerrainMixedStartV1` is explicitly
ignored, terrain-only and not a rendered boat run or normal-menu replacement.

The fresh flow validation in session 7271 completed successfully, from the mixed joined
inputs into `tmp/colorado-continuous-cook-mixed-joined-v1`. It uses the current
isolated native solver, 54,000 steps at 0.05 s, frame interval 3,000, HLL/order 2,
CFL 0.2, original n=0.04, bed-source scale 1, authored forcing 0 and fixture/
global-mass corrections disabled. It starts from the new input state, not an
old cook over different geometry. Its unchanged global and per-core construction
screens now pass: `tmp/colorado-continuous-review-mixed-joined-v1/review.json`.
Core wet IoUs are 0.9180088 and 0.9201104; global stage absolute p95 is 0.553399 m,
face-discharge error p95 2.6274%, settling depth p95 0.0044295 m. These are
construction checks, not visual, boat or packaged FPS acceptance. The exported
`tmp/colorado-continuous-runtime-mixed-start-v1` covers source cores 0-2400 m;
terrain/solver bed discrepancy is 1.66e-10 m. Sparse art-directed dressing is in
`tmp/colorado-continuous-dressing-mixed-start-v1.json` (1309 instances, 40 chunks).

### Native continuous terrain streaming validation (October 6)

The full editor build in session 12542 succeeded. The new rescue terrain source
provider uses the actual raft and live swimmer world positions, with stable
per-passenger source identities; it does not own or reset rescue simulation.
`tmp/continuous-rescue-streaming-native-v1/index.json` records one native test
passed, zero failures. Registration lifecycle and actual streamed gameplay are
still required; this isolated source query test is not rescue-descent acceptance.

The first World Partition terrain candidate, `L_Colorado_TerrainMixedStreamV1`,
created 76 spatial proxies and passed 3800 complex-collision probes (maximum
0.317972 cm). **Do not accept it:** save-time bounds revealed that UE 5.8 proxy
splitting had cleared final render height textures. Its NullRHI import retained
old correct collision without recomposing the GPU edit layers. It is preserved
locally as rejected evidence, not registered in the normal game.

The importer now refuses NullRHI, forces landscape layer composition, and checks
every final render height vertex against its source (at most one encoded height
unit) before collision checks and saving. This correction compiled/linked in
session 68201. The fresh offscreen rendering-RHI import in session 23603 completed
successfully (exit 0), log `tmp/colorado-continuous-terrain-native-stream-v2.log`,
candidate `L_Colorado_TerrainMixedStreamV2`: all 1,225,804 final render vertices
passed source equality, 76 spatial proxies and 3800 complex-collision probes
passed with maximum error 0.317972 cm. Final map and external actor packages were
saved. No build, cook or import from this checkpoint remains active.
Both candidates and their exact external-actor/object folders are ignored until
accepted; existing playable maps remain untouched. Reload, visual, streaming,
boat, water/foam and packaged 20 FPS validation remain mandatory.
The 28 impacted Python location/cook-review/runtime/dressing/contract tests pass;
`git diff --check` reports no whitespace errors. No commit/push was performed.

### Continuous playable opening and long-world correction (October 6)

The offscreen GPU import of `L_Colorado_ContinuousMixedStartV1` completed in
session 76719. It binds the two-core runtime, 76 terrain proxies, 1309 dressing
instances and the production oar raft. All 103369 wet-cell collision probes
passed (maximum 0.261719 cm); 3800 additional terrain probes passed (maximum
0.317972 cm), and final render height textures passed the source-vertex check.
The candidate and exact external package directories remain ignored, not
registered as a finished full-river replacement.

The first actual `-game` launch exposed a production failure: the raft actor
clamped absolute Z to 50000 cm and cleared velocity. This surveyed start is
about 61700 cm above the map origin, so the raft was forced about 117 m below
the water. Preserve `tmp/colorado-continuous-start-game-v1.log` and captures as
rejected evidence. `RaftSimWorldPositionGuard` now accepts finite positions
inside the engine world and recovers invalid positions to the preceding valid
pose, without clipping legitimate river elevation/chainage. Build 70261 passed;
`tmp/continuous-world-position-native-v1/index.json` records two passing native
tests (world-position guard and rescue streaming sources), no failures.

Fresh launch `tmp/colorado-continuous-start-game-v2.log` completed normally.
Its three actual game-camera frames at 15, 45 and 75 seconds were inspected:
the raft remains afloat, with terrain and shoreline visible. Station advances
200 to 249.837 m; recorded freeboard is 16.3-17.5 cm, no grounding/penetration,
no retained water and integrity 1.0. Hull/render equality remains 26610 vertices,
38344 triangles, zero geometric error. This uncontrolled opening drift is not
a whole-reach descent, rescue test, polished environment or FPS acceptance.

The normal-input construction trial completed successfully in
`tmp/colorado-continuous-start-smoke-v1/colorado_continuous` (session 64470),
200-500 m with the real oar controls and midpoint/exit captures. It cleared in
144.400 simulated seconds, 278.307 wall seconds: 206 completed oar strokes,
zero full-hull impulses, swimmers, dry-center time or in-trial checkpoint resets;
maximum absolute roll 1.314 degrees, pitch 1.018 degrees, speed 2.867 m/s and
route error 4.653 m. Dependencies remained unchanged. Midpoint and exit frames
were visually inspected; their video-memory budget warning and stray guide-school
overlay are failures to address, not acceptable polished/performance evidence.
Two narrowly scoped corrections built successfully in session 80485 (39 actions,
226.43 seconds): reject a saved
scenario belonging to another map before replacing authored run bounds/mode;
and restrict curved far-field allocation to the presentation data's actual
station bounds, keeping the global lattice and a dry shoreline border. The old
renderer allocated 112645 by 101 nodes for a 450 km coordinate map even though
the resident source ends at 2686 m. Neither correction changes the water solver.
`tmp/continuous-integration-guards-native-v1/index.json` records six passing
native tests, no failures: source bounds, world/session isolation, valid world
positions, rescue streaming sources and both existing progress/review-range
regressions. The fresh normal `-game` capture
`tmp/colorado-continuous-start-game-v3.log` exited normally; its 15/30/45-second
frames were all inspected. Initial far-field allocation is now 673 by 101,
retaining exactly 22632 wet vertices and 46844 triangles. Initial build time is
240.124 ms versus v2's 5146.072 ms. This is one component's construction cost,
not a packaged FPS benchmark. Scene geometry/water remains visible and the raft
stays afloat. The repeated rendered normal-control descent completed in
session 94842, `tmp/colorado-continuous-start-smoke-v2/colorado_continuous`:
`section_cleared`, 144.400 simulated seconds / 250.269 wall seconds, end station
500.042 m, finite motion, 206 completed oar strokes, zero swimmers, full-hull
impulses or in-trial checkpoint resets. Maximum roll/pitch are 1.381/1.064
degrees; route error 4.670 m. Dependencies remained unchanged. Start, midpoint
and exit images were inspected: the video-memory warning and foreign
guide-school overlay are absent, and the continuous water/terrain remain
visible. Far-field builds 2-4 retain the same wet/triangle counts as the previous
descent and take 22.124, 14.606 and 18.930 ms. No packaged FPS claim follows from
these fixed-step editor trials. All build/import/native-test/recording sessions
listed above are terminal; only the independent six-core cook below remains
active, last observed at step 15000/54000, simulation time 750 seconds.
The 28 targeted Python geographic/construction tests pass. The first sandboxed
suite stalled after the read-only tests and was interrupted; the scoped elevated
run completed all tests in 0.850 seconds with fixture writes authorized.

Cook review additionally refuses incomplete registered-core endpoint coverage
and invalid/nonmonotone source station axes. Previously a nonempty partial
overlap could reach the per-core numerical gates. Two new regressions cover
partial overlap and invalid axes; all 30 targeted Python tests now pass.
Read-only checks confirm both current candidates meet the stricter bracket:
two-core source 0-2702.313824 m covers both 1200 m cores; six-core source
0-7511.743894 m covers all six cores through 7200 m. Numerical thresholds are
unchanged. No need to rerun an unchanged native cook for this check.

The independently running six-core cook in session 37632 uses
`tmp/colorado-continuous-inputs-mixed-six-joined-v1` and writes only
`tmp/colorado-continuous-cook-mixed-six-joined-v1`. It covers cores 0-7200 m with
the same unchanged 54000-step construction gates. No six-core runtime has been
exported/promoted. Review every core and inspect native streaming before using
it; do not start a duplicate cook. Full-river/all-catalog/environment/package
acceptance and commit/push remain pending.

### First source-core crossing and Badger corridor extension (October 6)

`tmp/colorado-continuous-core-seam-v1/colorado_continuous` completed the rendered
900-1500 m normal-oar trial, crossing the 1200 m construction seam without an
intermediate reset. Result: section cleared at 1500.396 m, 272.400 simulated
seconds / 457.108 wall seconds, 388 completed oar strokes, no swimmers,
full-hull impulses, grounding, dry-centre time or checkpoint restores. Maximum
roll/pitch were 1.285/1.472 degrees. Runtime/map dependency hashes remained
unchanged. This is a calm-reach construction crossing, not rapid difficulty,
rescue continuity or packaged 20 FPS acceptance. Crew energy reached zero by
the exit; it was not reset at the source boundary.

Midpoint and exit screenshots were inspected. The midpoint exposes Unreal's
non-Nanite virtual-shadow marking-queue overflow warning, although the exit
frame has no warning. The short native `-game` diagnostic
`tmp/colorado-continuous-shadow-diagnostic-v1.log` exited normally with page-area
reporting enabled. Its largest reported contributors were Landscape components
(maximum reported overlap 180); this diagnostic is not proof that the queue
overflow is repaired. No shadow quality was disabled, warning hidden or engine
threshold raised. The capture's station-placement hops are diagnostic setup,
not evidence of continuous travel; only the normal-oar trial above is.

Source construction now extends through cores 7200-14400 m, including Badger's
registered source point at 12822.904184 m. Native metre terrain where available
and explicitly masked 10 m fallback are preserved in
`tmp/colorado-continuous-terrain-mixed-badger-v1`; source water and sparse pool
bathymetry are retained separately. No new measured rapid-bed or boulder claim
is made. Initial evidence in `tmp/colorado-continuous-evidence-mixed-badger-v1`
has zero measured-bed changes and passes six source-bed/shoreline overlap checks
at 7200, 8400, 9600, 10800, 12000 and 13200 m, with zero shared bed/surface
differences and zero shoreline disagreements. Receipts:
`tmp/colorado-continuous-bed-seams-mixed-badger-v1`.

The first twelve-core Landscape candidate
`tmp/colorado-continuous-terrain-chunks-mixed-twelve-v1` has 262 complete chunks
and exact encoded shared edges, but **is not accepted for cooking**. Building
tile 0007 revealed missing source strip at 9225-9373 m and incomplete Landscape
coverage over approximately 8945-9459 m, inside its required core. An 80 m
source-crop margin is inadequate at this bend. No hole was interpolated, core
shortened or dry coverage invented. Six older edge-chunk hashes also change in
the expanded mosaic, so old cooked fields must not be blindly reused against it.

Fresh 400 m source extractions and evidence composition are in
`tmp/colorado-continuous-water-badger-wide-v1`,
`tmp/colorado-continuous-bed-badger-wide-v1` and
`tmp/colorado-continuous-evidence-mixed-badger-wide-v1`. They reuse captured
terrain and original survey/shoreline sources, retaining NoData and topology
repair receipts. Inspect completion before starting another extraction.
Re-export a fresh common Landscape and recheck all six inputs and seams before
any additional cook; the independent six-core cook remains unchanged.

The widened extraction/composition subsequently completed. All six source joins
pass with zero wet-bed/surface delta and zero shoreline disagreement in
`tmp/colorado-continuous-bed-seams-mixed-badger-wide-v1`. The corrected common
terrain `tmp/colorado-continuous-terrain-chunks-mixed-twelve-wide-v1` has 364
complete chunks, 160 explicitly incomplete outer chunks, and zero encoded
shared-edge difference; manifest SHA256
`6673f7147f4db91f7a80a640731833ad0496a83fc5e3b3533392bb31393826e6`.
All twelve fresh inputs in `tmp/colorado-continuous-inputs-mixed-twelve-wide-v1`
now pass the complete-core coverage guard, including the previously failed
8400-9600 m bend. This fixes source/terrain coverage, not flow convergence.
The first five inputs have identical sampled bed to the active six-core cook.
Tile 0005 differs only in 78 outer-halo cells at source stations
7509.740-7511.744 m (maximum 1.076865 m); its required core is unchanged. Do not
reuse the old cook against the expanded candidate without a compatible solve
and review. No runtime map was replaced by this construction export.

The corrected twelve-core join completed in
`tmp/colorado-continuous-inputs-mixed-twelve-wide-joined-v1`: one 7322-by-167
2 m domain, source interval 0-14704.157623 m bracketing all twelve required cores
through 14400 m, with no exterior halo columns cropped. It is prepared, not
cooked or accepted. At this checkpoint only solver PID 2892 / session 37632 is
active, cooking the original six-core candidate (latest progress 33000/54000).
The native editor tests, shadow diagnostic, widened extraction and twelve-core
construction jobs have exited; no second solver was launched.

The scenario builder now rejects incomplete required-core coverage before
writing a solver input, reports internal missing-source intervals, and still
trims only exterior halo. Twenty-eight targeted scenario, cook-review, terrain
and join tests passed. This moves an existing acceptance requirement earlier;
it does not relax the later cook review or geographic source requirements.

### Native terrain-renderer comparison (October 6)

The continuous importer now supports an explicit `nanite_terrain` contract
option, still false by default during comparison. It builds native Nanite
representations only after final GPU height composition and the existing
source/collision checks; source LOD remains zero, position precision is increased
to 4, and no skirts or shadow-disabling workaround are added. The importer waits
for mesh builds and refuses missing/stale proxy representations before saving.
The Python regression verifies that selecting Nanite changes no launch,
collision, terrain, water or provenance field. Fourteen map-contract/terrain
tests pass, and the Editor Development build succeeded (session 60676,
43.98 seconds).

Fresh contract `tmp/colorado-continuous-map-nanite-start-v1.json` imports only
the existing two-core physical data into
`/Game/RaftSim/Maps/Continuous/L_Colorado_ContinuousNaniteStartV1`. Native import
`tmp/colorado-continuous-map-native-nanite-start-v1.log` succeeded: 76 built
up-to-date Nanite proxies, 3800 complex collision probes with maximum error
0.317972 cm, 103369 wet-bed probes with maximum error 0.261719 cm, and the same
1309 art-directed dryland instances. Original map and runtime files remain
unchanged. Exact candidate map/external-actor paths are ignored until accepted.

The identical rendered 900-1500 m normal-input trial completed under label
`colorado-continuous-core-seam-nanite-v1` (session 21211, native exit zero).
Actual motion reached 1500.372497 m in 272.400014 simulation seconds, with 388
completed oar strokes, zero full-hull impulses, swimmers, dry-centre duration or
checkpoint restores, and stable dependencies. Maximum roll/pitch were
1.254639/1.482195 degrees. First/midpoint/end frames were visually inspected and
contain no warning overlay, but the completed native log DOES contain the same
non-Nanite marking-queue overflow warning at 23:24:30 UTC. Therefore this is NOT
a verified shadow-warning fix. The 419.922172 wall seconds are not an FPS result:
the trial used fixed simulation time, an editor viewport and a concurrent solver.
A targeted native fallback-caster diagnostic is running in session 75143,
`tmp/colorado-continuous-shadow-nanite-diagnostic-v1.log`; it does not change
shadow quality or hide warnings. The six-core solver remains independently active.

Source acquisitions additionally extend cores 0012-0023, global 14400-28800 m,
through Soap Creek and House Rock. Fresh output families are
`tmp/colorado-continuous-terrain-{1m,10m,mixed}-soap-house-v1`,
`tmp/colorado-continuous-water-soap-house-v1` and
`tmp/colorado-continuous-bed-soap-house-v1`; water/bed use the corrected 400 m
capture margin. Terrain acquisition/blending (session 46967) and source
extraction (46733) both completed successfully. All twelve windows retain their
native 1 m valid-coverage mask and explicit 10 m fallback. Pool survey coverage
is partial, not fabricated through rapids. Fresh evidence composition is running
in session 27594 into `tmp/colorado-continuous-evidence-mixed-soap-house-v1`.
These acquisitions have not altered any playable map.

Terrain export and joined-input source lookup now use a bounded 256 MiB LRU for
decompressed source arrays. Geographic footprints are read from small array
headers, so distant source beds need not be loaded to reject a query. Reads
refuse sources changed during assembly. An individual array larger than the
budget is returned without retaining it; this bounds the retained cache, not
the entire solver domain or transient process memory. Sampling, owner selection,
encoding and source coverage are unchanged. Twenty-three terrain/join/contract
tests passed, including forced-eviction eager/lazy sample equality and changed
source refusal. The real twelve-core re-export in
`tmp/colorado-continuous-terrain-chunks-mixed-twelve-wide-cache-v1` completed with
364 chunks and zero shared-edge differences. Its manifest SHA-256 is exactly
the prior export's `6673f7147f4db91f7a80a640731833ad0496a83fc5e3b3533392bb31393826e6`.
This is a construction memory improvement, not new playable river coverage.

The follow-up native diagnostic (session 75143) exited successfully. It reports
`landscape.RenderNanite=1` and `r.Nanite=1`; its page-overlap messages identify
the production crew body/helmet straps, not Landscape components. The second
actual game frame was visually inspected at 1280x720 and is clean. This short
diagnostic does not overturn the overflow warning from the longer matched run
or establish its sole cause. No crew shadows or geometry were disabled.

Dryland generation also uses bounded source reads and retains at most two
source-water distance transforms, taking the same conservative minimum across
overlapping captures. Forced-eviction tests preserve that minimum. Both this
change and the subsequent indexed terrain lookup reproduce the original 1309
instances exactly (SHA-256
`768dc51029e15d4ee9f14f23bdbc5144456be9a5bd11e362741cfd83fef5d8da`).

`LandscapeTriangles.sample` now groups queries by geographic tile instead of
scanning the entire query domain once per tile. Exact outer edges can use a
lower neighbour, but missing interiors are never extrapolated. Negative tile
indices, four-way corners, holes, empty/scalar queries and nonfinite/extreme
coordinates have regression coverage. Thirty-five targeted terrain, dressing,
join, runtime and map-contract tests pass. On the existing 364-chunk twelve-core
domain, all 1,222,774 samples exactly matched the exhaustive sampler; measured
construction time was 0.527344 seconds versus 10.262267 seconds. The initial
additional bitwise comparison to the previously generated solver bed failed by
at most 2.698698e-9 m because builder/exporter coordinate arithmetic already
differs in operation order. The exact old/new sampler comparison passed; the
existing runtime-export 1e-8 m consistency check also passes and was not changed.
These are offline construction timings, not engine FPS.

The complete Colorado Python regression selection now passes 122 tests; the
Chilko geographic-evidence suite passes 10. `git diff --check` passes (only
existing Windows line-ending conversion notices). No engine binaries were
relinked during the subsequent source/cache work, and no active cook inputs,
existing playable scenes or acceptance thresholds were replaced.

Soap Creek–House Rock composition (session 27594) completed for all twelve
cores 0012-0023. Every source receipt reports zero measured-bed change and zero
survey/profile conflicts. All twelve new source seams, including the join to
core 0011 at 14.4 km, pass with zero bed-height, reference-stage or shoreline
differences (`tmp/colorado-continuous-bed-seams-mixed-soap-house-v1`). These
checks cover shared classified wet cells within 100 m of each source boundary,
not engine or hydraulic continuity.

The bounded 24-core terrain export (session 94452) completed into
`tmp/colorado-continuous-terrain-chunks-mixed-twentyfour-v1`: 700 complete chunks,
300 explicitly incomplete peripheral chunks, zero shared encoded-edge
differences; manifest SHA-256
`9766fcb5729d0d73271cc6a7d4ef31d6e674d49a0e34dc02b50fc702eb98d646`.
Fresh per-core input generation and joined-coverage checks completed in session
53175 into `tmp/colorado-continuous-inputs-mixed-twentyfour-v1` and
`tmp/colorado-continuous-inputs-mixed-twentyfour-joined-v1`. All 24 required cores
are covered: the joined 14488x167 two-metre grid spans source station
0-29103.724418 m, includes the entire 0-28800 m core domain, trims no exterior
halo columns, and explicitly retains 979336 dry padding cells. This is a
complete 28.8 km construction domain, not cooked or playable coverage. No
second solver or map replacement was launched.

The existing six-core native cook finally exited successfully in session 37632:
54000 steps, 19 frames, 4895.28 seconds solve/capture plus 94.5485 seconds export.
Its solver-level validation passed, but the completed unchanged-gate review
(session 94660, `tmp/colorado-continuous-review-mixed-six-joined-v1`) REJECTS
promotion: discharge-error p95 is 28.902728%, versus the unchanged 5% limit.
The inlet is 226.534773 m3/s and outlet 160.755830 m3/s. Global wet IoU 0.945412,
surface-error p95 0.491729 m and depth-change p95 0.021410 m pass their respective
screens; every individual core passes those three checks, but only the first
core passes discharge. The unaccepted fields were not exported to a playable map.

Native no-stepping face-flux probes of saved frames 14/16/18 (simulation seconds
2100/2400/2700) show outlet flows 153.003753/155.685283/160.755830 m3/s and
discharge-error p95 32.399365/31.165312/28.902728%. Stored grid volumes increase
2695693.284655 -> 2717422.223492 -> 2737960.563322 m3; late storage rates
72.429796 then 68.461133 m3/s are consistent with the inlet/outlet deficit.
This supports ongoing storage adjustment, not proof of a steady boundary error
or eventual convergence. A fresh exact-state continuation is being prepared in
`tmp/colorado-continuous-inputs-mixed-six-continue-v1`, with output
`tmp/colorado-continuous-cook-mixed-six-continue-v1`. It adds 180000 native steps
(9000 simulation seconds), captures every 9000 steps, and changes no bed,
roughness, boundary, forcing or mass policy. Preparation succeeded and the
continuation is active in session 11997 (first native step finite at depth
17.0024 m). Review every core again after it finishes. Do not duplicate it or
relax the failed discharge check. All prior native/editor, source-composition,
terrain-export and joined-input sessions named above have exited. Main remains
checked out; no commit/push or normal-menu replacement is claimed at this
checkpoint.

### Downstream batch expansion and source-query scaling (October 6)

The previous goal turn made concrete progress (native 600 m comparison, bounded
source caches, indexed terrain checks, verified 28.8 km construction coverage),
and identified the six-core discharge failure. Its exact-state continuation was
confirmed live at the next turn, session 11997/PID 33228; no duplicate cook was
started.

Separate bounded acquisitions now cover selected source cores 0024-0119,
global 28.8-144 km, in eight twelve-window batches (`batch0024-0035-v1` through
`batch0108-0119-v1`). Session 49734 sequentially captures 10 m terrain, locks
native fine-source catalogs, captures partial 1 m coverage and blends the
explicit fallback mask. Session 88845 extracts matching classified water and
partial pool bathymetry from the existing captures with 400 m margins. Fresh
output families are `tmp/colorado-continuous-terrain-{1m,10m,mixed}-batch*-v1`,
`tmp/colorado-continuous-water-batch*-v1` and
`tmp/colorado-continuous-bed-batch*-v1`. Inspect completion before composition;
acquisition alone is not a new playable rapid or accepted full-river coverage.

`TerrainMosaic.sample` now interpolates only queries inside each source raster,
and samples bed values only where that source wins the unchanged owner rule.
This avoids repeatedly interpolating the entire river against every local
source. The exhaustive regression checks outside coverage, overlaps, scalar
queries and missing/NaN coordinates; all 123 Colorado tests pass. Real re-export
`tmp/colorado-continuous-terrain-chunks-mixed-twelve-covered-v1` reproduced all
364 heightfile hashes, source owners, source identities, edge values and missing
coverage records exactly. Its whole-manifest hash initially differed solely
because the CLI recorded an absolute rather than relative spelling of the same
route path. Both path resolution and route SHA agree, and all other JSON fields
are exactly equal. No existing export or cook dependency was changed to force
that comparison to pass.

### Source absence, legacy reporting and native rescue continuation (October 6)

Acquisition session 49734 completed terrain batches 0024-0095, then correctly
refused the all-invalid native 1 m export for core 0103. Its incomplete raw
`batch0096-0107-v1` directory is preserved. Water/partial-pool extraction session
88845 completed every window through 0119 (144 km). The capture helper now has
a separate explicit `--allow-empty-fine` raw-evidence option, requiring partial
capture and still requiring locked audited native sources. An empty export is
recorded as absent, with zero native pixels and invalid composition coverage;
it cannot be used directly as terrain. Default rejection is unchanged.

Fresh capture/blend session 3197 completed successfully. It reuses the verified
10 m capture for batch0096-0107, writes new fine/mixed `-v2` directories, and
completes fine/coarse/mixed batch0108-0119-v1. Cores 0103-0105 contain zero native
fine pixels and exclusively labelled 10 m fallback. Other windows retain their
actual mixed/native resolution masks. All source families now reach 144 km;
this does not establish 144 km of modeled rapids or playable coverage. Source
composition session 1015 is independently processing cores 0024-0095 into
fresh `colorado-continuous-evidence-mixed-batch*-v1` directories. Do not duplicate
it. The longer six-core cook continuation 11997 remains active and unaccepted.

The legacy `report_rapid_assessment.py` correction is now implemented: clean
hands-off passage no longer automatically assigns Class I, controller workload
and approach counts no longer manufacture ordinal classes, and Grand Canyon
ratings are not halved into I-VI. Raw route/steering/incident/recovery evidence
and all 99 inventory entries remain. Nonfinite or obsolete high-side evidence
is linked but excluded from usable observations; current
`checkpoint_restores_during_trial` and legacy reset fields both prevent a
restored exit from counting as recovery. Source-matched decision campaigns,
not this legacy variant inventory, are required for class comparison. Fresh
report `tmp/rapid-assessment-observation-correction-v2` retained 99 entries and
24 supplied native receipts, with no invented class claims. All 148 Colorado,
legacy-assessment and decision-report regression tests pass; `git diff --check`
passes with only line-ending notices. This fixes reporting, not gameplay.

Rendered native session 11637/PID 22776 uses the unchanged production DLLs and
Nanite-start map for `tmp/colorado-continuous-rescue-seam-v1`. Its fresh plan
starts at 1120 m, explicitly puts the solo guide overboard at 1199 m, enables
normal swim/reentry controls, and continues toward 1370 m with gates around
the 1200 m source-core seam. This is a controlled-overboard construction drill,
not naturally generated washout, proof of distant-swimmer cell unloading,
river difficulty, packaged acceptance or an FPS benchmark. It completed with
native exit zero and stable dependencies: section cleared at 1370.225446 m in
111.400006 simulation seconds (215.073095 wall seconds), one completed rescue,
148 actual oar strokes, zero checkpoint restores, hull contacts or dry-centre
duration. Guide overboard was issued at 1199.068487 m; the 1200 m gate retained
one swimmer and zero resets. Swimmer count first returned to zero at 1205.304178 m
(34.800002 s); the climbing animation still appeared in the later 1210 m frame,
so count removal alone is not the completion time of that animation. Start,
source-seam underwater, downstream climb-in and finish frames were inspected;
the finish returned to normal seated controls. Maximum roll/pitch were
1.042301/0.410302 degrees. The actual 1280x628 editor captures and fixed-time
concurrent run are not the required 1280x720 packaged performance test. The
native log records moving-window handoffs at 1200.5, 1281.0 and 1361.1 m and
contains no marking-queue overflow for this run. It does not erase the warning
from the longer previous trial. No DLL replacement or duplicate engine run was
started. Session 11637 is terminal; no engine editor remains from this drill.

Separate composition session 84619 now processes only cores 0096-0119 into
fresh `colorado-continuous-evidence-mixed-batch*-v1` outputs, using terrain
batch0096-0107-v2 and batch0108-0119-v1. It does not overlap session 1015.
Source seam review 82296 completed boundaries 0024-0029, including the join to
existing core 0023: zero shoreline and stage differences; maximum bed difference
is 0.00006103515625 m at seam0024 and zero at the other five. These are source
geometry checks, not hydraulic/engine acceptance. Core0024-0035 composition
subsequently completed all twelve manifests. Session 25837 reviewed the six
remaining boundaries0030-0035, each with zero bed, stage and shoreline
differences, then started the fresh 36-core terrain export
`tmp/colorado-continuous-terrain-chunks-mixed-thirtysix-v1` (0-43.2 km cores plus
captured halos). The export completed successfully: 1036 complete tiles,
440 explicitly incomplete peripheral tiles, zero shared encoded-edge
differences. Matching enlarged solver inputs have not yet been generated.
This does not extend the existing 2.4 km screened water field or replace the
normal playable Hance map. Composition1015 continues from core0036 onward;
84619 continues its disjoint0096-0119 selection, and11997 remains the only cook.

### Chilko fisheries-map exclusion (October 6)

The PSC-hosted DFO report *Enumeration of Chilko River Chinook Salmon Escapement
(Mark-Recapture) 2011*, final September 21, 2012, was downloaded and its Figure 4
(page 16) visually inspected with the PDF skill. The named **Magic Mile** is an
angling site in reach 7 upstream of Brittany Creek, not a coordinate source for
the post-Bidwell Magic/Miracle Canyon or Green Mile. Pages 11-13 explain coverage;
Table 1 coordinates are NAD83 reach boundaries, not surveyed rapid bounds.
Figure 2's local render omitted underlying geometry and was not used for
registration. No approximate rapid placement or alias was added. Ten geographic
tests pass; latest ledger receipt is `tmp/chilko-catalog-location-audit-v8.json`,
evidence SHA256 `3db7ddb8d300c6c78068a02d4ba02799da1207d0550390ce0ddeedfe3f1616dc`.

The further Chilko source review also inspected Selander's 2011 UC Davis
geomorphology text. It helps explain confined bedrock versus alluvial reaches,
but provides no extracted Green Mile/Miracle Canyon registration; figure image
retrieval failed and must not be represented as visual map inspection. The
Riversearch Chilko page's Cataract Canyon/Big Drop table is cross-river content
and is rejected. The Wright guidebook cited by Michalec is a bibliographic lead,
not an accessed rapid map. No unverified alias or geographic placement changed.
Fresh receipt `tmp/chilko-catalog-location-audit-v6.json` supersedes v5 for this
expanded ledger (SHA256
`6a5567f12e81b8e7dd31be7511424a53bae489ed15ae9f5684c09d24798256d3`).
All 91 targeted construction/location/export tests still pass.

### Continuous environment dressing and fine-source extension

`build_colorado_continuous_dressing.py` adds art-directed, sparse Colorado
dryland shrubs and ground cover using the existing first-party opaque V2 meshes.
Placement seeds use global integer cells so extending the river does not shuffle
existing plants or duplicate chunk edges. Both captured water and actual cooked
wet cells exclude placements by at least 12 m; slopes above 30 degrees, unknown
terrain and terrain farther than 180 m from source water are excluded. These
are artistic placements, not mapped species or surveyed individual vegetation.

`build_colorado_continuous_map_contract.py --dressing` binds the dressing to the
exact runtime, terrain and mesh hashes. The native continuous-map importer now
creates chunk-local HISM groups with 450-650 m distance culling, nonblocking
collision and roots aligned to actual complex terrain collision (10 cm maximum
allowed ground discrepancy). Local instance buffers avoid losing precision
hundreds of kilometres from the river's common origin. No vegetation is added
to normal maps until the new runtime candidate passes its flow review and native
import; rendered vegetation quality and FPS remain unverified.

Both dressing importer builds succeeded, including the final chunk-local-origin
update in session 19079 (37.70 s). No editor remained active afterward. The
expanded Python suite has 98 passing tests, including stable
placement, water/slope exclusion, changed-mesh refusal and terrain/runtime binding.

Fine acquisition session 50318 completed for tiles 0002-0005 in
`tmp/colorado-continuous-terrain-1m-next-v1`. The explicit
`--allow-partial-fine` option retains raw gaps and marks incomplete captures as
not directly composable; it does not weaken the composer's missing-pixel gate.
`tmp/colorado-continuous-terrain-mixed-next-v1` preserves 1,679,198 / 1,528,764 /
1,996,313 / 1,860,148 valid fine cells with labelled coarse fallback elsewhere.
Composition and all-six terrain/input assembly completed with exit 0 in session
28645, producing `tmp/colorado-continuous-evidence-mixed-next-v1`,
`tmp/colorado-continuous-terrain-chunks-mixed-six-v1`,
`tmp/colorado-continuous-inputs-mixed-six-v1` and
`tmp/colorado-continuous-inputs-mixed-six-joined-v1`. All five required source
seams passed; the result has 189 complete terrain chunks and a 3739 by 167 shared
hydraulic grid. The new four tiles preserve measured bed with zero maximum
change. This is construction input, not an imported or accepted playable run.
Do not cook this extension until
reviewing its result and the still-running first-two-core cook in session 7271.
Never swap enlarged/recomposed terrain under the first cook without exact bed
agreement and provenance checks.

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

## Chilko canonical terrain follow-up (2026-10-07 UTC)

The previous Editor build in session 35136 completed successfully. Native test
`RaftSim.M9.ContinuousRiverIdentityAndFrame` passed without warnings or errors;
receipt: `tmp/continuous-river-spec-native-v1/index.json`. The continuous
importer now distinguishes Colorado from Chilko, including rig, material/optics,
horizontal CRS and vertical reference. It preserves the legacy Colorado schema
and refuses to disguise Chilko coordinates as EPSG:6404. A subsequent Chilko
forest-dressing implementation is awaiting its own build and native tests;
Colorado dryland vegetation is not substituted for Chilko.

V6's solver finished successfully. Review
`tmp/chilko-bidwell-continuous-review-v6/compare.json` reports wet IoU 0.893974,
1,648 extra wet cells, 6 missed cells, inlet/outlet numerical discharge
45.0/44.98219 m3/s, last-frame depth-change p95 0.00002096 m and maximum
0.0350024 m. Median/p90 absolute surface-reference residuals are approximately
0.206/0.347 m. This is an **inferred DEM surface reference**, not a surveyed
stage or accepted shoreline. Generic solver success is not gameplay acceptance.

The V7 evidence builder also completed. Comparison against V4 confirms identical
captured DEM, class codes, all non-class-2 bed values and the complete seven-rock
inference JSON. Only inferred class-2 bed was adjusted. No old evidence, map or
capture was deleted or replaced.

Before another cook, the terrain/solver sampling mismatch was removed:

- `export_chilko_continuous_terrain.py` exports the bounded evidence window onto
  the native 127-vertex/2 m/252 m terrain lattice. It uses explicit EPSG:3157 and
  CGVD2013 (EPSG:6647), rejects missing source samples and omits incomplete
  chunks instead of extrapolating them. Height encoding and all shared edges
  are checked by the same triangle reader used for hydraulic inputs.
- `build_curvilinear_river_scenario.py --terrain-manifest` initializes the
  hydraulic bed, depth and discharge from those encoded triangles. The evidence
  hashes, origin, river identity, CRS, vertical reference and datum must match;
  every hydraulic cell must be covered. The prior four-sample behavior remains
  available for existing callers without this option.
- Runtime query reconstruction also supports this explicit Chilko frame.
  Synthetic end-to-end tests compare its positions and triangle heights with
  the generated bed, initial depths and 5 m3/s conveyance. Together with Colorado
  terrain/runtime/contract, Chilko location and source-capture regressions,
  **60 Python tests pass**.

Fresh candidate `tmp/chilko-bidwell-canonical-terrain-v1` has 36 complete chunks
and 30 explicitly omitted partial-edge chunks; shared-edge encoded difference
is zero. Its manifest SHA-256 is
`feea0be22ecbd35d94e3a799868850d9153267019abdb0e68b74473ec43fb8f8`.
The 1,190 by 33 hydraulic grid in
`tmp/chilko-bidwell-canonical-inputs-v1` is entirely covered. This is still only
the bounded 38.0–40.4 km FWA construction interval, not surveyed rapid bounds or
a full-river map. Comparing its exact triangle bed to the former four-sample
method gives initially wet-cell absolute differences p50/p95/p99
0.01596/0.17102/0.31266 m, maximum 0.78671 m; the all-cell maximum 2.15577 m
occurs on dry terrain. These are **sampling differences**, not measured errors
against underwater survey. Initial states are finite (maximum speed 8.587 m/s).

The 48,000-step/2,400 s candidate completed successfully (session **3166**), output
`tmp/chilko-bidwell-canonical-cook-v1`, scenario ID `chilko_bidwell_canonical_v1`.
It uses the existing native HLL2 binary, CFL 0.2, dt 0.05, frame interval 2,400,
roughness 0.045, target Q 45 m3/s, bed-slope source enabled, authored feature
strength zero, and no initial-mass preservation or fixture calibrations.
The strict review `tmp/chilko-bidwell-canonical-review-v1/review.json` passes:
water IoU 0.905462, surface-reference absolute residual p95 0.259229 m, settled
depth-change p95 0.000114 m, transported-discharge p95 relative error 0.0010713,
and inlet/outlet numerical discharge 45.0/44.976804 m3/s. All 1,190 sections
are sampled and continuously wet. Surface and shore references remain inferred,
not surveyed. No review thresholds were weakened.

Runtime `tmp/chilko-bidwell-canonical-runtime-v1` was exported with the identical
encoded terrain and correct Chilko flow/CRS/rig identity. Native import of
`/Game/RaftSim/Maps/Continuous/L_Chilko_ContinuousBidwellV1` succeeded: 36 Nanite
streaming proxies, 1,800 terrain collision probes (max 0.178964 cm), and 15,590
wet-bed probes (max 0.178223 cm). This is a bounded construction map, not a
normal-launch or full-river delivery.

Rendered continuous descent session **1558** completed against V1, from 30 to
2,340 m, with production hull and normal paddle/guide controls. Outcome
`section_cleared`, final station 2,340.133 m, 852.000 simulation seconds,
1,047.652 wall seconds, finite motion, zero checkpoint restores during the
trial, zero swimmers/capsizes/incidents and zero dry-centre time. It recorded
3,370 actual full-hull impulses in 3,127 fixed steps (26.058 s), maximum roll
14.673 degrees, maximum speed 5.102 m/s, and minimum centre clearance -0.02046 m.
This is a successful prepared-input traversal, not a no-contact or difficulty
claim. The native test passed with one `r.MotionVectorSimulation` render-thread
warning; dependencies remained unchanged. Captures are in
`tmp/chilko-bidwell-canonical-descent-v1`.
The 800 m view has bare source-backed banks and a guide arm obscuring much of
the right foreground; it is not evidence of finished visual polish. This is a
fixed-step run, not measured 20 FPS acceptance.

`build_chilko_continuous_dressing.py` generated 4,869 artistic conifer/shrub
placements in 35 chunks, excluding unknown/steep terrain and keeping at least
12 m from source-indicated and solved water. Existing first-party temperate
assets are hash-bound; the importer requires the exact river-specific mesh
whitelist. `tmp/chilko-bidwell-canonical-dressing-v1.json` and fresh map contract
`tmp/chilko-bidwell-canonical-map-v2.json` preserve V1. **75 Python tests pass**.
Guarded rebuild **17586** completed after V1 exited; two native identity/frame
and dressing tests passed without warnings/errors in
`tmp/chilko-continuous-dressing-native-v1/index.json` (session **59874**).
Native V2 import **4471** succeeded with 4,869 nonblocking plants, maximum root
ground error 0.197176 cm, unchanged terrain/wet-bed errors 0.178964/0.178223 cm.
Three short rendered production-hull passes **16345** cleared at approach,
800 m and 1,800 m starts, with finite motion, no hull impulses, no dry-centre
time, no swimmers and no checkpoint restores during each pass. Each trial has
an independent initial placement; this is not a second uninterrupted descent.
Their dependencies remained unchanged. Start/middle/downstream images were
visually inspected in `tmp/chilko-bidwell-dressing-render-v1`: vegetation is
visible and the water remains connected, but slopes still look sparse and the
guide sleeve obscures too much of the first-person foreground. Appearance and
performance are not accepted merely because these short passes succeeded.
No packaged FPS acceptance, commit or push is claimed here.

The next connected-source extension was captured without replacing prior crops:
`tmp/chilko-connected-{west-south,west-north,east}-source-v1.npz`. Offline mosaic
`tmp/chilko-connected-bidwell-white-source-v1.npz` covers
[442900,5750760,445500,5755360] in EPSG:3157/CGVD2013, 4,600 by 2,600 native
one-metre pixels, with **zero missing pixels**. SHA-256:
`521467820ed58d04c7fb4b69ad3ed7d539517c9f10aefb86c63d8f895c8af6d9`.
First finite captured pixels retain ownership; no averaging or gap invention.
Neighbor overlap differences p95/max are 0.03998/3.21002 m and remain recorded,
not hidden. Network captures remain capped at 8 million pixels; only offline
assembly accepts up to 32 million, with a regression test for the distinction.
Evidence generation **14219** completed a single 38.0–43.2 km FWA interval from
this mosaic, output `tmp/chilko-connected-bidwell-white-evidence-v1`. It has
129,155 inferred channel cells, 1,836 source-indicated whitewater cells and
eight inferred boulders, with no new rapid names/bounds. Canonical terrain
`tmp/chilko-connected-bidwell-white-terrain-v1` has 153 complete chunks, 56
omitted edge chunks and identical shared-edge encoding. Manifest SHA-256:
`95508f9d6239a366b24862c93018fcd8383d50b93a99590fb92cbdedeb7af228`.
Inputs `tmp/chilko-connected-bidwell-white-inputs-v1` use 2,575 by 33 two-metre
cells, station 0–5,148 m, origin [442000,5749000], datum 900, explicit EPSG:3157
and CGVD2013. An initial descriptive CRS-label mismatch was rejected before
writing inputs; the retry used the exact canonical identifier, not weaker
validation. Initial states are finite with no dry sections, zero eta-depth-bed
error, Q 45 m3/s at every section, depth max 2.44348 m and speed max 12.38946 m/s.
These initial velocities are inferred, not field measurements.

One new solve is active in session **49641**, output
`tmp/chilko-connected-bidwell-white-cook-v1`, scenario
`chilko_connected_bidwell_white_v1`: 96,000 steps, 4,800 simulation seconds,
frame interval 4,800, HLL2/CFL 0.2, feature scale 0, bed-source scale 1,
roughness scale 1, no mass preservation or fixture calibrations, two threads.
Check this job before launching another cook. The longer model is not yet
screened, imported or a playable delivery. Colorado continuation **11997** is
also still active (last observed step 144,000/180,000); do not duplicate it.

Research rechecked the 2007 Wetcoast report and its historical BC OpenMaps
session 20565; the latter remains inaccessible. Both were already represented
in the ledger, so this is not a new independent source or a new coordinate.
Green Mile/White Kilometer synonymy and Miracle/Magic Canyon identity remain
unresolved. Do not turn repeated search results into additional evidence or
arbitrarily subdivide their broad sequence brackets.

### Production-eye camera correction verified (October 6)

The compact gameplay head is not the production skeleton's anatomical eye.
The production rig deliberately keeps its longer authored spine/neck lengths,
so `GetPoseHeadWorldLocationCm()` plus a fixed offset can put the guide camera
beside a shoulder during a stroke. A narrow runtime correction now obtains the
actual eye landmark from the production head transform. It restores reference
head scale in a copy only, so first-person head hiding cannot collapse the eye
anchor into the joint; rendered head hiding and arm animation are preserved.
Procedural/non-CC0 fallback retains the compact head's forward/up eye offset.

`RaftSim.Crew.GuideEyeAnchorFollowsProductionRig` samples ten actions at four
phases in two world frames, comparing visible, hidden and restored eyes and
the raft-to-camera API. Initial build 21945 caught missing test friendship;
that access was corrected, and guarded rebuild 33637 succeeded (173 seconds).
Native test 39800 passed all 80 samples with no warnings/errors in
`tmp/chilko-guide-eye-native-v1/index.json`; maximum old compact-eye discrepancy
was 55.198 cm across the sampled poses. The 75 focused Python source/terrain/
cook/dressing checks also pass; they do not substitute for the native test.

Fresh rendered run 98674, `tmp/chilko-guide-eye-render-v1`, repeated the same
three V2 map passes with production hull/render equality and normal controls.
All cleared: 130.021 m in 32.4 s, 900.205 m in 28.2 s, 1900.185 m in 25.4 s.
All remained finite, with zero swimmers, dry-centre time, hull impulses and
checkpoint restores; dependencies stayed unchanged. Approach/middle/downstream
gate images were inspected against the preserved V1 captures. The large sleeve
no longer crosses the central view at the approach gate, but the near forearm
still occupies substantial lower-right space in some poses. This is a verified
anatomical camera improvement, not complete animation/environment polish or
packaged FPS acceptance. The new camera is in production code; the packaged
game has not yet been rebuilt with it.

The August 14-15, 2023 VanMarmot ROAM-trip account is now indexed as another
dated qualitative source. It supplies no Green Mile/Miracle Canyon coordinates.
Its broad White Mile wording is not an alias or boundary. Text/captions were
read; two linked image requests failed, so no photographed rock was geolocated.
The previously inaccessible ROAM expedition map remains uninspected. No rapid
coordinates or aliases were invented from these checks.

### Longer Chilko cook rejection and bounded bed experiment

49641 completed 96,000 steps / 4,800 simulation seconds, but exited 2 with native
validation false: initial/final volume 98,199.319/165,079.956 m3, relative change
0.681070 exceeds its unchanged 0.50 limit. State was finite and did not reach
the velocity limit. Output is nested under
`tmp/chilko-connected-bidwell-white-cook-v1/chilko_connected_bidwell_white_v1`.
Diagnostic comparison `tmp/chilko-connected-bidwell-white-diagnostic-v1` is not
an acceptance receipt. Final Q is 45.0 in / 44.817477 m3/s out, p95 section
error 0.233905%; settling p95 0.000023532 m. Nevertheless wet IoU is only
0.857354 (required 0.9), with 4,722 extra wet cells and 369 more than 4 m from
source water. Surface error median/p95 is +0.551100/0.688554 m against the
explicitly inferred DEM reference. No fields were promoted and no validation
gate was relaxed. More elapsed time alone is not the indicated remedy.

The existing `calibrate_river_bed.py` produced
`tmp/chilko-connected-bidwell-white-bed-step-v2.npz` with relaxation 0.7,
15 m smoothing and unchanged 1 m per-step cap: actual changes -0.498601 to
-0.096053 m, applied only to class-2 inferred bed after boulder inference.
Fresh evidence generation 2348 completed successfully in
`tmp/chilko-connected-bidwell-white-evidence-v2` with identical captured source,
FWA polygon, 38.0-43.2 km construction interval, 45 m3/s and other hypotheses.
Array checks confirmed every non-bed field identical, all 11,141,226 non-class-2
bed cells unchanged, and byte-identical boulders, centreline and surface profile.
Native terrain `tmp/chilko-connected-bidwell-white-terrain-v2` has 153 complete
chunks with identical common-edge encoding; manifest SHA-256
`ea4cb6953784a2fe7259b9b335da2153ab7ae3aa9de086089c505b18be9de04e`.
Evidence manifest/grid hashes are respectively
`82b5af78290c4ca1681db2964a600be7c4114ea3cf2b2c5848a706bead55a958` and
`a8155a41ee7d4bf23034ccabfe0c21f8573a01bfca17a2311fe3c8b6866d4599`.
New exact-terrain inputs `tmp/chilko-connected-bidwell-white-inputs-v2` remain
2,575 by 33 at 2 m spacing with the identical route, frame, discharge and
roughness. Initial states are finite, have no dry section, preserve exact
eta-depth-bed agreement and 45 m3/s initial sectional discharge. Max initial
speed/depth is 9.764744 m/s / 2.851065 m.

One distinctly labelled V2 solve is now active in session **15049**, output
`tmp/chilko-connected-bidwell-white-cook-v2`, nested scenario
`chilko_connected_bidwell_white_v2`. It uses the same hash-verified binary and
96,000 steps / 4,800 seconds, HLL2/CFL 0.2, two threads, no authored forcing,
no mass preservation and no fixture calibration. It has not been screened or
installed. Do not duplicate it. Colorado continuation 11997 remains live, last
observed 171,000/180,000 steps; no new Colorado solve was launched.

## Full Chilko source inventory and coordinate-frame clarification

The full configured lodge-to-Taseko FWA geometry has 811 vertices. Its stored
stationing is spherical distance (radius 6,371,000 m): 55,845.695680 m. The
identical vertices have 55,930.122579 m EPSG:3157 projected arc length, which is
the frame used by the Chilko terrain builder. This 84.426900 m difference is
not a disconnected route. `audit_chilko_catalog_locations.py` now exposes both
frames explicitly for source points and sequence brackets, with regression
coverage. Neither frame is the Gaussian-smoothed runtime chart; do not copy
station numbers between them. No rapid boundaries were invented or moved by
this audit change.

`plan_lidarbc_corridor_capture.py` inventoried the full route with a conservative
1 km buffer on a 2,048 m grid. Receipt:
`tmp/chilko-full-corridor-lidar-plan-v1/plan.json`. Twelve official LidarBC native
1 m float DEM headers passed CRS/grid checks (EPSG:3157 plus CGVD2013), covering
65 candidate cells through 89 bounded native intersections. Header intersection
does not establish finite pixel coverage, submerged bed, or rapid identity.

Actual Taseko-endpoint captures are preserved under
`tmp/chilko-taseko-native-terrain-v1`: native 2023 tiles 093b002 and 092o092 have
individual missing shares, but their first-finite-pixel mosaic covers the entire
2,048 by 2,048 m window [452608,5761024,454656,5763072] without gaps. Mosaic SHA:
`55de14333475e828744bed429653283d3e5dd3714f0382e543626ab73c3429b6`.
There are 204,819 overlap pixels; p95/max absolute disagreement is 0.049988 /
3.179993 m. Differences remain in the provenance; they were not averaged or
silently filled. This is captured terrain, not a new playable endpoint.

New `capture_lidarbc_plan.py` serializes bounded acquisition, validates source
plan and completed crop hashes/grid/pixels before reuse, preserves incomplete
captures, and records native empty windows without manufacturing elevations or
automatically repeating an unchanged failure. Exclusive output locking prevents
duplicate jobs. Five new acquisition tests plus existing corridor, crop,
mosaic and stationing tests pass: **39 tests**. Full acquisition is running in
session **85384**, output `tmp/chilko-full-corridor-native-captures-v1`, maximum
89 requests. Inspect this job before launching any further corridor captures.
Coverage mosaics still need construction and actual route-buffer checks.

Exact polyline/header intersection now finds the upstream projected interval
0-468.234773 m outside all accepted native DEM headers, even though every large
grid cell intersects at least one header. Regression tests cover gaps between
covered endpoints and across route vertices. The official catalogue query for
`bc_092n070%` returned no records. Do not label the first half-kilometre as 1 m
LiDAR or move the launch to conceal the gap. The existing July 15 NRCan capture
`source/terrain/nrcan_mrdem30_chilko_corridor_manifest.json` has both DTM/source
hashes verified; its actual EPSG:4326 raster is 1293 by 1131, with finite launch
sample 1148.873047 m CGVD2013. It is a resampled 30 m adjusted-Copernicus terrain
fallback, not rapid-scale bank/rock/bathymetry evidence. It covers the missing
launch area without another download. Full focused tests now total **42 pass**.

## Colorado continuation result: locally rejected, not promoted

Session **11997** completed normally after 180,000 additional steps / 9,000 s;
native validation passed (mass drift 0.0533363, max historical velocity
10.5786 m/s). Fresh review **38783** completed in
`tmp/colorado-continuous-review-mixed-six-continue-v1`.
Whole-joined-grid construction checks now pass: wet IoU 0.926327, surface p95
0.538927 m, settling p95 0.000515 m, exact Q target/inlet 226.534773 m3/s,
outlet 226.013241 m3/s, p95 discharge error 0.223814%.

The required per-core check still rejects source station 4800-6000 m: wet IoU
0.869828, 3,848 extra wet cells (2,180 more than 4 m from source), 12 missing
source-water cells. Its surface p95 is 0.568910 m and discharge p95 error
0.197856%; the other five cores pass. The long continuation resolved the prior
discharge imbalance, not this local shoreline mismatch. No runtime export,
engine promotion, acceptance-threshold relaxation or unchanged recook followed.
Inspect the measured/inferred bed and shore masks in this core before changing
geometry; preserve supported survey elevations.

Read-only geographic sampling of the 3,848 extra wet cells against tile0004's
original one-metre evidence classified all inside the source crop: 1,242 are
class 0 regional terrain, median/p95 water depth 3.204028/3.361064 m; 2,606 are
class 3 explicitly inferred shore stabilization, depth 0.208515/0.933872 m.
Class-3 median/p95 solved-surface excess over reference is 0.319302/0.570074 m,
above the source model's 0.15 m dry-shore clearance. This identifies overtopped
inferred banks and inundated low terrain, rather than an unresolved discharge
transient; it does not authorize changing measured pool bathymetry. Any revised
bank construction must remain explicitly inferred, preserve source arrays and
be regenerated consistently through common terrain, collision and solver inputs.

## Corrected connected Chilko V2 result and V3 preparation

Session **15049** completed normally: native validation passed, mass drift
0.234706, historical maximum speed 9.76474 m/s, solve/capture 1617.24 s and
export 13.743 s. `tmp/chilko-connected-bidwell-white-review-v2` passes surface,
flow, settling, continuous-wet-corridor and all-section-sampled checks. Wet IoU
improved from 0.857354 to **0.891246**, still below the unchanged 0.9 gate.
Surface p95 improved to 0.413331 m; median excess is 0.246765 m. Q is 45 in /
44.921414 m3/s out, p95 error 0.109747%; settling p95 0.000035477 m. There are
3,451 extra wet cells, 252 more than 4 m from source, and 20 missing cells.
No fields were promoted. This is a smaller remaining geometry mismatch, not a
reason to repeat the settled state unchanged or weaken the shoreline gate.

The V2 diagnostic and existing bounded calibration produced
`tmp/chilko-connected-bidwell-white-bed-step-v3.npz`, explicitly using
`--previous ...bed-step-v2.npz`. Incremental correction is -0.343429 to
-0.053440 m; cumulative is -0.841682 to -0.149493 m. Only inferred class-2 bed
may use it; measured dry terrain and inferred boulder identities stay fixed.
Fresh evidence build **10063** completed in
`tmp/chilko-connected-bidwell-white-evidence-v3`. All non-bed fields and all
11,141,226 non-class-2 bed cells are unchanged from V2; profile, centreline and
boulders JSON are byte-identical. Applied float32 incremental bed range is
-0.343445 to -0.053406 m. Matching terrain
`tmp/chilko-connected-bidwell-white-terrain-v3` has 153 complete chunks, 56
omitted source-edge chunks and identical shared edges; manifest SHA
`804c36839336e608f13dda6c3cfcaca8aef6594e35b62f4eb0df68896328eb31`.

Preflight correctly stopped the first V3 input candidate because its section
identifier was `chilko_continuous` instead of the original
`chilko_geographic_construction`, despite identical coordinate points/grid.
That candidate was preserved and never cooked. Fresh corrected inputs are
`tmp/chilko-connected-bidwell-white-inputs-v3a`: entire coordinate map now
byte-identical to V2, same 2575x33/2 m grid and 0.045 roughness, finite states,
continuous initial wet corridor, exact eta=bed+depth, all sectional Q=45 m3/s,
max initial speed 8.655674 m/s. Evidence manifest/grid SHA respectively:
`d0de9e629302744b9d14603a3597e4d2ec216efbf5d50ef568711df2ba28ca0b` /
`75130d8cb2808fb71f75c5dfde0c30edb843cba5d140a74ed489c73679a62c8d`.

One new solve is live in session **37567**, PID **15064**, output prefix
`tmp/chilko-connected-bidwell-white-cook-v3`, scenario
`chilko_connected_bidwell_white_v3`. It uses the same verified solver, HLL2,
CFL0.2, 96,000 steps / 4,800 s, two threads and unchanged no-forcing/no-mass-fix
configuration. Do not duplicate it. Full-corridor capture **85384**, PID30520,
was still active with 66/89 NPZ captures at this checkpoint. No Unreal process
was live. Neither job has produced a newly accepted playable map.

`project_nearest_route.py` replaces the Chilko evidence builder's exhaustive
nearest-sample distance matrix with a bounded spatial index. It preserves
nearest-sample semantics and original first-index tie selection, not a new
channel projection method. Four unit tests cover curved coordinates, ties,
duplicate samples, block boundaries and invalid inputs. Full-window parity
build **94945** completed: all **18 evidence arrays are bit-identical** to V2;
profile, centreline and boulders JSON are byte-identical. Receipt/output:
`tmp/chilko-connected-bidwell-white-projection-parity-v2`. On 100,000 fixed-seed
queries against the actual 811-vertex Chilko route, the old/indexed calls took
0.902095/0.058687 s (15.37x) with exactly equal outputs. This is an offline
construction improvement, not a game FPS claim or new playable content.
The combined focused suite passes **54 tests**, and `git diff --check` passes.

## Full Chilko source coverage and derived launch seam

Full-corridor acquisition **85384** completed with exit 0: **89/89** bounded
requests, no empty or pending requests. Assembly **45916** also completed
with exit 0 in `tmp/chilko-full-corridor-terrain-v1`: 65 aligned tiles,
264,312,074 native LidarBC pixels, 8,317,686 explicitly coarse MRDEM-30 pixels,
and zero missing pixels, including the complete requested 1 km route buffer.
These are terrain source statistics, not measured bathymetry or playable-map
acceptance. The native/coarse ownership is not averaged or relabeled as 1 m
survey coverage. The original captures and assembled source remain unchanged.

The bounded `CorridorTerrain` reader validates tile hashes and coordinates,
interpolates across actual tile boundaries, retains source classification,
and refuses missing interpolation support rather than clamping edges.
Actual route sampling found a launch-area source seam near projected station
579 m: a 4.908222 m maximum adjacent 1 m elevation step within 25 m of the
native/coarse transition. This is not a real rapid to reproduce.

`condition_chilko_terrain_seams.py` builds a separate derived candidate using
the native-minus-coarse boundary residual with a cubic 200 m taper **only on
coarse pixels**. It uses neighboring-tile halos and a reviewed maximum offset
of 30 m; no datum shift or native survey edit is permitted. Derived source
kind 3 explicitly identifies this inferred transition. Run **93869** completed
normally in `tmp/chilko-full-corridor-conditioned-terrain-v1`; 992,175 pixels
receive transition provenance. It has not been imported into the engine.

Independent audit **63161** completed normally in
`tmp/chilko-full-corridor-terrain-audit-v1`: every one of the **264,312,074 native
pixels is unchanged**, recorded correction arrays match actual modified
terrain, and all **55,932** one-metre samples along the **55,930.122579 m** FWA
route have finite terrain support. The local maximum 1 m step at the launch
join fell from **4.908222 to 0.059136 m**. The full first-1,200-m test has a
0.125533 m maximum step. Native-only route samples remain exactly equal.
Original/conditioned manifest hashes:
`5575b6bbd774ebfff942394410abbd3da8bb9897ff875dbb41eee94279c38a76` /
`a77e11c46ec66c0b27eb1150a0db7e54c5cc0ed04ce3cb0009f32b53a801d703`.
This fixes a source-model artifact, not a delivered game scene or hydraulic
surface; the explicit engine/boat/rapid-boundary acceptance flags remain false.

The previously captured FWA polygon is the full 7,569-vertex Chilko feature,
not just its request rectangle. Its projected bounds are approximately
420917.915,5720167.019 to 468354.054,5771694.019 in EPSG:3157. Geometry is valid;
all 13,984 route samples at 4 m spacing lie inside it. No duplicate planform
download is needed. It is a planform, not flight-day shoreline or rapid names.

The focused source/terrain/registration/cook/dressing suite passed **71 tests**,
then two added actual-pixel-audit and inferred-source-reader tests passed in
the 10-test seam/sampler subset. `git diff --check` passed. These are supporting
checks, not proof of full-river visuals, navigation, or 20 FPS.

Research added the August 14-15, 2023 VanMarmot eyewitness account to the
location ledger. It supports Bidwell's S-bend and terminal hole but supplies
no Green Mile/Miracle Canyon coordinates. Its broad use of White Mile cannot
replace the mapped representative point. Linked images failed to fetch and
were not visually inspected; no text or photos were redistributed. Continue
to preserve that uncertainty rather than inventing or silently aliasing names.

## Next implementation steps

1. Resolve the Colorado 4800-6000 m core's local shoreline mismatch identified
   by the completed continuation review; do not repeat that settled cook.
   Extend the hash-verified shared-frame terrain/water
   coverage toward the complete Lees Ferry-Pearce Ferry descent. Preserve raft,
   crew, swimmers and rescue state across streaming. Short construction maps
   are integration tests, not replacements for the requested full river.
2. Finish existing V3 solve 37567 and strictly screen against the identical
   V3a inputs/canonical terrain before any runtime export. Retain rejected V1/V2
   solves; no unchanged rerun or weakened validation.
   Preserve V1 descent, V2 vegetation and production-eye camera captures. Refine
   the remaining near-forearm obstruction,
   refine forest appearance and measure actual frame cost with competing jobs
   idle. Passing source and coordinate tests is not a full-river delivery.
3. Build a consistent connected Chilko terrain/bed model over the newly covered
   downstream sources; do not splice independently inferred beds. Continue
   source-backed registration of every missing catalogue entry without
   silently aliasing Green Mile/White Kilometer or inventing Miracle Canyon
   boundaries. Extend the same uninterrupted-run work to South Fork, Pacuare,
   Futaleufu and Zambezi, with terrain and appropriate vegetation throughout.
4. Integrate accepted increments into normal playable scenes. Exercise each
   registered rapid's prepared, late/absent steering, mistake and recovery
   controls in the connected run; quantify approach/timing tolerances and
   distinguish driver, terrain and hydraulic failures. Test linked descents
   and rescues, not only checkpoint-isolated cruxes. Do not publish additional
   isolated rapid maps as fulfillment of the continuous-river requirement.
5. Verify all catalogue placements and complete continuous environments in
   native views, then rebuild and test normal packaged launch at the user's
   20 FPS requirement. Produce the per-entry difficulty comparison from
   exercised native outcomes. Commit and push when the requested scope is
   verified; source-text tests, downloads and manifests alone are insufficient.
