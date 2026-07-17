# Credits

Per-item provenance, licenses, and hashes are recorded in intake manifests throughout the repository (the authoritative record). This file summarizes the third-party sources used. Entries are added as assets/data are integrated; regenerate against the manifests before each release.

## Engine and libraries

- **Unreal Engine 5.8** — © Epic Games, Inc., under the Unreal Engine EULA (not part of this repository).
- **Python libraries** — NumPy (BSD-3), pytest (MIT), Matplotlib (PSF-based), Clawpack/GeoClaw (BSD-3), rasterio (BSD-3).

## Art assets

- **Poly Haven** (polyhaven.com) — CC0 models and textures (evaluated tree/rock/material assets; per-item manifests under the asset intake records).
- **ambientCG** (ambientcg.com) — CC0 PBR materials (external review sets).
- CC0 scanned rock set (six-variant Nanite rocks; manifest-recorded).

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
