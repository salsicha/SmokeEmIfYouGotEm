"""Retile exact water cells and expose two inlets/one outlet inside buffers.

No flow is assigned here. Every retained cell is copied exactly, without
interpolation, bed adjustments, or discarding positive-depth shallow water.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.ops import substring

from build_futaleufu_continuous_water_domain import ROOT, PREFIX, sha, connected_tiles, observe_branches, FutaleufuBed

SIZE=28
FACES={'west':(np.s_[:,0],(-1,0),0,0), 'east':(np.s_[:,-1],(1,0),0,1),
       'south':(np.s_[0,:],(0,-1),1,0), 'north':(np.s_[-1,:],(0,1),1,1)}


def make_port(line, length, origin, incoming, name):
    if length<300. or line.length<=length: raise ValueError('Complete captured buffer and retained route required')
    station=60. if incoming else line.length-60.
    point=np.asarray(line.interpolate(station).coords)[0]
    tangent=np.asarray(line.interpolate(station+1).coords)[0]-np.asarray(line.interpolate(station-1).coords)[0]
    tangent/=np.linalg.norm(tangent);axis=int(np.argmax(abs(tangent)))
    line_index=int(np.rint((point[axis]-origin[axis])/SIZE))
    coordinate=float(origin[axis]+line_index*SIZE)
    ends=np.array([point-[10000,10000],point+[10000,10000]])
    ends[:,axis]=coordinate
    buffer=substring(line,0,length) if incoming else substring(line,line.length-length,line.length)
    hit=buffer.intersection(shapely.LineString(ends))
    if hit.geom_type!='Point': raise ValueError('Port plane must cross captured buffer exactly once')
    station=float(line.project(hit));outside=station if incoming else line.length-station
    if outside<10. or length-outside<300.: raise ValueError('Port must clear cap and retain 300 m hydraulic buffer')
    tangent=np.asarray(line.interpolate(station+1).coords)[0]-np.asarray(line.interpolate(station-1).coords)[0]
    tangent/=np.linalg.norm(tangent)
    sign=int(np.sign(tangent[axis]))*(1 if incoming else -1)
    if abs(tangent[axis])<.5: raise ValueError('Port insufficiently transverse to captured route')
    return dict(branch=name,incoming=incoming,axis=axis,line_index=line_index,coordinate_m=coordinate,
        retained_sign=sign,source_station_m=station,easting_northing_m=list(hit.coords)[0],
        exterior_removed_length_m=outside,remaining_buffer_m=length-outside,buffer_length_m=length,
        tangent_east_north=tangent.tolist())


def outside_port(centers, lines, ports):
    points=shapely.points(np.asarray(centers))
    distances=np.array([shapely.distance(points,line) for line in lines]);owner=distances.argmin(axis=0)
    excluded=np.zeros(len(points),bool)
    for j,(line,p) in enumerate(zip(lines,ports)):
        station=shapely.line_locate_point(line,points)
        buffer=station<p['buffer_length_m'] if p['incoming'] else station>line.length-p['buffer_length_m']
        excluded|=(owner==j)&buffer&((centers[:,p['axis']]-p['coordinate_m'])*p['retained_sign']<0)
    return excluded


def subdivide(index, arrays):
    shape=(252,252)
    if any(a.shape!=shape for a in arrays.values()): raise ValueError('Exact 252-cell parent tiles required')
    for x in range(9):
        for y in range(9):
            yield (index[0]*9+x,index[1]*9+y),{k:a[y*SIZE:(y+1)*SIZE,x*SIZE:(x+1)*SIZE] for k,a in arrays.items()}


def run(sources,network,profile,water,output):
    sources,network,profile,water,output=[Path(p).resolve() for p in (sources,network,profile,water,output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh hydraulic port output required')
    m=json.loads((water/'manifest.json').read_text());pm=json.loads((profile/'manifest.json').read_text())
    if (m.get('schema')!='raftsim.futaleufu_initial_cartesian_water.v1' or m['spacing_m']!=1.
            or m['tile_cells']!=[252,252] or m['rows_increase']!='north'
            or not m['sampled_cross_sections_share_component']):
        raise ValueError('Connected one-metre full buffered water required')
    origin=np.array(m['horizontal_origin_m'])
    bed=FutaleufuBed(sources,profile,network,depth_m=1.8)
    pins={ROOT/p:h for p,h in m['sources_sha256'].items()}
    for rel,h in bed.receipt['sources_sha256'].items():
        if pins.get(ROOT/rel)!=h: raise ValueError('Water and port profiles differ')
    pins.update({p:sha(p) for p in (water/'manifest.json',Path(__file__).resolve())})
    def verify():
        for p,h in pins.items():
            if sha(p)!=h: raise ValueError('Changed hydraulic port input: '+str(p))
    verify()
    ports=[make_port(line,pm['hydraulic_buffers']['branches'][name]['length_m'],origin,j<2,name)
           for j,(name,line) in enumerate(zip(bed.arrays,bed.lines))]
    blocks={}
    for row in m['tiles']:
        p=water/row['file'];pins[p]=row['sha256']
        if sha(p)!=pins[p]: raise ValueError('Water tile changed')
        with np.load(p,allow_pickle=False) as z: arrays={k:z[k].copy() for k in z.files}
        blocks.update(subdivide(row['chunk'],arrays))
    keys=list(blocks);centers=origin+(np.array(keys)+.5)*SIZE
    excluded={k for k,flag in zip(keys,outside_port(centers,bed.lines,ports)) if flag}
    # Retain every positive-depth cell, including below the observation wet
    # threshold, plus a dry tile halo in all eight directions for wetting.
    members={k for k,v in blocks.items() if k not in excluded and np.any(v['initial_depth_m']>0)}
    selected=set(members)
    for i,j in members:
        for di in (-1,0,1):
            for dj in (-1,0,1):
                k=(i+di,j+dj)
                if k in blocks and k not in excluded: selected.add(k)
    observations=[];boundary=[];counts={p['branch']:0 for p in ports};unclassified=[]
    for index in sorted(selected):
        arrays=blocks[index]
        for edge,(sl,neighbor,axis,upper) in FACES.items():
            if (index[0]+neighbor[0],index[1]+neighbor[1]) in selected: continue
            active=arrays['initial_depth_m'][sl]>0
            if not active.any(): continue
            coordinate=origin[axis]+(index[axis]+upper)*SIZE
            center=origin+(np.array(index)+.5)*SIZE
            matches=[p for p in ports if p['axis']==axis and abs(coordinate-p['coordinate_m'])<1e-8
                     and np.linalg.norm(center-np.array(p['easting_northing_m']))<256.
                     and (-neighbor[axis])==p['retained_sign']]
            if len(matches)!=1:
                unclassified.append(dict(tile=list(index),edge=edge,positive_cells=int(active.sum())))
                continue
            p=matches[0];counts[p['branch']]+=int(active.sum())
            boundary.append(dict(tile=list(index),edge=edge,branch=p['branch'],
                role='upstream' if p['incoming'] else 'downstream',positive_depth_cells=int(active.sum()),
                wet_cells=int((arrays['initial_depth_m'][sl]>.05).sum())))
    # Every original gameplay cross-section must still share one wet component;
    # physical port crops are allowed only outside the retained route.
    components,offset,n=connected_tiles({k:blocks[k]['wet'] for k in selected})
    old=FutaleufuBed(sources,PREFIX/'hydrology/channel_profile_2026_10_v2',
                   PREFIX/'hydrography/confluence_network_2026_10_v1/network.json',depth_m=1.8)
    observations,common=observe_branches(old,components,offset,origin,1.)
    errors=[]
    if unclassified: errors.append('Positive water at unclassified exterior faces')
    if not all(counts.values()): errors.append('Missing one or more wet hydraulic ports')
    if not common: errors.append('Original gameplay cross-sections no longer share a component')
    for face in boundary:
        i,j=face['tile'];x,y=np.array([i,j])*SIZE-offset
        labels=components[y:y+SIZE,x:x+SIZE][FACES[face['edge']][0]]
        face['wet_components']=np.unique(labels[labels>0]).tolist()
    for name in counts:
        ids={c for face in boundary if face['branch']==name for c in face['wet_components']}
        if not ids.intersection(common): errors.append('Port disconnected from original gameplay route: '+name)
    # Prove at cell level that physical cuts removed no positive-depth cells
    # whose nearest captured-arm projection belongs to the retained route.
    removed=0;interior_removed=0
    for index in sorted(excluded):
        row,col=np.nonzero(blocks[index]['initial_depth_m']>0)
        if not len(row): continue
        xy=origin+np.c_[index[0]*SIZE+col+.5,index[1]*SIZE+row+.5]
        points=shapely.points(xy)
        distances=np.array([shapely.distance(points,line) for line in bed.lines]);owner=distances.argmin(axis=0)
        for j,(name,line) in enumerate(zip(bed.arrays,bed.lines)):
            station=shapely.line_locate_point(line,points)
            r=pm['hydraulic_buffers']['branches'][name]
            retained=(station>=r['length_m']) if j<2 else (station<=line.length-r['length_m'])
            interior_removed+=int(((owner==j)&retained).sum())
        removed+=len(row)
    if interior_removed: errors.append('Physical cuts removed positive-depth interior cells')
    verify();output.mkdir(parents=True)
    rows=[]
    if not errors:
        for index in sorted(selected):
            name='tile_%d_%d.npz'%index
            np.savez_compressed(output/name,**blocks[index])
            rows.append(dict(chunk=list(index),file=name,sha256=sha(output/name)))
        np.savez_compressed(output/'components.npz',components=components,cell_offset=offset)
    report=dict(schema='raftsim.futaleufu_hydraulic_ports.v1',sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        horizontal_origin_m=origin.tolist(),spacing_m=1.,tile_cells=[SIZE,SIZE],rows_increase='north',
        parent_water_tiles=len(m['tiles']),subtiles_considered=len(blocks),selected_tiles=len(selected),
        positive_depth_tiles=len(members),dry_halo_tiles=len(selected-members),
        removed_positive_depth_cells=removed,removed_positive_depth_interior_cells=interior_removed,
        excluded_port_tiles=len(excluded),ports=ports,boundaries=boundary,positive_port_cells=counts,
        unclassified_exterior_faces=unclassified,original_route_observations=observations,
        common_original_route_components=common,errors=errors,tiles=rows,
        retained_cells_exact=True,discharge_assigned=False,native_throughflow_validated=False,normal_map_installed=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('selected_tiles','positive_depth_tiles','dry_halo_tiles','positive_port_cells','common_original_route_components','errors')}),flush=True)
    if errors: raise ValueError('; '.join(errors))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sources','network','profile','water','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.sources,a.network,a.profile,a.water,a.out)
