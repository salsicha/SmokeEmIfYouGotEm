"""Read-only inspection of the saved playable South Fork optical graph."""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'


def main():
    output = Path(os.environ['RAFTSIM_OPTICS_AUDIT']).resolve()
    assert output.is_relative_to(ROOT/'tmp') and not output.exists()
    source = ROOT/'unreal/Content'/f'{PACKAGE.removeprefix("/Game/")}.uasset'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    material = unreal.load_asset(PACKAGE)
    assert material
    library = unreal.MaterialEditingLibrary
    rows = []
    for expression in library.get_material_expressions(material):
        row = dict(name=expression.get_name(), kind=expression.get_class().get_name(),
                   inputs=[e.get_name() for e in library.get_inputs_for_material_expression(material, expression) if e])
        for prop in ('parameter_name', 'default_value', 'code', 'desc', 'r', 'constant', 'coordinate_index'):
            try:
                row[prop] = str(expression.get_editor_property(prop))
            except Exception:
                pass  # Property does not belong to this expression class.
        rows.append(row)
    roots = {}
    for name in ('MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_SPECULAR', 'MP_OPACITY', 'MP_OPACITY_MASK', 'MP_EMISSIVE_COLOR', 'MP_NORMAL', 'MP_WORLD_POSITION_OFFSET'):
        expression = library.get_material_property_input_node(material, getattr(unreal.MaterialProperty, name))
        roots[name] = expression.get_name() if expression else None
    by_name = {row['name']: row for row in rows}
    reachable = {}
    for name, root in roots.items():
        seen, pending = set(), [root] if root else []
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(by_name[current]['inputs'])
        reachable[name] = sorted({by_name[n]['parameter_name'] for n in seen if 'parameter_name' in by_name[n]})
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before, 'Read-only audit changed saved material'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(dict(accepted=False, saved_nothing=True, material=PACKAGE, material_sha256=before,
            roots=roots, reachable_parameters=reachable, expressions=rows,
            scope='Saved editor graph topology and defaults, not live MID values, evaluated shader inputs, or GPU depth/visibility.'), stream, indent=2)
    unreal.log(f'Read-only South Fork optical graph: {output}')


if __name__ == '__main__':
    main()
