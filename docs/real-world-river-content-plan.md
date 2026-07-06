# Real-World River Content And Seasonal Flow Plan

## Goal

Build playable rivers from real geospatial and hydrological data, then present them as photorealistic Unreal Engine waterways. The user should eventually choose:

- River
- Section / rapid
- Season
- Flow level
- Difficulty target
- Raft/crew setup

Those choices should drive both the visual scene and the 2.5D water/raft physics parameters.

## Milestone 9 Seed Implementation

Milestone 9 now has a committed seed pipeline for the first real-world river content pass. It is intentionally small enough for source control and automated tests, while preserving the provenance and validation shape needed for later production data pulls.

Implemented artifacts:

- `physics/src/raftsim/real_world.py`: candidate river inventory, source catalog, South Fork American representative fetch specs, centerline station samples, channel indicators, rapid candidate clustering, rapid review labels, seasonal flow bands, adaptive solver parameters, player selections, Unreal corridor metadata, and solver-neutral scenario generation.
- `physics/src/raftsim/examples/generate_real_world_scenario.py`: command-line generator for a selected river/flow/difficulty scenario or the full seed package.
- `physics/schemas/source_manifest.schema.json`: frozen source-manifest contract for geospatial, hydrology, imagery, guide/reference, field-media, solver, and Unreal provenance.
- `physics/data/real_world/candidate_river_inventory.json`: first inventory package with selection criteria, primary section, source-catalog linkage, and per-section source-manifest status.
- `physics/data/real_world/candidate_rivers.json`: first candidate river/region inventory.
- `physics/data/real_world/source_catalog.json`: source availability, licensing, attribution, and pipeline-use notes.
- `physics/data/real_world/rapid_review_labels.json`: manual review taxonomy for pools, riffles, wave trains, holes, ledges, laterals, eddies, eddy lines, strainers, portages, access points, boulder gardens, and constrictions.
- `physics/data/real_world/player_selection_model.json`: first player-facing region, river, section, season, flow, difficulty, and raft setup model.
- `physics/data/real_world/south_fork_american_chili_bar/source_manifest.json`: representative source manifest for the South Fork American River, Chili Bar to Coloma seed section.
- `physics/data/real_world/pacuare_river_costa_rica/source_manifest.json`: review-gated source manifest for the Pacuare River third runnable target.
- `physics/data/real_world/pacuare_river_costa_rica/flow_presets.json`: relative rain-fed flow bands that block numeric discharge values until Costa Rica hydrology, rainfall, and guide review are complete.
- `physics/data/real_world/south_fork_american_chili_bar/river_course.json`: centerline stationing, approximate banks/cross-section offsets, width, gradient, constriction, roughness, and rapid candidate metadata.
- `physics/data/real_world/south_fork_american_chili_bar/course_elevation_extraction.json`: prototype course/elevation extraction with station samples, cumulative drop, local gradient, width summary, cross-section prototypes, and provenance notes.
- `physics/data/real_world/south_fork_american_chili_bar/rapid_review_flow_difficulty_mapping.json`: first label-to-flow/difficulty tuning map for review labels, flow-response curves, expected raft outcomes, and generated solver parameter rows.
- `physics/data/real_world/south_fork_american_chili_bar/flow_presets.json`: low, median, and high runnable seed bands.
- `physics/data/real_world/south_fork_american_chili_bar/rapid_candidates.geojson`: candidate rapid points derived from DEM-slope, constriction, roughness, boulder-density, imagery-texture, bend, guide-note, and access signals.
- `physics/data/real_world/south_fork_american_chili_bar/rapid_review_editor_workflow.json`: first one-view rapid review/editor workflow contract with required DEM/lidar, aerial/satellite imagery, flowline, cross-section, gauge-history, source-manifest, candidate-tag, and guide-note layers.
- `physics/data/real_world/south_fork_american_chili_bar/scenario/`: loadable shared `scenario2_5d` package for GeoClaw and the custom C++ solver path.
- `physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json`: first Unreal-ready corridor package manifest with terrain, imagery mask, centerline, bank, rapid, hazard, flow, and confidence artifact slots.
- `physics/data/real_world/south_fork_american_chili_bar/validation_matrix.json`: low, median, and high runnable flow smoke matrix. The existing PyClaw matrix is a legacy baseline; the active plan is to regenerate each band with GeoClaw and the C++ solver.

The seed package records metadata-ready fetch specs for 3DEP/DEM, 3DHP/NHD, OSM, NAIP, USGS/NWIS, NOAA/NWPS/National Water Model, and StreamStats. The candidate inventory package marks the South Fork American Chili Bar to Coloma section as the primary drafted source-manifest section, with Colorado and Pacuare carried as drafted but review-gated follow-on targets. It does not vendor heavy lidar, imagery, guidebook text, or field media. Production extraction must replace the coarse seed measurements with pulled geospatial/hydrology data, reviewed aerial/satellite labels, and rights-cleared media. The course/elevation extraction prototype is intentionally derived from the seed station set first; before production use, it must be regenerated from CRS-recorded DEM/lidar, flowline, bank, water-mask, and cross-section measurements.

