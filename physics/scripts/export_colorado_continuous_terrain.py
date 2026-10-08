"""Export source-backed Landscape chunks on one geographic vertex lattice.

Shared vertices use one owner rule and one height encoding. No independent
per-chunk stretching/normalization, clamped missing terrain or copied foliage.
Uncovered chunks are reported, not filled or silently called complete.
"""
import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.ndimage import map_coordinates

from build_colorado_catalog_evidence import ROOT, sha
from export_hance_evidence_runtime import write_png_u16

VERTICES=127
SPACING=2.
SPAN=(VERTICES-1)*SPACING
HEIGHT_BASE=200.
HEIGHT_RANGE=2400.


class SourceGridCache:
    """Bound decompressed source arrays, not source coverage or terrain detail."""
    def __init__(self,max_bytes=256*1024*1024):
        if type(max_bytes) is not int or max_bytes<=0:raise ValueError('Invalid source cache budget')
        self.max_bytes=max_bytes;self.resident_bytes=0;self.arrays=OrderedDict()

    def get(self,grid,key):
        stat=grid.path.stat()
        if (stat.st_size,stat.st_mtime_ns)!=grid.identity:
            raise ValueError('Source grid changed during terrain assembly')
        cache_key=(grid.path,key)
        if cache_key in self.arrays:
            self.arrays.move_to_end(cache_key);return self.arrays[cache_key]
        with np.load(grid.path,allow_pickle=False) as source:array=source[key]
        if array.nbytes<=self.max_bytes:
            while self.resident_bytes+array.nbytes>self.max_bytes:
                _,old=self.arrays.popitem(last=False);self.resident_bytes-=old.nbytes
            self.arrays[cache_key]=array;self.resident_bytes+=array.nbytes
        return array


class LazySourceGrid:
    def __init__(self,path,cache):
        self.path=Path(path).resolve();self.cache=cache
        stat=self.path.stat();self.identity=(stat.st_size,stat.st_mtime_ns)
        # Read the small NPY header, not every decompressed bed just to obtain
        # its geographic footprint. Generated NPZ sources use header v1 or v2.
        with ZipFile(self.path) as archive,archive.open('bed_ellipsoid_m.npy') as stream:
            version=np.lib.format.read_magic(stream)
            if version==(1,0):shape,_,dtype=np.lib.format.read_array_header_1_0(stream)
            elif version==(2,0):shape,_,dtype=np.lib.format.read_array_header_2_0(stream)
            else:raise ValueError('Unsupported source array header')
        if len(shape)!=2 or min(shape)<=0 or dtype.kind!='f':raise ValueError('Invalid source bed shape/type')
        self.bed_shape=shape

    def __getitem__(self,key):return self.cache.get(self,key)


def encode_height(height):
    if not np.isfinite(height).all() or np.any(height<HEIGHT_BASE) or np.any(height>HEIGHT_BASE+HEIGHT_RANGE):
        raise ValueError('Missing terrain or height outside common encoding; never clamp')
    return np.rint((height-HEIGHT_BASE)/HEIGHT_RANGE*65535).astype('uint16')


