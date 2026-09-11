"""Constrain the route to captured water without excavating measured banks.

This is a geographic alignment, NOT a surveyed thalweg or a navigation line.
The search may not bridge a dry gap or silently move either reach endpoint.
"""
from pathlib import Path
import sys
import json
import heapq
import math

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt
from shapely.geometry import shape, mapping, LineString, Point
from shapely.ops import transform
from pyproj import Transformer

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def wet_segment(a, b, wet):
    """Conservative supercover: a diagonal cannot cut across a dry corner."""
    a, b = np.asarray(a), np.asarray(b)
    points = a + np.linspace(0, 1, max(2, int(np.linalg.norm(b-a)*4)+1))[:,None]*(b-a)
    cells = np.floor(points+.5).astype(int)
    if not wet[cells[:,0], cells[:,1]].all():
        return False
    delta = np.diff(cells, axis=0)
    corners = np.where(np.all(delta != 0, axis=1))[0]
    return bool(wet[cells[corners,0], cells[corners+1,1]].all()
                and wet[cells[corners+1,0], cells[corners,1]].all())


def channel_path(allowed, clearance, guide_distance, start, end):
    """Eight-connected A*; the admissible heuristic is metric distance."""
    rows, cols = allowed.shape
    start, end = tuple(start), tuple(end)
    if not allowed[start] or not allowed[end]:
        raise ValueError('Reach endpoint outside captured water')
    cost = np.full(allowed.shape, np.inf, dtype=np.float32)
    parent = np.full(allowed.shape, -1, dtype=np.int32)
    cost[start] = 0
    queue = [(math.dist(start,end), 0., start[0], start[1])]
    closed = np.zeros(allowed.shape, dtype=bool)
    directions = [(dr,dc,math.hypot(dr,dc)) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc]
    while queue:
        _, g, r, c = heapq.heappop(queue)
        if closed[r,c]:
            continue
        closed[r,c] = True
        if (r,c) == end:
            result = [(r,c)]
            while (r,c) != start:
                r,c = divmod(int(parent[r,c]), cols)
                result.append((r,c))
            return np.asarray(result[::-1]), int(closed.sum())
        for dr,dc,length in directions:
            nr,nc = r+dr,c+dc
            if nr<0 or nc<0 or nr>=rows or nc>=cols or not allowed[nr,nc] or closed[nr,nc]:
                continue
            if dr and dc and (not allowed[r,nc] or not allowed[nr,c]):
                continue
            # Avoid skimming banks; retain the independently mapped route as
            # a weak guide, never as authority to erase real bank geometry.
            penalty = 1. + 2./(1.+clearance[nr,nc]) + .003*guide_distance[nr,nc]
            candidate = g + length*penalty
            if candidate < cost[nr,nc]:
                cost[nr,nc] = candidate
                parent[nr,nc] = r*cols+c
                heapq.heappush(queue,(candidate+math.hypot(nr-end[0],nc-end[1]),candidate,nr,nc))
    raise ValueError('No continuous surveyed-water path; refusing to invent a channel across dry ground')


def simplify_inside_water(path, wet, max_span=12):
    result = [path[0]]
    i = 0
    while i < len(path)-1:
        j = min(i+max_span,len(path)-1)
        while j>i+1 and not wet_segment(path[i],path[j],wet):
            j -= 1
        result.append(path[j]); i=j
    return np.asarray(result)


def main():
    original = json.loads((BASE / 'corrected_route_candidate.geojson').read_text())
    feature = next(f for f in original['features'] if f['geometry']['type']=='LineString')
    to_metric = Transformer.from_crs(4326,32610,always_xy=True)
    to_geo = Transformer.from_crs(32610,4326,always_xy=True)
    route = transform(to_metric.transform,shape(feature['geometry']))
    with rasterio.open(BASE / 'full_reach/unknown_submerged_bed_mask.tif') as ds:
        affine = ds.transform
        wet = ds.read(1)==1
        near = rasterize([(mapping(route.buffer(120)),1)],out_shape=wet.shape,transform=affine,dtype='uint8')==1
        guide = rasterize([(mapping(route),1)],out_shape=wet.shape,transform=affine,dtype='uint8')==1
        clearance = distance_transform_edt(wet).astype(np.float32)*ds.res[0]
        guide_distance = distance_transform_edt(~guide).astype(np.float32)*ds.res[0]
        endpoints = [ds.index(*route.coords[i]) for i in (0,-1)]
    path, searched = channel_path(wet&near,clearance,guide_distance,*endpoints)
    simplified = simplify_inside_water(path,wet&near)
    xy = np.column_stack(affine*(simplified[:,1]+.5,simplified[:,0]+.5))
    aligned = LineString(xy)
    controls = []
    for f in original['features']:
        if f['geometry']['type']=='Point':
            f['properties']['aligned_station_m'] = aligned.project(transform(to_metric.transform,shape(f['geometry'])))
            controls.append(f)
    report = {'schema':'raftsim.south_fork.survey_constrained_axis.v1',
        'status':'candidate_geographic_axis_not_navigation',
        'length_m':aligned.length,'previous_nhd_length_m':route.length,
        'horizontal_crs':'EPSG:32610','raster_cell_m':2.,
        'searched_cells':searched,'axis_vertex_count':len(xy),
        'all_segments_inside_survey_water':True,
        'measured_terrain_modified':False,'dry_gaps_bridged':0,
        'endpoint_quantization_m':[float(Point(xy[i]).distance(Point(route.coords[i]))) for i in (0,-1)],
        'not_a_surveyed_thalweg':True,'production_promoted':False}
    output = {'type':'FeatureCollection','features':[{'type':'Feature','id':'survey_constrained_axis',
        'properties':report,'geometry':mapping(transform(to_geo.transform,aligned))},*controls]}
    (BASE/'survey_constrained_route_candidate.geojson').write_text(json.dumps(output,indent=2),encoding='utf-8')
    (BASE/'full_reach/channel_alignment_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
