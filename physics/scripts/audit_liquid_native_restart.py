"""Verify two actual native generations in one Unreal process, with full flow audits."""
import argparse
import json
from pathlib import Path

from audit_liquid_native_retirement import audit as audit_retirement
from audit_liquid_native_transfer import audit as audit_transfer
from audit_liquid_native_generation import verify_generation, verify_distinct_generations


def audit(directory):
    directory = Path(directory).resolve()
    restart = json.loads((directory/'restart.json').read_text())
    if (not restart['complete'] or restart['process_id'] <= 0 or
            [g['directory'] for g in restart['generations']] != ['generation-001', 'generation-002']):
        raise ValueError('Complete same-process two-generation replay required')
    reports, results = [], []
    for item in restart['generations']:
        root = directory/item['directory']
        capture = json.loads((root/'capture.json').read_text())
        if not item['complete'] or not capture['complete'] or item['process_id'] != restart['process_id'] or capture['process_id'] != restart['process_id']:
            raise ValueError('Restart generations were not completed in the same native process')
        reports.append(json.loads((root/'stages.json').read_text()))
        transport = audit_retirement(root, log_path=directory.with_suffix('.log'))
        p2g = audit_transfer(root, log_path=directory.with_suffix('.log'))
        if not p2g['native_packet_p2g_verified'] or not transport['handoff_continuous_through_capture'] or not transport['native_emission_verified']:
            raise ValueError('Each new generation must actually emit, move, transfer and retire water')
        results.append(dict(transport=transport, p2g={k:v for k,v in p2g.items() if k not in ('raw_regions','particles')}))
    generations = verify_distinct_generations(reports)
    return dict(native_generation_restart_verified=True, process_id=restart['process_id'],
                generations=generations, replays=results, dense_flow_or_visual_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path);parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'replays'}, indent=2))
