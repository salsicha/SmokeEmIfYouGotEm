"""Exact terrain pages and shared/exterior grid addressing for regional liquid.

This is a coupling contract, not independent tanks. Shared halo cells refer to
the unique physical owner, including diagonal neighbors. They contain no stage,
velocity forcing, emitter, or pressure-reservoir defaults. A runtime must exchange
pressure at each projection iteration and reduce particle/grid contributions;
copying last frame's halos is not an implementation of this contract.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_contact_region import extract
from build_south_fork_liquid_contact import sample_packed
from south_fork_registered_mesh import RegisteredMeshSampler


FACES = ('west', 'east', 'south', 'north')


def ownership_table(domain, regions):
    counts = np.asarray(domain['physical_cells'])
    if counts.shape != (3,) or not np.issubdtype(counts.dtype, np.integer) or (counts < 2).any():
        raise ValueError('Integer physical grid required')
    table = np.full((counts[1], counts[0]), -1, dtype=np.int32)
    ids = set()
    for r in regions:
        rid = r['id']
        bounds = np.asarray(r['cell_bounds_xy'])
        if (not isinstance(rid, int) or isinstance(rid, bool) or rid < 0 or rid in ids or
                bounds.shape != (2, 2) or not np.issubdtype(bounds.dtype, np.integer)):
            raise ValueError('Unique integer region IDs and cell bounds required')
        lo, hi = bounds
        if (lo < 0).any() or (hi > counts[:2]).any() or (hi-lo < 2).any():
            raise ValueError('Region outside parent or too narrow for two-cell halo')
        physical = np.r_[hi-lo, counts[2]]
        if not np.array_equal(physical, r['physical_cells']) or not np.array_equal(physical+[4, 4, 0], r['computational_cells']):
            raise ValueError('Region allocation disagrees with parent cells')
        view = table[lo[1]:hi[1], lo[0]:hi[0]]
        if (view >= 0).any():
            raise ValueError('Duplicate physical ownership')
        view[:] = rid
        ids.add(rid)
    if (table < 0).any():
        raise ValueError('Missing physical ownership')
    return table


def boundaries(parent, manifest, regions):
    """Slice exterior rows unchanged and address every XY halo cell exactly once.

    Index order is canonical station/lateral/up, NOT reflected Niagara local Y.
    The runtime must reflect both ends of a transfer consistently. Z is unchanged
    for all cell columns; no vertical halo is invented.
    """
    if parent.get('schema') != 'raftsim.liquid_grid_boundary.v3' or parent['domain'] != manifest['domain']:
        raise ValueError('Matching full-domain v3 boundary required')
    domain = manifest['domain']
    cells = np.asarray(domain['physical_cells'])
    packed = np.asarray(parent['packed_vectors'], dtype=float)
    nx, ny, nz = cells.tolist()
    offsets = [8, 8+ny, 8+2*ny, 8+2*ny+nx]
    lengths = [ny, ny, nx, nx]
    vector_offset = 8+2*(nx+ny)
    if (packed.shape != (vector_offset+2*(nx+ny), 3) or not np.isfinite(packed).all() or
            parent.get('vector_rows_offset') != vector_offset or parent.get('face_rows_offsets') != offsets or
            parent.get('face_row_counts') != lengths or not np.array_equal(packed[5], cells) or
            not np.array_equal(packed[6], cells+[4, 4, 0]) or
            not np.allclose(packed[4], np.asarray(domain['cell_size_m'])*100, atol=1e-9, rtol=0)):
        raise ValueError('Full boundary layout/metrics mismatch')
    table = ownership_table(domain, regions)
    by_id = {r['id']: r for r in regions}
    # Validate interface records against actual cell adjacency, not their flags.
    expected = set()
    for r in regions:
        lo, hi = np.asarray(r['cell_bounds_xy'])
        for axis in (0, 1):
            if hi[axis] == cells[axis]:
                continue
            row = table[lo[1]:hi[1], hi[0]] if axis == 0 else table[hi[1], lo[0]:hi[0]]
            neighbors = np.unique(row)
            if len(neighbors) != 1:
                raise ValueError('Split-face topology needs explicit segmented interfaces')
            expected.add((r['id'], int(neighbors[0]), axis, int(hi[axis]), int(lo[1-axis]), int(hi[1-axis])))
    interfaces, interface_ids = {}, set()
    for f in manifest['interfaces']:
        key = (f['lower_region'], f['upper_region'], f['axis'], f['parent_face_index'], *f['tangential_cell_range'])
        if (key not in expected or key in interfaces or f['id'] in interface_ids or
                f.get('native_source_emission') is not False or
                f.get('coupling') != 'shared-pressure-velocity-and-particle-transfer'):
            raise ValueError('Invalid shared interface or internal reservoir')
        interfaces[key] = f['id']; interface_ids.add(f['id'])
    if set(interfaces) != expected:
        raise ValueError('Missing shared interface')
    result = []
    for r in regions:
        lo, hi = np.asarray(r['cell_bounds_xy']); size = hi-lo
        if (r.get('canonical_frame') != 'parent-ENU-centimetres' or r.get('internal_source_emission') is not False or
                not np.allclose([r['axis_x_canonical'], r['axis_y_canonical']], packed[:2, :2], atol=1e-12, rtol=0)):
            raise ValueError('Regional canonical frame or emission mismatch')
        faces = []
        for face, name in enumerate(FACES):
            axis, positive = face//2, face % 2
            edge = int(hi[axis] if positive else lo[axis])
            begin, end = int(lo[1-axis]), int(hi[1-axis])
            record = dict(face=name, axis=axis, parent_face_index=edge, tangential_cell_range=[begin, end])
            exterior = edge == (cells[axis] if positive else 0)
            if exterior:
                base = offsets[face]+begin
                vb = vector_offset+offsets[face]-8+begin
                record.update(kind='external', parent_rows=list(range(base, base+end-begin)),
                    bed_stage_inward_speed_cm=packed[base:base+end-begin].tolist(),
                    velocity_station_lateral_up_cm_per_s=packed[vb:vb+end-begin].tolist())
            else:
                matches = [(k, value) for k, value in interfaces.items() if k[2:] == (axis, edge, begin, end)
                           and k[0 if positive else 1] == r['id']]
                if len(matches) != 1:
                    raise ValueError('Shared face does not match unique interface')
                key, interface_id = matches[0]
                record.update(kind='shared', interface_id=interface_id, neighbor_region=key[1 if positive else 0])
            faces.append(record)
        shared, external = [], []
        for y in range(int(size[1])+4):
            for x in range(int(size[0])+4):
                if 2 <= x < size[0]+2 and 2 <= y < size[1]+2:
                    continue
                p = lo+np.array([x, y])-2
                if (p >= 0).all() and (p < cells[:2]).all():
                    owner = int(table[p[1], p[0]])
                    source_lo = np.asarray(by_id[owner]['cell_bounds_xy'][0])
                    q = p-source_lo+2
                    # Destination XY, physical owner's ID and source XY. This
                    # includes diagonal corners, never another region's ghost.
                    shared.append([x, y, owner, int(q[0]), int(q[1])])
                else:
                    # Exact corresponding cell in full-parent computational
                    # grid. Corner handling stays with the external solver;
                    # do not pick an arbitrary face or invent a reservoir row.
                    external.append([x, y, int(p[0]+2), int(p[1]+2)])
        result.append(dict(schema='raftsim.regional_liquid_boundary.v1', region_id=r['id'],
            canonical_frame='parent-ENU-centimetres', index_frame='canonical-station-lateral-up',
            physical_cells=r['physical_cells'], computational_cells=r['computational_cells'],
            first_parent_cell_xy=lo.tolist(), cell_size_cm=packed[4].tolist(),
            origin_canonical_cm=r['origin_canonical_cm'], axis_x_canonical=r['axis_x_canonical'],
            axis_y_canonical=r['axis_y_canonical'], source_geometry_sha256=parent['source_geometry_sha256'],
            faces=faces, shared_halo_columns=shared, external_halo_columns=external,
            internal_source_emission=False, runtime_coupling_verified=False))
    return result


def contact_request(profile, region, spacing_m, query_padding_cm):
    if not np.isfinite(query_padding_cm) or query_padding_cm < 0:
        raise ValueError('Finite nonnegative query padding required')
    spacing = np.asarray(spacing_m, dtype=float)*100
    size = np.asarray(region['physical_cells'])[:2]
    axes = np.asarray([region['axis_x_canonical'], region['axis_y_canonical']])
    half = (size/2+1.5)*spacing[:2]
    corners = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])*half
    corners = corners@axes+np.asarray(region['origin_canonical_cm'])[:2]
    low, high = corners.min(axis=0)-query_padding_cm, corners.max(axis=0)+query_padding_cm
    meta, dims = np.asarray(profile['packed_vectors'][:2], dtype=np.float32)
    # One nominal quad on every side preserves the original query's 3x3
    # candidate search, including measured XY offsets at rock triangles.
    first = np.floor([(low[0]-meta[0])/meta[2], (meta[1]-high[1])/dims[0]]).astype(int)-1
    last = np.floor([(high[0]-meta[0])/meta[2], (meta[1]-low[1])/dims[0]]).astype(int)+1
    if profile['schema'] == 'raftsim.registered_liquid_contact.v3':
        offset = np.asarray(profile['packed_vectors'][2][:2], dtype=int)
        first -= offset; last -= offset
    return low, high, first, last


def extend_contact(profile, sampler, regions, spacing_m, query_padding_cm):
    """Extend insufficient parent support using only its original mesh triangles.

    Keep the old table intact and prove retained quad origins/vertices identical.
    This preparation table can exceed the DI cap; emitted pages cannot.
    """
    if profile.get('schema') != 'raftsim.registered_liquid_contact.v2':
        raise ValueError('Extension requires original v2 parent table')
    packed = np.asarray(profile['packed_vectors'], dtype=np.float32)
    meta, dims = packed[:2]; nc, nr = dims[1:].astype(int)
    requests = [contact_request(profile, r, spacing_m, query_padding_cm) for r in regions]
    first = np.minimum(np.min([q[2] for q in requests], axis=0), [0, 0])
    last = np.maximum(np.max([q[3] for q in requests], axis=0), [nc-1, nr-1])
    # Locate the nominal source origin in float32, the profile's actual ABI.
    cs = np.flatnonzero((sampler.east*100).astype(np.float32) == meta[0])
    rs = np.flatnonzero((sampler.north*100).astype(np.float32) == meta[1])
    if len(cs) != 1 or len(rs) != 1 or not np.allclose([sampler.dx*100, sampler.dy*100], [meta[2], dims[0]], atol=1e-9, rtol=0):
        raise ValueError('Contact table cannot be located in original captured mesh')
    lo = np.array([cs[0], rs[0]])+first
    hi = np.array([cs[0], rs[0]])+last+1
    if (lo < 0).any() or (hi > [sampler.cols-1, sampler.rows-1]).any():
        raise ValueError('Original captured mesh lacks requested support; no clamping')
    c, r = np.meshgrid(np.arange(lo[0], hi[0]), np.arange(lo[1], hi[1]))
    q = r.ravel()*(sampler.cols-1)+c.ravel()
    faces = np.stack([sampler.faces[q], sampler.faces[q+sampler.quads]], axis=1).reshape(-1, 3)
    vertices = sampler.xyz[faces].reshape(-1, 3)*100
    origins = np.c_[sampler.east[c.ravel()], sampler.north[r.ravel()]]*100
    vertices[:, :2] -= np.repeat(origins, 6, axis=0)
    vertices = vertices.astype(np.float32)
    count = hi-lo
    new_meta = np.array([sampler.east[lo[0]]*100, sampler.north[lo[1]]*100, meta[2]], dtype=np.float32)
    old_start = -first
    retained = vertices.reshape(count[1], count[0], 6, 3)[old_start[1]:old_start[1]+nr, old_start[0]:old_start[0]+nc]
    if not np.array_equal(retained.reshape(-1, 3), packed[2:]):
        raise ValueError('Extending contact would change original triangle bytes')
    for axis, n, step in ((0, nc, meta[2]), (1, nr, -dims[0])):
        a = np.float32(meta[axis]+np.arange(n)*float(step))
        b = np.float32(new_meta[axis]+(old_start[axis]+np.arange(n))*float(step))
        if not np.array_equal(a, b):
            raise ValueError('Extending contact would change original quad origins')
    result = {k: v for k, v in profile.items() if k not in ('packed_vectors', 'query_seed_count', 'seed_query_max_error_cm')}
    result.update(schema='raftsim.registered_liquid_contact.v3',
        packed_vectors=np.concatenate([meta[None], [[dims[0], *count]], [[*first, 0]], vertices]).tolist(),
        query_columns=int(count[0]), query_rows=int(count[1]), triangle_count=int(2*np.prod(count)),
        extended_original_nominal_quad_bounds=[lo.tolist(), hi.tolist()],
        retained_parent_quad_region=[*old_start.tolist(), int(nc), int(nr)],
        retained_parent_triangle_bytes_exact=True, runtime_support_verified=False)
    return result


def contact_page(profile, region, spacing_m, query_padding_cm=50.):
    """Retain all 3x3 nominal-quad query candidates around the requested support.

    Support = full computational cell centers' ENU AABB plus explicit padding.
    Padding is a spatial contract, not a verified maximum particle sweep. A
    moving runtime must enforce/query its support rather than clamp an escape.
    """
    low, high, first, last = contact_request(profile, region, spacing_m, query_padding_cm)
    count = last-first+1
    page = extract(profile, *first.tolist(), *count.tolist(), stable_anchor=True)
    page.update(region_id=region['id'], query_support_bounds_enu_cm=[low.tolist(), high.tolist()],
                query_padding_cm=float(query_padding_cm), query_candidate_halo_quads=1)
    # Check all current seeds and every computational XY center, plus a fixed
    # sample of the declared support. These are query tests, not GPU contacts.
    size = np.asarray(region['physical_cells'])[:2]
    spacing = np.asarray(spacing_m, dtype=float)*100
    axes = np.asarray([region['axis_x_canonical'], region['axis_y_canonical']])
    x, y = np.meshgrid((np.arange(size[0]+4)-size[0]/2-1.5)*spacing[0],
                       (np.arange(size[1]+4)-size[1]/2-1.5)*spacing[1])
    centers = np.c_[x.ravel(), y.ravel()]@axes+np.asarray(region['origin_canonical_cm'])[:2]
    probes = np.random.default_rng(910+region['id']).uniform(low, high, (4096, 2))
    probes = np.concatenate((probes, np.array([[low[0], low[1]], [low[0], high[1]],
                                             [high[0], low[1]], [high[0], high[1]]])))
    seeds = np.asarray(region['positions_canonical_cm'], dtype=float).reshape(-1, 3)[:, :2]
    points = np.concatenate((seeds, centers, probes)).astype(np.float32)
    original = sample_packed(profile['packed_vectors'], points, True, profile['schema'].endswith('.v3'))
    cropped = sample_packed(page['packed_vectors'], points, True, True)
    if not np.isfinite(original).all() or not np.array_equal(original, cropped):
        bad = np.flatnonzero(~np.isfinite(original) | (original != cropped))
        raise ValueError('Regional contact query lost support or changed captured triangles: '+str(dict(
            region=region['id'], bad=len(bad), original_missing=int(np.isnan(original).sum()),
            cropped_missing=int(np.isnan(cropped).sum()), max_error_cm=float(np.nanmax(abs(original-cropped))),
            examples=[dict(point=points[i].tolist(), original=float(original[i]), cropped=float(cropped[i])) for i in bad[:5]])))
    page.update(prepared_query_count=len(points), prepared_query_bitwise_parity=True)
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent', type=Path); parser.add_argument('regions', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--query-padding-cm', type=float, default=50.)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve previous regional geometry evidence')
    read = lambda p: json.loads(p.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = read(args.regions/'manifest.json')
    for name, digest in manifest['parent_files_sha256'].items():
        if sha(args.parent/name) != digest:
            raise ValueError('Parent identity changed: '+name)
    regions = []
    for record in manifest['region_files']:
        path = args.regions/record['file']
        if sha(path) != record['sha256']:
            raise ValueError('Regional identity changed: '+record['file'])
        regions.append(read(path))
    parent_boundary = read(args.parent/'grid_vector_boundary_profile.json')
    contact = read(args.parent/'triangle_contact_profile.json')
    if contact['source_geometry_sha256'] != manifest['geometry_source_sha256'] or parent_boundary['source_geometry_sha256'] != manifest['geometry_source_sha256']:
        raise ValueError('Contact/boundary captured geometry identity mismatch')
    records = boundaries(parent_boundary, manifest, regions)
    root = Path(__file__).resolve().parents[2]
    window = read(args.parent/'manifest.json')
    geometry = read(root/window['source_geometry_manifest'])
    mesh_path = root/geometry['mesh_path']
    if sha(mesh_path) != manifest['geometry_source_sha256']:
        raise ValueError('Original captured mesh identity changed')
    with np.load(mesh_path) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    contact = extend_contact(contact, sampler, regions, manifest['domain']['cell_size_m'], args.query_padding_cm)
    args.output.mkdir(parents=True)
    extended_path = args.output/'extended_parent_contact.json'
    extended_path.write_text(json.dumps(contact, separators=(',', ':'), allow_nan=False)+'\n')
    emitted = []
    for r, b in zip(regions, records):
        c = contact_page(contact, r, manifest['domain']['cell_size_m'], args.query_padding_cm)
        paths = [args.output/f"region-{r['id']:03d}-{suffix}.json" for suffix in ('boundary', 'contact')]
        for path, data in zip(paths, (b, c)):
            path.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False)+'\n')
        emitted.append(dict(id=r['id'], files={p.name: sha(p) for p in paths},
            contact_query_count=c['prepared_query_count'], contact_quad_region=c['source_quad_region'],
            shared_halo_columns=len(b['shared_halo_columns']), external_halo_columns=len(b['external_halo_columns'])))
        print('Prepared region', r['id'], flush=True)
    result = dict(schema='raftsim.regional_liquid_geometry.v1',
        ownership_manifest_sha256=sha(args.regions/'manifest.json'),
        extended_parent_contact_sha256=sha(extended_path), original_mesh_sha256=sha(mesh_path),
        parent_files_sha256={n: sha(args.parent/n) for n in ('triangle_contact_profile.json', 'grid_vector_boundary_profile.json')},
        regions=emitted, query_padding_cm=args.query_padding_cm,
        runtime_coupling_verified=False, performance_or_visual_acceptance=False)
    (args.output/'manifest.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
