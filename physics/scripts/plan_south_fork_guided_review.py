"""Plan a conservative diagnostic paddle route in inferred candidate water.

This is a game-test input, not surveyed navigation advice or a real-river line.
"""
from pathlib import Path
import heapq
import hashlib
import json
import sys
import argparse

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
from scipy.ndimage import minimum_filter, shift


def aligned_raft_clearance(depth,cell,half_length=2.35,half_width=1.2):
    """Exact bilinear extrema for an axis-aligned envelope at grid centres.

    This includes a 20-cm margin on the 4.3 x 2.0 m raft. It is only a route
    planning envelope; yawed hull clearance must be checked in gameplay.
    """
    offsets=lambda half: sorted(set([-half,half,*[i*cell for i in range(-int(half/cell),int(half/cell)+1)]]))
    clearance=depth.copy()
    for y in offsets(half_width):
        for x in offsets(half_length):
            clearance=np.minimum(clearance,shift(depth,(y/cell,x/cell),order=1,mode='constant',cval=0,prefilter=False))
    return clearance


def plan(depth,start,end_column,cell=1.0,footprint_radius=3.0,minimum_depth=.55,clearance=None,velocity=None):
    if depth.ndim!=2 or not np.isfinite(depth).all() or cell<=0:
        raise ValueError('Finite depth grid and positive cell size required')
    radius=int(np.ceil(footprint_radius/cell))
    if clearance is None:clearance=minimum_filter(depth,size=2*radius+1,mode='constant',cval=0)
    if clearance.shape!=depth.shape or not np.isfinite(clearance).all():raise ValueError('Invalid footprint clearance grid')
    if velocity is not None:
        if len(velocity)!=2 or any(a.shape!=depth.shape or not np.isfinite(a).all() for a in velocity):
            raise ValueError('Two finite velocity grids matching depth are required')
    safe=clearance>=minimum_depth
    rows,cols=depth.shape
    if not (0<=start[0]<rows and 0<=start[1]<cols and 0<=end_column<cols) or not safe[start]:
        raise ValueError('Start or endpoint is outside safe footprint water')
    queue=[(0.,start)];cost={start:0.};parent={}
    end=None
    while queue:
        distance,current=heapq.heappop(queue)
        if distance!=cost[current]:continue
        y,x=current
        if x==end_column:end=current;break
        for dy,dx in ((0,1),(1,1),(-1,1),(1,0),(-1,0),(0,-1),(1,-1),(-1,-1)):
            yy,xx=y+dy,x+dx
            if not (0<=yy<rows and 0<=xx<cols and safe[yy,xx]):continue
            if dx and dy and not (safe[y,xx] and safe[yy,x]):continue
            step=np.hypot(dx,dy)*cell*(1.+.6/max(float(clearance[yy,xx]),.1))
            if velocity is not None:
                u,v=velocity
                length=np.hypot(dx,dy)
                along=(u[y,x]*dx+v[y,x]*dy)/length
                cross=(v[y,x]*dx-u[y,x]*dy)/length
                # Ground-track speed attainable with the game's existing
                # 2.2 m/s over-water paddling governor, not a force override.
                if abs(cross)>=2.2:continue
                speed=along+np.sqrt(2.2**2-cross**2)
                if speed<=.1:continue
                step/=speed
            candidate=distance+step
            nxt=(yy,xx)
            if candidate<cost.get(nxt,float('inf')):
                cost[nxt]=candidate;parent[nxt]=current;heapq.heappush(queue,(candidate,nxt))
    if end is None:raise ValueError('No connected route with the required footprint depth')
    path=[end]
    while path[-1]!=start:path.append(parent[path[-1]])
    return path[::-1],clearance


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--flow-aware',action='store_true')
    parser.add_argument('--fields',type=Path,default=Path('tmp/south-fork-survey-hydraulics/1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907/engine_review'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    folder=(ROOT/args.fields).resolve()
    out=ROOT/(args.output or Path('docs/reconstruction-review-2026-09-07/guided-route-flow-following.json' if args.flow_aware else 'docs/reconstruction-review-2026-09-07/guided-route.json'))
    if out.exists():raise FileExistsError('Preserve previous route evidence; select a new --output')
    manifest=json.loads((folder/'manifest.json').read_text());grid=manifest['grid']
    record=manifest['bands'][0]['arrays']['h'];source=folder/record['file']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Depth export changed')
    start=json.loads((folder/'engine_start.json').read_text())['station_lateral_m']
    cell=grid['dx_m']
    if cell!=grid['dy_m']:raise ValueError('Only square diagnostic grid supported')
    origin=np.array([grid['origin_x_m'],grid['origin_y_m']])
    xy=np.rint((np.array(start)-origin)/cell).astype(int)
    depth=np.load(source)
    velocity=None
    if args.flow_aware:
        arrays=[]
        for key in ('u','v'):
            entry=manifest['bands'][0]['arrays'][key];path=folder/entry['file']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Velocity export changed')
            arrays.append(np.load(path))
        velocity=tuple(arrays)
    path,clearance=plan(depth,(xy[1],xy[0]),round((112-origin[0])/cell),cell,
        clearance=aligned_raft_clearance(depth,cell),velocity=velocity)
    points=[[float(origin[0]+x*cell),float(origin[1]+y*cell)] for y,x in path]
    report={'schema':'raftsim.survey.guided_route.v1','source_geometry_sha256':manifest['review']['source_geometry_sha256'],
        'source_bed_sampling':manifest['review'].get('source_bed_sampling','bilinear'),
        'cooked_fields_dir':folder.relative_to(ROOT).as_posix(),'depth_sha256':record['sha256'],
        'station_lateral_m':points,'planning_footprint_length_m':4.7,'planning_footprint_width_m':2.4,
        'planning_footprint_orientation':'downstream aligned; actual yawed clearance checked only at runtime',
        'required_depth_m':.55,
        'minimum_route_footprint_depth_m':float(min(clearance[y,x] for y,x in path)),
        'method':('8-neighbour depth-weighted attainable travel time' if args.flow_aware else
            '8-neighbour depth-weighted shortest path')+'; no dry diagonal corner cutting',
        'current_aware_travel_time':args.flow_aware,'paddling_speed_limit_mps':2.2 if args.flow_aware else None,
        'real_river_navigation_line':False,'underwater_depth_measured':False,'guided_traversal_validated':False}
    out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='station_lateral_m'},indent=2))
    print(f'{len(points)} route points, start {points[0]}, end {points[-1]}')


if __name__=='__main__':main()
