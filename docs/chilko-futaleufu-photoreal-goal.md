# Chilko And Futaleufu Photoreal Goal

## Portfolio Decision

The original five-river production portfolio is:

1. South Fork American River, Chili Bar to Folsom Reservoir.
2. Colorado River through Grand Canyon, Lees Ferry to Pearce Ferry.
3. Pacuare River, Tres Equis to Siquirres.
4. Futaleufu River, Rio Azul Swinging Bridge to The Pasarela.
5. Chilko River, Chilko River Lodge to the Chilko-Taseko Junction.

Zambezi Batoka Gorge is now the sixth runnable environment and, with Futaleufu, forms the immediate environment priority. Its current classification is `reference_free_run`: the complete physical corridor and procedural water seed are playable, but authoritative full-reach terrain, centerline, bathymetry, rapid hydraulics, guide, and review evidence remain required for production-fidelity promotion. This priority change does not remove Chilko from the runnable portfolio or promote, delete, or rewrite any existing evidence.

## Objective

Complete photoreal, physically readable Unreal environments for Futaleufu and Chilko. Completion requires lifelike guide-seat and river-eye captures at reviewed flow levels, exact route and rapid stationing, validated C++ water windows, flexible-raft outcome runs, rights and publication review, and measured desktop, console-quality, handheld, and VR evidence.

Futaleufu keeps its existing Rio Azul Swinging Bridge-to-The Pasarela production corridor and native canopy work. Chilko now has a first source-scale technical corridor and isolated Unreal Landscape candidate, but neither is a validated rapid corridor or photoreal environment.

## Current Chilko Evidence

The first source attachment is committed under `physics/data/real_world/chilko_river_bc/`. It preserves 545 official British Columbia Freshwater Atlas features named Chilko River and selects 160 source segments between the current put-in and take-out review seeds. The corridor builder proves those selected segments form one unbranched chain and stitches all 160 at zero join gap. Clipping to the nearest official vertices yields a 55.846 km review route. The nearest vertices remain 218.44 m from the lodge seed and 84.929 m from the Taseko-mouth seed, so this is official hydrography stationing, not launch/ramp approval.

Environment and Climate Change Canada metadata plus monthly mean discharge are attached for `08MA002` from November 1928 through December 2025 and `08MA001` from May 1927 through December 2024. `08MA002` is the upstream seasonality/timing candidate, but it is above the put-in and omits route tributaries. `08MA001` is downstream of the Taseko confluence, so it is routing context only and cannot define pre-confluence gameplay discharge. Numeric low/reference/high bands remain blocked pending daily-window routing and local guide review.

The corridor now range-reads bounded official source windows rather than downloading national rasters. The attached MRDEM-30 DTM and per-pixel-source clips retain the EPSG:3979 source CRS, CGVD2013 orthometric vertical datum (EPSG:6647), 30 m resolution, and Open Government Licence - Canada provenance. The attached August 25, 2025 Sentinel-2 true-color and scene-classification clips provide 10 m and 20 m route-window context with zero obscured valid pixels in the selected window. They support source-scale terrain and seasonal surface review only; they are not orthophoto, bank, rock, bathymetry, access, or rapid geometry authority.

The generated corridor records a 33.904 km by 38.789 km bounding window, bounded visual channel conditioning with a measured 56.038 m maximum cut and zero fill, 2048 material/mask inputs, and a 1009x1009 16-bit Unreal heightfield whose 33.6-38.5 m sample spacing matches the source scale. The isolated UE 5.8 candidate builds one current Nanite representation, binds all 64 Landscape and 64 Nanite material slots, and captures guide-seat and river-eye evidence. Visual review rejects photoreal promotion: smooth 30 m banks, weak source-albedo read, sparse generic vegetation, and non-solver review water remain obvious. Exact metrics, hashes, captures, and blockers are in `docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_source_scale_landscape_review.json`.

## Chilko Source Contract

The authored reach starts at the Chilko River Lodge put-in and ends at the Chilko-Taseko Junction recreation-site take-out. Put-in ownership, access, and exact launch geometry require direct review. The take-out has an official British Columbia recreation-site record, but its exact ramp geometry and current access conditions still require field or operator confirmation.

Preferred source stack:

