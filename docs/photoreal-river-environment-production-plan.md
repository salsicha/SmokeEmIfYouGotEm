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
- `physics/data/real_world/reference_media_link_manifest.json`: link-only candidate media manifest for official/public pages, Wikimedia/Flickr review seeds, and public social/search seeds. It records reference leads only; no third-party media is downloaded or cleared for game use by this file.
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

Initial source slice:

- `physics/data/real_world/pacuare_river_costa_rica/production_source_pull_manifest.json` records the first Pacuare source pull.
- Copernicus DEM GLO-30 public COG tiles `N09_00_W084_00` and `N10_00_W084_00` now cover the draft WGS84 bounds. They are source terrain artifacts only; clipping, reprojection, hydrologic conditioning, and Unreal heightfield import remain open.
- NASA GIBS MODIS/Terra true-color samples were pulled for five dates. The April 2, 2025 sample has the best visible rainforest texture, is retained at 512px for cloud-screening evidence, and has a larger 1024px request feeding the active Unreal preview drape; the other dates are retained as cloud-screening evidence.
- `physics/src/raftsim/geospatial_preview.py` now generates deterministic Pacuare preview drapes that blend the selected NASA GIBS image with Copernicus DEM relief, filling cloud gaps with DEM-derived rainforest shading. The active Unreal preview uses `imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png`; the 512px output remains reproducible provenance. This improves source-derived preview continuity but is still not production photoreal imagery.
- The same utility emits `terrain/pacuare_dem_relief_preview_1024.png`, which the Unreal preview generator samples for Pacuare bank/gorge height perturbation. The retained 512px relief remains for provenance. The river channel is masked so water readability remains intact; this is a preview-only step before proper heightfield import.
- The same utility now also emits `terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png`, a 1009x1009 16-bit grayscale Unreal Landscape import-test candidate normalized from the Copernicus DEM tiles with min/max elevation recorded in `terrain/pacuare_copernicus_dem_corridor_heightfield_manifest.json`. This is review-gated and not production terrain until CRS, clipping, void review, hydrologic conditioning, channel burning, and guide review are complete.
- `unreal/Content/RaftSim/River/pacuare_heightfield_import_test.json` links that heightfield to the Unreal geospatial import pipeline as a disabled, review-gated Landscape import-test contract. It records the required CRS, clipping, conditioning, channel-burning, access/protected-area, guide-review, and import/export validation gates before it can replace the current procedural terrain.
- Pacuare now has review-gated official-source research manifests for terrain, aerial imagery, hydrology/gauge search, rainfall context, protected-area/source-rights review, and access/conservation constraints. These files attach SNIT/IDECORI, IMN, ICE, MINAE/Direccion de Agua, SINAC/MINAE, Copernicus, Landsat, NASA GIBS, HydroSHEDS, and OpenTopography leads without promoting unreviewed social or third-party media into game assets.
- The utility also emits preview-only USGS 3DEP relief PNGs for the South Fork and Colorado sample pulls, letting the generated Unreal terrain use source-derived bank/canyon perturbation while full DEM conditioning and landscape import remain open.
- The generated Unreal preview maps now sample the three review-gated 1009px heightfield candidates into bounded bank, valley, and canyon preview geometry while still using procedural river-channel masks. This gives the screenshots more source-shaped terrain before full Landscape import, but the heightfield candidates remain disabled for production replacement until CRS/transform review, full-corridor clipping/tiling, void review, hydrologic conditioning, channel burning, access/protected-area checks, and guide review pass.
- A first-party procedural detail pass now adds terrain-conforming canyon strata, rainforest/foothill leaf-litter bands, wet-rock accents, and deterministic talus/pebble bars for all three preview maps. These layers are rights-safe proxy dressing generated from code and engine primitives; they must be replaced or promoted only after production asset, material, and guide-review gates pass.
- The river ribbon mesh now uses `M_RaftSim_VertexColorWaterPreview`, a first-party procedural vertex-color water material with shallow/deep tinting and subtle along-flow variation. Crude foreground raft proxies are disabled in generated preview maps and hidden in capture automation, preview cameras use fixed manual exposure, and capture automation performs a warm-up render before pixel readback so water review is not polluted by placeholder geometry, exposure shifts, or first-frame material warm-up artifacts until production raft art is ready. This improves the current preview screenshots but does not replace the future production water shader, reflections, solver-driven surface detail, spray, mist, or foam.
- OpenTopography SRTMGL1 was probed and returned an API-key requirement, so that path remains available only after key and terms review.

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
- Engine evidence: each river has a guide-seat downstream screenshot plus a raft-hidden river-eye downstream environment-review screenshot captured from Unreal, then later a flythrough/video capture.
- Performance evidence: desktop and VR budgets are captured before promotion.

