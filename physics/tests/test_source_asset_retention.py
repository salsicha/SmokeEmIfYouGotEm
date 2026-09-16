import hashlib
import json
import pytest
from source_asset_retention import retained_asset_digest, IDENTITY


def fixture(tmp_path):
    path=tmp_path/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Ground.uasset'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'retained metadata')
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    before=dict(format='source_v1',collision_lod=0,collision_trace_flag=3,collision_source_sha256='b'*64,
                triangle_count=12,provider_vertex_count=24,flip_normals=True,available=True,allow_cpu_access=False)
    row=dict(asset='/Game/RaftSim/Environment/SouthForkReconstruction/Ground',original_asset_sha256='a'*64,
             retained_asset_sha256=actual,before=before,after=dict(before,allow_cpu_access=True),native_source_unchanged=True)
    document=dict(schema='raftsim.ground_cpu_retention.v1',completed=True,assets=[row])
    receipt=tmp_path/'receipt.json'
    return path,receipt,document,row


def test_unchanged_package_needs_no_exception(tmp_path):
    path,receipt,document,row=fixture(tmp_path)
    assert retained_asset_digest(path,row['retained_asset_sha256'],root=tmp_path,receipt=receipt)==row['retained_asset_sha256']


def test_forward_digest_preserves_exact_provenance_chain(tmp_path):
    path,receipt,document,row=fixture(tmp_path)
    receipt.write_text(json.dumps(document))
    assert retained_asset_digest(path,row['original_asset_sha256'],root=tmp_path,receipt=receipt)==row['retained_asset_sha256']


@pytest.mark.parametrize('field', IDENTITY)
def test_collision_change_is_never_waived(tmp_path,field):
    path,receipt,document,row=fixture(tmp_path)
    row['after'][field]='wrong'
    receipt.write_text(json.dumps(document))
    with pytest.raises(ValueError,match='identity changed'):
        retained_asset_digest(path,row['original_asset_sha256'],root=tmp_path,receipt=receipt)


@pytest.mark.parametrize('case',['partial','duplicate','new_package','new_original','no_cpu','false_proof'])
def test_stale_or_incomplete_receipts_refuse(tmp_path,case):
    path,receipt,document,row=fixture(tmp_path)
    original=row['original_asset_sha256']
    if case=='partial': document['completed']=False
    if case=='duplicate': document['assets'].append(dict(row))
    if case=='new_package': path.write_bytes(b'unrelated changed geometry')
    if case=='new_original': row['original_asset_sha256']='c'*64
    if case=='no_cpu': row['after']['allow_cpu_access']=False
    if case=='false_proof': row['native_source_unchanged']=False
    receipt.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        retained_asset_digest(path,original,root=tmp_path,receipt=receipt)
