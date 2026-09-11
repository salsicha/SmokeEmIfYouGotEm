"""Attribute exposed surface changes to the solver-cell interior floor.

Uses the captured pre-floor density and post-floor scalar, not material pixels.
This detects a rendering contribution, not the cause of particle undersampling.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_anisotropic_surface import upper_surface


def analyze(directory):
    source=directory/'live_density'
    shape=(48,136,136)
    density=np.fromfile(source/'density.u32',dtype='<u4').reshape(shape)/1048576
    audit=np.fromfile(source/'occupancy.rg32f',dtype='<f4').reshape((*shape,2))
    if not np.isfinite(audit).all():raise ValueError('Nonfinite captured field')
    after=.5-audit[...,0]
    original=upper_surface(density,(-11.15625,-11.15625,0),(22.3125,22.3125,8))
    filled=upper_surface(after,(-11.15625,-11.15625,0),(22.3125,22.3125,8))
    common=np.isfinite(original)&np.isfinite(filled)
    delta=filled[common]-original[common]
    # A core transition crosses half-way between solver centers, i.e. a
    # solver-cell face. Count proximity only, not proof of sole causation.
    on_face=lambda a: abs(a/(8/24)-np.rint(a/(8/24)))<1e-5
    surface=np.fromfile(source/'surface.rgba16f',dtype='<f2').reshape((*shape,4))
    rendered=upper_surface(.5-surface[...,0].astype(float),(-11.15625,-11.15625,0),(22.3125,22.3125,8))
    runtime=json.loads((source/'report.json').read_text())
    return dict(capture=str(directory),common_columns=int(common.sum()),
        floor_applied=runtime.get('solver_occupancy_floor_applied',True),
        rendered_solver_face_columns=int((np.isfinite(rendered)&on_face(rendered)).sum()),
        added_columns=int((~np.isfinite(original)&np.isfinite(filled)).sum()),
        raised_more_than_1cm=int((delta>.01).sum()),
        raised_more_than_10cm=int((delta>.1).sum()),
        height_raise_quantiles_m=np.quantile(delta,[0,.5,.9,.99,1]).tolist(),
        original_solver_face_columns=int((np.isfinite(original)&on_face(original)).sum()),
        filled_solver_face_columns=int((np.isfinite(filled)&on_face(filled)).sum()),
        physical_or_visual_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    args=p.parse_args();result=analyze(args.directory)
    with (args.directory/'occupancy_surface_attribution.json').open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