## Current Blockers

- First-pass river `.umap` assets now exist under `unreal/Content/RaftSim/Maps/EnvironmentPreviews/`.
- Rendered guide-seat and raft-hidden river-eye procedural blockout captures now exist under `docs/environment-captures/photoreal_river_previews/`, but they are not lifelike production evidence yet.
- The first South Fork official source slice now exists at `physics/data/real_world/south_fork_american_chili_bar/production_source_pull_manifest.json`: historical USGS `11445500` daily discharge, TNM NHD product metadata, TNM DEM/NAIP zero-hit diagnostics, a small USGS 3DEP GeoTIFF sample, and a small USDA/APFO NAIP aerial sample.
- The South Fork preview now uses the larger USDA/APFO NAIP `imagery/usda_naip_chili_bar_corridor_sample_1024.png` as a denser terrain-conforming source-drape mosaic and `terrain/usgs_3dep_chili_bar_corridor_relief_preview_1024.png` as preview-only bank/valley terrain relief in Unreal. This proves larger official imagery and relief plumbing, but the inputs are still corridor samples rather than complete orthomosaic, conditioned DEM, or terrain material passes.
- South Fork now also has `terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png`, a 1009x1009 16-bit grayscale Unreal Landscape import-test candidate generated from the larger USGS 3DEP corridor sample, plus `unreal/Content/RaftSim/River/south_fork_heightfield_import_test.json` as a disabled, review-gated import contract.
- The first Colorado/Lees Ferry official source slice now exists at `physics/data/real_world/colorado_river_grand_canyon_rowing/production_source_pull_manifest.json`: USGS `09380000` and `09402500` daily discharge histories through July 4, 2026, a small USGS 3DEP GeoTIFF sample, and a small USDA/APFO NAIP aerial sample. The Colorado preview uses that NAIP sample as a denser terrain-conforming canyon source-drape mosaic.
- The Colorado preview now uses the larger USDA/APFO NAIP `imagery/usda_naip_lees_ferry_corridor_sample_1024.png` as the active source drape and `terrain/usgs_3dep_lees_ferry_corridor_relief_preview_1024.png` as preview-only canyon bank relief in Unreal, while full Grand Canyon corridor terrain tiling, river-mile stationing, and heightfield import remain pending.
- Colorado now also has `terrain/usgs_3dep_lees_ferry_corridor_heightfield_1009.png`, a 1009x1009 16-bit grayscale Unreal Landscape import-test candidate generated from the larger USGS 3DEP Lees Ferry corridor sample, plus `unreal/Content/RaftSim/River/colorado_heightfield_import_test.json` as a disabled, review-gated import contract.
- The first Pacuare public/global source slice now exists at `physics/data/real_world/pacuare_river_costa_rica/production_source_pull_manifest.json`: Copernicus DEM GLO-30 public COG tiles for the draft bounds, a NASA GIBS MODIS/Terra April 2, 2025 true-color preview sample selected from five cloud-screened dates, a larger 1024px request for the selected date, deterministic NASA-plus-DEM preview drapes, and an OpenTopography API-key gate probe. The Pacuare preview now uses the 1024px derived drape as a denser terrain-conforming rainforest source-drape mosaic.
- `physics/data/real_world/reference_media_link_manifest.json` now records the first link-only reference media seed list for all three rivers: official/public pages, Wikimedia/Flickr review searches, and public social/search seeds. These are fidelity-review leads only and remain blocked from asset use until item-level rights, attribution, date, reach, observed flow/weather context, and permission status are recorded.
- The preview generator now keeps source provenance out of the rendered guide-seat frame and records it in JSON instead. It also uses a lit preview material, computed procedural mesh normals, vertex-color terrain and water variation, deterministic wet-bank/shoreline dressing, first-party procedural strata/leaf-litter/wet-rock/talus detail, denser terrain-conforming source-drape mosaics, PCG sample foliage meshes where available, denser low-bank understory/scrub placeholders, subtle current-streak proxies, and curved procedural foam/wave/eddy-line ribbons. This improves depth and review readability but is still not production photoreal vegetation, rock, water, or terrain material work.
- The existing default map path `/Game/RaftSim/Maps/L_RaftSimBoot` has no committed level asset yet.
- Local Unreal content inventory found no committed Megascans/Quixel/Fab or photogrammetry environment assets for rocks, foliage, cliffs, water, foam, mist, or terrain materials. The current previews rely on generated geometry, source-derived rasters, RaftSim preview materials, and engine/plugin PCG sample meshes, so lifelike screenshots now require approved production asset/data imports or first-party procedural equivalents.
- Colorado and Pacuare still need full-corridor geospatial processing, hydrology review, guide review, and rights-cleared field/reference media.
- South Fork has the only solver corridor package, but its terrain, imagery, and field media are still representative placeholders rather than production pulls.
- Production photoreal review is blocked on reviewed DEM/aerial imports plus rights-cleared or first-party river environment assets for terrain materials, wet rocks, foliage, water surface detail, foam, mist, spray, and lighting.

