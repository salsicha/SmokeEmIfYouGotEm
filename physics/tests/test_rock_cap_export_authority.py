import hashlib
import json
import pytest
from rock_cap_export_authority import verify_export_authority


def test_matching_audit_required_and_mutations_rejected(tmp_path):
    cap=tmp_path/'cap.json';cap.write_text(json.dumps(dict(cap_sha256='cap',independent_source={'sha256':'survey'})))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    geometry=tmp_path/'geometry.json'
    geometry.write_text(json.dumps(dict(completed=True,rock_cap_manifest=cap.name,
        terrain_union=dict(cap_manifest_sha256=sha(cap),cap_sha256='cap',independent_source={'sha256':'survey'}))))
    audit=tmp_path/'source_exact_audit.json';audit.write_text(json.dumps(dict(passed=True,manifest_sha256=sha(geometry))))
    assert verify_export_authority(cap,geometry,tmp_path)['geometry_manifest_sha256']==sha(geometry)
    cap.write_text(cap.read_text()+' ')
    with pytest.raises(ValueError,match='lacks matching'):verify_export_authority(cap,geometry,tmp_path)
