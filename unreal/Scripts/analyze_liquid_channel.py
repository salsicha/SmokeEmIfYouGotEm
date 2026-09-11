"""Check GPU channel lifecycle evidence, not photorealism or calibrated flow."""
import argparse
import json
from pathlib import Path
import re


def check_capture(directory):
    capture = json.loads((directory / 'capture.json').read_text())
    assert capture['complete'] and capture['stop_inlet_after_seconds'] == 4
    assert capture['blocking_particle_readback']
    samples = []
    for frame in (240, 300, 360):
        sample = json.loads((directory / f'liquid_{frame:04d}_particles.json').read_text())
        fluid = next(e for e in sample['emitters'] if 'FluidControl' in e['emitter'])
        assert fluid['position_count'] == fluid['velocity_count'] > 0
        assert fluid['nonfinite_positions'] == fluid['nonfinite_velocities'] == 0
        assert fluid['inside_obstacle_core60cm'] == 0
        assert fluid['below_fixture_floor_count'] == 0
        assert fluid['outside_fixture_domain_count'] == fluid['beyond_fixture_outlet_count']
        assert fluid['flow_regions_exclude_outside_fixture_domain']
        maximum = [float(v) for v in re.findall(r'[XYZ]=([-+\d.]+)', fluid['bounds_max_cm'])]
        minimum = [float(v) for v in re.findall(r'[XYZ]=([-+\d.]+)', fluid['bounds_min_cm'])]
        assert len(maximum) == len(minimum) == 3
        # Update retirement precedes FLIP particle integration. One final
        # timestep can cross the outlet; it must stay within one grid cell,
        # not accumulate into the previous 134 m off-grid falling plume.
        cell_cm = 500 / 64
        assert maximum[0] <= 200 + cell_cm
        assert minimum[0] >= -200 and minimum[1] >= -200 and minimum[2] >= 0
        assert maximum[1] <= 200 and maximum[2] <= 500
        downstream = fluid['flow_regions'][2]
        assert downstream['count'] > 0
        assert downstream['mean_velocity_x_cm_per_s'] > 0
        samples.append({'seconds': frame / 60,
                        'live_particles': fluid['position_count'],
                        'outlet_pending_retirement': fluid['beyond_fixture_outlet_count'],
                        'outlet_overshoot_cm': max(0, maximum[0] - 200),
                        'in_domain_downstream_mean_vx_cm_per_s': downstream['mean_velocity_x_cm_per_s']})
    counts = [s['live_particles'] for s in samples]
    assert counts[0] > counts[1] > counts[2], 'Stopped inlet must drain, not retain escaped particles'
    return {'scope': 'Fixed-domain GPU particle lifecycle, not river realism or volumetric discharge',
            'passed': True, 'samples': samples,
            'particle_count_reduction_after_two_seconds': 1 - counts[-1] / counts[0],
            'production_acceptance': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('capture_directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = check_capture(args.capture_directory)
    # Never replace earlier evidence, including a failed run.
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))
