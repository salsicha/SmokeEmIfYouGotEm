"""Captured OSM river polygons, preserving islands and incomplete-source errors.

Mapping is not a surveyed or image-date shoreline. Do not silently close open
ways, repair self-intersections, flatten relation holes, or import unrelated
waterbodies as bank evidence.
"""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.ops import polygonize_full, transform
from pyproj import Transformer


def coordinates(geometry):
    try:
        xy=np.array([[p['lon'],p['lat']] for p in geometry],dtype=float)
    except (KeyError,TypeError,ValueError) as exc:
        raise ValueError('Incomplete captured geometry') from exc
    if (xy.ndim!=2 or xy.shape[1]!=2 or len(xy)<2 or not np.isfinite(xy).all()
            or np.any(abs(xy[:,0])>180) or np.any(abs(xy[:,1])>90)):
        raise ValueError('Finite geographic geometry required')
    return xy


def rings(members):
    lines=[shapely.LineString(coordinates(m['geometry'])) for m in members]
    polygons,cuts,dangles,invalid=polygonize_full(lines)
    if polygons.is_empty or any(not p.is_empty for p in (cuts,dangles,invalid)):
        raise ValueError('Captured relation rings are incomplete or invalid')
    # polygonize can itself insert a hole when two rings are nested. Role
    # interpretation belongs to the caller; retain each ring independently.
    result=[]
    for p in polygons.geoms:
        result.append(shapely.Polygon(p.exterior))
    return result


def parse_water(data):
    water=lambda e:e.get('tags',{}).get('natural')=='water' and e.get('tags',{}).get('water')=='river'
    relations=[e for e in data['elements'] if e['type']=='relation' and water(e)]
    member_ids=set();features=[]
    for e in relations:
        if e['tags'].get('type')!='multipolygon':
            raise ValueError('Unknown river relation type')
        members=e['members']
        if any(m['type']!='way' or m.get('role') not in ('outer','inner') or not m.get('geometry') for m in members):
            raise ValueError('Complete explicitly role-tagged river members required')
        outer=rings([m for m in members if m['role']=='outer'])
        inner_members=[m for m in members if m['role']=='inner']
        inner=rings(inner_members) if inner_members else []
        shell=shapely.union_all(outer)
        holes=shapely.union_all(inner)
        if not holes.is_empty and not shell.covers(holes):
            raise ValueError('Inner river ring lies outside captured outer rings')
        geom=shell.difference(holes)
        if geom.is_empty or not geom.is_valid:
            raise ValueError('Invalid source river polygon; no automatic repair')
        features.append(('relation',e['id'],geom))
        member_ids.update(m['ref'] for m in members)
    for e in data['elements']:
        if e['type']!='way' or not water(e) or e['id'] in member_ids:
            continue
        xy=coordinates(e.get('geometry'))
        if len(xy)<4 or not np.array_equal(xy[0],xy[-1]):
            raise ValueError('Standalone water way must be explicitly closed')
        geom=shapely.Polygon(xy)
        if not geom.is_valid or geom.area<=0:
            raise ValueError('Invalid source water way; no automatic repair')
        features.append(('way',e['id'],geom))
    if not features:
        raise ValueError('No captured river polygons')
    return features


def load_planform(path):
    features=parse_water(json.loads(Path(path).read_text(encoding='utf-8')))
    project=Transformer.from_crs(4326,32718,always_xy=True).transform
    return [(kind,identity,transform(project,geometry)) for kind,identity,geometry in features]


def mapped_span(polygon, center, normal, half_width_m=256.):
    center,normal=np.asarray(center,float),np.asarray(normal,float)
    if (center.shape!=(2,) or normal.shape!=(2,) or not np.isfinite([*center,*normal,half_width_m]).all()
            or abs(np.linalg.norm(normal)-1)>1e-8 or half_width_m<=0 or not polygon.is_valid):
        raise ValueError('Valid planform, finite point and unit normal required')
    if not polygon.covers(shapely.Point(center)):
        return None
    cross=shapely.LineString([center-half_width_m*normal,center+half_width_m*normal])
    hit=cross.intersection(polygon)
    parts=list(hit.geoms) if hasattr(hit,'geoms') else [hit]
    candidates=[]
    for part in parts:
        if part.geom_type!='LineString' or part.is_empty:
            continue
        lateral=(np.asarray(part.coords)-center)@normal
        lo,hi=float(lateral.min()),float(lateral.max())
        if lo<=1e-8 and hi>=-1e-8 and hi-lo>1e-8:
            candidates.append((lo,hi))
    if len(candidates)!=1:
        raise ValueError('No unique positive mapped component containing source route')
    lo,hi=candidates[0]
    if lo<=-half_width_m+1e-6 or hi>=half_width_m-1e-6:
        raise ValueError('Mapped bank exceeds cross-section; no clamped shoreline permitted')
    return lo,hi
