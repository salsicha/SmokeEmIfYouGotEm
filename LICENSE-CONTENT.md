# Content License

**Scope.** This license covers first-party content in this repository: maps, textures, materials, meshes, audio, capture images, and data manifests authored for this project (generally everything under `unreal/Content/`, `docs/environment-captures/`, and `physics/data/` that is not third-party per below).

**License.** First-party content is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**: https://creativecommons.org/licenses/by/4.0/

Attribution: "SmokeEmIfYouGotEm project (RaftSim), © 2026 Alex Moran and contributors, CC BY 4.0".

**Code** (C++, Python, build scripts, shaders-as-code) is licensed separately under the MIT License — see `LICENSE`.

**Third-party content is NOT covered by this license.** Every third-party asset or data source in this repository is tracked by an intake manifest recording its origin, license, and hashes. The manifest is authoritative per item. Categories include:

- **CC0 assets** (e.g. Poly Haven models/textures) — committed to the repository; no attribution required, credited in `CREDITS.md` anyway.
- **Licensed marketplace assets** (e.g. Fab Standard License items) — never committed to this repository; used only in packaged builds where the item's license permits, with local-only storage and committed procedural fallbacks.
- **Government / open geospatial data** (USGS 3DEP, NAIP, Copernicus DEM, Sentinel-2, provincial hydrography, gauge records) — used under their respective open-data terms; provenance recorded per source manifest; see `CREDITS.md`.

The canonical asset-source policy is `docs/free-and-ai-asset-policy.md` and `unreal/Content/RaftSim/development_asset_source_policy.json`.
