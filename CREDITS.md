# Credits

Per-item provenance, licenses, and hashes are recorded in intake manifests throughout the repository (the authoritative record). This file summarizes the third-party sources used. Entries are added as assets/data are integrated; regenerate against the manifests before each release.

## Engine and libraries

- **Unreal Engine 5.8** — © Epic Games, Inc., under the Unreal Engine EULA (not part of this repository).
- **Python libraries** — NumPy (BSD-3), pytest (MIT), Matplotlib (PSF-based), Clawpack/GeoClaw (BSD-3), rasterio (BSD-3).

## Art assets

- **MetaHuman** production guide/crew — generated with Epic's UE 5.8 MetaHuman
  tools and used under the [Epic Content License Agreement](https://www.unrealengine.com/eula/content)
  and [MetaHuman terms](https://www.unrealengine.com/eula/mhc). Editable and optimized
  source assets remain local-only; released characters are incorporated into cooked builds.
- **Poly Haven** (polyhaven.com) — CC0 models and textures (evaluated tree/rock/material assets; per-item manifests under the asset intake records).
- **ambientCG** (ambientcg.com) — CC0 PBR materials (external review sets).
- CC0 scanned rock set (six-variant Nanite rocks; manifest-recorded).
- **MakeHuman Community Hair02** — `elvs_grump_hair`, `elvs_braided_rows`,
  `elvs_short_side_do`, and the retained-but-unshipped `elvs_braid_bun` by
  **Elvaerwyn**, licensed under
  [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
  Source and per-file hashes are recorded in
  `unreal/SourceArt/RaftSim/Characters/CC0Production/Hair/Hair02/source_manifest.json`.

## Geospatial and hydrological data

- **USGS** — 3DEP elevation, NHD hydrography, gauge records (public domain, courtesy U.S. Geological Survey).
- **USDA NAIP** — aerial imagery (public domain).
- **Copernicus DEM GLO-30 & Sentinel-2** — © European Union, Copernicus programme; ESA open data terms.
- **Natural Resources Canada** — MRDEM elevation (Open Government Licence – Canada).
- **GeoBC / BC Data Catalogue** — Freshwater Atlas hydrography (Open Government Licence – British Columbia).
- **Environment and Climate Change Canada** — hydrometric station data.
- **California DWR / CDEC** — river flow data.
- **OpenStreetMap** — © OpenStreetMap contributors, ODbL (used for discovery/seeding only, per source policy).

## River knowledge

Rapid names, classifications, and river-mile references are factual information compiled from published guidebooks, agency publications, and outfitter descriptions; sources are cited link-only in `physics/data/real_world/named_rapid_source_catalog.json`. No third-party prose, maps, or photographs are reproduced in this repository.
