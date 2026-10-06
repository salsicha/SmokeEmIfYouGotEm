"""Check FXC reflection against the SM5 eight-UAV limit, not just compiler exit.

This is a resource-compatibility gate, not GPU execution or full-cook acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


def audit(text):
    if '// Resource Bindings:' not in text or not re.search(r'^[ \t]*cs_5_0\s*$', text, re.M):
        raise ValueError('Complete FXC cs_5_0 assembly/reflection required')
    rows = re.findall(r'^//\s+(\w+)\s+UAV\s+\S+\s+\S+\s+u(\d+)\s+(\d+)\s*$', text, re.M)
    slots = []
    for name, first, count in rows:
        if int(count) < 1:
            raise ValueError('Invalid UAV binding count')
        slots.extend(range(int(first), int(first)+int(count)))
    declared = [int(value) for value in re.findall(r'^[ \t]*dcl_uav\w*\s+u(\d+)\b', text, re.M)]
    if len(slots) != len(set(slots)) or sorted(declared) != sorted(slots):
        raise ValueError('UAV declarations and reflection disagree')
    extended = '64 UAV slots' in text
    return dict(schema='raftsim.sm5_shader_resources.v1',
                passed=not extended and all(slot < 8 for slot in slots),
                uav_count=len(slots), highest_uav_slot=max(slots, default=-1),
                requires_extended_uav_slots=extended,
                bindings=[dict(name=name, first=int(first), count=int(count)) for name, first, count in rows],
                gpu_execution_accepted=False, full_cook_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assembly', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    data = args.assembly.read_bytes()
    result = audit(data.decode('utf-8-sig'))
    result.update(assembly=str(args.assembly.resolve()), assembly_sha256=hashlib.sha256(data).hexdigest())
    with args.report.open('x') as target:
        json.dump(result, target, indent=2)
        target.write('\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
