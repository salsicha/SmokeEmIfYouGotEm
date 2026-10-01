"""Set the render-only observed-whitewater display gain on saved river maps.

Run inside the editor (UnrealEditor-Cmd -run=pythonscript, or -ExecutePythonScript):

    RAFTSIM_OBSERVED_WHITEWATER_GAIN=0.25 \
    RAFTSIM_OBSERVED_WHITEWATER_MAPS=/Game/RaftSim/Maps/L_Hance,/Game/RaftSim/Maps/L_Terminator \
    UnrealEditor-Cmd SmokeEmIfYouGotEm.uproject -ExecutePythonScript=unreal/Scripts/set_observed_whitewater_gain.py

The gain floors each wet vertex's displayed foam at gain x the layer's whitewater
fraction (ARaftSimWaterSurfaceActor). The landscape-candidate builder writes the
same value (kObservedWhitewaterDisplayGain); this script applies it to the saved
maps without regenerating terrain, water or dressing. Only the river water
config's ObservedWhitewaterGain changes; each map is saved only if it changed.
A JSON report is written to RAFTSIM_OBSERVED_WHITEWATER_REPORT when set.
"""
import json
import os

import unreal

GAIN = float(os.environ.get('RAFTSIM_OBSERVED_WHITEWATER_GAIN', '0.25'))
MAPS = [m for m in os.environ.get('RAFTSIM_OBSERVED_WHITEWATER_MAPS', '').split(',') if m]
REPORT = os.environ.get('RAFTSIM_OBSERVED_WHITEWATER_REPORT', '')


def main():
    assert MAPS, 'set RAFTSIM_OBSERVED_WHITEWATER_MAPS'
    assert 0.0 <= GAIN <= 1.0
    results = []
    config_class = unreal.load_class(None, '/Script/RaftSimWater.RaftSimRiverWaterConfig')
    for path in MAPS:
        world = unreal.EditorLoadingAndSavingUtils.load_map(path)
        assert world, f'could not load {path}'
        configs = unreal.GameplayStatics.get_all_actors_of_class(world, config_class)
        row = dict(map=path, configs=len(configs), before=[], after=[], saved=False)
        changed = False
        for actor in configs:
            before = float(actor.get_editor_property('observed_whitewater_gain'))
            row['before'].append(before)
            if abs(before - GAIN) > 1e-6:
                actor.modify()
                actor.set_editor_property('observed_whitewater_gain', GAIN)
                changed = True
            row['after'].append(float(actor.get_editor_property('observed_whitewater_gain')))
        if len(configs) != 1:
            row['error'] = 'expected exactly one river water config'
        elif changed:
            row['saved'] = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, path))
        results.append(row)
        unreal.log(f'RaftSim observed whitewater gain: {json.dumps(row)}')
    if REPORT:
        with open(REPORT, 'w', encoding='utf-8') as f:
            json.dump(dict(gain=GAIN, maps=results), f, indent=1)


main()
