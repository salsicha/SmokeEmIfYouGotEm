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
