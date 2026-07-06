# Photoreal River Environment Production Plan

## Goal

Construct complete, photorealistic Unreal river environments for the first three runnable rivers:

- South Fork American River, Chili Bar to Coloma
- Colorado River, Lees Ferry to Diamond Creek rowing prototype
- Pacuare River, lower Pacuare planning corridor

Each river environment must be driven by traceable river maps, seasonal or release-driven flow levels, aerial/satellite imagery, reviewed terrain and hydrography, and rights-reviewed visual reference. Procedural generation is expected for terrain dressing, foliage, rock scatter, debris, foam cues, wetness masks, lighting variants, and placeholder art until imported or first-party assets are approved.

## Source Rules

- Official/open geospatial and hydrology sources are preferred over guidebook or social sources.
- Third-party photos, social posts, guidebook text, and footage are link-only unless explicit redistribution and game-use rights are recorded.
- Social media can inform fidelity review only through public links, creator/date/platform notes, approximate station or reach, observed flow context, and rights status. Do not scrape, download, vendor, or train on those assets without explicit rights.
- Aerial/satellite data must preserve provider, acquisition date, CRS, product id, license/terms URL, and processing version.
- Generated environments must remain traceable back to source manifests and validation overlays.
- Procedural dressing must not hide hazards, rescue targets, water-readability cues, or physics validation failures.

## Canonical Outputs

- `unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json`: source and capture manifest for the three river environments.
- Per-river source manifests under `physics/data/real_world/**/source_manifest.json`.
- Unreal preview maps under `/Game/RaftSim/Maps/EnvironmentPreviews/` once generated in the editor.
- Screenshot evidence under `docs/environment-captures/photoreal_river_previews/`.
- Future imported source data under per-river `terrain`, `imagery`, `hydrography`, `hydrology`, `field_media`, and `review` folders, with large binary assets moved to LFS when they become necessary.

## River Source Stack

### South Fork American

Use the existing South Fork corridor package as the baseline. Fill it with production-quality source pulls:

- Maps and terrain: USGS 3DEP, The National Map product queries, state or county lidar if higher quality is available.
- Hydrography: USGS 3DHP/NHD fallback, OSM only for supplemental access/bridge context.
- Flow levels: USGS Water Data station `USGS-11445500`, including daily and instantaneous discharge plus stage when available.
- Aerial imagery: NAIP where available, plus Landsat/Sentinel for historical season comparison and water/vegetation masks.
- Review media: rights-cleared guide footage, first-party field captures, Wikimedia/Flickr Creative Commons candidates only after per-item license review, and public social links as reference-only annotations.

### Colorado River

Treat this as a big-water rowing/oar-rig environment:

- Maps and terrain: USGS 3DEP, USGS/NPS/Grand Canyon corridor references, NPS river trip and river-mile context, USGS Grand Canyon Monitoring and Research Center sources where suitable.
- Hydrography: USGS 3DHP/NHD fallback, NPS route context, river-mile stationing.
- Flow levels: USGS `USGS-09380000` at Lees Ferry, USGS `USGS-09402500` near Grand Canyon, and Bureau of Reclamation Glen Canyon Dam release context.
- Aerial imagery: Landsat/Sentinel for canyon-scale season and water-color history, plus approved U.S. imagery products where available.
- Review media: NPS/public-domain or rights-cleared photos where terms permit, guide/oarsman footage by permission, and public social links as reference-only annotations.

### Pacuare

Treat this as a rain-fed tropical gorge environment until authoritative hydrology is secured:

- Maps and terrain: Costa Rica SNIT/IDECORI layers first, OpenTopography/global DEMs as fallback, SRTM/Copernicus DEM if permitted by source terms.
- Hydrography: SNIT official hydric resource layers where available, HydroSHEDS for global river network and basin context, OSM only as planning seed.
- Flow levels: keep relative clear-season, rainfed-runnable, rainy-season-high, and flash-response bands until Costa Rica gauge/rainfall authority review is complete.
- Rainfall and weather: IMN/MINAE weather and rainfall context, ICE/hydrometeorological sources if public access and rights are confirmed.
- Protected-area review: SINAC/MINAE and SNIT protected-area layers before publishing detailed route packages.
- Aerial imagery: Copernicus Sentinel and Landsat for vegetation, river color, and cloud-aware seasonal review.
- Review media: first-party field captures or explicit outfitter/guide permissions; public social links remain reference-only.

## Unreal Construction Plan