Regenerate the seed source/scenario package:

```bash
python -m raftsim.examples.generate_real_world_scenario --write-full-package --output-dir outputs/real_world
```

The validation matrix is a recorded smoke-run result, not a static source-data export. Rebuild it with fresh GeoClaw and C++ solver outputs before accepting any real-world flow preset.

Generate one selected scenario:

```bash
python -m raftsim.examples.generate_real_world_scenario --flow-band high_runnable --difficulty advanced --output-dir outputs/real_world
```

Milestone 10 generated the first readiness gate artifacts. Its current decision is approved after shallow-cell-aware velocity/Froude comparison. Production Unreal work can begin with telemetry/replay playback, while live water, selected raft/contact runtime coupling, VR, contact integration, and richer real-world flow presets continue behind validation fixtures.

## Engine And Rendering Direction

Use the latest stable Unreal Engine 5.x release available when Unreal production begins. As of the current planning pass, Epic's public documentation is on UE 5.8, so the Unreal plan should expect modern UE5 features and re-check exact feature support at the Unreal readiness gate.

Target UE5 feature set:

- Nanite for photogrammetry rocks, canyon walls, large instanced debris, terrain details, and high-density scene geometry.
- Nanite foliage for dense riverbank vegetation, forested canyons, animated foliage, and large open vistas.
- Nanite landscapes, Nanite splines, and Nanite tessellation/displacement where they help terrain, banks, trails, gravel bars, and eroded rock detail.
- Lumen for dynamic time-of-day, canyon bounce lighting, wet-rock reflections, and changing weather/season light.
- Virtual Shadow Maps for high-resolution shadows in large, dynamically lit waterways.
- World Partition for long river corridors and streaming multiple river sections.
- Procedural Content Generation (PCG) for bank vegetation, rocks, gravel, driftwood, debris, foam-line accents, camps, and access points.
- Water System for visual water surfaces, shoreline blending, and material integration, but not as authoritative physics.
- Niagara for spray, mist, foam bursts, paddle splashes, rain, water droplets, and rescue effects.
- Substrate/material-layering workflows for wet rock, rubber, helmets, PFDs, muddy banks, foam, and translucent/aerated water.
- Cesium for Unreal or equivalent geospatial tooling for real-world scale, WGS84 positioning, 3D Tiles, terrain, imagery, and georeferenced scene setup.

The custom C++ water solver remains authoritative for water fields. Unreal rendering systems visualize the solver and geospatial content; they do not replace the physics model.

## Geospatial Data Sources

Use official/open sources first, then commercial or field-captured data only when needed.

Primary U.S. sources:

- USGS 3D Elevation Program (3DEP): DEMs, lidar-derived terrain, and high-resolution topography.
- USGS 3D Hydrography Program (3DHP) and legacy NHD/NHDPlus where needed: river/stream flowlines, waterbodies, drainage areas, catchments, and hydro network context.
- USGS The National Map: access point for elevation, hydrography, map layers, and related geospatial products.
- USGS Water Data for the Nation / NWIS APIs: historical and real-time gauge stage/discharge.
- USGS StreamStats: drainage basin characteristics and streamflow statistics where gauges are sparse.
- NOAA National Water Prediction Service / National Water Model: forecast and modeled streamflow context.
- USDA NAIP aerial imagery: high-resolution U.S. aerial imagery for banks, boulder gardens, channels, roads, access points, and vegetation.
- USGS Landsat: long-term seasonal and historical satellite imagery.
- Copernicus Sentinel-2: global multispectral imagery for river color, sediment, water masks, seasonal vegetation, and wide-area change detection.

Optional / supplemental sources:

- State lidar portals and local GIS datasets.
- OpenStreetMap for access roads, trails, bridges, land use, and named features.
- Commercial photogrammetry or aerial imagery when licensing allows.
- Field survey data, guide GPS tracks, drone imagery, and reference video.

## Canonical Geospatial Formats

Use standard geospatial formats for source/editor data, then convert into deterministic solver packages and Unreal-facing assets.

| Layer | Canonical format | Notes |
| --- | --- | --- |
| Source manifest and provenance | JSON | Record rights, CRS, source URLs, confidence, processing version, and redistribution notes. |
| Simple vector exchange | GeoJSON | Centerlines, banks, cross sections, rapid polygons, validation annotations, and editor-friendly interchange. |
| Larger multi-layer GIS workspace | GeoPackage (`.gpkg`) | Use when a river section outgrows loose GeoJSON layers or needs multi-layer review in desktop GIS. |
| Terrain, DEMs, water masks, foam masks, and raster confidence layers | GeoTIFF / Cloud Optimized GeoTIFF | Preserve georeferencing for elevation and imagery-derived masks. |
| Lidar or dense point clouds | LAS/LAZ or COPC | Use only when raw point clouds are needed beyond processed DEM tiles. |
| Gauge and flow history | Normalized JSON first; CSV/Parquet for larger time series | Preserve gauge id, parameter code, units, timestamp, timezone, retrieval date, and transfer-function context. |
| Solver package | Versioned JSON plus `.npy`/`.npz` arrays | Deterministic bed, state, reach/drop IDs, probes, features, flow presets, and comparison windows for GeoClaw/C++. |
| River validation annotations | GeoJSON plus JSON manifest | Geometry anchors plus footage timecodes, gauge context, imagery dates, guide feedback, expected outcomes, confidence, and rights. |
| Unreal corridor package | JSON/GeoJSON metadata plus converted terrain, masks, splines, data assets, and optional 3D Tiles | Preserve source references and local-to-WGS84 transforms while producing engine-ready assets. |

