from fractions import Fraction as F
import math
import random
import pytest
from pressure_cut_face_reference import cut_pressure_column as original
from pressure_cut_endpoint_reference import cut_pressure_column as candidate, exact_endpoint_cuts


@pytest.mark.parametrize('retained_fraction', [F(0), F(1), F(1, 2), F(1, 2**200), F(1)-F(1, 2**200)])
@pytest.mark.parametrize('height', [math.nextafter(0., 1.), 1., 1e300, F(1, 2**2000)])
def test_exact_fractions_and_extreme_endpoints(height, retained_fraction):
    h = F(height); r = h*retained_fraction
    rates = dict(height_rate=F(3, 7), integrated_rate=-F(2, 3),
        bottom_rate=F(2**1500), retained_height_rate=F(1, 7))
    assert candidate(h, -F(2**1200), F(1, 2**2000), r, **rates) == original(
        h, -F(2**1200), F(1, 2**2000), r, **rates)


def test_random_exact_outputs_and_one_sided_tangents():
    rng = random.Random(713)
    for _ in range(300):
        h = F(rng.randint(1, 100), rng.randint(1, 100))
        retained = h*rng.choice([F(0), F(1), F(rng.randrange(1, 100), 100)])
        p, b, ht, pt, bt, rt = [F(rng.randint(-100, 100), rng.randint(1, 100)) for _ in range(6)]
        if retained == 0: rt = abs(rt)
        if retained == h: rt = ht-abs(rt)
        rates = dict(height_rate=ht, integrated_rate=pt, bottom_rate=bt, retained_height_rate=rt)
        assert candidate(h, p, b, retained, **rates) == original(h, p, b, retained, **rates)


@pytest.mark.parametrize('args,kwargs', [
    ((0, 1, 1, 0), {}), ((1, 1, 1, -1), {}), ((1, 1, 1, 2), {}),
    ((1, 1, 1, 0), dict(retained_height_rate=-1)),
    ((1, 1, 1, 1), dict(retained_height_rate=1)),
    ((1, 1, 1, 1), dict(bottom_rate=math.inf)),
    ((1, True, 1, 1), {}), ((1, 1, 1, 0), dict(integrated_rate=math.nan)),
])
def test_invalid_inputs_rejected_even_when_unused_at_endpoint(args, kwargs):
    with pytest.raises(ValueError) as a: original(*args, **kwargs)
    with pytest.raises(ValueError) as b: candidate(*args, **kwargs)
    assert str(a.value) == str(b.value)


def test_context_restores_after_failure_and_nesting():
    import reconstructed_pressure_geometry as geometry
    import reconstructed_pressure_rates as rates
    before = geometry.cut_pressure_column, rates.cut_pressure_column
    with pytest.raises(RuntimeError):
        with exact_endpoint_cuts():
            assert geometry.cut_pressure_column is rates.cut_pressure_column is candidate
            with exact_endpoint_cuts():
                assert geometry.cut_pressure_column is candidate
            assert geometry.cut_pressure_column is candidate
            raise RuntimeError('test cleanup')
    assert (geometry.cut_pressure_column, rates.cut_pressure_column) == before


def test_full_audit_records_array_and_scalar_bits_without_ambiguous_equality():
    import json
    import numpy as np
    from audit_pressure_cut_endpoints import exact_record
    value = dict(fluxes=[np.array([1., -0.]), np.float64(-0.)], maximum=2.)
    record = exact_record(value)
    assert record == exact_record(value)
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    other = dict(fluxes=[np.array([1., 0.]), np.float64(-0.)], maximum=2.)
    assert record != exact_record(other)
    assert exact_record(-0.) != exact_record(0.)
    with pytest.raises(ValueError): exact_record(np.array([{}], dtype=object))
