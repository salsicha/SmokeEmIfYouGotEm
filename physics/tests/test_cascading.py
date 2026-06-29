import pytest

from raftsim.cascading import (
    BankShape2_5D,
    ReachGridTransform2_5D,
    ReachMetadata2_5D,
    StationProfilePoint2_5D,
)


def _reach(**overrides):
    values = {
        "reach_id": "pool_001",
        "kind": "pool",
        "station_start": 0.0,
        "station_end": 42.0,
        "local_grid": ReachGridTransform2_5D(origin_x=0.0, origin_y=-8.0, station_origin=0.0),
        "slope_profile": (
            StationProfilePoint2_5D(0.0, 0.002),
            StationProfilePoint2_5D(42.0, 0.003),
        ),
        "width_profile": (
            StationProfilePoint2_5D(0.0, 18.0),
            StationProfilePoint2_5D(42.0, 22.0),
        ),
        "bank_shape": BankShape2_5D("vegetated", left_bank_offset_m=11.0, right_bank_offset_m=-10.0),
        "bed_roughness": 0.041,
        "boulder_density": 0.15,
        "vegetation_flags": ("willow", "riparian_grass"),
        "debris_flags": ("seasonal_wood",),
        "confidence_score": 0.72,
    }
    values.update(overrides)
    return ReachMetadata2_5D(**values)


def test_reach_metadata_round_trips_required_milestone_fields():
    reach = _reach()
    data = reach.to_json_dict()
    loaded = ReachMetadata2_5D.from_json_dict(data)

    assert loaded == reach
    assert data["station_start"] == 0.0
    assert data["station_end"] == 42.0
    assert data["local_grid"]["dx"] == 1.0
    assert data["slope_profile"][0]["value"] == 0.002
    assert data["width_profile"][1]["value"] == 22.0
    assert data["bank_shape"]["shape"] == "vegetated"
    assert data["bed_roughness"] == 0.041
    assert data["boulder_density"] == 0.15
    assert data["vegetation_flags"] == ["willow", "riparian_grass"]
    assert data["debris_flags"] == ["seasonal_wood"]
    assert data["confidence_score"] == 0.72


def test_reach_metadata_rejects_invalid_station_range():
    with pytest.raises(ValueError, match="station_end"):
        _reach(station_start=10.0, station_end=10.0)


def test_reach_metadata_rejects_profiles_outside_station_range():
    with pytest.raises(ValueError, match="slope profile"):
        _reach(slope_profile=(StationProfilePoint2_5D(50.0, 0.01),))


def test_reach_metadata_rejects_negative_or_unbounded_controls():
    with pytest.raises(ValueError, match="boulder density"):
        _reach(boulder_density=1.5)
    with pytest.raises(ValueError, match="confidence"):
        _reach(confidence_score=-0.1)
    with pytest.raises(ValueError, match="width"):
        _reach(width_profile=(StationProfilePoint2_5D(0.0, 0.0),))
