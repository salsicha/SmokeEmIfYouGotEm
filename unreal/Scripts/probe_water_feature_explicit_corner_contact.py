"""Locate explicit-wall native contact errors and their actual eight-node fields.

Read-only diagnostic: all primary records and original derived samples retained.
No solver substitution, source mutation, particle projection or surface clipping.
"""
import argparse
import ctypes
import dis
import hashlib
import json
from pathlib import Path
import sys
import bpy
import manta
import numpy as np
import openvdb
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_authored_contact import contacts
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import cleanup, grid_array, vector_data_address
from water_feature_geometry import world_coordinates
from audit_water_feature_mesh_contact import topology, interior_distance


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def signed_distance(point, solids):
    # Exact closed-solid BVH distance/parity at the queried point, not SDF
    # interpolation or triangle normals. Union SDF is minimum per-solid SDF.
    values = {}
    for name, (_, _, tree) in solids.items():
        _, _, _, distance = tree.find_nearest(Vector(point))
        if distance is None:
            raise ValueError('No nearest actual collider')
        values[name] = -distance if interior_distance(tree, point) > 0 else distance
    return values


def annotate(row, fields, solids, origin, h):
    for points in row.values():
        for data in points.values():
            for item in data['deepest_points']:
                point = np.asarray(item['world_m'])
                cell = np.floor((point-origin)/h-.5).astype(int)
                stencil = []
                for dx in (0, 1):
                    for dy in (0, 1):
                        for dz in (0, 1):
                            index = cell+np.array([dx, dy, dz])
                            world = origin+(index+.5)*h
                            exact = signed_distance(world, solids)
                            stencil.append(dict(index=index.tolist(), world_m=world.tolist(),
                                final_obstacle_m=float(fields['phi_obstacle'][tuple(index)]*h),
                                input_obstacle_m=float(fields['phi_obstacle_inflow'][tuple(index)]*h),
                                exact_union_m=min(exact.values()), exact_solids_m=exact,
                                flags=int(fields['flags'][tuple(index)])))
                exact = signed_distance(point, solids)
                item.update(exact_union_m=min(exact.values()), exact_solids_m=exact,
                    interpolation_stencil=stencil,
                    interpolation_fraction=((point-origin)/h-.5-cell).tolist())