Avoid Shapefile as a canonical format. It can be imported from outside sources, but it should be converted into GeoJSON or GeoPackage because Shapefile loses modern metadata, has awkward field limits, and is brittle for provenance-heavy workflows.

## River Course And Elevation Extraction

Pipeline:

1. Select candidate river section from 3DHP/NHD/OSM flowlines and known rafting guidebooks or curated internal lists.
2. Pull DEM/lidar terrain from 3DEP or state lidar.
3. Reproject all data into a common local coordinate system for modeling.
4. Extract river centerline and downstream stationing.
5. Snap or refine the line against DEM-derived valley/thalweg indicators and visible water masks.
6. Estimate banks from imagery, hydrography polygons, DEM slope breaks, and water masks.
7. Generate cross sections at regular intervals and at known features.
8. Derive longitudinal gradient, local slope, constrictions, pool/drop spacing, channel width, boulder density, and likely bed roughness.
9. Store raw source references, processing version, coordinate transforms, and confidence scores.

Output:

- `river_course.json`
- `course_elevation_extraction.json`
- `centerline.geojson`
- `cross_sections.geojson`
- `terrain_dem.tif` or Cloud Optimized GeoTIFF plus normalized solver grid export
- `bank_masks.tif` / `water_masks.tif`
- `rapid_annotations.geojson` and `river_validation_annotations.geojson`
- Optional `river_workspace.gpkg` for larger reviewed multi-layer sections
- `source_manifest.json`

## Variable Cascading River Model

For California Sierra pool-and-drop rivers, the real-world extraction should produce a cascading 2.5D scenario package instead of a single uniform river strip. The package should represent the river as an ordered sequence of pools, tongues, steep drops, hydraulic controls, wave trains, boulder gardens, eddies, and recovery sections.

This is a good fit for the simulator because it matches the structure guides actually read on many California runs:

- Pools store water, slow the raft, allow regrouping, and set the tailwater depth for the next drop.
- Constricted tongues and ledges convert elevation head into velocity, waves, holes, and impact risk.
- Boulder gardens and rough beds add lateral deflection, drag, pin risk, and localized standing waves.
- Eddy lines and recovery zones create guide-relevant steering decisions after each drop.
- Variable slope lets the physics model produce distinct transitions instead of one averaged rapid.

The package should add these production fields:

- `reaches`: downstream station range, local coordinate transform, length, slope profile, width profile, bank geometry, bed roughness, boulder density, vegetation/debris indicators, and confidence score.
- `drop_transitions`: upstream pool ID, downstream pool/reach ID, crest station, bed-elevation fall, ramp or ledge length, tailwater control, expected hydraulic type, recirculation/aeration proxy, eddy recovery window, hazard tags, and review status.
- `pool_controls`: depth estimate, residence/storage behavior, inflow/outflow relationship, eddy/recirculation areas, and low-flow/high-flow changes.
- `stitching`: reach-local grids with overlap/ghost zones for authoring and streaming, plus mandatory stitched whole-window validation outputs with reach/drop IDs. The exported GeoClaw and C++ inputs must remain semantically identical.
- `validation_windows`: per-reach probes, cross sections, drop-entry/drop-exit windows, raft checkpoints, and whole-section conservation summaries.

Use discontinuities carefully. A drop can have an abrupt bed-elevation change, but the solver handoff cannot be a hidden impulse. Energy loss, turbulence, aeration, and recirculation should be represented with topography, roughness, hydraulic controls, and explicit source/damping fields that are visible to the comparison harness.

South Fork American should be the baseline content target for this package revision. Its first production pass should create low, median, and high runnable cascading packages for the seed section, then validate GeoClaw and the custom C++ solver against the same reach/drop sequence.

The second real-world river target should be a Colorado River rowing route rather than another paddle-raft-only section. This route should introduce an oar rig/rowing frame, larger-volume current reading, longer canyon pacing, rowing-specific ferry/pull/back-row controls, and passenger safety decisions over longer recovery distances. Because this is a rowing route, it should use direct manual rowing controls and should not expose passenger paddle voice commands. Its source manifest, flow bands, corridor package, guide review, and validation annotations should be drafted only after the South Fork baseline workflow is proven.

