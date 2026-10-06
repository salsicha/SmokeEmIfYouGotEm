"""Independently prove exported native candidate geometry using exact rationals.

Original shared endpoints have analytic rational coordinates. Their binary64
storage error is reported separately; it is NOT silently accepted as wet.
No native floating predicate or native pass flag establishes this proof.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
from three_wet_bank_envelope import certificate,value

def number(x):
    v=float(x)
    if not math.isfinite(v):raise ValueError('Finite native binary64 values required')
    return F(v)

def audit(path,expected_sha256):
    content=Path(path).read_bytes();digest=hashlib.sha256(content).hexdigest()
    if digest!=expected_sha256:raise ValueError('Native export hash mismatch')
    data=json.loads(content)
    if data['normal_renderer_integrated'] or data['gameplay_accepted']:
        raise ValueError('Native reference cannot claim playable acceptance')
    if len(data['cases'])!=4:raise ValueError('Four original native cases required')
    results=[]
    for index,item in enumerate(data['cases']):
        if item['case']!=index:raise ValueError('Native case identity changed')
        B,H=tuple(map(number,item['bed'])),tuple(map(number,item['depth']))
        if len(B)!=4 or len(H)!=4 or H[0]!=0 or any(H[i]<=0 or B[0]<=B[i]+H[i] for i in (1,2,3)):
            raise ValueError('Invalid high-bank donor geometry')
        points=lambda key:tuple(tuple(map(number,p)) for p in item[key])
        boundary,inner,polygon=points('boundary'),points('inner'),points('polygon')
        if len(boundary)<2 or len(inner)!=len(boundary):raise ValueError('Incomplete native band')
        if any(len(p)!=2 or any(v<0 or v>1 for v in p) for group in (boundary,inner,polygon) for p in group):
            raise ValueError('Native vertex outside original cell')
        if polygon!=((F(1),F(1)),(F(1),F(0)),*boundary,(F(0),F(1))):
            raise ValueError('Native polygon/boundary identity mismatch')
        expected=((1-H[1]/(B[0]-B[1]),F(0)),(F(0),1-H[2]/(B[0]-B[2])))
        endpoint_error=max(sum(abs(a-b) for a,b in zip(p,q)) for p,q in zip((boundary[0],boundary[-1]),expected))
        # This is a FLOATING STORAGE ERROR guard, not a wet-depth allowance.
        # Strict wet certificates for those stored coordinates are reported below.
        if endpoint_error>F(64)*F(math.ulp(1.)):
            raise ValueError('Shared endpoint differs by more than arithmetic rounding')
        ideal_boundary=(expected[0],*boundary[1:-1],expected[1])
        ideal_polygon=(polygon[0],polygon[1],*ideal_boundary,polygon[-1])
        width=F(1,1000)
        for p,q in zip(ideal_boundary,inner):
            if sum(abs(a-b) for a,b in zip(p,q))>width:
                raise ValueError('Native dry-side band exceeds original 1mm bound')
        triangles=item['triangles']
        if len(triangles)!=len(polygon)-2:raise ValueError('Incomplete native triangulation')
        area=F(0);strict_stored=True
        def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        for p,q,a,b in zip(ideal_boundary,ideal_boundary[1:],inner,inner[1:]):
            if cross((0,0),p,q)<=0 or cross(p,q,b)<0 or cross(p,b,a)<0:
                raise ValueError('Native radial order or boundary-band partition invalid')
        edges={}
        for ids in triangles:
            if len(ids)!=3 or any(type(i)!=int or not 0<=i<len(polygon) for i in ids):
                raise ValueError('Invalid native triangle index')
            tri=tuple(ideal_polygon[i] for i in ids)
            signed=cross(*tri)
            if signed>=0 or not certificate(B,H,tri,1):raise ValueError('Native wet triangle not exactly certified')
            area-=signed/2
            actual=tuple(polygon[i] for i in ids)
            strict_stored &= certificate(B,H,actual,1)
            for a,b in zip(ids,(*ids[1:],ids[0])):
                key=tuple(sorted((a,b)));edges.setdefault(key,[]).append((a,b))
        # Detect missing, duplicated, reversed or nonmanifold triangles/edges.
        for key,uses in edges.items():
            adjacent=(key[1]-key[0]==1 or key==(0,len(polygon)-1))
            if adjacent and len(uses)!=1:raise ValueError('Native perimeter edge multiplicity')
            if not adjacent and (len(uses)!=2 or uses[0]!=uses[1][::-1]):
                raise ValueError('Native interior edge incidence mismatch')
        for i in range(len(polygon)):
            if tuple(sorted((i,(i+1)%len(polygon)))) not in edges:raise ValueError('Native perimeter incomplete')
        omitted=sum(cross((0,0),p,q)/2 for p,q in zip(ideal_boundary,ideal_boundary[1:]))
        if area+omitted!=1:raise ValueError('Native polygon does not partition the original cell')
        for p,q in zip(inner,inner[1:]):
            if not certificate(B,H,((F(0),F(0)),p,q),-1):raise ValueError('Native omitted region is not certified dry')
        results.append(dict(case=index,segments=len(boundary)-1,triangles=len(triangles),
            ideal_shared_endpoint_geometry_certified=True,dry_band_certified=True,
            binary64_stored_geometry_strictly_certified=bool(strict_stored),
            endpoint_storage_error_local=str(endpoint_error),
            minimum_stored_vertex_numerator=str(min(value(B,H,p) for p in polygon)),
            construction_ms=item['construction_ms'],coefficient_tests=item['coefficient_tests']))
    return dict(native_export_sha256=digest,cases=results,whole_river_or_gameplay_accepted=False,
                native_world_mapping_and_cache_accepted=False,isolated_performance_accepted=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--sha256',required=True)
    args=p.parse_args();print(json.dumps(audit(args.native,args.sha256),indent=2))
