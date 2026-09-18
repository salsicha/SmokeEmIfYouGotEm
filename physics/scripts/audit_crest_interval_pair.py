"""Strict paired adaptive-crest interval timings, never FPS acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median


def summarize(report):
    rows=report.get('pairs')
    if (report.get('schema')!='raftsim.crest_interval_pair.v1' or type(report.get('exact')) is not bool
            or not isinstance(rows,list) or len(rows)!=64):
        raise ValueError('Complete original 64-pair crest-interval report required')
    for i,row in enumerate(rows):
        if (type(row.get('pair')) is not int or row['pair']!=i or type(row.get('candidate_first')) is not bool
                or row['candidate_first']!=bool(i%2) or type(row.get('exact')) is not bool):
            raise ValueError('Numbered alternating pairs and explicit equality required')
        for key in ('frame','vertices','triangles'):
            v=row.get(key)
            if type(v) not in (int,float) or not math.isfinite(v) or v<=0 or int(v)!=v:
                raise ValueError('Positive finite integral counts required')
        if row['frame']<120 or (i and row['frame']<rows[i-1]['frame']):
            raise ValueError('Original post-warmup frame order required')
        for key in ('reference_ms','candidate_ms'):
            v=row.get(key)
            if type(v) not in (int,float) or not math.isfinite(v) or v<=0:
                raise ValueError('Positive finite measured timings required')
    if rows[0]['frame']==rows[-1]['frame']:raise ValueError('Live multi-frame evidence required')
    groups={}
    for name,group in (('all',rows),('reference_first',rows[::2]),('candidate_first',rows[1::2])):
        groups[name]=dict(pairs=len(group),reference_mean_ms=mean(r['reference_ms'] for r in group),
            candidate_mean_ms=mean(r['candidate_ms'] for r in group),
            reference_median_ms=median(r['reference_ms'] for r in group),
            candidate_median_ms=median(r['candidate_ms'] for r in group),
            candidate_faster_pairs=sum(r['candidate_ms']<r['reference_ms'] for r in group))
    return dict(exact_topology_and_production=report['exact'] and all(r['exact'] for r in rows),
        measured_both_orders_faster=all(g['candidate_mean_ms']<g['reference_mean_ms'] for g in groups.values()),
        first_frame=rows[0]['frame'],last_frame=rows[-1]['frame'],groups=groups,release_accepted=False,
        scope='Whole adaptive build on current paired inputs with the same prepared sites. Exact ordered parents, triangles, ownership, expanded coordinates and production topology. Not FPS, physical or visual acceptance.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path);parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args();payload=args.capture.read_bytes();result=summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()),sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(result))
    return 0 if result['exact_topology_and_production'] and result['measured_both_orders_faster'] else 1


if __name__=='__main__':raise SystemExit(main())
