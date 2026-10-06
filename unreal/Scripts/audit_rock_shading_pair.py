"""Read-only native triangle/normal comparison for two existing local meshes."""
import hashlib
import json
import math
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]


def canonical_triangles(vertices, indices, normals):
    if not indices or len(indices) % 3 or len(vertices) != len(normals):
        raise ValueError('Complete indexed mesh with vertex normals required')
    records = []
    for start in range(0, len(indices), 3):
        ids = indices[start:start+3]
        if any(i < 0 or i >= len(vertices) for i in ids):
            raise ValueError('Invalid triangle index')
        points = [tuple(vertices[i]) for i in ids]
        values = [tuple(normals[i]) for i in ids]
        if any(len(p) != 3 or not all(math.isfinite(x) for x in p) for p in points+values):
            raise ValueError('Finite three-component geometry and normals required')
        # Rotate but never reflect winding. Native vertex splitting is allowed.
        first = min(range(3), key=lambda i: points[i])
        records.append((tuple(points[first:]+points[:first]), tuple(values[first:]+values[:first])))
    return sorted(records)


def compare_records(reference, candidate):
    if not reference or [r[0] for r in reference] != [r[0] for r in candidate]:
        raise ValueError('Native directed triangles changed')
    differences = [math.dist(a, b) for left, right in zip(reference, candidate)
                   for a, b in zip(left[1], right[1])]
    changed = sum(d > 1e-5 for d in differences)
    if not changed:
        raise ValueError('No native shading change was installed')
    positions = [r[0] for r in reference]
    return dict(triangle_count=len(reference), expanded_corner_count=len(differences),
                exact_native_directed_triangles=True,
                triangle_positions_sha256=hashlib.sha256(json.dumps(positions).encode()).hexdigest(),
                changed_normal_corners=changed, maximum_normal_vector_difference=max(differences))


def main():
    raw = json.loads(Path(os.environ['RAFTSIM_ROCK_SHADING_PAIR_CONFIG']).read_text())
    report = (ROOT/raw['report']).resolve()
    if not report.is_relative_to(ROOT/'tmp') or report.exists():
        raise ValueError('Fresh local report required')
    records, hashes = [], {}
    for key in ('reference', 'candidate'):
        asset = raw[key]
        if not asset.startswith('/Game/RaftSim/Environment/GeneratedLocalReview/') or '..' in asset or '\\' in asset:
            raise ValueError('Existing generated-local-review meshes required')
        path = ROOT/'unreal/Content'/(asset[6:]+'.uasset')
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        mesh = unreal.load_asset(asset)
        assert isinstance(mesh, unreal.StaticMesh)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert mesh.get_num_sections(0) == 1
        vertices, triangles, normals, _, _ = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, 0)
        assert len(triangles) == mesh.get_num_triangles(0)*3
        xyz = lambda values: [(v.x, v.y, v.z) for v in values]
        records.append(canonical_triangles(xyz(vertices), list(triangles), xyz(normals)))
    result = compare_records(*records)
    for name, digest in hashes.items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    report.write_text(json.dumps(dict(schema='raftsim.rock_shading_pair.v1', **raw,
        **result, protected_mesh_hashes=hashes, assets_saved=False,
        measured_geometry_improved=False, visual_accepted=False), indent=2)+'\n')
    unreal.log('Exact native shading-only pair verified: '+str(report))


if __name__ == '__main__':
    try: main()
    finally: unreal.SystemLibrary.quit_editor()
