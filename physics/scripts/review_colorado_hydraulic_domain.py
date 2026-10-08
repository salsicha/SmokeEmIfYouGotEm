"""Geometry checks for a bounded hydraulic chart, independent of solver success.

Dry domain edges alone do not prove coverage: a disconnected channel can sit
entirely outside a strip. Check all classified source-water pixel centres in
the required core against the physical chart footprint as well. This never
edits source masks or declares off-chart water dry.
"""
import numpy as np
from shapely import intersects_xy
from shapely.geometry import Polygon
from shapely.ops import unary_union


def lateral_axis(interval):
    a=np.asarray(interval,dtype=float)
    if (a.shape!=(2,) or not np.isfinite(a).all() or not a[0]<0<a[1] or
            not 8<=a[1]-a[0]<=500 or np.any(np.mod(a,2.)!=0)):
        raise ValueError('A finite, origin-containing, 2 m-aligned domain of at most 500 m is required')
    return np.arange(a[0],a[1]+2.,2.)


def construction_lateral_axis(width,reviewed_interval=None):
    """Keep the legacy default; explicit domains also require footprint review.

    A truncated symmetric diagnostic transect is not the boundary of a
    separately reviewed asymmetric domain. Callers using this explicit path
    MUST run source_footprint_coverage plus terrain, wet-edge and fold gates.
    """
    intervals=[a for row in width['widths'] for a in row['classified_water_intervals_lateral_m']]
    if not intervals:raise ValueError('Unbounded or missing water transects')
    values=np.asarray(intervals,dtype=float)
    if values.ndim!=2 or values.shape[1]!=2 or not np.isfinite(values).all():
        raise ValueError('Invalid captured water transects')
    if reviewed_interval is not None:return lateral_axis(reviewed_interval)
    if any(w['transect_truncated'] for w in width['widths']):
        raise ValueError('Unbounded or missing water transects')
    half=float(np.ceil((np.max(np.abs(values))+20)/2)*2)
    if half>250:raise ValueError('Curved strip wider than reviewed 500 m limit')
    return np.arange(-half,half+2,2.)


def source_footprint_coverage(grid,profile,xy,normal,lateral,end_caps=None):
    xy,normal,lateral=map(lambda a:np.asarray(a,dtype=float),(xy,normal,lateral))
    if (xy.ndim!=2 or xy.shape[1]!=2 or len(xy)<2 or normal.shape!=xy.shape or
            lateral.ndim!=1 or len(lateral)<2 or np.any(np.diff(lateral)<=0) or
            not all(np.isfinite(a).all() for a in (xy,normal,lateral)) or
            not np.allclose(np.linalg.norm(normal,axis=1),1.,atol=1e-9,rtol=0)):
        raise ValueError('Invalid physical chart')
    wet=np.asarray(grid['classified_water_mask']);station=np.asarray(grid['station_m'],dtype=float)
    corner=np.asarray(grid['corner_east_north_m'],dtype=float)
    cell=np.asarray(grid['cell_m'],dtype=float)
    core=np.asarray(profile['source_core_interval_m'],dtype=float)
    origin=profile['source_halo_interval_m'][0]
    if (wet.ndim!=2 or wet.dtype.kind!='b' or station.shape!=wet.shape or
            corner.shape!=(2,) or cell.shape!=(2,) or not np.array_equal(cell,[1.,1.]) or
            core.shape!=(2,) or not core[0]<core[1] or
            not all(np.isfinite(a).all() for a in (station,corner,core,np.array([origin])))):
        raise ValueError('Registered complete one-metre classified source grid required')
    station=station+origin
    if end_caps is not None:
        ends=np.asarray(end_caps['stations'],dtype=float)
        positions=np.asarray(end_caps['positions'],dtype=float)
        directions=np.asarray(end_caps['directions'],dtype=float)
        if (ends.shape!=(2,) or positions.shape!=(2,2) or directions.shape!=(2,2) or
                not ends[0]<ends[1] or not all(np.isfinite(a).all() for a in (ends,positions,directions)) or
                not np.allclose(np.linalg.norm(directions,axis=1),1.,atol=1e-9,rtol=0)):
            raise ValueError('Invalid captured source end planes')
        local=np.asarray(grid['station_m'])
        for end in ends:
            if profile['source_halo_interval_m'][0]<=end<=profile['source_halo_interval_m'][1]:
                # Match the terrain coverage review: recover exact stored
                # endpoint clamping, not all stations near the last sample.
                stored=np.asarray(end-origin,dtype=local.dtype)
                station[local==stored]=end
    inside=wet&(station>=core[0])&(station<=core[1])
    r,c=np.nonzero(inside)
    if not len(r):raise ValueError('No classified source water in required core')
    x=corner[0]+c+.5;y=corner[1]-r-.5;outside=np.zeros(len(r),bool)
    if end_caps is not None:
        points=np.column_stack([x,y])
        for k,sign in ((0,-1.),(1,1.)):
            distance=(points-positions[k])@directions[k]
            outside|=(np.abs(station[r,c]-ends[k])<=1e-6)&(sign*distance>1e-6)
        x,y=x[~outside],y[~outside]
        if not len(x):raise ValueError('No classified source water inside physical run')
    left=xy+normal*lateral[0];right=xy+normal*lateral[-1]
    # The boundary comes from the actual queried chart, not a fitted corridor
    # buffer. Use two triangles per strip cell so even a dry-side fold cannot
    # cause a topology repair to silently erase an uncovered wet component.
    triangles=[]
    for i in range(len(xy)-1):
        for vertices in ((left[i],left[i+1],right[i+1]),(left[i],right[i+1],right[i])):
            triangle=Polygon(vertices)
            if triangle.area>0:triangles.append(triangle)
    if not triangles:raise ValueError('Empty physical chart footprint')
    footprint=unary_union(triangles)
    covered=intersects_xy(footprint,x,y)
    missing=np.flatnonzero(~covered)
    return dict(classified_source_core_cells=int(len(x)),uncovered_classified_source_core_cells=int(len(missing)),
        outside_route_endpoint_cells=int(outside.sum()),
        complete_classified_core_coverage=not len(missing),
        missing_examples_epsg6404_m=np.column_stack([x[missing[:8]],y[missing[:8]]]).tolist(),
        policy='All in-route classified 1 m source-core pixel centres inside the linear chart-strip footprint; only exactly station-clamped cells beyond captured geographic end planes excluded; no buffer, mask edit or dry reinterpretation',
        source_geometry_modified=False)
