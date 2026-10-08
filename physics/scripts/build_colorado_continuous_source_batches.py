"""Acquire and compose bounded sequential full-river source batches, never gameplay.

Reuse the same captured survey and classified water; query actual terrain
coverage for each window. Failed/partial outputs are preserved, not overwritten.
"""
import argparse
import json
import math
from pathlib import Path
import shutil

from extract_colorado_bed_windows import sha


def plan_batches(index,start,stop=None,batch_size=12):
    if index.get('schema')!='raftsim.colorado_continuous_source_index.v1':
        raise ValueError('Registered continuous source index required')
    rows=index['windows'];length=index['route_length_m']
    if (not rows or not isinstance(length,(int,float)) or not math.isfinite(length) or length<=0 or
            type(start) is not int or type(batch_size) is not int or not 1<=batch_size<=12):
        raise ValueError('Invalid bounded source selection')
    stop=len(rows) if stop is None else stop
    if type(stop) is not int or not 0<=start<stop<=len(rows):
        raise ValueError('Selected source cores outside registered route')
    previous=0.
    for i,row in enumerate(rows):
        lo,hi=row['source_core_interval_m']
        if (row.get('tile_id')!=f'colorado_continuous_{i:04d}' or
                row.get('name')!=f'Colorado continuous {i:04d}' or
                not all(math.isfinite(v) for v in (lo,hi)) or lo!=previous or hi<=lo):
            raise ValueError('Source identity or continuous ordering changed')
        previous=hi
    if previous!=length:raise ValueError('Source index does not reach captured route endpoint')
    return [list(range(i,min(i+batch_size,stop))) for i in range(start,stop,batch_size)]