- Terrain: BC Data Catalogue and GeoBC elevation or lidar coverage first; Natural Resources Canada CanElevation products as the national fallback. Record product, acquisition date, horizontal and vertical datum, resolution, license, void handling, and hydrologic conditioning.
- Hydrography: British Columbia Freshwater Atlas or another official provincial watercourse layer, checked against aerial imagery and guide GPS. OSM can seed discovery only.
- Flow: Environment and Climate Change Canada stations `08MA002` (Chilko River at outlet of Chilko Lake) and `08MA001` (Chilko River near Redstone) are the first official candidates. Gauge coverage, regulation, lag, tributary effects, station periods, units, and route applicability must be reviewed before any gameplay band gets a numeric threshold.
- Imagery: GeoBC or other rights-compatible provincial orthophoto where available, then Copernicus Sentinel-2 and Landsat for seasonal color, water extent, vegetation, snow, smoke, and cloud screening.
- Land, culture, and publication: Tŝilhqot’in National Government place-name, fisheries, title-land, access, stewardship, and publication guidance must be reviewed before public release or detailed hazard/access publication.
- Guide and visual evidence: BC Whitewater, outfitter descriptions, guide interviews, first-party footage, and public/social links are reference-only until item-level permission and provenance are recorded.

No guide page, social post, or satellite scene is exact bathymetry authority. No source may be used to expose sensitive locations or imply permission to access private or Title lands.

## Rapid Priorities

Initial guide/media leads name Bidwell Rapids, Lava Canyon, White Mile, Green Mile, and Miracle Canyon. These are provisional production targets, not accepted stations. Exact names, order, class, geometry, runnable lines, portage/scout behavior, and flow response require source reconciliation and local guide review.

Each accepted rapid must have:

- Exact WGS84 point or span geometry and production-route stationing.
- Terrain, channel, rock, and bank evidence with accuracy and datum limits.
- Low, reference, and high flow context tied to reviewed gauge windows rather than invented discharge bands.
- An unforced or minimally forced C++ water window that passes analytic, conservation, boundary, stitched-window, and GeoClaw comparison gates where GeoClaw applies.
- Clean, bounded consequence, pin/wrap, flip, swimmer, rescue, and recovery runs appropriate to the feature.
- Guide-seat and river-eye visual/audio comparisons at the same flow and camera station.

## Visual Direction

Chilko should read as a real transition through the Chilcotin landscape, not a generic alpine canyon. Source evidence should determine river color and turbidity, canyon and bench form, exposed rock, conifer/aspen/willow distribution, burned or regenerating areas, riparian density, weather, and seasonal snow. Turquoise water, basalt canyon walls, open plateau benches, forest transitions, and hoodoo-like forms may be used only where the attached corridor evidence supports them.

Futaleufu remains a Patagonian turquoise big-water corridor with granite and mixed temperate-rainforest structure, but current coigue and cordilleran-cypress candidates remain review assets rather than ecology or photoreal approval.

## Chilko Organic Lit Terrain V1

The runnable Lava Canyon map now uses a Chilko-only four-scale Default Lit
surface instead of leaving its source-conditioned banks nearly black. The graph
retains registered macro color, water/material zones, detail normals, wet-bank
conditioning, and the existing Landscape, then adds open-bench value, dry grass
and mineral soil, slope-aware wet and oxidized basalt, scree, and fine mineral
response at non-harmonic world scales. It has no world-position offset and does
not change terrain geometry, collision, the protected solver strip, bathymetry,
hydraulic state, route stationing, or raft forces.

In the fixed left-bank guide region, mean luminance increases from 0.1199 to
0.2375 and pixels below 0.035 luminance fall from 30.05% to 1.04%. At river eye,
the same measures move from 0.1397 to 0.2616 and from 32.90% to 0.85%. The
editor build, native saved-material audit, runnable-map gate, and focused
regressions pass. Visual review still rejects photoreal promotion: the 30 m
source creates broad landforms and horizontal bands, the procedural trees are
repeated and stylized, ground cover and reach-specific rock structure are
sparse, the water remains uniform and opaque, and Lava Canyon's crests, holes,
foam, spray, mist, and shoreline impacts are understated.

