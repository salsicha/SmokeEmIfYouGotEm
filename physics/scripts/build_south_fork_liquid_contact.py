"""Pack preserved registered triangles for identical GPU contact/pressure queries."""
import hashlib
import json
from pathlib import Path
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT = Path(__file__).resolve().parents[2]


def sample_packed(packed, xy, relative_vertices=False, anchored=False):
    """Float32 reference for the bounded GPU query, not raster interpolation."""
    packed = np.asarray(packed, dtype=np.float32)
    xy = np.asarray(xy, dtype=np.float32)
    m, n = packed[:2]
    cols, rows = int(n[1]), int(n[2])
    offset = packed[2, :2].astype(int) if anchored else np.zeros(2, dtype=int)
    header = 3 if anchored else 2
    c0 = np.floor((xy[:, 0]-m[0])/m[2]).astype(int)-offset[0]
    r0 = np.floor((m[1]-xy[:, 1])/n[0]).astype(int)-offset[1]
    result = np.full(len(xy), np.nan, dtype=np.float32)
    for dr in (0, -1, 1):
        for dc in (0, -1, 1):
            r, c = r0+dr, c0+dc
            pending = np.flatnonzero((r >= 0)&(r < rows)&(c >= 0)&(c < cols)&np.isnan(result))
            for side in (0, 1):
                pending = pending[np.isnan(result[pending])]
                base = header+((r[pending]*cols+c[pending])*2+side)*3
                a, b, d = (packed[base+i] for i in (0, 1, 2))
                query=xy[pending]
                if relative_vertices:
                    origin=np.column_stack((m[0]+(c[pending]+offset[0])*m[2],m[1]-(r[pending]+offset[1])*n[0])).astype(np.float32)
                    query=query-origin
                ab, ad, ap = b-a, d-a, query-a[:, :2]
                det = ab[:, 0]*ad[:, 1]-ab[:, 1]*ad[:, 0]
                u = (ap[:, 0]*ad[:, 1]-ap[:, 1]*ad[:, 0])/det
                v = (ab[:, 0]*ap[:, 1]-ab[:, 1]*ap[:, 0])/det
                inside = (u >= -1e-5)&(v >= -1e-5)&(u+v <= 1+1e-5)
                result[pending[inside]] = (a[:, 2]+u*ab[:, 2]+v*ad[:, 2])[inside]
    return result


def main(directory=None):
    directory = Path(directory) if directory is not None else ROOT/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
    output = directory/'triangle_contact_profile.json'
    if output.exists():
        raise FileExistsError('Retain previous contact geometry evidence')
    window = json.loads((directory/'manifest.json').read_text())
    geometry = json.loads((ROOT/window['source_geometry_manifest']).read_text())
    path = ROOT/geometry['mesh_path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != window['source_geometry_sha256']:
        raise ValueError('Registered geometry changed')
    sampler = RegisteredMeshSampler(np.load(path))
    extent=np.asarray(window.get('physical_extent_xy_m',[20.,20.]))
    centre=np.asarray(window.get('centre_station_lateral_m',[0.,0.]))
    legacy=np.array_equal(extent,[20.,20.]) and np.array_equal(centre,[0.,0.])
    if legacy:
        # Preserve the original 40m query box around the 21m fixture.
        cs=np.flatnonzero(abs(sampler.east)<=20);rs=np.flatnonzero(abs(sampler.north)<=20)
    else:
        registration=json.loads((ROOT/window['source_hydraulic_directory']).parent.joinpath('registration.json').read_text())
        rotation=np.column_stack([registration['downstream_unit'],registration['left_unit']])
        corners=(np.array([[-1,-1],[1,-1],[1,1],[-1,1]])*extent/2+centre)@rotation.T
        low=corners.min(axis=0)-2;high=corners.max(axis=0)+2
        if low[0]<sampler.east[0] or high[0]>sampler.east[-1] or low[1]<sampler.north[-1] or high[1]>sampler.north[0]:
            raise ValueError('Full contact domain lacks captured query support; no clamping')
        cs=np.flatnonzero((sampler.east>=low[0])&(sampler.east<=high[0]))
        rs=np.flatnonzero((sampler.north>=low[1])&(sampler.north<=high[1]))
    cmin, cmax, rmin, rmax = cs[0], cs[-1], rs[0], rs[-1]
    r, c = np.meshgrid(np.arange(rmin, rmax), np.arange(cmin, cmax), indexing='ij')
    q = r.ravel()*(sampler.cols-1)+c.ravel()
    faces = np.stack((sampler.faces[q], sampler.faces[q+sampler.quads]), axis=1).reshape(-1, 3)
    vertices = sampler.xyz[faces].reshape(-1, 3)*100
    if not legacy:
        # Preserve sub-centimetre registered offsets without subtracting two
        # rounded large world coordinates for every skinny rock triangle.
        origins=np.column_stack((sampler.east[c.ravel()],sampler.north[r.ravel()]))*100
        vertices[:,:2]-=np.repeat(origins,6,axis=0)
    vertices=vertices.astype(np.float32)
    meta = np.array([[sampler.east[cmin]*100, sampler.north[rmin]*100, sampler.dx*100],
                     [sampler.dy*100, cmax-cmin, rmax-rmin]], dtype=np.float32)
    packed = np.concatenate((meta, vertices))
    seeds = json.loads((directory/'hydraulic_initial_state.json').read_text())
    points = np.array(seeds['positions_world_cm'])[:, :2]
    actual = sampler.sample(points[:, 0]/100, points[:, 1]/100)*100
    sampled = sample_packed(packed, points,relative_vertices=not legacy)
    error = np.abs(actual-sampled)
    if not np.isfinite(sampled).all() or error.max() > .01:
        invalid=~np.isfinite(sampled)|(error>.01)
        examples=[dict(xy_cm=points[i].tolist(),expected_cm=float(actual[i]),sampled_cm=float(sampled[i]),error_cm=float(error[i]))
                  for i in np.flatnonzero(invalid)[:5]]
        raise ValueError(f'Packed float32 query disagrees with registered topology: nonfinite={int((~np.isfinite(sampled)).sum())}, max_error_cm={float(np.nanmax(error))}, examples={examples}')
    report = {'schema': 'raftsim.registered_liquid_contact.v1' if legacy else 'raftsim.registered_liquid_contact.v2',
              'source_geometry_sha256': window['source_geometry_sha256'],
              'packed_vectors': packed.tolist(), 'triangle_count': len(faces),
              'query_seed_count': len(points), 'seed_query_max_error_cm': float(error.max()),
              'query_columns':int(cmax-cmin),'query_rows':int(rmax-rmin),
              'runtime_support_verified':False,
              'vertex_encoding':'world-centimetres' if legacy else 'nominal-quad-local-xy-and-world-z-centimetres',
              'query_authority': 'Preserved XY/triangles, float32 world centimetres; not mesh SDF or resampled height raster',
              'submerged_bed_authority': window['submerged_bed_authority'],
              'registered_rapid_identity_verified': False, 'production_promoted': False}
    with output.open('x') as stream:
        json.dump(report, stream, separators=(',', ':'))
    print({k: report[k] for k in ('triangle_count', 'query_seed_count', 'seed_query_max_error_cm')})


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path)
    main(parser.parse_args().directory)
