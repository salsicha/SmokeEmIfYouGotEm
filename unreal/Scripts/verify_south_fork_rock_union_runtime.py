"""Shared source bed, actual full-map collision and native candidate loader."""
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_south_fork_rock_union_collision import main

if __name__=='__main__':
    try:
        main(ROOT/'tmp/south-fork-rock-union-runtime-expectations-v2-20260915.json',
            ROOT/'unreal/Saved/RaftSimValidation/south-fork-rock-union-runtime-v2-20260915.json')
    finally:unreal.SystemLibrary.quit_editor()
