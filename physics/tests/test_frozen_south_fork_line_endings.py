"""Keep byte-identical frozen evidence; never normalize inside the hash gate."""
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[2]
PATHS=[
    'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorSouthForkMaterial.cpp',
    'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/RaftSimEditorSouthForkOrganicTerrainTest.cpp',
    'docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_american_south_fork.json',
]


@pytest.mark.parametrize('relative',PATHS)
def test_exact_historical_bytes_and_checkout_policy(relative):
    review=json.loads((ROOT/'docs/environment-captures/south_fork_full_reach/m9_south_fork_organic_foothill_terrain_v1_review.json').read_text())
    expected=next(a['sha256'] for a in review['hash_locked_artifacts'] if a['path']==relative)
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected
    policy=subprocess.check_output(['git','check-attr','eol','--',relative],cwd=ROOT,text=True)
    assert policy.strip()==relative+': eol: lf'