The alpha prototype for that route now lives in `unreal/Content/RaftSim/River/colorado_rowing_route_editor_pass.json` and is surfaced through `unreal/Content/RaftSim/UI/river_selection_catalog.json`. The prototype is intentionally review-gated: all Colorado flow bands remain placeholder planning data until gauge history, rights-cleared guide notes, field-media timecodes, and geospatial corridor pulls replace them. The route exposes direct manual oar inputs, disables passenger paddle voice commands, records large-volume water-reading cues for tongues, laterals, boils, eddy fences, and hydraulics, and tracks canyon pacing checkpoints with longer swimmer rescue windows. Guide-review annotations must capture flow-specific rowing lines, large-volume feature outcomes, and long-water rescue plans before the route can become a production-playable river.

The third runnable river target should be the Pacuare River in Costa Rica. Treat it as a distinct tropical rainforest/gorge whitewater package rather than another U.S. geodata-first section. The draft artifacts now live in `physics/data/real_world/pacuare_river_costa_rica/source_manifest.json`, `physics/data/real_world/pacuare_river_costa_rica/flow_presets.json`, and `unreal/Content/RaftSim/River/pacuare_river_third_target_editor_pass.json`. They intentionally use planning bounds and relative rain-fed flow bands only: numeric discharge ranges, solver packages, and Unreal corridor exports remain blocked until Costa Rica hydrology/gauge-source review, rainfall/flash-rise review, protected-area/source-rights review, and rights-cleared guide/field-media annotations replace the placeholders.

The current photoreal environment source plan is `unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json`; the production workflow is described in `docs/photoreal-river-environment-production-plan.md`. That plan promotes river maps, seasonal/release/rainfall flow levels, aerial/satellite imagery, rights-reviewed guide and media references, and procedural generation into a single Unreal environment track for South Fork American, Colorado River, and Pacuare. Pacuare now has a larger active 1024px NASA GIBS plus Copernicus DEM source-preview drape, a 1024px DEM relief preview, production-import placeholder derivatives, a generated Unreal-preview centerline/stationing scaffold, an official service access plan for SNIT/IDECORI plus Direccion de Agua/SINIGIRH source review, an archived SNIT node layer-list summary, and selected SNIT per-layer metadata wired into the review manifests. The Direccion de Agua/SINIGIRH WMS capabilities metadata, SNIT layer lists, and selected per-layer SNIT metadata are archived and summarized, but they remain metadata-only: no official geometry, station records, map tiles, WFS features, station time series, masks, or media are imported yet. Pacuare remains preview-only until higher-resolution cloud-screened imagery, official hydrography, hydrology/rainfall, protected-area/access review, and guide/media review are attached. Social media and outfitter media are reference-only links until explicit reuse rights are recorded. `physics/data/real_world/reference_media_review_queue.json` is the station-aware handoff from link leads to review work: it records visual questions, candidate source IDs, flow context, annotation outputs, and rights status without downloading or promoting third-party media. Each runnable river now also has link-only `review/production_import_pilot/reference_annotations.geojson` and `field_media/production_import_pilot/rights_manifest.json` scaffolds with review-only stationing-derived points so editors can place review targets and track rights before any photo, footage, caption, thumbnail, comment, or audio becomes an asset source.

## Rapid Identification From Aerial And Satellite Imagery

Identify candidate rapids by combining terrain, hydrography, image analysis, and human review.

Signals:

- Increased gradient over short downstream distance.
- Channel constrictions.
- Boulder gardens and exposed rocks.
- Foam/whitewater texture in aerial imagery.
- Persistent standing-wave or hydraulic-looking surface patterns.
- Sharp bends with outside-bank current.
- Visible eddies, gravel bars, islands, and ledges.
- Access points, named rapids, bridges, guidebook notes, and GPS/video references.
- Alternating pool/drop signatures: lower-gradient wider pools upstream/downstream of short steep gradient breaks, bedrock shelves, constrictions, or boulder bars.

Workflow:

1. Generate automated rapid candidates from slope, constriction, roughness, and imagery texture.
2. Build a rapid review and validation annotation editor that shows DEM, aerial/satellite imagery, flowline, cross sections, gauge history, reference footage links, guide feedback, and candidate tags.
3. Let a designer or river-domain reviewer classify each candidate: pool, riffle, wave train, technical rapid, hole, ledge, strainer risk, portage, access point.
4. Let reviewers annotate station ranges, reach/drop IDs, polygons, points, and raft lines with footage timecodes, gauge/date context, aerial imagery dates, guide notes, confidence, expected surf/flush/pin/flip outcomes, and rights/provenance status.
5. Save rapid boundaries, validation annotations, and feature annotations back into the scenario database.
6. Group reviewed labels into cascading reaches and drop transitions.
7. Feed selected reach/drop sequences into GeoClaw/custom-C++ scenario generation.

The first version can use manual/semi-automated labeling. Machine learning for rapid detection should wait until enough labeled examples exist.

## River Validation Annotation Editor

