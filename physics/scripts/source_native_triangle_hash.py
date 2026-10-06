"""Independent reproduction of RaftSimGroundSourceLibrary's directed hash.

All float32 source coordinates and material indices participate. Renumbering
and cyclic corner rotation are permitted; reversed winding or changed geometry
are not. Export/import roundoff must be investigated, never silently rounded.
"""
import hashlib
import numpy as np


def triangle_hash(vertices, faces, materials=None):
    vertices, faces = np.asarray(vertices), np.asarray(faces)
    if (vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all()
            or faces.ndim != 2 or faces.shape[1] != 3 or not np.issubdtype(faces.dtype, np.integer)
            or not len(faces) or faces.min() < 0 or faces.max() >= len(vertices)):
        raise ValueError('Finite source vertices and complete indexed triangles required')
    materials = np.zeros(len(faces), dtype='<u4') if materials is None else np.asarray(materials)
    if (materials.shape != (len(faces),) or not np.issubdtype(materials.dtype, np.integer)
            or materials.min() < 0 or materials.max() > np.iinfo(np.uint32).max):
        raise ValueError('One uint32 material index per triangle required')
    points = np.ascontiguousarray(vertices[faces], dtype='<f4')
    if not np.isfinite(points).all():
        raise ValueError('Source coordinates exceed float32 range')
    packed = points.view('S12').reshape(-1, 3)
    first = np.argmin(packed, axis=1)
    # Degenerate duplicate vertices cannot have a unique least corner; native
    # code compares complete rotations. Resolve only those ties explicitly.
    rotations = points[np.arange(len(points))[:, None], (first[:, None]+np.arange(3)) % 3]
    raw = np.zeros((len(faces), 40), dtype=np.uint8)
    raw[:, :36] = np.ascontiguousarray(rotations).view(np.uint8).reshape(-1, 36)
    raw[:, 36:] = materials.astype('<u4').view(np.uint8).reshape(-1, 4)
    tied = np.sum(packed == packed[np.arange(len(packed)), first, None], axis=1) > 1
    for i in np.flatnonzero(tied):
        corners = [points[i, j].tobytes() for j in range(3)]
        raw[i, :36] = np.frombuffer(min(b''.join(corners[j:]+corners[:j]) for j in range(3)), np.uint8)
    records = np.sort(raw.view('V40').ravel())
    return hashlib.sha256(records.tobytes()).hexdigest()
