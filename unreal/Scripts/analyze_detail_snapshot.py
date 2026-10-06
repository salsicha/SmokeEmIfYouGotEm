"""Analyze actual opt-in engine GPU snapshots; no inferred FPS or realism score."""
import json
import argparse
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'docs/reconstruction-review-2026-09-07/detail-snapshot'


def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def describe(x):
    return dict(minimum=float(x.min()), maximum=float(x.max()),
                mean=float(x.mean()), rms=float(np.sqrt(np.mean(x*x))),
                standard_deviation=float(x.std()),
                p50_abs=float(np.quantile(abs(x), .5)), p95_abs=float(np.quantile(abs(x), .95)))


def analyze(prefix, moving_cartesian=False):
    metadata = json.loads(Path(str(prefix)+'.json').read_text(encoding='utf-8-sig'))
    assert metadata['schema'] == 'raftsim.detail.snapshot.v1' and metadata['arrays_complete']
    shape = tuple(metadata['shape'])
    cell = metadata['cell_m']
    assert (shape, cell) in [((128,128,4),.5), ((256,256,4),.25)]
    ny, nx, _ = shape
    origin = np.array(metadata['origin_m'])
    if moving_cartesian:
        assert np.isfinite(origin).all() and np.array_equal(origin/cell,np.round(origin/cell))
        assert metadata['center_world_cm']==[0,0,0]
        assert metadata['downstream_world']==[1,0,0]
        assert metadata['left_world'] in ([0,1,0],[0,-1,0])
    else:
        assert np.allclose(origin-cell*.5, [-32.25,-32.25])
    arrays = {}
    for name in ('flow', 'state', 'surface'):
        data = np.fromfile(str(prefix)+'.'+name+'.f32', dtype='<f4')
        assert data.size == ny*nx*4 and np.isfinite(data).all(), name
        arrays[name] = data.reshape(shape).astype(np.float64)
    flow, state, surface = (arrays[n] for n in ('flow', 'state', 'surface'))
    y, x = np.indices((ny, nx))
    edge = np.minimum.reduce((x, y, nx-1-x, ny-1-y))*cell
    weight = smooth(0,4,edge)*smooth(.02,.4,flow[...,0])
    height = state[...,0]*weight
    padded = np.pad(height,1,mode='edge')
    dx = (padded[1:-1,2:] - padded[1:-1,:-2])/(2*cell)
    dy = (padded[2:,1:-1] - padded[:-2,1:-1])/(2*cell)
    expected = np.stack((height, dx, dy, (1-np.exp(-np.maximum(state[...,3],0)))*weight),axis=-1)
    expected[weight<=0] = 0
    errors = np.max(abs(surface-expected),axis=(0,1))
    assert max(errors)<1e-5, errors
    assert state[...,3].min()>=-1e-6 and surface[...,3].max()<=1.000001
    group_origin=-(np.array([nx,ny])-1)*cell*.5 if moving_cartesian else origin
    crux = (abs(x*cell+group_origin[0])<=16)&(abs(y*cell+group_origin[1])<=12)
    masks = dict(wet_interior=(weight>.99), entrainment=(weight>.99)&(flow[...,3]>.3),
                 foam=(weight>.99)&(surface[...,3]>.65), dense_foam=(weight>.99)&(surface[...,3]>.9),
                 crux_foam=crux&(weight>.99)&(surface[...,3]>.65))
    groups = {}
    for name, mask in masks.items():
        group = dict(cells=int(mask.sum()))
        if mask.any():
            group.update(height_m=describe(surface[...,0][mask]),
                         slope=describe(np.linalg.norm(surface[...,1:3],axis=-1)[mask]),
                         coverage=describe(surface[...,3][mask]), source=describe(flow[...,3][mask]))
        groups[name] = group
    return dict(prefix=prefix.name,metadata=metadata,resolve_max_errors=errors.tolist(),groups=groups), arrays


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DIRECTORY)
    parser.add_argument('--moving-cartesian',action='store_true')
    args=parser.parse_args()
    directory = args.directory
    reports=[]; previous=None; temporal=[]
    for i in range(3):
        report, arrays = analyze(directory/f'live_{i:02d}',args.moving_cartesian)
        reports.append(report)
        if previous is not None and not args.moving_cartesian:
            mask=(arrays['surface'][...,3]>.65)&(previous['surface'][...,3]>.65)
            temporal.append(dict(cells=int(mask.sum()),height_change_m=describe(
                arrays['surface'][...,0][mask]-previous['surface'][...,0][mask]) if mask.any() else None))
        previous=arrays
    result=dict(snapshots=reports,temporal_foam_overlap=temporal,
                moving_cartesian=args.moving_cartesian,
                limitations='Three sparse physical snapshots. Not a frequency spectrum, total macro wave height, particle collision, FPS or photographic acceptance. Crux group is relative to the detail-window center, not an image-space ROI. Moving windows deliberately omit index-wise temporal comparisons: those indices do not represent the same world locations.')
    (directory/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
