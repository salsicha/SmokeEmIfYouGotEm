"""Bounded sampler for assembled Chilko terrain, including across tile edges.

Returns source kind with every interpolated elevation. Missing support remains
missing; no edge-clamping and no interpreting this terrain surface as riverbed.
"""
import json
from collections import OrderedDict
from pathlib import Path

import numpy as np

from capture_lidarbc_window import validate_window
from mosaic_lidarbc_crops import sha


class CorridorTerrain:
    def __init__(self,folder,cache_tiles=4):
        self.folder=Path(folder).resolve()
        self.manifest=json.loads((self.folder/'manifest.json').read_text())
        m=self.manifest
        if (m.get('schema') not in ('raftsim.chilko_corridor_terrain.v1', 'raftsim.chilko_corridor_conditioned_terrain.v1') or
                m.get('river_id')!='chilko_river_bc' or m.get('horizontal_crs')!='EPSG:3157' or
                m.get('vertical_reference')!='CGVD2013 (EPSG:6647)' or m.get('cell_m')!=1. or
                type(cache_tiles) is not int or not 1<=cache_tiles<=16):
            raise ValueError('Unsupported terrain frame or cache limit')
        self.conditioned=m['schema']=='raftsim.chilko_corridor_conditioned_terrain.v1'
        if self.conditioned and (not m.get('inferred_seam',{}).get('native_pixels_unchanged') or
                m['inferred_seam'].get('measured') is not False or not m.get('source_terrain',{}).get('sha256')):
            raise ValueError('Missing inferred transition provenance')
        self.entries={};self.cache=OrderedDict();self.cache_tiles=cache_tiles;self.size=None
        for row in m['tiles']:
            x0,y0,x1,y1=validate_window(row['bounds'])
            size=x1-x0
            if (size!=y1-y0 or x0%size or y0%size or row['cell']!=[x0//size,y0//size] or
                    (self.size is not None and self.size!=size) or tuple(row['cell']) in self.entries):
                raise ValueError('Terrain tiles must share one nonoverlapping square lattice')
            self.size=size
            path=(self.folder/row['file']).resolve();path.relative_to(self.folder)
            self.entries[tuple(row['cell'])]=(path,row)
        if not self.entries:raise ValueError('No terrain tiles')

    def load(self,key):
        if key not in self.entries:return None
        if key in self.cache:
            self.cache.move_to_end(key);return self.cache[key]
        path,row=self.entries[key]
        if sha(path)!=row['sha256']:raise ValueError('Changed terrain tile')
        with np.load(path,allow_pickle=False) as z:
            height,kind=z['height_m'],z['source_kind']
            if (height.shape!=(self.size,self.size) or kind.shape!=height.shape or
                    height.dtype!=np.float32 or kind.dtype!=np.uint8 or
                    float(z['cell_m'])!=1. or float(z['x0'])!=row['bounds'][0] or
                    float(z['y_top'])!=row['bounds'][3] or np.isinf(height).any() or
                    not np.isin(kind,[0,1,2,3] if self.conditioned else [0,1,2]).all() or
                    not np.array_equal(kind>0,np.isfinite(height))):
                raise ValueError('Terrain pixels disagree with grid/source receipt')
        self.cache[key]=(height,kind)
        while len(self.cache)>self.cache_tiles:self.cache.popitem(last=False)
        return height,kind

    def sample(self,xy):
        xy=np.asarray(xy,dtype=float)
        if xy.ndim<2 or xy.shape[-1]!=2 or not np.isfinite(xy).all():
            raise ValueError('Finite geographic sample coordinates required')
        shape=xy.shape[:-1];points=xy.reshape(-1,2)
        result=np.zeros(len(points));kind=np.zeros(len(points),np.uint8)
        for start in range(0,len(points),65536):
            stop=min(start+65536,len(points));p=points[start:stop]-.5
            base=np.floor(p).astype(np.int64);fraction=p-base
            heights=result[start:stop];sources=kind[start:stop];valid=np.ones(len(p),bool)
            for dx,dy in ((0,0),(1,0),(0,1),(1,1)):
                weights=(fraction[:,0] if dx else 1-fraction[:,0])*(fraction[:,1] if dy else 1-fraction[:,1])
                needed=np.flatnonzero(weights>0)
                pixel=base[needed]+[dx,dy];keys=pixel//self.size
                unique,inverse=np.unique(keys,axis=0,return_inverse=True)
                for i,key in enumerate(unique):
                    subset=inverse==i;indices=needed[subset]
                    tile=self.load(tuple(key))
                    if tile is None:
                        valid[indices]=False;continue
                    local=pixel[subset]-key*self.size
                    h,k=tile[0][self.size-1-local[:,1],local[:,0]],tile[1][self.size-1-local[:,1],local[:,0]]
                    finite=np.isfinite(h);valid[indices]&=finite
                    heights[indices]+=np.where(finite,h,0)*weights[indices]
                    sources[indices]=np.maximum(sources[indices],k)
            heights[~valid]=np.nan;sources[~valid]=0
        return result.reshape(shape),kind.reshape(shape)
