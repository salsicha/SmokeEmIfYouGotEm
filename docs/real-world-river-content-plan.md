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

Workflow:

1. Generate automated rapid candidates from slope, constriction, roughness, and imagery texture.
2. Build a rapid review tool that shows DEM, aerial/satellite imagery, flowline, cross sections, and candidate tags.
3. Let a designer or river-domain reviewer classify each candidate: pool, riffle, wave train, technical rapid, hole, ledge, strainer risk, portage, access point.
4. Save rapid boundaries and feature annotations back into the scenario database.
5. Feed selected rapid segments into PyClaw/custom-C++ scenario generation.

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

Internally, each selection maps to a scenario package and parameter preset that can be run by PyClaw and the custom C++ solver.

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
- PyClaw reference run.
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
- Store rapid segments and hazard tags.

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
