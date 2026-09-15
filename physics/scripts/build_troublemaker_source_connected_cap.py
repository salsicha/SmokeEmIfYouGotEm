"""Extend the cap through original lower returns, stopping at supported ground.

Bin connectivity and the .3 m clearance are reconstruction priors, not a
measured rock outline. Missing support remains open; it is never a bevel.
"""
import argparse
from collections import deque
import json
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles, intersects_xy, union_all
from shapely.geometry import LineString, MultiPoint, Polygon
from shapely.ops import split
from scipy.spatial import Delaunay

from build_troublemaker_dem_rock_cap import (
    ROOT, PARENT, RETURNS, ORIGIN, PARENT_SHA, RETURNS_SHA, cap_triangles,
    close_cap_below_retained_terrain, native_collision_probes, refine_source_coverage, sample_cap,
)
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_rock_union import sha

NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def reviewed_region(path, previous):
    """Read an explicitly interpreted selection; never relabel it measured."""
    path = Path(path).resolve()
    record = json.loads(path.read_text())
    if record.get('schema') != 'raftsim.interpreted_source_selection.v1':
        raise ValueError('Explicit interpreted source selection required')
    for key in ('source_mesh_sha256', 'original_returns_sha256', 'source_naip_sha256',
                'source_naip_export_sha256', 'origin_utm_and_vertical_datum_m'):
        if record.get(key) != previous[key]:
            raise ValueError('Selection belongs to different sources/frame: ' + key)
    if record.get('measured_outline') is not False or record.get('measured_flanks') is not False:
        raise ValueError('Image selection cannot claim measured outlines or flanks')
    region = Polygon(record['interpreted_selection_polygon_m'])
    if not region.is_valid or region.area <= 0:
        raise ValueError('Valid positive-area reviewed selection required')
    return region, dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path),
        measured_outline=False, measured_flanks=False,
        interpretation=record['interpretation'],
        registration_uncertainty_m=record['registration_uncertainty_m'])


def lower_bins(xyz, ids, cell_m=.5, minimum_count=2):
    xyz, ids = np.asarray(xyz, float), np.asarray(ids)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.issubdtype(ids.dtype, np.integer):
        raise ValueError('Original XYZ and integer IDs required')
    if ids.ndim != 1 or len(np.unique(ids)) != len(ids) or not len(ids) or ids.min() < 0 or ids.max() >= len(xyz):
        raise ValueError('Distinct supported original IDs required')
    if not np.isfinite(xyz[ids]).all() or not np.isfinite(cell_m) or cell_m <= 0 or minimum_count < 1 or int(minimum_count) != minimum_count:
        raise ValueError('Finite original points and positive selection parameters required')
    bins = np.floor(xyz[ids, :2] / cell_m).astype(np.int64)
    keys, groups, counts = np.unique(bins, axis=0, return_inverse=True, return_counts=True)
    order = np.lexsort((ids, xyz[ids, 2], groups))
    first = np.r_[True, groups[order[1:]] != groups[order[:-1]]]
    positions = order[first]
    keep = counts[groups[positions]] >= minimum_count
    positions = positions[keep]
    return ids[positions], keys[groups[positions]], counts[groups[positions]]


def connected_support(gaps, seed_bins, threshold_m=.3):
    """Face-connected high bins plus one ring of actually sampled low bins.

    Forced seed bins retain the prior cap even if a lower observation occupies
    the same bin. A missing neighbor is reported, not replaced by ground.
    """
    if not np.isfinite(threshold_m) or threshold_m < 0 or any(not np.isfinite(v) for v in gaps.values()):
        raise ValueError('Finite clearances and nonnegative threshold required')
    active = {tuple(map(int, key)) for key in seed_bins}
    if not active:
        raise ValueError('Original cap seeds required')
    pending = deque(sorted(active))
    while pending:
        x, y = pending.popleft()
        for dx, dy in NEIGHBORS:
            key = (x + dx, y + dy)
            if key not in active and key in gaps and gaps[key] > threshold_m:
                active.add(key)
                pending.append(key)
    collar, unsupported = set(), set()
    for x, y in sorted(active):
        for dx, dy in NEIGHBORS:
            key = (x + dx, y + dy)
            if key in active:
                continue
            if key in gaps:
                collar.add(key)
            else:
                unsupported.add(((x, y), key))
    return active, collar, sorted(unsupported)


