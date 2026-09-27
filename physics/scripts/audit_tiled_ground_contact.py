"""Compare saved in-game contact probes with archived render/collision triangles.

This is an independent source-height check, not a new game run or proof of the
identity/completeness of all colliders in the scene. Missing coverage fails;
no raster interpolation, nearest-point snapping or extrapolation is allowed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_path(value):
    path = (ROOT / value).resolve()
    require(path.is_relative_to(ROOT), 'Source outside repository')
    return path


def verified(value, expected):
    path = source_path(value)
    require(sha(path) == expected, f'Source hash mismatch: {path}')
    return path


def world_vertices(local_m, translation_cm, scale):
    """FBX local centimetres are float32; actor transform is double precision."""
    local_m = np.asarray(local_m, dtype=np.float64)
    translation_cm, scale = np.asarray(translation_cm), np.asarray(scale)
    require(local_m.ndim == 2 and local_m.shape[1] == 3, 'Expected XYZ vertices')
    require(translation_cm.shape == scale.shape == (3,), 'Expected three-axis transform')
    require(np.isfinite(local_m).all() and np.isfinite(translation_cm).all()
            and np.isfinite(scale).all() and (scale != 0).all(), 'Invalid transform/vertices')
    return (local_m * 100).astype(np.float32).astype(np.float64) * scale + translation_cm


def triangle_heights(vertices, triangles, xy):
    """Highest intersected triangle, retaining actual diagonals and holes."""
    require(np.issubdtype(triangles.dtype, np.integer) and triangles.ndim == 2
            and triangles.shape[1] == 3, 'Expected integer triangle triplets')
    require(np.all((triangles >= 0) & (triangles < len(vertices))), 'Invalid triangle index')
    require(np.isfinite(vertices).all() and np.isfinite(xy).all(), 'Nonfinite geometry/query')
    faces = vertices[triangles]
    lo, hi = faces[:, :, :2].min(axis=1), faces[:, :, :2].max(axis=1)
    heights = np.full(len(xy), np.nan)
    face_ids = np.full(len(xy), -1, dtype=int)
    for i, p in enumerate(xy):
        ids = np.flatnonzero(np.all((p >= lo) & (p <= hi), axis=1))
        if not len(ids):
            continue
        a, b, c = np.moveaxis(faces[ids], 1, 0)
        u, v, q = b[:, :2] - a[:, :2], c[:, :2] - a[:, :2], p - a[:, :2]
        det = u[:, 0]*v[:, 1] - u[:, 1]*v[:, 0]
        valid = det != 0
        ids, a, b, c, u, v, q, det = [x[valid] for x in (ids, a, b, c, u, v, q, det)]
        if not len(ids):
            continue
        wb = (q[:, 0]*v[:, 1] - q[:, 1]*v[:, 0])/det
        wc = (u[:, 0]*q[:, 1] - u[:, 1]*q[:, 0])/det
        wa = 1 - wb - wc
        inside = (wa >= -1e-12) & (wb >= -1e-12) & (wc >= -1e-12)
        z = wa*a[:, 2] + wb*b[:, 2] + wc*c[:, 2]
        z[~inside] = -np.inf
        best = int(np.argmax(z))
        if np.isfinite(z[best]):
            heights[i], face_ids[i] = z[best], ids[best]
    return heights, face_ids


def compare(probes, heights, tolerance_cm=.002):
    require(len(probes) > 0 and len(probes) == len(heights), 'Nonempty matching probes required')
    require(np.isfinite(tolerance_cm) and tolerance_cm > 0, 'Positive finite tolerance required')
    rows = []
    for index, (probe, height) in enumerate(zip(probes, heights)):
        for key in ('ground_hit', 'support_available', 'support_wet', 'raw_available', 'raw_wet'):
            require(type(probe[key]) is bool, f'Boolean required: {key}')
        for key in ('x_cm', 'y_cm', 'ground_z_cm', 'water_z_cm'):
            require(type(probe[key]) in (int, float) and np.isfinite(probe[key]), f'Finite number required: {key}')
        covered = bool(np.isfinite(height))
        buried = bool(probe['water_z_cm'] <= height) if covered else None
        expected_wet = bool(probe['raw_available'] and probe['raw_wet'] and not buried) if covered else None
        error = abs(probe['ground_z_cm'] - float(height)) if covered and probe['ground_hit'] else None
        passed = (covered and probe['ground_hit'] and probe['support_available']
                  and error <= tolerance_cm and probe['support_wet'] == expected_wet)
        rows.append(dict(probe_index=index, covered=covered, source_ground_cm=float(height) if covered else None,
                         absolute_error_cm=error, source_buried=buried, passed=bool(passed)))
    errors = [r['absolute_error_cm'] for r in rows if r['absolute_error_cm'] is not None]
    return dict(passed=all(r['passed'] for r in rows), probes=len(rows),
                uncovered=sum(not r['covered'] for r in rows),
                failed=sum(not r['passed'] for r in rows),
                source_buried=sum(r['source_buried'] is True for r in rows),
                maximum_ground_error_cm=max(errors) if errors else None,
                tolerance_cm=tolerance_cm, rows=rows)


def audit(capture_path, replacement_paths):
    capture = json.loads(capture_path.read_text(encoding='utf-8-sig'))
    probes = capture['ground_contact_probes']
    require(bool(probes), 'Missing probes')
    xy = np.array([[p['x_cm'], p['y_cm']] for p in probes], dtype=float)
    require(np.isfinite(xy).all(), 'Nonfinite probes')
    heights, owners = np.full(len(xy), np.nan), [None]*len(xy)
    inputs = {str(capture_path.relative_to(ROOT)): sha(capture_path)}
    selected = []
    for replacement_path in replacement_paths:
        replacement = json.loads(replacement_path.read_text())
        source = verified(replacement['source_tile_manifest'], replacement['source_tile_manifest_sha256'])
        original = json.loads(source.read_text())
        inputs[str(replacement_path.relative_to(ROOT))] = sha(replacement_path)
        inputs[str(source.relative_to(ROOT))] = sha(source)
        replacements = {t['name']: t for t in replacement['tiles']}
        require(len(replacements) == len(replacement['tiles']), 'Duplicate replacement tile')
        originals = {t['name']: t for t in original['tiles']}
        require(len(originals) == len(original['tiles']) and replacements.keys() <= originals.keys(), 'Invalid tile membership')
        # Conservative XY bounds used only to avoid decompressing distant tiles.
        # Actual geometry bounds and original triangles decide all coverage.
        width = original['maximum_tile_width_m'] * 100
        require(np.isfinite(width) and width > 0, 'Positive finite tile extent required')
        for name, old in originals.items():
            tile = replacements.get(name, old)
            for key in ('actor_translation_cm', 'actor_scale', 'origin_utm_m', 'vertex_count', 'triangle_count'):
                require(tile[key] == old[key], f'Changed source metadata: {name}/{key}')
            if name in replacements:
                require(tile['retained_source_path'] == old['path'] and tile['retained_source_sha256'] == old['sha256'], 'Wrong retained tile')
            origin = np.asarray(tile['actor_translation_cm'])[:2]
            extent = width * np.abs(np.asarray(tile['actor_scale'])[:2])
            ids = np.flatnonzero(np.all(np.abs(xy-origin) <= extent + .01, axis=1))
            if not len(ids):
                continue
            path = verified(tile['path'], tile['sha256'])
            with np.load(path, allow_pickle=False) as packed:
                vertices = world_vertices(packed['xyz_local_m'], tile['actor_translation_cm'], tile['actor_scale'])
                triangles = packed['triangles']
                require(len(vertices) == tile['vertex_count'] and len(triangles) == tile['triangle_count'], 'Geometry count mismatch')
                require(np.all(np.abs(vertices[:, :2]-origin) <= extent+.01), 'Declared tile extent does not enclose vertices')
                z, faces = triangle_heights(vertices, triangles, xy[ids])
            selected.append(dict(name=name, path=tile['path'], sha256=tile['sha256'], covered=int(np.isfinite(z).sum())))
            for i, height, face in zip(ids, z, faces):
                if np.isfinite(height) and (not np.isfinite(heights[i]) or height > heights[i]):
                    heights[i], owners[i] = height, dict(tile=name, source_face=int(face))
    result = compare(probes, heights)
    for row, owner in zip(result['rows'], owners):
        row['source'] = owner
    result.update(schema='raftsim.tiled_ground_contact.v1', source_inputs=inputs, tiles=selected,
                  scope=__doc__, full_scene_collider_identity_verified=False,
                  measured_bathymetry=False, reconstruction_accepted=False,
                  detail_frame_sequence=capture.get('detail_frame_sequence'),
                  script_sha256=sha(Path(__file__)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--replacement-manifest', type=Path, action='append', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    require(not args.report.exists(), 'Fresh output required')
    result = audit(args.capture.resolve(), [p.resolve() for p in args.replacement_manifest])
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('rows', 'tiles')}, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
