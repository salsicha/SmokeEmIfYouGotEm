"""Audit exact ownership/sampling at the real rapid-to-full-river join."""
from pathlib import Path
import json
import numpy as np
from south_fork_composite_terrain import CompositeTerrainSampler

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/composite_terrain'


def main():
    sampler = CompositeTerrainSampler(DIRECTORY)
    manifest = sampler.manifest
    origin = np.array(manifest['rapid_origin_utm_m'])
    # Every existing captured/inferred rapid vertex survives at its exact XYZ.
    p = sampler.rapid.xyz
    height, owner = sampler.sample(p[:, 0]+origin[0], p[:, 1]+origin[1], with_owner=True)
    vertex_error = float(np.max(abs(height-(p[:, 2]+manifest['rapid_datum_navd88_m']))))
    assert vertex_error < 1e-7 and np.all(owner == 2)
    vertices, faces = sampler.seam_xyz, sampler.seam_faces
    edges, counts = np.unique(np.sort(faces[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1), axis=0, return_counts=True)
    assert counts.max() == 2 and len(vertices)-len(edges)+len(faces) == 0
    assert int((counts == 1).sum()) == len(vertices)
    error = 0.
    engine_probes = []
    for weights in ([1/3]*3, [.07, .32, .61]):
        point = np.einsum('tij,i->tj', vertices[faces], weights)
        h, own = sampler.sample(point[:, 0], point[:, 1], with_owner=True)
        assert np.all(own == 3)
        error = max(error, float(np.max(abs(h-point[:, 2]))))
        local = point-np.r_[origin, manifest['rapid_datum_navd88_m']]
        engine_probes.extend((local*[100, -100, 100]).tolist())
    assert error < 1e-7
    # Compare shared boundary heights with the adjoining owner's exact source.
    boundary = vertices[np.unique(edges[counts == 1])]
    composed = sampler.sample(boundary[:, 0], boundary[:, 1])
    boundary_error = float(np.max(abs(composed-boundary[:, 2])))
    assert boundary_error < 1e-7
    report = dict(rapid_vertex_count=len(p), maximum_rapid_vertex_error_m=vertex_error,
        seam_probe_count=len(faces)*2, maximum_seam_sampling_error_m=error,
        boundary_vertex_count=len(boundary), maximum_boundary_height_gap_m=boundary_error,
        manifold_annulus=True, one_owner_per_query=True, no_clamped_or_invented_gap_fallback=True,
        normal_map_integrated=False, hydraulic_validation_passed=False)
    (DIRECTORY/'sampling_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    (DIRECTORY/'engine_seam_probes.json').write_text(json.dumps(dict(
        source_geometry_sha256=manifest['artifacts']['troublemaker_seam.npz'],
        local_rapid_engine_cm=engine_probes), indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
