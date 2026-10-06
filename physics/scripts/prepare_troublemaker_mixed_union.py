"""Create and validate an uninstalled mixed-cap manifest for shared union use."""
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import SourceRockUnion,sha

ROOT=Path(__file__).resolve().parents[2]

def candidate_solid_metadata(old, receipt):
    """Keep only the retained floor; closure statistics belong to the new mesh."""
    return dict(internal_floor_m=old['inferred_solid']['internal_floor_m'],
                **receipt['closure'])

def main():
    directory=ROOT/'tmp/troublemaker-mixed-support-candidate-20260925'
    output=directory/'rock_cap_manifest-v2.json'
    if output.exists():raise ValueError('Manifest already exists')
    receipt_path=directory/'report.json'; receipt=json.loads(receipt_path.read_text())
    old_path=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/source_matched_20260917/rock_cap_manifest.json'
    old=json.loads(old_path.read_text());cap=directory/'mixed_survey_rock_cap.npz'
    if sha(cap)!=receipt['candidate_sha256'] or old['cap_sha256']!=receipt['parent_cap_sha256']:
        raise ValueError('Candidate/parent identity changed')
    keys=['source_mesh_path','source_mesh_sha256','original_returns_path','original_returns_sha256',
          'origin_utm_and_vertical_datum_m']
    manifest={k:old[k] for k in keys}
    manifest['inferred_solid']=candidate_solid_metadata(old,receipt)
    manifest.update(schema='raftsim.mixed_survey_rock_cap.v1',status='unpromoted_interpreted_local_support',
        cap_path=cap.relative_to(ROOT).as_posix(),cap_sha256=sha(cap),
        independent_source=receipt['independent_source'],
        parent_manifest=dict(path=old_path.relative_to(ROOT).as_posix(),sha256=sha(old_path)),
        construction_receipt=dict(path=receipt_path.relative_to(ROOT).as_posix(),sha256=sha(receipt_path)),
        measured_outline=False,measured_flanks=False,production_promoted=False)
    output.write_text(json.dumps(manifest,indent=2)+'\n')
    origin=np.asarray(manifest['origin_utm_and_vertical_datum_m'])
    union=SourceRockUnion(output,ROOT,ROOT/manifest['source_mesh_path'],origin[:2],origin[2])
    print(json.dumps(union.identity))

if __name__=='__main__':main()
