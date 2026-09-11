"""Preserve an actual renderer SDF for an identical-particle geometry A/B."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def geometry_only_volume(rgba):
    if rgba.ndim != 4 or rgba.shape[-1] != 4 or not np.isfinite(rgba).all():
        raise ValueError('Finite ZYXC renderer readback required')
    output = np.zeros_like(rgba)
    output[...,0] = rgba[...,0]
    return output


def run(grids,particles,output):
    if output.exists():
        raise FileExistsError(output)
    if grids.resolve() != (particles.parent/(particles.stem.removesuffix('_particles')+'_grids')).resolve():
        raise ValueError('Particle and renderer captures must be paired artifacts')
    data = json.loads((grids/'grids.json').read_text())
    volumes = data['render_target_volumes']
    if len(volumes)!=1 or volumes[0]['pixel_format']!=10 or volumes[0]['size']!=[136,136,48] or not volumes[0]['readback_saved']:
        raise ValueError('One complete native RGBA16f render-volume capture required')
    file = grids/volumes[0]['file']
    rgba = np.fromfile(file,dtype='<f2').reshape(48,136,136,4)
    result = geometry_only_volume(rgba)
    if result[...,0].min()>=0 or result[...,0].max()<=0:
        raise ValueError('Captured field must contain liquid and air')
    output.mkdir(parents=True)
    result.tofile(output/'surface.rgba16f')
    report = dict(source=str(file.resolve()),source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                  particle_capture_sha256=hashlib.sha256(particles.read_bytes()).hexdigest(),
                  grid_cells=[136,136,48],minimum_m=[-11.15625,-11.15625,0],extent_m=[22.3125,22.3125,8],
                  finite=True,red_channel_bitwise_unchanged=bool(np.array_equal(rgba[...,0].view('u2'),result[...,0].view('u2'))),
                  renderer_texture='surface.rgba16f',texture_sha256=hashlib.sha256((output/'surface.rgba16f').read_bytes()).hexdigest(),
                  distance_reference='captured renderer SDF, unchanged red channel',
                  foam_channel_zero=True,physical_or_visual_acceptance=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grids',type=Path)
    parser.add_argument('--particles',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    run(args.grids,args.particles,args.output)
