"""Read-only actual collider/cache export for geometric aperture experiments."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
import openvdb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_geometry import world_coordinates
from water_feature_subcell_geometry import section_mesh


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--frame', type=int, default=169)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text()); control = audit['controls'][0]
    source = Path(control['source_blend']); data = source.parent/'cache'/'data'/f'fluid_data_{args.frame:04d}.vdb'
    if not audit['complete'] or Path(bpy.data.filepath).resolve() != source.resolve():
        raise ValueError('Exact completed original scene required')
    inputs = {str(p.resolve()): digest(p) for p in
              (args.audit, source, data, Path(__file__), Path(__file__).with_name('water_feature_geometry.py'),
               Path(__file__).with_name('water_feature_subcell_geometry.py'))}
    if inputs[str(data.resolve())] != audit['dependency_sha256'][str(data.resolve())]:
        raise ValueError('Preserved original DATA changed')
    args.output.mkdir(); outputs = {}; meshes = []; fields = {}

    def save(name, array):
        path = args.output/(name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        outputs[str(path.resolve())] = digest(path)
        return str(path.resolve())

    # Read evaluated colliders, not rendered substitutes or guessed box bounds.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for i, entry in enumerate(control['colliders']):
        obj = bpy.data.objects[entry['name']].evaluated_get(depsgraph); mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            v = world_coordinates([p.co[:] for p in mesh.vertices], obj.matrix_world)
            t = np.array([p.vertices[:] for p in mesh.loop_triangles], np.int64)
            sha = hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest()
            if sha != entry['geometry_sha256']:
                raise ValueError('Actual collider geometry changed: '+entry['name'])
            # Includes global closure validation even for a plane outside solid.
            _, proof = section_mesh(v, t, 0, float(v[:, 0].min()-1))
            meshes.append(dict(name=entry['name'], geometry_sha256=sha, vertices=save(f'mesh-{i}-vertices', v),
                triangles=save(f'mesh-{i}-triangles', t), bounds_m=[v.min(0).tolist(), v.max(0).tolist()],
                vertices_count=len(v), triangles_count=len(t), validation=proof, hide_render=entry['hide_render']))
        finally:
            obj.to_mesh_clear()
    if len(meshes) != 8:
        raise ValueError('All eight original physical colliders required')
    shape = tuple(control['shape'])
    for name, dtype, vector in (('phi', np.float32, False), ('phi_obstacle', np.float32, False),
            ('phi_obstacle_inflow', np.float32, False), ('phi_inflow', np.float32, False),
            ('phi_out', np.float32, False), ('flags', np.int32, False), ('velocity', np.float32, True)):
        grid = openvdb.read(str(data), name)
        if tuple(grid.metadata['file_base_resolution']) != shape:
            raise ValueError('Unexpected native cached grid dimensions')
        array = np.empty((*shape, 3) if vector else shape, dtype); grid.copyToArray(array)
        if not np.isfinite(array).all():
            raise ValueError('Nonfinite preserved field')
        fields[name] = save(name, array)
    if any(digest(p) != sha for p, sha in inputs.items()):
        raise ValueError('Read-only source preservation failed')
    report = dict(complete=True, accepted=False, read_only_source_unchanged=True, frame=args.frame,
        blender_version=bpy.app.version_string, blender_build_hash=bpy.app.build_hash.decode(),
        source_blend=str(source.resolve()), shape=shape, origin_m=control['origin_m'], cell_m=control['cell_m'],
        meshes=meshes, fields=fields, dependency_sha256=inputs, outputs_sha256=outputs,
        scope='Actual unchanged collider triangles and preserved cached fields; no native evolution or scene mutation')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('SUBCELL_ACTUAL_INPUTS', len(meshes), len(fields), args.output, flush=True)


if __name__ == '__main__':
    main()