class TerrainMosaic:
    def __init__(self,sources):
        self.sources=sorted(sources,key=lambda s:s['core'][0])
        if len({tuple(s['core']) for s in self.sources})!=len(self.sources):
            raise ValueError('Duplicate source cores')
        bounds=[]
        for source in self.sources:
            if 'bounds' in source:x,y,h,w=source['bounds']
            else:
                x,y=source['grid']['corner_east_north_m']
                h,w=source['grid']['bed_ellipsoid_m'].shape
            if not np.isfinite([x,y,h,w]).all() or min(h,w)<=0:
                raise ValueError('Invalid source terrain footprint')
            bounds.append([x,y-h,x+w,y])
        self.bounds=np.asarray(bounds,dtype=float).reshape(-1,4)

    def candidate_indices(self,east,north):
        # A Landscape chunk is tiny compared with the full 453 km river. Test
        # the batch bounding box once, instead of allocating a full per-query
        # coverage mask for hundreds of geographically irrelevant sources.
        # Preserve global indices/order: overlapping-core ownership is unchanged.
        finite=np.isfinite(east)&np.isfinite(north)
        if not finite.any():return np.empty(0,dtype=int)
        x0,x1=east[finite].min(),east[finite].max()
        y0,y1=north[finite].min(),north[finite].max()
        b=self.bounds
        return np.flatnonzero((b[:,0]<=x1)&(b[:,2]>=x0)&(b[:,1]<=y1)&(b[:,3]>=y0))

    def sample(self,east,north):
        east,north=np.broadcast_arrays(np.asarray(east,dtype=float),np.asarray(north,dtype=float))
        height=np.full(east.shape,np.nan)
        owner=np.full(east.shape,-1,dtype=np.int32)
        score=np.full(east.shape,np.inf)
        for index in self.candidate_indices(east,north):
            source=self.sources[index]
            g=source['grid']
            if 'bounds' in source:x,y,h,w=source['bounds']
            else:
                x,y=g['corner_east_north_m'];h,w=g['bed_ellipsoid_m'].shape
            # The grid is cell-centred. Only the existing outer half-cell uses
            # its adjacent sample, matching the source export convention.
            covered=(east>=x)&(east<=x+w)&(north>=y-h)&(north<=y)
            if not covered.any():continue
            # Sample only this source's geographic footprint. The full-river
            # query array can be orders of magnitude larger than one raster.
            positions=np.flatnonzero(covered)
            rows=np.clip(y-north[covered]-.5,0,h-1);cols=np.clip(east[covered]-x-.5,0,w-1)
            st=map_coordinates(g['station_m'],[rows,cols],order=1,mode='nearest',prefilter=False)+source['origin']
            start,end=source['core']
            distance=np.maximum(start-st,0)+np.maximum(st-end,0)
            take=distance<score[covered]
            if not take.any():continue
            z=map_coordinates(g['bed_ellipsoid_m'],[rows[take],cols[take]],order=1,mode='nearest',prefilter=False)
            if not np.isfinite(z).all():raise ValueError('Nonfinite source terrain')
            height.flat[positions[take]]=z;score.flat[positions[take]]=distance[take];owner.flat[positions[take]]=index
        return height,owner


def load_sources(evidence,profiles,bounded=False):
    if len(evidence)!=len(profiles) or not evidence:raise ValueError('One profile per evidence grid required')
    sources=[];cache=SourceGridCache() if bounded else None
    for folder,profile_path in zip(evidence,profiles):
        folder=folder.resolve();profile_path=profile_path.resolve()
        m=json.loads((folder/'manifest.json').read_text());p=json.loads(profile_path.read_text())
        if (p.get('schema')!='raftsim.colorado_continuous_source_window.v1' or
                m['horizontal_crs']!='EPSG:6404' or m['vertical_datum']!='NAD83(2011) ellipsoid' or
                m['source_files_sha256'].get(str(profile_path.relative_to(ROOT)))!=sha(profile_path) or
                m['evidence_grid_sha256']!=sha(folder/'evidence_grid.npz')):
            raise ValueError('Unregistered source profile/grid')
        if bounded:g=LazySourceGrid(folder/'evidence_grid.npz',cache)
        else:
            with np.load(folder/'evidence_grid.npz',allow_pickle=False) as source:g=dict(source)
        if not np.array_equal(g['cell_m'],[1,1]):raise ValueError('Expected one metre source grid')
        shape=g.bed_shape if bounded else g['bed_ellipsoid_m'].shape
        sources.append(dict(grid=g,bounds=(*g['corner_east_north_m'],*shape),
            core=p['source_core_interval_m'],origin=p['source_halo_interval_m'][0],
            receipt=dict(evidence=folder.relative_to(ROOT).as_posix(),
                         evidence_manifest_sha256=sha(folder/'manifest.json'),
                         profile=profile_path.relative_to(ROOT).as_posix(),profile_sha256=sha(profile_path))))
    return sources


