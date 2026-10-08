"""Measure original lidar support for terrain queries; never infer a water mask.

Nearest classified ground is only a support diagnostic. Its elevation is not
an interpolated terrain height, surveyed bathymetry or a concurrent river stage.
"""
import numpy as np
from scipy.spatial import cKDTree


def ground_support(points, classification, excluded, queries):
    points=np.asarray(points,dtype=float)
    classification=np.asarray(classification);excluded=np.asarray(excluded)
    queries=np.asarray(queries,dtype=float)
    if (points.ndim!=2 or points.shape[1]!=3 or queries.ndim!=2 or queries.shape[1]!=2 or
            classification.shape!=(len(points),) or excluded.shape!=(len(points),) or
            excluded.dtype.kind!='b' or classification.dtype.kind not in 'ui' or
            not np.isfinite(points).all() or not np.isfinite(queries).all()):
        raise ValueError('Finite registered XYZ/XY and explicit point classifications/flags required')
    eligible=(classification==2)&~excluded
    ground=points[eligible]
    if not len(ground):
        return dict(distance_m=np.full(len(queries),np.inf),
                    nearest_ground_z_m=np.full(len(queries),np.nan),eligible_ground_points=0)
    distance,index=cKDTree(ground[:,:2]).query(queries,workers=1)
    return dict(distance_m=distance,nearest_ground_z_m=ground[index,2],
                eligible_ground_points=int(len(ground)))


def summarize_support(support, terrain, stage, mask):
    distance=np.asarray(support['distance_m']);z=np.asarray(support['nearest_ground_z_m'])
    terrain=np.asarray(terrain);stage=np.asarray(stage);mask=np.asarray(mask)
    if (distance.ndim!=1 or any(a.shape!=distance.shape for a in (z,terrain,stage,mask)) or
            mask.dtype.kind!='b' or np.isnan(distance).any() or (distance<0).any() or
            not np.isfinite(terrain[mask]).all() or not np.isfinite(stage[mask]).all()):
        raise ValueError('Matching finite terrain/stage and explicit query group required')
    result=dict(query_count=int(mask.sum()),nearest_ground_distance_threshold_counts={},
                measured_water_level=False,terrain_modified=False)
    for radius in (.5,1.,2.,5.):
        selected=mask&(distance<=radius)
        result['nearest_ground_distance_threshold_counts'][str(radius)]=int(selected.sum())
    close=mask&(distance<=.5)
    if close.any():
        if not np.isfinite(z[close]).all():raise ValueError('Nonfinite supported point height')
        result['within_half_metre']=dict(
            count=int(close.sum()),percentiles=[5,50,95],
            point_minus_dem_m=np.percentile((z-terrain)[close],[5,50,95]).tolist(),
            point_minus_inferred_stage_m=np.percentile((z-stage)[close],[5,50,95]).tolist(),
            point_below_inferred_stage_by_over_5cm=int((z[close]<stage[close]-.05).sum()),
            warning='Nearest point at up to 0.5 m horizontal offset; not a co-located DEM error or measured flood extent')
    return result
