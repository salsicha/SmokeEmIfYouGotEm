"""Shared numerical chart; never a replacement for geographic source geometry."""
import numpy as np
import shapely
from shapely.geometry import LineString

from build_curvilinear_river_scenario import arc_resample, gauss_smooth, curvature


def full_route_frame(line, step=2., smoothing_m=80., end_extension_m=0., chart_line=None):
    if (not isinstance(line, LineString) or not line.is_simple or
            not np.isfinite([step, smoothing_m, end_extension_m]).all() or step != 2. or
            not 4 <= smoothing_m <= 320 or not 0 <= end_extension_m <= 128 or
            end_extension_m % step != 0 or line.length < 100):
        raise ValueError('Simple full route and bounded 2 m numerical chart required')
    chart_line=line if chart_line is None else chart_line
    if not isinstance(chart_line,LineString) or not chart_line.is_simple or chart_line.length<100:
        raise ValueError('Simple bounded numerical chart reference required')
    source = np.asarray(line.coords)
    chart_source=np.asarray(chart_line.coords)
    x, y, _ = arc_resample(chart_source[:, 0], chart_source[:, 1], step)
    x, y, station = arc_resample(gauss_smooth(x, smoothing_m/step),
                                gauss_smooth(y, smoothing_m/step), step)
    xy = np.c_[x, y]
    if end_extension_m:
        # Extend numerical coordinates only, never source geometry or terrain.
        tangent_start=xy[1]-xy[0];tangent_start/=np.linalg.norm(tangent_start)
        tangent_end=xy[-1]-xy[-2];tangent_end/=np.linalg.norm(tangent_end)
        distance=np.arange(step,end_extension_m+step,step)
        xy=np.r_[xy[0]-distance[::-1,None]*tangent_start,xy,
                 xy[-1]+distance[:,None]*tangent_end]
        station=np.r_[-distance[::-1],station,station[-1]+distance]
        x,y=xy.T
    source_station = shapely.line_locate_point(line, shapely.points(xy))
    delta=np.diff(source_station)
    if np.any(delta < 0):
        raise ValueError('Numerical chart reverses source progression')
    # Distinct chart cells may project to the same actual source vertex.
    vertices=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(source,axis=0),axis=1))]
    repeated=source_station[:-1][delta==0]
    indices=np.searchsorted(vertices,repeated)
    if len(repeated) and not np.allclose(vertices[np.minimum(indices,len(vertices)-1)],repeated,atol=1e-7,rtol=0):
        raise ValueError('Repeated source projection is not a polyline vertex')
    tangent = np.gradient(xy, step, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    normal = np.c_[-tangent[:, 1], tangent[:, 0]]
    return dict(station=station, xy=xy, normal=normal, source_station=source_station,
                curvature=curvature(x, y)/step)


def hydraulic_frame(line, planform_policy=None):
    """Retain a verified parent chart while projecting onto corrected geography.

    A numerical chart need not follow the water's centre. Recentring it when a
    geographic branch is corrected can clip other branches. Both versions still
    require independent complete footprint, branch, and no-overlap validation.
    """
    from pathlib import Path
    from correct_chilko_route import lineage, sha, route_points, projected
    import json
    chart_line=None
    policy=dict(kind='same_geographic_route')
    if planform_policy and planform_policy.get('kind')!='original_FWA_polygons':
        manifest=Path(planform_policy['route_lineage_manifest'])
        if sha(manifest)!=planform_policy['route_lineage_sha256']:
            raise ValueError('Changed derived-route chart source')
        route=manifest.with_suffix('').with_suffix('.geojson')
        receipt,_=lineage(route)
        if not np.array_equal(projected(route_points(json.loads(route.read_text()))),np.asarray(line.coords)):
            raise ValueError('Chart route differs from corrected geographic source')
        parent=Path(receipt['parent_route']['path'])
        chart_line=LineString(projected(route_points(json.loads(parent.read_text()))))
        policy=dict(kind='verified_parent_numerical_chart_with_corrected_geographic_projection',
                    chart_route=dict(path=str(parent),sha256=sha(parent)),
                    geographic_route_sha256=sha(route),
                    qualification='Parent vertices define numerical coordinates only; source stage, bed ownership and rapid anchors use corrected geography')
    return full_route_frame(line,smoothing_m=320.,end_extension_m=64.,chart_line=chart_line),policy


def directions_at_source_points(line, points):
    """Orient exact geographic anchors across the shared chart, not tiny edges.

    These are numerical sampling directions, not observed flow directions.
    Geographic coordinates, stationing, bank masks and heights stay unchanged.
    Use actual chart arclength for projection, not its nominal 2 m parameter.
    """
    points=np.asarray(points,dtype=float)
    if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():
        raise ValueError('Finite geographic section anchors required')
    if len(points) and np.max(shapely.distance(line,shapely.points(points)))>1e-6:
        raise ValueError('Section anchors must remain on the exact geographic route')
    frame=full_route_frame(line,smoothing_m=320.,end_extension_m=64.)
    chain=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(frame['xy'],axis=0),axis=1))]
    along=shapely.line_locate_point(LineString(frame['xy']),shapely.points(points))
    normal=np.c_[np.interp(along,chain,frame['normal'][:,0]),
                 np.interp(along,chain,frame['normal'][:,1])]
    norm=np.linalg.norm(normal,axis=1)
    if (norm<1e-6).any():raise ValueError('Degenerate chart sampling direction')
    return normal/norm[:,None]
