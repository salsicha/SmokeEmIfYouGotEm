"""Explicit geometry identity for regular and captured-XY review candidates.

An irregular mesh must never fall through to a raster sampler. Its hash covers
coordinates AND triangle connectivity; the same source is used by FBX and FV.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

REGISTERED_SCHEMA = 'raftsim.captured_rock_xy_mesh_candidate.v1'
SOURCE_EXTENSION_SCHEMA = 'raftsim.constriction_source_candidate.v1'


def geometry_identity(manifest_path, root, expected_sha=None):
    root = Path(root).resolve()
    source = json.loads(Path(manifest_path).read_text())
    registered = source.get('schema') in (REGISTERED_SCHEMA, SOURCE_EXTENSION_SCHEMA)
    path_key, hash_key = ('mesh_path', 'mesh_sha256') if registered else ('shared_geometry_path', 'shared_geometry_sha256')
    path = (root/source[path_key]).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Geometry source is outside the project')
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != source[hash_key] or (expected_sha is not None and actual != expected_sha):
        raise ValueError('Rendered geometry no longer matches the cooked source')
    return source, path, actual, registered


def load_registered_mesh(path):
    from south_fork_registered_mesh import RegisteredMeshSampler
    with np.load(path, allow_pickle=False) as packed:
        data = {k: packed[k].copy() for k in packed.files}
    return data, RegisteredMeshSampler(data)


def require_sampling_kind(registered, method):
    if registered != (method == 'registered_triangles'):
        raise ValueError('Registered XY geometry requires explicit registered_triangles sampling; raster modes are incompatible')
