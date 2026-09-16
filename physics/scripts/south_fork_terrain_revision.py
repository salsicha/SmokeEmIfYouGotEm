"""Exact registered-bed replacement, applied before the retained rock union.

Only original authority-2 submerged-prior heights may differ. This operator
never adds a second ground surface or transfers a state across changed beds.
"""
import json
from pathlib import Path
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_geometry_source import geometry_identity


class RegisteredTerrainRevision:
    def __init__(self, original, revised, origin, datum):
        if set(original) != set(revised):
            raise ValueError('Terrain revision changed source fields')
        for key in original:
            if original[key].dtype != revised[key].dtype or original[key].shape != revised[key].shape:
                raise ValueError('Terrain revision changed field type/shape: '+key)
            if key != 'z_m' and not np.array_equal(original[key], revised[key]):
                raise ValueError('Terrain revision changed protected field: '+key)
        changed = original['z_m'] != revised['z_m']
        if np.any(changed & (original['authority'] != 2)):
            raise ValueError('Only original submerged-prior heights may change')
        if changed[0].any() or changed[-1].any() or changed[:,0].any() or changed[:,-1].any():
            raise ValueError('Revision changed the retained rapid/seam boundary')
        if not changed.any():
            raise ValueError('Terrain revision is empty')
        self.original = RegisteredMeshSampler(original)
        self.revised = RegisteredMeshSampler(revised)
        self.origin = np.asarray(origin, float)
        self.datum = float(datum)
        if self.origin.shape != (2,) or not np.isfinite(self.origin).all() or not np.isfinite(self.datum):
            raise ValueError('Finite metric source frame required')
        faces = self.original.faces[np.any(changed.ravel()[self.original.faces], axis=1)]
        affected = self.original.xyz[np.unique(faces), :2]
        self.lower = affected.min(axis=0)+self.origin
        self.upper = affected.max(axis=0)+self.origin
        self.changed_vertices = int(changed.sum())

    def apply(self, east, north, parent):
        east, north, parent = np.broadcast_arrays(np.asarray(east,float), np.asarray(north,float), np.asarray(parent,float))
        if not np.isfinite([east,north,parent]).all():
            raise ValueError('Finite source coordinates and bed required')
        xy = np.column_stack((east.ravel(), north.ravel()))
        ids = np.flatnonzero(np.all(xy >= self.lower,axis=1) & np.all(xy <= self.upper,axis=1))
        out = parent.ravel().copy()
        if len(ids):
            local = xy[ids]-self.origin
            before = self.original.sample(*local.T)+self.datum
            if not np.array_equal(before, out[ids]):
                raise ValueError('Replacement input is not the exact retained registered bed')
            out[ids] = self.revised.sample(*local.T)+self.datum
        return out.reshape(parent.shape), (out != parent.ravel()).reshape(parent.shape)


def load_revision(manifest_path, root, original_path, origin, datum):
    import hashlib
    root = Path(root).resolve()
    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_relative_to(root):
        raise ValueError('Revision manifest escapes project')
    record, revised_path, revised_sha, registered = geometry_identity(manifest_path, root)
    original_path = Path(original_path).resolve()
    original_sha = hashlib.sha256(original_path.read_bytes()).hexdigest()
    if (not registered or record.get('parent_mesh_sha256') != original_sha
            or record.get('origin_utm_m') != list(origin)
            or record.get('vertical_origin_navd88_m') != datum):
        raise ValueError('Revision does not belong to this retained geometry/frame')
    with np.load(original_path,allow_pickle=False) as data:
        original = {k:data[k].copy() for k in data.files}
    with np.load(revised_path,allow_pickle=False) as data:
        revised = {k:data[k].copy() for k in data.files}
    revision = RegisteredTerrainRevision(original, revised, origin, datum)
    revision.identity = dict(schema='raftsim.registered_submerged_bed_revision.v1',
        manifest=manifest_path.relative_to(root).as_posix(),
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        original_geometry_sha256=original_sha, revised_geometry_sha256=revised_sha,
        mesh_path=revised_path.relative_to(root).as_posix(),
        changed_vertices=revision.changed_vertices, captured_vertices_unchanged=True,
        registered_xy_and_topology_unchanged=True, rapid_seam_boundary_unchanged=True,
        measured_bathymetry=False, state_transfer_permitted=False)
    return revision
