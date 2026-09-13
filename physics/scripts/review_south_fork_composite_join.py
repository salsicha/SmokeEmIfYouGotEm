"""Screen the enlarged join solve with unchanged South Fork settling gates."""
import argparse
import json
from pathlib import Path
import numpy as np
from south_fork_survey_sanity import check_frame

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    run = json.loads((work/'run_result.json').read_text())
    folder = ROOT/run['output_dir']
    frames = json.loads((folder/'manifest.json').read_text())['frames']
    registration = json.loads((work/'registration.json').read_text())
    scenario = json.loads(next((work/'scenario').glob('*/scenario.json')).read_text())
    nx, ny = scenario['grid']['nx'], scenario['grid']['ny']
    cell = scenario['grid']['dx']
    target = registration['target_discharge_m3s']
    steps = int(run['command'][run['command'].index('--steps')+1])
    interval = int(run['command'][run['command'].index('--frame-interval')+1])
    assert len(frames) == steps//interval+1
    snapshots = []
    for index, name in enumerate(frames):
        data = np.genfromtxt(folder/name, delimiter=',', names=True)
        sanity = check_frame(data)
        h, u, eta, x, y = [data[k].reshape(ny, nx) for k in ('h', 'u', 'eta', 'x', 'y')]
        stations = [-220, -190, -150, -50, 0, 50, 150, 190, 220]
        columns = [int(np.argmin(abs(x[0]-s))) for s in stations]
        crux = (abs(x)<25) & (abs(y)<30) & (h>.1)
        snapshots.append(dict(seconds=min(index*interval, steps)*scenario['fixed_dt'], sanity=sanity,
            volume_m3=float(h.sum()*cell*cell), section_stations_m=stations,
            section_discharge_m3s=[float((h[:, c]*u[:, c]).sum()*cell) for c in columns],
            crux_stage_median_navd88_m=float(np.median(eta[crux])+registration['vertical_origin_navd88_m'])))
        print(f'Screened frame {index+1}/{len(frames)}: sane={sanity["passed"]}', flush=True)
    tail = snapshots[-4:]
    storage = [(b['volume_m3']-a['volume_m3'])/(b['seconds']-a['seconds']) for a, b in zip(tail[:-1], tail[1:])]
    relative_error = max(abs(q-target)/target for row in tail for q in row['section_discharge_m3s'])
    checks = dict(all_frames_sane=all(row['sanity']['passed'] for row in snapshots),
        section_flux_within_5_percent_of_target=relative_error <= .05,
        storage_within_2_percent_of_target=max(map(abs, storage)) <= .02*target,
        regional_stage_change_below_1cm=np.ptp([row['crux_stage_median_navd88_m'] for row in tail]) <= .01)
    report = dict(status='numerical_screen_not_visual_or_full_river_acceptance',
        geometry_sha256=registration['geometry_sha256'], source_bed_sampling=registration['bed_sampling'],
        target_discharge_m3s=target, snapshots=snapshots, last_intervals_storage_m3s=storage,
        maximum_tail_section_relative_error=relative_error, checks={k: bool(v) for k, v in checks.items()},
        mean_flow_screen_passed=bool(all(checks.values())), actual_numerical_boundary_flux_audited=False,
        measured_bathymetry=False, normal_map_integrated=False, full_reconstruction_accepted=False)
    (work/'flow_review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'snapshots'}, indent=2))


if __name__ == '__main__':
    main()
