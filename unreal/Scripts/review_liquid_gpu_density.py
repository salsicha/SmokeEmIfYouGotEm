"""Run the scoped particle-density diagnostic and exit the offscreen editor."""
import hashlib
import json
from pathlib import Path
import re
import unreal

root=Path(__file__).resolve().parents[2]/'docs/reconstruction-review-2026-09-07'
command=unreal.SystemLibrary.get_command_line()
source_match=re.search(r'-LiquidDensitySource=([A-Za-z0-9_-]+)',command)
label_match=re.search(r'-LiquidDensityLabel=([A-Za-z0-9_-]+)',command)
try:
    assert source_match and label_match,'Explicit source and fresh output labels required'
    source=root/source_match.group(1)
    output=root/label_match.group(1)
    assert not output.exists(),'Output must be unused'
    manifest=json.loads((source/'report.json').read_text())
    assert hashlib.sha256((source/'positions.rgba32f').read_bytes()).hexdigest()==manifest['positions_sha256']
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world,f'RaftSim.LiquidDensityGPUReview "{source}" "{output}"')
    assert (output/'report.json').is_file(),'GPU density report missing'
    report=json.loads((output/'report.json').read_text())
    assert report['diagnostics']==[0,0,0,0],f'GPU diagnostics failed: {report}'
finally:
    unreal.SystemLibrary.quit_editor()
