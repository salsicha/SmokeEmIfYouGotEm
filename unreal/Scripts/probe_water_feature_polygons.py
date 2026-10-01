"""Capture rejected native extraction polygons without modifying saved geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_polygon import triangulate_polygon
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from water_feature_triangulation import weld_exact_endpoints


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[192])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    source = Path(bpy.data.filepath)
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    bake = json.loads((root/'bake-mesh.json').read_text())
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or not bake['baked_mesh'] or source.resolve() != Path(bake['blend']).resolve()):
        raise ValueError('Completed aligned eddy mesh required')
    original_hashes = {str(source): sha256(source)}
    rows = []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame outside native cache')
        for file in [root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb',
                     root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz']:
            original_hashes[str(file)] = sha256(file)
        bpy.context.scene.frame_set(frame)
        liquid = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        derived = clipped_surface(liquid, [bpy.data.objects[n] for n in EDDY_SOLIDS],
                                  union_solids=True, contact_materials=True)
        bm = bmesh.new()
        try:
            bm.from_mesh(derived.data)
            before = {tuple(v.co) for v in bm.verts}
            welded = weld_exact_endpoints(bm)
            if {tuple(v.co) for v in bm.verts} != before:
                raise ValueError('Distinct coordinate lost')
            failures, passed = [], 0
            for face in bm.faces:
                coordinates = [tuple(v.co) for v in face.verts]
                try:
                    triangles = triangulate_polygon(coordinates)
                    corners = np.asarray(coordinates, float)[triangles]
                    areas = np.linalg.norm(np.cross(corners[:, 1]-corners[:, 0],
                                                   corners[:, 2]-corners[:, 0]), axis=1)/2
                    if np.any(areas < 1e-12):
                        raise ValueError('Triangulation retains area below 1e-12 m2')
                    passed += 1
                except ValueError as error:
                    points = np.asarray(coordinates, float)
                    failures.append(dict(reason=str(error), material_index=face.material_index,
                        vertex_count=len(points), polygon_area_m2=face.calc_area(),
                        exact_duplicate_coordinates=len(points)-len(set(coordinates)),
                        vertices=coordinates))
            rows.append(dict(frame=frame, exact_edge_endpoints_welded=welded,
                             passed_polygons=passed, failed_polygons=failures))
            print('POLYGON_PROBE', frame, 'passed', passed, 'failed', len(failures), flush=True)
        finally:
            bm.free()
            remove_surface(derived)
    if any(sha256(Path(path)) != digest for path, digest in original_hashes.items()):
        raise ValueError('Original native files changed')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, frames=rows,
                       original_file_sha256=original_hashes, originals_unchanged=True,
                       limitations='Captured exact native polygon boundaries, not solver/contact acceptance.'), stream, indent=2)


if __name__ == '__main__':
    main()
