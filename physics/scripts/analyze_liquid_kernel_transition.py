"""Measure continuous sparse-kernel changes on actual captured particle positions."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from liquid_anisotropic_surface import fit_kernels,filter_kernels


def analyze(source,output):
    if output.exists():raise FileExistsError(output)
    raw=source.read_bytes();points=np.frombuffer(raw,dtype='<f4').reshape(-1,4)[:,:3].astype(float)
    started=time.perf_counter()
    old=filter_kernels(fit_kernels(points,.4,smoothing=0),1/6)
    new=filter_kernels(fit_kernels(points,.4,smoothing=0,smooth_sparse=True),1/6)
    change=np.max(abs(old['axes']-new['axes']),axis=1)
    confidence=new['sparse_confidence']
    result=dict(particle_count=len(points),positions_sha256=hashlib.sha256(raw).hexdigest(),
        raw_neighbor_count_quantiles=np.quantile(new['neighbor_counts'],[0,.25,.5,.75,.95,1]).tolist(),
        raw_count_20_to_30=int(((new['neighbor_counts']>=20)&(new['neighbor_counts']<=30)).sum()),
        continuous_transition_particles=int(((confidence>0)&(confidence<1)).sum()),
        purely_isotropic_particles=int((confidence==0).sum()),fully_anisotropic_particles=int((confidence==1).sum()),
        axis_change_cm_quantiles=np.quantile(change*100,[.5,.9,.95,.99,1]).tolist(),
        axes_changed_over_1cm=int((change>.01).sum()),axes_changed_over_5cm=int((change>.05).sum()),
        particle_positions_exact=np.array_equal(new['centers'],points) and np.array_equal(old['centers'],points),
        quadrature_weights_exact=np.array_equal(old['sample_volumes'],new['sample_volumes']),
        geometry_or_physical_volume_accepted=False,wall_seconds=time.perf_counter()-started)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();analyze(args.source,args.output)
