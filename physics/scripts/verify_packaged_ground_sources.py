"""Run the non-editor ground-source audit against a fresh packaged executable.

The saved retention receipt is input evidence, never rewritten. A successful
process exit alone does not qualify geometry, and geometry does not qualify
gameplay, settled hydraulics, visual fidelity, or the 30 FPS gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from package_runtime_bundle import verify_staged
from source_asset_retention import IDENTITY

FORMAT = 'le_f32_cyclic_directed_triangles_material_u32_sorted_v1'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(row):
    if not isinstance(row, dict) or row.get('format') != FORMAT:
        raise ValueError('Complete native source format required')
    asset = row.get('asset', '')
    if not isinstance(asset, str) or not re.fullmatch(r'/Game/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+', asset):
        raise ValueError('Canonical project asset required')
    if not re.fullmatch(r'[0-9a-f]{64}', str(row.get('collision_source_sha256', ''))):
        raise ValueError('Native source SHA256 required')
    for key, minimum in [('collision_lod', 0), ('collision_trace_flag', 0),
                         ('triangle_count', 1), ('provider_vertex_count', 3)]:
        value = row.get(key)
        if type(value) not in (int, float) or not value >= minimum or value % 1:
            raise ValueError('Integral native source identity required: '+key)
    if type(row.get('flip_normals')) is not bool:
        raise ValueError('Native winding setting required')
    return dict(asset=asset, **{key: row[key] for key in IDENTITY})


def expected_sources(receipt):
    if receipt.get('schema') != 'raftsim.ground_cpu_retention.v1' or receipt.get('completed') is not True:
        raise ValueError('Completed retention receipt required')
    expected = {}
    for row in receipt.get('assets', []):
        before, after = row.get('before', {}), row.get('after', {})
        value = identity(after)
        if (identity(before) != value or row.get('asset') != value['asset'] or
                row.get('native_source_unchanged') is not True or
                before.get('available') is not True or after.get('available') is not True or
                after.get('allow_cpu_access') is not True):
            raise ValueError('Unchanged retained native source required')
        if value['asset'] in expected:
            raise ValueError('Duplicate retained asset')
        expected[value['asset']] = value
    if not expected:
        raise ValueError('Nonempty retained asset set required')
    return expected


def verify_native_report(expected, actual):
    if actual.get('passed') is not True or actual.get('editor_only_data') is not False:
        raise ValueError('Passing non-editor report required')
    observed = {}
    for row in actual.get('assets', []):
        value = identity(row)
        if (row.get('available') is not True or row.get('allow_cpu_access') is not True or
                row.get('source_matches') is not True or row.get('editor_only_data') is not False):
            raise ValueError('Non-editor CPU geometry must be available and matched for every asset')
        if value['asset'] in observed:
            raise ValueError('Duplicate observed asset')
        observed[value['asset']] = value
    if not expected or observed != expected:
        raise ValueError('Exact complete retained asset identities required')
    return dict(assets_verified=len(observed),
                directed_triangles_verified=sum(row['triangle_count'] for row in observed.values()))


def run(executable, executable_sha256, receipt_path, bundle, output):
    executable, receipt_path, bundle, output = map(lambda p: Path(p).resolve(),
                                                   (executable, receipt_path, bundle, output))
    if output.exists():
        raise ValueError('Fresh audit directory required')
    if executable.name != 'SmokeEmIfYouGotEm.exe' or sha(executable) != executable_sha256:
        raise ValueError('Expected packaged game executable identity required')
    if not list((executable.parents[2]/'Content/Paks').glob('*.pak')):
        raise ValueError('Cooked project package required beside the game binary')
    receipt_bytes = receipt_path.read_bytes()
    expected = expected_sources(json.loads(receipt_bytes))
    staged = verify_staged(bundle, executable.parent/'RaftSimRuntimeData')
    # All preflight checks complete before creating reports or launching UE.
    output.mkdir(parents=True)
    expected_path, native_path = output/'expected.json', output/'native.json'
    expected_path.write_text(json.dumps(dict(assets=list(expected.values())), indent=2)+'\n')
    command = [str(executable), '/Game/RaftSim/Maps/L_RaftSimBoot', '-nullrhi',
               '-nosound', '-unattended', '-nosplash', '-stdout', '-FullStdOutLogOutput',
               '-RaftSimEphemeralProfile', '-abslog='+str(output/'engine.log'),
               f'-ExecCmds=RaftSim.AuditGroundSources "{expected_path}" "{native_path}"']
    launch = dict(command=command, cwd=str(executable.parent), executable_sha256=executable_sha256,
                  retention_receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
                  expected_sha256=sha(expected_path), runtime_bundle=staged)
    (output/'launch.json').write_text(json.dumps(launch, indent=2)+'\n')
    with (output/'stdout.log').open('wb') as log:
        # The invoking tool can yield while this owned process remains live.
        # An observation timeout must not kill/restart a valid native audit.
        completed = subprocess.run(command, cwd=executable.parent, stdout=log,
                                   stderr=subprocess.STDOUT, check=False)
    if completed.returncode != 0:
        raise ValueError('Packaged native audit process failed: '+str(completed.returncode))
    counts = verify_native_report(expected, json.loads(native_path.read_text(encoding='utf-8-sig')))
    if sha(executable) != executable_sha256 or receipt_path.read_bytes() != receipt_bytes:
        raise ValueError('Executable or retention receipt changed during audit')
    if verify_staged(bundle, executable.parent/'RaftSimRuntimeData') != staged:
        raise ValueError('Runtime bundle changed during audit')
    result = dict(schema='raftsim.packaged_ground_source_audit.v1', passed=True, **counts,
                  packaged_execution_verified=True, editor_only_data=False,
                  executable_sha256=executable_sha256,
                  retention_receipt_sha256=launch['retention_receipt_sha256'],
                  native_report_sha256=sha(native_path), runtime_bundle=staged,
                  gameplay_verified=False, physical_acceptance=False,
                  visual_acceptance=False, performance_accepted=False)
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--executable-sha256', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.executable, args.executable_sha256, args.receipt,
                         args.bundle, args.output), indent=2))
