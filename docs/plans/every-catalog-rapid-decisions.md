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

## Connected Chilko V3 native increment and full-route reference

V3 solve **37567** completed successfully and the strict construction review in
`tmp/chilko-connected-bidwell-white-review-v3/review.json` passes all six gates:
wet intersection/union 0.904103, inferred-surface p95 error 0.279718 m, settled
discharge p95 fractional error 0.001078, and no missing wet sections. These are
checks against an inferred reference, not surveyed bathymetry or class acceptance.
The rejected V1/V2 evidence remains preserved.

The corresponding 5.148 km construction reach was exported and imported as
`/Game/RaftSim/Maps/Continuous/L_Chilko_ConnectedBidwellWhiteV3` (import **17967**).
Its 153 terrain chunks share the solver bed; 7,650 collision and 31,815 wet-bed
probes have maximum discrepancies below 0.18 cm. The 11,901 artistic vegetation
instances are not surveyed plants. This map is not registered as a replacement
for the normal full-river run; its inputs remain construction artifacts in `tmp`.

Rendered native trials **49372** at the source-mapped Bidwell point, intervening
reach, and source-mapped White Mile point all completed with the actual production
26,610-vertex/38,344-triangle, five-material hull. They recorded finite motion,
no swimmers/capsize or checkpoint restores, and stable dependencies. These are
short ordinary-control construction trials, not whole-rapid difficulty tests.
The inspected screenshots still show near-forearm obstruction during strokes,
repetitive terrain material and sparse forest. Do not mark visual acceptance.
Fixed-timestep 30 Hz is not measured 20 FPS performance.

The uninterrupted descent **75332** completed with exit 0 under
`tmp/chilko-connected-descent-v3/chilko_continuous`. The actual production raft
travelled from 34.908728 to 5100.606695 m in 1908.600100 simulation seconds
(1857.813714 wall seconds), with finite states, zero checkpoint restores,
no capsize and zero swimmers. Dependencies remained unchanged. Crew energy
persisted from 1 to 0; it was not reset between the three checkpoints. Maximum
roll/pitch were 17.639299/15.857719 degrees. There were 83.908338 seconds of
fixed steps containing committed contact impulses, not a collision-free run
or that duration of resting pinning. Start, middle, White Mile-point and finish
screenshots were inspected. The middle/finish frames confirm the remaining
guide-hand obstruction. This is a completed construction descent, not a full
55.93 km river, calibrated rapid difficulty or packaged FPS acceptance. PID
14100 exited normally; no engine process remained at the subsequent check.

The full-route source profile in `tmp/chilko-full-corridor-profile-v4` covers
55,930.122579 m at 4 m spacing. Four raw unsupported reference samples at
4368-4380 m remain NaN; a separately marked inferred stage bridges the measured-
terrain-derived references at 4364 and 4384 m (20 m span, 0.179836 m fall).
The mapped narrow branch was not widened and no terrain was removed. The
upstream coarse-source reference still needs review: global monotonic regression
adjusts a sample near 392 m by 4.098449 m. This is not a hydraulic bed, surveyed
water level, engine validation or complete river delivery. Preserve all masks and
provenance when constructing the shared full-river bed.

The location ledger's duplicate `vanmarmot_2023` key was consolidated, retaining
the notes in one source. The geographic audit now refuses duplicate JSON keys
instead of silently overwriting evidence. The location/profile suite passes
21 tests. Additional public name searches and the UC Davis source-map links did
not establish new boundaries; unavailable images/PDFs were not treated as read.
Green Mile remains bracketed by the published Bidwell and White Mile points,
not fixed to their midpoint. Miracle Canyon remains unregistered, with no proven
alias to Magic Canyon. No rapid coordinates were invented in this follow-up.

## Full-corridor canonical bed and source-weighting repair

`chilko_corridor_bed.py` and `export_chilko_corridor_terrain.py` now construct
the whole 55,930.122579 m route on the existing shared 2 m/127-vertex engine
lattice. The 600 m visual buffer yields **1,349 chunks**. Only low mapped-water
pixels receive a discharge/depth-based initial inferred bed; emergent terrain
is retained and individual submerged obstacles are not invented without imagery.
The initial depth is not a solved discharge or measured bathymetry. Every chunk
retains separate source elevations, native/coarse ownership and the exact
inferred-bed mask. Water must subsequently sample the encoded triangles.

Candidate V1 (`tmp/chilko-full-corridor-canonical-terrain-v1`, export **66412**)
and independent source/bed audit **86046** completed normally. The audit found
84 cross-sections below a diagnostic 4 m point-span/0.3 m initial-depth screen;
76 were in the first 1.2 km. This is not a raft-footprint navigation verdict.
Inspection found a real construction error: the global stage regression gave
upsampled 30 m terrain samples the same influence as native 1 m samples, pulling
the native channel reference down by about 1.6 m near the source join. No native
terrain was removed to hide that obstruction.

Profile V5 (`tmp/chilko-full-corridor-profile-v5`, **74663**) fixes that source
weighting: native support weight 1, coarse/conditioned support weight 1/900.
This is an explicit resolution-based modeling assumption, not a measurement of
sensor accuracy. Raw reference samples, source coordinates, mapped widths and
support masks are unchanged; the reference after 1200 m is bit-identical to V4.
The native-only raw/reference p95/max adjustment is 0.027364/0.525758 m. The
largest overall adjustment is now 5.721123 m on coarse terrain, which remains
an uncertainty, not evidence of measured stage. The four separately inferred
narrow-branch reference samples are unchanged.

Fresh candidate V2 and its independent audit both completed in **75619**:
`tmp/chilko-full-corridor-canonical-terrain-v2` and
`tmp/chilko-full-corridor-canonical-audit-v2.json`. All 1,349 chunks have matching
shared edges and finite source coverage. Including shared-edge duplicates,
**21,284,777 vertices retain their source elevation**, and **473,244** are
explicitly inferred bed vertices. Maximum cut is 3.346740 m; height encoding
adds at most 0.018311 m error. The initial-clearance exceptions fell from
**84 to 8**, with all 76 upstream-join exceptions resolved. Remaining diagnostic
stations are 6088, 6168, 6172, 7304, 7308, 7312, 38944 and 39040 m. Check their
actual channel/obstacle geometry and hydraulic response; do not bulldoze bars
or widen the measured banks merely to pass a static reference-depth screen.
V1/V4 remain preserved for comparison. V2 is not yet imported, furnished or
hydraulically cooked, and is not the normal playable river.

The geospatial extra now declares PyProj, SciPy and Shapely alongside Rasterio;
`physics/uv.lock` was regenerated normally and `uv lock --check` passes. A fresh
scratch environment using that lock, without the research-cache PYTHONPATH,
passes **60 Chilko tests**. The README documents the reproducible command.
No C++ DLL was changed or rebuilt, no source captures were deleted, and the
unrelated SEIYGECore submodule changes remain untouched.

## Full-corridor source ownership and native chart diagnosis

The V2 canonical bed still conflated **source-water ownership** with the
regressed hydraulic stage. At FWA station 7308 m, the raw channel reference is
1114.983029 m but the regressed stage is 1114.515408 m. Applying the 0.25 m
source allowance to that lower stage incorrectly retained the captured channel
surface as a dry obstruction. `CorridorBed` now classifies low mapped water
against the local **raw** channel reference and constructs its inferred bed
against the separate stage. Higher locally emergent features remain untouched;
the raw reference is not claimed as surveyed water or bathymetry. Only the
existing explicitly bounded short-gap policy fills missing classification
references. Regression cannot newly authorize cutting a bar.

Export and independent audit **32364** both completed normally for
`tmp/chilko-full-corridor-canonical-terrain-v3` and
`tmp/chilko-full-corridor-canonical-audit-v3.json`. The audit reprojects every
mapped vertex onto the hash-verified route/profile to verify both reference
fields, and independently checks source elevations. All **1,349 chunks** pass
source ownership and shared edges. **21,285,074 source vertices** are unchanged
and **472,947** are inferred bed (shared-edge duplicates included). Maximum cut
and encoding error remain 3.346740/0.018311 m. The 7304/7308/7312 m artificial
barrier diagnostics are gone. Seven static initial-clearance warnings remain:
6088, 6168, 6172, 13768, 38940, 38944 and 39040 m. The two newly flagged sections
reflect retaining higher local source features, not a weakened screen.

`build_chilko_corridor_scenario.py` adds full-corridor inputs without pretending
the data is a legacy single-raster evidence window. The source identity,
geographic frame, ownership policy and hydraulic assumptions are checked, and
water samples the actual encoded Landscape triangles before initialization.
`review_chilko_continuous_cook.py` and the existing vegetation builder now accept
these full-route source receipts. Vegetation still requires a screened runtime,
excludes mapped polygon **area** and actual solved water separately, and makes
no measured-canopy claim. No full-river vegetation or map import has occurred.

The first full input (`tmp/chilko-full-corridor-inputs-v1`, **88627**) covers
source station 22.000000..55909.615035 m with explicit 20 m endpoint buffers:
27,824 by 161 cells on a 16 m-smoothed numerical chart. Independent native-query
reconstruction verified every bed cell. Its 5600..7800 m test window
(`tmp/chilko-corridor-source-water-inputs-v1`) has a byte-identical full chart
and bit-identical bed and initial fields to the matching full-input slice.

Native test **41465**, PID **23740**, is **terminal and rejected**, not a job to
restart. The known solver SHA remains
`984ac852bcea8d16ad8289d394e2a62306fb71e339cb6ce3dc5a6e4bd8aec28d`.
It completed 24,000 x 0.05 s steps (1,200 s) using HLL2/CFL0.2, actual terrain,
feature scale 0, roughness/bed-source scale 1, no mass fix and no fixture
calibration. Output is
`tmp/chilko-corridor-source-water-cook-v1/chilko_corridor_source_water_inputs_v1`.
State remained finite and no velocity limit was hit, but the native volume
change gate failed: 63,205.016 to 104,287.637 m3 (**64.999%**). Final wet IoU is
**0.432192**, extra wet cells 24,652 (21,833 over 4 m from classified water),
settling depth p95 0.087154 m. Exact final inlet/outlet flux is **45/7.347709
m3/s**; the last 120 s adds 4,487.486 m3. Maximum final speed is 2.339232 m/s,
not the initial 14.768738 m/s. The initial field is not a solved discharge.

Most importantly, newly wetted cells entered a folded part of the chart:
minimum solved-wet metric **-1.576482**. Initially wet/source-only checks missed
that error. The review and export now independently reject solved wet metrics
at or below 0.1, preserving previous thresholds. Heavy smoothing alone is also
insufficient: a wide strip can overlap globally despite positive local metric.
Tests now cover full-strip polygon validity, source-route/bank coverage,
clipped water, dry cross sections, and newly wetted folds.

A checked 80 m-smoothed chart with **104 m half-width** has a globally valid
strip and covers all tested source-route/bank points; no mapped water intersects
its lateral edges. A 100 m half-width missed 21 mapped-water cells near source
station 173..218 m; 108 m and larger strips overlap globally. The failed
100 m input-generation run **26835** is terminal, created no accepted input and
started no solver. Do not repeat it unchanged. Numerical smoothing changes the
chart only: terrain, mapped banks and source rapid points are not moved. Keep
the actual river/navigation route distinct from this numerical centreline.

The new full input and chart-only comparison were queued sequentially in exec
**90703**: full `tmp/chilko-full-corridor-inputs-v3`, test-window
`tmp/chilko-corridor-source-water-inputs-v3`, then native cook
`tmp/chilko-corridor-source-water-cook-v3` with the same 24,000-step settings.
Both input builds completed and independent native-query reconstruction passed.
The full input has **27,222 by 105 cells**, source coverage
20.605662..55908.404940 m, minimum full-strip metric **0.506025** and **41,919**
covered source-route/bank probes. The test's chart, bed and all initial fields
are identical to the corresponding full-input slice. Native PID **8792** and
exec **90703** are now **terminal**: all 24,000 steps completed, but validation
failed. No native water or editor job remains from this continuation. Do not
restart this comparison unchanged.

The chart repair is confirmed by the final solved-wet metric **+0.506025**
(previously -1.576482). Hydraulic acceptance still fails: initial/final volume
60,438.644/101,499.941 m3, **67.939%** change; wet IoU **0.481608**; extra wet
cells 19,739 (16,596 over 4 m from source); settling p95 **0.124365 m**;
exact inlet/outlet **45/7.129335 m3/s**. State is finite and unclipped; final
maximum speed/depth is 2.343361 m/s / 2.569628 m. Fixing chart topology alone
does not repair the inferred channel's capacity or the stage-registration
error below. Both rejected native outputs remain preserved; neither was
exported into the game.

Do **not** start a whole-river cook from this initial field yet. The full V3
input exposes a distinct reference-registration error: its fastest initial
cell is **54.516791 m/s** at numerical-row source station 49120.117627 m.
That physical cell projects to source station **49114.814125 m**. The builder
broadcasts the row centre's stage **856.648333 m** across its width, although
the cell's source-referenced stage is **857.585470 m**. With actual canonical
bed **856.405041 m**, that creates only **0.243292 m** of initial depth and an
artificially high velocity to carry the target discharge. Correct the
geographic stage sampling rather than clipping velocity, flattening the
measured terrain or changing the discharge to make a test pass. Keep the
chart-only native comparison intact to isolate changes; a cellwise reference
will need corresponding review support rather than a misleading 1-D surface
comparison.

A separate read-only capacity diagnosis identifies the next bed assumption to
review: the initial depth formula uses the full mapped width, but locally high
bars exclude much of it. At 5800/6088/6168/6172 m, integrating the existing bed's
Manning conveyance at its own reference/slope yields only about
**7.26/6.99/6.51/8.41 m3/s**, not the assumed 45 m3/s. At 7000/7308/7600 m it is
about 44.50/42.51/43.10. These are construction estimates, not numerical face
fluxes. Correct the actual available cross-section inference if confirmed;
do not raise the mass threshold, force a velocity clip, cut observed bars or
claim that a longer unchanged cook resolves a folded chart.

The latest regression run passes **70 Chilko tests**. All source captures,
prior candidates and the unrelated SEIYGECore changes are preserved. No C++ DLL,
normal playable scene, package, commit or push was changed in this increment.

### Geographic stage, available depth and native friction correction (2026-10-07)

The next three isolated controls are preserved; none has been exported into a
normal playable map. There is no permission or missing-tile blocker here.

1. `tmp/chilko-full-corridor-inputs-v4` and its source-water window retain V3
   terrain and sample the reference stage at each physical cell's exact FWA
   projection. The previous row-centre broadcast could disagree by 0.937137 m.
   Full-route initial maximum velocity drops from 54.516791 to 20.264188 m/s,
   without clipping or changing discharge. Review supports the same geographic
   cell stage and independently checks the source projection. Its native V4
   comparison still fails: volume change 0.681362, IoU 0.482201, outlet 7.124769
   m3/s and settling p95 0.124857 m. Exec 87612 is terminal.
2. `tmp/chilko-available-channel-depth-v1` fits an explicitly inferred depth
   amplitude using only the available source-owned cross section, preserving
   excluded emergent features and any already-deeper terrain. At 1 m lateral /
   4 m station sampling, 11,508 sections need greater amplitude (maximum
   6.475105 m, hard limit 10 m). Estimated Manning capacity rises to at least
   the assumed 45 m3/s; this is NOT native flux or measured bathymetry. The
   depth NPZ hash is `1cf76c0ace400f562a44bbb7a080627e06c01f7518ed9abee54b3bb18d8255f8`.
   Canonical terrain V4 contains 1,349 chunks, 473,708 inferred vertices
   (including shared-edge duplicates), maximum cut 4.224835 m and maximum
   encoding error 0.018311 m. Its independent audit preserves native terrain
   outside the owned cuts and shared-edge agreement. One static clearance
   warning remains at FWA 39040 m; this is not a raft-footprint test and must
   not be removed by cutting an observed bar. Full V5 inputs reduce initial
   maximum speed to 9.471535 m/s. Native V5 is finite/unclipped but fails:
   volume change 0.517665, IoU 0.484057, outlet 9.608658 m3/s, settling p95
   0.102275 m. Execs 82272 and 14171 are terminal.
3. A separate friction contract error is now confirmed in the actual frozen
   native binary, not just inferred from source. C++ damping uses
   `1-dt*roughness*speed/h^(4/3)` without another gravity or square. Passing
   Manning n=0.045 therefore supplied about 2.27 times the intended coefficient.
   `tmp/chilko-native-friction-contract-v1/result.json` records three uniform,
   flat-bed one-step controls (zero drag, 0.045 and g*n*n=0.01986525). At h=2,
   u=2, dt=0.05, actual u is respectively 2, 1.9964283476330715 and
   1.9984232940626194, matching the coefficient law exactly. The tested binary
   SHA is `984ac852bcea8d16ad8289d394e2a62306fb71e339cb6ce3dc5a6e4bd8aec28d`.
   `chilko_native_friction.py` converts only the new full-corridor inputs and
   explicitly records the physical n separately. The existing live engine
   copies the historically named band's `manning_n` directly into native
   `Scenario.roughness`; the exporter therefore preserves the coefficient
   in that legacy field and adds its unambiguous semantics and inference.
   It does NOT convert it again or retune old Colorado/Chilko packages.

Friction-only native V6 completed all 24,000 steps / 1200 simulation seconds
in exec 67630 (terminal, no engine build). Native validation now passes:
finite, no velocity limit, volume change **0.472609**. The unchanged construction
review still rejects it: **IoU 0.492404**, 19,201 extra wet cells (16,092 more
than 4 m from source), 645 missing cells, stage error p95 **0.885140 m**,
settling depth p95 **0.118197 m**, inlet/outlet **45/9.911908 m3/s**, flux error
p95 **80.9023%**. Final max speed/depth is 3.880214 m/s / 3.561796 m. All 1,034
sections remain wet; minimum solved-wet chart metric is +0.506025. These are
construction diagnostics, not actual raft, visuals, named-rapid or FPS proof.
The full review is `tmp/chilko-corridor-source-water-review-v6/review.json`.

Independent verification `tmp/chilko-v5-full-v6-control-verification.json`
confirms the full V5 bed is the encoded native terrain, cell stages match the
exact source projection, and V6 window geometry and all initial fields equal
the full-input slice and previous V5 control. Only friction changed. The new
full V6 inputs apply that same corrected contract; do not start a whole-river
cook while the local source/flux/settling gates still fail.

The remaining inundation is spatially diagnosed, not a missing-data or folded
chart failure: 16,684 final wet cells are outside the FWA polygon, all on
unchanged native 1 m terrain. Their native bed minus geographically projected
reference has median -0.078312 m and p95 +0.573853 m; final depths median
0.314854 m / p95 0.862168 m. A further 2,517 wet cells are source-excluded
features inside the polygon, also native. The worst 200 m intervals include
5800-6200 and 6600-6800 m. Receipt: `tmp/chilko-v6-spread-diagnosis.json`.
This does not prove the FWA map matches the LiDAR acquisition shoreline or
that the current inferred reference/discharge is correct. Diagnose that
source/flow relationship before raising native banks, broadening the accepted
water mask or repeating a rejected cook. Do not weaken thresholds. Preserve
the incomplete-settling evidence when deciding whether a hash-bound saved-state
continuation is useful; an unchanged rerun from time zero adds no evidence.

