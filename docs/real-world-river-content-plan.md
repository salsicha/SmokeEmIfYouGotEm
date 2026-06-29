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
- `physics/data/real_world/candidate_rivers.json`: first candidate river/region inventory.
- `physics/data/real_world/source_catalog.json`: source availability, licensing, attribution, and pipeline-use notes.
- `physics/data/real_world/rapid_review_labels.json`: manual review taxonomy for pools, riffles, wave trains, holes, ledges, laterals, eddies, eddy lines, strainers, portages, access points, boulder gardens, and constrictions.
- `physics/data/real_world/player_selection_model.json`: first player-facing region, river, section, season, flow, difficulty, and raft setup model.
- `physics/data/real_world/south_fork_american_chili_bar/source_manifest.json`: representative source manifest for the South Fork American River, Chili Bar to Coloma seed section.
- `physics/data/real_world/south_fork_american_chili_bar/river_course.json`: centerline stationing, approximate banks/cross-section offsets, width, gradient, constriction, roughness, and rapid candidate metadata.
- `physics/data/real_world/south_fork_american_chili_bar/flow_presets.json`: low, median, and high runnable seed bands.
- `physics/data/real_world/south_fork_american_chili_bar/rapid_candidates.geojson`: candidate rapid points derived from DEM-slope, constriction, roughness, boulder-density, imagery-texture, bend, guide-note, and access signals.
- `physics/data/real_world/south_fork_american_chili_bar/scenario/`: loadable shared `scenario2_5d` package for GeoClaw and the custom C++ solver path.
- `physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json`: first Unreal-ready corridor package manifest with terrain, imagery mask, centerline, bank, rapid, hazard, flow, and confidence artifact slots.
- `physics/data/real_world/south_fork_american_chili_bar/validation_matrix.json`: low, median, and high runnable flow smoke matrix. The existing PyClaw matrix is a legacy baseline; the active plan is to regenerate each band with GeoClaw and the C++ solver.

The seed package records metadata-ready fetch specs for 3DEP/DEM, 3DHP/NHD, OSM, NAIP, USGS/NWIS, NOAA/NWPS/National Water Model, and StreamStats. It does not vendor heavy lidar, imagery, guidebook text, or field media. Production extraction must replace the coarse seed measurements with pulled geospatial/hydrology data, reviewed aerial/satellite labels, and rights-cleared media.

Regenerate the seed source/scenario package:

```bash
python -m raftsim.examples.generate_real_world_scenario --write-full-package --output-dir outputs/real_world
```

The validation matrix is a recorded smoke-run result, not a static source-data export. Rebuild it with fresh GeoClaw and C++ solver outputs before accepting any real-world flow preset.

Generate one selected scenario:

```bash
python -m raftsim.examples.generate_real_world_scenario --flow-band high_runnable --difficulty advanced --output-dir outputs/real_world
```

Milestone 10 generated the first readiness gate artifacts. Its current decision is approved after shallow-cell-aware velocity/Froude comparison. Production Unreal work can begin with telemetry/replay playback, while live water, Chrono raft coupling, VR, contact integration, and richer real-world flow presets continue behind validation fixtures.

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
- `centerline.geojson`
- `cross_sections.geojson`
- `terrain_dem.tif` or normalized grid export
- `bank_masks.tif` / `water_masks.tif`
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
- `stitching`: reach-local grids with overlap/ghost zones or one stitched global grid with reach/drop IDs. The exported GeoClaw and C++ inputs must remain semantically identical.
- `validation_windows`: per-reach probes, cross sections, drop-entry/drop-exit windows, raft checkpoints, and whole-section conservation summaries.

Use discontinuities carefully. A drop can have an abrupt bed-elevation change, but the solver handoff cannot be a hidden impulse. Energy loss, turbulence, aeration, and recirculation should be represented with topography, roughness, hydraulic controls, and explicit source/damping fields that are visible to the comparison harness.

South Fork American should be the baseline content target for this package revision. Its first production pass should create low, median, and high runnable cascading packages for the seed section, then validate GeoClaw and the custom C++ solver against the same reach/drop sequence.

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
2. Build a rapid review tool that shows DEM, aerial/satellite imagery, flowline, cross sections, and candidate tags.
3. Let a designer or river-domain reviewer classify each candidate: pool, riffle, wave train, technical rapid, hole, ledge, strainer risk, portage, access point.
4. Save rapid boundaries and feature annotations back into the scenario database.
5. Group reviewed labels into cascading reaches and drop transitions.
6. Feed selected reach/drop sequences into GeoClaw/custom-C++ scenario generation.

The first version can use manual/semi-automated labeling. Machine learning for rapid detection should wait until enough labeled examples exist.

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
4. Use PCG to populate vegetation, rocks, gravel, driftwood, debris, and access features from geospatial masks and biome rules.
5. Use Nanite for high-detail rocks, canyon walls, terrain detail meshes, and dense foliage where supported.
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
- Add overlap/ghost zones or a stitched global grid with reach/drop IDs.
- Validate conservation and raft continuity across reach boundaries.

### Milestone D: Seasonal Flow Model

- Pull gauge and modeled flow data.
- Build seasonal presets and difficulty-flow mapping.
- Make fluid parameters adaptive to river/season/flow/difficulty.

### Milestone E: River Selection UX

- Build data model for region, river, section, season, flow, difficulty, and raft setup.
- Surface data confidence, hazards, season window, and training value.

### Milestone F: Unreal Photoreal Corridor

- Use latest stable UE5 rendering stack, Nanite foliage, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara, Substrate/material layering, and water visualization.
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