The cordilleran-cypress V33 transition-path precursor now samples the V32 complementary source/HLOD handoff at 17 exact radial positions from 23.00 m through 27.00 m. It corrected an incomplete woody-material binding and proved that the current dynamic screen mask requires the unchanged source trunk geometry to use traditional raster: the Nanite source path leaked trunk and branches into HLOD-owned pixels. Two deterministic runs keep source, HLOD, and combined variation below 0.004557 percent, match the authored Bayer composite within 0.001411 percent, and bound transition overhead above ordinary camera-motion controls to 1.156684 percentage points. This retains a diagnostic path and renderer boundary, not a photoreal or production LOD. Same-world continuous motion with persistent view state, TAA history, motion vectors, target frame pacing, lit art, and desktop/VR profiling remains required.

V34 supplies that missing same-world diagnostic: three persistent source/HLOD/combined sequences each retain one world and TAA view state while moving from 23-27 m at a fixed 60 Hz simulation step, followed by endpoint settling. Independent runs reproduce all 147 frames within 0.000211 changed-pixel fraction at worst. Ending source coverage at 26 m and retaining ten HLOD-only moving frames reduces combined-to-HLOD history residue from 11.5889 percent to 2.4835 percent, then to 1.5829 percent after settling. The harness is retained, but the transition is not: the 4x4 Bayer pattern changes ownership in 6.25-percent ranks and causes a repeatable 4.3407 percentage-point spike above ordinary camera-motion controls, exceeding the unchanged 1.5-point limit. Replace it with a finer complementary mask or stable blue-noise sequence and rerun V34 before lit art or performance review. Fixed simulation pacing is not measured wall-clock performance, and the unlit frozen-WPO frames are not photoreal evidence.

V35 retains 4x4 as the historical default and exposes an isolated deterministic 8x8 pattern with 64 ownership ranks. Under the unchanged V34 motion contract, two independent 147-frame runs reduce maximum transition overhead by 68.79 percent, from 4.3407 to 1.3547 percentage points, passing the 1.5-point ceiling. Source-only controls change by at most 0.0000282, HLOD-only controls are byte-identical, and repeat variation stays below 0.0001020. The moving HLOD-only tail and settling reduce combined-to-HLOD residue from 5.8567 to 1.8537 to 1.1545 percent. Retain V35 for temporal validation, but do not treat it as photoreal approval: lit river-view patterning, source/HLOD silhouette mismatch, hazard readability, packaged desktop/VR performance, corridor ecology, and the other seven forms remain open.

## Runtime Water And Opaque Bank Ecology V1

Futaleufu and Chilko now have an explicit visible-water ownership contract. Their authored editor-capture ribbons remain hidden during play, while each saved `ARaftSimRiverWaterConfig` promotes the live solver mesh from a transparent detail overlay to the complete runtime carrier. River-specific calm/active coverage, color, roughness, specular response, and a 4.5 m sampled wet-bank feather replace the previous zero-coverage state that exposed black or terrain-textured “water.” A tag-based migration keeps already-versioned Pacuare and Colorado physical maps from losing both water carriers before their next regeneration.

Both maps also replace the 12,000-instance, broadleaf-dominated PVE card fallback with 6,200 deterministic source-mask and slope-screened opaque Nanite instances. Four project-owned volumetric forms provide conifer, broadleaf, shrub, and low ground-cover layers without masked leaf cards. This is bounded procedural infill where authoritative species-scale geometry is unavailable; it does not claim exact species, ecology, or terrain authority.

The Unreal editor builds, and focused `RaftSim.P4.RiverMapLoads.L_Terminator` and `RaftSim.P4.RiverMapLoads.L_LavaCanyon` each pass 1/1 with new assertions for visible solver coverage, four opaque vegetation forms, and organic ground cover. Matched gameplay review accepts the renderer correction and rejects photoreal promotion: the water remains too uniform and bright toward the horizon, the near banks remain broad and dark, and the solid procedural foliage is visibly stylized and repetitive. Exact hashes, contracts, evidence, and open external gates are recorded in `docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_futaleufu_runtime_water_opaque_vegetation_v1_review.json`.

## Temperate Canopy Variation V2

The shared Futaleufu/Chilko opaque fallback now removes its fixed downriver
species and height sequence. Exact-ratio 20-instance blocks use a deterministic
coprime permutation and block rotation, while tree height, yaw, footprint, and
material energy vary continuously. Temperate solid lobes increase from 8x16 to
12x24 topology, conifers gain overlapping inner crown mass, and broadleaf
branch/crown dimensions become continuous rather than modulo-stepped. Pacuare,
Zambezi, collision, bathymetry, solver fields, and raft forces are unchanged.

