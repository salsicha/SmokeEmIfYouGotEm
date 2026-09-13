"""Exercise native scenario-package parsing of explicit two-layer boundaries."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'tmp/south-fork-cartesian-profile-parser-v3-20260912'


def main():
    assert not OUT.exists(), 'Retain earlier parser evidence'
    OUT.mkdir()
    template = ROOT/'physics/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario/scenario.json'
    manifest = json.loads(template.read_text())
    ny,nx = manifest['grid']['ny'],manifest['grid']['nx']
    zeros, depth = np.zeros((ny,nx)), np.full((ny,nx),2.)
    u,v = np.full((ny,nx),.3),np.full((ny,nx),.5)
    np.save(OUT/'bed.npy',zeros)
    np.savez_compressed(OUT/'initial_state.npz',depth=depth,eta=depth,u=u,v=v,hu=depth*u,hv=depth*v,wet=np.ones((ny,nx),dtype=bool))
    (OUT/'features.json').write_text(json.dumps({'features':[]}))
    (OUT/'probes.json').write_text(json.dumps({'probes':[]}))
    manifest['metadata']['scenario_id']='cartesian_four_edge_profile_parser'
    manifest['metadata']['fixture_kind']=None
    manifest['fixed_dt']=.005
    manifest['duration']=.1
    manifest['roughness']=0.
    manifest['boundaries']=[dict(edge=edge,kind='ghost',ghost_cells=[[0.,2.,.3,.5]]*(2*(ny if edge in ['west','east'] else nx)))
                            for edge in ['west','east','south','north']]
    (OUT/'scenario.json').write_text(json.dumps(manifest,indent=2)+'\n')
    binary=ROOT/'tmp/troublemaker-row-solver-cartesian-v1-20260912/raftsim_water_solver.exe'
    command=[str(binary),'--scenario',str(OUT),'--output',str(OUT/'result'),'--steps','20','--frame-interval','10',
             '--solver-mode','finite_volume','--spatial-order','2','--boundary-mode','scenario','--flux-scheme','hll',
             '--cfl','.2','--feature-strength-scale','0','--roughness-scale','1','--bed-slope-source-scale','1',
             '--no-preserve-initial-mass','--disable-fixture-calibrations']
    run=subprocess.run(command,text=True,capture_output=True)
    (OUT/'stdout.txt').write_text(run.stdout)
    (OUT/'stderr.txt').write_text(run.stderr)
    assert run.returncode==0,run.stderr
    frames=sorted((OUT/'result/cartesian_four_edge_profile_parser/frames').glob('*.csv'))
    assert len(frames)==3
    errors={}
    for path in frames:
        with path.open() as stream:
            rows=list(csv.DictReader(stream))
        assert len(rows)==nx*ny
        for name,value in [('h',2.),('u',.3),('v',.5)]:
            errors[name]=max(errors.get(name,0.),max(abs(float(row[name])-value) for row in rows))
    assert max(errors.values())<1.e-12,errors
    report=dict(native_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                scenario_sha256=hashlib.sha256((OUT/'scenario.json').read_bytes()).hexdigest(),
                native_exit_code=run.returncode,frames_checked=len(frames),maximum_errors=errors,
                passed=True,full_river_flow_accepted=False,normal_map_integrated=False)
    (OUT/'parser_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