def separate_vertex_fans(vertices, faces):
    """Split disconnected triangle fans at a point without changing any XYZ.

    Filtered source triangulations can touch at a single vertex. Extruding that
    shared index would create four walls on one vertical edge. Each fan keeps
    the same original observation through the returned index map; no triangle,
    hole, point, adjacency across an edge, or sampled roof height is changed.
    """
    vertices, faces = np.asarray(vertices, float), np.asarray(faces)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all():
        raise ValueError('Finite original vertices required')
    if faces.ndim != 2 or faces.shape[1] != 3 or not np.issubdtype(faces.dtype, np.integer):
        raise ValueError('Integer triangles required')
    if not len(faces) or faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError('Supported triangles required')
    result = faces.copy()
    mapping = list(range(len(vertices)))
    incident = [[] for _ in vertices]
    for face_id, triangle in enumerate(faces):
        if len(set(triangle)) != 3:
            raise ValueError('Degenerate source indices')
        for vertex in triangle:
            incident[vertex].append(face_id)
    for vertex, around in enumerate(incident):
        edge_faces = {}
        for face_id in around:
            for neighbor in faces[face_id]:
                if neighbor != vertex:
                    edge_faces.setdefault(int(neighbor), []).append(face_id)
        if any(len(ids) > 2 for ids in edge_faces.values()):
            raise ValueError('Nonmanifold source edge cannot be repaired by vertex splitting')
        remaining = set(around)
        first = True
        while remaining:
            todo = [min(remaining)]; fan = set()
            while todo:
                face_id = todo.pop()
                if face_id in fan:
                    continue
                fan.add(face_id)
                for neighbor in faces[face_id]:
                    if neighbor != vertex:
                        todo.extend(i for i in edge_faces[int(neighbor)] if i not in fan)
            remaining.difference_update(fan)
            if not first:
                new_index = len(mapping); mapping.append(vertex)
                for face_id in fan:
                    result[face_id, result[face_id] == vertex] = new_index
            first = False
    mapping = np.asarray(mapping, dtype=np.int64)
    expanded = vertices[mapping]
    if not np.array_equal(expanded[result], vertices[faces]):
        raise ValueError('Fan separation changed source triangle geometry')
    return expanded, result, mapping


def recover_segment(vertices, faces, a, b):
    """Retriangulate only a crossed cavity, with the original segment fixed.

    GEOS constrained polygon triangulation preserves each cavity boundary.
    No Steiner/averaged vertex is permitted; every result must be an input XY.
    """
    edges = np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    target = np.sort([a,b])
    if np.any(np.all(edges == target,axis=1)):
        return faces
    segment = LineString(vertices[[a,b],:2])
    polygons = [Polygon(p) for p in vertices[faces,:2]]
    crossed = np.array([p.intersection(segment).length > 0 for p in polygons])
    cavity = union_all([p for p,take in zip(polygons,crossed) if take])
    if cavity.geom_type != 'Polygon':
        raise ValueError('Constraint cavity is not a simple connected polygon')
    halves = split(cavity,segment)
    if len(halves.geoms) != 2:
        raise ValueError('Original boundary segment did not split the cavity')
    lookup = {tuple(p):i for i,p in enumerate(vertices[:,:2])}
    recovered=[]
    for half in halves.geoms:
        for triangle in constrained_delaunay_triangles(half).geoms:
            coords=list(triangle.exterior.coords)[:-1]
            if len(coords)!=3 or any(tuple(p) not in lookup for p in coords):
                raise ValueError('Constraint recovery introduced a non-source vertex')
            recovered.append([lookup[tuple(p)] for p in coords])
    recovered=np.asarray(recovered,dtype=np.int64)
    if set(faces[crossed].ravel())!=set(recovered.ravel()):
        raise ValueError('Constraint recovery discarded a source vertex')
    v=vertices[recovered,:2]
    area=(v[:,1,0]-v[:,0,0])*(v[:,2,1]-v[:,0,1])-(v[:,1,1]-v[:,0,1])*(v[:,2,0]-v[:,0,0])
    recovered[area<0]=recovered[area<0][:,[0,2,1]]
    if np.any(area==0) or abs(np.abs(area).sum()/2-cavity.area)>1e-10:
        raise ValueError('Constraint recovery changed projected coverage')
    return np.concatenate([faces[~crossed],recovered])


