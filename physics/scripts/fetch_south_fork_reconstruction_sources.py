"""Download bounded, public geographic source artifacts with hashes/provenance.

Never downloads third-party video or substitutes a footprint bounding box for
actual coverage. The indexes must be spatially checked before DEM selection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlencode, urlparse

SOURCES = {
    "eldorado_2019_contractor_index.html": (
        "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/spatial_metadata/contractor_provided/"),
    "eldorado_2019_usgs_index.html": (
        "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/spatial_metadata/USGS/"),
    "eldorado_2019_footprint.kmz": (
        "https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/laz/geoid12b/9452/supplemental/ca2019_eldorado_m9452.kmz"),
    "eldorado_2019_breaklines.zip": (
        "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/breaklines.zip"),
    "eldorado_2019_spatial_metadata.html": (
        "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/spatial_metadata/"),
    "blm_south_fork_map.pdf": (
        "https://www.blm.gov/sites/default/files/documents/files/Maps_California_south-fork-of-the-american-river-map.pdf"),
}
SPATIAL = "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/spatial_metadata/USGS/"
for suffix in ("shp", "dbf", "prj"):
    SOURCES[f"USGS_Raster_Silhouette.{suffix}"] = SPATIAL + f"USGS_Raster_Silhouette.{suffix}"
SOURCES["eldorado_2019_tile_index.zip"] = SPATIAL + "USGS_CA_UpperSouthAmerican_Eldorado_2019_TileIndex.zip"
NAIP = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/"
SOURCES["naip_service.json"] = NAIP + "?f=pjson"
for label, bbox in (("chili_bar", "-120.826,38.762,-120.817,38.770"),
                    ("troublemaker", "-120.887,38.797,-120.880,38.803")):
    SOURCES[f"{label}_naip_export.json"] = NAIP + "exportImage?bbox=" + bbox + "&bboxSR=4326&imageSR=32610&size=1600,1600&format=png&f=pjson"
    SOURCES[f"{label}_naip_catalog.json"] = NAIP + "query?" + urlencode({
        "geometry": bbox, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "where": "Category=1", "outFields": "*",
        "returnGeometry": "false", "f": "pjson"})
SOURCES['eldorado_dem_bucket.xml'] = 'https://prd-tnm.s3.amazonaws.com/?' + urlencode({
    'list-type': 2, 'prefix': 'StagedProducts/Elevation/OPR/Projects/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/TIFF/', 'max-keys': 1000})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in SOURCES.items():
        target = args.output / name
        try:
            if not target.exists():
                request = urllib.request.Request(url, headers={"User-Agent": "RaftSim-source-review/1.0"})
                with urllib.request.urlopen(request, timeout=45) as response:
                    data = response.read(25_000_001)
                if len(data) > 25_000_000:
                    raise ValueError("Source exceeds 25 MB per-file intake limit")
                target.write_bytes(data)
            data = target.read_bytes()
            records.append({"file": name, "url": url, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(), "status": "downloaded"})
        except Exception as exc:
            records.append({"file": name, "url": url, "status": "failed", "error": str(exc)})
        print(json.dumps(records[-1]), flush=True)
        (args.output / "source-downloads.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    for label in ('chili_bar', 'troublemaker'):
        metadata_path = args.output / f'{label}_naip_export.json'
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text())
        href = metadata.get('href')
        if not href or urlparse(href).hostname != 'imagery.nationalmap.gov':
            print(f'{label}: export failed or unexpected image host: {metadata}', flush=True)
            continue
        target = args.output / f'{label}_naip.png'
        if not target.exists():
            with urllib.request.urlopen(href, timeout=45) as response:
                data = response.read(25_000_001)
            if len(data) > 25_000_000:
                raise ValueError('Export exceeds 25 MB intake limit')
            target.write_bytes(data)
        records.append({'file': target.name, 'url': href, 'source_metadata': metadata_path.name,
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'status': 'downloaded'})
        print(json.dumps(records[-1]), flush=True)
        (args.output / 'source-downloads.json').write_text(json.dumps(records, indent=2), encoding='utf-8')


if __name__ == "__main__":
    main()
