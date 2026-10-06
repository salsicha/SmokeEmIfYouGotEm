"""Locate native solid-extraction slivers before choosing any geometry repair."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from water_feature_geometry import world_coordinates
from audit_water_feature_mesh_contact import topology


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214])
    parser.add_argument('--constrained-extraction', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    source = Path(bpy.data.filepath)
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    if setup['case'] != 'eddy' or not setup.get('grid_aligned_domain'):
        raise ValueError('Only the aligned eddy surface study is in scope')
    source_hash, rows = digest(source), []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame unavailable')
        paths = [root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb',
                 root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz']
        hashes = {str(p.relative_to(root)): digest(p) for p in paths}
        bpy.context.scene.frame_set(frame)
        native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        derived = clipped_surface(native, [bpy.data.objects[name] for name in EDDY_SOLIDS],
                                  union_solids=True, contact_materials=True,
                                  triangulated=args.constrained_extraction,
                                  constrained=args.constrained_extraction)
        try:
            mesh = derived.data
            mesh.calc_loop_triangles()
            local_vertices = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
            vertices = world_coordinates(local_vertices, derived.matrix_world)
            native_transformed_vertices = np.array([derived.matrix_world @ v.co for v in mesh.vertices], dtype=np.float64)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int64)
            corners = vertices[triangles]
            corners32 = corners.astype(np.float32)
            local_corners = local_vertices[triangles]
            native_corners = native_transformed_vertices[triangles]
            local_area = np.linalg.norm(np.cross(local_corners[:, 1]-local_corners[:, 0],
                                                local_corners[:, 2]-local_corners[:, 0]), axis=1)/2
            native_area = np.linalg.norm(np.cross(native_corners[:, 1]-native_corners[:, 0],
                                                 native_corners[:, 2]-native_corners[:, 0]), axis=1)/2
            area64 = np.linalg.norm(np.cross(corners[:, 1]-corners[:, 0], corners[:, 2]-corners[:, 0]), axis=1)/2
            area32 = np.linalg.norm(np.cross(corners32[:, 1]-corners32[:, 0], corners32[:, 2]-corners32[:, 0]), axis=1)/2
            bad = np.flatnonzero(area64 < 1e-12)
            materials = [mesh.polygons[t.polygon_index].material_index for t in mesh.loop_triangles]
            examples = [dict(triangle_index=int(i), coordinates_m=corners[i].tolist(),
                             area_m2=float(area64[i]), material_index=int(materials[i]),
                             parent_polygon_vertices=len(mesh.polygons[mesh.loop_triangles[i].polygon_index].vertices))
                        for i in bad[:12]]
            # Per-polygon near-zero triangles reveal triangulation, versus a
            # truly negligible source polygon. This is measurement, not cleanup.
            polygon_area = np.bincount([t.polygon_index for t in mesh.loop_triangles], weights=area64,
                                       minlength=len(mesh.polygons))
            row = dict(frame=frame, topology=topology(triangles), vertices=len(vertices),
                       triangles=len(triangles), degenerate_float32=int(np.sum(area32 < 1e-12)),
                       degenerate_float64=len(bad), exact_zero_float64=int(np.sum(area64 == 0)),
                       degenerate_local_float64=int(np.sum(local_area < 1e-12)),
                       degenerate_native_float32_transform=int(np.sum(native_area < 1e-12)),
                       maximum_native_transform_rounding_m=float(np.max(np.linalg.norm(vertices-native_transformed_vertices, axis=1))),
                       minimum_area_float64_m2=float(area64.min()),
                       degenerate_material_counts=dict(Counter(str(materials[i]) for i in bad)),
                       materials=[material.name for material in mesh.materials],
                       near_zero_source_polygons=int(np.sum(polygon_area < 1e-12)),
                       geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest(),
                       degenerate_examples=examples, original_file_sha256=hashes)
            rows.append(row)
            print('MESH_PRECISION', json.dumps({k: v for k, v in row.items()
                                              if k not in ('degenerate_examples', 'original_file_sha256')}), flush=True)
        finally:
            remove_surface(derived)
        if any(digest(root/name) != value for name, value in hashes.items()):
            raise ValueError('Original cache changed')
    if digest(source) != source_hash:
        raise ValueError('Source blend changed')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, originals_unchanged=True,
                       constrained_extraction=args.constrained_extraction,
                       geometry_measurement='float64 affine transform before area/hash; native float32 transform counted separately',
                       source_blend_sha256=source_hash, frames=rows,
                       scope='Float64 area and source-polygon classification of extracted native geometry. Not mesh cleanup, contact dynamics, mass, optical or hydraulic acceptance.'), stream, indent=2)


if __name__ == '__main__':
    main()
