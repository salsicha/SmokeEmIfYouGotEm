"""Exact endpoint welding and native polygon triangulation for extracted meshes."""
import bmesh
from collections import Counter
from water_feature_polygon import triangulate_polygon


def weld_exact_endpoints(bm):
    """Join only endpoints of existing edges having exactly equal coordinates."""
    targets = {}

    def representative(vertex):
        while vertex in targets:
            vertex = targets[vertex]
        return vertex

    for edge in bm.edges:
        a, b = edge.verts
        if tuple(a.co) == tuple(b.co):
            a, b = representative(a), representative(b)
            if a != b:
                targets[b] = a
    targets = {vertex: representative(target) for vertex, target in targets.items()}
    if targets:
        bmesh.ops.weld_verts(bm, targetmap=targets)
    return len(targets)


def triangulate_extraction(obj, constrained=False):
    """Never merge merely nearby coordinates or smooth/move a liquid vertex."""
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        original_coordinates = {tuple(v.co) for v in bm.verts}

        def triangle_key(coordinates):
            return min(coordinates[i:]+coordinates[:i] for i in range(3))

        original_triangles = Counter(triangle_key(tuple(tuple(v.co) for v in face.verts))
                                     for face in bm.faces if len(face.verts) == 3)
        welded = weld_exact_endpoints(bm)
        faces = [face for face in bm.faces if len(face.verts) > 3]
        if not constrained:
            bmesh.ops.triangulate(bm, faces=faces, quad_method='BEAUTY', ngon_method='BEAUTY')
        if {tuple(v.co) for v in bm.verts} != original_coordinates:
            raise ValueError('Triangulation moved/lost a distinct vertex coordinate')
        bm.normal_update()
        report = dict(method='constrained ears' if constrained else 'native BEAUTY',
                      projection='orthonormal area-normal plane' if constrained else 'native',
                      exact_zero_edge_vertices_welded=welded,
                      polygons_retriangulated=len(faces), distinct_coordinates_unchanged=True,
                      smoothing_applied=False, distance_tolerance_m=0.)
        if constrained:
            bm.verts.index_update()
            vertices = [tuple(v.co) for v in bm.verts]
            triangles, material_indices, smooth = [], [], []
            for face in bm.faces:
                indices = [v.index for v in face.verts]
                local_triangles = [(0, 1, 2)] if len(indices) == 3 else triangulate_polygon([vertices[i] for i in indices])
                for triangle in local_triangles:
                    triangles.append(tuple(indices[i] for i in triangle))
                    material_indices.append(face.material_index)
                    smooth.append(face.smooth)
            obj.data.clear_geometry()
            obj.data.from_pydata(vertices, [], triangles)
            for face, material, shade in zip(obj.data.polygons, material_indices, smooth):
                face.material_index, face.use_smooth = material, shade
        else:
            bm.to_mesh(obj.data)
        obj.data.update()
        output_triangles = Counter(triangle_key(tuple(tuple(obj.data.vertices[i].co)
                                                      for i in face.vertices))
                                   for face in obj.data.polygons if len(face.vertices) == 3)
        retained = all(output_triangles[key] >= count for key, count in original_triangles.items())
        if not retained:
            raise ValueError('Retriangulation removed/changed an existing triangular face')
        report.update(original_triangular_faces=len(list(original_triangles.elements())),
                      original_triangular_faces_unchanged=retained)
        return report
    finally:
        bm.free()
