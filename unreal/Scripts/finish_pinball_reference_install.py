"""Finish a prepared paired terrain/flow install only after Unreal has exited.

Every path and old/new hash is checked before replacement. A partial operation
can be resumed: already replaced files must have exactly the staged hash.
Backups and the pending receipt are retained; no history or sources are deleted.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
RIVER=ROOT/'physics/data/real_world/pacuare_river_costa_rica'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finish(pending):
    pending=pending.resolve()
    assert pending.is_relative_to(ROOT/'tmp')
    processes=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
    names=[row[0].lower() for row in csv.reader(io.StringIO(processes)) if row]
    assert not any(n.startswith(('unrealeditor','smokeemifyougotem')) for n in names), 'Unreal/game must exit before replacing mapped flow files'
    report=json.loads(pending.read_text())
    assert report['status']=='map_saved_runtime_pending' and report['patch']['applied'] and report['patch']['collision_rebuilt']
    final=(ROOT/report['final_receipt']).resolve()
    assert final.is_relative_to(ROOT/'tmp') and not final.exists()
    assert sha(ROOT/'unreal/Content/RaftSim/Maps/L_UpperHuacas.umap')==report['map_sha256_after']
    replacements=[]
    for relative,h in report['paired_runtime_files'].items():
        live=(ROOT/relative).resolve();staged=(ROOT/h['staged']).resolve()
        assert live.is_relative_to(RIVER) and staged.is_relative_to(ROOT/'tmp')
        assert sha(staged)==h['after'] and sha(live) in (h['before'],h['after']), 'Source or live file changed after preparation'
        replacements.append((live,staged,h))
    for live,staged,h in replacements:
        if sha(live)==h['after']:continue
        temporary=live.with_name(live.name+'.raftsim-install-pending')
        shutil.copy2(staged,temporary)
        assert sha(temporary)==h['after']
        os.replace(temporary,live)
    assert all(sha(live)==h['after'] for live,_,h in replacements)
    report['status']='paired_install_complete'
    final.write_text(json.dumps(report,indent=2)+'\n')
    return final


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pending',type=Path)
    print(finish(parser.parse_args().pending))