def constrained_extension(vertices, preserved_faces, maximum_edge_m=1., allowed_region=None):
    """Keep every old roof triangle verbatim; constrain its outside connection."""
    vertices,preserved_faces=np.asarray(vertices,float),np.asarray(preserved_faces)
    if len(np.unique(vertices[:,:2],axis=0))!=len(vertices):
        raise ValueError('Ambiguous XY in constrained source geometry')
    faces=Delaunay(vertices[:,:2]).simplices.copy()
    p=vertices[faces,:2]
    cross=(p[:,1,0]-p[:,0,0])*(p[:,2,1]-p[:,0,1])-(p[:,1,1]-p[:,0,1])*(p[:,2,0]-p[:,0,0])
    faces[cross<0]=faces[cross<0][:,[0,2,1]]
    old_polygons=[Polygon(p) for p in vertices[preserved_faces,:2]]
    old_footprint=union_all(old_polygons)
    if allowed_region is not None:
        if not allowed_region.is_valid or allowed_region.area <= 0:
            raise ValueError('Valid reviewed extension region required')
        # The older cap is retained, not reinterpreted by an extension review.
        allowed_region = union_all([allowed_region, old_footprint])
    old_edges=np.sort(np.concatenate([preserved_faces[:,[0,1]],preserved_faces[:,[1,2]],preserved_faces[:,[2,0]]]),axis=1)
    edges,count=np.unique(old_edges,axis=0,return_counts=True)
    constraints=edges[count==1]
    for a,b in constraints:
        faces=recover_segment(vertices,faces,int(a),int(b))
    present={tuple(e) for e in np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)}
    if any(tuple(e) not in present for e in constraints):
        raise ValueError('A later cavity lost an original constraint')
    outside=[]
    for face in faces:
        polygon=Polygon(vertices[face,:2])
        overlap=polygon.intersection(old_footprint).area
        if overlap>1e-10:
            if abs(overlap-polygon.area)>1e-10:
                raise ValueError('New face crosses the preserved roof')
            continue
        if allowed_region is not None and not allowed_region.covers(polygon):
            continue
        xy=vertices[face,:2]
        if np.linalg.norm(xy-np.roll(xy,1,axis=0),axis=1).max()<=maximum_edge_m:
            outside.append(face)
    return np.concatenate([preserved_faces,np.asarray(outside,dtype=np.int64).reshape(-1,3)])


