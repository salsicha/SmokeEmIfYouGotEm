"""Read-only, independent reassembly of regional terrain and halo records.

Does not call the preparation or ownership builders. This proves data identity
and address coverage, not runtime pressure exchange, GPU contacts or realism.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from build_south_fork_liquid_contact import sample_packed


def audit(parent, states, geometry):
    read = lambda p: json.loads(p.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = read(geometry/'manifest.json'); ownership = read(states/'manifest.json')
    if sha(states/'manifest.json') != manifest['ownership_manifest_sha256']:
        raise ValueError('Ownership identity changed')
    for name, digest in manifest['parent_files_sha256'].items():
        if sha(parent/name) != digest:
            raise ValueError('Parent geometry identity changed')
    for record in ownership['region_files']:
        if sha(states/record['file']) != record['sha256']:
            raise ValueError('Regional state identity changed')
    ext_path = geometry/'extended_parent_contact.json'
    if sha(ext_path) != manifest['extended_parent_contact_sha256']:
        raise ValueError('Extended contact identity changed')
    original = read(parent/'triangle_contact_profile.json')
    extended = read(ext_path)
    root = Path(__file__).resolve().parents[2]
    window = read(parent/'manifest.json'); source_manifest = read(root/window['source_geometry_manifest'])
    mesh_path = root/source_manifest['mesh_path']
    if sha(mesh_path) != manifest['original_mesh_sha256'] or manifest['original_mesh_sha256'] != original['source_geometry_sha256']:
        raise ValueError('Captured mesh identity changed')
    # Verify ALL extended triangles against the original source faces, not just
    # their overlap with the old clipped table. No registration is refitted.
    with np.load(mesh_path) as mesh:
        xyz = np.c_[mesh['east_m'].ravel(), mesh['north_m'].ravel(), mesh['z_m'].ravel()]*100
        east = mesh['nominal_east_axis_m']*100; north = mesh['nominal_north_axis_m']*100
        triangles = mesh['triangles']; total_quads = (len(east)-1)*(len(north)-1)
        (sc, sr), (hc, hr) = extended['extended_original_nominal_quad_bounds']
        cc, rr = np.meshgrid(np.arange(sc, hc), np.arange(sr, hr))
        index = (rr*(len(east)-1)+cc).ravel()
        faces = np.stack([triangles[index], triangles[index+total_quads]], axis=1).reshape(-1, 3)
        source_vertices = xyz[faces].reshape(-1, 3)
        source_vertices[:, :2] -= np.repeat(np.c_[east[cc.ravel()], north[rr.ravel()]], 6, axis=0)
    old = np.asarray(original['packed_vectors'], dtype=np.float32)
    big = np.asarray(extended['packed_vectors'], dtype=np.float32)
    nc, nr = old[1, 1:].astype(int); ec, er = big[1, 1:].astype(int)
    if not np.array_equal(old[0], big[0]):
        raise ValueError('Addressing anchor changed')
    x0, y0 = -big[2, :2].astype(int)
    all_triangles = big[3:].reshape(er, ec, 6, 3)
    if not np.array_equal(source_vertices.astype(np.float32), big[3:]):
        raise ValueError('Extended support triangles differ from original mesh')
    if not np.array_equal(old[2:].reshape(nr, nc, 6, 3), all_triangles[y0:y0+nr, x0:x0+nc]):
        raise ValueError('Original contact triangles changed')
    boundary = read(parent/'grid_vector_boundary_profile.json')
    rows = np.asarray(boundary['packed_vectors'])
    nx, ny, nz = ownership['domain']['physical_cells']
    region_states = {r['id']: r for r in (read(states/e['file']) for e in ownership['region_files'])}
    if set(region_states) != {r['id'] for r in manifest['regions']} or len(region_states) != len(manifest['regions']):
        raise ValueError('Incomplete geometry coverage')
    seen_external_rows = []
    shared_total = external_total = queried_seeds = queried_cells = 0
    probes_total = 0
    for record in manifest['regions']:
        rid = record['id']; state = region_states[rid]
        for name, digest in record['files'].items():
            if sha(geometry/name) != digest:
                raise ValueError('Regional geometry bytes changed')
        b = read(geometry/f'region-{rid:03d}-boundary.json')
        page = read(geometry/f'region-{rid:03d}-contact.json')
        if b['schema'] != 'raftsim.regional_liquid_boundary.v1' or b['internal_source_emission'] is not False:
            raise ValueError('Legacy tank or internal emission')
        if b['index_frame'] != 'canonical-station-lateral-up' or b['region_id'] != rid:
            raise ValueError('Wrong boundary address frame')
        for name in ('physical_cells', 'computational_cells', 'origin_canonical_cm', 'axis_x_canonical', 'axis_y_canonical'):
            if b[name] != state[name]:
                raise ValueError('Geometry/state frame mismatch: '+name)
        lo, hi = np.asarray(state['cell_bounds_xy']); size = hi-lo
        for i, face in enumerate(b['faces']):
            axis, sign = i//2, 1 if i % 2 else -1
            edge = int(hi[axis] if sign > 0 else lo[axis])
            external = edge == ([nx, ny][axis] if sign > 0 else 0)
            if (face['kind'] == 'external') != external:
                raise ValueError('Internal cut mistaken for native river boundary')
            if external:
                starts = [8, 8+ny, 8+2*ny, 8+2*ny+nx]
                expected = np.arange(starts[i]+lo[1-axis], starts[i]+hi[1-axis])
                if not np.array_equal(face['parent_rows'], expected):
                    raise ValueError('Exterior rows missing/reordered')
                seen_external_rows.extend(expected.tolist())
                if not np.array_equal(face['bed_stage_inward_speed_cm'], rows[expected]) or not np.array_equal(
                        face['velocity_station_lateral_up_cm_per_s'], rows[expected+boundary['vector_rows_offset']-8]):
                    raise ValueError('Exterior forcing changed')
            else:
                if any(k in face for k in ('parent_rows', 'bed_stage_inward_speed_cm', 'velocity_station_lateral_up_cm_per_s')):
                    raise ValueError('Internal reservoir values present')
                neighbor = region_states[face['neighbor_region']]
                nlo, nhi = np.asarray(neighbor['cell_bounds_xy'])
                if edge != (nlo[axis] if sign > 0 else nhi[axis]) or lo[1-axis] != nlo[1-axis] or hi[1-axis] != nhi[1-axis]:
                    raise ValueError('Wrong shared face neighbor')
        expected_cells = {(x, y) for y in range(size[1]+4) for x in range(size[0]+4)
                          if not (2 <= x < size[0]+2 and 2 <= y < size[1]+2)}
        seen = []
        for x, y, owner, sx, sy in b['shared_halo_columns']:
            seen.append((x, y)); shared_total += 1
            src = region_states[owner]; slo, shi = np.asarray(src['cell_bounds_xy'])
            if owner == rid or not (2 <= sx < shi[0]-slo[0]+2 and 2 <= sy < shi[1]-slo[1]+2):
                raise ValueError('Shared source is not a neighbors physical cell')
            if not np.array_equal(lo+[x-2, y-2], slo+[sx-2, sy-2]):
                raise ValueError('Shared cells have different canonical position')
        for x, y, px, py in b['external_halo_columns']:
            seen.append((x, y)); external_total += 1
            if not np.array_equal(lo+[x, y], [px, py]) or (2 <= px < nx+2 and 2 <= py < ny+2):
                raise ValueError('Exterior halo mismatch')
        if len(seen) != len(expected_cells) or set(seen) != expected_cells:
            raise ValueError('Lost/duplicate halo address')
        packed = np.asarray(page['packed_vectors'], dtype=np.float32)
        pc, pr = packed[1, 1:].astype(int)
        if page['schema'] != 'raftsim.registered_liquid_contact.v3' or max(pc, pr) > 256 or not np.array_equal(packed[0], old[0]):
            raise ValueError('Invalid bounded anchored contact')
        first = (packed[2, :2]-big[2, :2]).astype(int)
        expected_triangles = all_triangles[first[1]:first[1]+pr, first[0]:first[0]+pc]
        if not np.array_equal(packed[3:].reshape(pr, pc, 6, 3), expected_triangles):
            raise ValueError('Page moved/resampled a captured triangle')
        seeds = np.asarray(state['positions_canonical_cm']).reshape(-1, 3)[:, :2].astype(np.float32)
        values = sample_packed(packed, seeds, True, True)
        if not np.array_equal(values, sample_packed(old, seeds, True)) or not np.isfinite(values).all():
            raise ValueError('Seed contact changed from ORIGINAL pre-extension parent')
        queried_seeds += len(seeds)
        spacing = np.asarray(ownership['domain']['cell_size_m'])*100
        cx, cy = np.meshgrid((np.arange(size[0]+4)-size[0]/2-1.5)*spacing[0],
                             (np.arange(size[1]+4)-size[1]/2-1.5)*spacing[1])
        axes = np.asarray([state['axis_x_canonical'], state['axis_y_canonical']])
        centers = (np.c_[cx.ravel(), cy.ravel()]@axes+state['origin_canonical_cm'][:2]).astype(np.float32)
        support = np.asarray(page['query_support_bounds_enu_cm'])
        if (centers < support[0]).any() or (centers > support[1]).any():
            raise ValueError('Computational center outside declared query support')
        probes = np.random.default_rng(1061+rid).uniform(*support, (8192, 2)).astype(np.float32)
        points = np.concatenate([centers, probes])
        a = sample_packed(big, points, True, True); c = sample_packed(packed, points, True, True)
        if not np.isfinite(c).all() or not np.array_equal(a, c):
            raise ValueError('Grid or independent support probe contact mismatch')
        queried_cells += len(centers); probes_total += len(probes)
    if sorted(seen_external_rows) != list(range(8, boundary['vector_rows_offset'])):
        raise ValueError('Not all exterior rows retained exactly once')
    return dict(prepared_geometry_audit_passed=True, region_count=len(region_states),
        exterior_rows_preserved_once=len(seen_external_rows), shared_halo_columns=shared_total,
        external_halo_columns=external_total, seeds_contact_bitwise_equal_to_original_parent=queried_seeds,
        computational_xy_centers_checked=queried_cells, independent_support_probes=probes_total,
        original_triangle_bytes_unchanged=True, original_address_anchor_unchanged=True,
        all_extended_triangles_verified_against_original_mesh=int(len(big[3:])//3),
        geometry_manifest_sha256=sha(geometry/'manifest.json'), runtime_coupling_verified=False,
        gpu_contact_verified=False, pressure_continuity_verified=False, performance_or_visual_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('parent', 'states', 'geometry', 'output'): parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError('Keep previous audit evidence')
    result = audit(args.parent, args.states, args.geometry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))
