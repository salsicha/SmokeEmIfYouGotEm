"""Independent on-disk provenance and wet-exterior check of coupled core export."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/coupled_geometry'


def main():
    path = BASE/'manifest.json'
    output = BASE/'source_exact_audit.json'
    assert not output.exists(), 'Retain previous geometry verification'
    manifest = json.loads(path.read_text())
    assert manifest['completed'] and manifest['remaining_interior_wet_exterior_faces']==0
    fields = ('bed_navd88_m','captured_surface_navd88_m','captured_water_mask','terrain_owner')
    records = manifest['regions']
    keys = {tuple(r['center_utm_m']):r for r in records}
    assert len(keys)==len(records)
    declared = {(r['region'],r['edge']) for r in manifest['open_geometry_edges']}
    checked = set()
    observed = set()
    original_cells = extra_cells = 0
    for record in records:
        core_path = ROOT/record['geometry_file']
        source_path = ROOT/record['source_geometry_file']
        assert hashlib.sha256(core_path.read_bytes()).hexdigest()==record['geometry_sha256']
        if source_path not in checked:
            assert hashlib.sha256(source_path.read_bytes()).hexdigest()==record['source_geometry_sha256']
            checked.add(source_path)
        row,col = record['source_slice_row_column']
        with np.load(core_path,allow_pickle=False) as core, np.load(source_path,allow_pickle=False) as source:
            for name in fields:
                assert core[name].shape==(80,80)
                assert np.array_equal(core[name],source[name][row:row+80,col:col+80]),(record['name'],name)
            water=core['captured_water_mask']
        if record['added_interior_context']:
            extra_cells += 6400
        else:
            original_cells += 6400
        x,y=record['center_utm_m']
        for edge,delta,wet in [('west',(-80,0),water[:,0]),('east',(80,0),water[:,-1]),
            ('south',(0,-80),water[0,:]),('north',(0,80),water[-1,:])]:
            if (x+delta[0],y+delta[1]) not in keys and np.any(wet):
                observed.add((record['name'],edge))
    assert observed==declared and len(observed)==4
    assert original_cells==799*6400 and extra_cells==27*6400
    result=dict(manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        checked_core_count=len(records),source_packet_hash_count=len(checked),
        source_fields_checked=list(fields),original_cells_exact=original_cells,added_source_context_cells_exact=extra_cells,
        four_declared_endpoint_faces_only=True,passed=True,hydraulic_state_solved=False,normal_map_integrated=False)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
