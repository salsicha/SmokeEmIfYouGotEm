# Chilko And Futaleufu Photoreal Goal

## Portfolio Decision

The active five-river production portfolio is:

1. South Fork American River, Chili Bar to Folsom Reservoir.
2. Colorado River through Grand Canyon, Lees Ferry to Pearce Ferry.
3. Pacuare River, Tres Equis to Siquirres.
4. Futaleufu River, Rio Azul Swinging Bridge to The Pasarela.
5. Chilko River, Chilko River Lodge to the Chilko-Taseko Junction.

Zambezi Batoka Gorge is now an additional active photoreal environment target and, with Futaleufu, forms the immediate environment priority. It remains outside the five-river runnable claim until authoritative full-reach terrain, centerline, route, guide, and review evidence pass. This priority change does not remove Chilko from the runnable portfolio or promote, delete, or rewrite any existing evidence.

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

The cordilleran-cypress V33 transition-path precursor now samples the V32 complementary source/HLOD handoff at 17 exact radial positions from 23.00 m through 27.00 m. It corrected an incomplete woody-material binding and proved that the current dynamic screen mask requires the unchanged source trunk geometry to use traditional raster: the Nanite source path leaked trunk and branches into HLOD-owned pixels. Two deterministic runs keep source, HLOD, and combined variation below 0.004557 percent, match the authored Bayer composite within 0.001411 percent, and bound transition overhead above ordinary camera-motion controls to 1.156684 percentage points. This retains a diagnostic path and renderer boundary, not a photoreal or production LOD. Same-world continuous motion with persistent view state, TAA history, motion vectors, target frame pacing, lit art, and desktop/VR profiling remains required.

V34 supplies that missing same-world diagnostic: three persistent source/HLOD/combined sequences each retain one world and TAA view state while moving from 23-27 m at a fixed 60 Hz simulation step, followed by endpoint settling. Independent runs reproduce all 147 frames within 0.000211 changed-pixel fraction at worst. Ending source coverage at 26 m and retaining ten HLOD-only moving frames reduces combined-to-HLOD history residue from 11.5889 percent to 2.4835 percent, then to 1.5829 percent after settling. The harness is retained, but the transition is not: the 4x4 Bayer pattern changes ownership in 6.25-percent ranks and causes a repeatable 4.3407 percentage-point spike above ordinary camera-motion controls, exceeding the unchanged 1.5-point limit. Replace it with a finer complementary mask or stable blue-noise sequence and rerun V34 before lit art or performance review. Fixed simulation pacing is not measured wall-clock performance, and the unlit frozen-WPO frames are not photoreal evidence.

## Flexible Raft Review

Both rivers must exercise the flexible outer-tube contract in `unreal/Content/RaftSim/Raft/flexible_raft_tube_validation_plan.json`. A seated or high-siding passenger must depress the local tube and alter freeboard; current overtopping that tube must add recorded water load and roll moment; rock contact must support bounded indentation, wrap or pinch, recovery, and pressure-dependent response. Simulator evidence must distinguish a missed high-side flip or pin from a correctly timed save.

## Promotion Gate

Neither river is photoreal or production-playable until route, terrain, flow, rapid, rights, publication, guide, flexible-raft, art, hazard-readability, performance, and human lifelike review all pass. Procedural terrain, foliage, rocks, water detail, foam, spray, and mist may fill source gaps only when manifest-recorded and visibly review-gated; they may not fabricate authoritative geometry or hide physics failures.
