"""Native eddy mesh/solid vertex and triangle-centroid contact diagnostics."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from water_feature_geometry import world_coordinates


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topology(triangles):
    edges = Counter(tuple(sorted(edge)) for a, b, c in triangles
                    for edge in ((a, b), (b, c), (c, a)))
    return dict(boundary_edges=sum(n == 1 for n in edges.values()),
                nonmanifold_edges=sum(n > 2 for n in edges.values()))


def interior_distance(tree, point, tolerance=1e-6):
    """Parity of an oblique ray in a closed solid; do not trust smoothed normals."""
    point = Vector(point)
    nearest, _, _, distance = tree.find_nearest(point)
    if nearest is None:
        raise ValueError('Missing nearest collider surface')
    if distance <= tolerance:
        return 0.
    direction = Vector((1., .371390676, .19723111)).normalized()
    origin, hits = point, 0
    for _ in range(32):
        location, _, _, _ = tree.ray_cast(origin, direction)
        if location is None:
            return float(distance) if hits % 2 else 0.
        hits += 1
        origin = location+direction*tolerance
    raise ValueError('Ray crossing limit exceeded; invalid/unresolved collider')


def contact(points, solid):
    lo, hi, tree = solid
    candidates = points[np.all((points > lo+1e-6) & (points < hi-1e-6), axis=1)]
    depths = np.array([interior_distance(tree, point) for point in candidates])
    depths = depths[depths > 0]
    return dict(samples=len(points), inside_solid_samples=len(depths),
                deepest_inside_m=float(depths.max()) if len(depths) else 0.,
                median_inside_m=float(np.median(depths)) if len(depths) else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 216, 240, 264, 288])
    parser.add_argument('--solid-clipped', action='store_true', help='Audit exact shared-collider surface extraction, not changed physics')
    parser.add_argument('--union-solids', action='store_true', help='Unite overlapping shared solids before one exact subtraction')
    parser.add_argument('--contact-materials', action='store_true')
    parser.add_argument('--triangulated-extraction', action='store_true')
    parser.add_argument('--constrained-triangulation', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.union_solids and not args.solid_clipped:
        parser.error('--union-solids requires --solid-clipped')
    if (args.contact_materials or args.triangulated_extraction) and not args.union_solids:
        parser.error('Material/triangulation studies require --union-solids')
    if args.constrained_triangulation and not args.triangulated_extraction:
        parser.error('--constrained-triangulation requires --triangulated-extraction')
    if args.output.exists():
        raise FileExistsError(args.output)
    source = Path(bpy.data.filepath)
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    bake = json.loads((root/'bake-mesh.json').read_text())
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or not bake['baked_mesh'] or not bake['original_data_unchanged']
            or source.resolve() != Path(bake['blend']).resolve()):
        raise ValueError('Completed aligned eddy native mesh required')
    source_hash = sha256(source)
    solids, collider_rows = {}, []
    names = EDDY_SOLIDS
    for name in names:
        obj = bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
            triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
            array = np.array(vertices)
            counts = topology(triangles)
            if counts != dict(boundary_edges=0, nonmanifold_edges=0):
                raise ValueError('Closed collider topology required: '+name)
            solids[name] = (array.min(axis=0), array.max(axis=0),
                            BVHTree.FromPolygons(vertices, triangles, all_triangles=True))
            collider_rows.append(dict(name=name, topology=counts,
                geometry_sha256=hashlib.sha256(array.tobytes()+np.array(triangles).tobytes()).hexdigest()))
        finally:
            obj.to_mesh_clear()
    rows = []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame outside native mesh coverage')
        data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        mesh_file = root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz'
        hashes = {str(p.relative_to(root)): sha256(p) for p in (data, mesh_file)}
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        derived = None
        if args.solid_clipped:
            derived = clipped_surface(obj, [bpy.data.objects[name] for name in names], args.union_solids,
                                      args.contact_materials, args.triangulated_extraction, args.constrained_triangulation)
            obj = derived.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices = world_coordinates([v.co[:] for v in mesh.vertices], obj.matrix_world)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=int)
            if len(vertices) <= 8 or not np.isfinite(vertices).all():
                raise ValueError('Missing/nonfinite native liquid mesh')
            corners = vertices[triangles]
            area = np.linalg.norm(np.cross(corners[:, 1]-corners[:, 0],
                                           corners[:, 2]-corners[:, 0]), axis=1)/2
            row = dict(frame=frame, vertices=len(vertices), triangles=len(triangles),
                       topology=topology(triangles), degenerate_triangles=int(np.sum(area < 1e-12)),
                       exact_zero_area_triangles=int(np.sum(area == 0)), minimum_triangle_area_m2=float(area.min()),
                       extraction_triangulation=(json.loads(derived['extraction_triangulation'])
                                                 if derived is not None and args.triangulated_extraction else None),
                       signed_mesh_volume_m3=float(np.sum(np.einsum('ij,ij->i', corners[:, 0],
                           np.cross(corners[:, 1], corners[:, 2])))/6),
                       bounds_m=[vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
                       colliders={name: dict(vertices=contact(vertices, solid),
                           triangle_centroids=contact(corners.mean(axis=1), solid))
                           for name, solid in solids.items()}, original_file_sha256=hashes)
            rows.append(row)
            print('NATIVE_MESH_CONTACT', json.dumps(row), flush=True)
        finally:
            obj.to_mesh_clear()
            if derived is not None:
                remove_surface(derived)
        if any(sha256(root/path) != digest for path, digest in hashes.items()):
            raise ValueError('Native cache changed during contact audit')
    if sha256(source) != source_hash:
        raise ValueError('Source blend changed')
    for name, digest in bake['original_data_sha256'].items():
        if sha256(root/'cache'/'data'/name) != digest:
            raise ValueError('Preserved base data hash mismatch')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, source_blend=str(source),
                       source_blend_sha256=source_hash, originals_unchanged=True,
                       solid_clipped_surface=args.solid_clipped,
                       shared_solids_united=args.union_solids,
                       contact_materials_transferred=args.contact_materials,
                       triangulated_extraction=args.triangulated_extraction,
                       geometry_measurement='float64 affine transform of original object-space coordinates; collider parity uses native BVH precision',
                       collider_geometry=collider_rows, frames=rows,
                       limitations='All native vertices and triangle centroids sampled against closed authored collider meshes with oblique-ray parity. Not exhaustive triangle/solid intersection, solver contact dynamics, mass, flux, surface continuity or visual acceptance. Signed mesh volume is reconstruction, not conserved solver mass.'), stream, indent=2)


if __name__ == '__main__':
    main()