class LandscapeTriangles:
    """Sample the encoded, common-grid UE triangle surface, not the source DEM."""
    def __init__(self,folder):
        from PIL import Image
        self.folder=Path(folder).resolve()
        manifest_bytes=(self.folder/'manifest.json').read_bytes()
        self.manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest()
        self.manifest=json.loads(manifest_bytes)
        m=self.manifest;layout=m['landscape']
        generic=m.get('schema')=='raftsim.continuous_landscape.v1'
        futaleufu=generic and m.get('river_id')=='futaleufu_river_chile'
        height_base=0. if futaleufu else HEIGHT_BASE
        if generic:
            frames={'chilko_river_bc':('EPSG:3157','CGVD2013 (EPSG:6647)'),
                    'futaleufu_river_chile':('EPSG:32718','EGM2008')}
            if (m.get('river_id') not in frames or
                    (m.get('horizontal_crs'),m.get('vertical_reference'))!=frames.get(m.get('river_id')) or
                    'horizontal_origin_epsg6404_m' in m or 'height_base_ellipsoid_m' in layout):
                raise ValueError('Unsupported continuous river geographic frame')
        elif m.get('schema')!='raftsim.colorado_continuous_landscape.v1':
            raise ValueError('Unsupported common Landscape schema')
        self.spacing=layout['spacing_m'];self.span=(VERTICES-1)*self.spacing
        if (
                layout['vertices']!=VERTICES or isinstance(self.spacing,bool) or
                self.spacing not in ((1.,2.) if generic else (SPACING,)) or
                layout['span_m']!=self.span or layout['height_base_m' if generic else 'height_base_ellipsoid_m']!=height_base or
                layout['height_range_m']!=HEIGHT_RANGE):
            raise ValueError('Unsupported common Landscape layout')
        origin=np.asarray(m['horizontal_origin_m' if generic else 'horizontal_origin_epsg6404_m'],dtype=float)
        if origin.shape!=(2,) or not np.isfinite(origin).all():raise ValueError('Invalid geographic origin')
        self.chunks=[];self.by_index={};self.origin=origin;encoded_by_index={}
        for chunk in m['chunks']:
            index=tuple(chunk['chunk']);name=chunk['heightfield'];path=self.folder/name
            if len(index)!=2 or any(type(i)!=int for i in index) or index in encoded_by_index:
                raise ValueError('Invalid or duplicate chunk')
            if path.parent!=self.folder or path.suffix!='.png' or sha(path)!=chunk['sha256']:
                raise ValueError('Changed or unsafe heightfield')
            with Image.open(path) as image:encoded=np.array(image)
            if (encoded.shape!=(VERTICES,VERTICES) or encoded.dtype.kind not in 'ui' or
                    np.any(encoded<0) or np.any(encoded>65535)):
                raise ValueError('Invalid height samples')
            corner=origin+np.array([index[0],index[1]+1])*self.span
            if not np.array_equal(corner,chunk['origin_m' if generic else 'origin_epsg6404_m']):
                raise ValueError('Chunk shifted off common geographic lattice')
            encoded_by_index[index]=encoded
            surface=(corner,height_base+encoded.astype(float)*HEIGHT_RANGE/65535)
            self.chunks.append(surface);self.by_index[index]=surface
        if not self.chunks:raise ValueError('Empty terrain assembly')
        indices=np.array(list(self.by_index),dtype=np.int64)
        self.index_min=indices.min(axis=0);self.index_max=indices.max(axis=0)
        self.index_width=int(self.index_max[0]-self.index_min[0]+1)
        self.by_key={int(i-self.index_min[0]+self.index_width*(j-self.index_min[1])):surface
                     for (i,j),surface in self.by_index.items()}
        for (i,j),encoded in encoded_by_index.items():
            left=encoded_by_index.get((i-1,j));below=encoded_by_index.get((i,j-1))
            if ((left is not None and not np.array_equal(encoded[:,0],left[:,-1])) or
                    (below is not None and not np.array_equal(encoded[-1,:],below[0,:]))):
                raise ValueError('Decoded Landscape boundary is discontinuous')

    def verify_unchanged(self):
        """Close a reused sampling batch against the exact loaded snapshot."""
        if sha(self.folder/'manifest.json')!=self.manifest_sha256:
            raise ValueError('Terrain manifest changed after snapshot')
        for chunk in self.manifest['chunks']:
            if sha(self.folder/chunk['heightfield'])!=chunk['sha256']:
                raise ValueError('Terrain heightfield changed after snapshot')

    def sample(self,xy):
        from export_colorado_catalog_runtime import landscape_sample
        xy=np.asarray(xy,dtype=float)
        if not xy.ndim or xy.shape[-1]!=2:raise ValueError('Expected east/north queries')
        shape=xy.shape[:-1];points=xy.reshape(-1,2);result=np.full(len(points),np.nan)
        # Bound before integer conversion, including nonfinite/extreme inputs.
        finite=np.isfinite(points).all(axis=1)
        lower=self.origin+self.index_min*self.span
        upper=self.origin+(self.index_max+1)*self.span
        selected=np.flatnonzero(finite&(points>=lower).all(axis=1)&(points<=upper).all(axis=1))
        indices=np.floor((points[selected]-self.origin)/self.span).astype(np.int64)
        # Interior queries visit one tile. An exact upper edge can belong to a
        # missing tile, so try its lower neighbours without extrapolating.
        for offset in ((0,0),(-1,0),(0,-1),(-1,-1)):
            pending=np.isnan(result[selected]);query=selected[pending]
            cell=indices[pending]+offset
            valid=(cell>=self.index_min).all(axis=1)&(cell<=self.index_max).all(axis=1)
            query= query[valid];cell=cell[valid]
            if not len(query):continue
            keys=cell[:,0]-self.index_min[0]+self.index_width*(cell[:,1]-self.index_min[1])
            order=np.argsort(keys);keys=keys[order];query=query[order]
            starts=np.r_[0,np.flatnonzero(np.diff(keys))+1];ends=np.r_[starts[1:],len(keys)]
            for start,end in zip(starts,ends):
                surface=self.by_key.get(int(keys[start]))
                if surface is None:continue
                corner,height=surface;take=query[start:end];p=points[take]
                rows=(corner[1]-p[:,1])/self.spacing;cols=(p[:,0]-corner[0])/self.spacing
                inside=(rows>=0)&(rows<=VERTICES-1)&(cols>=0)&(cols<=VERTICES-1)
                if inside.any():result[take[inside]]=landscape_sample(height,rows[inside],cols[inside])
        return result.reshape(shape)


