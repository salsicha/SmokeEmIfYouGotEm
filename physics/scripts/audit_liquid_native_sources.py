"""Verify actual GPU source selections through immutable birth IDs and counts.

Final readback covers retained incoming particles and the current birth batch,
not an exact history of particles that already exited. No scene/physics writes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from liquid_stage_journal import stage_groups
from liquid_dataset import resolve
from liquid_stratified_source import native_sites


def audit(root):
    root=root.resolve();d=json.loads((root/'stages.json').read_text());capture=json.loads((root/'capture.json').read_text())
    if not capture['complete'] or not capture.get('inlet_sources_unchanged') or not d.get('native_stratified_source_requested'):
        raise ValueError('Successful native stratified source capture and immutable source snapshots required')
    snapshots=json.loads((root/'inlet-sources.json').read_text())
    expected_sources={'RaftSimLiquidStratifiedSource.h','RaftSimLiquidRegionalState.cpp',
        'RaftSimLiquidNativeTransferAudit.h','RaftSimEditorLiquidRegionalStageProbe.cpp'}
    if snapshots.get('schema')!='raftsim.liquid_inlet_sources.v1' or set(snapshots['files_sha256'])!=expected_sources:
        raise ValueError('Complete native inlet implementation snapshots required')
    for name,digest in snapshots['files_sha256'].items():
        p=(root/name).resolve()
        if p.parent!=root or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Native source snapshot changed')
    steps=[g for g in stage_groups(d) if g['entries'][0]['first']][:d['native_transfer_packet_step']]
    if len(steps)!=d['native_transfer_packet_step'] or any([e['owner'] for e in g['entries']]!=list(range(12)) for g in steps):
        raise ValueError('Full native birth-count history required')
    counts=np.array([[e['native_rate_spawns']+e['native_event_spawns'] for e in g['entries']] for g in steps],dtype=np.int64)
    ends=counts.cumsum(axis=0);starts=ends-counts;dataset=resolve(d)
    all_ids=[];all_sites=[]
    for r in d['native_transfer_packet']:
        n=r['particle_count'];nf=r['route_float_components'];ni=r['route_int_components'];cap=r['particle_capacity']
        words=read(root,r,'route_words',(nf+ni,cap))
        ids=words[nf+np.array(r['route_identity_offsets'][:2]),:n].T.astype(np.int64)
        offset=r.get('route_source_index_offset',-1)
        # Nonemitting owners may have the unused source index optimized away.
        if offset<0:
            if np.any(ids[:,1]>=counts[0,ids[:,0]]):raise ValueError('Retained incoming particle lacks native source-index attribute')
            sites=np.full(n,-1)
        else:
            if offset>=ni:raise ValueError('Source index lies outside native ABI')
            sites=words[nf+offset,:n].view('<i4').astype(np.int64)
        all_ids.append(ids);all_sites.append(sites)
    ids=np.concatenate(all_ids);sites=np.concatenate(all_sites)
    if len(np.unique(ids,axis=0))!=len(ids):raise ValueError('Native immutable identities duplicated')
    records=[];mismatches=0;duplicates=0
    for owner in range(12):
        use=(ids[:,0]==owner)&(ids[:,1]>=counts[0,owner]);sequences=ids[use,1];actual=sites[use]
        if not len(sequences):
            if counts[-1,owner]:raise ValueError('Entire current source batch missing from native readback')
            continue
        path=dataset['regions']/f'region-{owner:03d}.json';r=json.loads(path.read_text());w=r['source_weights_m3_per_s']
        born=np.searchsorted(ends[:,owner],sequences,side='right')
        if (born>=len(steps)).any():raise ValueError('Birth identity is later than captured native step')
        expected=native_sites(w,sequences,starts[born,owner],counts[born,owner],int(d['native_source_seed'])+owner*7919)
        mismatch=actual!=expected;mismatches+=int(mismatch.sum())
        pair=np.column_stack((born,actual));dupes=len(pair)-len(np.unique(pair,axis=0));duplicates+=dupes
        current=int((born==len(steps)-1).sum())
        records.append(dict(birth_owner=owner,retained_incoming_particles=len(sequences),source_index_mismatches=int(mismatch.sum()),
            duplicate_sites_within_retained_birth_batches=dupes,current_batch_particles=current,
            current_batch_expected=int(counts[-1,owner]),current_batch_complete=bool(current==counts[-1,owner]),
            source_profile_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            first_mismatches=[dict(sequence=int(sequences[i]),native_step=int(born[i]+1),actual=int(actual[i]),expected=int(expected[i])) for i in np.flatnonzero(mismatch)[:8]]))
    return dict(native_step=d['native_transfer_packet_step'],particles=len(ids),owners=records,
        native_source_indices_match=bool(records and mismatches==0 and all(r['current_batch_complete'] for r in records)),
        mismatches=mismatches,duplicate_sites_within_retained_birth_batches=duplicates,
        scope='retained incoming particles plus all current births; not retired particle history',
        native_stages_sha256=hashlib.sha256((root/'stages.json').read_bytes()).hexdigest(),
        native_sources=snapshots['files_sha256'],physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=audit(a.capture);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2))
