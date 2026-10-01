"""Check phase centers against the actual closed liquid surface used for renders."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_geometry import world_coordinates
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from audit_water_feature_mesh_contact import topology, interior_distance


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214])
    parser.add_argument('--samples', type=int, default=4096)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists() or args.samples < 1:
        raise ValueError('Fresh output and positive distributed sample count required')
    source = Path(bpy.data.filepath)
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    bake = json.loads((root/'bake-particles.json').read_text())
    mapping = json.loads((root/'secondary-mapping-v1.json').read_text())
    if (setup['case'] != 'eddy' or not mapping['complete'] or not mapping['originals_unchanged']
            or not bake['baked_particles'] or Path(bake['blend']).resolve() != source.resolve()):
        raise ValueError('Completed independently mapped native secondary phases required')
    hashes = {str(source): digest(source)}
    rows = []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame outside native coverage')
        for path in [root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb',
                     root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz',
                     root/'cache'/'particles'/f'fluid_particles_{frame:04d}.vdb']:
            hashes[str(path)] = digest(path)
        bpy.context.scene.frame_set(frame)
        native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        phase_positions = {}
        for ps in native.particle_systems:
            if ps.name.lower() in ('foam', 'spray', 'bubbles'):
                positions = np.empty(len(ps.particles)*3, np.float32)
                ps.particles.foreach_get('location', positions)
                phase_positions[ps.name] = positions.reshape(-1, 3)
        derived = clipped_surface(native, [bpy.data.objects[n] for n in EDDY_SOLIDS],
                                  union_solids=True, contact_materials=True,
                                  triangulated=True, constrained=True)
        try:
            mesh = derived.data
            mesh.calc_loop_triangles()
            vertices = world_coordinates([v.co[:] for v in mesh.vertices], derived.matrix_world)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int64)
            if topology(triangles) != dict(boundary_edges=0, nonmanifold_edges=0):
                raise ValueError('Closed native extraction required for parity classification')
            tree = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
            phases = []
            for name, positions in phase_positions.items():
                selected = np.linspace(0, len(positions)-1, min(args.samples, len(positions)), dtype=int)
                values, unresolved = [], []
                for index in selected:
                    try:
                        values.append(interior_distance(tree, positions[index]))
                    except ValueError as error:
                        if str(error) != 'Ray crossing limit exceeded; invalid/unresolved collider':
                            raise
                        unresolved.append(dict(particle_index=int(index), position_m=positions[index].tolist(),
                                               reason=str(error)))
                depths = np.array(values)
                inside = int(np.sum(depths > 0))
                phases.append(dict(name=name, count=len(positions), sampled=len(selected),
                    resolved_samples=len(depths), unresolved_samples=unresolved,
                    sampled_inside_fraction=float(np.mean(depths > 0)) if len(depths) and not unresolved else None,
                    sampled_inside_fraction_bounds=[inside/len(selected), (inside+len(unresolved))/len(selected)] if len(selected) else None,
                    sampled_inside_over_one_cell_fraction=float(np.mean(depths > setup['approximate_cell_m'])) if len(depths) and not unresolved else None,
                    inside_depth_quantiles_m=np.quantile(depths[depths > 0], [.05, .5, .95]).tolist() if np.any(depths > 0) else None,
                    maximum_inside_depth_m=float(depths.max()) if len(depths) else None))
            rows.append(dict(frame=frame, geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest(), phases=phases))
            print('SECONDARY_MESH_FRAME', json.dumps(rows[-1]), flush=True)
        finally:
            remove_surface(derived)
    if any(digest(Path(path)) != value for path, value in hashes.items()):
        raise ValueError('Original native files changed')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, originals_unchanged=True, frames=rows,
            original_file_sha256=hashes,
            scope='Distributed native phase-center samples against actual closed render extraction, oblique-ray parity/native BVH nearest depth. Sampled, not exhaustive intersections or exact arithmetic. Not calibrated particle radii, ballistic kinetics, bubble/foam interface coupling, mass or physical acceptance.'), stream, indent=2)


if __name__ == '__main__':
    main()
