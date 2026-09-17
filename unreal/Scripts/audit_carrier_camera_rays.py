"""Map screenshot probes to exported CPU water triangles, not visible GPU pixels."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_submitted_carrier_shape import (
    SOURCE_FIELDS_V2, VERTEX_FIELDS, gradients, raw_stage, read_table, summarize,
)


def camera_ray(view, meta, pixel):
    if view.get('schema') != 'raftsim.carrier_view.v1':
        raise ValueError('Wrong camera schema')
    for key in ('game_frame', 'world_seconds'):
        if key not in meta or not np.isfinite(meta[key]) or view.get(key) != meta[key]:
            raise ValueError('Camera/carrier epoch mismatch')
    matrix = np.asarray(view['world_cm_to_clip_row_matrix'], dtype=float)
    rect = np.asarray(view['constrained_view_rect'], dtype=float)
    pixel = np.asarray(pixel, dtype=float)
    if matrix.shape != (4, 4) or rect.shape != (4,) or pixel.shape != (2,) or not all(
            np.isfinite(v).all() for v in (matrix, rect, pixel)):
        raise ValueError('Invalid camera/probe')
    extent = rect[2:] - rect[:2]
    if np.any(extent <= 0) or np.any(pixel < rect[:2]) or np.any(pixel >= rect[2:]):
        raise ValueError('Probe outside constrained viewport')
    ndc = (pixel - rect[:2]) / extent * [2., -2.] + [-1., 1.]
    # UE reversed Z: near=1, infinite far=0. Use a finite point on the ray.
    homogeneous = np.array([[*ndc, 1., 1.], [*ndc, .01, 1.]]) @ np.linalg.inv(matrix)
    if np.any(homogeneous[:, 3] == 0):
        raise ValueError('Nonfinite unprojection')
    points = homogeneous[:, :3] / homogeneous[:, 3, None] * .01
    direction = points[1] - points[0]
    length = np.linalg.norm(direction)
    if not np.isfinite(points).all() or not np.isfinite(length) or length == 0:
        raise ValueError('Invalid camera ray')
    return points[0], direction / length


def nearest_triangle(origin, direction, xyz):
    """Two-sided Moller-Trumbore. Zero/parallel/backward/missing hits excluded."""
    if xyz.ndim != 3 or xyz.shape[1:] != (3, 3) or not all(
            np.isfinite(a).all() for a in (origin, direction, xyz)):
        raise ValueError('Invalid ray/triangles')
    edge1, edge2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
    p = np.cross(np.broadcast_to(direction, edge2.shape), edge2)
    det = np.einsum('ij,ij->i', edge1, p)
    inverse = np.divide(1., det, out=np.zeros_like(det), where=det != 0)
    offset = origin - xyz[:, 0]
    u = np.einsum('ij,ij->i', offset, p) * inverse
    q = np.cross(offset, edge1)
    v = (q @ direction) * inverse
    distance = np.einsum('ij,ij->i', edge2, q) * inverse
    valid = (det != 0) & (u >= 0) & (v >= 0) & (u+v <= 1) & (distance >= 0)
    if not valid.any():
        return None
    index = int(np.argmin(np.where(valid, distance, np.inf)))
    return index, float(distance[index]), np.array([1-u[index]-v[index], u[index], v[index]])


def probe(meta, view, vertices, triangles, source, normals, pixels):
    if meta.get('schema') != 'raftsim.submitted_carrier_shape.v2':
        raise ValueError('Current source/target export required')
    summarize(meta, vertices, triangles, source, 30.)  # Validate original evidence.
    if normals.shape != (len(vertices), 4) or not np.isfinite(normals).all() or not np.array_equal(
            normals[:, 0], vertices[:, 0]):
        raise ValueError('Missing/reordered CPU normals')
    ids = triangles.astype(int)
    xyz = vertices[:, 1:4] * .01
    xyz[:, 2] += vertices[:, 6] * .01
    rows = []
    for pixel in pixels:
        origin, direction = camera_ray(view, meta, pixel)
        hit = nearest_triangle(origin, direction, xyz[ids])
        row = dict(pixel=list(pixel), hit=None)
        if hit is not None:
            index, distance, barycentric = hit
            selected = ids[index]
            points = xyz[selected]
            xy = points[None, :, :2]
            heights = dict(carrier=vertices[selected, 3]*.01,
                           crest=(vertices[selected, 4]+vertices[selected, 5])*.01,
                           detail=vertices[selected, 6]*.01)
            heights['base'] = heights['carrier']-heights['crest']-meta['render_lift_cm']*.01
            heights['displayed'] = points[:, 2]
            components = {k: gradients(xy, z[None])[0] for k, z in heights.items()}
            raw, valid = raw_stage(points[:, :2], source, meta['source_nx'], meta['source_ny'], meta['world_y_sign'])
            if valid.all():
                target, _ = raw_stage(points[:, :2], source, meta['source_nx'], meta['source_ny'], meta['world_y_sign'], 6)
                components['cached_source'] = gradients(xy, raw[None])[0]
                target_g = gradients(xy, target[None])[0]
                components['target_minus_source'] = target_g-components['cached_source']
                components['submitted_base_minus_target'] = components['base']-target_g
            normal = barycentric @ normals[selected, 1:]
            face_normal = np.r_[-components['displayed'], 1.]
            normal_length, face_length = np.linalg.norm(normal), np.linalg.norm(face_normal)
            position = barycentric @ points
            nx, ny = meta['source_nx'], meta['source_ny']
            spacing = np.array([source[1, 1]-source[0, 1], source[nx, 2]-source[0, 2]])
            cell = np.floor((position[:2]*[1, meta['world_y_sign']]-source[0, 1:3])/spacing).astype(int)
            corners = []
            if np.all(cell >= 0) and np.all(cell < [nx-1, ny-1]):
                root = cell[1]*nx+cell[0]
                for corner in source[[root, root+1, root+nx, root+nx+1]]:
                    corners.append(dict(zip(SOURCE_FIELDS_V2, corner.tolist())))
            row['hit'] = dict(triangle=index, vertex_ids=selected.tolist(),
                world_m=position.tolist(), distance_from_near_plane_m=distance,
                barycentric=barycentric.tolist(), vertices_world_m=points.tolist(),
                slope_degrees=float(np.degrees(np.arctan(np.linalg.norm(components['displayed'])))),
                component_gradient={k: g.tolist() for k, g in components.items()},
                source_cell_corners=corners,
                fully_wet_source_comparison=bool(valid.all()), cpu_normal=normal.tolist(),
                cpu_normal_face_angle_degrees=float(np.degrees(np.arccos(np.clip(
                    np.dot(normal, face_normal)/(normal_length*face_length), -1., 1.)))) if normal_length else None)
        rows.append(row)
    return dict(schema='raftsim.carrier_camera_rays.v1', accepted=False,
        game_frame=meta['game_frame'], world_seconds=meta['world_seconds'],
        detail_sequence=meta['detail_sequence'], probes=rows,
        limitations='Nearest exported CPU water triangle, NOT guaranteed visible water. No terrain/crew occlusion, material vertex displacement, GPU latency, jitter or refraction. CPU normals are not optical normals. Same request epoch is not a GPU fence. Dry-boundary source comparisons are unavailable, not extrapolated.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('view', type=Path)
    parser.add_argument('--pixel', type=float, nargs=2, action='append', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    paths = [args.capture, args.view] + [Path(str(args.capture)+suffix) for suffix in (
        '.vertices.csv', '.triangles.csv', '.source.csv', '.normals.csv')]
    meta, view = [json.loads(p.read_text(encoding='utf-8-sig')) for p in paths[:2]]
    tables = [read_table(p, fields) for p, fields in zip(paths[2:], [VERTEX_FIELDS,
        ['a', 'b', 'c'], SOURCE_FIELDS_V2, ['id', 'normal_x', 'normal_y', 'normal_z']])]
    result = probe(meta, view, *tables, args.pixel)
    result['input_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