Both regenerated runnable maps retain 6,200 vegetation instances with the
4,650/1,550 canopy-understory split. Focused `L_Terminator` and `L_LavaCanyon`
runtime tests each pass 1/1 with zero warnings and errors, including the new
`RaftSimTemperateCanopyVariationV2` saved-map assertion. Fixed-camera review
accepts this as an incremental fallback improvement only: the stands are less
regular and less harshly faceted, but the one-form broadleaf/conifer family is
still visibly procedural, water and banks remain simplified, and species,
ecology, guide, art, and performance gates remain open. The review also records
four rejected isolated brackets—bare small crownlets, mushroom-like flat caps,
exposed trunk tips, and wall-forming Nanite Preserve Area—none of which were
promoted. Exact hashes, comparison metrics, artifacts, and remaining blockers
are in `docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_futaleufu_temperate_canopy_v2_review.json`.

## Temperate Canopy Structure V3

Futaleufú and Chilko now replace each temperate fallback's single smooth crown
ellipsoid with one distance-stable core and three deterministic embedded crown
volumes. Conifers also vary branch count and azimuth, stagger whorl height, retain
bounded storm-shortened limbs, and surround the branch skeleton with eleven
overlapping asymmetric crown-body volumes. The trunk now ends at the highest
whorl instead of protruding as a repeated spear above the foliage. Rainforest and
Zambezi vegetation paths are unchanged.

Both runnable maps retain the existing four-form family, 6,200 total instances,
and 4,650/1,550 canopy-understory split. The editor builds, the focused source
tests pass, and `RaftSim.P4.RiverMapLoads.L_Terminator` plus
`RaftSim.P4.RiverMapLoads.L_LavaCanyon` each complete 1/1 with zero warnings or
errors under the new `RaftSimTemperateCanopyStructureV3` saved-map assertion.
Fixed-camera comparison changes 8.99-10.60 percent of pixels beyond an eight-level
channel threshold and accepts the stronger continuous conifer silhouette as an
incremental fallback improvement.

This does not pass the photoreal gate. Only one broadleaf and one conifer
morphology remain, close crown geometry is still procedural, the banks lack dense
micro-ecology, and water remains too dark and uniform. The external tree audit did
not promote any reviewed third-party set: the available assets either failed the
active cameras or remain contract-limited to isolated comparison. Exact map and
asset hashes, before/after frames, test reports, rejected brackets, and remaining
external gates are recorded in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_futaleufu_temperate_canopy_structure_v3_review.json`.

## Chilko Native Water V1

Lava Canyon's retained capture ribbon no longer reuses the shared South Fork
shader field. It now has an isolated opaque Default Lit parent, two moving
Chilko-native normal layers, and two non-harmonic world-space optical scales.
The reach-local packed cooked field is sampled exactly once while ribbon
geometry and vertex color are built on the CPU; shader-field controls remain
present only as zeroed compatibility metadata. The live solver surface remains
the sole gameplay water and force authority and now receives Chilko-specific
reflection, ripple, foam, and color settings from the saved runtime config.

The fixed water-band comparison records a 99.65% changed-pixel fraction in the
guide/rapid view and 99.33% at river eye. Mean luminance increases from 0.1522
to 0.2529 and 0.1518 to 0.2514, while RGB standard deviation increases from
0.0463 to 0.0771 and 0.0473 to 0.0777. The isolated material audit and runnable
map gate pass, but this is a technical provenance correction rather than a
photoreal promotion. The retained frames still show broad synthetic water,
sparse foam and spray, weak crest-scale rapid structure, smooth 30 m banks,
repeated procedural ecology, and incomplete reach-specific rocks and ground
cover. No new live-gameplay renderer frame was accepted for this bracket, so
the runtime optical values remain config- and map-tested rather than visually
approved. Exact hashes, metrics, and the six open external gates are recorded
in `docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_lava_canyon_native_water_v1_review.json`.

## Futaleufu Native Water V1

Terminator's retained capture ribbon no longer reuses either Pacuare's normal
atlas or the shared South Fork shader field. It now has an isolated opaque
Default Lit parent, two moving Futaleufú-native normal layers, and two
non-harmonic world-space optical scales. The reach-local packed cooked field is
sampled exactly once while ribbon geometry and vertex color are built on the
CPU; the shader field controls are present only as zeroed compatibility
metadata. The live solver surface remains the sole gameplay water and force
authority and now receives Futaleufú-specific reflection, ripple, foam, and
color settings from the saved runtime config.

The fixed water-band comparison records a 57.56% changed-pixel fraction in the
guide/rapid view and 58.97% at river eye. Mean luminance increases from 0.1611
to 0.2063 and 0.1583 to 0.2028, while RGB standard deviation increases from
0.0482 to 0.0722 and 0.0479 to 0.0719. The isolated material audit and runnable
map gate pass, but this is a technical provenance correction rather than a
photoreal promotion. The retained frames still show broad synthetic water,
sparse foam and spray, weak crest-scale rapid structure, smooth 30 m banks,
repeated procedural ecology, and incomplete reach-specific rocks and ground
cover. No new live-gameplay renderer frame was accepted for this bracket, so
the runtime optical values remain config- and map-tested rather than visually
approved.

## Cold Water Optical Breakup V2

The retained Futaleufú and Chilko capture ribbons now carry readable
center-channel water structure instead of relying on a nearly flat solver
surface and one uniform optical response. Each river-local Default Lit parent
uses three moving normal directions, three non-harmonic world fields, and
bounded spatial roughness variation. The CPU review ribbon increases from 32
to 48 cross-current samples and combines the unchanged cooked solver relief
with bounded multiscale and cross-current chop plus restrained aeration color.
All render relief and embedded aeration taper to zero at the ribbon banks, so
the new current structure cannot lift water onto adjacent land.

This is a presentation milestone, not a physics change. The edited ribbon is
noncolliding and hidden during play; the live C++ solver mesh remains the sole
gameplay water renderer, collision, hydraulic-state, buoyancy, and raft-force
authority. Fixed captures accept more legible crest/current breakup in both
rivers, and the editor build plus both native water audits pass. Photoreal
promotion still fails because the near-field water remains dark and opaque,
named rapid holes and VFX are sparse, 30 m terrain is coarse, vegetation is
procedural, and no external guide, geospatial, hydraulic, art/VFX, or
target-hardware reviewer has accepted the result. Exact settings, metrics,
hashes, captures, authority boundaries, and six external gates are recorded in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_futaleufu_cold_water_v2_review.json`.

