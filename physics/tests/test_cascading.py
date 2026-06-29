import pytest

from raftsim.cascading import (
    BankShape2_5D,
    DropTransitionMetadata2_5D,
    PoolControlMetadata2_5D,
    PoolEddyControl2_5D,
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


def test_drop_transition_metadata_round_trips_required_milestone_fields():
    transition = DropTransitionMetadata2_5D(
        transition_id="drop_001",
        upstream_reach_id="pool_001",
        downstream_reach_id="wave_train_001",
        crest_station=42.0,
        bed_elevation_fall=1.15,
        geometry_kind="ledge",
        ramp_length=2.0,
        ledge_length=0.75,
        tailwater_depth=1.4,
        expected_hydraulic_control="retentive_hole",
        recirculation_risk=0.64,
        aeration_proxy=0.82,
        turbulence_proxy=0.77,
        hazard_tags=("hole", "keeper", "raft_flip"),
    )

    data = transition.to_json_dict()
    loaded = DropTransitionMetadata2_5D.from_json_dict(data)

    assert loaded == transition
    assert data["crest_station"] == 42.0
    assert data["bed_elevation_fall"] == 1.15
    assert data["control_length"] == 2.75
    assert data["tailwater_depth"] == 1.4
    assert data["expected_hydraulic_control"] == "retentive_hole"
    assert data["recirculation_risk"] == 0.64
    assert data["aeration_proxy"] == 0.82
    assert data["turbulence_proxy"] == 0.77
    assert data["hazard_tags"] == ["hole", "keeper", "raft_flip"]


def test_drop_transition_metadata_rejects_invalid_handoff_controls():
    with pytest.raises(ValueError, match="distinct reaches"):
        DropTransitionMetadata2_5D(
            transition_id="bad",
            upstream_reach_id="same",
            downstream_reach_id="same",
            crest_station=12.0,
            bed_elevation_fall=0.4,
            ramp_length=2.0,
        )
    with pytest.raises(ValueError, match="ramp or ledge"):
        DropTransitionMetadata2_5D(
            transition_id="bad",
            upstream_reach_id="a",
            downstream_reach_id="b",
            crest_station=12.0,
            bed_elevation_fall=0.4,
        )
    with pytest.raises(ValueError, match="recirculation"):
        DropTransitionMetadata2_5D(
            transition_id="bad",
            upstream_reach_id="a",
            downstream_reach_id="b",
            crest_station=12.0,
            bed_elevation_fall=0.4,
            ramp_length=2.0,
            recirculation_risk=1.4,
        )


def test_pool_control_metadata_round_trips_depth_eddy_recirculation_and_tailwater_controls():
    eddy = PoolEddyControl2_5D(
        zone_id="river_left_eddy",
        center_station=18.0,
        lateral_offset=6.5,
        radius=4.0,
        circulation_strength=0.45,
        recirculation_risk=0.2,
    )
    recirculation = PoolEddyControl2_5D(
        zone_id="tailout_recirculation",
        center_station=38.0,
        lateral_offset=-3.0,
        radius=2.5,
        circulation_strength=0.35,
        recirculation_risk=0.52,
    )
    pool = PoolControlMetadata2_5D(
        pool_id="pool_001_control",
        reach_id="pool_001",
        depth_profile=(
            StationProfilePoint2_5D(0.0, 1.9),
            StationProfilePoint2_5D(42.0, 1.45),
        ),
        tailwater_depth=1.3,
        storage_coefficient=0.62,
        residence_time_seconds=28.0,
        outflow_control="drop_controlled",
        eddy_controls=(eddy,),
        recirculation_zones=(recirculation,),
    )

    data = pool.to_json_dict()
    loaded = PoolControlMetadata2_5D.from_json_dict(data)

    assert loaded == pool
    assert data["mean_depth"] == 1.6749999999999998
    assert data["tailwater_depth"] == 1.3
    assert data["storage_coefficient"] == 0.62
    assert data["residence_time_seconds"] == 28.0
    assert data["outflow_control"] == "drop_controlled"
    assert data["eddy_controls"][0]["zone_id"] == "river_left_eddy"
    assert data["recirculation_zones"][0]["recirculation_risk"] == 0.52


def test_pool_control_metadata_rejects_inactive_or_invalid_pool_controls():
    with pytest.raises(ValueError, match="depth profile"):
        PoolControlMetadata2_5D(pool_id="pool", reach_id="reach", depth_profile=(), tailwater_depth=1.0)
    with pytest.raises(ValueError, match="tailwater"):
        PoolControlMetadata2_5D(
            pool_id="pool",
            reach_id="reach",
            depth_profile=(StationProfilePoint2_5D(0.0, 1.0),),
            tailwater_depth=0.0,
        )
    with pytest.raises(ValueError, match="radius"):
        PoolEddyControl2_5D(zone_id="bad", center_station=1.0, lateral_offset=0.0, radius=0.0)
