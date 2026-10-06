"""Prepare the unchanged full-map union gates for the constrained cap."""
import json
import numpy as np
from build_troublemaker_dem_rock_cap import ROOT,native_collision_probes
from prepare_source_vertex_collision_probes import prepare as prepare_visible
from prepare_south_fork_union_collision import prepare as prepare_union
from south_fork_rock_union import sha


def main():
    directory=ROOT/'tmp/constrained-wall-map-check-20260925'
    if directory.exists():raise ValueError('Fresh check directory required')
    manifest=ROOT/'tmp/troublemaker-constrained-wall-extension-v1-20260925/rock_cap_manifest.json'
    m=json.loads(manifest.read_text());cap=ROOT/m['cap_path']
    if sha(cap)!=m['cap_sha256']:raise ValueError('Source changed')
    directory.mkdir()
    with np.load(cap) as data:
        legacy=native_collision_probes(data['vertices_m'],data['triangles'],data['solid_vertices_m'],data['solid_triangles'],data['solid_face_kind'],sha(cap))
    legacy_path=directory/'legacy-probes.json';legacy_path.write_text(json.dumps(legacy)+'\n')
    visible_path=directory/'visible-probes.json'
    visible=prepare_visible(manifest,legacy_path,visible_path)
    probes_path=directory/'union-probes.json'
    summary=prepare_union(ROOT/'tmp/troublemaker-constrained-wall-union-20260925/manifest.json',probes_path,visible_path)
    config=json.loads((ROOT/'tmp/troublemaker-mixed-installed-visible-config-20260925.json').read_text())
    native_path=ROOT/'tmp/constrained-wall-native-orientation-20260925.json';native=json.loads(native_path.read_text())
    if not native['passed'] or native['source_cap_sha256']!=m['cap_sha256']:raise ValueError('Native validation mismatch')
    config.update(probes=probes_path.relative_to(ROOT).as_posix(),probes_sha256=sha(probes_path),
        export_directory='tmp/troublemaker-constrained-wall-export-20260925',candidate_native_sha256=native['native']['collision_source_sha256'],
        report='tmp/constrained-wall-full-map-collision-20260925.json')
    (directory/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps(dict(visible=visible,union=summary),indent=2))


if __name__=='__main__':main()
