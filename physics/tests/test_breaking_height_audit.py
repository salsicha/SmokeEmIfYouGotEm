from pathlib import Path
import runpy

HELPERS = runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/audit_breaking_height.py'))
ROW = ('BreakingHeightAudit world_s=10 station_m=8361 lateral_m=0 up_depth_m=.8 '
       'up_fr=1.4 down_fr=.7 raw_rise_m=.3 optical_rise_m=-.1 '
       'raw_extra_m=.5 optical_extra_m=.65 coverage=1 clearance_m=5 accepted=1')


def test_height_audit_detects_erased_rise_without_claiming_final_height():
    rows = HELPERS['parse']('[prefix] '+ROW)
    result = HELPERS['summarize'](rows, 8355, 8365)
    assert result['pre_deduplication_candidate_count'] == 1
    assert result['rise_reversed_count'] == 1
    assert abs(result['maximum_extra_height_deficit_m']-.15) < 1e-8
    assert not HELPERS['summarize'](rows, 8400, 8410)['candidates']


def test_height_audit_rejects_incomplete_or_mixed_snapshots():
    for text in ['', ROW.replace('up_fr=1.4', 'up_fr=nan'), ROW.replace('accepted=1', ''),
                 ROW+'\n'+ROW.replace('world_s=10', 'world_s=11')]:
        try:
            HELPERS['parse'](text)
        except ValueError:
            continue
        raise AssertionError('Invalid audit accepted')


SPATIAL = (' down_station_m=8364 down_lateral_m=1 up_surface_m=100 down_surface_m=100.3 '
           'up_bed_m=99.2 down_bed_m=99.3 flow_direction_x=.6 flow_direction_y=.8')


def test_spatial_endpoints_preserved_without_claiming_a_rendered_profile():
    rows = HELPERS['parse'](ROW+SPATIAL)
    result = HELPERS['summarize'](rows, 8355, 8365)
    assert result['spatial_geometry_available']
    assert result['candidates'][0]['down_station_m'] == 8364
    assert not HELPERS['summarize'](HELPERS['parse'](ROW),8355,8365)['spatial_geometry_available']
    assert not HELPERS['summarize'](rows,8400,8410)['spatial_geometry_available']


def test_spatial_records_reject_partial_inconsistent_or_mixed_endpoints():
    valid = ROW+SPATIAL
    for text in [ROW+' down_station_m=8364', valid.replace('down_surface_m=100.3','down_surface_m=100.4'),
                 valid.replace('flow_direction_x=.6','flow_direction_x=0'),
                 valid+'\n'+ROW, valid.replace('down_bed_m=99.3','up_bed_m=99.2')]:
        try:
            HELPERS['parse'](text)
        except ValueError:
            continue
        raise AssertionError('Invalid spatial record accepted')


def test_independent_native_rounding_is_allowed():
    text = (ROW+SPATIAL).replace('down_surface_m=100.3','down_surface_m=100.3001')
    assert HELPERS['parse'](text)[0]['down_surface_m'] == 100.3001


def test_depth_is_not_assumed_to_include_every_presentation_height():
    # Some adapter paths add a traveling presentation wave but retain physical
    # source depth. Preserve this evidence rather than assert a false identity.
    text = (ROW+SPATIAL).replace('up_bed_m=99.2','up_bed_m=99')
    assert HELPERS['parse'](text)[0]['up_depth_m'] == .8