def export(evidence,profiles,route_path,out):
    if out.exists():raise ValueError('Fresh terrain export required')
    route=json.loads(route_path.read_text())
    if route.get('world_y_sign')!=-1 or route.get('vertical_reference')!='NAD83(2011) ellipsoid heights':
        raise ValueError('Wrong world frame')
    origin=np.asarray(route['horizontal_origin_epsg6404_m']);datum=route['vertical_datum_m']
    mosaic=TerrainMosaic(load_sources(evidence,profiles,bounded=True))
    candidates=set()
    for s in mosaic.sources:
        x,y,h,w=s['bounds']
        lo=np.floor((np.array([x,y-h])-origin)/SPAN).astype(int)
        hi=np.floor((np.array([x+w,y])-origin)/SPAN).astype(int)
        candidates.update((i,j) for i in range(lo[0],hi[0]+1) for j in range(lo[1],hi[1]+1))
    out.mkdir(parents=True)
    chunks=[];missing=[];edges={};max_edge_delta=0
    for i,j in sorted(candidates):
        x0,y0=origin+np.array([i,j])*SPAN
        east,north=np.meshgrid(x0+np.arange(VERTICES)*SPACING,y0+SPAN-np.arange(VERTICES)*SPACING)
        heights,owners=mosaic.sample(east,north)
        if np.any(owners<0):
            missing.append(dict(chunk=[i,j],missing_vertices=int((owners<0).sum())))
            continue
        encoded=encode_height(heights)
        for neighbour,edge,other in [((i-1,j),encoded[:,0],'east'),((i,j-1),encoded[-1,:],'north')]:
            if neighbour in edges:
                delta=int(np.abs(edge.astype(int)-edges[neighbour][other].astype(int)).max())
                max_edge_delta=max(max_edge_delta,delta)
                if delta:raise ValueError('Adjacent Landscape edges disagree')
        edges[i,j]=dict(east=encoded[:,-1],north=encoded[0,:])
        name=f'height_{i}_{j}.png';write_png_u16(out/name,encoded)
        chunks.append(dict(chunk=[i,j],heightfield=name,sha256=sha(out/name),
            origin_epsg6404_m=[float(x0),float(y0+SPAN)],
            world_northwest_xy_cm=[float((x0-origin[0])*100),float((origin[1]-y0-SPAN)*100)],
            source_owner_indices=np.unique(owners).tolist()))
    if not chunks:raise ValueError('No completely source-backed terrain chunks')
    result=dict(schema='raftsim.colorado_continuous_landscape.v1',
        route_coordinate_map=str(route_path),route_sha256=sha(route_path),
        horizontal_origin_epsg6404_m=origin.tolist(),vertical_datum_m=datum,
        source_inputs=[s['receipt'] for s in mosaic.sources],
        landscape=dict(vertices=VERTICES,spacing_m=SPACING,span_m=SPAN,
            subsections_per_component=2,quads_per_subsection=63,
            height_base_ellipsoid_m=HEIGHT_BASE,height_range_m=HEIGHT_RANGE,
            # UE landscape signed height maps encoded 32768 to actor Z.
            actor_z_cm=(HEIGHT_BASE+HEIGHT_RANGE*32768/65535-datum)*100,
            scale_xyz=[SPACING*100,SPACING*100,HEIGHT_RANGE*100/512*65536/65535]),
        shared_edge_max_encoded_difference=max_edge_delta,chunks=chunks,
        incomplete_source_chunks=missing,
        scope='Canonical source-derived terrain only; bed inference retained; collision/engine review still required',
        vegetation_complete=False,engine_validated=False,full_river_complete=False)
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,action='append',required=True)
    p.add_argument('--profile',type=Path,action='append',required=True)
    p.add_argument('--route',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=export(a.evidence,a.profile,a.route,a.out)
    print(json.dumps(dict(chunks=len(r['chunks']),incomplete_chunks=len(r['incomplete_source_chunks']),
                         shared_edge_max_encoded_difference=r['shared_edge_max_encoded_difference'])))
