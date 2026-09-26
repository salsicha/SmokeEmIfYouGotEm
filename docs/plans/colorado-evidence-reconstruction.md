# Colorado Grand Canyon evidence-based reconstruction

Requested 2026-09-06. Queued after completion and validation of the South Fork
reconstruction; not started or accepted. Do not switch away from unfinished
South Fork work merely because its source data has been downloaded.

## Objective

Reconstruct the Colorado run's rapids, including boulder locations, rock
islands, channel constrictions, drops and banks, as closely as available
online evidence permits. Then reconcile water physics and geometry with the
reconstructed environment.

## Work and acceptance

1. Audit the Colorado scene's reach, geographic origin, named-rapid locations,
   coordinate units and existing terrain provenance before modifying it.
2. Research authoritative elevation, LiDAR, orthophoto, river-survey and
   bathymetric resources. Verify coverage, acquisition dates, datums, units,
   resolution and licensing. Compare dated photos and footage at known flow
   levels where available.
3. Reconstruct rapids individually using fixed landmarks and captured rock
   geometry. Preserve evidence and uncertainty for each feature. Do not label
   guessed submerged shapes or random boulder scatter as surveyed geometry.
4. Use one consistent reconstruction for visible terrain/rocks, collision,
   riverbed and hydraulic boundaries. Re-cook flows against that geometry;
   check conservation, wet/dry banks, recirculation, crest locations and raft
   interaction. Do not retain incompatible old cooked fields.
5. Compare actual in-engine boat-height and overhead views, plus animated
   runs, with reference evidence. Check shoreline stability, surface
   continuity, collision and measured performance before acceptance.

Public footage is reference-only unless its license permits shipping.
Unknown submerged geometry remains an explicit estimate. This is a game
reconstruction, not navigation or river-safety guidance.

## User-requested next river

On 2026-09-06 the user queued Pacuare after Colorado is completed and
validated. See `pacuare-evidence-reconstruction.md`. Finish Colorado's playable
scene, collision and water-physics validation before starting Pacuare.

## Scene audit and source research (2026-09-26)

Audit (step 1), from repository data only:

- The shipping Hance scene is interpreted, not geographic. Its solver bed is a
  planning cook with authored features (44 seeded boulders, an imposed 0.008
  mean slope, drop/hole/eddy parameters in
  `scenario_hance/window_manifest.json`), and the 600 x 320 m visual terrain
  adds a deterministic "debris fan desert canyon" infill around a 78 m solver
  strip (`terrain/hance_visual/hance_visual_terrain_manifest.json`). None of it
  is survey geometry.
- The repository's Colorado DEM, NAIP and NHD extracts all cover Lees Ferry
  (the put-in, near river mile 0), not Hance Rapid (river mile ~76.7). There is
  no Hance-area elevation, imagery or bathymetry in the repository.

Authoritative public-domain sources found (step 2; not downloaded):

- **Measured channel bathymetry:** USGS/GCMRC "Channel Mapping of the Colorado
  River in Grand Canyon National Park, Arizona", river miles 61-88 (includes
  Hance): April 2011 and April-May 2014 surveys, multibeam and singlebeam
  echosounders combined into a DEM with an uncertainty-polygon layer and a bed
  sediment map. CC0. 2014 release: https://doi.org/10.5066/P99SSSU6 ; 2011:
  https://data.usgs.gov/datacatalog/data/USGS:5f43d93a82ce4c3d1222d335
- **Corridor topography:** USGS "DEM and DSM data for the Colorado River
  corridor in Grand Canyon NP and Glen Canyon NRA (2002, 2009, 2013, 2021)",
  1 m, DSMs for all four years and a DEM for 2021, 15 zones, ellipsoid heights
  (a geoid conversion to NAVD88 is required). CC0.
  https://doi.org/10.5066/P93Y4FMJ
- **Imagery:** "Four Band Multispectral High Resolution Image Mosaic of the
  Colorado River Corridor, Arizona - 2013", 20 cm, May 2013 overflight,
  0.36 m RMSE against 91 control points.
  https://www.sciencebase.gov/catalog/item/588bac04e4b0ad67324029c5

This is better evidence than South Fork had: the bed under water is measured,
not inferred. The 2014 bathymetry release is four small 7z archives on
ScienceBase item 5f45276582ce4c3d122516ea: DEM 4.87 MB, hillshade 2.08 MB, bed
sediment classification 2.05 MB, fiducial polygons 12 KB (plus 12 KB FGDC
metadata). The corridor DEM/DSM release is split into six child items (DEM 2021;
DSM 2002/2009/2013/2021; accuracy) by zones 1-15; the zone holding river mile
~76.7 and its size are not stated on the landing page. Next step needs the
user's explicit permission to download the bathymetry archives, then the Hance
zone of the 2021 DEM and the 2013 imagery tiles once their sizes are read.
Until then Colorado stays queued behind South Fork.
