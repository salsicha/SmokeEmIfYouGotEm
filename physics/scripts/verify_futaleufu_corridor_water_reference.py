"""Independently recompute temporal optical votes from the original mosaics."""
import argparse
import json
from pathlib import Path
import numpy as np
from build_futaleufu_corridor_sources import ROOT,OPTICAL,sha


def audit(reference,sources):
    reference,sources=Path(reference).resolve(),Path(sources).resolve()
    out=reference/'original-pixel-audit.json'
    if out.exists():raise ValueError('Fresh pixel audit required')
    r=json.loads((reference/'manifest.json').read_text());s=json.loads((sources/'manifest.json').read_text())
    if r['schema']!='raftsim.futaleufu_corridor_water_reference.v1' or r['grid']!=s['grid']:
        raise ValueError('Water reference and native source grid disagree')
    pins={reference/'manifest.json':sha(reference/'manifest.json'),sources/'manifest.json':sha(sources/'manifest.json')}
    for relative,digest in r['sources_sha256'].items():
        p=(ROOT/relative).resolve();p.relative_to(ROOT)
        if sha(p)!=digest:raise ValueError('Changed source')
        pins[p]=digest
    path=reference/'water_reference.npz'
    if sha(path)!=r['artifact_sha256']:raise ValueError('Changed reference arrays')
    pins[path]=r['artifact_sha256']
    shape=tuple(s['grid']['shape']);r0,r1,c0,c1=s['grid']['native_optical_crop_rc']
    count=np.zeros(shape,dtype='u1');water=count.copy();bright=count.copy()
    dates=[]
    for item in s['optical']:
        original=(OPTICAL/item['source']).resolve();original.relative_to(OPTICAL)
        if sha(original)!=item['source_sha256']:raise ValueError('Changed original mosaic')
        pins[original]=item['source_sha256']
        with np.load(original,allow_pickle=False) as z:
            raw=[z[b][r0:r1,c0:c1] for b in ('blue','green','red','nir')]
        valid=np.logical_and.reduce([v!=0 for v in raw])
        b,g,red,n=[v.astype(np.float32)*.0001-.1 for v in raw]
        white=(b>.22)&(g>.22)&(red>.18)&(abs(b-red)<.12)&valid
        wet=(((g-n)/np.maximum(g+n,.001)>.05)|white)&valid
        count+=valid;water+=wet;bright+=white;dates.append(item['datetime'])
    with np.load(path,allow_pickle=False) as z:
        for key,value in [('valid_dates',count),('water_dates',water),('bright_dates',bright),
                          ('repeated_water',(count>=2)&(water>=2))]:
            if not np.array_equal(z[key],value):raise ValueError('Original pixels disagree with '+key)
        if np.any(z['route_associated_water']&~z['repeated_water']):raise ValueError('Association invented water')
    if dates!=r['dates'] or int((3-count).sum())!=r['native_unknown_observations']:
        raise ValueError('Date/unknown observation mismatch')
    if not all(sha(p)==h for p,h in pins.items()):raise ValueError('Source changed during independent audit')
    result=dict(schema='raftsim.futaleufu_water_original_pixel_audit.v1',passed=True,
        reference_manifest_sha256=pins[reference/'manifest.json'],dates=dates,
        original_pixel_observations=int(count.size*3),unknown_observations=int((3-count).sum()),
        per_pixel_votes_exact=True,associated_mask_does_not_invent_water=True,
        qualification='Radiometric and native-grid numerical agreement only, not physical bank/stage accuracy or cloud screening.')
    with out.open('x') as f:json.dump(result,f,indent=2)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--sources',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.reference,a.sources),indent=2))
