"""Bind a mixed-source mesh export to a completed shared-union audit."""
import hashlib
import json
from pathlib import Path


def verify_export_authority(cap_manifest,geometry_manifest,root):
    root=Path(root).resolve()
    cap_manifest=Path(cap_manifest).resolve();geometry_manifest=Path(geometry_manifest).resolve()
    if not cap_manifest.is_relative_to(root) or not geometry_manifest.is_relative_to(root):
        raise ValueError('Export dependencies outside project')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    cap=json.loads(cap_manifest.read_text());geometry=json.loads(geometry_manifest.read_text())
    audit=json.loads((geometry_manifest.parent/'source_exact_audit.json').read_text())
    identity=geometry['terrain_union']
    if (audit.get('passed') is not True or audit['manifest_sha256']!=digest(geometry_manifest)
        or not geometry.get('completed') or (root/geometry['rock_cap_manifest']).resolve()!=cap_manifest
        or identity['cap_manifest_sha256']!=digest(cap_manifest)
        or identity['cap_sha256']!=cap['cap_sha256']
        or identity.get('independent_source',{}).get('sha256')!=cap['independent_source']['sha256']):
        raise ValueError('Mixed export lacks matching verified shared union')
    return dict(geometry_manifest=geometry_manifest.relative_to(root).as_posix(),
                geometry_manifest_sha256=digest(geometry_manifest),
                cap_manifest_sha256=digest(cap_manifest),
                source_audit_sha256=digest(geometry_manifest.parent/'source_exact_audit.json'))