The rapid review tool should grow into a game/editor-integrated level-design tool for rapid fidelity review. It must let designers and river-domain reviewers attach evidence directly to locations in the river rather than keeping footage, gauge notes, imagery, and guide feedback in loose documents.

Annotation anchors:

- River station, centerline distance, local/world coordinate, reach ID, drop-transition ID, pool/control ID, and optional polygon/line/point geometry.
- Flow context: gauge source, discharge/stage, observation date/time, flow band, flow percentile, season, transfer-function confidence, and release/snowmelt/rain context where known.
- Visual context: aerial/satellite imagery source, acquisition date, tile/product ID, water mask, foam/whitewater texture note, boulder/bank/ledge observation, and confidence.
- Media context: reference footage/still ID, timecode, camera location/direction where known, licensing/review status, and whether the media can be redistributed or only referenced internally.
- Guide feedback: expected line, hazard notes, scout notes, commercial/local running advice, flow-specific changes, and reviewer confidence.
- Validation target: expected water feature behavior, raft outcome class, surf/flush/pin/flip risk, high-side/brace/line counterplay, and accepted tolerance or review status.

The first workflow contract is generated by `build_rapid_review_editor_workflow()` and written as `rapid_review_editor_workflow.json` by `write_real_world_seed_package()`. It defines one-view layers, panels, per-candidate review items, evidence references, cross-section summaries, gauge context, editable fields, save targets, and export targets for Python scenario generation, GeoClaw/C++ validation reports, and Unreal data assets.

The South Fork alpha expansion contract is `unreal/Content/RaftSim/River/south_fork_alpha_content_expansion.json`. It links reviewed rapid candidates into longer scout/eddy/rapid/recovery-pool chains, adds shoulder-season and high-flow variants, defines commercial-training through expert linked-run difficulty presets, and records guide fidelity notes that require flow context, evidence references, rights review, and human guide signoff before any new flow or route is promoted to authoritative playable content.

Unreal corridor metadata now carries a `fidelity_review_overlays` section that tells the editor how to display annotation pins/spans/polygons, stitched solver fields, raft transition checkpoints and future trajectories, rendered water/foam/spray cues, audio emitters, and expected surf/flush/pin/release/flip outcomes in the same review mode.

The editor should export text-first JSON/GeoJSON annotation packages that can be consumed by Python scenario generation, GeoClaw/C++ validation reports, and Unreal data assets. Heavy footage, imagery, guidebook text, or third-party media should be referenced through source manifests unless rights allow vendoring. During game-engine fidelity review, the same annotations should appear as viewport pins, station spans, polygons, overlays, and comparison panels next to GeoClaw/C++ fields, raft trajectories, and rendered water/foam/audio cues.

## Seasonal Flow Research

Each playable river/section should have a flow profile built from real data where available.

Data sources:

- Gauge daily values and instantaneous values from USGS Water Data/NWIS.
- Stage/discharge rating curves where available.
- NOAA/NWPS/National Water Model forecasts and modeled reaches.
- StreamStats or regional hydrology estimates for ungauged reaches.
- Snowpack, rainfall, reservoir release calendars, and local boating/guiding references where relevant.
- Historical satellite/aerial imagery dates matched to gauge values.

Per river section, derive:

- Typical runnable season windows.
- Monthly/weekly percentile flows: low, median, high, flood.
- User-facing difficulty bands at flow ranges.
- Label-specific flow-response curves, such as sticky holes peaking only in the flow bands where guide/footage evidence says they should, shallow/boulder hazards becoming more prominent at low flows, and high-flow features washing out or strengthening according to reviewed evidence.
- Gauge-to-section transfer function if the nearest gauge is upstream/downstream.
- Stage-to-width/depth estimates for the scenario grid.
- Flow confidence score.

Season presets should be data-backed:

- Spring runoff
- Summer commercial season
- Late-summer low water
- Fall rain event
- Winter/off-season, where relevant
- Custom flow, unlocked for sandbox/testing

## Adaptive Fluid Parameters

The selected river, season, flow level, and difficulty should drive solver and raft parameters.

Inputs:

- Discharge or normalized flow percentile
- Stage estimate
- Channel width/depth estimate
- Bed slope
- Roughness / boulder density
- Water temperature proxy
- Sediment/turbidity proxy
- Difficulty override selected by the user

Adaptive outputs:

- Boundary inflow and outflow conditions.
- Initial water depth and momentum.
- Manning/roughness or equivalent friction.
- Effective turbulence/aeration fields.
- Hole retention strength.
- Wave train amplitude and spacing.
- Lateral wave forcing.
- Rapid-review flow/difficulty mapping rows that expose the derived gameplay and validation parameters to designers.
- Boil/upwelling proxy strength.
- Eddy strength and eddy-line shear.
- Shallow grounding risk.
- Strainer/hazard activation.
- Raft drag, paddle catch, and buoyancy/damping modifiers where justified.

Difficulty should not simply scale speed. It should modify scenario selection and setup:

- Beginner: lower flow band, more recovery eddies, fewer unavoidable holes, wider clean lines.
- Intermediate: median runnable flow, clearer feature consequences, moderate recovery windows.
- Advanced: higher or technical flow bands, stronger hydraulics, tighter lines, stronger eddy lines, more pin/surf consequences.
- Expert: high-consequence flows only after validation and safety/readability checks.

## User Selection Model

The player-facing river picker should be data-backed but readable.

Selection hierarchy:

1. Region
2. River
3. Section
4. Season
5. Flow level
6. Difficulty
7. Raft/crew setup

Each option should show:

- River class / difficulty estimate
- Flow range and gauge source
- Season window
- Rapid count and named/key rapids
- Main hazards
- Length and estimated run time
- Visual biome
- Data confidence
- Training value

Internally, each selection maps to a scenario package and parameter preset that can be run by GeoClaw and the custom C++ solver.

## Unreal Content Pipeline

1. Import geospatial terrain and hydro data into a source-data workspace.
2. Convert terrain and river corridor into Unreal-ready assets, landscape tiles, or 3D Tiles.
3. Use World Partition for long corridors and section streaming.
4. Use PCG to populate highly detailed, immersive vegetation, rocks, gravel, driftwood, debris, camps, trails, and access features from geospatial masks, biome rules, and reviewed reference.
5. Use Nanite for high-detail rocks, canyon walls, terrain detail meshes, and dense foliage where supported, pushing landscapes and foliage as close to photorealistic as target hardware and gameplay readability allow.
6. Use Lumen and Virtual Shadow Maps for dynamic seasonal lighting and photoreal canyon/forest shading.
7. Use water materials, foam masks, Niagara spray/mist, and solver debug textures to visualize the custom C++ water field.
8. Keep the water visual layer synchronized to solver fields: depth, velocity, turbulence, aeration, foam, and hazard tags.

## Validation And Review

Each real-world river section must pass:

- Source-data manifest completeness.
- Coordinate and scale validation.
- Terrain/elevation sanity checks.
- River centerline and bank alignment review.
- Rapid candidate review.
- Seasonal flow model review.
- Reach/drop sequence review for pool-and-drop structure, transition geometry, and section-boundary confidence.
- GeoClaw reference run.
- Custom C++ solver comparison run.
- Raft outcome review across selected season/difficulty presets.
- Unreal visual readability review.

## Milestones

### Milestone A: Data Source Inventory

- List target rivers and regions.
- Confirm data availability for 3DEP/3DHP, imagery, gauges, flow history, and access information.
- Record licensing and attribution requirements.

### Milestone B: River Course And Terrain Extraction

- Extract centerline, DEM, banks, cross sections, gradient, constrictions, and roughness indicators.
- Produce solver-neutral geospatial scenario inputs.

### Milestone C: Rapid Identification

- Build automated candidate detection from slope/constriction/imagery texture.
- Add manual review and feature annotation.
- Store rapid segments, pool segments, drop transitions, hazard tags, and review confidence.

### Milestone C2: Cascading Scenario Segmentation

- Segment the selected river section into ordered reaches and drop transitions.
- Encode reach-local slope, roughness, width, pool depth, tailwater controls, and drop geometry.
- Add reach-local overlap/ghost zones and stitched whole-window validation outputs with reach/drop IDs.
- Validate conservation and raft continuity across reach boundaries.

### Milestone D: Seasonal Flow Model

