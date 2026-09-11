"""Independent metric route and true LiDAR footprint audit, without promotion."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile
import io

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tmp/south-fork-geospatial-deps"))
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.ops import transform
import shapefile

BASE = ROOT / "physics/data/real_world/south_fork_american_chili_bar"
OUT = BASE / "reconstruction_2026_09"
TO_METRIC = Transformer.from_crs(4326, 32610, always_xy=True)
GEOD = Geod(ellps="WGS84")


def metric(point):
    return TO_METRIC.transform(*point[:2])


def main():
    route = json.loads((BASE / "hydrography/full_reach_adopted_route.geojson").read_text())
    feature = next(f for f in route["features"] if f["geometry"]["type"] == "LineString")
    coords = feature["geometry"]["coordinates"]
    line = LineString([metric(p) for p in coords])
    geodesic_length = GEOD.line_length([p[0] for p in coords], [p[1] for p in coords])
    with zipfile.ZipFile(OUT / "sources/eldorado_2019_footprint.kmz") as archive:
        doc = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.kml'))))
    ns = {"k": doc.tag.split('}')[0].lstrip('{')}
    polygons = []
    for poly in doc.findall('.//k:Polygon', ns):
        outer = poly.find('k:outerBoundaryIs/k:LinearRing/k:coordinates', ns).text
        ring = [metric(tuple(float(v) for v in item.split(',')[:2])) for item in outer.split()]
        holes = []
        for inner in poly.findall('k:innerBoundaryIs/k:LinearRing/k:coordinates', ns):
            holes.append([metric(tuple(float(v) for v in item.split(',')[:2])) for item in inner.text.split()])
        polygons.append(Polygon(ring, holes))
    # NOAA KMZ is only a raster browse overlay, not an actual coverage polygon.
    # Use the USGS raster silhouette shape, including any internal holes.
    if not polygons:
        prefix = OUT / 'sources/USGS_Raster_Silhouette'
        reader = shapefile.Reader(shp=io.BytesIO(prefix.with_suffix('.shp').read_bytes()),
                                  dbf=io.BytesIO(prefix.with_suffix('.dbf').read_bytes()))
        from shapely.geometry import shape
        project = Transformer.from_crs(prefix.with_suffix('.prj').read_text(), 32610, always_xy=True)
        polygons = [transform(project.transform, shape(item.__geo_interface__)) for item in reader.shapes()]
    if not polygons:
        raise ValueError('No coverage polygons; coverage is unknown, not absent')
    footprint = unary_union(polygons)
    # Search anchors only, not final riverbank/rapid control coordinates.
    leads = {
        "chili_bar_bridge_search": {"lon_lat": [-120.8218, 38.7659],
            "source": "https://snoflo.org/paddle/california/chili-bar", "authority": "secondary_search_coordinate_not_surveyed"},
        "hazard_below_troublemaker": {"lon_lat": [-120.88453, 38.79998],
            "source": "https://www.americanwhitewater.org/content/River/view/river-detail/point-of-interest/hazard/101824",
            "authority": "published_hazard_marker_not_boulder_outline"},
    }
    for lead in leads.values():
        p = Point(metric(lead["lon_lat"]))
        lead["distance_to_existing_route_m"] = line.distance(p)
        lead["metric_station_on_existing_route_m"] = line.project(p)
        lead["inside_actual_lidar_footprint"] = footprint.covers(p)
    rapid = next(f for f in route["features"] if f.get('properties', {}).get('label') == 'Troublemaker')
    old = rapid['geometry']['coordinates']
    hazard = leads['hazard_below_troublemaker']['lon_lat']
    report = {
        "status": "audit_not_production_reconstruction", "metric_crs": "EPSG:32610",
        "existing_origin_lon_lat": coords[0], "existing_endpoint_lon_lat": coords[-1],
        "existing_declared_length_m": feature['properties']['station_end_m'],
        "existing_geometry_geodesic_length_m": geodesic_length,
        "existing_geometry_utm_length_m": line.length,
        "lidar_footprint_polygon_count": len(polygons),
        "existing_route_length_inside_lidar_m": line.intersection(footprint).length,
        "search_anchors": leads,
        "existing_troublemaker_lon_lat": old,
        "existing_troublemaker_to_published_downstream_hazard_m": GEOD.inv(old[0], old[1], hazard[0], hazard[1])[2],
        "provisional_chili_to_endpoint_geometry_length_m": line.length - leads['chili_bar_bridge_search']['metric_station_on_existing_route_m'],
        "requirements": ["Confirm actual Chili Bar launch/bridge in georeferenced orthophoto",
                         "Do not use generic guide miles from the old upstream origin",
                         "Do not interpret LiDAR hydro-flattened water as bathymetry"]}
    (OUT / 'route-and-lidar-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    with zipfile.ZipFile(OUT / 'sources/eldorado_2019_tile_index.zip') as archive:
        names = archive.namelist()
        print('Tile-index files:', names)
        shp = next(n for n in names if n.endswith('.shp'))
        dbf = next(n for n in names if n.endswith('.dbf'))
        prj = next(n for n in names if n.endswith('.prj'))
        tiles = shapefile.Reader(shp=io.BytesIO(archive.read(shp)), dbf=io.BytesIO(archive.read(dbf)))
        project = Transformer.from_crs(archive.read(prj).decode(), 32610, always_xy=True)
        from shapely.geometry import shape
        selections = []
        corrected = json.loads((OUT / 'corrected_route_candidate.geojson').read_text())
        corrected_feature = next(f for f in corrected['features'] if f['geometry']['type'] == 'LineString')
        corrected_line = LineString([metric(p) for p in corrected_feature['geometry']['coordinates']])
        full_reach_tiles = []
        for item in tiles.iterShapeRecords():
            polygon = transform(project.transform, shape(item.shape.__geo_interface__))
            matched = [label for label, lead in leads.items() if polygon.distance(Point(metric(lead['lon_lat']))) < 400]
            if matched:
                selections.append({'leads': matched, 'attributes': item.record.as_dict()})
            if polygon.distance(corrected_line) < 250:
                full_reach_tiles.append({'leads': matched + ['corrected_full_reach'],
                                        'attributes': item.record.as_dict()})
        (OUT / 'lidar-tile-selection.json').write_text(json.dumps(selections, indent=2), encoding='utf-8')
        print('Selected tiles:', json.dumps(selections))
        (OUT / 'full-reach-lidar-tile-selection.json').write_text(json.dumps(full_reach_tiles, indent=2), encoding='utf-8')
        print('Full reach tile count:', len(full_reach_tiles))


if __name__ == '__main__':
    main()
