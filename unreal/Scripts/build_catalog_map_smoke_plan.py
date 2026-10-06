"""Exercise a new catalog map with the normal native raft driver.

This is integration coverage only: no implied correct line or class acceptance.
"""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def build(contract,start,finish):
    if not contract['launch']['station_m']<=start<finish<=contract['finish_station_m']:
        raise ValueError('Smoke trial outside construction descent')
    source=contract['cooked_fields'].rsplit('/',1)[0]+'/manifest.json'
    return [dict(river=contract['section_id'],map=contract['map_package'],
        scenario=contract['section_id'],source=source,seconds_per_trial=600,
        capture_gate_frames=True,
        calibration_scope='Construction integration only; not a difficulty or route-width comparison.',
        trials=[dict(id=contract['section_id']+'--integration',rapid_id=contract['section_id'],
            name=contract['display_name'],catalog_class='construction test; not graded',
            variant='integration',start_m=start,finish_m=finish,control_m=(start+finish)/2,
            strict_route=True,normal_rescue_inputs=False,lane_m=0,lookahead_m=45,
            route_laterals=[[start,0],[finish,0]],
            input_interval_s=.85,wall_limit_s=1200,
            gates=[dict(id='construction_midpoint',station_m=(start+finish)/2),
                   dict(id='construction_exit',station_m=finish-2)])])]


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--start',type=float,required=True)
    p.add_argument('--finish',type=float,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise SystemExit('Fresh plan path required')
    a.out.write_text(json.dumps(build(json.loads(a.contract.read_text()),a.start,a.finish),indent=2)+'\n')
