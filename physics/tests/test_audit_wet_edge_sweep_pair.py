import pytest
from audit_wet_edge_sweep_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, phase=i%2+1, frame=122+i//2,
        nx=512, ny=152, vertices=512*152, mask_crc32=i//2, exact=True,
        sweep_first=bool(i//2%2), queue_ms=3., sweep_ms=1.) for i in range(64)])


def test_full_original_pairs_are_scoped_not_release_acceptance():
    result = summarize(fixture())
    assert result["exact_distances"] and result["both_orders_and_phases_faster"]
    assert result["compared_distances"] == 64*512*152
    assert result["groups"]["phase_1_sweep_first"]["pairs"] == 16
    assert result["groups"]["phase_2_queue_first"]["pairs"] == 16
    assert not result["release_accepted"]


def test_one_losing_phase_order_or_any_mismatch_prevents_promotion():
    data = fixture()
    for row in data["pairs"]:
        if row["phase"] == 2 and row["sweep_first"]:
            row["sweep_ms"] = 4.
    result = summarize(data)
    assert result["groups"]["phase_0_all"]["sweep_mean_ms"] < 3.
    assert not result["both_orders_and_phases_faster"]
    data = fixture(); data["pairs"][31]["exact"] = False
    assert not summarize(data)["exact_distances"]


@pytest.mark.parametrize("key,value", [
    ("pair", True), ("pair", 1), ("phase", 2), ("sweep_first", True),
    ("frame", 119), ("vertices", 1), ("nx", 0), ("ny", 1.5),
    ("mask_crc32", -1), ("mask_crc32", 2**32),
    ("queue_ms", 0), ("sweep_ms", float("nan")), ("exact", 1)])
def test_malformed_original_records_reject(key, value):
    data = fixture(); data["pairs"][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_incomplete_repeated_or_order_confounded_captures_reject():
    data = fixture(); data["pairs"].pop()
    with pytest.raises(ValueError): summarize(data)
    data = fixture()
    for row in data["pairs"]: row["frame"] = 122
    with pytest.raises(ValueError): summarize(data)
    data = fixture()
    for row in data["pairs"]: row["mask_crc32"] = 1
    with pytest.raises(ValueError): summarize(data)
    data = fixture()
    for i, row in enumerate(data["pairs"]): row["sweep_first"] = bool(i%2)
    with pytest.raises(ValueError): summarize(data)
