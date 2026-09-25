"""Hash-bound native zero-step outlet-stage sensitivity; never boundary calibration."""
import argparse
import json
from pathlib import Path
import subprocess
from audit_cartesian_cook_snapshot import digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('frame',type=Path)
    p.add_argument('solver',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args();assert not a.report.exists()
    manifest=json.loads(a.manifest.read_text())
    assert digest(a.manifest)==digest(a.frame.parent/'input_manifest.json')
    hashes={str(a.manifest):digest(a.manifest),str(a.solver):digest(a.solver)}
    for row in manifest['inputs']:
        for filename,expected in row['files'].items():
            path=a.manifest.parent/row['name']/filename
            assert digest(path)==expected
            hashes[str(path)]=expected
    for name in ('complete.json','h.npy','u.npy','v.npy'):
        path=a.frame/name;hashes[str(path)]=digest(path)
    complete=json.loads((a.frame/'complete.json').read_text())
    downstream=[(i,r) for i,r in enumerate(manifest['boundary_probes']) if r['role']=='downstream']
    assert downstream and all(r['edge']=='west' for _,r in downstream)
    runs=[]
    for offset in (0.,-.01,.01):
        command=[str(a.solver.resolve()),str(a.manifest.resolve()),str(a.frame.resolve()),
            *[str(r['tile_index']) for _,r in downstream],f'--outlet-stage-offset-m={offset}']
        native=json.loads(subprocess.run(command,check=True,capture_output=True,text=True).stdout)
        assert native['state_unchanged'] and native['solver_steps_run']==0
        assert native['boundary_sensitivity'] and native['outlet_stage_offset_m']==offset
        assert native['altered_in_memory_boundaries']==len(downstream)
        tiles={r['tile_index']:r for r in native['tiles']}
        flux=[tiles[r['tile_index']]['inward_flux_m3s'][0] for _,r in downstream]
        if offset==0.:
            assert all(abs(f-complete['exterior_fluxes'][i])<1e-8 for f,(i,_) in zip(flux,downstream))
        runs.append(dict(offset_m=offset,outlet_outflow_m3s=-sum(flux),native=native))
    for path,expected in hashes.items():assert digest(Path(path))==expected
    result=dict(dependencies=hashes,runs=runs,time_seconds=complete['time_seconds'],
        centered_outflow_derivative_m2s=(runs[2]['outlet_outflow_m3s']-runs[1]['outlet_outflow_m3s'])/.02,
        scope='Instantaneous fixed-state sensitivity, not evolved flow or calibrated stage',
        solver_steps=0,files_unchanged=True,playable_integrated=False,settling_accepted=False)
    a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('dependencies','runs')}))
    print([(r['offset_m'],r['outlet_outflow_m3s']) for r in runs])


if __name__=='__main__':main()
