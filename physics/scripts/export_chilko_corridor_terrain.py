"""Export the complete captured Chilko corridor on the shared engine lattice.

All geometry consumers must sample these encoded triangles. This candidate
does not contain calibrated rapid obstacles or a validated hydraulic solution.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely

from chilko_corridor_bed import CorridorBed
from chilko_triangle_ownership import support_policy, preserve_triangle_support
from export_colorado_continuous_terrain import (
    VERTICES, SPACING, SPAN, HEIGHT_BASE, HEIGHT_RANGE, LandscapeTriangles,
    encode_height, sha, write_png_u16)


def corridor_chunks(line, origin, buffer_m, *, spacing_m=SPACING):
    support_policy(spacing_m)
    span=(VERTICES-1)*spacing_m
    origin = np.asarray(origin, dtype=float)
    if origin.shape != (2,) or not np.isfinite(origin).all() or not 100 <= buffer_m <= 600:
        raise ValueError('Finite geographic origin and 100-600 m visual corridor required')
    footprint = line.buffer(buffer_m)
    lo = np.floor((np.asarray(footprint.bounds[:2]) - origin) / span).astype(int)
    hi = np.floor((np.asarray(footprint.bounds[2:]) - origin) / span).astype(int)
    # The captured buffer is 1000 m: 600 m plus a chunk diagonal < 957 m.
    # Test entire chunks against actual source coverage rather than assuming it.
    return [(i, j) for i in range(lo[0], hi[0]+1) for j in range(lo[1], hi[1]+1)
            if footprint.intersects(shapely.box(*(origin + [i*span, j*span]),
                                                *(origin + [(i+1)*span, (j+1)*span])))]


def export(terrain, profile, out, origin, datum, buffer_m=600., discharge=45., roughness=.045, depth_profile=None, *, spacing_m=SPACING):
    policy=support_policy(spacing_m)
    span=(VERTICES-1)*spacing_m
    out = Path(out).resolve()
    if out.exists(): raise ValueError('Fresh full-corridor candidate required')
    if not np.isfinite(datum): raise ValueError('Finite vertical datum required')
    model = CorridorBed(terrain, profile, discharge, roughness, depth_profile=depth_profile)
    origin = np.asarray(origin, dtype=float)
    indices = corridor_chunks(model.line, origin, buffer_m, spacing_m=spacing_m)
    grid=model.receipt.get('available_channel_depth',{}).get('capacity_grid')
    if grid is not None:
        from chilko_encoded_capacity import validate_capacity_grid
        validate_capacity_grid(grid,origin,spacing_m)
    out.mkdir(parents=True)
    chunks = []; inferred_count = 0; sources = {str(i): 0 for i in (1, 2, 3)}
    max_cut = 0.; max_quantization_error = 0.
    for count, (i, j) in enumerate(indices):
        west, south = origin + np.array([i, j]) * span
        east, north = np.meshgrid(west + np.arange(VERTICES)*spacing_m,
                                  south + span - np.arange(VERTICES)*spacing_m)
        xy = np.stack((east, north), axis=-1)
        result = preserve_triangle_support(model, xy, model.sample(xy),spacing_m=spacing_m)
        encoded = encode_height(result['height_m'])
        decoded = HEIGHT_BASE + encoded.astype(float) * HEIGHT_RANGE / 65535.
        max_quantization_error = max(max_quantization_error, float(abs(decoded-result['height_m']).max()))
        inferred_count += int(result['inferred_bed'].sum())
        max_cut = max(max_cut, float((result['source_height_m']-result['height_m']).max()))
        for kind in sources: sources[kind] += int((result['source_kind']==int(kind)).sum())
        name = f'height_{i}_{j}.png'; write_png_u16(out/name, encoded)
        proof = f'source_{i}_{j}.npz'
        np.savez_compressed(out/proof, **result)
        chunks.append(dict(chunk=[int(i), int(j)], heightfield=name, sha256=sha(out/name),
            source_receipt=proof, source_receipt_sha256=sha(out/proof),
            origin_m=[float(west), float(south+span)],
            world_northwest_xy_cm=[i*span*100, -(j+1)*span*100]))
        if count % 20 == 0: print(f'canonical corridor chunks {count+1}/{len(indices)}', flush=True)
    receipt = model.receipt
    if (sha(model.terrain.folder/'manifest.json') != receipt['terrain_manifest_sha256'] or
            sha(Path(receipt['profile_manifest'])) != receipt['profile_manifest_sha256']):
        raise ValueError('Source manifests changed during full-corridor export')
    depth_spec=receipt.get('available_channel_depth')
    if depth_spec and (sha(Path(depth_spec['manifest']))!=depth_spec['manifest_sha256'] or
                       sha(Path(depth_spec['manifest']).parent/'depth.npz')!=depth_spec['depth_sha256']):
        raise ValueError('Available-channel depth changed during full-corridor export')
    manifest = dict(schema='raftsim.continuous_landscape.v1', river_id='chilko_river_bc',
        horizontal_crs='EPSG:3157', vertical_reference='CGVD2013 (EPSG:6647)', world_y_sign=-1,
        horizontal_origin_m=origin.tolist(), vertical_datum_m=float(datum), evidence_source=receipt,
        landscape=dict(vertices=VERTICES, spacing_m=spacing_m, span_m=span,
            subsections_per_component=2, quads_per_subsection=63, height_base_m=HEIGHT_BASE,
            height_range_m=HEIGHT_RANGE, actor_z_cm=(HEIGHT_BASE+HEIGHT_RANGE*32768/65535-datum)*100,
            scale_xyz=[spacing_m*100, spacing_m*100, HEIGHT_RANGE*100/512*65536/65535]),
        geographic_scope=dict(route_interval_m=[0., model.line.length], buffer_m=buffer_m,
            frame='Exact EPSG:3157 FWA route arclength; no rapid boundaries assigned'),
        inference_support_policy=policy,
        chunks=chunks, incomplete_source_chunks=[], shared_edge_max_encoded_difference=0,
        vertex_counts_including_shared_edges=dict(source_kind=sources, inferred_bed=inferred_count),
        source_kind=model.terrain.manifest['source_kind'], maximum_inferred_cut_m=max_cut,
        maximum_height_quantization_error_m=max_quantization_error,
        scope='Complete corridor initial terrain/bed candidate, not accepted river hydraulics or rapid geometry',
        vegetation_complete=False, engine_validated=False, full_river_complete=False)
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    # This reader independently verifies every common edge and encoded tile.
    LandscapeTriangles(out)
    print(json.dumps(dict(chunks=len(chunks), inferred_vertices=inferred_count,
                         max_cut_m=max_cut, max_quantization_error_m=max_quantization_error)))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('terrain', 'profile', 'out'): parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--origin', type=float, nargs=2, required=True)
    parser.add_argument('--vertical-datum-m', type=float, required=True)
    parser.add_argument('--buffer-m', type=float, default=600.)
    parser.add_argument('--discharge-m3s', type=float, default=45.)
    parser.add_argument('--manning-n', type=float, default=.045)
    parser.add_argument('--depth-profile', type=Path)
    parser.add_argument('--spacing-m',type=float,choices=(1.,2.),default=2.)
    a = parser.parse_args()
    export(a.terrain, a.profile, a.out, a.origin, a.vertical_datum_m,
           a.buffer_m, a.discharge_m3s, a.manning_n, a.depth_profile,spacing_m=a.spacing_m)