1. Create source-controlled preview recipes for all three rivers from the manifest.
2. Generate one Unreal preview level per river with procedural terrain bands, river surface, bank/canyon walls, boulders, foliage proxies, lighting, camera, and source/capture metadata.
3. Capture downstream guide-seat screenshots for each preview level.
4. Replace proxy terrain and visual masks with real DEM, hydrography, imagery, and flow-derived masks as source pulls are reviewed.
5. Replace proxy rocks/foliage/materials with free/open, first-party, procedural, or paid-release-gated assets only after manifest approval.
6. Iterate until guide-seat screenshots read as lifelike while keeping hazards, swimmer/rescue targets, and solver water cues visible.

## Review Gates

- Source manifest completeness: maps, terrain, hydrography, imagery, flow, media, guide feedback, CRS, rights, and confidence.
- Seasonal flow sanity: low/median/high or release/rainfall bands are backed by gauges, release data, rainfall data, guide review, or a clear placeholder block.
- Photoreal fidelity: landscape, rock, foliage, wetness, lighting, water color, foam, spray, mist, and atmospheric depth match reviewed references.
- Gameplay readability: hazards, eddies, swimmer rescue targets, lines, and high-side moments remain readable.
- Engine evidence: each river has a guide-seat downstream screenshot captured from Unreal, then later a flythrough/video capture.
- Performance evidence: desktop and VR budgets are captured before promotion.

## Current Blockers

- First-pass river `.umap` assets now exist under `unreal/Content/RaftSim/Maps/EnvironmentPreviews/`.
- Rendered guide-seat procedural blockout captures now exist under `docs/environment-captures/photoreal_river_previews/`, but they are not lifelike production evidence yet.
- The first South Fork official source slice now exists at `physics/data/real_world/south_fork_american_chili_bar/production_source_pull_manifest.json`: historical USGS `11445500` daily discharge, TNM NHD product metadata, TNM DEM/NAIP zero-hit diagnostics, a small USGS 3DEP GeoTIFF sample, and a small USDA/APFO NAIP aerial sample.
- The South Fork preview now uses the USDA/APFO NAIP sample as a source-derived visible terrain overlay in Unreal. This proves the imagery-to-editor path, but it is a small smoke-test raster rather than a complete orthomosaic or terrain material pass.
- The first Colorado/Lees Ferry official source slice now exists at `physics/data/real_world/colorado_river_grand_canyon_rowing/production_source_pull_manifest.json`: USGS `09380000` and `09402500` daily discharge histories through July 4, 2026, a small USGS 3DEP GeoTIFF sample, and a small USDA/APFO NAIP aerial sample. The Colorado preview uses that NAIP sample as a source-derived visible canyon terrain overlay.
- The existing default map path `/Game/RaftSim/Maps/L_RaftSimBoot` has no committed level asset yet.
- Colorado and Pacuare still need real geospatial pulls, hydrology review, guide review, and rights-cleared field/reference media.
- South Fork has the only solver corridor package, but its terrain, imagery, and field media are still representative placeholders rather than production pulls.
- Production photoreal review is blocked on reviewed DEM/aerial imports plus rights-cleared or first-party river environment assets for terrain materials, wet rocks, foliage, water surface detail, foam, mist, spray, and lighting.

## Current Unreal Evidence

- South Fork American: `/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview`, capture `docs/environment-captures/photoreal_river_previews/american_south_fork_guide_seat_downstream.png`.
- South Fork source data: `physics/data/real_world/south_fork_american_chili_bar/production_source_pull_manifest.json` records the initial official pull; this is enough to prove provenance plumbing but not enough for production terrain/imagery.
- South Fork Unreal source layer: `physics/data/real_world/south_fork_american_chili_bar/imagery/usda_naip_chili_bar_sample_512.png` is sampled into visible terrain overlay tiles for the generated preview map; `physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_sample_256.tif` is recorded in the generated capture manifest for the next heightfield-conditioning pass.
- Colorado River: `/Game/RaftSim/Maps/EnvironmentPreviews/L_ColoradoGrandCanyon_PhotorealPreview`, capture `docs/environment-captures/photoreal_river_previews/colorado_river_guide_seat_downstream.png`.
- Colorado source data: `physics/data/real_world/colorado_river_grand_canyon_rowing/production_source_pull_manifest.json` records the initial official pull; `imagery/usda_naip_lees_ferry_sample_512.png` is sampled into visible canyon terrain overlay tiles, and `terrain/usgs_3dep_lees_ferry_sample_256.tif` is recorded for the next canyon heightfield-conditioning pass.
- Pacuare River: `/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview`, capture `docs/environment-captures/photoreal_river_previews/pacuare_guide_seat_downstream.png`.
- These captures verify editor automation, camera placement, generated valley terrain meshes, curved river ribbons, foam/hydraulic cue strips, boulder bars, foliage proxies, and per-river light/fog variants. They must be replaced by source-derived or rights-cleared photoreal passes before the goal is complete.