Full V6 generation exec 97546 is terminal; its bed, coordinate map, reference
and every initial-state array exactly equal independently verified full V5.
No solver/editor process remains from this increment. Regression checks pass
**82 Chilko tests, 13 Colorado cook tests and 11 Colorado runtime tests**;
`git diff --check` passes (only the repository's usual LF/CRLF notices).

The geography uncertainty is unchanged: no new coordinate-bearing evidence
was found for Green Mile or Miracle Canyon. No alias or guessed bounds were
introduced. All source captures and the user's SEIYGECore changes remain
preserved. No C++ DLL, normal game map, package, commit or push changed here.

### Settled flow and omitted mapped branches (2026-10-07, next continuation)

The preceding turn was progress (confirmed friction contract and independent
geometry checks). This turn advances the exact native saved state and corrects
the geographic source selection. It is not blocked by access or an active job.

`continue_chilko_corridor_cook.py` now checks the complete prior review, source
hashes, native settings, final-frame hash and constant/unforced boundaries.
It copies actual saved depth, surface, momentum, velocity and wetness unchanged;
no bed edit, mass rescaling or friction change. An unsettled review can be
continued without declaring it accepted. The clock restart and previous
evidence remain explicit in `native_continuation`. Four focused regression
tests cover changed sources, clipping, forcing, friction and time-dependent
boundary refusal. The final added parent-hash recheck was made after the
already-running V6a preparation; do not claim that extra check ran in V6a.

Native **V6a** (`tmp/chilko-corridor-source-water-cook-v6a/`), prepared from
`tmp/chilko-corridor-source-water-continue-v6a`, is terminal in exec **74048**.
It advances 48,000 steps / another 2400 seconds, for 3600 cumulative simulation
seconds. It remains finite and unclipped. Local continuation volumes are
111,068.886840 -> 147,443.657975 m3 (32.7497% change); the original initial
volume was 75,423.200956 m3, so the clock restart does NOT erase the original
filling history. No simulation time or mass change is presented as real-time
engine FPS or conservation acceptance.

The unchanged review in `tmp/chilko-corridor-source-water-review-v6a/review.json`
now passes **discharge p95 error 4.11614%** and **settling p95 0.006554 m**;
exact inlet/outlet is **45 / 43.115646 m3/s**. All 1,034 source sections stay
wet, the chart remains nonfolding and stage error p95 is 0.920506 m. The
remaining failed gate is shoreline IoU **0.386273**: 31,463 extra wet cells
(26,944 over 4 m from the old source mask), 58 missing cells. Longer unchanged
cooking is not the next fix for that geography mismatch. No rejected field
was exported to the game.

Scientific source/native-field inspection at FWA 5750-6300 m suggested an
omitted side channel. This was checked against the official FWA Rivers layer,
not accepted from the diagnostic picture alone:
https://delivery.maps.gov.bc.ca/arcgis/rest/services/mpcm/bcgwpub/MapServer/36
The unfiltered local query found **five additional river polygons** with the
same watershed key 356364103: waterbody IDs 329707044, 329707086, 329707065,
329707093 and 329081676. Together, they contain **1,928** native V6 wet cells
previously counted outside the single captured polygon. This explains part,
not all, of the shoreline disagreement. It does not authorize changing the
threshold or treating every flooded cell as observed river.

`capture_chilko_fwa_corridor.py` performs an IDs-first paged query of the
same-watershed definite-river layer, checks complete/unique IDs and original
geometry validity, then selects exact intersections with the full route's
1000 m buffer. It retains full original polygons without clipping/repair.
The capture `tmp/chilko-fwa-corridor-all-branches-v1.geojson` contains **79**
selected polygons from **82** envelope-query results, instead of one. SHA:
`d0fd1bd60446269299e04e3d573d017c54e8097ef2eadd2f158802337c09dbd2`.
Its receipt records all stable IDs, URLs, page hashes, same-route hash and the
Open Government Licence - British Columbia. These are mapped river areas,
NOT a 2023 acquisition-day shoreline, bathymetry or named rapid boundaries.
The official orthophoto index has local 2006 colour 0.5 m / 2001 monochrome
1 m coverage; only metadata was read, not imagery. Do not claim a contemporaneous
image comparison. Index receipt: `tmp/chilko-shoreline-orthophoto-index-v1`.

`chilko_planform.py` supplies hash- and identity-verified collection support to
the full-route profile and bed/vegetation source model, while retaining old
single-body compatibility. Missing, duplicate, foreign-watershed, invalid or
changed geometry is refused. The complete rebuilt profile is
`tmp/chilko-full-corridor-profile-v6-all-branches` (exec **23033 terminal**):
13,984 sections; complete reference with the same four explicitly inferred
4364-4384 m gap samples; mapped width range **7..218 m**; reference adjustment
p95 0.033505 m / maximum 5.798667 m. NPZ SHA:
`95d5d5f3fc7ccf788aef050b676194ec09c02d5ee7585bbd60b7522cead47cfa`.
No new canonical terrain or hydraulic cook has yet been built from it.

The source correction exposes a domain limitation that must be fixed first:
the old 80 m-smoothed / 104 m-halfwidth chart misses **1,858 of 37,403**
four-metre-spaced mapped boundary probes. `validate_branch_coverage` now refuses
that silent clipping rather than validating only the main-route banks. Keep
the old input/cook evidence intact. A read-only domain audit explored wider
coordinates without moving geography. With 320 m numerical smoothing and
256 m halfwidth, the strip is globally valid and minimum metric is **0.545986**;
only one probe remains outside at source **20.207047 m** near the inlet cap.
The centreline's source projection has **zero reverse steps but 320 repeats**
(closest points on original FWA polyline vertices), unlike an actually folded
or reversed chart. Do not conflate repeated nearest-source projections with
physical coordinate overlap. Next fix the inlet-cap coverage and explicitly
represent nondecreasing source projection if justified; retain globally valid
strip, metric, actual mapped-boundary and per-cell geographic-stage checks.
Do not drop branch polygons, shift measured terrain or quietly widen a folded
grid to make coverage pass. Audit receipts:
`tmp/chilko-all-branches-domain-audit-v1.json` and
`tmp/chilko-wide-chart-projection-audit-v1.json`.

Regression checks pass **91 Chilko tests** and **62 Colorado continuation/
continuous tests**; `git diff --check` passes. All jobs are terminal, no source
captures or user submodule changes were removed, and no DLL, normal playable
map, package, commit or push was changed in this increment. Green Mile and
Miracle Canyon identity/boundary uncertainty remains separate from this now
confirmed mapped-branch omission.

### Complete-branch domain and independent terrain rebuild (2026-10-07)

The numerical chart now covers all **37,403** mapped branch-boundary probes
and **41,919** route/bank probes. Its 320 m coordinate smoothing, 256 m
halfwidth and 64 m numerical endpoint extension do not move source geography.
The full strip is globally valid with minimum metric **0.545986**. Its 365
repeated closest-source projections are verified original polyline vertices,
not repeated physical grid cells; actual reverse progress is still refused.

Expanding raw-source normal cross sections exposed another error: near source
3424-3528 m, the normal reached a different bend near 4094.93 m. That failed
attempt is retained; its V2 depth and V5 terrain outputs were never created.
`build_chilko_corridor_depth.py` now fits on the non-overlapping chart and
applies every constraint to that cell's own geographic source nodes. A
conservative nodal envelope preserves existing deeper cells. The completed
`tmp/chilko-available-channel-depth-v3-branch-chart-envelope` has maximum
amplitude **8.180054 m** (10 m bound), with 12,427 changed source nodes.
Its reported fitted capacities are lower bounds before the geographic
envelope, not exact final capacities, measured bathymetry or native flux.
Depth NPZ SHA:
`73a75a2596d33451983b2cf6cd4f810ca9b11d248caba51cf4c1b800977e80f8`.

Canonical export exec **79182 is terminal**. The full 1,349-chunk candidate is
`tmp/chilko-full-corridor-canonical-terrain-v5-all-branches`, manifest SHA
`60ee0ea40dfb3b282a75296a0b79c3f668e8374813926b2ba61668a898a6ba69`.
The independent audit in
`tmp/chilko-full-corridor-canonical-audit-v5-all-branches.json` verifies source
heights/classes, original polygon masks, per-cell stage/ownership, permitted
bed cuts, encoded triangles and shared edges: **21,237,536 unchanged source
vertices**, **520,485 explicitly inferred bed vertices** (including shared
edges), maximum quantization error **0.018311 m**. Maximum inferred cut is
7.494710 m. No banks or emergent source features were raised/carved to force
a shoreline match.

The old raw-normal/row-stage clearance diagnostic reports three warnings at
4108, 4112 and 39040 m. Physical-chart samples instead have 104, 104 and 6 m
of aggregate wet-cell width above 0.3 m respectively; aggregate width is NOT
continuous boat clearance. Retain the warnings and evaluate actual connected
clearance/native navigation, not an artificial obstruction repair from the
old diagnostic alone.

Local V7 inputs (`tmp/chilko-corridor-source-water-inputs-v7-all-branches`)
cover 941 x 257 cells, source 5625.837638-7784.116528 m. Full V7 inputs
(`tmp/chilko-full-corridor-inputs-v7-all-branches`, exec **32731 terminal**)
cover 25,552 x 257 cells, source 20.842378-55908.482914 m with explicit
endpoint buffers. Initial peak speeds are 3.334669 and 5.224283 m/s; these
are initial construction states, not solved fields. Source masks and ownership
are now independently resampled during review, so editing a reference mask
cannot legitimize flooding. The new test also rejects integer truncation or
unbounded/read-only depth-envelope arrays.

Full-input independent verification is complete in exec **88464**:
`tmp/chilko-full-v7-independent-verification.json` independently checks encoded
bed triangles, original masks/source classes/ownership, exact geographic cell
stages and every local initial/reference array against the full-grid slice.
The first owned read-only check (exec 64043) was stopped because lateral-major
batching repeatedly reread the entire source mosaic; adjacent-column batching
fixes that without changing any queries or tolerance. No other task, editor
or solver was stopped. Two initial 0.3 m-depth / 4 m-point-span deficiencies
remain at source **46072.556463 / 46074.529264 m**, both 2 m point spans.
These are diagnostics, not full-hull navigability conclusions.

Native **V7** (exec **66171 terminal**) is finite/unclipped after 1200 seconds:
volume 129913.195782 -> 151843.524975 m3 (+16.8808%), peak reported speed
4.352580 m/s. Its shoreline IoU is 0.570101, stage p95 error 0.461365 m,
outflow 25.576256 m3/s and settling p95 0.036593 m. It was not accepted.
The exact saved state was continued unchanged in **V7a** (exec **85963
terminal**) for 2400 more simulation seconds. Result and review:
`tmp/chilko-corridor-source-water-cook-v7a-all-branches/` and
`tmp/chilko-corridor-source-water-review-v7a-all-branches/review.json`.
V7a remains finite/unclipped: volume 151843.524975 -> 166087.830011 m3
(9.38091% local change; original filling history retained). It passes exact
discharge p95 error **0.670685%**, inlet/outlet **45 / 44.692724 m3/s**,
settling p95 **0.000952887 m**, stage p95 **0.451247 m**, all 941 wet sections
and solved wet metric minimum **0.847355**. Shoreline alone still fails:
IoU **0.544950**, 24,055 extra wet cells (19,260 farther than 4 m), 1,117
missing classified cells. Do not run another unchanged settling continuation.

`tmp/chilko-v7a-shoreline-diagnosis.json` separates **20,042** wet cells
outside original mapped polygons from **4,013** excluded emergent cells inside
them. All are native-source terrain, not coarse fallback. Outside-polygon
source ground minus the local ownership reference has median **-0.323533 m**;
native depth median is **0.331618 m**. This identifies the need to resolve
source shoreline/reference compatibility, not permission to raise captured
terrain or reclassify all flooded cells. An additional official source check
found the provincial 1:20,000 topographic product catalogue
`58af35e6-0dc3-4c9f-9385-8ee70a9466e8` is **Access Only**, not OGL-BC.
Its public directory has local `bc_092n080_xc2m_bcalb_20070115.ecw`; installed
Rasterio lacks ECW support. No pixels from that product were read, no reuse
licence inferred, and no contemporary shoreline agreement claimed.

The review now additionally checks a **face-connected inlet-to-outlet wet
path**. Wet cells in every column can otherwise hide disconnected puddles;
diagonal contact alone is not a finite-volume face connection. The settled
V7a local field passes this independent check. Full V7 **initial** water does
not: the two main components occupy source ranges 20.84-4374.18 and
4126.61-55908.48 m. Their closest cells are 8 m apart near
**51.7277 N, 124.1079 W**, inside mapped river water on native terrain.
The intervening initial dry cells are excluded by source-ownership and stage
classification, not missing terrain. This is not yet a solved-water or boat
barrier. The separate same-chart **3000-4900 m source interval** control is
now terminal in exec **10983**, with fresh inputs/cook/review named
`tmp/chilko-corridor-connectivity-{inputs,cook,review}-v1`. Its initial state
and bed were independently verified as an exact full-input slice (257 x 865).
After 1200 native simulation seconds it is **face-connected from inlet to
outlet**, finite and unclipped without a bed edit or artificial water bridge.
Thus this initial dry gap is NOT demonstrated to be a permanent water barrier;
do not carve a channel to remove it. Native reported peak speed is 4.662340 m/s,
absolute relative volume change 1.58242%, final maximum depth 4.132111 m,
minimum solved wet metric 0.740579, settling p95 0.015063 m, stage p95
0.636351 m. It is not a promoted cook: shoreline IoU 0.644946 and discharge
p95 error 11.53759% still fail (inlet/outlet 45 / 51.159562 m3/s). No boat
clearance, named-rapid decision or packaged-performance claim follows from
this connectivity check. All native jobs from this increment are terminal.

Latest regressions: **100 Chilko**, **55 Colorado continuous**, **13 Colorado
continuation/catalog-review** tests pass. All prior evidence, source captures
and user SEIYGECore edits remain preserved. No game scene, DLL, package,
commit or push has been replaced by this candidate.

### 2026-10-07 independent imagery identifies a source-route error

Two bounded Sentinel-2 crops were actually read and visually inspected, not
only located in a catalogue: **2023-10-05 and 2023-10-20**, covering EPSG:3157
423200..424500 E / 5732200..5734400 N. Raw RGB/green/NIR bands retain their
10 m pixels; SCL retains its 20 m pixels. Inputs, item JSON, hashes, source URLs
and local classification counts are in `tmp/chilko-sentinel-source-v1/`.
Receipt SHA256:
`0f848fd11f6a1b5fda40820cee79800ce917436dca404162a5cf50877cf3b636`.
Attribution: modified Copernicus Sentinel data (2023), via Element 84 Earth
Search; terms: https://dataspace.copernicus.eu/terms-and-conditions .
No imagery was installed as a game texture or converted into a purported
2 m surveyed shoreline. Source COG offset metadata are potentially conflicting;
raw green-minus-NIR sign is invariant under the shared positive scale/common
offset and was used only as a diagnostic, not calibrated NDWI acceptance.

The first scene is locally affected by thin cirrus: 1304/1615 distinct 10 m
pixels intersecting candidate wet points outside mapped water sample SCL 10.
October 20 is more useful: those pixels sample 1348 bare/nonvegetated,
47 vegetation, 57 shadow and 163 water classifications. Mixed pixels and
shadows prevent translating these counts into surveyed area or precise banks.
The source-native overlay visibly places candidate water on exposed bars.
**The mismatches cannot all be excused as missing FWA branch polygons.**

Adding the exact original route to the image reveals **two obsolete or
non-active branch choices in this 2023 scene**. The southern and western loops
cross exposed bars while visible flow follows straighter channels. One manually
selected coarse channel spot, EPSG:32610 **423890 / 5733150**, lies about
**182.30 m** from the old source route (nearest old EPSG:3157 chainage
**6398.81 m**). This is an indicative image spot, not a surveyed replacement
vertex; pixel size is not an established position accuracy. Evidence and
inspection bounds are now recorded in
`physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_alignment_evidence_2026_10_07.json`.
The catalogue audit reports this route-alignment failure separately from its
otherwise correct source-chainage arithmetic. All **14 catalogue-location
tests** pass, including the new distinction. No named rapid is placed by this
imagery check, and the original route, source DEM and V7a result are preserved.

The local lidar catalogue was also captured in
`tmp/chilko-pointcloud-source-audit-v1/`: the two relevant LAZ records list
classes **1, 2, 7, 12**, not water class 9. The linked one-page acquisition
report was rendered and inspected and lists the same classes. Its programme
accuracy specification is not a local water-level or underwater survey.
LAZ files were not downloaded. The PDF filename/contract identifiers differ;
retain the association as catalogue metadata, not independent site accuracy.
Its capture script emitted a console encoding error after successfully saving
the PDF/text; that is not a failed source download.

`tmp/chilko-image-stage-diagnosis-v1.json` is a limited read-only comparison,
not a revised profile. In particular, raw section normals can intersect remote
bends; candidate terrain heights cannot be assigned to that row without their
own geographic projection. The decisive next repair is **current channel
alignment and source-water ownership**, not another unchanged settling cook,
deeper carving of the old branch, raised captured banks, or a relaxed IoU gate.
Then rebuild the global profile, canonical terrain and native inputs together,
and reproject named-rapid geographic anchors into the revised station frame.
Full/short canonical-field equality alone cannot certify an obsolete route.

No engine scene, packaged build, commit or push was changed in this diagnostic
increment. Green Mile/Miracle Canyon boundaries remain unverified; the image
crop is upstream of them and is not evidence for naming or aliasing those rapids.

### 2026-10-07 source-backed branch correction and complete rebuild

The local FWA network capture now includes unnamed branches: 148 features in
`tmp/chilko-all-local-streams-v1.geojson`. The selected 15 edges were captured
again from the official WFS in the same geographic export convention as the
original route (`tmp/chilko-reviewed-wfs-branches-v1.geojson`, SHA256
`b946e89db5a89ad06b52aed4f35d03ddaae80a0a64af3cd43e6df0c26743abdf`).
This avoids treating the roughly 1.3 m difference between service export
conventions as a reason to relax endpoint matching. WFS/original joins are
exactly coincident. Source attribution remains Open Government Licence - BC;
cartographic network Z is discarded, not used as bathymetry.

`correct_chilko_route.py` reconstructs selected changes from hashed parent
vertices and ordered network objects. The first candidate followed two
transverse network topology links and was rejected: they are not current
centreline geometry. V2 replaces original vertices 115..146 with ten selected
official edges and two **explicitly inferred** connecting segments through
original vertex 125 (213.18 m and 109.82 m). The October 20 source overlay was
visually inspected again. Every other original vertex and both replacement
endpoints remain exact. This is a local channel correction, not an imagery
audit of the entire river or evidence for rapid names.

Candidate: `tmp/chilko-corrected-branch-route-v2/route.geojson`, SHA256
`efa7cdcba4203663d87e0797d83cafa55fcd826513e93b48d06de60bca08ec57`.
Length is **55,723.045 m**, versus 55,930.123 m for the preserved original.
Original FWA polygons remain unchanged. Their union with a 20 m half-width
buffer on replacement geometry (including the inferred joins) is an explicit
construction footprint, **not measured banks**. The older V2 receipt's short
width-policy wording says official geometry, but the actual reconstruction and
explicit connector records include those inferred joins; the builder wording
has been corrected for future outputs. The receipt itself was not rewritten
under the newly hashed profiles.

The V2 raw-direction profile failed at source station 6216 m: a tiny source
edge pointed its cross section along the river and exceeded the +/-320 m
sampling span. Shared chart directions at exact geographic anchors resolve
that numerical sampling problem without moving banks, reducing bank margins,
or altering terrain. `tmp/chilko-full-corridor-profile-v9-corrected-chart`
now contains all **13,932** sections; the existing four narrow-reference
samples at 4368..4380 m retain their explicit 20 m bounded stage inference.
Profile manifest SHA256:
`ffef8390c6be051e22d5b6f131d3199a4f5cb16309ebbfcb4f83058e6bb42994`.

Recentring the numerical water grid on the corrected route was rejected: it
clipped 50/37,553 mapped boundary probes at 256 m half-width; wider domains
began overlapping globally before covering everything. Retaining the already
validated **parent numerical chart**, while projecting source stage/ownership
onto **corrected geography**, passes all 37,553 branch-boundary and 41,763
route/bank checks, has no source-progression reversal, and keeps minimum
full-strip metric 0.545986. The chart is not a geographic river centreline.
`chilko_corridor_chart.py` records that distinction, and input review rebuilds
and checks its coordinates independently. No clipping/no-fold gate changed.

The complete bounded depth inference is
`tmp/chilko-available-channel-depth-v5-corrected-geography` (NPZ SHA256
`fb7d155c970b9f1e18d3db09b719b3caae4396f4cb644e6bb317640b41ba58c1`).
Maximum amplitude 7.894735 m remains below the unchanged 10 m bound. These
are Manning construction coefficients for assumed 45 m3/s, not measured
underwater depths or proof of native discharge.

The matching complete terrain export is
`tmp/chilko-full-corridor-canonical-terrain-v6-corrected-geography`, manifest
SHA256 `6a494193d9f5d2a3c742ec7558a0e85716553c1a0eec633ac86155932144f3e6`.
Independent audit
`tmp/chilko-full-corridor-canonical-audit-v6-corrected-geography.json`
passes **1,346 chunks**, 21,187,736 preserved source vertices and 521,898
explicitly inferred vertices (counts include shared edges). Shared edges agree;
maximum height quantization error remains 0.018311 m. All initial section
checks have at least a 4 m point span at 0.3 m reference depth. This is not a
raft-footprint or solved-water clearance proof; 491 literal centreline samples
still stand above their reference, and valid water can be off that centreline.

Full inputs: `tmp/chilko-full-corridor-inputs-v8-corrected-geography`,
25,552 x 257 cells, corrected source interval 20.842..55,701.405 m.
The local window `tmp/chilko-corridor-source-water-inputs-v8-corrected-geography`
has the **same 941 x 257 physical cells** as V7, chart station 5110..6990 m,
now corrected source station 5625.838..7577.039 m. Independent local
source/terrain/chart checks passed before its fresh native run; full/window
verification and the new 1200-second native result are tracked below. No old
depth coefficients or old native water fields are combined with new terrain.

`audit_chilko_catalog_locations.py --corrected-route ...` now reprojects
unchanged published points instead of silently reusing their old chainages.
Receipt: `tmp/chilko-corrected-catalog-stationing-v1.json`. Corrected Bidwell
and White Mile contributor-marker chainages are 38,296.184 and 42,461.506 m;
Eagle's Talon is 44,533.005 m. These are representative points, not entrance/
exit surveys. They all move 207.078 m in chainage, **not geographic position**.
Green Mile's bracket remains only between the published Bidwell/White Mile
points; Miracle Canyon identity/bounds remain unresolved. No aliases, names,
or bounds are authorized by this route repair.

Full/window independent verification completed:
`tmp/chilko-full-v8-independent-verification.json`. Every full-domain source
mask, cell-stage and encoded triangle resamples independently; the local bed,
references, initial state and chart are exact full-domain slices. The verifier's
first console output used an ambiguous `passed: true` for those checks; its
code now prints the source/slice and initial-clearance outcomes separately.
Actual-chart initial clearance still has **three** 2 m point-span rows at
corrected source 38,714.724, 45,865.479 and 45,867.452 m. The source-anchored
section audit above and this different numerical sampling must not be conflated.
They need solved/full-hull navigation checks, not automatic extra carving.

V8's 1200-second native run completed (exec 25417 terminal): finite, no velocity
clamp, connected inlet-to-outlet wet path, all 941 surface rows sampled. Review:
`tmp/chilko-corridor-source-water-review-v8-corrected-geography/review.json`.
It **fails** shoreline IoU (0.621653), settling (depth-change p95 0.041287 m)
and discharge (inlet 45 / outlet 29.935975 m3/s). Stage-error p95 is 0.577869 m.
There are 16,299 extra wet cells (13,167 more than 4 m beyond source mask),
2,002 missing source cells, and 11.1949% accumulated volume. This is an
improvement over the older flooding pattern but not a settled comparison or
accepted water. Original 1200 s and continuation evidence remain preserved.

The new native contours were rendered and visually inspected against both
dated crops in
`tmp/chilko-sentinel-source-v1/corrected-route-v2-native-v8-overlay.png`.
The large northern bar flood is reduced, but channels still spread onto exposed
bars. October 20 diagnostic pixels outside the input planform include 824 SCL
bare/nonvegetated pixels out of 959 distinct 10 m pixels; mixed pixels are not
surveyed area and the new inferred footprint differs from the old FWA-only
mask. Do not use those changing-mask counts as a like-for-like area reduction.
An unchanged-state continuation V8a reached the same 3600 s total duration as
V7a (exec 49274 terminal; 535.85 s solve/capture, 37.78 s export for the extra
2400 s). Review exec 99577 is terminal:
`tmp/chilko-corridor-source-water-review-v8a-corrected-geography/review.json`.
Discharge now passes (45 inlet / 44.335627 outlet m3/s, p95 error 1.4721%),
settling passes (depth-change p95 0.000691 m), stage p95 0.529057 m passes,
and continuous face-connected water/all 941 surface sections/no-fold checks
pass. **Shoreline IoU still fails at 0.601045**, versus required 0.9:
18,435 extra wet cells, 14,602 over 4 m beyond source mask, 1,715 missing.
Final maximum depth 3.027770 m and speed 4.339126 m/s are finite and unclamped.
The equal-duration overlay
`tmp/chilko-sentinel-source-v1/corrected-route-v2-native-v8a-overlay.png`
was visually inspected. Exposed-bar flooding persists. More unchanged settling
is not the next action, and this is **not an accepted native field**.
The remaining current-planform ownership includes historical FWA branches
outside the corrected centreline. Those are a source-review issue, not reason
to relabel the native flood as accepted river or widen the shoreline gate.

Current regressions: **115 Chilko**, **55 Colorado continuous**, **6 Colorado
catalogue review**, **7 Colorado continuation** tests pass. `git diff --check`
passes. An initial continuation-test glob matched no files; the actual seven
tests were then run explicitly. No engine map, DLL, packaged build, commit or
push is claimed by this source/terrain increment. User SEIYGECore edits remain
untouched; workspace remains on `main`.

### Image-bounded active-planform candidate (2026-10-07, in progress)

The follow-on V3 route retains V2's exact geographic vertices and route SHA
`efa7cdcba4203663d87e0797d83cafa55fcd826513e93b48d06de60bca08ec57`.
Its new lineage policy retires historical mapped branches only inside the two
pre-existing October 20 image-review rectangles, outside the explicitly inferred
20 m half-width active channel. The original FWA polygon file, captured terrain,
previous candidates and image pixels remain unchanged. No native wet mask is an
input to this replacement, and this does not authorize named rapid placement.

The source-only visual review is
`tmp/chilko-sentinel-source-v1/active-planform-v3-source-only.png`. Both reviewed
areas show obsolete mapped loops crossing exposed bars and the retained channel
following the visible current. The operation retires about 77,392 square metres
of historical construction footprint, not measured water area. The rectangular
review edges bound the edit; their straight edges are not asserted surveyed banks.
All source mapping outside those rectangles is preserved. Tests verify this
invariant, retention of the active corridor, no newly created water footprint,
and refusal of changed captured pixels/metadata or an unsupported reference policy.

Full profile V10 (`tmp/chilko-full-corridor-profile-v10-active-planform`) is complete:
13,932 source-anchored sections across 55,723.045 m, width range 8-152 m, unchanged
four explicitly inferred stage samples between 4,364 and 4,384 m. Reference
regression absolute adjustment p95 is 0.026823 m. Profile manifest SHA is
`a5fb5803372d73f461f450bce02e8d14277e588d1126079da43b8fa5fd386582`.
Depth V6 (`tmp/chilko-available-channel-depth-v6-active-planform`) retains the
10 m amplitude cap (actual maximum 7.894735 m); all 36,760 independently sampled
mapped-boundary probes fit inside the unchanged numerical chart. These are
construction checks, not a measured discharge or bank survey.

Canonical V7 (`tmp/chilko-full-corridor-canonical-terrain-v7-active-planform`)
contains 1,346 chunks; independent audit
`tmp/chilko-full-corridor-canonical-audit-v7-active-planform.json` passes source
ownership and shared edges. It preserves 21,197,117 source vertices and labels
512,517 inferred vertices (counts include shared edges). Maximum cut is
7.169101 m; encoding error is at most 0.018311 m. Its manifest SHA is
`dad4a295c2954c9055d0a319838f9b7ce998869119315a4c29f803f2ca431234`.
The source-normal static-clearance diagnostic has no deficient sections but
484 literal route centres above initial reference; this is not boat clearance
or solved navigability. Native input V9 uses the same physical cells as V8;
the local mapped-water count changes from 51,795 to 33,016 through the explicit
source-only retirement policy. Complete V9 inputs have 25,552 by 257 cells;
the diagnostic window has 941 by 257 cells. Independent verification
`tmp/chilko-full-v9-independent-verification.json` confirms exact full/window
bed, reference, initial state and coordinates, and independently resamples
source masks and stages. The same three actual-chart 2 m point-span diagnostics
remain at corrected-source 38,714.724, 45,865.479 and 45,867.452 m; they are
outside this source-footprint correction and still require full-hull review.
Native V9 is terminal at 1,200 s. Its immutable frame SHA is
`042480d04b8799b807a22112e4c37d339dc7528bdc8aac846a55cb7b717cd8e6`;
review is `tmp/chilko-corridor-source-water-review-v9-active-planform/review.json`.
All 941 sections are wet, face-connected and finite with no velocity clamp.
However construction acceptance fails: IoU 0.546156, 16,887 extra classified-water
cells (14,862 farther than 4 m), 1,107 missing cells, surface absolute p95
0.904805 m, settling depth p95 0.082508 m, outlet 21.253325 versus inlet 45 m3/s,
and discharge-error p95 52.6029%. Maximum depth is 7.295349 m and speed 10.399302 m/s.
This is genuinely unsettled, not another run of the old settled V8a failure.

The independent captured-image overlay is
`tmp/chilko-sentinel-source-v1/active-planform-v3-native-v9-overlay.png`.
It shows remaining bar flooding, so the mask change is not a promotion.
A like-for-like V8/V9 comparison at 1,200 s on identical physical points
(h > 0.05 m, not a comparison against differing acceptance masks) reduces wet
points in the upstream image-review box from 8,817 to 7,174 and in the downstream
box from 11,754 to 6,788; overall wet points fall from 46,369 to 38,541.
These are transient grid-point counts, not surveyed area or settled acceptance.
The source-only retirement restores ground by more than 4 cm at 10,084 retired
grid points, maximum 2.991956 m relative to the old inferred bed. Source ownership
is validated at canonical vertices; raw 1 m DEM samples and interpolated 2 m
terrain triangles must not be treated as identical pointwise surfaces.

Read-only localization is `tmp/chilko-active-planform-v9-transient-diagnostic.json`:
the maximum depth is in the inferred channel near corrected source 5,931.724 m,
not an invented raised bank. Remaining wet cells outside the mapped footprint
are separate from the review's stricter source-supported-channel count.

Exact-state continuation V9a is **terminal, exit 0** after 48,000 steps /
additional 2,400 s (cumulative 3,600 s). Input is
`tmp/chilko-corridor-source-water-inputs-v9a-active-planform`; output root is
`tmp/chilko-corridor-source-water-cook-v9a-active-planform`, scenario subfolder
`chilko_corridor_source_water_inputs_v9_active_planform`. All geography, bed,
friction, constant boundaries and solver options are unchanged. Its independent
review is `tmp/chilko-corridor-source-water-review-v9a-active-planform/review.json`;
final frame SHA is `c335dfc3f96c26283211b125bf685c21c073584acae85ee7ebac1040fd8dea8f`.
All construction gates except shoreline pass: all 941 sections are finite,
wet and face-connected; surface absolute p95 is 0.688072 m, settling depth p95
0.001061 m, outlet 44.085274 versus inlet 45 m3/s, discharge-error p95 2.04004%.
However IoU is only 0.505925, with 20,955 extra cells (18,288 farther than 4 m)
and 644 missing cells. Maximum final speed is 8.980242 m/s and depth 7.313516 m.
The inspected `tmp/chilko-sentinel-source-v1/active-planform-v3-native-v9a-overlay.png`
still shows bar/old-loop flooding. This settled candidate is rejected; do not
repeat unchanged V9a or promote it into terrain/runtime assets.
118 Chilko tests and `git diff --check` pass. No game scene or performance claim
is made for this supporting increment.

### Colorado bounded bank candidate and native restart (2026-10-07)

All six 0-7200 m source cores were rebuilt with the existing, explicitly inferred
dry-shore clearance increased from 0.15 to 1 m within its original 10 m radius.
The driver is `tmp/build_colorado_continuous_shore1_v2.py`; source-preservation
receipts are `tmp/colorado-continuous-evidence-shore1-v2/verification.json`.
All source arrays, surveyed bed and classified wet bed remain identical; only
inferred dry-bank cells change. All five source handoffs pass. Common terrain is
`tmp/colorado-continuous-terrain-shore1-v2`, manifest SHA
`b7deb5d5451fffcc6dfe82b70c0aeb0cf22f5339921fdbc48e7431f813d6e7fe`.
The fresh joined grid is 3739 x 167 at 2 m, retaining the original coordinate
map, reference-water mask/stage, resistance and discharge.

`warm_start_colorado_bank_cook.py` prepared
`tmp/colorado-continuous-inputs-shore1-warm-v2` from the previous reviewed settled
flow and the new joined terrain. This is a **bed-edit warm start, not exact
continuation or accepted flow**. All unchanged cells are exact; changed cells
retain old surface where possible and lose depth/momentum as the bank rises.
No water is added. 36,634 native bed cells change, maximum 0.878920 m after common
terrain encoding/interpolation; 13,274 cells become dry and numerical-grid water
volume decreases 23,583.956854 m3. These are restart diagnostics, not measured
river quantities. Independent finite-state and eta-minus-depth/bed checks pass.

The fresh native test completed successfully (exec session 8191), 24,000 steps / 1,200 s,
output `tmp/colorado-continuous-cook-shore1-warm-v2/colorado_continuous_joined`.
Frozen solver SHA remains
`984ac852bcea8d16ad8289d394e2a62306fb71e339cb6ce3dc5a6e4bd8aec28d`;
HLL/order 2/CFL 0.2, no authored forcing, no fixture calibration or mass reset.
Do not duplicate this completed cook. Independent review
`tmp/colorado-continuous-review-shore1-warm-v2/review.json` passes every registered
core, not just the global average. Global wet IoU is 0.971914, stage absolute p95
0.543387 m, discharge error p95 4.50792%, settling depth p95 0.003033 m.
The previously failing 4800-6000 m core improves from IoU 0.869828 to 0.938982;
its 1531 extra cells (1285 over 4 m from source) and 137 missing cells remain
explicit residuals, not perfect shoreline agreement. The Colorado review
now additionally refuses mismatched native configuration, failed native
validation, incomplete frame sets, changed bed/grid, and a first frame that does
not match the saved initial state (including momentum). 27 targeted warm-start,
native-review and location tests pass; no acceptance threshold was weakened.
No game scene was changed or FPS acceptance claimed by this work.

The screened six-core runtime export is complete at
`tmp/colorado-continuous-runtime-shore1-six-v2` (exec 44293 exit 0). It covers
source cores 0-7200 m and hydraulic stations 0-7476 m, retaining the common
terrain triangles with maximum solver-bed discrepancy 1.311e-9 m. Exported
provenance includes the changed-bed warm-start receipt and input-build/review
hashes. Six runtime-export tests pass. This is a partial runtime candidate,
not yet imported or promoted into a normal scene; full-river coverage, engine
validation and acceptance flags remain false.

The literature follow-up adds Robin Hartikainen's dated 2013 ROAM trip account
to the Chilko evidence ledger. It corroborates broad commercial naming, not
Green Mile/Miracle Canyon coordinates. Exact-name and guide/map searches did
not resolve those boundaries; neither catalogue entry has been assigned an
invented midpoint or automatic alias. The uninspected/access-restricted maps
listed in the ledger remain distinct from inspected sources.

### Chilko bounded stage-capacity correction (2026-10-07)

Read-only localization of settled V9a found 19,464 extra wet cells outside the
mapped footprint and 1,491 inside it but outside the source-owned channel.
Outside-footprint depth median/p95/max is 0.272519/0.891520/1.121037 m.
Channel-cell surface-error median/p95 is +0.048320/+0.528429 m; this is not
the per-section statistic used by the existing construction gate. No source
water mask was enlarged to match the flooding.

`calibrate_chilko_corridor_depth.py` now derives one bounded positive-stage
capacity experiment from actual wet source-owned cells projected to their
corrected geographic station. It does not substitute the numerical row station.
The policy uses 20 m median bins, 30 m smoothing and 150 m zero-at-boundary
tapers, with no correction in unsampled bins and no shallowing. Additional
depth amplitude is limited to 0.75 m and total amplitude to 10 m. It binds the
settled review, frame, original depth and full source identities; repeat
calibration of a calibrated parent is refused. A new native solve and unchanged
acceptance gates remain mandatory. The depth loader independently verifies
parent arrays and hashes and refuses out-of-interval or unbounded changes.

New depth is `tmp/chilko-available-channel-depth-v7-stage-calibration`, NPZ SHA
`3cfe083716c95d3250f298b86f0096f6a2070ab3e0edb326ec61831e50979ee9`.
485 source nodes change, maximum additional amplitude 0.666889 m; maximum total
amplitude is 8.026932 m. This is inferred submerged geometry, not measured bed
or a solved field. 50 targeted calibration, bed/depth, export and review tests
pass, including stale-parent/frame refusal and preservation outside the window.

Full canonical terrain export V8-stage-calibration is complete:
`tmp/chilko-full-corridor-canonical-terrain-v8-stage-calibration`, manifest SHA
`2c3094e03ff7e49b8dee20af837fa5d3ffb0d4779055fdfc852c75cc92b2d3b6`.
All 1,346 chunks span the same 55,723.045 m route. The independent source audit
passes common edges and ground ownership. Of 21,709,634 vertices including
shared edges, 21,197,111 remain captured/conditioned source ground and 512,523
are explicitly inferred. Maximum height-encoding error remains 0.018311 m.
Comparison against V7 confirms all captured source arrays, mapped masks and
reference stages identical: only 20,785 inferred vertices change, by at most
0.541466 m; 1,334 encoded chunks are byte-identical. Receipt is
`tmp/chilko-stage-calibration-v10-source-preservation.json`.

The driver `tmp/build_chilko_stage_calibration_v10.py` completed successfully;
do not repeat the export. Both the 941 x 257 local input at
`tmp/chilko-corridor-source-water-inputs-v10-stage-calibration` and the 25552 x 257
full input at `tmp/chilko-full-corridor-inputs-v10-stage-calibration` are complete.
Independent verification is terminal and passes source identity and full/local
slice equality (`tmp/chilko-full-v10-independent-verification.json`). Its separate
initial point-clearance screen still fails at three downstream sections, with a
2 m minimum span. That failure is not waived by the source-identity pass.

`warm_start_chilko_depth_cook.py` prepares the changed-bed initial guess without
adding water: old h/u/v/hu/hv/wet are exact, while eta follows the lowered bed.
It refuses changed grids, reference arrays, resistance, boundaries, unreviewed
parents, raised beds or excessive cuts. The candidate is bound to the same native
review and frame used to derive its depth correction. Fresh output
`tmp/chilko-corridor-source-water-inputs-v10-warm-stage-calibration` is complete:
15,784 bed cells change, maximum cut 0.549325 m, added water volume zero.
125 Chilko tests pass, including the changed-bed mass/momentum and refusal cases.
This is not exact continuation or solved flow. After Colorado completed, the
fresh Chilko native test completed successfully (exec session 61271): 24,000 steps / 1,200 s,
frame interval 2400, the same frozen solver, HLL/order 2/CFL 0.2, no authored
forcing, fixture calibration or mass reset. Output root is
`tmp/chilko-corridor-source-water-cook-v10-warm-stage-calibration`, scenario
`chilko_corridor_source_water_inputs_v10_stage_calibration`. Do not repeat this
completed cook. Independent review is terminal at
`tmp/chilko-corridor-source-water-review-v10-warm-stage-calibration/review.json`:
wet IoU 0.502678 still fails and is slightly worse than V9a's 0.505925; extra
wet cells 21,307 (18,734 beyond 4 m), missing 609. Discharge p95 error 6.26377%
also fails (45.0 m3/s inlet, 42.127771 outlet). Stage absolute p95 0.693685 m,
settling depth p95 0.006056 m, finite state, full 941-section coverage, connected
wet path and nonfolding coordinates pass. This candidate is rejected for
runtime promotion; no threshold, captured bank or water mask was relaxed.
A read-only connected-component check finds 20,501 extra wet cells connected
to source-channel water versus 806 isolated extras across 162 total wet
components. Stranded pools therefore do not explain most of the mismatch.
Further blind deepening or an unchanged rerun is not justified by this result.
The first-frame check now binds eta, h, u, v, hu, hv and wetness with explicit
shape/finite checks (not only h/u/v). The actual V10 first frame passed this
stronger check; all 127 Chilko tests pass. Native fields were not interpolated
or recooked for that verification.
No normal scene, engine acceptance, rapid-location acceptance or FPS claim is
made for this construction correction. The three downstream full-chart
initial-clearance diagnostics are outside the correction and remain open.

## Next implementation steps

### Live Colorado engine validation (2026-10-07)

The six-core runtime has been imported into
`/Game/RaftSim/Maps/Continuous/L_Colorado_ContinuousShoreSixV2` using the existing
rendering-RHI batched importer. Exec 68972 exited 0; log is
`tmp/colorado-continuous-map-shore1-six-v2.log`. All 189 chunks/proxies completed
in six batches: 9,450 terrain collision probes maximum error 0.317972 cm;
217,102 wet-bed probes maximum error 0.261719 cm. Native render-height and Nanite
source checks passed, preserving collision. Dressing is 3,006 art-directed
nonblocking dryland instances across 95 chunks, at least 12 m from cooked water.
The contract is `tmp/colorado-continuous-map-shore1-six-v2.json`; 16 map-contract
and dressing tests pass. Only the exact candidate map/external packages are
ignored while validation is pending; no existing map was replaced.

**Exec 90243 / Unreal PID 24088 is running** the rendered normal-oar descent
`tmp/colorado-continuous-shore1-six-descent-v2/colorado_continuous`, using
`tmp/colorado-continuous-shore1-six-descent-plan-v2.json`. One trial travels
200-7150 m through all source boundaries, with gate captures and normal rescue
inputs, not checkpoint-separated sections. Check the live handle/process before
launching any engine/build. Initial native camera screenshot has been inspected:
raft, continuous water, banks and vegetation visible; no visible memory/foreign
scenario warning. Early telemetry shows the real 26610-vertex/38344-triangle
hull/render agreement, afloat with no grounding or penetration. These are early
observations, not whole-descent acceptance. This fixed-step rendered trial is
not a packaged FPS benchmark or a full Colorado descent. Source coverage beyond
7200 m, all other normal full-river maps, environment polish and packaged 20 FPS
acceptance remain required before commit/push.

1. The Colorado six-core shore1 candidate now passes native construction screens
   as recorded above; validate its matching runtime increment in the engine.
   Do not repeat the rejected predecessor or the completed shore1 cook.
   Extend the hash-verified shared-frame terrain/water
   coverage toward the complete Lees Ferry-Pearce Ferry descent. Preserve raft,
   crew, swimmers and rescue state across streaming. Short construction maps
   are integration tests, not replacements for the requested full river.
2. Use the completed V3 construction descent as continuity evidence, not a full
   river or class acceptance claim. Retain rejected V1/V2 solves; no unchanged
   rerun or weakened validation.
   Preserve V1 descent, V2 vegetation and production-eye camera captures. Refine
   the remaining near-forearm obstruction,
   refine forest appearance and measure actual frame cost with competing jobs
   idle. Passing source and coordinate tests is not a full-river delivery.
3. Preserve original V7/V7a and all earlier candidates as historical evidence.
   The source route remains V3-active-planform and complete profile V10.
   The new bounded depth V7-stage-calibration and audited canonical terrain
   V8-stage-calibration are recorded above; full/window V10 verification and its
   native test are terminal. V10 still fails shoreline and discharge as recorded
   above; localize the connected overflow before any new geometry experiment.
   Preserve independently verified full/window
   V9-active-planform as the preceding candidate. V9 is
   terminal and fails shoreline, settling and discharge; its exact-state V9a
   continuation is terminal and settled, but fails shoreline as recorded above.
   Do not repeat V7a, V8a, V9, V9a or the rejected raw-direction/expanded-chart candidates. The two
   image-bounded historical branch retirements are now implemented and tested;
   do not count this as engine integration or hydraulic acceptance. Use the
   captured October 20 image/network evidence, not native flooded cells, for
   any further source-water correction. Preserve original source polygons and
   label inferred widths/joins; rebuild dependent geometry and fields together.
   Retain the original numerical chart
   separately from corrected geographic stationing; all current source anchors
   have already been independently reprojected. The distinct upstream
   connectivity control (exec 10983) is terminal and proves normal native
   filling connects the initial gap; do not edit the bed to erase that initial
   mask artifact or repeat the test just to prove connectivity again.
   Reject folded, clipped or globally overlapping charts, and resolve channel
   capacity against the available source-supported cross sections. Resolve the
   three actual-chart corrected-source 38714.72/45865.48/45867.45 m initial-clearance diagnostics against
   full-hull navigation, and distinguish the source-normal audit from
   actual geographic cell stages and hydraulic behavior. Then add full-corridor
   vegetation and import the connected environment. Do not splice independently
   inferred beds or call an initial depth field a solved flow. Continue
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

### 2026-10-07 source coverage boundary repaired; rendered descent reaches third join

**Live jobs at this checkpoint:** rendered Colorado descent remains exec **90243**,
Unreal PID **24088**. The recovered source-only Colorado batch is exec **36422**,
Python launcher/worker **30048/12060**. Inspect these before launching anything
similar. No DLL, loaded map, normal packaged game or user SEIYGECore change was
replaced in this increment. No commit/push yet.

The production-raft uninterrupted descent has crossed the **1200, 2400 and
3600 m** source joins. Actual gate screenshots in
`tmp/colorado-continuous-shore1-six-descent-v2/colorado_continuous/` were visually
inspected; water and banks remain continuous, no visible seam/warning or
recorded swim/incident at these gates. At 3600 m the HUD shows **31:42**, **49%**,
**3.40 of 7.0 km**, **0 swims**, **0 incidents**, crew energy **0%**. This is a
single run from 200 m, not independent checkpoint resets. It is still live;
not a completed descent, full river, final environment polish or FPS proof.

Colorado source cores **0120-0131 (144000-158400 m)** finished composition:
`tmp/colorado-continuous-evidence-shore1-batch0120-0131-v1`. Terrain, classified
water and measured pool-bed captures have matching `batch0120-0131-v1` names.
All measured pool-bed changes are **0 m**; no source bed/profile conflicts.
Actual fine coverage is only **289247 cells** in 0120 and **102883** in 0121;
0122-0131 use explicit captured **10 m** fallback throughout. Do not call the
one-metre export lattice one-metre evidence. All **12** handoff checks, including
0119-to-0120, pass in
`tmp/colorado-continuous-bed-seams-shore1-batch0120-0131-v1`: maximum wet-bed
difference **0.00006103515625 m**, water-reference difference **0 m**, and
**0** classified-shoreline disagreements. These are shared wet-cell construction
checks, not proof of dry-bank, cooked-flow or engine continuity in that batch.

`review_colorado_continuous_bed_seam.py` now refuses a discontinuous reference
surface even when the bed matches. Both maxima must be <=0.1 m under the
existing shoreline condition. The completed batch was rechecked against this
stricter screen. Empty/nonfinite/negative statistics and independent reference
jumps have regression coverage. **144 Colorado tests pass**, including existing
continuous construction and both fine/mixed and coarse-only terrain paths.

The next source batch **0132-0143 (158400-172800 m)** initially stopped in exec
**86989** (terminal exit 1): core 0134's catalogue has no native fine-resolution
source. All coarse captures were already complete, and the original partial
fine directory remains preserved. The acquisition code now records explicit
catalogue absence with no fake raster and no empty/unlocked export request.
Unknown resolution, changed/incomplete catalogue and inappropriate datum remain
errors. The blender independently checks the absence receipt/hash and coarse
registration; its source-resolution map labels the result **10 m**, not 1 m.

Recovery uses `tmp/capture_compose_colorado_batch0132_0143_v1.py
--resume-fine-catalog-absence`, preserving 40 GiB free-space headroom. Completed
coarse inputs are reused; fine metadata/absence receipts are in
`tmp/colorado-continuous-terrain-1m-batch0132-0143-v2`. Cores 0134-0142 have no
fine catalogue source; 0132/0133/0143 have locked candidates but **zero usable
fine pixels**. Thus all twelve mixed outputs currently use explicitly labeled
coarse fallback. Classified-water and measured-bed extraction also completed;
geometric composition/seam review is still live in exec **36422**. Source
centreline points are outside the classified mask at one sample each in 0140
and 0141: preserve and review this, do not inflate the water mask to hide it.

Chilko's rejected V10 was diagnosed without a new cook or geometry change:
`tmp/chilko-v10-overflow-ground-stage-diagnostic-v3.json`. Stored source stage
arrays intentionally contain NaN outside mapped water; treating those cells
as zero evidence was invalid. V3 explicitly projects each wet point onto the
hash-verified corrected geographic route and extends its **inferred** profile
for diagnostic comparison only. Inside the mapped polygon it reproduces the
stored stage/reference exactly. Of **20501** connected extra wet cells, **8934**
have captured terrain >5 cm below that projected inferred stage, and **8884**
have terrain >5 cm below the similarly projected raw local DEM reference.
Ground-minus-inferred-stage median is **-0.001037 m**, p05 **-0.593941 m**;
this is not a measured flood extent. The largest 100 m groups are corrected
geographic stations **5800-5900 (3562 cells)**, **5700-5800 (3085)** and
**5600-5700 (2293)**. It exposes source/reference compatibility as well as native
excess stage; it does not authorize raising captured banks, expanding source
water, accepting the rejected solver, or another blind deepening experiment.
The old incomplete V1 diagnostic JSON and valid V2 remain historical evidence;
use V3 for outside-polygon comparisons. No new Green Mile/Miracle Canyon
coordinates or aliases were established.

The provincial orthophoto index remains metadata, not inspected fine imagery.
A fresh check of the [official imagery FAQ](https://openmaps.gov.bc.ca/thumbs/kmlviewer_help/wimsi_faq.html)
confirms that free low-resolution views remain copyrighted and personal-use;
commercial/publication permission is not implied. The [current base-map store
instructions](https://www2.gov.bc.ca/gov/content/data/geographic-data-services/topographic-data/base-map-online-store)
also distinguish free topographic products from purchased orthophotos. No
purchase, source-access bypass or game-asset reuse was made. The public 2006
thumbnail did not load in the web tool; do not claim its pixels were inspected.

Later source-batch progress: cores **0132-0134** have composed and passed their
wet-bed/reference handoff screens. Core **0133** reports **105** measured-bed /
profile conflicts; original survey crops remain unchanged and those cells are
not classified as supported measured bed in the composite. Review the conflict
locations before using that core hydraulically. Do not summarize this batch as
conflict-free or surveyed throughout. Exec **36422** remains live.

### 2026-10-07 twelve-core candidate and guarded remaining-source pipeline

This checkpoint supersedes the preceding live-job status, not its historical
evidence. **No commit or push yet; full-river delivery remains unaccepted.**

- Exec **36422** finished successfully. All twelve construction handoffs for
  source cores **0132-0143**, including the preceding-batch join, pass both
  wet-bed and reference-surface screens. Maximum wet-bed difference is
  **0.0001220703125 m**, reference difference **0 m**, classified-shoreline
  disagreements **0**. All twelve terrain exports use explicitly labeled
  captured **10 m** fallback, not measured one-metre detail.
- `tmp/colorado-batch0132-0143-conflict-ownership-v1.json` resolves the 105
  core-0133 conflict flags geographically: all are endpoint-clamped halo cells,
  not that core's owned interval. The actual shared TerrainMosaic selects core
  **0132** for all 105; all remain measured bed, with **0 m** difference from
  the original survey and no selected conflicts. Original captures are intact.
- `tmp/colorado-0140-0141-route-water-audit-v1.json` proves the two centreline
  warnings are **one identical geographic sample**, at source river mile
  **105.21**, station **169253.18515822515 m**, WGS84
  **(-112.315502501999, 36.189305991659694)**. It belongs to core 0141 and is
  **0.16760000051 m** from classified water. Nearby transect water intervals
  are retained in the receipt. This is not evidence of two blocked reaches,
  a solid rock or a navigable boat route; no polygon inflation or route move
  was made. Classification uncertainty and actual hydraulic passage still
  need consideration when this distant portion becomes a runtime candidate.

Exec **6485** completed the **0-14400 m** shore1 terrain/input candidate through
Badger Creek: `tmp/colorado-continuous-evidence-shore1-twelve-v1`,
`tmp/colorado-continuous-terrain-shore1-twelve-v1`, and
`tmp/colorado-continuous-inputs-shore1-twelve-joined-v1`. All source arrays and
wet/measured bed were compared to the preceding construction and preserved.
Only the already-explicit bounded inferred dry-shore clearance changed. All
eleven internal wet-bed/reference handoffs pass. There are **364** terrain
chunks and a **7322 x 167** two-metre hydraulic grid. Independent resampling
of exported terrain triangles agrees with native input bed to
**2.69869815e-9 m**. This is construction consistency, not solved acceptance.

Fresh native solve **exec 2970**, solver PID **29512**, is running in
`tmp/colorado-continuous-cook-shore1-twelve-v1`. It uses the frozen solver SHA
`984ac852bcea8d16ad8289d394e2a62306fb71e339cb6ce3dc5a6e4bd8aec28d`,
48000 steps at 0.05 s, HLL/order 2/CFL 0.2, authored feature strength zero,
fixture calibration disabled and no artificial initial-mass preservation.
It starts from independently checked finite initial fields, **not** a reused
six-core cook or continuation. Inspect launch/completion receipts before
reviewing or rerunning. Do not launch a duplicate native solve.

New `physics/scripts/build_colorado_continuous_source_batches.py` runs the
remaining **234 source cores (0144-0377, 172800-453334.02824855957 m)** in bounded
batches of at most twelve. Registered route identity/order/endpoint, previous
handoff, source hashes, explicit native-resolution coverage and at least
**40 GiB** free headroom are checked. Each batch preserves its captures and
receipts; any failure stops with its exact stage rather than overwriting or
discarding evidence. No source job promotes gameplay or launches native cooks.
All **147 Colorado regression tests pass**, including three new batch-planning
tests for the partial terminal core, gap/overlap, identity and invalid ranges.

This source-tail job is **exec 71588**, Python launcher/worker **15784/28132**,
output `tmp/colorado-continuous-full-source-tail-v1`. At this checkpoint batch
0144-0155 has captured/blended terrain and extracted water/pool bed; composition
is live. Do not launch manual overlapping source jobs at or beyond core 0144.
Inspect root `failure.json`/`completed.json` and batch receipts first.

Rendered uninterrupted production-raft descent **exec 90243**, Unreal PID
**24088**, remains live. Additional **4800, 5400 and 6000 m** gate captures were
visually inspected in `tmp/colorado-continuous-shore1-six-descent-v2/`.
At 6000 m the HUD reads **53:51**, **83%**, **5.80 of 7.0 km**, **0 swims**,
**0 incidents**, crew energy **0%**. Water and banks show no obvious join gap;
native logging still reports production hull/render equality (26610 vertices,
38344 triangles, zero error). Sparse shrubs appear detached against some
steep slopes in the 5400/6000 m views. Record this as an **unresolved rendered
vegetation concern**, not completed environment polish. The importer already
checks collision-ground anchors and mesh-pivot bounds, so a root-height cause
has not been established. Do not alter loaded assets or guess a repair before
checking the rendered terrain/plant relationship. This is still a fixed-step
editor diagnostic, not packaged performance or full-river acceptance.

Fresh name/location searches did not provide a new Green Mile or Miracle
Canyon geographic anchor. A search hit joining Chilko with "Miracle Mile"
in Cristina Opdahl's *More Rides* (Outside, July 1, 2001) is not such evidence:
the indexed article places that name in its separate Upper Youghiogheny
section. No synonym, coordinate, new rapid boundary or licensed imagery claim
was added on that basis. The existing Chilko source ledger and unresolved
location qualifications remain in force.

### 2026-10-07 uninterrupted descent, local vegetation support and streamed shadows

This checkpoint supersedes the preceding live-job status. No full-river,
packaged-performance or catalogue-placement acceptance is implied; no commit
or push has been made for this reconstruction effort.

**Native playable evidence:** exec 90243 exited successfully with unchanged
dependencies. The production oar raft travelled from 202.92385295 m to
7150.17601877 m in one uninterrupted 3881.4002 s simulation descent. All seven
recorded gates passed, with zero checkpoint restores, swimmers, incidents,
full-hull ground impulses and dry-centre seconds. There were 5544 completed
ordinary oar strokes; maximum roll/pitch were 5.1082/4.9662 degrees. The final
engine view was inspected. The receipt is
`tmp/colorado-continuous-shore1-six-descent-v2/colorado_continuous/results.json`.
This validates approximately 6.95 km of the construction candidate, not all
453 km or the later named rapids. It used fixed simulation stepping and is
not a 20 FPS measurement.

**Implemented vegetation correction:** the old central-gradient placement
test could cancel opposite slopes at folds. Colorado and Chilko dressing now
also screen eight one-sided cardinal/diagonal offsets on actual Landscape
triangles, retaining the central gradient and rejecting unknown support.
New planar/fold/diagonal/unknown-support tests pass. Combined discovery of
`test_colorado*.py` and `test_chilko*.py` passes **279 tests** (151/128).
The established standalone `shapefile.py` injection remains necessary in the
geospatial validation environment; do not prepend the older dependency tree.

The new Colorado dressing is a strict subset of the preceding candidate:
**109** locally steep placements removed, **2897** unchanged placements retained
across 94 chunks. Source terrain, cooked water and meshes were not altered.
Evidence: `tmp/colorado-shore1-vegetation-support-diagnostic-v1.json` and
`tmp/colorado-continuous-dressing-shore1-six-support-v3.json`.
Fresh map `/Game/RaftSim/Maps/Continuous/L_Colorado_ContinuousShoreSixSupportV3`
was imported only after the preceding engine exited. Import exec 82918 passed
9450 collision probes (maximum 0.317972 cm), 217102 wet-bed probes (0.261719 cm)
and 2897 decorative ground-anchor checks (0.273296 cm), with all 189 Nanite
terrain proxies verified at source LOD0/relative precision4. Two short native
ordinary-oar trials, at 5400 and 6000 m, cleared without resets or swimmers;
exec 91852 exited with unchanged dependencies. Screenshots were inspected.
Some shrub silhouettes still appear detached: collision root anchoring alone
does not settle rendered foliage quality, and this is not declared fixed.

**Triangular canyon-wall shadows isolated:** same-map, process-only comparisons
preserve the map, runtime and DLL hashes. Disabling Nanite removes the wall
patches, but increasing Nanite detail with `r.Nanite.MaxPixelsPerEdge 0.25`
does not. Enabling `r.Nanite.VSMInvalidateOnLODDelta 1` removes them in the
inspected first, gate and final frames while retaining normal Nanite rendering.
The installed UE source explicitly describes this control as invalidating
virtual-shadow-map caches when streamed clusters reach the requested LOD;
its default is zero and it is experimental. This supports a streaming/cache
cause, not a reason to deform terrain, disable shadows or increase normal bias.
The invalidation run, exec **60333**, exited zero with stable dependencies and
cleared the same short section in 33.6000 simulation seconds. Native samples
are not bitwise identical across independent starts: the invalidation comparison
has maximum station/lateral/height differences of 0.001410/0.003474/0.003567 m
and roll difference 0.1395 degrees, with aligned sample times. These differences
are recorded, not hidden by asserting exact physics equality.

Comparison receipt: `tmp/colorado-support-render-comparison-receipt-v1.json`.
New frames: `tmp/colorado-continuous-shore1-six-support-streaming-invalidation-v1/`.
**No persistent render default was changed.** An isolated real-time cost
comparison is required before promotion: current visual runs used fixed-step
simulation, screenshots and a concurrent native hydraulic solve. Do not use
their wall times as performance acceptance or run the isolated profiling
harness while the solve remains live.

**Source and cook progress:** exec 71588 has completed cores **0144-0179**,
36 sections/43.2 km beyond the prior batch. All 36 handoffs pass; batches
0144-0155 and 0156-0167 have maximum wet-bed discrepancy 0.00006103515625 m,
0168-0179 has zero. Reference differences, shoreline disagreements, selected
measured-bed changes and source-bed/profile conflicts are all zero in these
three completed batches. Batch **0180-0191** is now active. These are source
construction results, not hydraulic or engine acceptance. The twelve-core
native solve (exec **2970**, PID **29512**) last reported **14400/48000** steps,
720 s simulation time, maximum depth 18.9928 m. It remains live; no duplicate
solve or source-tail job should be started. Disk headroom at this check is
127875112960 bytes; the source job retains its 40 GiB stop floor.

**Chilko evidence check:** the official provincial point-cloud catalogue was
queried at the independently diagnosed 5600-5900 m overflow area. Two 2023
CGVD2013 LAZ records declare classes 1/2/7/12, not water class9. This is catalogue
metadata only: neither LAZ was downloaded, no actual class histogram was
verified, and no measured water level follows. Receipt and source response are
`tmp/chilko-overflow-pointcloud-catalog-v1/receipt.json` and `catalog.json`
(response SHA256 `e77930335babe75709bb8256f94bc18a77078912a1cd92e88cd68f198373f900`).
Do not widen water masks, raise banks or promote the rejected V10 cook from
this metadata. The literature/map ledger still brackets Green Mile after
Bidwell and before White Mile without surveyed endpoints, and still lacks
a defensible geographic identity for Miracle Canyon. No new coordinate,
alias or imagery reuse permission was inferred.

### 2026-10-07 registered native diagnostics and imagery-origin repair

This checkpoint supersedes the preceding live-build status. The guarded
`continuous-diagnostic-access-build-v2` full Editor build succeeded after
correcting the failed v1 include to the installed `String/LexFromString.h`.
The terminal v2 receipt records exit zero. No engine was replaced while loaded.

**Continuous diagnostic repair:** `RaftSim.PlaceAtStation` previously admitted
only legacy map names. It now requires exactly one water configuration and a
valid current rapid/chart registration (or the validated legacy configuration),
and rejects nonfinite numeric input. This does not enable new water effects or
change the normal integration: continuous feature configuration already used
the registered chart. The native `RaftSim.Continuous.RapidRegistration` test
passed with zero warnings/errors in
`tmp/continuous-diagnostic-access-native-v2/index.json`, including wrong,
missing and invalidated chart rejection. The profiler accepts the specific
`Continuous/L_*` directory, rejects path traversal/alternate directories, and
labels continuous candidates separately in editor and packaged receipts.
Both parameter-binding and unchanged strict 20 FPS budget tests pass.

A fresh **actual game-mode** launch of
`/Game/RaftSim/Maps/Continuous/L_Colorado_ContinuousShoreSixSupportV3`
then verified exactly one placement at 5400 m, at world time 4.085546 s.
The production 26610-vertex/38344-triangle hull/render comparison remained
zero-error. Three frames at world times 12.390528, 14.415561 and 16.415921 s
show normal free drift (0.68-0.69 m/s, Rest command), not repeated placement
or scripted guidance. All three PNGs were inspected. The process exited zero,
with unchanged hashed dependencies and no runtime errors:
`tmp/continuous-station-command-v1/completion.json`;
`unreal/Saved/Screenshots/continuous-station-command-v1_000.png` through `_002.png`.
No render overrides were used. This short console-command validation is not
full-river, shoreline-quality, rapid-difficulty or FPS acceptance; a concurrent
hydraulic solve makes it unsuitable for isolated timing. Persistent Nanite
shadow settings remain unchanged pending isolated comparison.

**Futaleufu source correction:** both the evidence builder and the Terminator
location audit used the requested acquisition rectangle rather than the
captured Sentinel raster transform. The requested origin is 4.4082054 m east
and 1.0354171 m south of the actual native corner. New shared sampling uses
the native pixel centres, verifies captured NPZ hashes, CRS, band alignment,
shape, integer encoding, radiometry and nodata support, and refuses out-of-range
sampling. The location audit no longer clips partial boxes or treats unknown
pixels as dry land. Nine targeted tests pass; with the existing Chilko
location tests, **23** pass. Source captures, existing maps and cooks were not
rewritten. Regenerating any geometry still requires a fresh matching cook and
native collision/shoreline validation. Unsupported shoreline +/-5 m and local
water-height +/-2 m claims were removed from the builder documentation.

The repaired diagnostic
`tmp/futaleufu-native-grid-location-audit-v2.json` finds persistent bright-water
candidate bins at OSM 74.0-74.2 and 74.6-74.8 km within its 68-77 km search.
It explicitly does **not** identify a rapid by brightness alone. El Trono lies
outside that particular search, so the empty run comparison is not a failed
El Trono appearance test.

**Asleep at the Wheel cross-check:** the archived Rio Azul way endpoint
(-71.9711003, -43.3150156) projects exactly onto the captured mainstem at
67001.9 m. [GoRafting](https://gorafting.com/chile/futaleufu-river/) places
Asleep approximately 3 km after that confluence; the
[Whitewater Guidebook](https://www.whitewaterguidebook.com/chile/futaleufu-river-inferno/)
distance difference is 1.5 miles. Their resulting hypotheses disagree by
585.984 m. The native-grid Sentinel crops from 2020-02-20, 2024-02-19 and
2026-01-04 were all inspected: the approximately 70.0 km hypothesis overlaps
persistent bright water, while the 69.416 km marker appears smoother. This
supports a search area, not unique identity, precise whole-rapid bounds,
measured hole geometry or a resolved catalog class (the guides disagree).
Receipt: `tmp/futaleufu-asleep-source-review-v1/report.json`; source hashes,
OSM/Copernicus rights and image-date discharge uncertainty are retained there.
No guide map artwork was imported or licensed by inference.

**Ongoing Colorado work:** the source-tail job (exec 71588) has completed
cores 0144-0215, 72 cores/86.4 km beyond its starting point, reaching 259.2 km
of the registered route. All 72 construction handoffs pass, with zero selected
measured-bed changes. Tile 0182 reports one source-bed/profile conflict, not
zero: its local station is endpoint-clamped to zero in its upstream halo.
The same EPSG:6404 cell (162492.5, 596603.5) belongs to core 0181 at global
station 217667.330773 m. That owner preserves the measured 567.814208984375 m
bed exactly and does not flag a conflict. Keep the warning and explicit
ownership; do not overwrite source values or certify all halos as conflict-free.
Read-only receipt: `tmp/colorado-0182-conflict-diagnostic-v1.json`.
The twelve-core native solve (exec 2970, PID 29512) last reported
28800/48000 steps, 1440 s simulation time, maximum depth 18.967 m. It remains
live; no duplicate solve or isolated performance launch is warranted yet.

**Chilko:** the existing literature/map ledger remains authoritative about
uncertainty. This check found no new independent Green Mile/Miracle Canyon
coordinates; the operator's public `CCF2026.jpg` link again returned a cache
miss and was not visually inspected. Repeated checks are not new sources.
Green Mile remains bracketed by Bidwell and White Mile; Miracle Canyon still
cannot be assigned to a particular canyon or silently aliased to Magic Canyon.
No arbitrary estimate, midpoint split, map import or new placement was made.
No full-river acceptance, commit or push is claimed by this checkpoint.

### 2026-10-07 next playable extension and cliff-detail projection

The preceding goal turn made progress (imagery sampling and registered native
diagnostics were repaired and tested). This continuation confirmed both
existing construction processes live before doing additional work; no new
hydraulic solve was launched.

**Implemented, compiled, awaiting rendered validation:** the continuous/catalog
terrain importer now creates versioned `M_ColoradoCatalogGroundV2` and
`M_ChilkoContinuousGroundV2` materials. Existing V1 assets/maps are preserved.
The old material sampled only world XY, stretching detail up steep canyon
walls. V2 uses the same existing texture and 3.5 m repeat on YZ/XZ/XY planes,
blended by normalized squared world-space vertex-normal components. This
changes texture projection only, not source heights, water, collisions,
normal quality settings or surveyed features. The guarded full Editor build
`tmp/continuous-diagnostic-access-build-v3` succeeded (86.26 s, exit zero).
No generated V2 asset, screenshot, shader-performance or packaged acceptance
is implied by C++ compilation. Inspect the actual native import and subsequent
views; keep the extra texture samples visible in the later cost audit.

**Active integration job:** exec **52857**, driver
`tmp/finish_colorado_twelve_candidate_v1.py`, Python wrapper PID **27808** /
runtime PID **29856**, was confirmed live. Its receipt directory is
`tmp/colorado-twelve-integration-v1`. It waits on the specific existing native
solve PID **29512** and its terminal immutable-input receipt; it never starts
or restarts a solver. It then runs the unchanged construction review, including
every registered core, and refuses runtime export if any gate fails. Only a
passing result is exported to
`tmp/colorado-continuous-runtime-shore1-twelve-v1`, given grounded sparse
vegetation, and bound to a fresh
`/Game/RaftSim/Maps/Continuous/L_Colorado_ContinuousShoreTwelveV1` contract.
The import waits for the versioned material build and sixty seconds with no
shared engine/build activity. Failure and rejected evidence are retained;
there is no automatic acceptance or promotion to the normal menu.

The existing solve last reported **38400/48000** steps, **1920 s** simulation
time and maximum depth **18.9628 m**. Its session is still exec **2970**.
The independent source-tail job, exec **71588**, has started batch 0240-0251;
this is source-processing progress, not evidence of playable coverage.

Prepared `tmp/colorado-continuous-twelve-descent-plan-v1.json` runs from
200 to 14350 m without intermediate restores, through Badger Creek, with
ordinary oar/rescue commands and fourteen observation gates. These are
construction continuity gates, not precise named-rapid boundaries or a
demonstration of class difficulty. It has **not** run yet. After terminal
integration, inspect the import's native geometry/water/vegetation receipts,
reopen the map to verify serialized rapid registration, and run this descent
using `unreal/Scripts/run_rapid_assessment.ps1 -PreparedTrials -Render` with
a fresh label. Follow with source-registered Badger early/late/no-steering
approaches and actual first/middle/end views. Its documented decision remains
upper-right-hole avoidance followed by the tongue/waves, not an invented
mandatory slalom. The GoRafting Badger page was rechecked; approximate guide
descriptions do not upgrade authored hole dimensions to measured geometry.

Normal-menu installation, all remaining river lengths/rapids, isolated
packaged 20 FPS and final commit/push remain required. Do not confuse a saved
continuous candidate or the automatic integration worker with those outcomes.

### 2026-10-07 native Badger approach registration

This continuation made supporting validation progress, not a visible map
delivery. `unreal/Scripts/reproject_continuous_rapid_trials.py` now transfers
retained approach paths through the actual source/world/target coordinate
adapters. It checks common geographic frames, source coverage, monotone
projected routes, centimetre round trips and the harness's interpolated path.
It converts steering events and the initial physical heading, refuses unknown
distance/event fields and existing outputs, and explicitly excludes a
station-varying heading-hold test instead of silently changing its meaning.
Six contract tests pass; their linear adapter stub is not engine evidence.

Fresh **native** exec **39325** exited zero with no logged errors. Receipt
`tmp/badger-continuous-trials-v1/receipt.json` records 1,104 production-adapter
queries, maximum world round-trip error **0.0000301364 m** and maximum
interpolated approach deviation **0.001456773 m**. Six trials now cover
approximately station **12682.742-13032.742 m** in the continuous hydraulic
chart: tongue, right-hydraulic, right-early, right-late, left-bypass and
hands-off. The old poor-angle heading-hold case remains explicitly excluded
pending new calibration. Source inputs were unchanged. The command used
NullRHI for coordinates only; it did not run a boat, save a map, validate
water, render screenshots or measure FPS.

After the existing twelve-core integration passes, use
`tmp/badger-continuous-trials-v1/plan.json` with the normal assessment runner
(`-PreparedTrials -Render`, river `colorado_continuous`, fresh label), in
addition to the prepared uninterrupted 14 km descent. Do not launch before
`tmp/colorado-twelve-integration-v1/completed.json` exists and its saved map
and serialized registration are verified. Existing cook exec **2970**, PID
**29512**, is still live at last observation, most recent progress
**43200/48000** steps. Integration exec **52857** is still waiting on it.
Source-tail exec **71588** completed batch0240-0251; this remains source
processing, not playable river coverage. Approximately 114.7 GiB disk space
remained. No duplicate cook/build was launched.

Another task rebuilt the shared engine and recorded `crew-bodies-v1` during
this turn. Our no-overlap guard refused two launches; native reprojection
only started after its process exited. Preserve that task's new crew source
edits as well as the existing SEIYGECore edits. No process was stopped and
no message was sent to the other task. Fresh Chilko searches yielded no new
location authority: the existing source ledger and unresolved identities
stand unchanged. No guessed rapid bounds, alias, normal-menu promotion,
commit, push or full-goal acceptance is claimed here.

### 2026-10-07 twelve-core rejection and physical-friction unit repair

The previous turn was supporting progress (native approach reprojection).
This turn completed the pending hydraulic review and repaired a newly
identified input-contract error. Original solve exec **2970** is terminal
exit zero (8,242.11 s solve, 172.684 s export, 48,000 steps/2,400 simulated
seconds). Inputs and frozen solver were unchanged. Integration exec **52857**
is terminal **rejected**, not waiting: its unchanged gates failed discharge,
settling and eleven of twelve individual source cores. **No twelve-core map
or runtime was created.** Do not run the prepared boat trials yet.

`tmp/colorado-continuous-review-shore1-twelve-v1/review.json` reports wet IoU
0.983060932, zero extra wet cells over 4 m outside the source, stage-error
p95 0.472064 m, settling p95 0.041940 m, inlet/outlet 226.534773/152.515977
m3/s and discharge-error p95 33.8888%. The source water/geometry agreement
does not excuse the flux failure. All rejection evidence is retained.

Read-only diagnostic exec **30767** completed successfully:
`tmp/colorado-twelve-transient-diagnostic-v1.json` uses native face-flux
inspection at 0, 1200, 2160 and 2400 s, with source hashes and no added time
steps. Initial inlet/outlet both equal 226.534773 m3/s; outlet subsequently
falls to 161.623252, 153.645792 and 152.515977. The last 240 s store water at
73.470747 m3/s, consistent with the growing inlet/outlet imbalance. Thus the
inlet is not missing; the reach remains transient. Extending the same solve
blindly would not address its resistance-unit discrepancy.

The fresh Colorado continuous builder was passing **0.04** directly to the
native damping coefficient. The already verified frozen solver implements
`roughness * speed / h^(4/3)`, not `g * roughness^2 * speed / h^(4/3)` (same
binary SHA as `tmp/chilko-native-friction-contract-v1/result.json`). For the
explicit **inferred**, not measured, Manning n=0.04 hypothesis, the native
coefficient is **0.015696**. The previous value supplies 2.54842 times that
resistance. This establishes a physical-parameter discrepancy, not proof that
it explains every flux/geometry failure or that the corrected river passes.

Implemented:
- New shared-frame Colorado scenario construction now uses the existing
  explicit friction contract; standalone legacy input behavior is unchanged.
- Joining rejects differing physical-friction contracts and preserves the
  Manning hypothesis separately from the coefficient. Native review checks
  the contract; future roughness sensitivities convert the physical n once.
- `repair_colorado_friction_inputs.py` creates a fresh packet with only the
  coefficient and its metadata changed. It refuses unrelated/ambiguous
  packets, double conversion and existing output. Actual candidate geometry,
  reference, coordinate map and starting state are byte-identical to V1.
- Runtime export already preserves the native coefficient in its historically
  named `manning_n` field, with explicit semantics; no second conversion or
  installed-map mutation is made. Forty targeted tests pass.

**Live successor:** exec **12666**, native PID **18880**, driver
`tmp/cook_colorado_twelve_friction_v2.py`, confirmed live after launch.
Inputs: `tmp/colorado-continuous-inputs-shore1-twelve-friction-v2`.
Cook: `tmp/colorado-continuous-cook-shore1-twelve-friction-v2`.
It runs one 48,000-step/2,400 s solve with two worker threads, the same frozen
binary, unchanged bed/source terms, zero authored forcing, and no mass fix or
fixture calibration. It then performs the unchanged full-domain and per-core
review into `tmp/colorado-continuous-review-shore1-twelve-friction-v2`.
Check its exact live handle/terminal receipts before any further cook. No
automatic runtime/map import is scheduled for this successor: inspect its
review first. A passing result needs fresh runtime/dressing/map paths, native
collision and saved-profile checks, rendered Badger trials and the continuous
descent. The old V1 prepared plans must be rebound to that verified new map;
their chart identity must remain checked. Full-river, normal-menu, packaged
20 FPS, all catalog entries and final commit/push remain outstanding.

### 2026-10-07 active extension through House Rock and source exclusion

- A separate source-only extension is live in exec **61302**, Python PID
  **4512** (wrapper **28976**): `tmp/build_colorado_through_house_v1.py`.
  It targets `tmp/colorado-continuous-through-house-v1`, source stations
  **0–28,800 m**, reusing cores 0–11 and extending through Soap Creek and
  House Rock with cores 12–23. Cores through 17 have passed the per-core
  measured/wet-bed preservation checks. It will check all 23 source seams,
  export common-lattice terrain, and join fresh friction-corrected inputs.
  Check its `completed.json` or `failure.json` before doing anything else;
  no native cook, runtime export or map acceptance is implied.
- Corrected twelve-core solve exec **12666**, native PID **18880**, remains
  live; latest progress is **4,800/48,000 steps**, 240 simulated seconds.
  Do not duplicate it or overwrite its inputs. The separate full-source
  tail exec **71588** has completed batch 264–275 and is working on 276–287.
- Added the inspected Contos 2010 American Whitewater article to Chilko's
  source ledger as a geographic exclusion: its detailed descent is on the
  Taseko, not upper Chilko. Full three-page extracted text was inspected;
  PDF screenshots/page images failed to fetch. No Green Mile/Miracle Canyon
  point or boundary was recovered. Do not repeatedly retry the same failed
  image fetches or transfer the Taseko features to Chilko. Twenty-four
  location/friction tests passed. This is supporting research, not a visible
  game improvement, and the two names remain geographically unresolved.

### 2026-10-07 original Chilko lidar support and through-House construction

**New source evidence, not a new accepted water solution:** the two public
2023 LAZ files covering the diagnosed 5600–5900 m Chilko area have now actually
been downloaded and decoded, rather than only reading their catalogue classes.
Both LAS headers identify EPSG:3157 horizontal / EPSG:6647 vertical coordinates.
Original complete files remain in `tmp/chilko-overflow-pointcloud-inspection-v1`:

- `bc_092n080_1_4_2_xyes_8_utm10_20231007_20231007.laz`, 505,228,212 bytes,
  SHA-256 `411d511d763c46560a0367773e79e6e824184fd35b9ba0e7d2bb8ef3feda69a9`.
- `bc_092n080_1_4_4_xyes_8_utm10_20231007_20231012.laz`, 481,556,631 bytes,
  SHA-256 `980ede2a18d25add442948145e8c09ce9ff1035802a7c7af1e235314a283a679`.

V1 inspection exec **69042** stopped at its crop-memory bound on the second
file; both downloads and the first successful inspection were preserved.
V2 exec **25563** is terminal **0**, using 500,000-point chunks and separate
hashed crop parts without redownloading. Its final receipt is
`tmp/chilko-overflow-pointcloud-inspection-v2/completed.json`: 179,033,817
original points decoded, 8,489,425 within the bounded area, including 980,923
class-2 ground returns. No local water-class-9 points were found. Classification
does not make these ground returns surveyed bathymetry or a measured stage.
OGL-BC attribution and source URLs are retained.

The unchanged rejected V10 cook was compared with those original returns in
exec **22011**, terminal **0**. Receipt:
`tmp/chilko-overflow-lidar-support-v1.json`. Of 10,472 connected extra-wet cells
inside the inspection rectangle, 9,647 have unflagged classified ground within
0.5 m and 10,327 within 1 m. For the half-metre-supported subset, nearest point
minus DEM p05/median/p95 is **-0.040850 / 0.000795 / 0.030080 m**; 5,230 nearest
points lie more than 5 cm below the projected inferred reference stage.
Horizontal offsets remain explicit: this is not an exact co-located DEM error
or a measured flood extent. It materially rules out absent ground-point support
as the explanation for most sampled overflow cells. Preserve the captured
ground; next investigate the inferred stage/active shoreline compatibility,
not arbitrary bank raising or another identical failed cook.

`chilko_lidar_support.py` supplies the bounded diagnostic and excludes flagged
and non-ground points. Four focused tests and twelve related bed/window tests
pass. No terrain, flow, named rapid placement or game asset changed here.

**Colorado extension:** exec **61302** is now terminal **0**. The fresh
`tmp/colorado-continuous-through-house-v1/completed.json` and independent read
verify all 24 cores, **0–28,800 m**, **23 passing source bed seams**, **700**
common-lattice terrain chunks and exactly zero encoded shared-edge difference.
Joined inputs are **14,488 × 167** cells at 2 m, with inferred Manning n=.04
encoded as native coefficient .015696. Measured/wet source bed is unchanged.
There is no new 24-core native cook or map: wait for corrected twelve-core
exec **12666** and inspect its unchanged acceptance gates before selecting
the next hydraulic run. Full-source tail exec **71588** has reached batch
288–299; inspect its live handle and completion receipts before restarting.

### October 7: actual lidar capture dates and construction-flow parameter repair

Original point timestamps, not filename date ranges, now establish that all
8,489,425 points inside the bounded Chilko overflow rectangle were collected
on **October 7, 2023**. Exec **90224** is terminal **0**; it reused the two
hash-verified downloads, decoded XY/GPS in 500,000-point chunks, and neither
downloaded again nor changed terrain. Both UTC and fixed-PST dates agree.
The first file's local times span 17:55:14–18:05:53 UTC; the second spans
17:13:06–18:05:53 UTC, despite its October 7–12 filename.

Receipt: `tmp/chilko-lidar-capture-dates-v1/completed.json`, SHA-256
`9f0deb88714be1f9b03c0f81d1fc92f22b536a2dcafc0973adce6a1026403457`.
Durable source URLs, hashes, bounds and qualifications are in
`physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/source_capture_flow_evidence_2026_10_07.json`.
The retained HYDAT 08MA002 series gives **33.5 m3/s** on the lidar date and
**29.6 m3/s** on the October 20 image date, against the **45 m3/s** construction
hypothesis. This is a concrete non-concurrent-source confound, not proof that
all overflow is legitimate. The outlet's daily discharge is not measured
instantaneous local discharge; its assumed-datum level is not CGVD2013 stage.

Fixed an independent builder defect: `build_chilko_corridor_scenario.py`
reconstructed the canonical bed with default 45/.045 even when its manifest
explicitly specified different discharge/Manning n. It now uses the canonical
parameters, retains the existing identity checks, and labels serialized flow
from the actual value. The depth builder also takes explicit bounded parameters
instead of silently reverting its capacity fit/receipt to 45/.045. Defaults
remain unchanged. **40 tests pass**, including actual serialized-grid flow,
native friction units, default/nondefault parameter forwarding, timestamp
conversion and UTC/PST midnight handling. No captured ground, gameplay flow,
runtime map, review threshold or rejected V10 evidence was changed.

Next distinguish fixed inferred bathymetry from boundary-flow sensitivity;
do not re-carve a different bed at each discharge merely to match a lower-flow
image. Colorado's corrected twelve-core solve **12666 / PID 18880** and
source-tail **71588** remain active; no duplicate cook was launched. The other
task is still recording South Fork riparian assets; do not overwrite its DLLs
or edits. Geographic literature searches did not produce new Green Mile or
Miracle Canyon boundaries. A new Team Bad Idea 2016 first-person-trip search
lead returned a web cache miss on full-page retrieval and supplies no accepted
location; do not treat its search excerpt as an inspected map.

### October 7: fixed-bed source-flow comparison launched; sparse imagery scan repaired

The preceding turn made progress: original point times resolved the local
capture date, and construction parameters stopped silently reverting to defaults.
This turn keeps bathymetry fixed while testing the resulting discharge hypothesis.
`prepare_chilko_fixed_bed_flow.py` verifies the saved native parent, preserves
all h/eta/u/v/hu/hv/wet values, and scales only the west ghost longitudinal
velocity. Bed, chart, references, features and probes are byte-identical;
friction and outlet stage are unchanged. The 45 m3/s terrain-inference receipt
is retained explicitly, distinct from the diagnostic 33.5 m3/s inflow.
The original failed V10 review is preserved, not upgraded to a pass.

Actual preparation exec **24686** finished **0** in
`tmp/chilko-fixed-bed-flow33p5-v1`. Its build report binds the original inputs,
review and exact final frame by hash. The distinct native job is now live in
exec **5479**, solver PID **28524**, driver
`tmp/cook_chilko_fixed_bed_flow33p5_v1.py`. It uses the frozen solver SHA-256
`984ac852bcea8d16ad8289d394e2a62306fb71e339cb6ce3dc5a6e4bd8aec28d`,
one OMP thread, 48,000 steps at .05 s, and a frame every 4,800 steps. At last
poll it reached **9,600 / 48,000**, 480 simulated seconds. Cooks go to
`tmp/chilko-fixed-bed-flow33p5-cook-v1`; the terminal review is intended for
`tmp/chilko-fixed-bed-flow33p5-review-v1`. Do not duplicate or assume completion
because frames have not appeared yet; inspect the live process/session first.

The launch guard permits only the already-recorded distinct Colorado PID
18880 alongside this comparison, checks at least 6 GiB free RAM / 40 GiB disk,
and never touches shared Unreal DLLs. Colorado exec **12666** reached
**14,400 / 48,000**, 720 simulated seconds. Source-tail exec **71588** completed
batch 288–299 and entered 300–311. The other task is running crew/gear engine
review; leave it and its changes alone.

`checked_cook` now explicitly refuses fixed-bed diagnostic flow experiments as
runtime export sources, even if their construction screen passes. This keeps
lower-flow source comparisons from silently replacing the requested game flow.
Sixty-one related construction, continuation, review and timestamp tests pass.
No new playable map, geography, vegetation, class match or performance claim.

**Futaleufu:** extending the existing Asleep search uncovered a real sampling
defect in `audit_futaleufu_terminator_location.py`: a 100 m bin was omitted if
it contained no OSM vertex, even when a source segment traversed it. It now
samples each bin midpoint by interpolation along source segments, preserves
bends, rejects out-of-route extrapolation, and refuses overwriting a report.
Native raster coordinates, radiometry and brightness thresholds are unchanged.
Twelve imagery/location tests pass, including sparse/dense source equivalence.
The fresh `tmp/futaleufu-asleep-extended-source-review-v3.json` covers every one
of 42 bins from **68.8 to 73.0 km** on all three archived image dates, with zero
missing bins; V2 is retained. Maximum bright-pixel counts per box are 2/3/2,
below the unchanged 8-pixel threshold. This is a completed coverage check, not
evidence that no rapid exists or a uniquely located Asleep at the Wheel.
The earlier crop's bright-water search hypotheses remain hypotheses; no new
rapid boundary or class is assigned from this spectral screen.

### October 7: geographic review checkpoint and captured-source recovery

Expanded the Chilko ledger with Wells part II, the OARS itinerary, and Teague's
2007 photograph metadata. These are explicit source-quality assessments, not
three new geographic fixes. Wells continues the same Bidwell rescue; OARS does
not name Green Mile or Miracle Canyon; the photo metadata supplies no camera
coordinates. The newly attempted OARS map and plausible Wells part-III URL
were unavailable. Do not repeat these unchanged fetch failures or count unseen
pixels as inspected maps. Fourteen geographic-audit tests pass.

The corrected-route projection still places the representative BC Whitewater
markers at 38,296.184 m (Bidwell), 42,461.506 m (White Mile), and 44,533.005 m
(Eagles Talon), from the lodge construction origin, not lake-outlet kilometres.
The first two bracket Green Mile/White Kilometer; that 4.165 km bracket is
neither their individual boundaries nor proof of synonymy. Miracle Canyon's
precise identity/bounds remain unavailable in inspected sources. Preserve this
uncertainty without inventing two non-overlapping rapids or relabelling the
upstream geographic Lava Canyon. Current playable labels are still displaced;
this source work has not repaired or validated the runtime map.

The prior full corrected Futaleufu scan is verified at
`tmp/futaleufu-full-location-midpoint-audit-v1.json`: all three captured dates,
60-82 km; its 62.3-62.5 km bright cluster contains the mapped El Trono control
at 62.4024 km. Other clusters include 74.0-74.3 and 74.6-74.8 km. These are
spectral candidates, not named-rapid boundaries. GoRafting lists Terminator
Wave and Terminator Rapid at the same approximate 39.25 km, so this marker
cannot independently locate both. Existing observation notes already use
Rio Azul/Pasarela scaling; inspect that registration and actual photo control
before attempting another single-anchor offset or assigning Asleep.

**New resolved source-pipeline error:** Colorado source-tail exec **71588**
ended **1** during batch 0312-0323 terrain blending, after completing through
core 311. USGS raster 64838's retained catalogue reports LowPS
`0.9999999999999971`, while blending required exact equality to 1. The capture
had correctly retained 1,968,837 valid fine cells for core 323. No source raster
was missing. `nominal_resolution_matches` now allows only absolute 1e-12 m
catalogue roundoff (zero relative tolerance), preserves original metadata,
and rejects actual coarse/invalid resolutions. Acquisition uses the same
comparison for the symmetric just-above-1 case. Coverage, datum, pixel and
hydraulic acceptance requirements are unchanged. Twenty-five related tests
pass, including actual raster blending with that original LowPS value.

Recovery driver `tmp/recover_colorado_source_batch0312_v1.py` is running in
exec **4166** (Python 36252/35884 at last check). It checks captured hashes,
catalogue locks, source index, preceding core 311 and 40 GiB free-space guard,
then uses the already-downloaded 312-323 sources in fresh
`tmp/colorado-source-recovery0312-v1`. All twelve raster blends now succeed,
including formerly rejected core 323; water/bed composition and seam checks
are still pending. Original failure and partial files remain untouched. After
successful seams it continues only 324-377 in
`tmp/colorado-continuous-full-source-tail-v2`. Inspect the live process and
receipts before restarting; no duplicate capture or native cook was launched.

Chilko fixed-bed 33.5 comparison exec **5479** reached 38,400/48,000 (1,920 s);
Colorado corrected-friction exec **12666** last reported 19,200/48,000.
Both remain active and unaccepted. No new game assets, full-river acceptance,
packaged FPS, commit or push is claimed. Continue the useful remaining work;
the newly found source-pipeline defect is repaired, not a reason to mark the
overall goal blocked or complete.

### October 7: corrected Pacuare sequence and completed Chilko flow comparison

Pacuare's source catalog contained a real downstream-order error: it placed
Upper Huacas before Bobo/Rodeo/Double Drop and Guatemala before both Pinballs.
Re-read the public GoRafting guide and cross-checked the already-inspected lodge
map. The corrected middle sequence is Bobo, Rodeo, Double Drop, Upper Huacas,
Lower Huacas, Upper Pinball, Lower Pinball, Guatemala, Cimarrones. The new
`catalog_order_evidence_2026_10_07.json` records the fourteen public guide
kilometres in their **San Martin** frame, separately from Bobo's lodge-map
bracket. They are NOT `river_km` values in the existing runtime station frame.
Bobo/Bobito identity, exact boundaries and class disagreements remain open;
the tributary Bobito Falls is not substituted for a mainstem rapid.

Regenerated the existing named-rapid review markers, review geometry, review
runs and Pacuare A3 status after verifying all four were reproducible before
the change. The order-only stationing and non-production gates remain intact.
Thirty-two targeted registry, stationing, Chilko location and fixed-bed-flow
tests pass. This repairs source/review data, not the actual playable Pacuare
geometry. Existing named trial matching uses names for Pacuare (not renumbered
orders), so no historical native trial was reassigned to a different rapid.

Three retained OSM controls are available for the next Pacuare geographic
registration: Linda Vista node 13809756614 at source-chain 73,785.8 m; Lower
Huacas node 13805040110 at 83,041.6 m; Dos Montanas node 13805044421 at
92,483.4 m. Their corresponding guide distances are 4.14, 13.33 and 22.67 km.
These are approximate crowdsourced point controls, not rapid endpoints or
independent surveyed observations; the source-chain origin is the relation's
upstream end. Do not transfer those numbers directly into existing game
coordinates or use equal catalog-order spacing as geographic placement.

Chilko exec **5479** completed successfully after 48,000 native steps (2,400
simulated seconds) on the unchanged fixed bed. Its review is
`tmp/chilko-fixed-bed-flow33p5-review-v1/review.json`. At the 33.5 m3/s diagnostic
inlet, outlet flow is 34.33 m3/s and 95th-percentile face-flux error is about
2 percent; depth settling is 0.00534 m. However, wet IoU is only **0.52402**,
with **19,014** extra wet cells (17,007 farther than 4 m from the reference).
Surface-reference absolute p95 is **0.91221 m**. The wet-mask gate still fails;
no import or gameplay-flow change is authorized.

Read-only comparison against the 45 m3/s parent confirms identical bed arrays.
Most excess cells remain connected to source-channel water: 17,579 of 19,014,
versus 20,501 of 21,307 in the parent. Lower inflow alone has therefore not
resolved the spread; this is not solely a collection of isolated warm-start
puddles. Source reference stage remains inferred, and the mixed-date mapped
planform is not a surveyed 2 m shoreline. Preserve ground, masks and acceptance
criteria while resolving that distinction; do not raise banks or clear wet
states to force a passing receipt. No further native Chilko cook was started.

Colorado source recovery **4166** has completed cores 312-323 using retained
downloads, all twelve bed handoffs passing with unchanged source hashes.
`tmp/colorado-source-recovery0312-v1/completed.json` ends at source station
388,800 m. The same process advanced to cores 324-377 in the planned V2 tail;
324-335 acquisition/blending has completed and composition is ongoing. This
is source construction, not 388.8 km of accepted gameplay. The separate
corrected-friction Colorado native solve **12666** remains active; inspect
its output before launching any replacement. No DLLs, active captures or
another task's changes were touched.

### October 7: geographic registration provenance and Pacuare source rights

The Pacuare guide-to-OSM registration is now implemented in
`physics/scripts/register_pacuare_catalog_locations.py`, with five focused
tests. `tmp/pacuare-catalog-location-registration-v1.json` preserves three
original captured OSM controls and registers twelve catalog search points.
The first and last controls span Linda Vista to Dos Montanas. Bienvenidos and
Las Ranitas are outside that control span and are not extrapolated; Bobo's
identity/location remains unresolved. Each record explicitly refuses runtime
placement and leaves rapid boundaries null. A 167.6 m spread between the three
single-offset estimates motivates piecewise registration; it is not an error
bound. No IGN/SNIT material is used by this registration.

An important source-rights correction is recorded in
`pacuare_river_costa_rica/review/snit_rights_review_2026_10_07.json` and the
Pacuare plan. The official SNIT conditions explicitly prohibit commercial use,
including derived geographic products. The old captured manifest's permissive
interpretation is superseded without rewriting or deleting the capture. A
user question about commercial distribution and replacement versus separate
permission is pending. Do not acquire more SNIT data or promote its derivatives
for commercial shipment while that decision remains unresolved. Independently
licensed OSM/Copernicus evidence remains separate.

Additional Chilko literature searches found no new coordinate authority for
Green Mile or Miracle Canyon. The UC Davis 2011 field-summary HTML describes
an alluvial/island/confluence study, not named rapid bounds; its full linked
report was not inspected. The newly attempted 2011 gallery returned a cache
miss. Do not repeat this failed access or claim all literature/maps were read.
The existing Green Mile/White Kilometer shared Bidwell-to-White-Mile search
bracket and unresolved Magic/Miracle identity remain unchanged. Corrected-route
audit brackets now preserve each rapid's name, sources and unresolved status,
instead of emitting indistinguishable anonymous intervals. Boundaries stay
null and runtime-placement authority stays false; a regression test covers
this distinction. Thirty-four Chilko-location, Pacuare-registration, catalog
and A3 tests pass; targeted diff whitespace checks pass.

Colorado source job 4166 advanced to cores 336-347 (water/pool crops emitted).
Corrected-friction solver 12666 remains active. Another task's Unreal crew
review is active; no engine builds or DLL replacements were started here.
These are research/source improvements, not new playable terrain or completed
full-river acceptance. No new FPS result, commit or push is claimed.

### October 7: continuous Colorado middle-source assembly repair

The previous goal turn made progress by preserving named source provenance in
corrected Chilko stationing and verifying the updated catalog registrations;
it did not establish new Green Mile/Miracle Canyon boundaries. This turn
returned to continuous environment construction rather than repeating those
unchanged literature searches.

Found a concrete assembly inconsistency: source cores 24-119 still use the
old 0.15 m inferred dry-shore hypothesis, while the preceding 24-core candidate
and cores 120 onward use 1 m. The new source-only
`harmonize_colorado_shore_sources.py` reuses the exact captured inputs, applies
that existing 1 m construction policy, and independently proves all classified
water, measured bed, inferred wet bed, source terrain arrays, coordinates and
other reference fields remain identical. Only bounded inferred dry-shore bed
cells and their ownership/class tags may change. This is not a surveyed-bank
claim or a relaxation of native water-footprint/stage acceptance.

Live exec **8000** runs `tmp/run_colorado_harmonize_middle_v1.py`, child Python
**17136**, wrapper **17976**. Selection:
`tmp/colorado-middle-shore-source-selection-v1.json`; fresh output:
`tmp/colorado-continuous-middle-shore1-v1`. It covers cores 24-119 and verifies
handoffs to unchanged cores 23 and 120, with a 40 GiB free-space guard. No
captures are downloaded again and no existing sources are overwritten.
Core **24** has completed with identical protected arrays and a passing source
bed/reference handoff. Inspect this live handle and output before restarting
or creating another job for this interval. Its eventual completion receipt
will still explicitly report hydraulic and engine acceptance as false.

Full-route terrain export now rejects geographically disjoint source footprints
before allocating per-vertex coverage masks. Original global source indices,
overlap-owner tie order, two-metre vertex lattice and shared encoding remain
unchanged. The 378-source regression covers original owner identity, exact
footprint edges, nonfinite/empty queries and batches spanning the whole route.
Together with source harmonization, terrain, batch and bed-seam checks,
**25 tests pass**. This is an assembly scaling improvement, not a measured
runtime FPS improvement.

Separately, native corrected-friction solve **12666** reached 38,400/48,000
steps (1,920 simulated seconds, reported maximum depth 18.9443 m), still live
and unaccepted. Source-tail job **4166** completed batch 336-347 and began
348-359. The other task's Unreal crew review was live during this turn; no
engine build, DLL replacement, source interruption or message was attempted.

### October 7: full Colorado terrain assembly and exhaustive wet-cell coverage

The preceding literature pass did not resolve new Chilko coordinates. Live
source/cook processes were verified again; no equivalent failed research or
native solve was restarted. This turn added
`physics/scripts/assemble_colorado_full_terrain.py` to assemble all **378**
registered source cores, including the partial terminal core at
**453,334.02824855957 m**. It refuses gaps, duplicates, truncated selections,
changed capture/profile/grid identities and stale or failed source handoffs.
Existing hash-bound seam receipts are reused, not rerun unchanged. Export
retains the shared two-metre Landscape lattice and common height encoding.
It then visits every classified water cell owned by each core, in bounded
batches, to find terrain holes that a centreline or source-seam check misses.
Missing in-route terrain produces `rejected.json`, never playable acceptance.

Exercising the new check on the existing 24-core/28.8 km through-House terrain
first reported 34,841 missing cells, all at clamped station zero. Geographic
inspection proved they were upstream of the captured route endpoint, not
holes inside the descent. The corrected check clips only endpoint-clamped
cells outside the actual geographic start/end cross-sections; lateral cells
and later meanders behind those planes remain checked. The original raw
diagnostic is preserved at `tmp/colorado-through-house-wet-terrain-coverage-v1`.
The corrected V2 receipt verifies **2,513,029 in-route classified cells with
zero missing terrain cells**, separately reporting 58,615 upstream crop cells
outside the route. This is actual source/encoded-terrain coverage, not engine
collision, hydraulic, vegetation, rapid-location or FPS acceptance.

Full assembly is now queued in live exec **54350**, child Python **1624**,
wrapper **28184**, running
`tmp/assemble_colorado_full_terrain_when_ready_v1.py`. Job receipt directory:
`tmp/colorado-full-terrain-assembly-job-v2`. It waits for the already-running
middle harmonization (Python 17136, exec 8000) and downstream source recovery
(Python 35884, exec 4166), validating their live command identities. A transient
observation failure is not terminal; three confirmed absences without a
completion receipt fail without restarting anything. Once sources complete,
it writes `tmp/colorado-full-terrain-selection-v1.json` and assembles into
`tmp/colorado-full-continuous-terrain-v1`. Preserve 40 GiB disk headroom.
The initial waiting worker 63772 was stopped by this task before export to
correct endpoint ownership; its cancellation receipt is retained in job V1.
No other task's process was stopped, paused or messaged.

Also recorded: live exec **23848**, Python **24168**, is the guarded
`tmp/finish_colorado_twelve_friction_v2.py` integration worker, waiting for
corrected cook 12666's own terminal review (no duplicate review/cook). Its
receipts are under `tmp/colorado-twelve-friction-integration-v2`. It requires
unchanged construction gates, a full minute of engine inactivity and unchanged
dependencies before importing the distinct
`L_Colorado_ContinuousShoreTwelveFrictionV2` candidate. A saved map would still
require rendered descent, boat/foam/collision, menu and packaged >=20 FPS tests;
do not confuse its receipt with final acceptance.

**36 targeted tests pass** for full terrain selection/coverage, endpoint scope,
terrain sampling, source batching, bed seams, harmonization and friction units.
Main remains checked out. No normal launch path was changed in this turn;
no completed full-river environment, commit or push is claimed.

### October 7: takeout registration, Chilko literature and live cook correction

The full captured Colorado envelope is not the playable takeout. Added
`register_colorado_takeout.py` and a source-identity ledger at
`physics/data/real_world/colorado_river_grand_canyon_rowing/review/pearce_ferry_location_evidence_2026_10_07.json`.
The NPS 2011 orientation identifies the 2010 ramp above Pearce Ferry Rapid;
the RRFW June 2013 report places it on river left. These dated narratives
establish identity and order, not current operating rules or surveyed geometry.
OSM node 4684612927 v4 supplies the best mapped point found in this review:
36.1258863 N, 113.9821908 W. OSM attribution/ODbL remain separate from USGS
source rights. Captured XML and the complete source route are checksum-bound.

Actual registration receipt:
`tmp/colorado-pearce-ferry-location-v1/registration.json`.
The takeout projects to **452,069.449 m** on the geographic source polyline,
14.507 m left of it. The mapped rapid is **962.195 m downstream**; the capture
continues **1,264.579 m past the ramp**. The RiverBrain access point checked
in this review lies **1,664.085 m from the source route**, so it is not used as
the modern ramp. No claim is made about that point's historical identity.
All captured terrain is retained. This receipt is not a hydraulic-chart finish
station, accepted wet-bank approach, surveyed ramp, collision or playable map.
Those must be bound and tested when complete runtime coverage exists. Tests
reject wrong chart identity/metric stationing, endpoint clamping, distant
points and a takeout downstream of the rapid.

Chilko research recovered the public 18-page preview of Cecil Kuhne's 2025
*The White Mile Trial*. Complete printed pages ix and 3 were visually
inspected after PDF rendering; the preview text was read, not the full book.
It adds no coordinates or Green Mile/Miracle Canyon identity. Courtroom
opening claims are not surveyed distances, geometry or difficulty calibration.
Recorded as a qualified literature source, without adding an anchor or alias.
The earlier UC Davis Site 2 PDF was also successfully recovered: its upstream
ecological island sketch does not locate these rapids. Do not repeat the old
PDF-access failure or imply all report figures/full books were inspected.
**24 targeted Chilko-location and Colorado-takeout tests pass.**

Corrected-friction 12-core cook **12666** completed, but failed its unchanged
5% discharge gate: p95 relative error **9.2344%**, inlet 226.5348 and outlet
207.8232 cubic metres/second. Wet IoU **0.980187**, water-height p95 **0.190159 m**
and depth-settling p95 **0.011100 m** passed. The downstream nine cores fail
flow; the first three pass. Integration **23848** and rendered descent
**97600** correctly refused this result; no V2 map was imported or recorded.
Do not restart that unchanged pipeline.

New saved-frame storage check
`tmp/colorado-twelve-friction-storage-v1.json` measured **18.2136 m3/s** filling
over the final interval, consistent with the final **18.7116 m3/s** inlet-outlet
difference. Exact final-state continuation is now live in exec **31328**,
driver **18544** (wrapper 17548), solver **11596**, through
`tmp/continue_colorado_twelve_friction_v3.py`. It retains bed, boundaries,
friction, solver executable and acceptance gates, adding 4,800 simulated
seconds (96,000 fixed steps); initial progress reached 4,800 steps. Receipts:
`tmp/colorado-twelve-friction-continuation-job-v3`. This is not a fresh
geometry experiment, accepted field or FPS test. No integration worker is
queued for this continuation yet.

Final source batch 372-377 completed; tail receipt is
`tmp/colorado-continuous-full-source-tail-v2/completed.json`. Middle shore
harmonization **8000**, child **17136**, reached core 79 with protected wet
and measured arrays unchanged. Full-terrain assembler **54350**, child
**1624**, remains waiting for that producer. Another task's editor build
was live; no engine build, cook, DLL replacement, interruption or message
was initiated here. Main remains checked out. Changes in this update are
geographic evidence/tooling, not newly delivered playable scenery.

### October 7: Soap Creek profile wiring and additional Chilko research

The existing difficulty reporter already removes the old hands-off Class I
shortcut and the invalid Grand Canyon numeric-to-Roman conversion. Earlier
notes describing those as unfixed are superseded; no reporter change was
needed in this pass.

Added Soap Creek to the exact production profile allowlist and continuous
map source registration, using its v5 source chart and the existing shared
surface/froth/immersed-hull kernels. Eighteen authored sites approximate the
post-2015 guide description: right-of-centre approach, stronger centre/left
hydraulics and a lower wave train. Dimensions remain authored hypotheses,
not measured boulders, solved hydraulics or accepted difficulty. The source
ledger is `observed_rapids/soap_creek_profile_evidence_2026_10_07.json` under
the Colorado data directory. All 18 source centres are classified water;
constructed reference depths range 1.4695-2.0753 m. Three conservative support
rectangles contain dry cells, explicitly recorded with source-array hashes.
Do not call shoreline coverage passed before the production wet/depth gates
are exercised in-engine. No new rock collider was invented.

Native profile tests now cover the Soap tongue, roller, lower wave, pool
release and wet/depth gates. The real-source registration test now requires
four reaches and 86 sites instead of three and 68. These native changes have
NOT been rebuilt or run yet. The Python location/map-contract/takeout suite
passes 36 tests. Another task's editor was active during this work; no DLLs
were overwritten and no competing build was launched. Soap is not yet a
delivered normal-menu map or a packaged performance acceptance.

Further Chilko searches did not resolve Green Mile versus White Kilometer,
or Miracle versus Magic Canyon. Repeated operator narratives are not new
independent geographic control. The publisher's page for Tamar Glouberman's
2022 *Chasing Rivers* identifies another literature lead, but its chapters
were not accessible and are not claimed as read. Added that limitation to
the existing source ledger. No midpoint placement, invented exact boundary,
or automatic alias was introduced. The user's request remains research-led
placement, not permission to substitute guessed locations.

Exact-state Colorado continuation remains live in exec 31328, solver 11596;
latest emitted progress is 9,600/96,000 steps (480 additional simulated
seconds). It has not emitted terminal acceptance receipts. No duplicate cook
or acceptance-threshold change was made. Full-river integration, gameplay,
normal launch and packaged 20 FPS remain open.

### October 7: native rapid registration, geographic takeout and terminal terrain repair

Guarded full builds V4 and V5 succeeded; V5 completion is recorded in
`tmp/continuous-diagnostic-access-build-v5/completion.json`. Other tasks'
editors were allowed to finish without interruption or messages. The fresh
native report `tmp/colorado-soap-takeout-native-v1/index.json` records three
passes, zero failures and no skipped tests: RapidChallengeProfiles,
RapidRegistration and RapidSourceRegistration. Actual source registration
covered Badger (17 sites), Soap (18), House Rock (11) and Hance (40).
Maximum source-to-target centre error was 0.909458980 cm, with headings
preserved. Soap's evidence ledger now records this specific native proof;
rendered shoreline coverage, boat trials and difficulty remain pending.

The continuous map contract now requires source-identified Pearce Ferry
geography for a full Colorado run. It revalidates the original route,
OSM points and evidence, binds their hashes, and lets the production native
adapter resolve the finish station. It does not copy source-chainage or
extend a partial cooked interval. Legacy partial contracts remain supported.
Native helper tests reject the wrong bank, downstream-of-rapid finish,
unloaded charts and insufficient cooked coverage. Python tests also reject
source/request changes during registration.

Read-only native projection succeeded in
`tmp/colorado-pearce-ferry-native-projection-v1.json` (SHA256
`c0edad65f82cef5a3807ddfae1b998a32a4a01138b153d97279da05b51d7b636`).
The actual continuous chart resolves the takeout to station 449378.526204404 m,
left lateral 10.445442041 m; the downstream rapid to 450314.234794027 m.
Maximum world-coordinate round-trip error is 0.00002386412 m. These stations
belong to the receipt's exact target chart, not the original source arc.
No map was modified and no ramp/docking or full cooked coverage was accepted.

All 96 middle source cores completed with protected wet/measured arrays
unchanged. Full terrain assembly then exported 9869 common-lattice chunks
across all 378 cores (453334.028248560 m source route), with zero encoded
shared-edge difference. Its original terminal receipt correctly rejects
35161 missing classified cells in final core 377; preserve that rejection.
Diagnosis reproduced float32 endpoint identity loss: adding the large global
origin yielded 453334.03125 instead of 453334.02824855957 m, defeating the
existing geographic end-cap exclusion. The repair promotes station arithmetic
before addition and recognizes only exactly stored endpoint-clamped values;
the geographic half-plane is still required. Tests cover both rounding
directions, unchanged input arrays and continued rejection of a genuine gap
or a later bend beyond the same plane. No terrain/source data or tolerance was
altered. Fresh final-core checking finds 76452 in-route cells, zero missing,
and 78671 clamped cells beyond the route excluded.

The no-regeneration full coverage recheck completed successfully (exec 86227,
`tmp/review_colorado_existing_full_terrain_v2.py`). Its terminal receipt is
`tmp/colorado-full-terrain-coverage-review-v2/review.json`: all 378 cores,
37805809 in-route classified cells, zero missing terrain cells, and 137286
endpoint-clamped cells geographically outside the run excluded. All bound
source, seam and terrain files are unchanged. The original rejected capture
is preserved. This accepts geographic coverage only, not terrain-to-solver
height agreement, rendered shorelines, vegetation, boat navigation or FPS.
Expanded Python regression suite: 83 passed. Exact-state water continuation
31328 remains separate; latest observed progress 28800/96000 steps (1440
additional simulated seconds). No duplicate cook or changed acceptance gate.

Additional Chilko research inspected CanoeMap's public expedition overview,
but not its inaccessible interactive map. It supplies no Green Mile/Miracle
coordinates or boundaries and is recorded as a qualified secondary source,
not independent geographic control. Their identities/precise bounds remain
unresolved; no guessed placement, midpoint split or alias was introduced.
This update delivers native registration and geographic/coverage fixes, not
a newly accepted normal-menu full-river scene or packaged 20 FPS result.

### October 7: full-route hydraulic preparation and guarded playable handoff

Previous goal turn made progress: corrected terminal terrain coverage and
verified all 378 cores plus native rapid/takeout coordinates. Current work
extends that terrain into actual solver-input sections, without another cook.

`LandscapeTriangles` now keeps the hash of the manifest bytes it loaded and
provides `verify_unchanged()` for closing a reuse batch against every original
heightfield. The source-scenario builder can borrow that same loaded snapshot
only with its matching registered directory and unchanged manifest; emitted
receipts bind the loaded manifest, not a later replacement. The full batch
verifies all source and terrain identities again before its terminal receipt.
This avoids decoding 9869 terrain chunks for each of 378 source sections;
geographic samples, bed, resolution and construction gates are unchanged.
Sixty-six Colorado/Chilko builder, terrain, export and join tests pass,
including changed-manifest/heightfield rejection. Real cores 0-2 have
bit-identical bed arrays, all initial-state and reference arrays, and identical
coordinate-map hashes compared with the earlier through-House preparation.

Full-route preparation is live in exec **83066**, Python **29540** (wrapper
35096), `tmp/prepare_colorado_full_hydraulic_sources_v1.py`. Its fresh output
is `tmp/colorado-full-hydraulic-sources-v2`; cores 0-61 (through source station
74400 m) have prepared successfully with no rejected cores observed yet.
It checks every source identity, inferred Manning resistance, complete core
coverage, wet-strip geometry and dry domain edges. It records individual
refusals instead of filling/clipping missing water or moving geography. Do
not edit the protected builder/terrain/frame modules while this job is live.
V1 stopped before preparing any core because the initial driver assumed the
water directory was literally named `water`; that failure is preserved.
V2 identifies the capture from its matching width-manifest contents instead.
Both use a 40 GiB disk-headroom floor. Neither starts a native solver.

Existing continuation exec **31328**, solver **11596**, remains active. A
single guarded consumer now waits for its actual V3 terminal cook and review:
exec **21308**, Python **20380** (wrapper 32164),
`tmp/finish_colorado_twelve_friction_v3.py`. Job receipts are in
`tmp/colorado-twelve-friction-integration-v3`. It must refuse failed unchanged
construction gates; it never repeats the solve/review. If accepted, it exports
matched terrain/water, grounded decoration and native profile registration,
waits for a full minute of engine/build idleness, rechecks dependencies and
imports only the fresh `L_Colorado_ContinuousShoreTwelveFrictionV3` candidate.
Required V5 build is already successful. No DLL replacement, existing-map
overwrite or normal-menu promotion is authorized by this consumer.

Rendered production-raft descent is separately queued behind that import:
exec **79718**, Python **34296** (wrapper 34996),
`tmp/run_colorado_twelve_friction_descent_when_ready_v3.py`, receipts in
`tmp/colorado-twelve-friction-descent-job-v3`. It waits for the exact producer,
refuses an import failure, then uses normal oar inputs for station 200 to
14350 with fourteen recorded gates and no resets. The underlying current
domain ends at station 14642, so that finish is inside real field coverage.
No native descent has started yet; screenshots, shoreline, motion, performance
and normal-launch acceptance remain required. No extra cook/build or repeated
old V2 rejection was launched. Other tasks' changes and live editors remain
untouched. Main remains checked out; final commit/push awaits the full goal.

### October 7: repaired the shared chart at the 53.6-mile bend

This goal turn made progress: isolated and repaired a numerical coordinate
fold, then rebuilt the four affected/adjacent real source inputs without
changing captured water, bed, terrain or active cooks. This is construction
progress, not a newly accepted playable map or packaged FPS result.

Full-route source preparation exec **83066** remains live. Latest inspected
snapshot: 242 of 378 cores checked, 238 prepared, four rejected (71, 72, 92,
93). The original-frame batch is intentionally unchanged while running.
Its protected modules and terrain files must remain unchanged until its
terminal identity check. Existing A3 continuation exec **31328** remains
live at last observed progress 33600/96000 steps; its guarded V3 integration
and rendered-descent consumers have neither completed nor reported failure.
No new native cook, engine build or editor process was launched here.

`tmp/colorado-folded-sections-v1.json` identifies **the same 333 cells** in
the overlapping halos of cores 71/72, not two unrelated bends. The bad source
interval is 86222.015258-86288.836680 m (published profile river miles
53.595907-53.637857), with minimum wet metric -0.165065769. A 144 m lateral
offset crossed the local curvature radius of the old numerical chart.
These coordinates are not Unkar; do not label this bend using a nearest
catalog entry many kilometres away.

`refine_colorado_shared_hydraulic_frame.py` now creates a fresh, explicitly
registered local smoothing refinement. It reconstructs and bit-compares the
original full chart before writing, binds source/specification identities,
requires non-overlapping bounded refinements, and refuses output overwrite.
The original 60 m smoothing remains outside the taper. The checked recipe is
`physics/data/real_world/colorado_river_grand_canyon_rowing/review/continuous_chart_bend_refinement_2026_10_07.json`:
90 m smoothing over source interval 85200-87400 m with 600 m cosine tapers.
It is a **numerical coordinate choice**, not inferred physical bank movement.

Five isolated candidates (60, 75, 90, 120, 160 m smoothing) were evaluated in
`tmp/colorado-bend-chart-probe-v1/report.json`. The 75 m candidate still failed
the unchanged 0.1 minimum wet-metric gate. The 90 m candidate was the least
aggressive of the tested candidates that passed: minimum 0.240202623, no
folded wet cells, no wet lateral edges and no dry cross-sections in cores
70-73. Maximum numerical-axis displacement is 11.786909598 m; all world-space
source surfaces and masks remain untouched. The first 42046 full chart
points, through hydraulic station 84090 m, are bit-identical, including
normal, curvature and source station. Both the original frame and upstream
A3 solve remain unchanged.

Fresh chart: `tmp/colorado-shared-hydraulic-frame-bend-v2` (manifest SHA
`00a49fbcdd18e41a9d83ac8fc0a8b2174b5a3eb0fce773f980da476f826215b7`).
Its immutable receipt references the identical earlier temporary recipe;
the same recipe is now retained in the repository for reproduction. Actual
normal-builder inputs for cores 70-73 are in
`tmp/colorado-bend-hydraulic-repair-v2`; all four passed the existing builder
and Manning-friction checks against the unchanged encoded terrain, followed
by rehashing every source/heightfield. Terminal summary SHA:
`63f2e67d30f4df9c60a69a90defb63bb4c618fbdfb086668ca34ba2df60e160d`.
Thirty-eight targeted chart, scenario, terrain and join tests pass, including
overlap equality, unchanged upstream/source geometry, invalid/overlapping
refusal, source tampering, unreconstructable baseline and fresh-output guards.

Do **not** splice these four new inputs into downstream original-frame
inputs. Reparameterisation changes downstream stationing and the 2 m sample
phase; regenerate every affected input under one selected global chart once
the original-frame batch has finished and its other errors are reviewed.
The candidate still requires native coordinate-inverse checks, real cooked
water, physical-space continuity, boat motion, terrain collision and engine
views. The solver's absent curvilinear metric terms remain a limitation;
passing a positive Jacobian is not solved-hydraulics acceptance.

The remaining rejected cores 92/93 have genuinely incomplete width
observations at the original 250 m half-span. Read-only inspection of the
unchanged captured polygons in `tmp/colorado-truncated-transects-v1.json`
extended the **diagnostic** transects to 350 m, wholly within captured vector
bounds. Core 92 has 3 original truncated observations and core 93 has 9;
3 in each still touch the longer endpoints. They span published profile
river miles 69.53-69.78. The full geometry and whether these cuts intersect
another river limb still need investigation. No mask was clipped, width
limit raised, source geometry overwritten or missing region declared dry.
The initial diagnostic import lacked optional `pyshp`; this was resolved by
using installed Shapely directly, without installing packages or modifying
the production capture module. The completed diagnostic binds original
profile/vector hashes; no new network capture or native cook was needed.

### October 7: full input inventory and production asymmetric-domain repair

Previous turn: progress (first bend repair). This turn: progress (complete
source inventory, second bend repair, real production input rebuilds and a
stronger missing-channel coverage gate). Goal remains active; all-river
runtime, normal-menu and packaged performance acceptance are still open.

Exec **83066** is now terminal, exit 0: **370/378** original-frame cores
prepared; rejected 71,72,92,93,280,281,355,377. All original sources and 9869
terrain chunks passed the terminal identity audit. Summary:
`tmp/colorado-full-hydraulic-sources-v2/summary.json`, SHA
`1eee9fccdac3395ef207350db51ad893dfb6fcb2371adbe1aa50acb4e31a5586`.
The builder was not edited until the process exited and this audit succeeded.

At miles 69.53-69.55, longer cross-river cuts intersect a different river limb
roughly 484-523 m upstream on one side, while local classified water extends
beyond the old 250 m limit on the other. Simply increasing both sides is
not a valid repair. `tmp/colorado-remote-water-cuts-v1.json` binds the measured
source profile and original diagnostic. The asymmetric probe then exposed
an additional wet-grid fold in core 93 that the width refusal had hidden.

Fresh shared chart `tmp/colorado-shared-hydraulic-frame-bends-v3` adds 120 m
smoothing over source 111500-113000 m, with 600 m tapers, to the earlier
53.6-mile repair. Repository recipe:
`physics/data/real_world/colorado_river_grand_canyon_rowing/review/continuous_chart_bend_refinements_v2_2026_10_07.json`.
Chart manifest SHA `732aff913845a84122b4fc68d972d6c5674efbbd9b1c456e9a7a48079c133b98`.
The tested 75/90 m alternatives still folded; 120 m is the least aggressive
tested passing option. Maximum numerical-axis displacement is 32.462961 m;
the captured river, water mask and terrain did not move. Preserve the same
42046-point upstream prefix. Core 94 requires its width expanded to avoid
new edge clipping; do not use the original narrow width with the new chart.

Production `build_colorado_catalog_scenario.py` now accepts an explicit
`--reviewed-lateral-interval MIN MAX` only with a registered shared chart,
terrain and complete source core. Defaults and old symmetric-transect
refusals remain unchanged. The explicit route retains the 500 m total-width,
2 m lattice, full terrain/core, dry-edge, nonfolding, nonempty cross-section,
discharge and friction checks. It additionally uses
`review_colorado_hydraulic_domain.py` to verify **every classified 1 m
source-core water pixel centre** lies in the physical chart-strip footprint.
No distance buffer, source mask edit or off-chart-water-to-dry conversion is
allowed. A disconnected side channel outside otherwise dry strip edges is
an explicit rejection, covered by a regression test.

Actual normal-builder runs finished successfully in exec **36587**:
`tmp/colorado-bend-hydraulic-repair-v3`, cores 0,70-73,91-95. Domains 92/93
are [-320,180] m; 94 is [-160,160] m. The five 91-95 source cores contain
672986 classified 1 m water cells, **zero omitted**, with no folded wet cells,
wet edges or dry cross-sections. Core 93 minimum wet metric is 0.154766811.
Original core 0 bed, every initial/reference array and scenario JSON are
bit-identical; all original source and terrain hashes reverified. Summary
SHA `3c7f277fd8d83db5ca3de1f28c76b7529d1391b4cd9752dd1d14d9e12e5e54d6`.
Fifty targeted domain, frame, scenario, terrain, join and friction tests pass.
No new cook, DLL replacement, map import or production promotion occurred.

Next failures are concretely classified by
`tmp/colorado-remaining-domains-probe-v1.json` (SHA
`09a7038136013d6c3f07e5339d80726a2e116f909e3bc1100a937604389dc7d1`):

- Core 280 has genuine omitted source water in tested bounded domains;
  [-350,150] has dry edges but misses **3402** source-core water cells, so the
  new footprint gate correctly rejects this tempting incomplete fix.
- Core 281 independently passes [-350,150] geometry/coverage, but its final
  domain must be consistent with the still-unresolved core 280 handoff.
- Core 355 fits [-200,300] with complete coverage but exposes **72 folded wet
  cells**, minimum metric -0.037471007. It needs a registered chart repair,
  not a looser fold gate. Other tested bounds lack complete terrain/core.
- Core 377 has incomplete domain/source-end coverage under all five tested
  intervals. Do not clamp its required core, fill a terrain gap or call the
  full source route finished. The actual takeout and captured endpoint must
  remain distinguished when resolving this final construction window.

Do not mix old and new downstream charts. Rebuild affected inputs under the
selected final shared chart after all local geometry repairs. Existing A3
continuation exec **31328**, solver **11596**, remains live at last observed
43200/96000 steps; its V3 integration/descent consumers remain singular.
Other-task engine build observed earlier finished; no process was stopped or
messaged. Main remains checked out; final commit/push is still pending the
full goal, not these supporting construction checks.

### October 7: remaining bend repairs validated; terminal support isolated

The source-preparation job above is terminal, so its protected builder was
then safely repaired: `covered_source_slice` selects the single contiguous
valid component bracketing the entire required core. A disconnected valid
island beyond a missing exterior halo no longer rejects a complete core.
Internal gaps and either missing core endpoint still reject. The new
regression exercises both exterior islands and these core failures; this is
not permission to bridge missing terrain or shorten a river.

Core 355's actual folded source interval was 426343.837118–426388.565239 m.
The least tested passing local smoothing is 75 m, plateau 426100–426600 m
with a 600 m taper. Fresh chart V4 and real builder runs for 354–356 passed
in `tmp/colorado-bend-hydraulic-repair-v4` (terminal exec 23095); summary
SHA `85c971a64924cbd96ffae788cb437ee4b4dd73555affb1edae4ab0af0a27c8de`.
All three cores' 592373 classified source water cells were covered in the
independent physical-footprint probe. V3 and V4's 211158 coordinate points
before source station 425000 m were bit-identical.

Core 280's off-centre water was retained, not reclassified as a dry pond.
Its newly exposed fold lies at source 336669.264994–336721.983657 m. The
75/90/120 m alternatives still omitted classified water or touched the wet
domain edge; even the 120 m option's two missing cells were rejected. A
160 m local smoothing, plateau 336400–337000 m with a 600 m taper, passes
with domains 280 [-150,350] m and 281 [-350,150] m. The three-core 279–281
probe covers 292845 classified source cells, zero omitted. Maximum chart
axis displacement is 37.590575 m; captured terrain/water/geography did not
move. This changes the numerical coordinates only, not rapid positions.

The complete four-patch specification is
`physics/data/real_world/colorado_river_grand_canyon_rowing/review/continuous_chart_bend_refinements_v4_2026_10_07.json`.
It generated fresh shared chart `tmp/colorado-shared-hydraulic-frame-bends-v5`
(terminal exec 5871), manifest SHA
`66ccf1f288bc449be15a9be680d3858e383286e7711a9df01811e849e783f42f`.
The source profile and all upstream arrays before source 335000 m were
checked unchanged against V4. V5 real production builder runs for
279,280,281,354,355,356 all passed (terminal exec 77340), with source and
all terrain heightfield hashes verified after completion. Receipt:
`tmp/colorado-bend-hydraulic-repair-v5/summary.json`, SHA
`3b0c9683ed492efcbe63f62b5fbcd69b59ea6f98c75bdb7cc90252e5f9eda2a0`.
Core 280's minimum wet metric is 0.338570952; core 355's is 0.180314950
after V5's downstream lattice phase change. No threshold was reduced.
Fifty-eight targeted scenario, domain, refinement, shared-frame, terrain,
join and friction regressions passed together after these changes.

Terminal core 377 is now diagnosed more precisely by the completed
`tmp/colorado-terminal-support-v1.json` (exec 49700), SHA
`55ea7ec01b9e8c37ff7f8e0909296e39bdd4607de596bf438d4176ac6b52f11c`.
V5 stops at source 453332.0430068616 m, while the actual captured end is
453334.02824855957 m, EPSG:6404 [26954.20589,571360.5999]. The endpoint
is 2.764949 m from the last smoothed chart point. Existing source and
collision terrain support the exact endpoint and every required section
in tested [-200,200] and [-150,150] domains. Wider bounds can introduce
genuine interior dry-land coverage gaps; narrowing to [-100,100] clips
water. A probe-only appended endpoint is NOT an accepted chart repair:
its metric, normal continuity, physical endpoint footprint and runtime
boundary semantics still need validation. Also use the original cumulative
chainage exactly: a plain sum differs by 1.6e-9 m and must not silently
redefine the core endpoint. Preserve strict complete-core bracketing.

Next: implement a source-anchored final chart section with exact endpoint
and tested boundary semantics, including the already identified geographic
end-plane ownership of station-clamped raster cells. Do not extrapolate
terrain, drop water, shorten the run or accept a copied terminal curvature.
Then rebuild all affected windows under the final common chart and check
joins between the asymmetric domains before cooking them. Do not splice
V1/V3/V4/V5 downstream inputs simply because individual sections passed.
These receipts certify input construction only, not physical currents,
boat passage, normal-menu integration or 20 FPS.

The separate A3 native continuation remains live in exec 31328; last output
48000/96000 steps at additional simulation time 2400 s. Its singular guarded
import/descent consumers are still waiting, with no terminal failure or
completion receipt. Another task's engine build PID 13500 was observed;
no process was stopped/messaged and no DLL was replaced. The latest Chilko
exact-name and map searches supplied no new geographic boundary control;
the public SierraRios overview again distinguishes its overview from the
annotated topo maps supplied separately to trip participants. No new
Green Mile/Miracle Canyon coordinates or aliases were invented.

### October 7: both source endpoints repaired; full-channel initialization

Implemented `anchor_colorado_terminal_frame.py` and regressions. The terminal
chart now reaches exactly source 453334.02824855957 m and the captured end
cross-section, with a 200 m cubic numerical-coordinate correction. Normals
and curvature are recalculated; no copied terminal curvature, source-point
extension or terrain filling. Terminal local scale is 0.998633–1.005590;
maximum correction 1.922555 m. The first 225094 points remain bit-identical
to V5. Loader validation independently binds the endpoint and plane to the
hash-verified original source profile.

Fresh actual builder cores 376/377 passed in
`tmp/colorado-terminal-hydraulic-repair-v6` (exec 14287 terminal); summary
SHA `a7ecc86627b3cdc3f9e6d8f18d035fda5d463d42dc4007058afaaecc61830cb1`.
Core 377 covers all 76452 in-route classified water cells, zero omitted,
minimum wet metric 0.391070441. Its 78671 excluded pixels are exactly
station-clamped beyond the captured geographic end plane, not omitted
in-route water. Regression tests retain earlier meanders beyond that plane
and float32-rounded endpoint cells inside it. Production join 376–377 also
passed, source core 451200–453334.02824855957 m, without an internal boundary:
`tmp/colorado-repaired-join-review-v1/terminal`. No solver was started.

The 279–281 production join initially refused an overlap velocity difference
of 0.089408589 m/s between 280/281; bed, depth, stage and transverse velocity
were identical. The different halo side-channel extents had normalized
their initial discharge independently. Added explicit
`--rebuild-initial-conveyance` to `join_colorado_continuous_scenarios.py`:
only hash-bound, explicitly unsolved/unaccepted source-builder packages are
eligible, and every original depth/u/v must match its captured-stage,
zero-transverse, conveyance initialization before reconstructing Q over the
complete joined section. Strict overlap checks remain the default. Geometry,
depth, classification, source coverage and discharge gates remain; cooked or
modified states are rejected, never averaged. Fresh real branch join passed
in `tmp/colorado-repaired-branch-join-v2` (exec 55522 terminal), report SHA
`d80fd21bba1a055827a21c4fe0be390dc3c0bab0cd830a2fb14a24b03ed769a0`.
Its 700 m rectangular union has only verified dry uncovered padding; each
individual reviewed source domain retains its 500 m bound. Fresh hydraulic
solution and physical-space validation are still required.

A full-footprint check also found 444 in-route water cells omitted by the
old smoothed inlet. Added the corresponding source-anchored initial 200 m
correction; all coordinate arrays from point 103 onward are unchanged from
V6. The corrected inlet covers all 186521 in-route classified cells, zero
omitted; no source water was deleted. Its local scale is 0.993736–1.020963,
maximum correction 4.659515 m. Intermediate V7 and final V8 coordinate arrays
are identical; V8 clarifies that the inherited bend-only prefix identity
receipt describes the intermediate stage, before the inlet correction.
Final chart: `tmp/colorado-shared-hydraulic-frame-endpoints-v8`, manifest SHA
`a449d4215062c922f68335f35acf408c07299efa6d54834bc297775a78af983a`.
Seventy targeted regression tests passed. Compact input coordinate-map JSON
removes replicated whitespace, not coordinates or standalone file ownership.

Full physical source-water coverage is now mandatory for EVERY continuous
source core, not just explicitly widened domains. A single new full-route
preparation is live: exec **85340**, driver **10376**, wrapper **21776**,
`tmp/prepare_colorado_full_hydraulic_sources_v3.py`, output
`tmp/colorado-full-hydraulic-sources-v3`. First 15 cores (0–14) passed at the
last observed poll. It rebuilds all 378 inputs on V8, uses the reviewed
92/93/94/280/281/355/377 domains, preserves a 40 GiB reserve and checks all
source/terrain hashes at completion. Do not edit its protected builder,
shared-frame loader, domain reviewer, endpoint-anchor, terrain exporter or
friction module until it terminates. Do not duplicate this preparation.
The existing native continuation (exec 31328, solver 11596) independently
reached 52800/96000 steps; its guarded import/descent consumers remain live.
All current repairs are source/input construction, not engine acceptance,
normal-menu promotion or the final 20 FPS result. No commit/push yet.

### October 7: complete source coverage and Georgie native registration

Full V8 preparation (exec 85340) terminated: 376/378 passed. The mandatory
physical-footprint check found eight omitted classified cells in core 113
and 31 in core 173. Kept both failures and source masks. Actual source
coordinates justified expanding only the right-side domain: 113 from
[-108,108] to [-132,108] m; 173 from [-100,100] to [-274,100] m. The initial
173 trial at [-250,100] still omitted five cells and was refused. Final
inputs pass full source-water coverage, wet-edge and fold checks, with no
terrain/chart edits. See `continuous_hydraulic_domain_repairs_2026_10_07.json`.

Real production neighbour joins 112-114 and 172-174 passed using verified
un-cooked full-cross-section initialization, without halo cropping or
changing the strict physical state/bed/coverage checks. Removed a full-run
assembly bottleneck: classification now samples each query only from its
assigned source instead of allocating the entire river grid per source.
Regression tests prove identical values and reject missing ownership and
unclassified cells. This is construction efficiency, not a measured FPS gain.

The complete same-frame prepared selection is now
`tmp/colorado-repaired-source-joins-v5/selection.json`, SHA
`5cff9619ff62d08dc1c6372cb64f5063d3f6ebcbb513080c5f5ba07fbc86741a`.
All 378 inputs were hash-verified; their source cores cover 0 through
453334.02824855957 m contiguously. All 37,805,809 classified source-core
water cells are covered, zero omitted. This is NOT a full-route joined
solution, playable continuous descent or map promotion. Use this exact
selection (including the two repaired domains) for subsequent assembly;
do not repeat full source preparation or reuse the rejected core domains.

Added Georgie's authored water profile using the existing shared
surface/froth/immersed-hull kernels and its original v3 geographic chart.
Sources distinguish Georgie/24 Mile from the separate 24-and-a-half-mile
rapid and describe its centre-right tongue, wave/left lateral, right seam,
far-right hole and later pin-rock decision. No pin-rock geometry is invented.
An initially proposed hydraulic centre at 812,-18 was source-dry and rejected;
826,-18 lies within the captured ledge drop and passes the centre check.
All eight centres are classified water; footprint shoreline checks and
actual navigation remain pending. Dimensions are authored, not measured.

Full build and three native tests passed in
`tmp/colorado-georgie-native-v2/tests/index.json`, SHA
`d524295a20d4b8baa4a76df07bd4d07a1f0273906d275dca5091cada2f569503`.
Georgie's eight sites register into the actual final V8 chart with maximum
centre error 0.001283949 cm. The continuous import now binds five profiles
(Badger, House Rock, Soap, Georgie, Hance), 94 sites, through verified charts.
64 focused Python regressions passed. Native wet/depth/pool/kinematic
checks use controlled samples; NullRHI does not certify rendered water,
full-hull navigation, pin collision, catalog difficulty or packaged FPS.
No normal-menu change or commit/push is claimed.

Existing A3 14.4-km continuation remains separate on its original chart:
exec 31328, solver 11596, last observed 62400/96000 additional steps.
Its single guarded import and rendered-descent consumers remain waiting;
no duplicate cook, process interruption or solver threshold change.
Chilko's Green Mile/Miracle Canyon geographic identity remains unresolved
in the existing research ledger; no inferred boundaries or external contact
were authorized by this source/preparation work.

### October 7: full-width Colorado terrain padding, additive only

The first actual all-378 input join terminated after 112.297 seconds with
`Missing interior rendered terrain` (preserved in
`tmp/colorado-full-route-join-job-v1/failure.json`). It did not start a native
solver or create joined outputs. The subsequent complete 79,044,147-query
review identified 1,084,757 missing rendered-terrain samples in 404 common
Landscape tiles. All missing samples are outside the prepared source input
domains and unclassified as water in their owning source mask; none is an
omitted classified water sample. This does not make arbitrary height fill safe.
See `tmp/colorado-full-join-terrain-review-v1/review.json`.

Only nine complete required tile extents fit the existing captured DEM windows.
Added explicit bounded capture margins to the existing USGS acquisition path
(400 m default unchanged); grouped the remaining 395 tiles into 252 small
outer-terrain windows. Original captures, surveyed bed and inferred shore
construction were not changed. Capture v1 completed 147 windows before a
connection reset; v2 reused them and reached 156 before outer0156's fine
export failed with HTTP 502. V3 skipped that known failure and completed the
other 251 windows in total. Both failed passes and complete partial stages
remain intact; no repeated full acquisition or fabricated fine-source absence.

For outer0156's two tiles, a distinct valid 10 m export succeeded in
`tmp/colorado-outer-terrain-coarse0156-v1`. Its resolution stays 10 m, and the
fine-source availability remains explicitly unknown. This is regional outer
terrain, never a bathymetry replacement or measured boulder geometry.

New `extend_colorado_continuous_terrain.py` adds complete source-backed tiles
on the original encoded lattice. It copies every original tile unchanged,
retains construction-grid samples wherever they exist, interpolates the
captured profile GEOID18 only for new regional DEM samples, and rejects low
outer terrain rather than lifting it to stage. All encoded edges and source
hashes must pass. Partial source availability has an explicit rejected-tile
receipt, not a relaxed full-route pass. The join now accepts only a verified
additive superset binding the original manifest, exact original tile metadata
and hashes, frame and source list. Its water/state/coverage gates are unchanged.

95 targeted Python tests passed, including an actual GeoTIFF-to-Landscape
extension fixture, byte-identical original tiles, common edges, source
preservation, low/nodata rejection, exact blocked query sampling and strict
partial-capture refusal. These are construction tests, not engine FPS.

At this checkpoint partial export exec 62588 / driver 24152 had written 254
additional tiles to `tmp/colorado-full-continuous-terrain-padding-v1` and was
validating its manifest; wait for its terminal receipt. Guarded continuation
exec 37125 / driver 2104, `tmp/finish_colorado_outer_terrain_v2.py`, waits for
that exact pass and completed captures. It consolidates the verified 252
captures in v4, then runs a fresh full additive export to
`tmp/colorado-full-continuous-terrain-padding-v2`, checks all 79 million
native-grid terrain queries, and only then attempts the all-378 input join
at `tmp/colorado-full-route-joined-inputs-v2` with 12 GiB available commitment
and 40 GiB disk headroom. It refuses partial terrain/changed sources and never
starts a native solver. Do not duplicate these jobs or edit their protected
exporter/join/build dependencies before termination. Check
`tmp/colorado-outer-terrain-finish-job-v2` first on continuation.

The independent A3 14.4-km native continuation remains live (exec 31328,
solver 11596), last observed 76800/96000 additional steps; its existing
guarded engine import/descent remain queued. No engine build/cook duplication,
normal-menu promotion, full-river validation, commit or push is claimed here.

Full-domain cook resource guard: `Frame` currently owns six double state
arrays plus four double derived arrays, and `raftsim_water_solver.cpp`
retains every saved frame before writing output. For the 79,044,147-cell
full strip, those ten arrays alone cost 5.889 GiB/frame, or 123.674 GiB for
21 frames, before wet masks, solver state and scratch space. Do not launch
that full cook on this 32-GB host or infer that input-join success permits it.
A bounded output/validation implementation must preserve all numerical
validation semantics and continuation data; reducing checks or silently
decimating the geographic grid is not a resource repair. Current A3 remains
untouched. The guarded job above intentionally stops at joined inputs.

Terminal checkpoint: partial export exec 62588 completed its deliberately
partial scope: **254 new tiles**, **9,869 original tiles byte-identical**, all
encoded shared edges validated. Its 150 rejections are exclusively pending
captures in that immutable snapshot, not low/missing DEM failures. Receipt
SHA `d906bd4c1a8206f252494e95682c9ea435018c46d6cfcf79e01b4827feaeeb69`.
V3 capture also terminated; the guarded job consolidated all **252 verified
windows** (including the explicitly coarse outer0156) into v4 and is advancing
the full extension. No full-route join or engine result is yet recorded here.
Compact durable receipt: `continuous_terrain_padding_2026_10_07.json`.

### October 7: complete terrain coverage and tested streaming output

Full extension job exec 37125 terminated after successfully adding all 404
required tiles, preserving all 9,869 original tile bytes and validating shared
encoded edges. Manifest SHA
`04b9e808b8f0da4cd3484ab05137758c4b91f4214fa90313e0981d92e4dfdf87`.
The actual 79,044,147-point native-grid terrain check has **zero missing points**.
Its subsequent full-input join was deferred before starting by the unchanged
12-GiB available-commit / 40-GiB disk guard. A following host check reported
5,493,104 KiB available commitment and 74,732,806,144 free disk bytes: memory,
not source coverage, currently prevents that join. Preserve its `failure.json`;
do not rerun the entire capture/export/coverage job or lower the guard. Reuse
the verified v2 extension for a later resource-safe join. No native full-domain
cook started. The compact terrain receipt now records the completed check.

An isolated C++ build in `tmp/colorado-stream-output-build-v1` adds opt-in
`--stream-output --disable-fixture-calibrations`: write each borrowed saved
state as lossless gzip CSV, accumulate exactly the existing saved-frame
validation, and publish the completed manifest only after successful close.
The buffered default and history-based fixture diagnostics remain intact.
It changes no integrator, boundary, state sample, grid or validation threshold.
The running A3 binary and shared Unreal DLLs were not replaced.

All seven native CTests passed (streaming parity/failure guards, Cartesian
domain default/one/eight lanes, shoreline, lake-at-rest and transcritical bump).
Twenty-one Python tests passed, with no skips: actual solver CLI buffered /
streamed equality at zero, five and six steps, including terminal non-divisible
capture and progress mode; all CSV values, probes, cross sections, manifest
configuration and validation agree. Reader/continuation tests refuse corrupt,
truncated, nonfinite, negative, unordered, unregistered and mixed-format data.
Colorado review/continuation now accept only validated native manifest paths
for either original CSV or declared streamed gzip. Parsing scratch is bounded
to 16,384 cells, but every numeric field is still retained and validated.

Tested binary SHA
`b395879709047647fb48b1a4725aee9ca5c54ca94fd73b5f5f0036f315acde4a`.
Durable test summary: `native_stream_output_2026_10_07.json` in the Colorado
review directory. This solves retained output-history growth, **not** the
remaining total solver scratch / full multi-frame review memory budget.
Do not launch the full cook until that budget and disk cost are demonstrated.
No playable full-river promotion, 20-FPS acceptance, commit or push is claimed.
The A3 continuation and its existing guarded engine consumers remain separate;
check them before starting any shared engine operation. Another task ran a
crew GearReview this turn; it was not interrupted or messaged.

### October 7: bounded input assembly, verified against real sections

The prior goal turn made progress (completed terrain and tested output repair).
This turn reduces input-join memory without changing the geographic grid or
source states. `join_colorado_continuous_scenarios.py` now retains source
metadata, loading one package at a time. The initial velocity calculation
reuses pointwise allocations while keeping the original full-shape reduction;
a trial column-block reduction failed exact parity by up to 4.2e-17 and was
replaced, not accepted through relaxed comparisons. NPZ output writes one
derived array at a time, retaining every original field and row-major layout.
All source file hashes are checked again before publication. No numerical,
coverage, terrain, discharge or resource threshold was reduced.

43 focused tests passed. Actual old-versus-new joins for repaired cores 0113
and 0173 also passed, not just synthetic fixtures. All state/reference arrays,
bed, complete coordinate map and scenario JSON are exact, and the old/new
build-report hashes themselves match. Process peak commit was 1,797,419,008
bytes across these two checks; this is **not** a full-domain peak-memory proof.
Receipt: `tmp/colorado-bounded-join-validation-v1/completion.json`, SHA
`2254254d08b9cae7811cb3ad723ac8e1e998474cf5072d3ca7f3cab428accef0`.
Durable summary: `bounded_input_join_2026_10_07.json` in the Colorado review
directory. Validation exec 98158 is terminal success.

One guarded full-route join is live: exec **93967**, driver **28136** (wrapper
35896), script `tmp/join_colorado_full_when_memory_ready_v3.py`, job
`tmp/colorado-full-route-join-job-v3`, fresh output
`tmp/colorado-full-route-joined-inputs-v3`. It waits for the exact actual-source
parity receipt, 60 seconds without UnrealEditor, 12 GiB available commitment
and 40 GiB free disk, then joins the 378 verified sources using the already
complete v2 terrain. It never rebuilds captures/terrain or starts a solver.
After two hours without the guard it records `deferred.json`; do not treat a
poll timeout as termination. Check its live process and receipts before any
retry. While live, do not edit its hash-protected join, terrain exporter,
extension, source builder or friction modules.

A3 remains live in exec 31328 / solver 11596, now observed at **86,400/96,000**
additional steps, simulation time 4,320 s, maximum depth 19.0009 m. This is
progress, not a convergence pass. Existing guarded import/descent consumers
remain unchanged. No full-river engine acceptance, commit or push this turn.

### October 7: disk-backed native review, exact real-cook parity

The previous goal turn was progress: bounded input assembly passed synthetic
and actual-source parity and one guarded full join was launched. This turn
verified that exec 93967 / driver 28136 remains live and waiting; A3 solver
11596 remains live, and another task is running crew StrokeTuning in Unreal.
No task was interrupted, messaged or duplicated, and the join's protected
modules were not edited.

`NativeFrameStore` now scopes lossless disk-backed native frame tables in a
fresh private scratch directory. Colorado construction review uses it for
the first and final two frames, removing those three full numeric tables
from committed RAM. Before every scratch allocation the forty-GiB free-disk
reserve is checked. Windows mappings are explicitly closed before private
scratch cleanup, including parse failure. Sources are never changed. All
fields are retained; all nonfinite, ordering and depth gates remain enforced.

Native frame validation no longer allocates whole-domain row/column index
grids or comparison temporaries. Bounded row blocks check every coordinate,
state value, wet bit, bed relation and initial-state value with the original
tolerances. Initial NPZ fields load one at a time. Native frame hashes are
captured before parsing and rechecked before publishing the review.

25 targeted tests passed with no skips, including actual streamed CLI parity,
disk-backed value equality, scratch cleanup, pre-allocation disk refusal and
failures at validation-block boundaries. Actual 1,274-by-167 Colorado cook
review was then executed with in-memory and mapped readers (existing saved
flow only, no time stepping). Entire JSON reports match exactly, SHA
`10723b3721b512b83a68f2d881993ca2cfccf41e43b6e253b51c7f1e7ba6d41e`.
Its existing failing discharge and per-core checks remain failed: this is
review-storage parity, not a new hydraulic pass. Validation exec 95093 is
terminal success. Receipt `tmp/colorado-mapped-review-validation-v1/completion.json`
SHA `0bdc6cb539e4504877a476d0ab6b6812b1186d91622ce8301250b912481fa9fe`.
Durable summary: `mapped_frame_review_2026_10_07.json` in Colorado's review
directory. No normal-map promotion, commit or push.

Next resource work must cover the full pipeline, not assume this is sufficient:
three full 15-field disk-backed frames need about 26.5 GiB plus the forty-GiB
free-disk reserve. `solver_face_discharge.py` still returns full native face
arrays through JSON, and continuous runtime export still builds full query /
presentation arrays. Full native live/RK scratch is also unproven. Keep the
no-full-cook guard until these costs are verified. Check the existing join
and A3 handles before launching related work; do not rerun terrain acquisition.

### October 7: compact exact discharge and corrected pixel-edge classification

Previous turn was progress (disk-backed review and actual-cook parity). This
turn built **only isolated native tools** in `tmp/colorado-compact-flux-build-v1`.
New `--inspect-face-discharge` sums production reconstructed x-face fluxes in
ascending row order and multiplies by dy after summation, with no stepping.
It uses three primitive scratch arrays and no full diagnostic face-grid arrays.
Python receives nx+1 values instead of both river-sized face arrays as JSON.
The helper detects support through `--help`, retains legacy small-grid support,
and refuses the old JSON path above two million cells. Scratch NPZ fields are
written one at a time, extra native fields preserved, redundant initial-state
copy omitted, and forty-GiB disk reserve checked. Colorado review uses its own
output volume for scratch. Running A3 and engine DLLs were not replaced.

Seven native CTests and 30 Python tests passed, no skips. Exact face sums were
checked for HLL/Rusanov/Roe on three fixtures; inspection preserves time and
every state field. Old/new integration produced byte-identical outputs on the
wet/dry control. The actual 1,274-by-167 Colorado saved cook also gives exact
agreement for all 1,275 station faces between old full, new full, new compact
and automatic paths. Complete review reports match except diagnostic binary
identity, including the original failed discharge/core checks. Native binary
SHA `a1ae0d1409b98a9dc6ea070d90a53ac9f8dc5e23a8d58492e3c5609310b4e28e`.
Actual receipt `tmp/colorado-compact-discharge-validation-v1/completion.json`,
SHA `c93eed6b6612cb8be81e039f397e44aeaebe3d7c4670a5e1d264a4898ad6753b`.
Durable summary: `compact_face_discharge_2026_10_07.json`. Build exec 89520 and
actual validation exec 68630 are terminal success. Full native live/stage
memory and continuous runtime export's full-query arrays remain unproven.

The guarded full join **v3 did start**, with 15,479,402,496 available commit
bytes, but terminated with `Unclassified terrain padding`; no joined output
or native cook was published. Exec 93967 / driver 28136 are terminal, not
waiting. Targeted read-only diagnosis reproduced ten failures after 20,423,988
checked points: source tile0096, rows 1346.034–1346.405 in a 1,347-row mask.
Every point is inside the captured raster's outermost half-pixel. Terrain
ownership accepted the full cell-centred pixel footprint, while classification
`mode=constant` incorrectly treated beyond-centre coordinates as missing.

The sampler now checks the full captured footprint first, then reads its
existing edge pixel for the outer half-cell. Outside-footprint queries and
nonfinite values are still refused; no source pixels, water geometry or
heights are edited. All ten actual points now return their existing non-water
classification, not an invented fill or surveyed-dry claim. 45 targeted tests
passed, including every outer edge/corner and just-outside refusal.
First-failure receipt `tmp/colorado-padding-classification-review-v1/first-invalid.json`
SHA `c679478b9b8ab5fefdfc688a251cf2077418f0b05133d5f7cc0a49c5f4a70c5c`.
Diagnosis exec 40259 is terminal success.

A complete **79,044,147-point classification audit** is now live: exec 43897,
driver 24556 (wrapper 19384), script `tmp/validate_colorado_padding_classification_v2.py`,
job `tmp/colorado-padding-classification-review-v2`. It also counts every
classified-water query not covered by any prepared native input. This must
be zero; do not assume an edge fix proves full water coverage.
Exactly one new full join waits on that pass: exec 68698, driver 36168
(wrapper 22236), script `tmp/join_colorado_after_classification_v4.py`, job
`tmp/colorado-full-route-join-job-v4`, fresh output
`tmp/colorado-full-route-joined-inputs-v4`. Unchanged guards: 12 GiB available
commit, 40 GiB disk, 60 seconds engine idle; two-hour deferral. It never starts
a native cook. Both jobs hash-bind the join implementation; do not edit their
protected modules or start another join while live. The compact classification
receipt records these handles. A3 exec 31328 / solver 11596 is still live,
last observed **91,200/96,000** additional steps, t=4,560 s, max depth19.0045m.
No final-river completion, playable promotion, commit or push is claimed.

### October 7: bounded runtime export, terminal padding fold, and A3 completion

Previous turn made progress; this turn also made concrete source changes and
ran new completed-data checks. Continuous runtime export now verifies exact
geographic terrain/bed, centimetre float32 precision and every wet cross-section
in bounded station blocks. NPY rows and station-major support components are
streamed with the original arithmetic and byte layout. Colorado's checked cook
accepts a scoped mapped frame loader and reads the bed through a read-only map.
The output disk estimate includes both flow and copied terrain plus forty GiB
reserve. Chilko shares the bounded final serializer/geometry check, but its
upstream reference validation is not yet fully memory-bounded. No gate changed.

57 tests / 121 subtests passed with no skips. On the actual 1,274-by-167 saved
Colorado frame, one-row and normal-size blocks give byte-identical five NPY
files and support binary versus the prior algorithm. Sources were unchanged
and mapped scratch was removed. Receipt
`tmp/colorado-runtime-streaming-validation-v1/completion.json`, SHA
`91b1a3ecca41c05069ddf1d9720249d31a8c455bd42e12d8898c529c6efa6f7c`.
That old cook still fails construction checks; serialization parity does not
promote it. Durable summary: `runtime_streaming_2026_10_07.json`.

The full classification audit **finished**: all 79,044,147 samples are finite;
39 outer-half-pixel reads were recovered, all already non-water. However,
1,001 classified-water samples fall outside prepared input rectangles.
Accordingly full join v4 **terminated before joining**; exec 68698 / driver
36168 and audit exec 43897 / driver 24556 are no longer live. Do not repeat
either unchanged and do not wait for them as pending jobs.

A targeted terminal check (exec 3720, complete) accounts for every one of the
1,001 samples: source owner377, hydraulic stations450166–450228m,
lateral−324…−210m. Metric ratio reaches−2.342; 427 are nonpositive. Every
coordinate lies within the existing terminal ±200m triangle footprint, with
nearest-axis stations449828–449930m. Thus the widened rectangular padding
folds back onto water already represented upstream, rather than exposing new
missing geographic coverage. Do not simply widen tile0377, mask the samples
dry, edit terrain or relax the gate. Repair the terminal chart/domain and
revalidate. Exact diagnostic receipt
`tmp/colorado-terminal-padding-diagnosis-v1/diagnosis.json`, SHA
`7dbb47411dff975bf4525dab5d1d176455ae016ab25f97060e96deb4e0e8c86a`;
durable summary `terminal_padding_fold_2026_10_07.json`.

A3 exec31328 / solver11596 **completed**, not still running. Native validation
passed, but construction p95 discharge error0.05014816247 fails the unchanged
0.05 limit. Only core13200–14400m remains failed (discharge0.06075068214,
depth change p95 .024986m). Review SHA
`403e1b276c104cb49c180cdf09415cd02b95e7691bf7b8dcfbce692f4d803acb`.
The v3 import guard and descent guard both terminated with preserved failure
receipts: **no runtime, map or descent was created**. Their old handles21308
and79718 must not be treated as live.

New saved-frame storage analysis, `tmp/colorado-twelve-friction-storage-v2.json`
SHA `c2bf8c6c23af4a2c163bd55770d32e97d2bbb03f45599898ae9abf472b20864e`,
shows the last interval still filling at12.271994m³/s versus the final
12.614523m³/s inlet–outlet deficit. This supports further exact-state
continuation, not another reset or threshold change.

Exactly one bounded A4 driver is now live: **exec70425, driver3192 / wrapper33328**,
script `tmp/continue_colorado_twelve_friction_v4.py`, job
`tmp/colorado-twelve-friction-continuation-job-v4`. It waits for sixty seconds
with no engine/solver and ≥12GiB available commitment / ≥40GiB free disk,
deferring after thirty minutes. Then it prepares an unchanged A3 final-state
restart and advances2400s (total9600s), 48000 steps, interval4800, OMP2,
using the isolated verified compact/streaming binary SHA
`a1ae0d1409b98a9dc6ea070d90a53ac9f8dc5e23a8d58492e3c5609310b4e28e`.
No loaded DLL replacement or engine interruption. Output uses lossless streamed
frames. Check `native-launch.json` for its actual solver PID before any cook.
It hash-protects continuation/review/frame-reader/friction modules; don't edit
them while live. No A4 engine import/descent guard has been launched yet.
This is the older 14.4km construction chart, **not** the final full-river V8.

Next: inspect A4 without duplicating it; repair the terminal full-grid fold;
prove complete native live/RK and downstream runtime budgets before a full cook.
Normal-map validation, vegetation, continuous descents and packaged20FPS remain
required. Main's dirty user/other-task changes are preserved; no commit/push yet.

### October 7: repaired terminal chart and exact reuse of 376 source packages

Previous turn made progress. This turn fixed the terminal numerical-chart
defect rather than reclassifying duplicated water as dry. A read-only local
candidate probe tested eight bounded smoothing choices against actual captured
classification. The smallest successful candidate (1200m window,90m smoothing)
had zero classified-water folds or wet outer-edge cells across the full ±350m
tail strip. Larger candidates were not promoted. Probe exec35446 is complete;
results are in `tmp/colorado-terminal-smoothing-probe-v1/completion.json`.

New production tool `refine_colorado_terminal_bend.py` preserves the exact
captured endpoint/normal and 224,593 upstream chart samples. Only the last
numerical-axis window changes (maximum55.2606m displacement), with source bed,
terrain and masks untouched. Native end station becomes450314m; the geographic
source end remains453334.02824855957m. This is reparameterization, not shortening
the river. V9 chart `tmp/colorado-shared-hydraulic-frame-terminal-v9`, manifest
SHA `1568fa85c2a2cc2b0391a19091d0fd8596223719ff768df3040d955138569bc4`, frame
SHA `f3286ca2f63fbdfa06f3e83746e4ee917179c61946ed0a2606344446a20723df`.

Actual source cores376/377 were rebuilt with the unchanged original encoded
terrain and existing lateral intervals. Both pass full source-water footprint,
wet-edge, wet-fold and friction checks:153104+76452 classified core cells,
zero omitted; wet metric minima .4269629/.6499817. Exec73826 is complete,
receipt `tmp/colorado-terminal-bend-inputs-v9/completion.json`, SHA
`aafe610fbec84ee70708b68574799c5a752d2a9bc55e8bc398126b454f56f75f`.

New `SharedFrameCompatibility` makes an explicit replacement-chart join prove
that every used source station, position, normal, curvature, source association
and rendered map column is **bit-identical**. Changed used columns require a
rebuild; no field projection or tolerance was added. Legacy same-chart joining
is unchanged. The join's selected frame and provenance are updated only on
this explicitly verified path. This avoids duplicating 376 intact packages.
Sixty targeted tests /36 subtests passed, no skips, including invalid source,
frame, endpoint, registration and tiny-used-coordinate-change refusals.

All378 packages have now passed that compatibility/file-hash check.376 remain
unchanged and2 rebuilt; all37,805,809 source-core classified-water cells remain
covered. Selection `tmp/colorado-terminal-join-audit-v9/selection.json`, SHA
`208e9864f6822f9c6b85c53081c703985c93b268171e0e6db67073f3a851b95d`.
The actual mixed-parent last-three-window join also passed:1739×201 grid,
source450000–453334.02824855957m,15210 dry-padding cells. Report SHA
`d2b8aeb4495fc5c132d5c63d04f33bf8f2568c07c591e6d332f0646a526bb585` at
`tmp/colorado-terminal-join-audit-v9/tail-join/build_report.json`.
Durable summary: `terminal_bend_repair_2026_10_07.json`.

The same driver is now running the **complete new-chart terrain/classification/
input coverage audit**: **exec83133, driver22432 / wrapper13268**,
script `tmp/validate_colorado_terminal_join_v9.py`, job
`tmp/colorado-terminal-join-audit-v9`. A source-reuse or tail-join receipt is
not completion of this full audit. Check live process/terminal state first.
One full-input join waits for it: **exec51656, driver30460 / wrapper35216**,
script `tmp/join_colorado_after_terminal_audit_v9.py`, job
`tmp/colorado-full-route-join-job-v9`, output
`tmp/colorado-full-route-joined-inputs-v9`. It requires complete coverage,
zero classified-water folds,12GiB available commit,40GiB disk and60sec engine
quiet; two-hour deferral. It does not launch a native cook. These jobs bind the
join, compatibility and terrain modules; do not edit protected modules or
launch a duplicate while they remain live.

A4 is now actually advancing: exec70425, driver3192, **solver11252**, source
state unchanged, streamed output. Launch had20,238,057,472 available commitment
bytes and70,555,308,032 free disk bytes. Do not restart it. No A4 engine importer
or descent guard has been created. It remains the older14.4km diagnostic chart.

Read-only native memory inspection found another full-domain constraint:
initial/live/next states plus predictor/corrector and bed retain25 doubles per
cell; MUSCL primitive/slope scratch retains10 more, plus3 byte masks. Streamed
capture adds4 derived doubles while that scratch persists. The new79,030,458-cell
domain therefore needs at least24,894,594,270 bytes for these arrays during
capture, before row caches, loader/runtime overhead and system reserve. CLI
already moves its Scenario, so another move is not a repair. Do not launch the
full cook just because input joining fits12GiB. A bounded-stage/in-place
allocation improvement must preserve numerical results and be validated in an
isolated build, never overwrite the running A4 binary or loaded engine DLLs.

No captured geography was changed, other task interrupted, playable map
promoted, commit or push performed. Full-map gameplay/render/vegetation and
packaged20FPS validation remain outstanding; keep the goal active.

### October 7: complete V9 coverage audit and exact in-place native RK memory repair

Previous turn made progress. The complete V9 audit is now terminal-success:
all79,030,458 queries have terrain and classified-water input coverage, with
zero water-chart metric values at or below0.1; protected source files unchanged.
Receipt `tmp/colorado-terminal-join-audit-v9/completion.json`, SHA
`eaabd763279ebb82e84f634a51d41f78d8b563d018b6bb6c8465641e07d63222`.
Audit exec83133 is finished. Do not repeat this audit on unchanged inputs.

The one existing full-input join remains **exec51656, driver30460/wrapper35216**,
job `tmp/colorado-full-route-join-job-v9`. At the latest check it had no
`join-launch.json`: the other task resumed `RaftSim.Crew.StrokeTuning`
(`UnrealEditor-Cmd` PID33420, `tmp/stroke-tune-3.log`), and available commitment
was below the12GiB join guard. Do not stop or message it, weaken the guard, or
launch a duplicate. The guard defers after two hours; check terminal receipts
and live processes before deciding what to do next. No full native cook queued.

Core `solver_runtime.cpp` now avoids the third full WaterState only when
feature_strength_scale is exactly zero. Completed RK stages combine in place,
with every old cell primitive read before any write; derived fields recompute
after the row barrier. Nonzero authored forcing keeps the original separate
destination and publish semantics. No numerical operation, precision, threshold,
class layout or source geometry changed. Existing binary/DLLs are untouched.

New C++ tests compare all six state arrays bitwise (including signed zeros),
wet masks and time against the unchanged separate-destination path selected
using nonzero forcing and an empty feature list. They cover HLL/Roe/Rusanov,
wet/dry films, replacement state, large parallel/serial grids, three roughness
values, bed coupling off/on and CFL subdivisions. All seven CTests passed,
including tiled-domain workers1/8 and streamed output. Build exec60831 complete.
Isolated binary `tmp/colorado-inplace-rk-build-v1/raftsim_water_solver.exe`, SHA
`b75d0eeae84ad9e5be3624e449ce21cd7fa87666f0296ce6e2aa1e0e6de31132`;
CTest log SHA `4ddf2c8c96b853ce1ed983944f7096ce8af24a7322a9cb4270396c7ebc35745e`.
Fourteen Python frame/flux tests passed with all native parity tests enabled,
no skips. The unchanged running A4 binary is still the compact-flux-v1 build.

Actual saved Colorado1274×167 frame_0012 was replayed for five native steps in
private old/new packages, using the same real bed/boundaries/state and streamed
output. All four compressed frames, manifest and validation are byte-identical.
Windows native peak commitment fell68,968,448→58,671,104 bytes (10,297,344 saved).
All protected originals and binaries retained their hashes; no source hydraulic
failure was promoted. Exec89396 completed, script
`tmp/validate_colorado_inplace_rk_v1.py`; receipt
`tmp/colorado-inplace-rk-validation-v1/completion.json`, SHA
`ea31690546678cf993892853695f1b7c7155276020bb8611f1833033d7f69050`.
Durable summary: `native_inplace_rk_2026_10_07.json`.

The removed allocation is49bytes/cell, or3,872,492,442 bytes on full V9.
Remaining capture arrays still total at least21,022,101,828 bytes
(33 doubles+2 masks per cell), before row caches/loader/overhead/reserve.
This is not yet a safe full-cook budget. Next useful memory work is bounding
the retained MUSCL primitive/slope scratch or its capture lifetime, preserving
exact results and proving peak usage in another isolated build.

A4 remains the existing older14.4km exact-state continuation, exec70425,
driver3192/solver11252, advancing with unchanged compact-flux-v1 binary.
No duplicate production solve or A4 engine/descent guard launched. Check its
terminal review before promotion. Full-map runtime/navigation/dressing and
packaged20FPS remain required. Dirty user/other-task work is preserved; goal
active, no commit/push this turn.

### October 7: bounded MUSCL row scratch with frozen-binary numerical parity

Previous turn made verified progress. This turn replaced native full-grid
primitive/slope scratch with **five primitive rows and three slope rows per
worker**. The same immutable stage and cell arithmetic feed the rolling caches.
Each stage invalidates all row tags; failed fills never publish a partial row;
all six slopes are assigned including dry cells/dry-neighbor directions.
Per-thread retained capacity and independent nested leases remain; joined-row
barriers and serial diagnostic reduction order are unchanged. No float
precision, bed/water geometry, forcing, thresholds or solver class layout changed.

Isolated build **exec12413 completed**; all7CTest suites passed, including
rolling eviction/failed fills/small shapes/ownership, wet-dry replacement,
parallel/serial exact-state comparisons, Cartesian workers1/8 and stream output.
Binary `tmp/colorado-row-scratch-build-v1/raftsim_water_solver.exe`, SHA
`7e55aaf46b96c3508d3ffdff07dcde696ac8b9b43414b211de313948c58d2083`;
CTest log SHA `89e26e8eb399c92f0393a225a30885505c5e5dd5adb42a6854339cb16ce9ecf6`.
Do not overwrite the running A4 binary or any loaded engine DLL.

New `test_native_rolling_rows.py` compares the candidate with the unchanged
in-place-RK/full-scratch executable:27 fixture/grid/scheme cases, covering all
three flux schemes, row counts2/3/4/5/6 and a129×131 parallel wet/dry grid.
Every native output file is byte-identical; fixture full/compact/boundary flux
diagnostics are also exact. An initial synthetic package schema error was fixed
(empty features/probes must be keyed objects, not bare arrays); the reference
binary rejected those malformed fixtures before stepping. No physical tolerance
was weakened. The two new Python tests and14existing frame/flux tests now pass,
all native oracles enabled, no skips.

**Exec58047 completed** the real saved Colorado1274×167 replay:200native steps
per run, old/new/new/old ordering. All compressed initial/final frames,
manifests and validation files match across all four runs. Peak commitment:
old58,671,104/58,716,160 bytes; new42,708,992/42,680,320 bytes. Whole-process
times16.172/16.250s old versus15.344/15.953s new, so this bounded test found no
slowdown. This is not an FPS claim or promotion of the original failed-flow cook.
Script `tmp/validate_colorado_row_scratch_v1.py`; receipt
`tmp/colorado-row-scratch-validation-v1/completion.json`, SHA
`8512be3d40048b35b17dd8919969fb66423812d23dc88ab5a775cf9dbf9a5b1a`.
Protected sources/binaries unchanged. Durable summary and source fingerprints:
`native_rolling_scratch_2026_10_07.json`.

Full V9 scratch accounting drops6,322,436,640→273,792,128 bytes at native CLI's
default four worker lanes. With prior in-place RK, the capture-array lower bound
is now14,973,457,316bytes including retained row caches, versus24,894,594,270
before the two repairs. Actual full-grid peak remains unmeasured; loader/runtime
overhead, resource reserve and output disk budget must still be included.
The full capture volume and wall time matter too: do not automatically request
21full79M-cell CSV frames when current disk headroom cannot support them. Review
requires at least three frames (first/previous/final); choose a justified bounded
schedule without weakening its convergence, finite-state or hydraulic gates.
Do not start a duplicate production solver while A4 remains active.

The **existing full-input join really started** after the other engine run exited:
`tmp/colorado-full-route-join-job-v9/join-launch.json` at17:32local, with
19,374,362,624 available commitment bytes and69,824,667,648 free disk bytes.
Still live at last check: exec51656, driver30460/wrapper35216; CPU252.75s,
private2,618,454,016bytes. No completion/failure receipt yet, and the output
directory is created only after coverage/merge/hash checks; its absence is not
failure. Do not duplicate it or edit its protected Python dependencies.
A4 remains live: exec70425, driver3192, solver11252 (CPU7330.84s latest), old
compact-flux-v1 binary unchanged; no terminal review/importer/descent guard yet.

Next: inspect those live handles, finish full-domain RAM/disk/time launch budget
using the now-verified bounded native candidate, and advance actual map/terrain/
dressing/navigation validation when valid fields are available. Six continuous
normal playable rivers, all rapid placement evidence and packaged20FPS still
require end-to-end acceptance. Goal remains active; no commit/push this turn.

### October 7: full V9 input assembly completed; bounded vegetation exclusion

Previous turn made verified progress. **Full-input join exec51656 is now
terminal-success** (17:46local), not a job to restart. Receipt
`tmp/colorado-full-route-join-job-v9/completion.json`, SHA
`8394319d1f0b4dd2a0b0d37d7711881c9fa5c61e220c12531a1e8f2e28a94b56`.
Output `tmp/colorado-full-route-joined-inputs-v9`, build-report SHA
`0ccec045068d11ccb58232a4f66b56c53155cb0d683f50a160d17e62f3b3bce6`;
one225158×351,2m native grid covers source0–453334.02824855957m.
Actual scenario files include632,243,792byte bed and722,400,155byte compressed
initial-state archive. Source packages/terrain passed closing hashes.
This is the complete input domain, not a cooked or playable full river.

The Colorado/Chilko dressing builders previously materialized every registered
water coordinate and a full wet-point KD tree. New shared
`cooked_water_clearance.py` borrows the read-only wet-mask mapping, bounds each
candidate batch spatially, and queries at most262144registered cells per block.
Cross-section endpoint bounding boxes are rounded outward; all physically near
branches are included even at distant station indices. It preserves the same
cell-diagonal allowance and12m exclusion. Returned distances are deliberately
capped at12m for the eligibility decision, not presented as global nearest-water
measurements. Missing/invalid wet masks refuse rather than imply dry clearance.
Source water, slope/root support, meshes, deterministic candidate seeds and
art-directed/nonblocking status are unchanged.

Forty-nine clearance/dressing/runtime/map-contract tests passed, no skips,
including exact old-global-tree comparisons at folds, reversed chunk order,
several block sizes, nextafter threshold points, translated coordinates,
cropped lattices/Chilko CRS and bounded mask access. On **actual screened
runtimes**, full old/new dressing manifests are identical: Colorado shore-six
2897instances/94populated chunks; Chilko Bidwell4679/35. Actual Colorado build
times35.047s original/34.640s bounded; Chilko.844s/.688s. This changes allocation,
not visible placement. No full-river vegetation or new rendered acceptance is
claimed. Exec69334 completed; script `tmp/validate_bounded_dressing_v1.py`,
receipt `tmp/continuous-bounded-dressing-validation-v1/completion.json`, SHA
`81ba9b947b17c9459d2cd398fc0724f4538d5425014e4651a750bfbf2371abdf`.
Durable summary `continuous_vegetation_clearance_2026_10_07.json`.

One full-domain **read-only zero-step native inspection** is now guarded:
**exec90541, driver35928/wrapper27732**, script
`tmp/inspect_colorado_full_domain_v9.py`, job
`tmp/colorado-full-domain-inspection-v9`. It uses the unchanged isolated
rolling-scratch binary SHA
`7e55aaf46b96c3508d3ffdff07dcde696ac8b9b43414b211de313948c58d2083`
and hash-binds the complete V9 inputs. It waits60sec engine idle,16GiB available
commit,12GiB physical and41GiB disk; defers after30min. At latest check it had
only launch.json, **no native process yet**: available commitment was just below
the guard. Do not duplicate it or reduce the guard to force a launch.
Once allowed, --inspect-face-discharge loads the full native domain and checks
all225159station-face discharges, measuring process peak memory/time without
integration, writes or a duplicate cook. Only its own inspection process is
stopped if it exceeds15min or available commitment falls below2GiB. Its result
will not prove capture memory, convergence, final fields or FPS. Preserve any
failure/partial evidence; no blind retry. A4 remains the sole production solve
(exec70425, driver3192/solver11252), unchanged old14.4km domain.

Read-only downstream inspection found the next full-map integration issue:
`build_colorado_continuous_map_contract.py` still materializes all wet coordinates
and serializes every wet-bed collision probe into JSON. The native continuous
importer in `RaftSimEditorCatalogMap.cpp` then stores all those JSON vectors and
per-chunk arrays before its existing32-chunk terrain batches. A full37M-cell
wet corridor must not become a huge JSON object graph. The next bounded-import
repair should stream hash-bound per-chunk binary probes while retaining every
wet-cell validation, exact terrain ownership and old small-contract support;
do not replace full collision checking with sparse samples or weaken10cm gates.
Other task's latest live engine was PID14444, GearReview at `tmp/stroke-final-a`;
it exited naturally before the latest memory check. Never interrupt/message it.

No shared engine rebuild, map replacement, menu promotion, commit or push this
turn. Full native cook resource/time scheduling, continuous-map import/dressing,
all rapid placements, normal playable descent/rescue/render and packaged20FPS
remain required. Goal active; preserved user/other-task changes untouched.

### 2026-10-07 checkpoint: lossless chunk-owned collision probes

User requested committing/pushing the current river work, then continuing.
The solver dependency is committed and pushed on its main as `2f6d961`.
Main-repository checkpoint includes river reconstruction scripts/evidence,
bounded native import support and river diagnostics, not the other task's crew,
grip, rescue-animation, production-quality-test or changelog modifications.
Generated ShoreSixSupportV3 construction map/external actors are preserved
locally and explicitly ignored, not promoted as a finished gameplay map.

`continuous_collision_probes.py` writes all wet cells as hash-bound per-terrain-
chunk little-endian float64 XYZ streams. It keeps exact legacy arithmetic,
row-major order within each owner, native edge ownership and the 40 GiB disk
reserve. Large map contracts refuse the old unbounded JSON representation.
The native adapter checks complete counts, unique/known owners, bound hashes,
finite positions and owner identity before world creation; collision checking
then reads each chunk without retaining the full-river point set. All native
10 cm acceptance gates remain unchanged. Runtime dependency hashing is streamed.

Fresh real Colorado comparison:
`tmp/continuous-chunked-probes-validation-v1/completion.json` reports every one
of103369 wet probes bit-identical to the preserved batched-start-v4 contract,
partitioned among23 terrain owners in3.766s. New contract SHA256
`ba46e216319924a040321d66a25a3cc8f50c9d218e880d59cfc0f2ae30eb2a39`.
This is export parity, not a fresh engine import or packaged performance claim.
357 changed-script tests passed with5 native tests initially skipped; all16
native Python checks subsequently passed with explicit isolated binary paths,
and all7 CTests passed. The38 focused map/export/clearance tests also passed.

One editor build is queued in exec81222 using the existing idle-guard script,
label `continuous-diagnostic-access-build-v6`. It waits for60s without editor,
game or build processes and will not replace loaded DLLs. Other task's
GearReview PID37284 was live at the last check; do not stop or message it.
Native streaming-probe automation and actual chunked map import still require
that successful link. A4 exec70425 remains the sole live production solve;
full-grid read-only inspection exec90541 still has its resource/idle guard.
Do not confuse this requested source checkpoint with completed river acceptance.

Checkpoint delivery confirmed: main `3fa9b553d03ed0b84e9c72753dba57fafad89e31`
was pushed and `git ls-remote origin refs/heads/main` returned that exact commit.
All29 LFS objects (1.7 MB) uploaded. Solver dependency main `2f6d961` was pushed
first. Remaining tracked working edits at delivery were the other task's crew,
grip, rescue-animation and associated documentation/tests, deliberately excluded.
Additional20 catalog/Pacuare/reprojection pytest checks passed; both continuous
capture and profiler PowerShell fixture suites passed.

Continuing after the push: guarded editor build exec81222 completed successfully
at2026-10-08T01:08:17Z, with the new native parser test and map importer compiled
and linked. Receipt `tmp/continuous-diagnostic-access-build-v6/completion.json`
has exit_code0. Another task then started UBT PID37596; the immediate native-test
launch correctly refused to overlap it. One guarded native test is now waiting
in exec50884, script `tmp/test_chunked_probes_native_v1.ps1`. After60s shared idle,
it will run four targeted native tests (collision probe stream, both rapid
registrations and rapid profiles) into `tmp/continuous-chunked-probes-native-v1`.
It defers after15min busy, does not stop/message other work and does not import
or overwrite a map. Check this handle/report before launching any replacement.
The fresh binary-probe contract is ready at
`tmp/continuous-chunked-probes-validation-v1/contract.json`; full native terrain
import, normal gameplay and packaged20FPS are still separate acceptance gates.

### 2026-10-07 post-push native integration checks

Previous goal turn was progress: committed/pushed the verified checkpoint,
completed the editor rebuild and retained active guards. The full-domain
read-only native inspection exec90541 is now terminal success. It actually
loaded all79030458 V9 cells and evaluated225159 station faces in33.547s;
peak commitment10376486912 bytes, peak working set10360287232 bytes,332 samples.
Every discharge is finite, range62.760705..441.319903 m3/s; initial nonuniformity
is NOT convergence. All protected inputs/binary stayed identical. The durable
receipt is `review/native_full_domain_inspection_2026_10_07.json`. No steps,
native full cook, capture-memory or FPS measurement occurred. Do not repeat the
same read-only inspection; use its actual memory result in later scheduling.

Native probe stream, synthetic rapid registration and rapid profiles actually
passed in `tmp/continuous-chunked-probes-native-v1/automation/index.json`
(SHA `616ff7a01e78339d32fbfb5b63cd72fca31e180fff8670d603eecf9e544bd5d6`).
The fourth test reported Success WITH WARNING because its real assembly/chart
arguments were absent; that does not prove real source registration. The strict
import gate correctly stayed closed (3 clean successes,1 warning,0 failures).
Corrected native run is queued in exec44237, same guard script now selecting
`continuous-chunked-probes-native-v2`, actual `colorado-continuous-assembly-v3`
manifest and final `colorado-shared-hydraulic-frame-terminal-v9` chart. It must
produce4 clean successes and0 warnings before import; no gate was weakened.

The exact comparison import contract is
`tmp/continuous-chunked-import-parity-v1/contract.json`, SHA
`91a4e14c2ab250931ea9e20daa932a826287c9cc8089192dd2ffaa80c9b1106b`.
It preserves the earlier76-chunk BatchedStartV4 terrain, cooked fields, Nanite,
1309 vegetation instances, rig, launch/finish and three rapid source charts;
only the probe representation and fresh map identity differ. It preserves
every103369 original wet probe. This intentionally bounded regression is not
a substitute for the full450km replacement or new gameplay acceptance.
Our first waiting import guard exec93008/PID39948 was terminated before any
engine launch solely to correct the test-result dependency; no other process
was stopped. Replacement guard is live exec96215, script
`tmp/import_chunked_collision_parity_v1.ps1`, waiting on the V2 test result and
60s shared engine idle, with a25min wait deadline. Check it before any replacement.
It creates only fresh `L_Colorado_ContinuousChunkedParityV1`, never overwrites
earlier maps; its generated map/external actors are explicitly ignored.
Other task's latest live editor was17052 (stroke-final-e-tests); do not stop,
pause or message it. A4 exec70425/solver11252 remains the single live production
solve on the old14.4km chart. Full import and full-river acceptance remain open.

### 2026-10-07 native chunked import verified; full-length loader repair

Exec44237 completed with four clean native successes, zero warnings/failures.
The corrected real-source test exercised all94 sites in five source rapids on
the V9 chart. Exec96215 then completed: the fresh parity map saved successfully,
76 Nanite proxies,3800 terrain probes (max0.317972cm),103369 wet-bed probes
(max0.261719cm) and1309 vegetation roots (max0.273296cm). These match the earlier
legacy-JSON import exactly. Durable evidence: `review/native_chunked_import_2026_10_07.json`.
This closes the serialization/import regression, not full-river gameplay.

Found a separate full-length runtime blocker: all three RSBF readers capped
rows at200000 while Colorado V9 requires225158. New preflight retains the old
102400000-cell/922400040-byte budget, accepting351x225158 (712174794 bytes),
and validates all four serialized array counts before allocation. It rejects
invalid dimensions before multiplication, malformed counts, wrong file extents
and invalid spacing/origin. Existing physics and sampling arithmetic are unchanged.
Read-only compatibility audit `tmp/support-band-layout-audit-v1.json` checked
all18 existing files successfully (SHA256
`7c9c83073ad49259efbd2052f8653156124139f70aca57126bd0146211ea0920`).
Buildv7 linked successfully; native layout/bounds/transit tests run in exec59083.
A subsequent extreme-dimension overflow hardening requires a fresh build/test
before committing the loader. No full-domain cook, new descent or20FPS claim.

Final validation completed: buildv8 linked successfully at2026-10-08T01:35:42Z.
Water DLL SHA256 `0572b0505f2fdfa1dd7b1848ae51ebb47f6ffb229567f0a9f6afbc7f70816614`.
Exec59993 completed with3 clean native tests,0 warnings/failures/not-run, report
`tmp/support-band-layout-native-v2/automation/index.json` SHA256
`b1a938b75e51f7e4711a4483816f89f910450ec74999c8e50b0f72747638c606`.
The test actually wrote/read225158x2 through physical support, presentation and
observed-whitewater production loaders, verified the450314m endpoint and sampled
whitewater past the former row cap. Full351-column geometry is checked by an
exact virtual extent/count-word fixture, not claimed as full payload ingestion.
The unchanged South Fork full-reach transit test loaded its12271x21 baseline,
stepped native water and preserved overlap on window movement. Extreme malformed
dimensions and serialized counts are refused before payload allocation.

No build/import/test guard remains live from this batch. A4 exec70425/solver11252
continues independently, last observed28800/48000 steps. Preserve its bound
binary/inputs; next work remains full-domain hydraulics, continuous scene and
runtime bundle integration, then real descent/render/rescue and packaged20FPS
validation. None of those gates is replaced by these bounded regression checks.

### 2026-10-07 continuous runtime bundle closure

Previous goal turn was progress: full-length RSBF repair committed/pushed as
`ec7e51a2c`. Current work extends the verified runtime bundle path to curved
continuous rivers. Previously it accepted only Cartesian streaming/atlas data
and JSON/NumPy files, excluding the continuous map's binary baseline. The new
closure follows both named windows and hash-bound full-reach transit fields,
requires bed/h/u/v/wet_mask and the native-named presentation baseline, includes
declared observed-whitewater fields, checks RSBF sizes/counts without allocating
their payload and retains path/hash/scene-binding gates. UBT permits only named
RSBF sidecars in addition to the previous file types; no candidate was activated
in the normal package list.89 focused packaging/ground-source tests passed.
The existing South Fork production bundle verified unchanged:2405 files,
917995570 logical bytes. Other task's crew source edits remain excluded.

Read-only native inventory succeeded for the saved chunked-parity candidate:
`tmp/continuous-runtime-bundle-native-v1/inventory/bindings.json`. Its empty
run-manager route override correctly falls back to the curved hydraulic chart,
as the production RunManager does. No saved asset changed. A separate frozen
bundle and staged tree contain exactly9 dependencies/25942143 bytes; bundle
manifest SHA256 `f3d2ab1f06bebbeb024f194a08be7e6f7eaed971f688bb31d6d8732bbf6efa13`.

First native staged/source comparison completed1001 route queries and273 wet
field queries,24 solver steps per copy and one overlapping handoff per copy,
all with exactly zero difference. Nevertheless exec76159/PID38828 returned
-1073741819 after the log closed during editor shutdown. The partial report
`verify/report.json` is NOT a clean native pass. Preserve it and the log;
no new Unreal crash dump or Windows fault record was found during the bounded
inspection. Precise shutdown cause is not established. The verifier now resets
its own adapters and explicitly collects its Python/Unreal test objects before
requesting editor exit; no physics or acceptance threshold was changed.

Fresh rerun is queued in exec72522, script
`tmp/run_continuous_bundle_native_v1.ps1 -Mode verify`, output `verify-v2` inside
the same evidence root. It records process exit separately and must exit0.
Other task's live editor at last check was28128 (`tmp/neck-c/native.log`); wait,
do not stop/pause/message it. One dependent build guard is being started with
`tmp/build_after_continuous_bundle_verify_v1.ps1`: it requires a clean V2 process
and exact comparisons before invoking guarded buildv9. No duplicate build.
A4 exec70425/solver11252 remains live, last observed33600/48000 steps.
This is saved-data portability work, not a full-river cook, normal-menu map
replacement, packaged execution, rendered rescue or20FPS acceptance.

Dependent build guard handle is exec94443 (confirmed live); verifier exec72522
also remains live. At the final check the prior crew editor had exited; both
guards retain their idle/dependency checks. Do not start substitutes on the
basis of missing output while these handles are live. Current packaging edits
are uncommitted pending the clean native rerun/build; crew-review/crew-visual
source changes are owned by the other task and must not be staged with them.

### 2026-10-07 staged native rerun completed cleanly

Previous turn was progress (continuous packaging implementation,89 tests and
native inventory) plus verified waiting. Exec72522 is now terminal success:
PID40632 exited0 at2026-10-08T01:58:09Z after explicit harness-owned adapter reset
and Python/Unreal collection. All1001 route queries and273 wet field queries
matched exactly after24 actual solver steps/copy and an overlapping handoff.
The failed earlier exit remains preserved; no claim of a proven general engine
shutdown repair. Durable receipt: `review/native_staged_runtime_2026_10_07.json`.
Dependent exec94443/buildv9 completed0 at01:59:22Z; updated rules evaluated with
the unchanged active South Fork bundle. No candidate package activation occurred.
Both guards are terminal; no substitute build or repeated comparison is needed.
The next resource gap is full79M-cell native stepping/capture peak memory and
output size, distinct from the already-passed zero-step full-domain inspection.
A4 remains the only production cook; keep its bound binary/inputs untouched.
