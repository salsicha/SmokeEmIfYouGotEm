import copy
import pytest
from export_south_fork_discharge_bed_runtime import sha, verify_packet_geometry_identity


def inputs(tmp_path):
    path = tmp_path/'geometry.json'
    path.write_text('{}')
    frame = dict(world_origin_utm_m=[100.,200.],vertical_datum_navd88_m=20.,grid_spacing_m=1.)
    union = dict(terrain_revision=dict(revised_geometry_sha256='candidate'))
    source = dict(**frame,terrain_union=union,hydraulic_geometry_manifest='geometry.json',
        hydraulic_geometry_manifest_sha256=sha(path))
    geometry = dict(**frame,terrain_union=copy.deepcopy(union),discharge_bed=dict(
        retained_geometry_manifest='geometry.json',retained_geometry_manifest_sha256=sha(path)))
    return source, geometry


def test_matching_geometry(tmp_path):
    verify_packet_geometry_identity(*inputs(tmp_path),tmp_path)


@pytest.mark.parametrize('field,value',[
    ('hydraulic_geometry_manifest','old.json'),('hydraulic_geometry_manifest_sha256','old'),
    ('terrain_union',{}),('world_origin_utm_m',[101.,200.]),
    ('vertical_datum_navd88_m',21.),('grid_spacing_m',2.)])
def test_wrong_packet_family_refused(tmp_path,field,value):
    source, geometry = inputs(tmp_path)
    source[field] = value
    with pytest.raises(ValueError):
        verify_packet_geometry_identity(source,geometry,tmp_path)


def test_retained_geometry_mutation_refused(tmp_path):
    source, geometry = inputs(tmp_path)
    (tmp_path/'geometry.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='hydraulic geometry changed'):
        verify_packet_geometry_identity(source,geometry,tmp_path)
def test_identity_guard_imports_without_site_packages():
    import subprocess
    import sys
    from pathlib import Path
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    code=(f'import sys; sys.path.insert(0,{str(scripts)!r}); '
          'from south_fork_packet_geometry_identity import verify_packet_geometry_identity; '
          'assert "numpy" not in sys.modules')
    subprocess.run([sys.executable,'-I','-S','-c',code],check=True,capture_output=True,text=True)
