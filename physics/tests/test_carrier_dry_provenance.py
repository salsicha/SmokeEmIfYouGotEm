import copy

import pytest

from analyze_carrier_dry_provenance import analyze


def fixture():
    return dict(x_cm=25., y_cm=-75., water_z_cm=90., ground_z_cm=80.,
                raw_available=True, raw_wet=False, ground_hit=True,
                raw_bed_m=1., raw_depth_m=0.,
                triangle_vertices=[dict(x_cm=x, y_cm=y) for x,y in [(0.,0.), (0.,-250.), (50.,0.)]],
                source_cell=[
                    dict(field_x_m=x, field_y_m=y, cached_bed_m=.2*x+.4*y,
                         current_bed_m=.2*x+.4*y, cached_depth_m=.1,
                         current_depth_m=.1, current_available=True,
                         clipping_wet=True, current_wet=True)
                    for x, y in [(0., 0.), (1., 0.), (0., 1.), (1., 1.)]])


def test_coarse_lattice_misses_high_native_bed_without_changing_inputs():
    p = fixture()
    before = copy.deepcopy(p)
    r = analyze(p)
    assert r['bilinear_coarse_lattice']['current_bed_m'] == pytest.approx(.35)
    assert r['raw_bed_minus_coarse_current_bed_m'] == pytest.approx(.65)
    assert r['maximum_corner_depth_change_m'] == 0
    assert r['triangle_above_raw_bed_cm'] == -10
    assert r['triangle_above_ground_cm'] == 10
    assert r['coarse_positive_donor_stage_minus_bed_m'] == pytest.approx(.1)
    assert p == before


def test_both_world_orientations():
    p = fixture()
    first = analyze(p)
    p['y_cm'] *= -1
    for v in p['triangle_vertices']: v['y_cm'] *= -1
    assert analyze(p, 1.)['bilinear_coarse_lattice'] == first['bilinear_coarse_lattice']


def test_retained_packaged_three_wet_corner_discrepancy():
    # Actual v18 observer at world 10.025614811980631 seconds, input SHA256
    # 0da3f8add95688587d99277f2c06b83211bf1656b7eaf9d0310e61afe55110d5.
    # A diagnostic reproduction, NOT a passing shoreline acceptance test.
    p = fixture()
    p.update(x_cm=-542931.4614427652, y_cm=-361170.3368914142,
             water_z_cm=788.1619722471027, ground_z_cm=755.1181030273438,
             raw_bed_m=8.062271118164062,
             triangle_vertices=[dict(x_cm=x, y_cm=y) for x,y in [
                 (-542904.9703405886,-361150.), (-542909.9406811772,-361200.),
                 (-542954.9703405886,-361160.6737828284)]])
    beds = [7.243682861328125, 7.27630615234375, 9.9083251953125, 7.7048187255859375]
    cached = [.5688362717628479, .49260467290878296, 0., .2190435528755188]
    current = [.5688410997390747, .49260735511779785, 0., .21904486417770386]
    for i, c in enumerate(p['source_cell']):
        c.update(field_x_m=-5430.+i%2, field_y_m=3611.+i//2,
                 cached_bed_m=beds[i], current_bed_m=beds[i],
                 cached_depth_m=cached[i], current_depth_m=current[i],
                 clipping_wet=i != 2, current_wet=i != 2)
    r = analyze(p)
    assert r['triangle_query_error_cm'] == 0.
    assert r['coarse_positive_donor_stage_minus_bed_m'] == pytest.approx(-.19221246652413715)
    assert r['maximum_corner_depth_change_m'] < 5.e-6
    assert r['maximum_corner_bed_change_m'] == 0.
    assert abs(r['raw_bed_minus_coarse_current_bed_m']) < 7.e-6
    assert r['triangle_above_ground_cm'] > 33.
    assert r['triangle_above_raw_bed_cm'] < -18.


@pytest.mark.parametrize('change', ['wet', 'buried', 'unavailable', 'order', 'nan', 'negative', 'outside', 'triangle'])
def test_bad_or_irrelevant_evidence_rejected(change):
    p = fixture()
    if change == 'wet': p['raw_wet'] = True
    if change == 'buried': p['water_z_cm'] = 79.
    if change == 'unavailable': p['source_cell'][0]['current_available'] = False
    if change == 'order': p['source_cell'].reverse()
    if change == 'nan': p['source_cell'][0]['current_depth_m'] = float('nan')
    if change == 'negative': p['source_cell'][0]['current_depth_m'] = -1.
    if change == 'outside':
        p['x_cm'] = 101.
        for v in p['triangle_vertices']: v['x_cm'] += 76.
    if change == 'triangle': p['triangle_vertices'][0]['x_cm'] = 10.
    with pytest.raises(ValueError): analyze(p)