## Temperate Waterline Structure V1

The runnable Terminator and Lava Canyon maps now carry a full-route organic
waterline-structure layer where their 30 m terrain sources cannot resolve
cobbles and individual bank rocks. Each river places 1,440 deterministic
instances from the existing rights-reviewed six-form CC0 rock set. A 72-choice
search grounds every instance on the source Landscape and rejects placements
inside the complete visible-water width, below the dry-height floor, beyond the
55-degree slope ceiling, or too close to any segment of the full route. The six
HISM components are non-colliding and explicitly tagged as generic procedural
gap fill with no lithology, surveyed-bank, bathymetry, hazard, hydraulic, or
raft-force authority.

Both isolated generations place 1,440/1,440 targets with zero rejects.
Futaleufú retains a 32.568 m minimum centerline distance and 14.449-degree
maximum placed slope; Chilko retains 24.610 m and 15.746 degrees. Fixed-frame
comparison changes 14.35-14.43% of the selected Futaleufú bank band and
18.11-20.87% of the Chilko bank band beyond a two-percent pixel threshold.
The editor build passes, and the saved maps/manifests carry runtime-testable
component, density, collision, route, and authority tags.

This is retained as a technical environment improvement, not a photoreal
promotion. The added rocks supply needed scale and interrupt empty banks, but
the source benches remain broad, fine gravel and sediment are incomplete,
roots and deadwood are absent, foliage is visibly procedural, near-field water
is dark and opaque, rapid VFX are sparse, and all six external acceptance gates
remain open. Exact hashes, metrics, placement limits, captures, and blockers
are recorded in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_futaleufu_temperate_waterline_structure_v1_review.json`.

## Temperate Bank Ecology V4

The runnable Terminator and Lava Canyon maps now use two deterministic baked
morphologies for each broadleaf, conifer, riparian-shrub, and grass/forb
ground-cover form. The four new B meshes change seed, proportions, crown width,
height, and bounded growth lean before normals are rebuilt; this is real mesh
variation rather than another per-instance scale bracket. The existing
6,200-instance biome distribution remains intact.

Each river also adds 1,800 source-Landscape-grounded near-bank patches across
both sides of the complete route. A deterministic 64-choice search keeps every
patch outside the full visible-water width, above the conditioned water surface,
and below a 38-degree slope ceiling. All 1,800 targets place in both maps with
zero rejects. Understory increases from 1,550 to 3,350 instances while canopy
stays at 4,650, for 8,000 vegetation instances per river. The components are
non-colliding presentation geometry with no species, ecology, survey, terrain,
water, solver, bathymetry, hydraulic, or raft-force authority.

Matched V3-to-V4 fixed views show 6.26-6.83% changed pixels in Futaleufú and
6.35-6.56% in Chilko above eight RGB levels. The new grass/forb/shrub transition
visibly reduces the empty jump from waterline rocks to tree line, and the wider
canopy no longer comes from only one broadleaf and one conifer silhouette. The
editor builds, both runnable-map tests pass 1/1 with zero warnings or errors,
and all 14 focused M9 terrain/water audits pass.

This is an accepted incremental runtime fallback, not a photoreal promotion.
The vegetation remains visibly procedural, large bank benches remain smooth,
reach-specific species/litter/roots/deadwood/wetness are incomplete, water is
still dark and opaque, rapid-scale holes/rollers/aeration/VFX remain weak, and
all six external acceptance gates remain open. Exact hashes, metrics, placement
limits, reports, authority boundaries, and blockers are recorded in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_futaleufu_temperate_bank_ecology_v4_review.json`.

