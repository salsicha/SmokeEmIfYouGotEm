"""Resolve versioned native diagnostic inputs; never guess from scene names."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACKAGES={
    'core-v1':('south-fork-whole-rapid-liquid-float-seeds-20260910',
        'south-fork-liquid-regional-state-20260910','south-fork-liquid-regional-geometry-v4-20260910',
        'south-fork-liquid-face-bed-20260910'),
    'reservoir-v1':('south-fork-liquid-reservoir-window-20260910',
        'south-fork-liquid-reservoir-regions-20260910','south-fork-liquid-reservoir-geometry-20260910',
        'south-fork-liquid-reservoir-face-bed-20260910')}


def resolve(report=None, *, key=None, root=ROOT):
    evidence=(report or {}).get('native_dataset')
    if report is not None and 'native_dataset' in report and evidence is None:
        raise ValueError('Null native dataset descriptor is not a legacy capture')
    if evidence is not None:
        if not isinstance(evidence,dict) or (key is not None and key!=evidence.get('key')):
            raise ValueError('Conflicting native dataset identity')
        key=evidence.get('key')
    elif key is None:
        key='core-v1' # legacy captures predate explicit dataset selection
    if key not in PACKAGES:raise ValueError('Unknown native dataset; no path fallback')
    parent,regions,geometry,bed=(Path(root)/'tmp'/s for s in PACKAGES[key])
    paths=dict(key=key,parent=parent,regions=regions,geometry=geometry,face_bed=bed/'physical_face_bed.json',
        mesh=Path(root)/'tmp/south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz')
    if evidence is not None:
        for field,path in (('parent_manifest_sha256',parent/'manifest.json'),
            ('ownership_manifest_sha256',regions/'manifest.json'),('geometry_manifest_sha256',geometry/'manifest.json'),
            ('face_bed_sha256',paths['face_bed'])):
            expected=evidence.get(field)
            if not isinstance(expected,str) or len(expected)!=64 or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError('Native dataset input changed: '+field)
    return paths
