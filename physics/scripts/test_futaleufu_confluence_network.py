import numpy as np
import pytest
import json
from unittest.mock import patch

from build_futaleufu_confluence_network import upstream_arm, flow_budget


def test_arm_preserves_captured_vertices_and_flow_direction():
    points = np.array([[0, 0], [100, 0], [130, 40], [230, 40], [330, 40.]])
    first, arm = upstream_arm(points, 3, 120.)
    assert first == 1
    np.testing.assert_array_equal(arm, points[1:4])
    assert np.linalg.norm(np.diff(arm, axis=0), axis=1).sum() == 150
    arm[0, 0] = 999
    assert points[1, 0] == 100


@pytest.mark.parametrize('junction,length', [(0, 1), (4, 1), (3, 0), (3, np.nan), (3, 1000), (1.5, 10)])
def test_invalid_or_insufficient_capture_is_refused(junction, length):
    with pytest.raises(ValueError):
        upstream_arm([[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]], junction, length)


def test_exact_minimum_does_not_add_an_extra_segment():
    first, arm = upstream_arm([[0, 0], [10, 0], [20, 0], [30, 0]], 2, 10)
    assert first == 1 and len(arm) == 2


def test_separate_inlets_add_rather_than_replace_or_duplicate():
    # Synthetic arithmetic, not a real-river calibration.
    assert flow_budget(3, 40) == dict(rio_azul_m3_s=3, upstream_mainstem_m3_s=40,
                                      downstream_mainstem_m3_s=43)


@pytest.mark.parametrize('a,b', [(None, 400), (0, 400), (-1, 400), (30, np.nan),
                                (30, np.inf), (True, 400), ([1, 2], 400)])
def test_unknown_or_invalid_branch_cannot_be_filled_from_mainstem(a, b):
    with pytest.raises(ValueError):
        flow_budget(a, b)


def test_full_build_binds_sources_and_refuses_stale_chart(tmp_path):
    from build_futaleufu_confluence_network import build, sha
    from geo_frames import tm_forward, utm
    corridor = tmp_path/'production'; hydro = corridor/'hydrography'; hydro.mkdir(parents=True)
    osm = tmp_path/'futaleufu_sources_2026_09/osm'; osm.mkdir(parents=True)
    route = [[-72.001, -43.3], [-72, -43.3], [-72, -43.301]]
    main = [[-72, -43.298], [-72, -43.299], [-72, -43.3], [-72, -43.301]]
    (hydro/'route_stationing.json').write_text(json.dumps(dict(samples=[dict(lon=x, lat=y) for x,y in route])))
    (osm/'futaleufu_centreline.json').write_text(json.dumps(dict(centreline_lon_lat_chain=[p+[i*100] for i,p in enumerate(main)])))
    chart = tmp_path/'chart/coordinate_map.json'; chart.parent.mkdir()
    chart.write_text(json.dumps(dict(horizontal_crs='EPSG:32718 WGS 84 / UTM zone 18S')))
    (chart.parent/'manifest.json').write_text(json.dumps(dict(coordinate_map_sha256=sha(chart),
        confluence=dict(source_route_vertex=1, source_mainstem_vertex=2, lon_lat=route[1], route_station_m=80))))
    east,north = tm_forward(-72, -43.3, utm(18,south=True))
    source = tmp_path/'source'; source.mkdir()
    meta = dict(schema='raftsim.futaleufu_continuous_sources.v1',
        sources_sha256={'chart/coordinate_map.json':sha(chart)},
        grid=dict(epsg=32718,shape=[200,200],transform=[10,0,float(east)-1000,0,-10,float(north)+1000]))
    (source/'manifest.json').write_text(json.dumps(meta))
    with patch.multiple('build_futaleufu_confluence_network',ROOT=tmp_path,BASE=tmp_path,CORRIDOR=corridor,ROUTE=chart):
        result = build(source,tmp_path/'out',100)
        assert result['upstream_mainstem_source_vertex_interval']==[1,2]
        assert result['flow']['rio_azul_m3_s'] is None
        assert result['installed_in_engine'] is False
        a=result['branches']['rio_azul']['points_station_easting_northing_m'][-1][1:]
        b=result['branches']['upstream_mainstem']['points_station_easting_northing_m'][-1][1:]
        c=result['branches']['downstream_mainstem']['points_station_easting_northing_m'][0][1:]
        assert a==b==c
        with pytest.raises(ValueError,match='Fresh'):build(source,tmp_path/'out',100)
        chart.write_text(chart.read_text()+' ')
        with pytest.raises(ValueError,match='Changed source'):build(source,tmp_path/'refused',100)
        assert not (tmp_path/'refused').exists()
