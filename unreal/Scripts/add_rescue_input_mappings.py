"""Add the rescue/reseat key mappings the bootstrap defines to the saved IMC.

IMC_RaftSimDefault predates the rescue mappings in
RaftSimEditorVerticalSliceBootstrap.cpp (RescueTargetSelect, RescueReachGrab,
RescueThrowLine, ReseatCrew), so the M9 release-candidate keyboard/gamepad
matrix fails 10/14. Only those four actions' mappings are added, with the keys
and negate modifier the bootstrap uses; existing mappings are left untouched
(regenerating would also drop the saved Mouse2D look mapping the QA requires).
Environment: RAFTSIM_INPUT_REPORT (fresh tmp JSON).
"""
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
IMC = '/Game/RaftSim/Input/IMC_RaftSimDefault'
MAPPINGS = [
    ('RescueTargetSelect', 'MouseWheelAxis', False),
    ('RescueReachGrab', 'E', False),
    ('RescueThrowLine', 'R', False),
    ('ReseatCrew', 'F', False),
    ('RescueTargetSelect', 'Gamepad_LeftShoulder', True),
    ('RescueTargetSelect', 'Gamepad_RightShoulder', False),
    ('RescueReachGrab', 'Gamepad_FaceButton_Bottom', False),
    ('RescueThrowLine', 'Gamepad_RightTrigger', False),
    ('ReseatCrew', 'Gamepad_FaceButton_Right', False),
]


def key_name(mapping):
    return str(mapping.get_editor_property('key').get_editor_property('key_name'))


def action_name(mapping):
    action = mapping.get_editor_property('action')
    return action.get_name() if action else ''


def current(imc):
    # UE 5.8 keeps mappings in DefaultKeyMappings; the legacy array is empty.
    return imc.get_editor_property('default_key_mappings').get_editor_property('mappings')


def set_current(imc, mappings):
    data = imc.get_editor_property('default_key_mappings')
    data.set_editor_property('mappings', mappings)
    imc.set_editor_property('default_key_mappings', data)


def main():
    report = ROOT / os.environ['RAFTSIM_INPUT_REPORT']
    assert report.is_relative_to(ROOT / 'tmp') and not report.exists()
    imc = unreal.load_asset(IMC)
    assert isinstance(imc, unreal.InputMappingContext)
    before = [(action_name(m), key_name(m)) for m in current(imc)]
    added, modified = [], []
    for action_id, key, negate in MAPPINGS:
        action = unreal.load_asset(f'/Game/RaftSim/Input/IA_{action_id}')
        assert isinstance(action, unreal.InputAction), action_id
        if (f'IA_{action_id}', key) not in before:
            k = unreal.Key()
            k.set_editor_property('key_name', key)
            imc.map_key(action, k)
            added.append(dict(action=action_id, key=key))
        if negate:
            mappings = current(imc)
            for i in range(len(mappings)):
                m = mappings[i]
                if action_name(m) == f'IA_{action_id}' and key_name(m) == key:
                    if not any(isinstance(x, unreal.InputModifierNegate) for x in m.get_editor_property('modifiers')):
                        m.set_editor_property('modifiers', [unreal.InputModifierNegate(outer=imc)])
                        mappings[i] = m
                        set_current(imc, mappings)
                        modified.append(dict(action=action_id, key=key, modifier='Negate'))
                    break
    after = [(action_name(m), key_name(m)) for m in current(imc)]
    assert set(before).issubset(set(after)), 'Existing mappings must be retained'
    assert unreal.EditorAssetLibrary.save_loaded_asset(imc, only_if_is_dirty=False)
    report.write_text(json.dumps(dict(asset=IMC, before=before, added=added, after=after), indent=2) + '\n')
    unreal.log('RAFTSIM_RESCUE_INPUT_MAPPINGS ' + json.dumps(dict(added=len(added), modified=len(modified), total=len(after))))


if __name__ == '__main__':
    main()
