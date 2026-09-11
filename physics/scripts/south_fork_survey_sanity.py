"""Fail-closed numerical screening for the small Troublemaker survey candidate.

These deliberately generous 10 m / 20 m/s bounds detect a failed solve; they
are not measured bathymetry, target wave sizes, or photorealism acceptance.
Never apply them indiscriminately to other rivers or deep-pool scenarios.
"""
import numpy as np


def check_frame(data, maximum_depth_m=10., maximum_speed_mps=20.):
    required=('h','eta','u','v','hu','hv')
    if any(key not in (data.dtype.names or ()) for key in required):
        raise ValueError('Survey frame is missing a conserved or primitive field')
    finite=bool(all(np.isfinite(data[key]).all() for key in required))
    minimum=float(np.min(data['h']))
    maximum=float(np.max(data['h']))
    speed=float(np.max(np.hypot(data['u'],data['v'])))
    passed=finite and minimum>=-1e-9 and maximum<=maximum_depth_m and speed<=maximum_speed_mps
    return {'finite':finite,'minimum_depth_m':minimum,'maximum_depth_m':maximum,
        'maximum_speed_mps':speed,'depth_bound_m':maximum_depth_m,
        'speed_bound_mps':maximum_speed_mps,'passed':bool(passed)}


def require_sane_frames(folder, manifest):
    if not manifest.get('frames'):
        raise ValueError('No hydraulic frames to screen')
    reports=[]
    for name in manifest['frames']:
        path=(folder/name).resolve()
        if not path.is_relative_to(folder.resolve()):
            raise ValueError('Frame is outside its solver output directory')
        report={'frame':name,**check_frame(np.genfromtxt(path,delimiter=',',names=True))}
        reports.append(report)
        if not report['passed']:
            raise ValueError(f'Unstable survey frame cannot be exported: {report}')
    return reports
