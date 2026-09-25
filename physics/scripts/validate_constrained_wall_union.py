"""Bind the constrained candidate to the existing strict mixed-source loader."""
import json
import numpy as np
from build_troublemaker_dem_rock_cap import ROOT,PARENT,ORIGIN
from south_fork_rock_union import SourceRockUnion,sha


def main():
    directory=ROOT/'tmp/troublemaker-constrained-wall-extension-v1-20260925'
    output=directory/'rock_cap_manifest.json';validation=directory/'shared_union_validation.json'
    if output.exists() or validation.exists():raise ValueError('Fresh manifest and validation required')
    parent=ROOT/'tmp/troublemaker-mixed-support-candidate-20260925/rock_cap_manifest-v2.json'
    if sha(parent)!='1d37ed2dd4e9b53b55da3a76c8dc81ef9d811d389086b15a808b523492ec7558':raise ValueError('Parent manifest changed')
    m=json.loads(parent.read_text());receipt=directory/'report.json';report=json.loads(receipt.read_text())
    if report.get('preserved_boundary_constraints') is not True or not report['original_roof_exact'] or report['parent_cap_sha256']!=m['cap_sha256']:raise ValueError('Wrong construction receipt')
    cap=directory/'mixed_survey_rock_cap.npz'
    if sha(cap)!=report['cap_sha256']:raise ValueError('Constructed cap changed')
    m.update(status='unpromoted_constrained_exterior_support',cap_path=cap.relative_to(ROOT).as_posix(),cap_sha256=sha(cap),
        parent_manifest=dict(path=parent.relative_to(ROOT).as_posix(),sha256=sha(parent)),
        construction_receipt=dict(path=receipt.relative_to(ROOT).as_posix(),sha256=sha(receipt)),
        inferred_solid=dict(internal_floor_m=m['inferred_solid']['internal_floor_m'],**report['closure']))
    # The old record described one point. The archive now owns multiple exact
    # LAZ indices; do not retain a misleading single-point description.
    for key in ('las_point_index','source_xyz_m','classification','return_number','number_of_returns','gps_time'):
        m['independent_source'].pop(key,None)
    with np.load(cap) as data:
        m['independent_source']['las_point_indices']=sorted(set(map(int,data['source_point_index'][data['source_dataset']==1])))
    output.write_text(json.dumps(m,indent=2)+'\n')
    union=SourceRockUnion(output,ROOT,PARENT,ORIGIN[:2],ORIGIN[2])
    result=dict(manifest_sha256=sha(output),construction_sha256=sha(receipt),identity=union.identity,
        strict_source_coordinates_classes_and_solid_verified=True,hydraulics_recooked=False,
        native_collision_verified=False,playable_integrated=False)
    validation.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
