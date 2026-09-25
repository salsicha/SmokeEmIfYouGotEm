"""Actual native sampler comparison; no scene saves or solver advancement."""
import json
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_constriction_union_collision import verify_runtime


def main():
    output=ROOT/'tmp/troublemaker-mixed-native-runtime-20260925.json'
    assert not output.exists()
    probes=ROOT/'tmp/troublemaker-mixed-normal-visible-union-probes-20260925.json'
    expected=ROOT/'tmp/troublemaker-mixed-normal-runtime-expectations-20260925.json'
    result=verify_runtime(expected,probes,json.loads(probes.read_text()))
    result.update(saved_assets=False,saved_levels=False,playable_integrated=False,
                  hydraulic_settling_accepted=False,visual_acceptance=False)
    output.write_text(json.dumps(result,indent=2)+'\n')
    assert result['field_queries_verified'],'Native fields differ: '+str(output)
    unreal.log('Mixed-cap native water queries verified: '+str(output))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