## Live Rapid Lace V1

The runnable Futaleufú Terminator map now lowers only the solver-derived masked
rapid-lace focus window from `0.12-0.72` to `0.08-0.58`. The result increases
visible rapid-foam vertices from 47 to 53 at the retained runtime start and
keeps five interior breaking sites; the captured station-189 m site has full
presentation coverage and the required 15 m edge clearance. The accepted calm
carrier material is byte-identical to the baseline. No color, roughness,
normal, transmission, opacity, surface geometry, collision, wet/dry mask,
hydraulics, bathymetry, buoyancy, or raft-force experiment is retained. The
existing masked foam layer and raft/crew pixel exclusion remain in force.

The equivalent Chilko bracket was rejected. Its current cooked window produced
zero interior breaking sites and zero visible rapid-foam vertices; all four
detected transitions were at the wet-mask boundary, including a strongest
candidate with zero coverage and zero edge clearance. Lowering the display
threshold could not create missing solver structure and could amplify the same
water/land edge that must remain suppressed, so `L_LavaCanyon` was restored to
the conservative `0.12-0.72` focus defaults. Chilko still needs a reviewed
interior Lava Canyon cooked field rather than a cosmetic substitute.

River-filtered regeneration now reuses the reviewed shared solver textures and
foam material without resaving them, making isolated map iteration safer. The
editor build, 42 focused Python contracts, both M9 river audits, the M8 shared
material audit, both P4 map-load gates, and P2 water/occlusion rendering pass;
P2 retains Unreal's existing `r.MotionVectorSimulation` warning. The new
Futaleufú frame still reads too pale and sheet-like for photoreal acceptance,
and all six guide, geospatial, hydraulic, ecology/art, water-VFX/occlusion, and
target-hardware gates remain open. Exact evidence, hashes, the rejected Chilko
diagnostic, and authority boundaries are in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/futaleufu_live_rapid_lace_v1_review.json`.

## Chilko Rapid-Approach Launch V1

The prior Chilko rejection correctly described the live surface at the old
launch, but its missing-input diagnosis was too broad. The committed Lava
Canyon low, median, and high cooked fields already contain a genuine
supercritical-to-subcritical transition near local station 300 m. Launching at
station 24 m clamped the 240 m live-water carrier to stations 0-240, so the
runtime could only see four shoreline-boundary candidates and correctly
rejected all of them.

`L_LavaCanyon` now launches at station 228 m. That is deep, subcritical water
and leaves 72 m of approach to the interpreted crux while placing the existing
solver jump inside the initial carrier. A regression test bilinearly samples
all three committed 2 m cooked fields onto the same 3 m runtime grid and
applies the production Froude, wetness, phase-tolerance, coverage, intensity,
and 15 m clearance contract. Every band exposes at least one interior site.
The real PIE map reports one active station-300 m site, coverage 1.0, 15 m
clearance, six visible rapid-foam vertices, and a visible rapid-foam mesh.
Shoreline candidates remain suppressed; no detection threshold was relaxed.

This is a scenario-framing correction, not new bathymetry or hydraulic
calibration. Cooked fields, wet/dry masks, water collision, buoyancy, and raft
forces are byte-identical. The retained live frame still reads pale and
sheet-like, with smooth banks, visibly procedural forest, incomplete local
geology/ecology, and weak spray/mist/entrained-air volume. Photoreal promotion
and all six external gates remain open. Exact metrics, hashes, evidence, and
authority boundaries are recorded in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_lava_canyon_rapid_approach_launch_v1_review.json`.

