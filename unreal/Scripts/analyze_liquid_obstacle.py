"""Compare actual GPU particle readbacks, not screenshot occlusion.

This tests an analytic sphere in the isolated liquid tank. It does not validate
surveyed terrain, collision-free rendering, river boundaries or raft support.
"""
import argparse
import json
from pathlib import Path


def analyze(enabled, control):
    enabled, control = Path(enabled), Path(control)
    reports = [json.loads((directory/'capture.json').read_text())
               for directory in (enabled, control)]
    for capture in reports:
        assert capture['complete'] and capture['blocking_particle_readback']
        assert capture['obstacle']['centre_cm'] == [0, 0, 100]
        assert capture['obstacle']['radius_cm'] == 80
    assert reports[0]['collision_variant'] and not reports[1]['collision_variant']
    assert reports[0]['obstacle'] == reports[1]['obstacle']
    rows = []
    for frame in (240, 300, 360):
        pair = []
        for directory in (enabled, control):
            report = json.loads((directory/f'liquid_{frame:04d}_particles.json').read_text())
            assert report['blocking_gpu_readback']
            assert report['obstacle_centre_cm'] == 'X=0 Y=0 Z=100'
            emitter = next(e for e in report['emitters']
                           if e['emitter'] == 'Grid3D_FLIP_FluidControl_Emitter')
            assert emitter['position_count'] > 1000, 'Empty or trivial fluid cannot pass'
            assert emitter['position_count'] == emitter['velocity_count']
            assert emitter['nonfinite_positions'] == 0
            pair.append(emitter)
        on, off = pair
        rows.append({'age_seconds': frame/60, 'collision_enabled': on,
                     'collision_disabled': off,
                     'core_excluded': on['inside_obstacle_core60cm'] == 0,
                     'control_exercises_core': off['inside_obstacle_core60cm'] >= 1000,
                     'maximum_sampled_penetration_cm': max(
                         0, 80-on['minimum_obstacle_centre_distance_cm'])})
    # A coarse 500/64 cm cell cannot claim exact surface exclusion. Report both
    # the empty inner core and measured shallow penetration rather than hide it.
    return {'scope': 'Three sampled instants, analytic sphere only',
            'rows': rows,
            'all_sampled_cores_excluded': all(r['core_excluded'] for r in rows),
            'control_exercises_all_sampled_cores': all(r['control_exercises_core'] for r in rows),
            'collision_surface_tolerance_cm': 500/64,
            'within_one_cell_at_sampled_instants': all(
                r['maximum_sampled_penetration_cm'] <= 500/64 for r in rows),
            'exact_surface_exclusion_verified': False,
            'river_coupling_verified': False,
            'production_promoted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('enabled')
    parser.add_argument('control')
    parser.add_argument('output')
    args = parser.parse_args()
    result = analyze(args.enabled, args.control)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    assert result['all_sampled_cores_excluded']
    assert result['control_exercises_all_sampled_cores']
    assert result['within_one_cell_at_sampled_instants']
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}, indent=2))
