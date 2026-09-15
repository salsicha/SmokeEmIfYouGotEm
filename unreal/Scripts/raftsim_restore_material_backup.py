"""Restore one installed experimental material from its verified backup.

Run outside Unreal: its package file handles can prevent atomic replacement.
The caller must separately reopen and audit the restored material graph.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def restore(root, report, baseline, output):
    root = Path(root).resolve()
    report, output = Path(report).resolve(), Path(output).resolve()
    saved = (root/'unreal/Saved/RaftSimValidation').resolve()
    assert report.is_relative_to(saved) and output.is_relative_to(saved)
    assert not output.exists()
    installed = json.loads(report.read_text())
    name = installed['material']
    assert name.startswith('/Game/') and '..' not in Path(name).parts
    target = (root/'unreal/Content'/(name.removeprefix('/Game/')+'.uasset')).resolve()
    assert target.is_relative_to((root/'unreal/Content').resolve())
    assert target.suffix == '.uasset' and sha(target) == installed['material_sha256']
    backup = report.with_suffix('.backup.zip')
    member = target.relative_to(root).as_posix()
    with zipfile.ZipFile(backup) as archive:
        assert archive.namelist() == [member]
        original = archive.read(member)
    assert hashlib.sha256(original).hexdigest() == baseline
    with tempfile.NamedTemporaryFile(dir=saved, suffix='.uasset', delete=False) as staged:
        staged.write(original)
        staged.flush()
        os.fsync(staged.fileno())
        staged_path = Path(staged.name).resolve()
    assert staged_path.is_relative_to(saved) and sha(staged_path) == baseline
    # Verify both exact paths and the installed bytes again before replacement.
    assert target.is_relative_to((root/'unreal/Content').resolve())
    assert sha(target) == installed['material_sha256']
    os.replace(staged_path, target)
    assert sha(target) == baseline
    result = dict(restored=True, exact_backup_restoration=True, material=name,
        material_sha256=baseline, saved_graphs=installed['original_graphs'],
        requires_fresh_process_audit=True, visual_or_physical_accepted=False)
    output.write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('baseline_sha256')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = restore(Path(__file__).resolve().parents[2], args.report, args.baseline_sha256, args.output)
    print(json.dumps({k:v for k,v in result.items() if k != 'saved_graphs'}, indent=2))
