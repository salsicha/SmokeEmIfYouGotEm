"""Source-verified candidate solid union; no water-state mutation or promotion."""
import hashlib
import json
from pathlib import Path
import numpy as np
from build_troublemaker_dem_rock_cap import sample_cap, close_cap_below_retained_terrain


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SourceRockUnion:
    """Maximum of retained terrain and a source-exact roof with inferred sides.

    Inputs/outputs use absolute UTM / NAVD88 metres. Owner 5 means candidate
    solid, NOT measured rock classification. Unsupported cap XY retains the
    original bed. Source water masks/stages are never changed here.
    """
    def __init__(self, manifest_path, root, parent_path, origin_utm_m, datum_m):
        root=Path(root).resolve();manifest_path=Path(manifest_path).resolve()
        self.manifest=json.loads(manifest_path.read_text())
        m=self.manifest
        if m.get('schema')!='raftsim.original_return_rock_cap.v1':
            raise ValueError('Explicit original-return solid schema required')
        self.origin=np.asarray(m['origin_utm_and_vertical_datum_m'],float)
        if not np.array_equal(self.origin,np.r_[origin_utm_m,datum_m]):
            raise ValueError('Cap and retained terrain coordinate frames differ')
        paths={}
        for name in ('source_mesh','original_returns','cap'):
            path=(root/m[name+'_path']).resolve()
            if not path.is_relative_to(root) or sha(path)!=m[name+'_sha256']:
                raise ValueError('Changed or out-of-repository cap dependency: '+name)
            paths[name]=path
        if paths['source_mesh']!=Path(parent_path).resolve():
            raise ValueError('Cap belongs to a different retained terrain')
        selection=m.get('reviewed_extension_selection')
        if selection is not None:
            selection_path=(root/selection['path']).resolve()
            if not selection_path.is_relative_to(root) or sha(selection_path)!=selection['sha256']:
                raise ValueError('Changed or out-of-repository interpreted selection')
            review=json.loads(selection_path.read_text())
            if review.get('schema')!='raftsim.interpreted_source_selection.v1':
                raise ValueError('Explicit interpreted source selection required')
            if review.get('measured_outline') is not False or review.get('measured_flanks') is not False:
                raise ValueError('Interpreted selection cannot claim measured geometry')
            for key in ('source_mesh_sha256','original_returns_sha256','source_naip_sha256',
                        'source_naip_export_sha256','origin_utm_and_vertical_datum_m'):
                if review.get(key)!=m.get(key):
                    raise ValueError('Interpreted selection source/frame mismatch: '+key)
        with np.load(paths['cap'],allow_pickle=False) as data:
            self.xyz=data['vertices_m'].copy();self.faces=data['triangles'].copy()
            ids=data['original_return_index']
            with np.load(paths['original_returns'],allow_pickle=False) as source:
                original=np.column_stack([source[k][ids] for k in
                    ('utm_easting_m','utm_northing_m','navd88_m')])
                if not np.array_equal(self.xyz,original-self.origin):
                    raise ValueError('Candidate moved an original source vertex')
                if not np.array_equal(data['original_classification'],source['classification'][ids]):
                    raise ValueError('Candidate relabelled source classification')
                if not np.isin(data['original_classification'],[1,2,10]).all():
                    raise ValueError('Excluded source class in rock interpretation')
            self.floor=float(m['inferred_solid']['internal_floor_m'])
            with np.load(paths['source_mesh'],allow_pickle=False) as parent:
                if self.floor>=float(parent['z_m'].min()):
                    raise ValueError('Solid floor is not below the retained terrain')
            vertices,faces,kinds,_=close_cap_below_retained_terrain(self.xyz,self.faces,self.floor)
            if not (np.array_equal(vertices,data['solid_vertices_m']) and
                    np.array_equal(faces,data['solid_triangles']) and
                    np.array_equal(kinds,data['solid_face_kind'])):
                raise ValueError('Collision solid and hydraulic roof do not match')
        self.lower=self.xyz[:,:2].min(axis=0)+self.origin[:2]
        self.upper=self.xyz[:,:2].max(axis=0)+self.origin[:2]
        self.identity=dict(schema='raftsim.retained_terrain_rock_union.v1',
            cap_manifest_sha256=sha(manifest_path),
            parent_geometry_sha256=m['source_mesh_sha256'],cap_sha256=m['cap_sha256'],
            original_returns_sha256=m['original_returns_sha256'],
            operation='vertical solid union: maximum retained terrain and source roof',
            original_terrain_modified=False,flanks_measured=False,
            hydraulics_recooked=False,playable_integrated=False)
        if selection is not None:
            self.identity['interpreted_selection_sha256']=selection['sha256']

    def apply(self,east,north,parent):
        east,north,parent=np.broadcast_arrays(np.asarray(east,float),np.asarray(north,float),np.asarray(parent,float))
        if not np.isfinite([east,north,parent]).all():
            raise ValueError('Finite coordinates and retained terrain required')
        shape=parent.shape;out=parent.ravel().copy();changed=np.zeros(out.shape,bool)
        xy=np.column_stack((east.ravel(),north.ravel()))
        candidates=np.flatnonzero(np.all(xy>=self.lower,axis=1)&np.all(xy<=self.upper,axis=1))
        if len(candidates):
            roof=sample_cap(self.xyz,self.faces,xy[candidates]-self.origin[:2])+self.origin[2]
            supported=np.isfinite(roof)
            if np.any(out[candidates[supported]]<=self.floor+self.origin[2]):
                raise ValueError('Candidate bottom exposed outside retained solid')
            take=supported&(roof>out[candidates])
            out[candidates[take]]=roof[take];changed[candidates[take]]=True
        return out.reshape(shape),changed.reshape(shape)
