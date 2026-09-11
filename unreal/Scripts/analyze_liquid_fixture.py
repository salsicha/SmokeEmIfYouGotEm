"""Measure real fixture pixels and one GPU profile; never score river realism."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from PIL import Image


def difference(a, b):
    values = np.abs(a-b)
    return {'mean_absolute_rgb_8bit': float(values.mean()),
            'max_absolute_rgb_8bit': int(values.max()),
            'pixels_with_channel_difference_over_8': int((values.max(axis=2)>8).sum())}


def analyze(directory, log_path):
    capture = json.loads((directory/'capture.json').read_text())
    if not capture.get('complete') or not capture.get('activation_confirmed'):
        raise ValueError('Capture did not complete with confirmed activation')
    frames = [c for c in capture['captures'] if Path(c['image']).stem in
              ('liquid_0240','liquid_0300','liquid_0360')]
    if len(frames)!=3 or any(c['camera_cm']!=frames[0]['camera_cm'] for c in frames):
        raise ValueError('Expected three same-camera post-warm-up frames')
    images = [np.asarray(Image.open(c['image']).convert('RGB'),dtype=np.int16) for c in frames]
    hidden = np.asarray(Image.open(directory/'water_hidden.png').convert('RGB'),dtype=np.int16)
    if any(im.shape!=hidden.shape for im in images):
        raise ValueError('Capture dimensions differ')
    log = log_path.read_text(encoding='utf-8',errors='replace')
    rows = []
    for line in log.splitlines():
        if 'LogRHI:' not in line or '┃' not in line:
            continue
        times = re.findall(r'([0-9.]+) ms',line)
        if len(times)!=2:
            continue
        event = line.split('┃')[-2].strip()
        if 'NiagaraGpuComputeDispatch' in event or 'NiagaraGpuSim(' in event:
            rows.append({'event':event,'exclusive_ms':float(times[0]),'inclusive_ms':float(times[1])})
    compute = [r for r in rows if r['event']=='NiagaraGpuComputeDispatch' and r['inclusive_ms']>.01]
    pressure = [r for r in rows if 'Stage(Solve Pressure' in r['event']]
    raster = [r for r in rows if 'Stage(Fill Rasterization Grid' in r['event']]
    result = {
        'scope':'Isolated diagnostic pixels and single profiled frame, not river or release acceptance',
        'capture':str(directory/'capture.json'), 'log':str(log_path),
        'same_camera_motion':[difference(images[0],images[1]),difference(images[1],images[2])],
        'water_hidden_difference':difference(images[2],hidden),
        'recorded_niagara_ages': [float(v) for v in re.findall(r'LiquidFixture actual_age=([0-9.]+)',log)],
        'gpu_compute_observed_in_profiled_frame':bool(compute),
        'niagara_compute_scopes':compute,
        'pressure_iteration_dispatch_rows':len(pressure),
        'surface_rasterization_scopes':raster,
        'graphics_frame_ms':[float(v) for v in re.findall(r'Frame Time\s+:\s*([0-9.]+)ms',log)],
        'profile_scope':'Whole editor frame includes viewport and scene capture; not incremental river cost',
        'rendered_water_is_photorealistic':False, 'river_coupling_verified':False,
        'continuous_animation_accepted':False, 'production_promoted':False}
    (directory/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('log',type=Path)
    arguments=parser.parse_args()
    print(json.dumps(analyze(arguments.directory,arguments.log),indent=2))
