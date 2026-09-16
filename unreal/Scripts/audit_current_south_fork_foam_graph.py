"""Read the current playable parent's reachable optical/geometry graphs; no saves."""
import json
import os
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as source
from raftsim_material_graph_signature import canonical_graph


def main():
    output = Path(os.environ['RAFTSIM_CURRENT_FOAM_GRAPH_REPORT'])
    if output.exists():
        raise FileExistsError(output)
    before = source.sha(source.FILE)
    material = unreal.load_asset(source.PATH)
    if not material:
        raise RuntimeError('Current playable material unavailable')
    lib = unreal.MaterialEditingLibrary
    properties = ('BASE_COLOR', 'ROUGHNESS', 'SPECULAR', 'EMISSIVE_COLOR',
                  'OPACITY', 'OPACITY_MASK', 'NORMAL', 'WORLD_POSITION_OFFSET')
    graphs = {name: source.graph(material, lib.get_material_property_input_node(
              material, getattr(unreal.MaterialProperty, 'MP_' + name))) for name in properties}
    nodes = list(lib.get_material_expressions(material))
    descriptions = {n.get_name(): str(n.get_editor_property('desc')) for n in nodes}
    selected = {}
    for n in nodes:
        desc = descriptions[n.get_name()]
        if any(word in desc for word in ('Foam', 'Froth', 'RegisteredDetail')):
            selected[desc] = dict(node=n.get_name(), graph=source.graph(material, n),
                reachable_properties=[p for p, graph in graphs.items() if n.get_name() in graph],
                direct_consumers=[other.get_name() for other in nodes if n in source.links(material, other).values()])
    after = source.sha(source.FILE)
    if before != after:
        raise RuntimeError('Read-only audit unexpectedly changed saved material')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(dict(schema='raftsim.current_foam_graph.v1', read_only=True,
            material=source.PATH, material_sha256=after, descriptions=descriptions,
            graphs=canonical_graph(graphs), selected=canonical_graph(selected),
            runtime_overrides_measured=False, visual_accepted=False), stream, indent=2)
        stream.write('\n')
    unreal.log('Current playable foam graph read-only audit saved: ' + str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