## Chilko Organic Shoreline V1

The runnable Lava Canyon map introduced a Chilko-only, source-Landscape-
grounded presentation layer for the visibly barren bank transition. Six
existing rights-reviewed CC0 rock morphologies place 3,600 small-to-medium
cobbles, while two project-owned opaque ground-cover morphologies place 4,200
short, non-shadowing patches. A deterministic 48-choice search grounds every
instance on both banks of its original station range, keeps it outside the active river
width, rejects wet or steep placements, and leaves terrain, collision,
bathymetry, hydraulics, buoyancy, and raft forces unchanged. All 7,800 targets
place with zero rejects; the maximum measured slope is 15.951 degrees.

The first far-bank/small-scale tuning passed the numeric gates but was rejected
because it did not visibly break up the guide-eye bank. The retained tuning
moves the layer toward the actual dry bank face while preserving solver-strip
clearance. In the identical `breaking_water_side` frame, the measured bank-band
green-dominant fraction rises from 0.168841 to 0.265534, edge fraction rises
from 0.130677 to 0.218952, and mean edge magnitude rises from 0.033148 to
0.048663. The upper bench now has readable short cover and irregular stone
silhouettes instead of an uninterrupted tan surface.

This is retained as a technical runtime improvement, not photoreal or B2 asset-
set promotion. The lower wet-bank bench remains broad and smooth; cover is
bright, stylized, repetitive, and not species-reviewed; rocks are generic
morphology donors rather than Lava Canyon geology; the forest, terrain,
atmosphere, water, VFX, hydraulic calibration, and raft/crew presentation remain
incomplete. All six external acceptance gates remain open. Exact placement
contracts, visual metrics, hashes, evidence, authority boundaries, and blockers
are recorded in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_organic_shoreline_v1_review.json`.

Subsequent V2 auditing found that V1's hard-coded placement range ended at
station 253 m even though the runnable coordinate map spans 0-600 m. The V1
review remains immutable evidence for its original camera and placement, but
its “complete route” wording is superseded by the correction below.

## Chilko Non-Repeating Wet Bank And Full-Reach Shoreline V2

The runnable Lava Canyon map now covers stations 2.5-597.5 m with the bounded
shoreline presentation layer. Gravel doubles to 7,200 six-form instances and
short ground cover doubles to 8,400 two-form instances so the corrected full
reach retains approximately the original local density. All 15,600 targets
place with zero rejects. Every instance is source-Landscape grounded, outside
the complete visible-water width, non-colliding, and excluded from terrain,
bathymetry, solver, hydraulic, buoyancy, and raft-force authority.

The Chilko Landscape material also replaces its single close-detail projection
with a world-space-selected 124/217-scale pair; the second projection is rotated
37 degrees. The existing seven non-harmonic world fields now choose between
those projections and drive thresholded wet-bank silt, gravel, and iron-oxide
patches. The graph remains Default Lit and has no world-position offset.

The station-300 `breaking_water_side` frame and a fixed bank-facing close-up
confirm that the earlier empty evidence bank now receives fine gravel, short
cover, and non-square color variation. The matched global bank-band edge
fraction changes from 0.220892 to 0.216543, so V2 is deliberately not claimed
as a numeric edge-density improvement. It is retained for the audited full-
reach correction and reduced square repetition, not as photoreal acceptance.

The lower DEM-scale bank profile is still broad and smooth; ground shading,
vegetation, and generic rock donors remain visibly synthetic; one oversized
rock silhouette is still apparent; and water, rapid VFX, atmosphere, exact
geology/ecology, and all six external reviews remain open. Exact parameters,
hashes, captures, test results, authority boundaries, and blockers are recorded
in `docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_nonrepeating_wet_bank_v2_review.json`.

## Chilko Optical And Shoreline Naturalism V3

The runnable Lava Canyon map now preserves its authored river-local optical
values instead of entering a cooked-field compatibility branch that silently
restored the older reflective defaults. A default-off shared live-water mask is
enabled only for Chilko and derives coverage from the existing sampled depth;
the redundant broad detail skin is suppressed there while the wet-cell-clipped
transmitting core, moving normals, and separately solver-masked rapid foam
remain. The change is presentation-only: cooked fields, wet/dry ownership,
bathymetry, collision, buoyancy, hydraulics, and raft forces are unchanged.

The full-reach 7,200-gravel and 8,400-ground-cover layer remains deterministic,
source-Landscape-grounded, non-colliding, and outside the solver strip. Chilko
now resolves a river-local muted vegetation material, bounds cover to 18-58 cm,
and changes the gravel population to mostly 8-28 cm stones, a smaller 28-62 cm
class, and a rare 65-85 cm class. Shared temperate material defaults remain
identity values, so Futaleufu presentation is unchanged. A Chilko-only lower-
energy photographic rig further restrains sun, skylight, and reflection
brightness without changing any physical authority.

Against the retained V2 `breaking_water_side` frame, water-band mean luminance
falls from 0.679885 to 0.637845, 95th-percentile luminance falls from 0.884324
to 0.835865, coverage above 0.90 falls 59.21%, and coverage above 0.95 falls
98.93%. The measured bank neon-green fraction falls 64.77%. In the matched bank
close-up, green-dominant coverage falls from 0.471736 to 0.319063 and the neon
fraction falls 37.74%.

The retained result passes the technical renderer, material, map-load, and
MapCheck contracts but fails photoreal promotion. A pale shallow-water band is
still visible on the far bank, foam remains repetitive and stroke-like, the
DEM-scale bank profile remains smooth, vegetation and rock donors are generic,
and rapid-scale entrained air, spray, mist, calibrated hydraulics, target-
hardware performance, and all six named external reviews remain open. Exact
hashes, captures, measurements, authority boundaries, and blockers are in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_optical_shoreline_naturalism_v3_review.json`.

