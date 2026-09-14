from fractions import Fraction as F
import math
import random
import numpy as np
import pytest
from pressure_cut_face_reference import cut_pressure_column as original
from pressure_cut_basis_reference import make_cut_pressure_column, exact_cut_basis


@pytest.mark.parametrize('height', [math.nextafter(0., 1.), 1., 1e300, F(1, 2**2000)])
@pytest.mark.parametrize('ratio', [F(0), F(1), F(1, 2), F(1, 2**200), F(1)-F(1, 2**200)])
def test_exact_outputs_with_extreme_values_and_blocked_slivers(height, ratio):
    candidate = make_cut_pressure_column(); h = F(height); retained = h*ratio
    for p, b in [(F(1), F(0)), (F(0), F(1)), (-F(2**1400), F(1, 2**1800))]:
        rates = dict(height_rate=F(3, 7), integrated_rate=-F(2, 3),
            bottom_rate=F(2**1500), retained_height_rate=F(1, 7))
        assert candidate(h, p, b, retained, **rates) == original(h, p, b, retained, **rates)


def test_random_polynomial_algebra_and_cache_keys_include_all_rates():
    candidate = make_cut_pressure_column(maxsize=32); rng = random.Random(1483)
    for _ in range(300):
        h = F(rng.randint(1, 100), rng.randint(1, 100)); r = h*F(rng.randrange(1, 100), 100)
        p, b, ht, pt, bt, rt = [F(rng.randint(-100, 100), rng.randint(1, 100)) for _ in range(6)]
        for dh, dr in [(0, 0), (F(1, 1000), 0), (0, F(1, 1000))]:
            rates = dict(height_rate=ht+dh, integrated_rate=pt, bottom_rate=bt, retained_height_rate=rt+dr)
            expected = original(h, p, b, r, **rates)
            assert candidate(h, p, b, r, **rates) == expected
            assert candidate(h, p, b, r, **rates) == expected
    info = candidate.cache_info()
    assert info.hits == 900 and info.misses == 900 and info.currsize == info.maxsize == 32


@pytest.mark.parametrize('args,kwargs', [
    ((0, 1, 1, 0), {}), ((1, 1, 1, -1), {}), ((1, 1, 1, 2), {}),
    ((1, 1, 1, 0), dict(retained_height_rate=-1)),
    ((1, 1, 1, 1), dict(retained_height_rate=1)),
    ((1, 1, 1, 1), dict(bottom_rate=math.inf)),
    ((1, True, 1, 1), {}), ((1, 1, 1, 0), dict(integrated_rate=math.nan)),
])
def test_all_validation_is_retained(args, kwargs):
    candidate = make_cut_pressure_column()
    with pytest.raises(ValueError) as a: original(*args, **kwargs)
    with pytest.raises(ValueError) as b: candidate(*args, **kwargs)
    assert str(a.value) == str(b.value)


def test_partial_basis_reused_across_pressure_components_not_stale_geometry():
    candidate = make_cut_pressure_column()
    a = candidate(2, 1, 0, 1); b = candidate(2, 0, 1, 1)
    assert candidate.cache_info().hits == 1 and candidate.cache_info().misses == 1
    assert a == original(2, 1, 0, 1) and b == original(2, 0, 1, 1)
    assert candidate(3, 0, 1, 1) == original(3, 0, 1, 1)
    assert candidate.cache_info().misses == 2


def test_scoped_cache_cleanup_and_invalid_cache_size():
    import reconstructed_pressure_geometry as geometry
    import reconstructed_pressure_rates as rates
    before = geometry.cut_pressure_column, rates.cut_pressure_column
    counts = {}
    with pytest.raises(RuntimeError):
        with exact_cut_basis(counts, 3):
            geometry.cut_pressure_column(2, 1, 0, 1)
            rates.cut_pressure_column(2, 0, 1, 1)
            raise RuntimeError('cleanup test')
    assert (geometry.cut_pressure_column, rates.cut_pressure_column) == before
    assert counts == dict(closed=0, full=0, partial=2, cache=dict(hits=1, misses=1, maxsize=3, currsize=1))
    for size in (0, -1, True, 1.5):
        with pytest.raises(ValueError): make_cut_pressure_column(size)