- Pull gauge and modeled flow data.
- Build seasonal presets and difficulty-flow mapping.
- Make fluid parameters adaptive to river/season/flow/difficulty.
- Current South Fork source slice: `physics/data/real_world/south_fork_american_chili_bar/production_source_pull_manifest.json` records historical USGS `11445500` daily discharge, CDEC CBR/A25 flow context, a review-gated flow-band comparison at `hydrology/production_import_pilot/flow_band_review.json`, access/publication source leads at `review/production_import_pilot/access_publication_sensitivity_review.json`, TNM NHD product metadata, a review-gated NHD HU8 `18020129` bbox source extract, a derived South Fork mainstem candidate with preview metric stationing and cross-section seed lines, generated production-import draft hydrography overlays at `hydrography/production_import_pilot/centerline.geojson`, `banks.geojson`, and `cross_sections.geojson`, a first NAIP/DEM preview-mask alignment diagnostic, TNM DEM/NAIP zero-hit diagnostics, retained smoke-test USGS/USDA samples, and larger active official USGS 3DEP/USDA NAIP corridor samples. The flow-band review compares the current low/median/high planning presets to the attached 30-day CBR window, recording 25 local days peaking at or above 900 cfs, 9 days peaking at or above 1600 cfs, and 0 days reaching 3000 cfs; broader seasonal windows, A25 X-flag/routing review, legal signoff, and guide validation still block preset promotion. The access/publication review records California State Parks Marshall Gold Discovery evidence, an El Dorado County GIS lead, three station review zones, required access/sensitive-location/evacuation annotations, and a rejected BLM legacy URL; exact access geometry, parcel/public-private land status, current restrictions, sensitive-location screening, and guide/local approval still block detailed map or screenshot publication. The Unreal preview automation now samples the larger NAIP export into a terrain-conforming source-drape mosaic, uses the larger derived 3DEP relief preview for preview terrain, and records `terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png` plus `unreal/Content/RaftSim/River/south_fork_heightfield_import_test.json` for review-gated Landscape import testing. The NHD extract supplies official flowline/waterbody context, the mainstem candidate supplies a single review overlay, and stationing/cross-section seed files now supply production-import draft edit scaffolding, but the diagnostic confirms current preview masks are not acceptance evidence; production CRS review, direction confirmation, bank/cross-section work, stronger NAIP/DEM alignment, and guide validation remain open before replacing seed hydrography.
- Current Colorado source slice: `physics/data/real_world/colorado_river_grand_canyon_rowing/production_source_pull_manifest.json` records USGS `09380000` and `09402500` daily discharge histories through July 4, 2026, an official Reclamation Glen Canyon/Lake Powell daily Total Release series through July 5, 2026, a review-gated release-band comparison, NPS access/publication source leads at `review/production_import_pilot/access_publication_sensitivity_review.json`, a review-gated stitched NHD HU8 Lees Ferry source overlay, a derived exact-graph Colorado mainstem candidate with preview metric stationing, cross-section seeds, a first NAIP/DEM preview-mask alignment diagnostic, an NHD-aligned editor water-prior mask, generated production-import draft hydrography overlays, retained Lees Ferry smoke-test USGS/USDA samples, and larger active official USGS 3DEP/USDA NAIP corridor samples. `hydrology/production_import_pilot/usbr_glen_canyon_release_context.json` compares the release series to the USGS gauges and derives initial water-year 2026 preview release-band candidates, while `hydrology/production_import_pilot/release_band_review.json` records that water-year 2026 to date has 194 days at or above 8000 cfs, 0 days at or above 12000 cfs, and 0 days at or above 18000 cfs; final flow visuals still need explicit unit/terms confirmation, hourly/subdaily release behavior, river-mile travel-time review, sandbar/wet-bank masks, and guide/oarsman approval. The access/publication review records NPS River Trips / Permits, Noncommercial River Trip Helpful Links, Lees Ferry to Diamond Creek overview, and linked Noncommercial River Trip Regulations PDF leads, plus Lees Ferry launch, route camp/beach/sensitive-context, and Diamond Creek take-out review zones; exact launch/take-out geometry, camps/beaches, sensitive resources, permit/legal language, media reuse, screenshot publication, and oarsman approval still block detailed route packages. `hydrography/nhd_hu8_lees_ferry_bbox_extract_manifest.json` records TNM NHD HU8 products `14070006`, `14070007`, and `15010001`, 505 flowline features, 20 support features, 59 named Colorado River hits, Paria/Cathedral Wash context, and HUC12 crossings; `hydrography/nhd_hu8_lees_ferry_mainstem_candidate_manifest.json` then removes two duplicate HU8-overlap segments and orders 57 unique named Colorado River segments into a no-snap 145-vertex review line; `hydrography/nhd_hu8_lees_ferry_mainstem_stationing_candidate.json` adds 244 preview 100-meter station samples and river-left normals; `hydrography/nhd_hu8_lees_ferry_cross_section_seed_manifest.json` adds 123 fixed-width review lines for future bank/sandbar edits; `hydrography/nhd_hu8_lees_ferry_naip_dem_alignment_diagnostic.json` samples those station/cross-section seeds against the preview water/vegetation masks and DEM relief, finding 219 station samples and 109 cross-section centers inside the current pilot bbox; `imagery/production_import_pilot/nhd_mainstem_water_prior_manifest.json` records the blurred stationing raster for future mask generation; and `hydrography/production_import_pilot/hydrography_draft_manifest.json`, `centerline.geojson`, `banks.geojson`, and `cross_sections.geojson` repackage the Colorado stationing and cross-section seeds into editor-ready overlays with 145 centerline vertices, two bank-offset review lines, and 123 cross-section review lines. These are official source context, editor scaffolds, and review triage only until river-mile stationing, banks, sandbars, release-aware wet-bank classes, and oarsman/geospatial review are attached. The Unreal preview automation now samples the larger NAIP export into a terrain-conforming canyon source-drape mosaic, uses the larger derived 3DEP relief preview for preview terrain, and records `terrain/usgs_3dep_lees_ferry_corridor_heightfield_1009.png` plus `unreal/Content/RaftSim/River/colorado_heightfield_import_test.json` for review-gated Landscape import testing.
- Current Pacuare source slice: `physics/data/real_world/pacuare_river_costa_rica/production_source_pull_manifest.json` records Copernicus DEM GLO-30 tiles, NASA GIBS/Copernicus preview drapes and masks, a retained MODIS/GIBS cloud-screened scene index at `imagery/production_import_pilot/cloud_screened_scene_index.json`, a cloud/shadow diagnostic at `imagery/production_import_pilot/cloud_shadow_review.json`, production-import placeholder derivatives, Costa Rica hydrology/rainfall/protected-area source leads, archived Direccion de Agua/SINIGIRH WMS capabilities metadata, archived SNIT node layer-list metadata, selected SNIT per-layer metadata, rainfall/station review at `hydrology/production_import_pilot/rainfall_station_review.json`, discharge/stage station review at `hydrology/production_import_pilot/discharge_or_stage_station_review.json`, flash-response review at `hydrology/production_import_pilot/flash_response_review.json`, and now `hydrography/production_import_pilot/preview_centerline_scaffold.geojson` plus `preview_stationing_scaffold.json`. The scene index keeps April 2, 2025 as the active preview seed and records March 8, 2025 as the lowest simple cloud-like metric, but all candidates remain coarse MODIS/GIBS references. The SNIT summaries identify metadata-only candidate layers for Direccion de Agua aforos/hydrologic units, IMN rainfall climatology, SENARA rain stations/recharge, SINAC protected-area/forest/wetland context, and selected CRS/terms review; no features, map tiles, station time series, masks, or geometry have been imported. The rainfall/station review summarizes three IMN precipitation layers, two SENARA station layers, and one SENARA recharge context layer; the discharge/stage review records `DA_AFOROS`, `JASEC_ESTACIONES_HIDROMETRICAS`, and `DA_UNIDADES_HIDROLOGICAS` candidates; and the flash-response review links those leads to basin/recharge context while keeping rainfall-to-stage lag, unsafe-flow criteria, rescue readability, evacuation constraints, and guide/outfitter validation blocked. `review/production_import_pilot/protected_area_publication_sensitivity.json` and `review/production_import_pilot/access_and_conservation_policy.json` now convert SINAC/SNIT/SENARA metadata and access constraints into no-publish annotation, flow-dependent access review, and guide/conservation signoff gates; they still import no protected-area, access, evacuation, rescue, or sensitive-location geometry. The scaffold is generated from the deterministic Unreal Pacuare preview curve with 129 vertices and 184 station samples for annotation placement and procedural rainforest dressing only; it is not official hydrography, banks, wetted width, access stationing, or solver geometry.