## Shared Cold-Water Highlight Naturalism V1

The stable `L_Terminator` and `L_LavaCanyon` packages now advertise one
presentation-only cold-water highlight contract. Futaleufú receives Chilko's
reviewed 0.18 specular, 0.68 roughness, 0.05 fallback-sky strength, 0.55 ripple,
localized fallback reflection, turbulent slick-normal floor, -0.30 exposure,
55-degree sun yaw, and 0.65 corridor-reflection brightness. A first bracket
removed clipped highlights but also collapsed cold-water chroma; it was
rejected. The retained bracket restores river-local shallow, deep, and sky
blue separation without restoring the polished white/gold glare.

Across rows 260-719 of the identical 1280x720 Terminator camera, p95 luminance
falls from 0.888246 to 0.877031, >0.95 coverage falls from 0.001228 to
0.000022, and mean blue-minus-red rises from 0.027372 to 0.035525. Lava
Canyon's matched control changes by less than 0.0001 in mean luminance, p95,
and blue-minus-red. The retained maps still use their solver-owned wet-cell
cores, masks, rapid ownership, and forces; terrain, water topology, bathymetry,
collision, buoyancy, and hydraulics do not change.

This closes only the bounded highlight/color regression. Terminator still has
a broad pale center/left body and smooth standing-wave face; both rivers still
need observed foam, entrained air, spray/mist, shoreline microgeometry,
regional environment art, character/raft occlusion review, calibrated flows,
performance evidence, and all six external approvals. Exact captures, hashes,
thresholds, and blockers are in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_highlight_naturalism_v1_review.json`.

## Flexible Raft Review

Both rivers must exercise the flexible outer-tube contract in `unreal/Content/RaftSim/Raft/flexible_raft_tube_validation_plan.json`. A seated or high-siding passenger must depress the local tube and alter freeboard; current overtopping that tube must add recorded water load and roll moment; rock contact must support bounded indentation, wrap or pinch, recovery, and pressure-dependent response. Simulator evidence must distinguish a missed high-side flip or pin from a correctly timed save.

## Promotion Gate

Neither river is photoreal or production-playable until route, terrain, flow, rapid, rights, publication, guide, flexible-raft, art, hazard-readability, performance, and human lifelike review all pass. Procedural terrain, foliage, rocks, water detail, foam, spray, and mist may fill source gaps only when manifest-recorded and visibly review-gated; they may not fabricate authoritative geometry or hide physics failures.
