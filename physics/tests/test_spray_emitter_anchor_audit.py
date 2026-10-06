import pytest

from audit_spray_emitter_anchors import audit, MARKER


def triplet(enabled=1, sampled=1, slot=0, carrier=100.0):
    return '\n'.join(
        f'[2026.09.28-05.00.00:000][ 10]{MARKER}slot={slot} emitter={name} '
        f'enabled={enabled} sampled={sampled} x_cm=1.000000 y_cm=2.000000 '
        f'z_cm={carrier + gap:.6f} carrier_z_cm={carrier if sampled else 0:.6f} '
        f'clearance_cm={gap if sampled else 0:.6f}'
        for name, gap in [('aerosol', 6), ('roller', 3), ('crest', 3)])


def test_enabled_centres_with_disabled_unavailable_sites():
    report = audit(triplet() + '\n' + triplet(0, 0, 1))
    assert report['source_centre_clearance_passed']
    assert report['site_triplets'] == 2
    assert not report['visual_accepted'] and not report['performance_accepted']
    for row in report['emitters'].values():
        assert row['sampled_enabled_records'] == 1
        assert row['disabled_records'] == row['unavailable_records'] == 1
        assert row['enabled_slots'] == [0]


@pytest.mark.parametrize('text', ['', 'SprayAttachmentAudit enabled=1',
    triplet(0), triplet(0, 0), triplet(1, 0), triplet(slot=6),
    '\n'.join(triplet().splitlines()[:2]),
    '\n'.join(reversed(triplet().splitlines())),
    triplet().replace('slot=0', 'slot=0 slot=1', 1),
    triplet().replace('sampled=1 ', '', 1),
    triplet().replace('enabled=1', 'enabled=2', 1),
    triplet().replace('enabled=1', 'enabled=0', 1),
    triplet().replace('x_cm=1.000000', 'x_cm=nan', 1),
    triplet().replace('z_cm=106.000000', 'z_cm=106.100000', 1),
    triplet().replace('clearance_cm=6.000000', 'clearance_cm=6.100000', 1),
    triplet().replace('z_cm=106.000000', 'z_cm=107.000000').replace(
        'clearance_cm=6.000000', 'clearance_cm=7.000000'),
    triplet().replace('emitter=crest', 'emitter=unknown')])
def test_fail_closed(text):
    with pytest.raises(ValueError):
        audit(text)


def test_rounded_log_arithmetic_is_not_exact_binary_equality():
    text = triplet(carrier=1234567.123456).replace(
        'clearance_cm=6.000000', 'clearance_cm=6.000001', 1)
    assert audit(text)['source_centre_clearance_passed']


def test_disabled_sources_do_not_supply_clearance_evidence():
    inactive = triplet(0).replace('z_cm=106.000000', 'z_cm=150.000000').replace(
        'clearance_cm=6.000000', 'clearance_cm=50.000000')
    result = audit(triplet(slot=2) + '\n' + inactive)
    assert result['emitters']['aerosol']['sampled_enabled_records'] == 1
    assert result['emitters']['aerosol']['max_clearance_error_cm'] == 0
