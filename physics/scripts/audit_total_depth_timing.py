"""Compare warmed, paired native GPU intervals; never a scene FPS qualification.

These timestamps enclose boundary sampling, both RK2 stages, breaking, pressure,
acceptance and ledger work. They exclude uploads/readbacks and ordinary rendering.
The second graph is inactive in this two-step fixture and is reported separately.
"""
import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path

ROW=re.compile(r'GPU temporal evolution sample(\d+) graph(\d+) slots(\d+) cull([01]) ([0-9.]+) ms')


def summarize(text):
    if ('four alternating warm-up intervals, then eight paired samples with alternating order' not in text
        or 'Test Completed. Result={Success} Name={TemporalEvolutionGPU}' not in text
        or '**** TEST COMPLETE. EXIT CODE: 0 ****' not in text
        or 'temporal evolution trials2 accepted2 status1 mode1 bits0/0/0/1' not in text):
        raise ValueError('Complete successful warmed two-step timing run required')
    rows={}
    for sample,graph,slots,cull,milliseconds in ROW.findall(text):
        key=(int(sample),int(graph),int(cull));value=float(milliseconds)
        if key in rows or slots!='2' or not value>0:
            raise ValueError('Duplicate, invalid or differently partitioned timing sample')
        rows[key]=value
    expected={(s,g,c) for s in range(8) for g in range(2) for c in range(2)}
    if set(rows)!=expected:raise ValueError('All32 paired timestamp records required')
    def stats(values):
        return dict(samples=values,mean_ms=statistics.mean(values),median_ms=statistics.median(values),
                    p95_ms_nearest_rank=max(values),minimum_ms=min(values),maximum_ms=max(values))
    result={}
    for cull in range(2):
        active=[rows[s,0,cull] for s in range(8)];inactive=[rows[s,1,cull] for s in range(8)]
        result['indirect' if cull else 'direct']=dict(active_two_steps=stats(active),inactive_two_slots=stats(inactive),
            full_interval=stats([a+b for a,b in zip(active,inactive)]),
            active_graph_mean_per_accepted_step_ms=statistics.mean(active)/2)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs',nargs='+',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    runs=[]
    for path in args.logs:
        raw=path.read_bytes();native=path.with_suffix('')/'index.json';report_bytes=native.read_bytes();report=json.loads(report_bytes)
        if (report['succeeded']!=1 or any(report[k] for k in ('failed','succeededWithWarnings','notRun','inProcess'))
            or len(report['tests'])!=1 or report['tests'][0]['fullTestPath']!='RaftSim.WaterDetail.TemporalEvolutionGPU'):
            raise ValueError('Clean single-test native report required')
        command=re.search(r'LogInit: Command Line: (.*)',raw.decode('utf-8',errors='replace'))
        fixture=re.search(r'-RaftSimTemporalEvolutionFixture=("[^"]+"|\S+)',command[1] if command else '')
        if not fixture:raise ValueError('Recorded temporal input fixture required')
        fixture_path=Path(fixture[1].strip('"'));fixture_bytes=fixture_path.read_bytes()
        runs.append(dict(log=str(path.resolve()),log_sha256=hashlib.sha256(raw).hexdigest(),
            native_report=str(native.resolve()),native_report_sha256=hashlib.sha256(report_bytes).hexdigest(),
            fixture=str(fixture_path.resolve()),fixture_sha256=hashlib.sha256(fixture_bytes).hexdigest(),
            devices=report['devices'],measurements=summarize(raw.decode('utf-8',errors='replace'))))
    if len({r['fixture_sha256'] for r in runs})!=1:raise ValueError('Timing comparison changed fixture')
    result=dict(schema='raftsim.total_depth_warm_timing.v1',scope=__doc__,scene_accepted=False,
        performance_qualified=False,implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runs=runs)
    if len(runs)==2:
        before,after=[r['measurements']['indirect']['active_two_steps']['mean_ms'] for r in runs]
        result['indirect_active_mean_reduction_fraction']=1-after/before
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
