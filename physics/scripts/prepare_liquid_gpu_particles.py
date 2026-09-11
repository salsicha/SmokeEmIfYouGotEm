"""Prepare captured positions and existing CPU density reference for GPU parity."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def prepare(reference,output):
    if output.exists():
        raise FileExistsError(output)
    metadata=json.loads((reference.parent/'report.json').read_text())
    source=Path(metadata['source'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=metadata['source_sha256']:
        raise ValueError('Original particle capture identity changed')
    if metadata['center_smoothing']!=0 or metadata['weighting']!='equal_mass_over_local_density':
        raise ValueError('GPU implementation requires unshifted density-normalized reference')
    with np.load(reference) as data:
        points=data['centers']
        minimum,extent,cells=[data[k] for k in ('minimum','extent','cells')]
    positions=np.zeros((len(points),4),dtype='<f4')
    positions[:,:3]=points
    output.mkdir(parents=True)
    positions.tofile(output/'positions.rgba32f')
    report=dict(reference=str(reference.resolve()),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                particle_capture_sha256=metadata['source_sha256'],count=len(points),
                minimum_m=minimum.tolist(),extent_m=extent.tolist(),grid_cells=cells.tolist(),
                radius_m=metadata['kernel_radius_m'],footprint_m=metadata['moment_matched_footprint_m'],
                positions_sha256=hashlib.sha256(positions.tobytes()).hexdigest(),live_input=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    prepare(args.reference,args.output)