def native_primary(root, frame, shape, origin, h, displayed):
    scope = {}; error = None; positions = None; flags = None
    try:
        scope['s99'] = manta.Solver(name='owned_explicit_corner_primary', gridSize=manta.vec3(*shape), dim=3)
        scope['pp_s99'] = scope['s99'].create(manta.BasicParticleSystem, name='particles')
        scope['pVel_pp99'] = scope['pp_s99'].create(manta.PdataVec3, name='particles_velocity')
        if manta.load(name=str(root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'),
                      objects=[scope['pVel_pp99'], scope['pp_s99']], worldSize=6.75) != 1:
            raise ValueError('Native typed primary load failed')
        count = len(displayed)
        if scope['pp_s99'].pySize() != count:
            raise ValueError('Primary count mismatch')
        address = vector_data_address(scope['pp_s99'].getDataPointer(), count, 16)
        records = np.frombuffer(bytes((ctypes.c_ubyte*(count*16)).from_address(address)),
                               dtype=np.dtype([('position', '<f4', 3), ('flags', '<i4')]))
        positions = records['position']*h+origin
        flags = records['flags'].copy()
        np.testing.assert_allclose(positions, displayed, atol=1e-6, rtol=1e-6)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'; exc.__traceback__ = None
    finally:
        cleanup(scope, '99')
    if error:
        raise RuntimeError(error)
    return positions, flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text()); control = audit['controls'][0]
    source = Path(control['source_blend']); root = source.parent
    if not audit['complete'] or audit['accepted'] or Path(bpy.data.filepath).resolve() != source.resolve():
        raise ValueError('Exact completed unaccepted native control required')
    shape = tuple(control['shape']); origin = np.asarray(control['origin_m']); h = control['cell_m']
    if shape != (90, 31, 42) or abs(h-.075) > 1e-9:
        raise ValueError('Explicit-wall control required')
    hashes = {str(p.resolve()): digest(p) for p in (Path(__file__), args.audit, source)}
    for name in ('probe_water_feature_authored_contact.py', 'probe_water_feature_native_transport.py',
                 'probe_water_feature_solver_stages.py', 'water_feature_geometry.py',
                 'audit_water_feature_mesh_contact.py', 'water_feature_field_surface.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    domain = bpy.data.objects['Feature liquid']
    domain.modifiers[0].domain_settings.cache_directory = str(root/'cache')
    bpy.context.scene.frame_set(145); space, identifier = actual_space(shape)
    before = {name: hashlib.sha256(grid_array(space[f'{name}_s{identifier}'], shape).tobytes()).hexdigest()
              for name in ('phi', 'phiTmp')}
    compiled = [dict(name=name, instructions=[dict(offset=i.offset, opname=i.opname, argrepr=i.argrepr)
        for i in dis.get_instructions(space[f'{name}_{identifier}'])])
        for name in ('liquid_step', 'liquid_adaptive_step')]
    solids = {}
    for entry in control['colliders']:
        name = entry['name']; obj = bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices = world_coordinates([v.co[:] for v in mesh.vertices], obj.matrix_world)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int64)
            if topology(triangles) != dict(boundary_edges=0, nonmanifold_edges=0):
                raise ValueError('Actual closed collider required')
            if hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest() != entry['geometry_sha256']:
                raise ValueError('Authored collider changed')
            solids[name] = (vertices.min(0), vertices.max(0),
                           BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True))
        finally:
            obj.to_mesh_clear()
    if len(solids) != 8:
        raise ValueError('All eight physical colliders required')
    rows = []
    for frame in (145, 169, 191):
        data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'; sha = digest(data)
        if audit['dependency_sha256'][str(data.resolve())] != sha:
            raise ValueError('Pinned native DATA changed')
        hashes[str(data.resolve())] = sha
        fields = {}
        for name, dtype in (('phi', np.float32), ('phi_obstacle', np.float32),
                            ('phi_obstacle_inflow', np.float32), ('flags', np.int32)):
            grid = openvdb.read(str(data), name); array = np.empty(shape, dtype)
            grid.copyToArray(array); fields[name] = array
        bpy.context.scene.frame_set(frame)
        obj = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        particles = next(p for p in obj.particle_systems if p.name.lower() == 'liquid')
        displayed = np.empty(len(particles.particles)*3, np.float32)
        particles.particles.foreach_get('location', displayed)
        positions, flags = native_primary(root, frame, shape, origin, h, displayed.reshape(-1, 3))
        derived = next(r for r in audit['rows'] if r['frame'] == frame and r['refinement'] == 2)
        for p in derived['arrays'].values():
            if digest(p) != audit['outputs_sha256'][p]:
                raise ValueError('Pinned extraction changed')
            hashes[p] = digest(p)
        vertices = np.load(derived['arrays']['positions'], allow_pickle=False)
        triangles = np.load(derived['arrays']['triangles'], allow_pickle=False)
        cohorts = {name: {solid: contacts(points, s, fields, origin, h) for solid, s in solids.items()}
                   for name, points in (('primary', positions), ('field_vertices', vertices),
                                        ('field_triangle_centers', vertices[triangles].mean(1)))}
        annotate(cohorts, fields, solids, origin, h)
        unique, counts = np.unique(flags, return_counts=True)
        rows.append(dict(frame=frame, primary_native_display_match=True,
            all_primary_flags_retained=dict(zip(map(str, unique), map(int, counts))), cohorts=cohorts))
        for cohort, items in cohorts.items():
            for solid, info in items.items():
                if info['deepest_points']:
                    point = info['deepest_points'][0]
                    print('EXPLICIT_CORNER_WORST', root.name, frame, cohort, solid,
                          point['world_m'], point['depth_inside_m'], point['field_values_cells'], flush=True)
    bpy.context.scene.frame_set(145); space, identifier = actual_space(shape)
    if any(hashlib.sha256(grid_array(space[f'{name}_s{identifier}'], shape).tobytes()).hexdigest() != sha
           for name, sha in before.items()):
        raise ValueError('Read-only probe changed engine fields')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Read-only probe changed pinned sources')
    report = dict(complete=True, accepted=False, originals_unchanged=True, actual_fields_unchanged=True,
        dependency_sha256=hashes, source_blend=str(source.resolve()), shape=list(shape), origin_m=origin.tolist(),
        cell_m=h, frames=rows, compiled_native_steps=compiled, scope=__doc__,
        limitations='Vertex/triangle-center/primary-center tests with closed BVH parity at1um; no exhaustive triangle or sphere/trajectory checks. Deepest12 diagnosis does not discard any contacts. Exact union samples use per-solid signed minimum, not a true Euclidean distance of overlapping-solid union.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('EXPLICIT_CORNER_CONTACT_COMPLETE', root.name, flush=True)


if __name__ == '__main__':
    error = None
    try:
        main()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'; exc.__traceback__ = None
    if error:
        print('EXPLICIT_CORNER_CONTACT_FAILED', error, flush=True); raise SystemExit(1)