### Milestone E: River Selection UX

- Build data model for region, river, section, season, flow, difficulty, and raft setup.
- Surface data confidence, hazards, season window, and training value.

### Milestone F: Unreal Photoreal Corridor

- Use latest stable UE5 rendering stack, Nanite foliage, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara, Substrate/material layering, and water visualization.
- Use `RaftSim.CreatePhotorealEnvironmentPreviewMaps` and `RaftSim.CapturePhotorealEnvironmentPreviews` to generate and capture current source-draped preview evidence for South Fork American, Colorado River, and Pacuare under `/Game/RaftSim/Maps/EnvironmentPreviews/` and `docs/environment-captures/photoreal_river_previews/`; these previews remain non-photoreal until full-corridor terrain, imagery, assets, and guide-reviewed annotations are promoted.
- Treat the current generated valley terrain, river ribbons, foam/hydraulic cues, boulder bars, foliage proxies, and light/fog variants as review blockouts only. Promotion to photoreal production requires reviewed DEM/aerial imports and rights-cleared or first-party terrain, rock, foliage, water-detail, mist/spray, and raft assets.
- Validate performance against desktop/VR targets.

## Reference Sources To Re-check

These are planning references, not vendored dependencies. Re-check versions, licenses, quotas, coverage, and platform support before production decisions.

- Epic Unreal Engine Nanite documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine
- Epic Unreal Engine Lumen documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine
- Epic Unreal Engine World Partition documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine
- Epic Unreal Engine PCG documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-in-unreal-engine
- Epic Unreal Engine Virtual Shadow Maps documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine
- Epic Unreal Engine Water System documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/water-system-in-unreal-engine
- Epic Unreal Engine Niagara documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/niagara-visual-effects-in-unreal-engine
- Cesium for Unreal: https://cesium.com/platform/cesium-for-unreal/
- USGS 3D Elevation Program: https://www.usgs.gov/3d-elevation-program
- USGS 3D Hydrography Program: https://www.usgs.gov/3d-hydrography-program
- USGS The National Map: https://www.usgs.gov/programs/national-geospatial-program/national-map
- USGS Water Services / NWIS APIs: https://waterservices.usgs.gov/
- USGS Water Data for the Nation: https://waterdata.usgs.gov/nwis
- USGS StreamStats: https://www.usgs.gov/streamstats
- NOAA National Water Prediction Service / National Water Model products: https://www.weather.gov/owp/operations
- USDA NAIP aerial imagery: https://www.fsa.usda.gov/resources/aerial-photography
- USGS Landsat: https://www.usgs.gov/landsat-missions
- Copernicus Data Space / Sentinel access: https://dataspace.copernicus.eu/
