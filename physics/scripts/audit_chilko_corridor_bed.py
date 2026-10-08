"""Verify full-corridor source ownership and inspect initial wet cross sections.

Static inferred-reference clearance is a construction diagnostic, never a boat
navigation, solved-water or rapid-class acceptance test.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString

from chilko_corridor_terrain import CorridorTerrain
from chilko_corridor_bed import source_water_reference
from chilko_triangle_ownership import support_policy as grid_support_policy, preserve_triangle_support
from review_chilko_continuous_cook import verify_terrain_sources
from plan_lidarbc_corridor_capture import route_xy
from export_colorado_continuous_terrain import LandscapeTriangles, VERTICES, SPACING, sha


def longest_supported_width(mask, spacing=2.):
    mask = np.asarray(mask)
    if mask.ndim != 1 or mask.dtype.kind != 'b' or not np.isfinite(spacing) or spacing <= 0:
        raise ValueError('Boolean section and positive spacing required')
    edges = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    # Samples are point clearances; N samples span (N-1)*spacing, not N cells.
    return float(max(0, int(np.max(edges[1::2]-edges[::2], initial=0))-1)*spacing)


def verify_mapped_mask(recorded, xy, polygon, line):
    expected=shapely.contains_xy(polygon,xy[...,0],xy[...,1])
    station=shapely.line_locate_point(line,shapely.points(xy[expected]))
    interior=(station>0)&(station<line.length)
    selected=np.flatnonzero(expected)
    expected.flat[selected[~interior]]=False
    if recorded.dtype.kind!='b' or not np.array_equal(recorded,expected):
        raise ValueError('Recorded water ownership differs from original mapped polygons')
    return station[interior]


def audit(folder, terrain_folder, profile_folder, out):
    folder, profile_folder, out = [Path(p).resolve() for p in (folder, profile_folder, out)]
    if out.exists(): raise ValueError('Fresh independent bed audit required')
    triangles = LandscapeTriangles(folder); m = triangles.manifest
    source = CorridorTerrain(terrain_folder)
    receipt = m['evidence_source']
    model=verify_terrain_sources(receipt)
    if model is None:raise ValueError('Full-route source planform required for bed audit')
    support_policy = m.get('inference_support_policy')
    if support_policy not in (None, grid_support_policy(triangles.spacing)):
        raise ValueError('Unknown triangle inference-support policy')
    if (sha(source.folder/'manifest.json') != receipt['terrain_manifest_sha256'] or
            sha(profile_folder/'manifest.json') != receipt['profile_manifest_sha256'] or
            sha(profile_folder/'profile.npz') != receipt['profile_sha256']):
        raise ValueError('Changed source/profile')
    with np.load(profile_folder/'profile.npz', allow_pickle=False) as z: p = dict(z)
    profile_manifest = json.loads((profile_folder/'manifest.json').read_text())
    route = Path(profile_manifest['route']['path'])
    if sha(route) != profile_manifest['route']['sha256']:
        raise ValueError('Changed source route')
    line = LineString(route_xy(route))
    local_reference, _ = source_water_reference(p['station_m'], p['raw_reference_m'])
    ownership_policy = receipt.get('ownership_policy', 'legacy_regressed_stage')
    if ownership_policy not in ('local_raw_channel_reference_plus_0.25m_v1', 'legacy_regressed_stage'):
        raise ValueError('Unknown terrain ownership policy')
    count = 0; preserved = 0; inferred = 0; max_error = 0.
    manifest_hash = sha(folder/'manifest.json')
    for index, chunk in enumerate(m['chunks']):
        proof = (folder/chunk['source_receipt']).resolve(); proof.relative_to(folder)
        if sha(proof) != chunk['source_receipt_sha256']: raise ValueError('Changed source receipt')
        with np.load(proof, allow_pickle=False) as z: r = dict(z)
        if any(a.shape != (VERTICES, VERTICES) for a in r.values()):
            raise ValueError('Source receipt shape differs from canonical lattice')
        east, north = np.meshgrid(chunk['origin_m'][0]+np.arange(VERTICES)*triangles.spacing,
                                  chunk['origin_m'][1]-np.arange(VERTICES)*triangles.spacing)
        xy = np.stack((east, north), axis=-1)
        if support_policy:
            expected = preserve_triangle_support(model, xy, model.sample(xy),spacing_m=triangles.spacing)
            for key in ('height_m', 'inferred_bed', 'inference_support_veto'):
                if key not in r or not np.array_equal(r[key], expected[key]):
                    raise ValueError('Exported triangle-support ownership differs from source')
        original, kind = source.sample(xy)
        if (not np.array_equal(original, r['source_height_m']) or
                not np.array_equal(kind, r['source_kind'])):
            raise ValueError('Recorded terrain differs from independently sampled source')
        bed, changed, mapped = r['height_m'], r['inferred_bed'], r['mapped_water']
        ownership = r['reference_m'] if ownership_policy == 'legacy_regressed_stage' else r['ownership_reference_m']
        station = verify_mapped_mask(mapped,xy,model.polygon,line)
        expected_stage = np.interp(station, p['station_m'], p['reference_m'])
        expected_ownership = (expected_stage if ownership_policy == 'legacy_regressed_stage' else
                              np.interp(station, p['station_m'], local_reference))
        if (not np.array_equal(r['reference_m'][mapped], expected_stage) or
                not np.array_equal(ownership[mapped], expected_ownership)):
            raise ValueError('Recorded source ownership/stage differs from hash-verified profile')
        if (changed.dtype.kind != 'b' or mapped.dtype.kind != 'b' or not np.isfinite(bed).all() or
                not np.array_equal(bed[~changed], original[~changed]) or
                not np.all(bed[changed] < original[changed]) or
                not np.all(mapped[changed]) or
                not np.all(original[changed] <= ownership[changed]+.25)):
            raise ValueError('Bed modifications exceed supported low mapped-water ownership')
        encoded_height = triangles.sample(xy)
        error = float(abs(encoded_height-bed).max())
        if not np.isfinite(error) or error > 2400/65535/2 + 1e-8:
            raise ValueError('Encoded triangle heights differ beyond common quantization')
        max_error = max(max_error, error); count += bed.size
        preserved += int((~changed).sum()); inferred += int(changed.sum())
        if index % 50 == 0: print(f'independent source/bed audit {index+1}/{len(m["chunks"])}', flush=True)
    lateral = np.arange(-160., 162., 2.)
    widths = []; rejected = []; centre_depth = []
    for start in range(0, len(p['station_m']), 256):
        sl = slice(start, start+256)
        xy = p['xy_m'][sl, None, :] + p['normal_xy'][sl, None, :]*lateral[None, :, None]
        bed = triangles.sample(xy)
        if not np.isfinite(bed).all(): raise ValueError('Canonical terrain missing along full-route cross sections')
        depth = p['reference_m'][sl, None]-bed
        in_bank = ((lateral[None, :] > p['right_bank_m'][sl, None]) &
                   (lateral[None, :] < p['left_bank_m'][sl, None]))
        for j, row in enumerate((depth >= .3) & in_bank):
            width = longest_supported_width(row)
            widths.append(width); centre_depth.append(float(depth[j, len(lateral)//2]))
            if width < 4.:
                rejected.append(dict(station_m=float(p['station_m'][start+j]),
                    continuous_point_clearance_width_m=width,
                    max_initial_reference_depth_m=float(depth[j][in_bank[j]].max(initial=-np.inf))))
    result = dict(schema='raftsim.chilko_corridor_bed_audit.v1',
        terrain_manifest_sha256=manifest_hash, source_manifest_sha256=receipt['terrain_manifest_sha256'],
        profile_manifest_sha256=receipt['profile_manifest_sha256'],
        chunks=len(m['chunks']), vertices_including_shared_edges=count,
        unchanged_source_vertices=preserved, explicitly_inferred_vertices=inferred,
        max_height_quantization_error_m=max_error,
        route_length_m=float(p['station_m'][-1]), sections=len(widths),
        initial_reference_clearance=dict(depth_threshold_m=.3, point_span_threshold_m=4.,
            lateral_sample_spacing_m=2., width_percentiles_m=np.percentile(widths, [0, 5, 50, 95]).tolist(),
            deficient_sections=rejected, negative_center_reference_depth_count=int((np.array(centre_depth)<0).sum())),
        source_ownership_passed=True, shared_edges_passed=True,
        ownership_policy=ownership_policy,
        inference_support_policy=support_policy,
        scope='Initial-reference geometric diagnostic only, not solved discharge/stage, boat footprint, named rapids or playable acceptance',
        engine_validated=False, navigation_validated=False)
    if sha(folder/'manifest.json') != manifest_hash: raise ValueError('Canonical terrain changed during audit')
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as f: json.dump(result, f, indent=2, allow_nan=False)
    print(json.dumps(dict(chunks=result['chunks'], preserved=preserved, inferred=inferred,
        deficient_initial_reference_sections=len(rejected), quantization_error_m=max_error)))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('canonical', 'terrain', 'profile', 'out'): parser.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args(); audit(a.canonical, a.terrain, a.profile, a.out)
