"""Keep the CC0 shell fit bounded; image review still establishes appearance."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def test_cc0_helmet_fit_does_not_reintroduce_oversized_shells():
    source = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCC0CrewVisualActor.cpp').read_text()
    scales = {name: float(re.search(rf'{name}HelmetFitScale = ([0-9.]+)f;', source)[1])
              for name in ('Guide','Crew')}
    assert .82 <= scales['Crew'] <= .88
    assert .87 <= scales['Guide'] <= .94
    assert scales['Guide'] > scales['Crew']
    host = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp').read_text()
    assert 'const float FittedScale = RecommendedHelmetScale;' in host
    assert 'kProductionHelmetSkullCenterOffsetCm * LiftScale' in host


def test_helmet_review_records_scale_and_multiple_angles():
    review = (ROOT/'unreal/Scripts/review_crew_turntable.py').read_text()
    for required in ('range(5)', 'head_front', 'head_rear', 'head_side',
                     'helmet_fit_scale', 'helmet_anchor_error_cm',
                     'FORWARD_STROKE', 'BRACE', 'REENTRY'):
        assert required in review
