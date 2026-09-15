import copy
import numpy as np
import pytest

from audit_south_fork_source_birth_geometry import analyze
from subcell_source_activation import assembly
from test_subcell_source_birth_pressure import fixture


def test_birth_audit_uses_unmodified_original_receiving_support_and_nonzero_faces():
    part, _, _ = fixture()
    before = [(p['volume'], p['momentum'].copy()) for p in part.pools]
    result = analyze(part, assembly(part))
    assert result['receiving_region_count'] > 0
    assert result['incoming_face_count'] > 0
    assert result['exact_rational_integral_comparisons'] >= 15
    assert result['receipt_reassembly_error'] == 0
    assert not result['full_metric_flux_or_evolution_or_gameplay_accepted']
    for p, (v, momentum) in zip(part.pools, before):
        assert p['volume'] == v
        np.testing.assert_array_equal(p['momentum'], momentum)


@pytest.mark.parametrize('rate', [0., -1., float('nan'), float('inf')])
def test_invalid_receipt_rates_cannot_pass_exact_birth_evidence(rate):
    part, _, _ = fixture()
    original = assembly(part)
    modified = dict(original, new_region_rates=copy.deepcopy(original['new_region_rates']))
    modified['new_region_rates'][0]['volume_rate'] = rate
    with pytest.raises(ValueError, match='positive receipt'):
        analyze(part, modified)


def test_wrong_state_and_duplicate_receiving_source_reject():
    part, _, _ = fixture()
    original = assembly(part)
    with pytest.raises(ValueError, match='matching'):
        analyze(part, dict(original, partition=object()))
    with pytest.raises(ValueError, match='Repeated'):
        analyze(part, dict(original, new_region_rates=original['new_region_rates']*2))
