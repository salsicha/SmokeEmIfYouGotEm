"""Bind provisional class-20 observations to the installed reconstruction source.

Source-union predictions only; a separate read-only engine trace is required.
The observation is not automatically a rock, missing geometry, or bathymetry.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_eldorado_ignored_ground import ROOT, SOURCE, SOURCE_SHA
from south_fork_rock_union import SourceRockUnion, sha
from south_fork_registered_mesh import RegisteredMeshSampler
from prepare_south_fork_union_collision import engine_position
from build_troublemaker_dem_rock_cap import sample_cap
from source_native_triangle_hash import triangle_hash


def envelope_union(bed, roof):
    bed, roof = np.asarray(bed), np.asarray(roof)
    if bed.shape != roof.shape or not np.isfinite(bed).all() or np.isinf(roof).any():
        raise ValueError('Finite bed and matching roof samples required; NaN means outside roof')
    return np.where(np.isnan(roof), bed, np.maximum(bed, roof))


def observation_rows(rows, xyz, classes, heights, world_origin, datum):
    ids = np.array([r['original_return_index'] for r in rows])
    if (ids.ndim != 1 or not len(ids) or not np.issubdtype(ids.dtype, np.integer)
            or len(np.unique(ids)) != len(ids) or np.any(ids < 0) or np.any(ids >= len(xyz))):
        raise ValueError('Unique original source indices required')
    heights = np.asarray(heights)
    if heights.shape != ids.shape or not np.isfinite(heights).all():
        raise ValueError('Every observation needs a finite source-union height')
    if not np.all(np.asarray(classes)[ids] == 20):
        raise ValueError('Expected original ignored-ground classification')
    queries = np.array([r['source_utm_navd88_m'] for r in rows])
    if not np.array_equal(queries, xyz[ids]) or not np.isfinite(queries).all():
        raise ValueError('Observation coordinates no longer match original returns')
    if np.shape(world_origin) != (2,) or not np.isfinite([*world_origin, datum]).all():
        raise ValueError('Finite engine frame required')
    return [dict(original_return_index=int(i), source_utm_navd88_m=p.tolist(),
        source_union_navd88_m=float(z), observation_minus_union_m=float(p[2]-z),
        world_position_cm=engine_position(p[:2], z, world_origin, datum))
        for i, p, z in zip(ids, queries, heights)]


def prepare(screen_path, geometry_path, install_path, envelope_dir):
    screen = json.loads(screen_path.read_text())
    geometry = json.loads(geometry_path.read_text())
    install = json.loads(install_path.read_text())
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in (screen_path, geometry_path, install_path, SOURCE)}
    if sha(SOURCE) != SOURCE_SHA or screen['source_sha256'] != SOURCE_SHA:
        raise ValueError('Changed original return archive')
    cap_path = ROOT / geometry['rock_cap_manifest']
    cap = json.loads(cap_path.read_text())
    origin = np.asarray(cap['origin_utm_and_vertical_datum_m'])
    parent = ROOT / cap['source_mesh_path']
    revision = ROOT / geometry['terrain_revision_manifest']
    union = SourceRockUnion(cap_path, ROOT, parent, origin[:2], origin[2], revision)
    if union.identity != geometry['terrain_union']:
        raise ValueError('Compound geometry identity mismatch')
    descriptor_path = ROOT / install['descriptor']
    if sha(descriptor_path) != install['descriptor_sha256']:
        raise ValueError('Installed descriptor changed')
    descriptor = json.loads(descriptor_path.read_text())
    # The descriptor closes over the exact compound-geometry manifest.
    if descriptor['dependencies'].get(geometry_path.relative_to(ROOT).as_posix()) != sha(geometry_path):
        raise ValueError('Geometry is not in installed descriptor dependency closure')
    for p in (cap_path, parent, revision, descriptor_path):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    envelope_path = envelope_dir/'rock_envelope.npz'
    build_path = envelope_dir/'rock_envelope_build.json'
    envelope_install_path = envelope_dir/'rock_envelope_install.json'
    build = json.loads(build_path.read_text())
    envelope_install = json.loads(envelope_install_path.read_text())
    if (sha(envelope_path) != build['output_sha256']
            or sha(envelope_path) != envelope_install['envelope_sha256']
            or build['source_cap_sha256'] != cap['cap_sha256']
            or envelope_install['rock_actor'] != install['new_rock_actor']):
        raise ValueError('Current envelope lineage mismatch')
    for p in (envelope_path, build_path, envelope_install_path, ROOT/cap['cap_path']):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    with np.load(envelope_path, allow_pickle=False) as envelope:
        roof_vertices = envelope['solid_vertices_m'][:len(union.xyz)].copy()
        roof_faces = envelope['solid_triangles'][envelope['solid_face_kind'] == 0].copy()
        if (not np.array_equal(roof_vertices[:, :2], union.xyz[:, :2])
                or not np.array_equal(roof_faces, union.faces)
                or not np.isfinite(roof_vertices).all()
                or np.any(roof_vertices[:, 2] > union.xyz[:, 2])):
            raise ValueError('Envelope must preserve XY/topology and be lower-only')
        native_hash = triangle_hash(envelope['solid_vertices_m']*100,
                                    envelope['solid_triangles'][:, [0,2,1]])
        native_count = len(envelope['solid_triangles'])
    with np.load(parent, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    with np.load(SOURCE, allow_pickle=False) as source:
        xyz = np.column_stack([source[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])
        classes = source['classification']
        queries = np.array([r['source_utm_navd88_m'] for r in screen['rows']])
        base = sampler.sample(*(queries[:, :2]-origin[:2]).T)+origin[2]
        bed, revised = union.terrain_revision.apply(queries[:, 0], queries[:, 1], base)
        roof = sample_cap(roof_vertices, roof_faces, queries[:, :2]-origin[:2])+origin[2]
        heights = envelope_union(bed, roof)
        owners = np.where(heights > bed, 5, np.where(revised, 6, 0))
        rows = observation_rows(screen['rows'], xyz, classes, heights,
                                geometry['world_origin_utm_m'], geometry['vertical_datum_navd88_m'])
    for row, owner, base_z in zip(rows, owners, base):
        row.update(source_union_owner=int(owner), registered_base_navd88_m=float(base_z))
    for name, digest in inputs.items():
        if sha(ROOT/name) != digest:
            raise ValueError('Input changed during source query: '+name)
    meshes = [m for m in install['meshes'] if m['asset'] != envelope_install['previous_mesh']]
    if len(meshes) != 1:
        raise ValueError('Expected one retained ground mesh')
    meshes.append(dict(asset=envelope_install['new_mesh'], sha256=envelope_install['new_mesh_sha256'],
        native_source=dict(collision_source_sha256=native_hash, triangle_count=native_count)))
    return dict(schema='raftsim.ignored_ground_union_probes.v1', rows=rows,
        source_inputs=inputs, installed_meshes=meshes,
        installed_actor_names=[install['original_terrain_actor'], install['new_rock_actor']],
        translation_cm=descriptor['translation_cm'], level=install['level'],
        geometry_modified=False, engine_collision_verified=False,
        interpretation=__doc__)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--screen', type=Path, required=True)
    p.add_argument('--geometry', type=Path, required=True)
    p.add_argument('--install', type=Path, required=True)
    p.add_argument('--envelope', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp output required')
    result = prepare(a.screen.resolve(), a.geometry.resolve(), a.install.resolve(), a.envelope.resolve())
    with out.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(result['rows'], indent=2))