def run(previous_path, output, support_region=None):
    previous_path, output = Path(previous_path).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'tmp'):
        raise ValueError('Fresh project tmp candidate required')
    if sha(PARENT) != PARENT_SHA or sha(RETURNS) != RETURNS_SHA:
        raise ValueError('Original source changed')
    previous = json.loads(previous_path.read_text())
    selection_region, selection_identity = (None, None) if support_region is None else reviewed_region(support_region, previous)
    old_path = ROOT / previous['cap_path']
    if sha(old_path) != previous['cap_sha256']:
        raise ValueError('Previous cap changed')
    with np.load(PARENT, allow_pickle=False) as parent:
        sampler = RegisteredMeshSampler(parent)
        floor = float(parent['z_m'].min()) - 1
    with np.load(RETURNS, allow_pickle=False) as data, np.load(old_path, allow_pickle=False) as old:
        xyz = np.column_stack([data[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')]) - ORIGIN
        classes = data['classification']
        old_ids, old_xyz, old_faces = old['original_return_index'], old['vertices_m'], old['triangles']
        old_footprint = union_all([Polygon(p) for p in old_xyz[old_faces,:2]])
        if not np.array_equal(xyz[old_ids], old_xyz):
            raise ValueError('Previous cap did not retain original XYZ')
        # Whole captured mesh interior, not a guessed expanding rock radius.
        valid = np.isfinite(xyz).all(1) & np.isin(classes, [1, 2, 10])
        valid &= (xyz[:, 0] >= sampler.east[0] + sampler.dx / 2) & (xyz[:, 0] <= sampler.east[-1] - sampler.dx / 2)
        valid &= (xyz[:, 1] >= sampler.north[-1] + sampler.dy / 2) & (xyz[:, 1] <= sampler.north[0] - sampler.dy / 2)
        ids, keys, counts = lower_bins(xyz, np.flatnonzero(valid))
        clearance = xyz[ids, 2] - sampler.sample(xyz[ids, 0], xyz[ids, 1])
        reviewed = np.ones(len(ids), dtype=bool) if selection_region is None else intersects_xy(selection_region, xyz[ids,0], xyz[ids,1])
        gaps = {tuple(k): float(h) for k, h, keep in zip(keys, clearance, reviewed) if keep}
        active, collar, unsupported = connected_support(gaps, np.floor(old_xyz[:, :2] / .5).astype(int))
        wanted = active | collar
        take = np.array([tuple(k) in wanted for k in keys])
        outside_old = ~intersects_xy(old_footprint,xyz[ids,0],xyz[ids,1])
        seeds = np.union1d(old_ids, ids[take & outside_old & reviewed])
        all_ids = np.flatnonzero(valid)
        all_ids = all_ids[~intersects_xy(old_footprint,xyz[all_ids,0],xyz[all_ids,1])]
        if selection_region is not None:
            all_ids = all_ids[intersects_xy(selection_region,xyz[all_ids,0],xyz[all_ids,1])]
        bins = np.floor(xyz[all_ids, :2] / .5).astype(int)
        pool = np.union1d(old_ids, all_ids[[tuple(k) in wanted for k in bins]])
        # Keep original duplicate observations in the archive, but choose the
        # lowest original height for a height-field XY. Never invent a point.
        order = np.lexsort((pool, xyz[pool, 2], xyz[pool, 1], xyz[pool, 0]))
        pool = pool[order]
        unique = np.r_[True, np.any(xyz[pool[1:], :2] != xyz[pool[:-1], :2], axis=1)]
        pool = np.sort(pool[unique])
        if not np.isin(seeds, pool).all():
            raise ValueError('Duplicate XY rule would discard a retained seed')
        region = MultiPoint(xyz[seeds, :2]).convex_hull
        polygon = list(region.exterior.coords)
        selected = pool[refine_source_coverage(xyz[pool], np.searchsorted(pool, seeds), polygon)]
        old_to_selected = np.searchsorted(selected,old_ids)
        if not np.array_equal(selected[old_to_selected],old_ids):
            raise ValueError('Original cap IDs missing before constraint recovery')
        preserved_faces = old_to_selected[old_faces]
        faces = constrained_extension(xyz[selected],preserved_faces,allowed_region=selection_region)
        if not np.array_equal(xyz[selected[faces[:len(old_faces)]]],old_xyz[old_faces]):
            raise ValueError('Original roof triangles changed')
        used = np.unique(faces)
        mapping = np.full(len(selected), -1, int); mapping[used] = np.arange(len(used))
        selected, faces = selected[used], mapping[faces]
        vertices = xyz[selected]
        if not np.isin(old_ids, selected).all():
            raise ValueError('New triangulation discarded an original cap vertex')
        footprint = union_all([Polygon(p) for p in vertices[faces, :2]])
        lost_area = old_footprint.difference(footprint).area
        if lost_area > 1e-10:
            raise ValueError('Original cap coverage was lost')
        original_vertex_count = len(vertices)
        vertices, faces, fan_mapping = separate_vertex_fans(vertices, faces)
        selected = selected[fan_mapping]
        solid_vertices, solid_faces, kinds, solid_report = close_cap_below_retained_terrain(vertices, faces, floor)
        all_edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
        edges, n = np.unique(all_edges, axis=0, return_counts=True)
        boundary = edges[n == 1]
        parent_z = sampler.sample(vertices[:, 0], vertices[:, 1])
        boundary_ids = np.unique(boundary)
        boundary_gap = vertices[boundary_ids, 2] - parent_z[boundary_ids]
        old_centers = old_xyz[old_faces].mean(axis=1)
        old_delta = sample_cap(vertices, faces, old_centers[:, :2]) - old_centers[:, 2]
        if not np.isfinite(old_delta).all() or abs(old_delta).max()>1e-10:
            raise ValueError('Constrained extension changed original roof heights')
        support_counts = {tuple(k): int(c) for k, c in zip(keys, counts)}
        support = np.array([support_counts.get(tuple(k), 1) for k in np.floor(vertices[:, :2] / .5).astype(int)])
        output.mkdir()
        cap_path = output / 'original_return_rock_cap.npz'
        np.savez_compressed(cap_path, vertices_m=vertices, triangles=faces, original_return_index=selected,
            original_classification=classes[selected], bin_support_count=support,
            original_height_above_dem_m=data['height_above_flattened_surface_m'][selected],
            retained_parent_height_m=parent_z, boundary_edges=boundary,
            solid_vertices_m=solid_vertices, solid_triangles=solid_faces, solid_face_kind=kinds)
        report = dict(previous)
        report.update(status='source_connected_boundary_candidate_not_accepted', cap_path=cap_path.relative_to(ROOT).as_posix(),
            cap_sha256=sha(cap_path), previous_cap_manifest_sha256=sha(previous_path), previous_cap_sha256=previous['cap_sha256'],
            vertex_count=len(vertices), triangle_count=len(faces), projected_area_m2=footprint.area,
            boundary_edge_count=len(boundary), boundary_height_gap_range_m=[float(boundary_gap.min()), float(boundary_gap.max())],
            selected_classification_counts={str(int(c)): int((classes[selected] == c).sum()) for c in np.unique(classes[selected])},
            source_connected_selection=dict(bin_m=.5,minimum_count=2,clearance_prior_m=.3,connectivity='four face neighbors',
                active_bins=len(active),ground_collar_bins=len(collar),unsupported_directed_edges=unsupported,
                capture_interior_eligible_bins=len(ids),raw_pool_count=len(pool),selected_seed_count=len(seeds),
                reviewed_selection_eligible_bins=int(reviewed.sum()),
                excluded_by_reviewed_selection_bins=int((~reviewed).sum()),
                unsupported_edges_include_selection_exclusions=selection_region is not None,
                unsupported_edges_are_not_ground=True,original_region_is_seed_not_outline=True),
            reviewed_extension_selection=selection_identity,
            selection=dict(bin_size_prior_m=.5,minimum_original_returns_per_bin=2,
                clearance_connectivity_prior_m=.3,maximum_triangle_edge_prior_m=1.,water_mask_required=False,
                previous_seed_vertices_forced=True,near_ground_collar_uses_original_points=True),
            duplicated_original_vertices_for_disconnected_fans=len(vertices)-original_vertex_count,
            original_roof_triangles_retained_exactly=True,
            original_cap_vertices_retained=len(old_ids), original_cap_area_lost_m2=lost_area,
            original_cap_centroid_delta_min_median_max_m=np.percentile(old_delta,[0,50,100]).tolist(),
            boundary_gap_quantiles_m=np.percentile(boundary_gap,[0,25,50,75,90,100]).tolist(),
            boundary_vertices_above_clearance_prior=int((boundary_gap>.3).sum()),
            xy_bounds_m=[vertices[:,:2].min(0).tolist(),vertices[:,:2].max(0).tolist()],
            inferred_solid=dict(internal_floor_m=floor,**solid_report), engine_collision_verified=False,
            hydraulic_recooked=False,game_integrated=False,production_promoted=False)
        # Do not copy numerical claims about the previous candidate into this one.
        for key in ('original_seed_count','original_pool_count','additional_original_points_for_coverage',
                    'selected_returns_outside_old_water_mask','corroborated_single_return_vertices',
                    'vertex_height_above_retained_parent_range_m','maximum_triangle_centroid_error_m','original_observation_comparison'):
            report.pop(key,None)
        (output / 'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        (output / 'native-probes.json').write_text(json.dumps(native_collision_probes(vertices,faces,solid_vertices,solid_faces,kinds,report['cap_sha256']),indent=2)+'\n')
        return {k:report[k] for k in ('vertex_count','triangle_count','projected_area_m2','boundary_gap_quantiles_m',
            'boundary_vertices_above_clearance_prior','xy_bounds_m','original_cap_centroid_delta_min_median_max_m')} | dict(
            active_bins=len(active),ground_collar_bins=len(collar),unsupported_edges=len(unsupported))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--support-region',type=Path,
        help='Source-bound interpreted extension selection; never a measured outline')
    args=parser.parse_args()
    print(json.dumps(run(args.previous,args.output,args.support_region),indent=2),flush=True)