def run(windows,source_water,source_bed,previous_evidence,out,start,stop=None,batch_size=12,
        expected_index_sha256=None,min_free_gib=40):
    from fetch_colorado_terrain_windows import capture
    from blend_colorado_terrain_coverage import blend
    from extract_colorado_water_windows import extract as extract_water
    from extract_colorado_bed_windows import extract as extract_bed
    from build_colorado_catalog_evidence import build
    from review_colorado_continuous_bed_seam import review
    windows=Path(windows).resolve();out=Path(out).resolve()
    source_water=Path(source_water).resolve();source_bed=Path(source_bed).resolve()
    if out.exists():raise ValueError('Fresh job directory required; preserve partial evidence')
    index_path=windows/'index.json';index_sha=sha(index_path)
    if not expected_index_sha256 or index_sha!=expected_index_sha256:
        raise ValueError('Source index must match the explicitly registered hash')
    index=json.loads(index_path.read_text());batches=plan_batches(index,start,stop,batch_size)
    if not isinstance(min_free_gib,(int,float)) or not math.isfinite(min_free_gib) or min_free_gib<40:
        raise ValueError('At least 40 GiB disk headroom required')
    previous=Path(previous_evidence).resolve() if previous_evidence else None
    if start>0:
        if previous is None:raise ValueError('Previous adjacent evidence required for first handoff')
        pm=json.loads((previous/'manifest.json').read_text())
        if pm.get('name')!=index['windows'][start-1]['name']:
            raise ValueError('Previous evidence is not the adjacent source core')
    for ids in batches:
        for i in ids:
            row=index['windows'][i];p=json.loads((windows/(row['tile_id']+'.json')).read_text())
            if any(p.get(key)!=row.get(key) for key in ('name','tile_id','source_core_interval_m','source_halo_interval_m')):
                raise ValueError('Window file disagrees with registered index')
    def disk_check():
        if shutil.disk_usage(out.parent).free<min_free_gib*1024**3:
            raise ValueError('Source job stopped to preserve disk headroom; no sources deleted')
    disk_check();out.mkdir(parents=True)
    launch=dict(index_sha256=index_sha,source_water_manifest_sha256=sha(source_water/'manifest.json'),
                source_pool_raster_sha256=sha(source_bed),start=start,stop=batches[-1][-1]+1,
                batch_size=batch_size,min_free_gib=min_free_gib,previous_evidence=str(previous),
                scope='Source construction only; no hydraulic, engine, rapid-location or performance acceptance')
    with (out/'launch.json').open('x') as f:json.dump(launch,f,indent=2)
    completed=[];stage='starting';batch=None
    try:
        for ids in batches:
            disk_check()
            if sha(index_path)!=index_sha:raise ValueError('Registered source index changed')
            batch=out/f'batch{ids[0]:04d}-{ids[-1]:04d}';batch.mkdir()
            names=[index['windows'][i]['name'] for i in ids]
            coarse=batch/'terrain10m';fine=batch/'terrain1m';mixed=batch/'terrain_mixed'
            water=batch/'water';bed=batch/'bed';evidence=batch/'evidence';seams=batch/'seams'
            print(f'START {batch.name}: source cores only, not playable coverage',flush=True)
            stage='coarse_terrain';capture(windows,coarse,names,'3dep',10)
            disk_check();stage='fine_terrain';capture(windows,fine,names,'3dep',1,True,True)
            stage='terrain_blend';blend(fine,coarse,mixed)
            stage='classified_water';extract_water(source_water,windows,water,names,400)
            stage='measured_pool_bed';extract_bed(source_bed,windows,bed,names,400,True)
            evidence.mkdir();seams.mkdir();results=[]
            for i in ids:
                disk_check();stage=f'compose_{i:04d}'
                p=windows/(index['windows'][i]['tile_id']+'.json');dest=evidence/f'tile{i:04d}'
                result=build(p,water,bed,mixed,dest,1.)
                seam=None
                if previous is not None:
                    a=index['windows'][i-1];b=index['windows'][i]
                    stage=f'seam_{i:04d}'
                    seam=review(previous,dest,a['source_halo_interval_m'][0],b['source_halo_interval_m'][0],
                                b['source_core_interval_m'][0],seams/f'seam{i:04d}.json')
                    if not seam['bed_screen_passed']:raise ValueError('Construction wet-bed/reference handoff failed')
                results.append(dict(core=i,evidence_manifest_sha256=sha(dest/'manifest.json'),
                                    statistics=result['statistics'],bed_handoff_passed=bool(seam and seam['bed_screen_passed'])))
                previous=dest
            with (batch/'completed.json').open('x') as f:
                json.dump(dict(results=results,hydraulic_accepted=False,engine_accepted=False),f,indent=2)
            completed.append(batch.name)
            print(f'COMPLETED {batch.name}: {len(ids)} source cores, no runtime promotion',flush=True)
        stage='terminal_source_identity'
        if (sha(index_path)!=index_sha or sha(source_water/'manifest.json')!=launch['source_water_manifest_sha256'] or
                sha(source_bed)!=launch['source_pool_raster_sha256']):
            raise ValueError('Captured source identity changed during job')
        with (out/'completed.json').open('x') as f:
            json.dump(dict(completed_batches=completed,source_end_m=index['windows'][batches[-1][-1]]['source_core_interval_m'][1],
                           source_only=True,full_river_playable=False),f,indent=2)
    except Exception as error:
        with (out/'failure.json').open('x') as f:
            json.dump(dict(batch=str(batch),stage=stage,error=str(error),completed_batches=completed,
                           partial_evidence_preserved=True),f,indent=2)
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('windows','source-water','source-bed','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--previous-evidence',type=Path)
    p.add_argument('--start',type=int,required=True);p.add_argument('--stop',type=int)
    p.add_argument('--batch-size',type=int,default=12)
    p.add_argument('--expected-index-sha256',required=True)
    a=p.parse_args();run(a.windows,a.source_water,a.source_bed,a.previous_evidence,a.out,a.start,a.stop,
                         a.batch_size,a.expected_index_sha256)