## Current Unreal Evidence

- South Fork American: `/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview`, guide-seat capture `docs/environment-captures/photoreal_river_previews/american_south_fork_guide_seat_downstream.png`, river-eye capture `docs/environment-captures/photoreal_river_previews/american_south_fork_river_eye_downstream.png`.
- South Fork source data: `physics/data/real_world/south_fork_american_chili_bar/production_source_pull_manifest.json` records the initial official pull; this is enough to prove provenance plumbing but not enough for production terrain/imagery.
- South Fork Unreal source layer: `physics/data/real_world/south_fork_american_chili_bar/imagery/usda_naip_chili_bar_corridor_sample_1024.png` is sampled into a denser terrain-conforming source-drape mosaic for the generated preview map, `physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_corridor_relief_preview_1024.png` and `physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png` are sampled into preview terrain geometry, and `physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_corridor_sample_512.tif` is recorded for the next heightfield-conditioning pass.
- Colorado River: `/Game/RaftSim/Maps/EnvironmentPreviews/L_ColoradoGrandCanyon_PhotorealPreview`, guide-seat capture `docs/environment-captures/photoreal_river_previews/colorado_river_guide_seat_downstream.png`, river-eye capture `docs/environment-captures/photoreal_river_previews/colorado_river_river_eye_downstream.png`.
- Colorado source data: `physics/data/real_world/colorado_river_grand_canyon_rowing/production_source_pull_manifest.json` records the initial official pull plus larger active corridor samples; `imagery/usda_naip_lees_ferry_corridor_sample_1024.png` is sampled into a denser terrain-conforming canyon source-drape mosaic, `terrain/usgs_3dep_lees_ferry_corridor_relief_preview_1024.png` and `terrain/usgs_3dep_lees_ferry_corridor_heightfield_1009.png` are sampled into preview canyon terrain geometry, and `terrain/usgs_3dep_lees_ferry_corridor_sample_512.tif` is recorded for the next canyon heightfield-conditioning pass.
- Pacuare River: `/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview`, guide-seat capture `docs/environment-captures/photoreal_river_previews/pacuare_guide_seat_downstream.png`, river-eye capture `docs/environment-captures/photoreal_river_previews/pacuare_river_eye_downstream.png`.
- Pacuare source data: `physics/data/real_world/pacuare_river_costa_rica/production_source_pull_manifest.json` records the initial public/global pull plus the larger active preview source path; `imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_1024.png` is sampled into a denser terrain-conforming rainforest source-drape mosaic, `terrain/pacuare_dem_relief_preview_1024.png` and `terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png` are sampled into preview terrain geometry, and `terrain/copernicus_dem_glo30_N09_W084.tif` plus `terrain/copernicus_dem_glo30_N10_W084.tif` are recorded for the next gorge heightfield-conditioning pass.
- All three runnable rivers now have disabled, review-gated heightfield import-test contracts linked from `unreal/Content/RaftSim/River/geospatial_import_pipeline.json`. They are the next terrain replacement path, but none can replace procedural preview terrain until source CRS/working CRS transforms, full corridor clipping/tiling, void review, hydrologic conditioning, channel burning, access/protected-area review, and guide review pass.
- These captures verify editor automation, guide-seat and raft-hidden river-eye camera paths, generated valley terrain meshes, terrain-conforming source drapes, lit and vertex-color preview materials, deterministic wet-bank/shoreline dressing, first-party procedural strata/leaf-litter/wet-rock/talus detail, vertex-color water gradients, curved river ribbons, subtle current-streak proxies, procedural foam/wave/eddy-line ribbons, boulder bars, PCG sample foliage and bank understory/scrub placeholders, and per-river light/fog variants. They must be replaced by source-derived or rights-cleared photoreal passes before the goal is complete.
