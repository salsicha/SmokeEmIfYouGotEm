"""Verify the dry-support repair changes domain extent, not physical inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_futaleufu_native_cook import ROOT, sha


def physical_scenario(value):
    return {k:v for k,v in value.items() if k!='metadata'}


def physical_ports(manifest):
    keys=manifest['tile_indices']
    ports={}
    for row in manifest['boundary_probes']:
        key=(tuple(keys[row['tile_index']]),row['edge'])
        if key in ports:raise ValueError('Duplicate physical port')
        ports[key]=(row['role'],row['branch'])
    return ports


def verify(original, expanded, out):
    original,expanded,out=[Path(p).resolve() for p in (original,expanded,out)]
    for p in (original,expanded,out):p.relative_to(ROOT/'tmp')
    if out.exists():raise ValueError('Preserve existing evidence')
    paths=[original/'manifest.json',expanded/'manifest.json']
    before,after=[json.loads(p.read_text()) for p in paths]
    pins={p:sha(p) for p in paths+[Path(__file__).resolve()]}
    fields=('schema','dt_seconds','grid','horizontal_origin_utm18s_m','vertical_datum_m',
        'inlet_budget','combined_inlet_discharge_m3s','measured_discharge','measured_bathymetry')
    if any(before[k]!=after[k] for k in fields) or physical_ports(before)!=physical_ports(after):
        raise ValueError('Physical grid, clock, ports or discharge changed')
    if before['schema']!='raftsim.cartesian_flow_cook.v1' or before['grid']!={'cell_m':1.,'tile_cells':28}:
        raise ValueError('Reviewed native grid required')
    old={r['name']:r for r in before['inputs']};new={r['name']:r for r in after['inputs']}
    if len(old)!=len(before['inputs']) or len(new)!=len(after['inputs']) or not set(old)<set(new):
        raise ValueError('Strict additive unique domain required')
    for folder,m in ((original,before),(expanded,after)):
        if m['packages']!=[r['name'] for r in m['inputs']] or len(m['tile_indices'])!=len(m['inputs']):
            raise ValueError('Native package ordering differs')
        for key,row in zip(m['tile_indices'],m['inputs']):
            if row['name']!='tile_%d_%d'%tuple(key):raise ValueError('Package and tile index disagree')
            for filename,digest in row['files'].items():
                p=(folder/row['name']/filename).resolve();p.relative_to(folder)
                if sha(p)!=digest:raise ValueError('Changed native input')
                pins[p]=digest
    for name in old:
        for filename in ('bed.npy','features.json','probes.json'):
            if old[name]['files'][filename]!=new[name]['files'][filename]:raise ValueError('Original physical input changed')
        a,b=[json.loads((p/name/'scenario.json').read_text()) for p in (original,expanded)]
        if physical_scenario(a)!=physical_scenario(b):raise ValueError('Original physical scenario changed')
        with np.load(original/name/'initial_state.npz',allow_pickle=False) as a, np.load(expanded/name/'initial_state.npz',allow_pickle=False) as b:
            if set(a.files)!=set(b.files) or any(not np.array_equal(a[k],b[k]) for k in a.files):
                raise ValueError('Original native initial state changed')
    for name in set(new)-set(old):
        bed=np.load(expanded/name/'bed.npy',allow_pickle=False)
        with np.load(expanded/name/'initial_state.npz',allow_pickle=False) as a:
            if (bed.shape!=(28,28) or not np.isfinite(bed).all() or
                any(np.any(a[k]) for k in ('depth','u','v','hu','hv','wet')) or
                not np.array_equal(a['eta'],bed)):
                raise ValueError('Added tile is not exact dry zero-momentum support')
    if any(sha(p)!=digest for p,digest in pins.items()):raise ValueError('Input changed during verification')
    receipt=dict(schema='raftsim.futaleufu_expanded_native_domain_verification.v1',
        original_packages=len(old),added_packages=len(new)-len(old),total_packages=len(new),
        physical_ports_unchanged=True,original_physical_scenarios_unchanged=True,
        original_bed_features_and_initial_states_exact=True,added_water_and_momentum_zero=True,
        inlet_budget=after['inlet_budget'],hydraulics_accepted=False,
        sources_sha256={p.relative_to(ROOT).as_posix():digest for p,digest in pins.items()})
    with out.open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in receipt.items() if k!='sources_sha256'}),flush=True)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original','expanded','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();verify(a.original,a.expanded,a.out)
