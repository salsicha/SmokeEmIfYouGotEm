"""Guard the full source-exact hydraulic handoff after completed terrain export.

No reduced interval, modified terrain, cook, scene update or acceptance claim.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from qualify_futaleufu_native_ports import ROOT, sha, resources


def validate_export(request, completion, manifest):
    chunks=manifest.get('chunks',[])
    scope=manifest.get('geographic_scope',{})
    layout=manifest.get('landscape',{})
    if (request.get('expected_chunks')!=4772 or request.get('route_length_m')!=55723.04503105954 or
        request.get('spacing_m')!=1. or request.get('buffer_m')!=600. or
        completion.get('inputs_unchanged') is not True or completion.get('chunks')!=4772 or
        completion.get('maximum_shared_edge_encoded_difference')!=0 or
        manifest.get('schema')!='raftsim.continuous_landscape.v1' or manifest.get('river_id')!='chilko_river_bc' or
        manifest.get('horizontal_crs')!='EPSG:3157' or manifest.get('vertical_reference')!='CGVD2013 (EPSG:6647)' or
        manifest.get('world_y_sign')!=-1 or manifest.get('horizontal_origin_m')!=[442000.,5749000.] or
        manifest.get('vertical_datum_m')!=900. or layout.get('spacing_m')!=1. or layout.get('vertices')!=127 or
        layout.get('span_m')!=126. or len(chunks)!=4772 or
        len({tuple(r['chunk']) for r in chunks})!=4772 or
        scope.get('route_interval_m')!=[0.,request['route_length_m']] or scope.get('buffer_m')!=600. or
        'chunk_window_inclusive' in scope or manifest.get('incomplete_source_chunks')!=[]):
        raise ValueError('Complete verified one-metre 55.7 km terrain export required')


def run(export_job, canonical, output, job):
    export_job,canonical,output,job=[Path(p).resolve() for p in (export_job,canonical,output,job)]
    for p in (export_job,canonical,output,job):p.relative_to(ROOT/'tmp')
    if output.exists() or job.exists():raise ValueError('Fresh input/output job required')
    completion_path=export_job/'completed.json';request_path=export_job/'request.json';manifest_path=canonical/'manifest.json'
    if (export_job/'failure.json').exists():raise ValueError('Preserve failed export; do not use partial terrain')
    request,completion,manifest=[json.loads(p.read_text()) for p in (request_path,completion_path,manifest_path)]
    validate_export(request,completion,manifest)
    if sha(manifest_path)!=completion['manifest_sha256']:raise ValueError('Terrain completion hash differs')
    pins={ROOT/p:h for p,h in request['inputs_sha256'].items()}
    for p in (completion_path,request_path,manifest_path,Path(__file__).resolve()):
        digest=sha(p)
        if p in pins and pins[p]!=digest:raise ValueError('Conflicting source pin')
        pins[p]=digest
    def verify():
        for p,h in pins.items():
            if sha(p)!=h:raise ValueError('Input source changed: '+str(p))
    verify()
    r=resources()
    if min(r['available_physical_bytes'],r['available_commit_bytes'])<8*1024**3 or r['free_disk_bytes']<43*1024**3:
        raise ValueError('Full-input resource reserve unavailable')
    script=ROOT/'physics/scripts/build_chilko_corridor_scenario.py'
    if script not in pins:raise ValueError('Hydraulic builder must belong to pinned export source set')
    command=[sys.executable,'-u',str(script),'--terrain',str(ROOT/'tmp/chilko-full-corridor-conditioned-terrain-v1'),
        '--profile',str(ROOT/'tmp/chilko-full-corridor-profile-v13-source-local-1m'),
        '--canonical',str(canonical),'--out',str(output)]
    job.mkdir(parents=True)
    def save(name,value):
        with (job/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)
    save('request.json',dict(command=command,full_route=True,initial_resources=r,
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},timeout_seconds=8*3600))
    minimum=r.copy();started=time.monotonic();failure=None
    with (job/'build.log').open('x') as log:
        child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        save('launch.json',dict(pid=child.pid));print('Full Chilko hydraulic-input builder PID '+str(child.pid),flush=True)
        while child.poll() is None:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                current=resources();minimum={k:min(minimum[k],current[k]) for k in current}
                if min(current['available_physical_bytes'],current['available_commit_bytes'])<3*1024**3:failure='Owned builder memory reserve reached'
                if current['free_disk_bytes']<40*1024**3:failure='Owned builder disk reserve reached'
                if time.monotonic()-started>8*3600:failure='Owned builder time bound reached'
                if failure:child.terminate();child.wait(timeout=30);break
    receipt=dict(exit_code=child.returncode,elapsed_seconds=time.monotonic()-started,minimum_resources=minimum)
    try:
        if failure or child.returncode:raise RuntimeError(failure or 'Native-input construction failed')
        verify()
        report=json.loads((output/'build_report.json').read_text())
        scenario=json.loads((output/'scenario/scenario.json').read_text())
        if (report.get('full_route_hydraulic_inputs') is not True or report.get('full_route_chart') is not True or
            report.get('complete_source_route_length_m')!=request['route_length_m'] or
            report.get('stations')!=25552 or report.get('lateral_cells')!=257 or
            report['continuous_terrain']['manifest_sha256']!=sha(manifest_path) or
            scenario['grid']['nx']!=25552 or scenario['grid']['ny']!=257):
            raise ValueError('Generated inputs do not cover the required full route')
        receipt.update(full_route_inputs=True,inputs_unchanged=True,
            files_sha256={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()},
            hydraulic_solution=False,engine_validated=False)
        save('completed.json',receipt);print('Complete source-exact Chilko hydraulic inputs prepared',flush=True)
    except Exception as exc:
        receipt['failure']=str(exc);save('failure.json',receipt);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('export-job','canonical','output','job'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.export_job,a.canonical,a.output,a.job)
