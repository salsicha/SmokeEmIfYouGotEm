"""Expand dry computational support using exact existing parent water cells.

No terrain, water depth, current, physical port or acceptance gate is changed.
This prepares a fresh cold-start domain, not an accepted hydraulic result.
"""
import argparse
import json
import shutil
from pathlib import Path
import numpy as np
from prepare_futaleufu_hydraulic_ports import (
    ROOT, SIZE, FACES, sha, subdivide, outside_port, FutaleufuBed)


def expanded_keys(original, available, excluded, layers):
    if type(layers) is not int or not 1 <= layers <= 3:
        raise ValueError('One to three additional dry layers required')
    selected=set(original)
    if not selected <= set(available)-set(excluded):
        raise ValueError('Original domain lacks valid parent support')
    for _ in range(layers):
        selected |= {(i+di,j+dj) for i,j in selected
            for di in (-1,0,1) for dj in (-1,0,1)
            if (i+di,j+dj) in available and (i+di,j+dj) not in excluded}
    return selected


def run(ports, water, out, layers=2):
    ports,water,out=[Path(p).resolve() for p in (ports,water,out)]
    for p in (ports,water,out):p.relative_to(ROOT/'tmp')
    if out.exists():raise ValueError('Fresh output required')
    if shutil.disk_usage(ROOT).free<42*1024**3:raise ValueError('Preserve disk reserve')
    source=ports/'manifest.json';parent=water/'manifest.json'
    m=json.loads(source.read_text());w=json.loads(parent.read_text())
    if (m.get('schema')!='raftsim.futaleufu_hydraulic_ports.v1' or m['errors'] or
        not m['retained_cells_exact'] or m['removed_positive_depth_interior_cells'] or
        not m['common_original_route_components'] or m['tile_cells']!=[SIZE,SIZE] or
        w.get('schema')!='raftsim.futaleufu_initial_cartesian_water.v1' or
        w['tile_cells']!=[252,252] or w['spacing_m']!=1 or w['rows_increase']!='north' or
        m['horizontal_origin_m']!=w['horizontal_origin_m']):
        raise ValueError('Exact reviewed original domain and parent water required')
    pins={ROOT/p:h for p,h in m['sources_sha256'].items()}
    if pins.get(parent)!=sha(parent):raise ValueError('Wrong parent water')
    def pin(p,digest=None):
        p=Path(p).resolve();p.relative_to(ROOT)
        digest=digest or sha(p)
        if (p in pins and pins[p]!=digest) or sha(p)!=digest:
            raise ValueError('Changed or conflicting source: '+str(p))
        pins[p]=digest
    for p in (source,Path(__file__)):pin(p)
    def verify():
        for p,d in pins.items():
            if sha(p)!=d:raise ValueError('Changed source: '+str(p))
    verify()
    reference=FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
        ROOT/'tmp/futaleufu-hydraulic-buffer-profile-v1',
        ROOT/'tmp/futaleufu-hydraulic-buffer-network-v1/network.json',depth_m=1.8)
    for p,d in reference.receipt['sources_sha256'].items():
        if pins.get(ROOT/p)!=d:raise ValueError('Different port geometry source')
    blocks={}
    for row in w['tiles']:
        path=water/row['file'];pin(path,row['sha256'])
        with np.load(path,allow_pickle=False) as z:
            blocks.update(subdivide(row['chunk'],{k:z[k].copy() for k in z.files}))
    original={tuple(r['chunk']):r for r in m['tiles']}
    if len(original)!=len(m['tiles']):raise ValueError('Duplicate original tile')
    keys=list(blocks);origin=np.asarray(m['horizontal_origin_m'])
    excluded={k for k,flag in zip(keys,outside_port(origin+(np.array(keys)+.5)*SIZE,
        reference.lines,m['ports'])) if flag}
    selected=expanded_keys(original,blocks,excluded,layers)
    added=selected-set(original)
    if not added:raise ValueError('No additional support')
    for key in added:
        if np.any(blocks[key]['initial_depth_m']!=0):raise ValueError('Additional support must be initially dry')
    for key,row in original.items():
        path=ports/row['file'];pin(path,row['sha256'])
        with np.load(path,allow_pickle=False) as z:
            if set(z.files)!=set(blocks[key]) or any(not np.array_equal(z[k],blocks[key][k]) for k in z.files):
                raise ValueError('Existing cells disagree with parent')
    open_faces={(tuple(r['tile']),r['edge']) for r in m['boundaries']}
    for key,edge in open_faces:
        delta=FACES[edge][1]
        if (key[0]+delta[0],key[1]+delta[1]) in selected:raise ValueError('Physical port became interior')
    for key in selected:
        for edge,(sl,delta,_,_) in FACES.items():
            if (key[0]+delta[0],key[1]+delta[1]) not in selected and (key,edge) not in open_faces:
                if np.any(blocks[key]['initial_depth_m'][sl]>0):raise ValueError('Unclassified positive exterior water')
    verify();out.mkdir(parents=True)
    rows=[]
    for key in sorted(selected):
        name='tile_%d_%d.npz'%key
        if key in original:shutil.copyfile(ports/original[key]['file'],out/name)
        else:np.savez_compressed(out/name,**blocks[key])
        rows.append(dict(chunk=list(key),file=name,sha256=sha(out/name)))
    verify()
    report=dict(m)
    report.update(tiles=rows,selected_tiles=len(selected),dry_halo_tiles=len(selected)-m['positive_depth_tiles'],
        sources_sha256={p.relative_to(ROOT).as_posix():d for p,d in pins.items()},
        dry_support_expansion=dict(additional_layers=layers,added_tiles=len(added),original_tiles=len(original),
            added_initial_water_volume_m3=0.,original_tile_bytes_preserved=True,
            physical_ports_unchanged=True,encoded_terrain_unchanged=True),
        native_throughflow_validated=False,normal_map_installed=False)
    with (out/'manifest.json').open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report['dry_support_expansion']),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('ports','water','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--layers',type=int,default=2)
    a=p.parse_args();run(a.ports,a.water,a.out,a.layers)
