"""Exercise the candidate inlet selector using every actual native spawn count."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_stage_journal import stage_groups
from liquid_dataset import resolve
from liquid_stratified_source import select_sites,cumulative_weights


def audit(capture):
    capture=capture.resolve();native=json.loads((capture/'stages.json').read_text());dataset=resolve(native)
    observed=[g for g in stage_groups(native) if g['entries'][0]['first']]
    steps=observed[:native['native_transfer_packet_step']]
    if len(steps)!=native['native_transfer_packet_step']:raise ValueError('Missing captured native spawn steps')
    if any([e['owner'] for e in g['entries']]!=list(range(12)) for g in steps):raise ValueError('Complete native owner groups required')
    result=[]
    for owner in range(12):
        path=dataset['regions']/f'region-{owner:03d}.json';region=json.loads(path.read_text())
        w=np.array(region['source_weights_m3_per_s']);counts=[]
        for step,g in enumerate(steps):
            e=g['entries'][owner]
            if step==0:continue # Immutable initial-volume burst is NOT a source sample.
            counts.append(e['native_rate_spawns']+e['native_event_spawns'])
        if not len(w):
            if any(counts):raise ValueError('Native births exist on an owner without sources')
            continue
        unique=sorted(set(counts));duplicate_max=0;discrepancy=0.;float_duplicates=0;tested=0
        cdf32=cumulative_weights(w).astype('<f4')
        collapsed=int(((w>0)&(np.diff(np.r_[np.float32(0),cdf32])==0)).sum())
        for count in unique:
            for k in range(256):
                u=(k+.5)/256;chosen,r=select_sites(w,int(count),u);tested+=1
                duplicate_max=max(duplicate_max,r['duplicate_site_births']);discrepancy=max(discrepancy,r['maximum_count_discrepancy'])
                if count:
                    q=(np.arange(count,dtype='<f4')+np.float32(u))/np.float32(count)
                    selected=np.searchsorted(cdf32,q,side='right')
                    if (selected>=len(w)).any():raise ValueError('Float32 selector escaped source CDF')
                    float_duplicates=max(float_duplicates,len(selected)-len(np.unique(selected)))
        result.append(dict(owner=owner,source_sites=len(w),actual_birth_batches=len(counts),actual_total_births=sum(counts),
            distinct_native_counts=unique,maximum_expected_site_count=float(max(counts)*w.max()/w.sum()),
            candidate_offset_cases=tested,maximum_duplicate_site_births=duplicate_max,
            float32_maximum_duplicate_site_births=float_duplicates,float32_positive_weights_collapsed=collapsed,
            maximum_count_discrepancy=discrepancy,source_profile_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return dict(native_steps=len(steps),total_observed_journal_steps=len(observed),owners=result,
        native_stages_sha256=hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest(),
        algorithm_sha256=hashlib.sha256((Path(__file__).parent/'liquid_stratified_source.py').read_bytes()).hexdigest(),
        source_position_or_velocity_modified=False,spawn_count_or_volume_modified=False,
        native_selector_installed=False,actual_native_birth_site_readback_verified=False,
        physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    report=audit(a.capture);a.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(report,indent=2))
