"""Inspect source agreement and exact native face fluxes; never grade difficulty."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from build_colorado_catalog_evidence import sha
from solver_face_discharge import face_discharge


def load_frame(path,shape):
    table=np.genfromtxt(path,delimiter=',',names=True)
    if table.size!=np.prod(shape):raise ValueError('Incomplete native frame')
    rows,cols=np.indices(shape)
    for key,expected in (('row',rows),('col',cols)):
        if not np.array_equal(table[key].reshape(shape),expected):raise ValueError('Unordered frame cells')
    fields={k:table[k].reshape(shape) for k in table.dtype.names}
    if any(not np.isfinite(a).all() for a in fields.values()):raise ValueError('Nonfinite native state')
    if (fields['h']<0).any():raise ValueError('Negative water depth')
    return fields


def compare(reference,final,previous,step):
    wet=final['h']>.05; source=reference['classified_water'].astype(bool)
    both=wet&source; union=wet|source
    if not both.any():raise ValueError('No water in common with classified source')
    delta=np.where(both,final['eta']-reference['reference_surface'][None,:],np.nan)
    # Leave empty sections missing, never treat their water-height error as zero.
    med=np.array([np.median(delta[:,i][both[:,i]]) if both[:,i].any() else np.nan
                  for i in range(delta.shape[1])])
    available=med[np.isfinite(med)]
    edge_distance=distance_transform_edt(~source)*step
    changing=wet|(previous['h']>.05)
    return dict(wet_intersection_over_union=float(both.sum()/union.sum()),
        extra_wet_cells=int((wet&~source).sum()),
        extra_wet_cells_over_4m_from_source=int((wet&~source&(edge_distance>4)).sum()),
        missing_source_water_cells=int((source&~wet).sum()),
        surface_sections_sampled=int(len(available)),surface_sections_missing=int((~np.isfinite(med)).sum()),
        surface_error_median_m=float(np.median(available)),
        surface_error_abs_p95_m=float(np.percentile(np.abs(available),95)),
        depth_change_p95_m=float(np.percentile(np.abs(final['h']-previous['h'])[changing],95)),
        depth_change_max_m=float(np.abs(final['h']-previous['h'])[changing].max()),
        maximum_speed_mps=float(np.hypot(final['u'],final['v'])[wet].max()),
        maximum_depth_m=float(final['h'].max()),
        sampled_reference_station_m=reference['station'].tolist(),
        surface_error_per_station_m=[float(v) if np.isfinite(v) else None for v in med])


def review(inputs,cook,solver,out):
    if out.exists():raise ValueError('Fresh review directory required')
    build=json.loads((inputs/'build_report.json').read_text())
    for name,digest in build['files_sha256'].items():
        if sha(inputs/name)!=digest:raise ValueError('Solver input changed')
    reference=dict(np.load(inputs/'reference.npz'))
    frames=sorted((cook/'frames').glob('frame_*.csv'))
    if len(frames)<2:raise ValueError('Need two native frames for settling comparison')
    shape=reference['classified_water'].shape
    current=load_frame(frames[-1],shape); previous=load_frame(frames[-2],shape)
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    dx=scenario['grid']['dx'];dy=scenario['grid']['dy']
    expected_x=np.arange(shape[1])*dx+scenario['grid']['origin_x']
    expected_y=np.arange(shape[0])*dy+scenario['grid']['origin_y']
    if not np.allclose(current['x'],expected_x[None,:]) or not np.allclose(current['y'],expected_y[:,None]):
        raise ValueError('Native frame is in a different grid')
    stats=compare(reference,current,previous,dy)
    flux=face_discharge(solver,inputs/'scenario',current)
    q=scenario['boundaries'][0]['metadata']['target_discharge_m3s']
    stats.update(exact_face_discharge_target_m3s=q,
        exact_face_discharge_inlet_m3s=float(flux[0]),exact_face_discharge_outlet_m3s=float(flux[-1]),
        exact_face_discharge_range_m3s=[float(flux.min()),float(flux.max())],
        exact_face_discharge_abs_error_p95_fraction=float(np.percentile(abs(flux-q)/q,95)))
    gates=dict(surface_abs_p95_below_1m=stats['surface_error_abs_p95_m']<1.,
        wet_iou_at_least_point9=stats['wet_intersection_over_union']>=.9,
        discharge_abs_p95_below_5percent=stats['exact_face_discharge_abs_error_p95_fraction']<.05,
        settling_depth_p95_below_3cm=stats['depth_change_p95_m']<.03)
    report=dict(schema='raftsim.colorado_catalog_cook_review.v1',name=build['name'],
        scope='Construction-screen thresholds only; not engine, boat, rapid-specific, visual, or FPS acceptance.',
        source_profile_flow_cfs_approx=8400,target_flow_cfs=8000,
        comparison_frames=[p.name for p in frames[-2:]],
        frame_sha256={p.name:sha(p) for p in frames[-2:]},solver_sha256=sha(solver),
        native_manifest=json.loads((cook/'manifest.json').read_text()),statistics=stats,
        construction_screen=gates,construction_screen_passed=all(gates.values()),
        engine_validated=False,class_match='not_established')
    out.mkdir(parents=True)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(name=build['name'],construction_screen=gates,
        statistics={k:v for k,v in stats.items() if not k.endswith('per_station_m') and k!='sampled_reference_station_m'}),indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','cook','solver','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();review(a.inputs.resolve(),a.cook.resolve(),a.solver.resolve(),a.out.resolve())
