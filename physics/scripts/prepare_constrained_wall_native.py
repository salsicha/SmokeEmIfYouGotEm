"""Prepare every-face probes and an exact directed native collision fingerprint."""
import hashlib
import json
import struct
import numpy as np
from build_troublemaker_dem_rock_cap import ROOT
from south_fork_rock_union import sha


def fingerprint(vertices,faces):
    records=[]
    for face in faces:
        corners=[struct.pack('<3f',*vertices[i]) for i in face]
        records.append(min(b''.join(corners[k:]+corners[:k]) for k in range(3))+struct.pack('<I',0))
    return hashlib.sha256(b''.join(sorted(records))).hexdigest()


def main():
    path=ROOT/'tmp/constrained-wall-orientation-probes-20260925.json'
    if path.exists():raise ValueError('Fresh output required')
    # Bind the rounding and winding convention to the earlier native baseline.
    with np.load(ROOT/'tmp/troublemaker-mixed-support-candidate-20260925/mixed_survey_rock_cap.npz') as old:
        assert fingerprint(old['solid_vertices_m']*100,old['solid_triangles'][:,[0,2,1]])=='3745f79c8609822b440fd085b0f718f051b1cf63d798e5156df64ba355ba6e69'
    directory=ROOT/'tmp/troublemaker-constrained-wall-export-20260925'
    export=json.loads((directory/'manifest.json').read_text())
    manifest=json.loads((ROOT/export['cap_manifest']).read_text());cap=ROOT/manifest['cap_path']
    assert sha(cap)==manifest['cap_sha256']==export['source_cap_sha256']
    with np.load(cap) as data:
        v=data['solid_vertices_m'];f=data['solid_triangles'];kinds=data['solid_face_kind']
        triangles=v[f];normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
        probes=[dict(face=i,kind=int(kinds[i]),position_cm=(t.mean(axis=0)*[100,-100,100]).tolist(),outward_normal=(normals[i]*[1,-1,1]).tolist()) for i,t in enumerate(triangles)]
        digest=fingerprint(v*100,f[:,[0,2,1]])
    config=dict(export_directory=directory.relative_to(ROOT).as_posix(),report='tmp/constrained-wall-native-orientation-20260925.json',
        source_cap_sha256=sha(cap),reversed_provider_sha256=digest,probes=probes)
    path.write_text(json.dumps(config)+'\n');print('Prepared',len(probes),'faces; native SHA256',digest)


if __name__=='__main__':main()
