"""Prove immutable source windows still fit a replacement shared chart exactly.

No field is reprojected. Changed positions, normals, curvature or source
stationing inside any used window require rebuilding that window instead.
"""
import json
from pathlib import Path
import numpy as np
from anchor_colorado_terminal_frame import checked_arrays
from build_colorado_catalog_evidence import ROOT,sha


class SharedFrameCompatibility:
    def __init__(self,directory):
        self.cache={};self.protected={};self.records=[]
        path=Path(directory).resolve()/'manifest.json';path.relative_to(ROOT)
        self.receipt=dict(manifest=path.relative_to(ROOT).as_posix(),sha256=sha(path))
        self.target=self._load(self.receipt)

    def _load(self,spec):
        path=ROOT/spec['manifest'];key=(str(path.resolve()),spec['sha256'])
        if key in self.cache:return self.cache[key]
        if sha(path)!=spec['sha256']:raise ValueError('Changed source chart manifest')
        manifest=json.loads(path.read_text())
        if manifest.get('schema')!='raftsim.colorado_shared_hydraulic_frame.v1' or manifest.get('grid_step_m')!=2:
            raise ValueError('Expected registered two-metre shared chart')
        self.protected[path]=spec['sha256']
        for name in ('frame.npz','coordinate_map.json'):
            p=path.parent/name;digest=sha(p)
            if digest!=manifest['files_sha256'][name]:raise ValueError('Changed source chart file')
            self.protected[p]=digest
        source=ROOT/manifest['source_profile'];digest=sha(source)
        if digest!=manifest['source_profile_sha256']:raise ValueError('Changed captured chart source')
        self.protected[source]=digest
        with np.load(path.parent/'frame.npz',allow_pickle=False) as saved:arrays=checked_arrays(dict(saved))
        mapping=json.loads((path.parent/'coordinate_map.json').read_text())
        points=np.asarray(mapping.pop('points'),dtype=float);mapping.pop('mapping_policy',None)
        if (points.ndim!=2 or points.shape[1]!=5 or not np.isfinite(points).all() or
                np.any(np.diff(points[:,0])<=0)):
            raise ValueError('Invalid registered coordinate map')
        result=dict(manifest=manifest,arrays=arrays,mapping=mapping,points=points)
        self.cache[key]=result
        return result

    @staticmethod
    def _indices(available,required):
        indices=np.searchsorted(available,required)
        if np.any(indices>=len(available)) or not np.array_equal(available[indices],required):
            raise ValueError('Source window is not on the replacement shared lattice')
        return indices

    def check(self,report,grid):
        old=self._load(report['shared_hydraulic_frame']);new=self.target
        if (old['mapping']!=new['mapping'] or any(old['manifest'][k]!=new['manifest'][k]
                for k in ('source_profile','source_profile_sha256','grid_step_m'))):
            raise ValueError('Replacement changes the registered geographic frame or captured source')
        if report['files_sha256']['coordinate_map.json']!=old['manifest']['files_sha256']['coordinate_map.json']:
            raise ValueError('Input coordinate map is not its registered shared map')
        if (not isinstance(grid['nx'],int) or grid['nx']<2 or grid['dx']!=2 or grid['dy']!=2 or
                not np.isfinite(grid['origin_x'])):raise ValueError('Invalid source lattice')
        station=grid['origin_x']+np.arange(grid['nx'])*grid['dx']
        first=self._indices(old['arrays']['station_m'],station)
        second=self._indices(new['arrays']['station_m'],station)
        for key in old['arrays']:
            if not np.array_equal(old['arrays'][key][first],new['arrays'][key][second]):
                raise ValueError('Source chart changed inside used window; rebuild input: '+key)
        first=self._indices(old['points'][:,0],station);second=self._indices(new['points'][:,0],station)
        if not np.array_equal(old['points'][first],new['points'][second]):
            raise ValueError('Rendered coordinate map changed inside used window; rebuild input')
        record=dict(source_shared_frame=report['shared_hydraulic_frame'],
            hydraulic_station_range_m=[float(station[0]),float(station[-1])],
            checked_columns=len(station),all_frame_arrays_and_render_coordinates_bit_identical=True)
        self.records.append(record)
        return record

    def verify_unchanged(self):
        if any(sha(p)!=h for p,h in self.protected.items()):
            raise ValueError('Shared chart dependency changed during join')
