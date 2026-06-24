from raftsim.math2d import Vec2
from raftsim.river2d import River2DParameters, generate_river_2d


def test_river_generation_is_deterministic_for_seed():
    params = River2DParameters(seed=7, length=120.0, sample_count=41)
    first = generate_river_2d(params)
    second = generate_river_2d(params)

    assert first.to_json_dict() == second.to_json_dict()
    assert first.validate().passed
    assert len(first.features) > 0


def test_river_sampling_reports_current_and_bank_state():
    river = generate_river_2d(River2DParameters(seed=2, length=80.0, sample_count=31))
    center_sample = river.sample(river.section_at_s(5.0).center)
    far_bank_sample = river.sample(Vec2(5.0, 500.0))

    assert center_sample.inside_water is True
    assert center_sample.current.magnitude > 0.0
    assert far_bank_sample.inside_water is False
    assert far_bank_sample.bank_distance > 0.0


def test_river_json_export(tmp_path):
    river = generate_river_2d(River2DParameters(seed=3, length=60.0, sample_count=21))
    output_path = river.write_json(tmp_path / "river.json")

    text = output_path.read_text(encoding="utf-8")
    assert '"parameters"' in text
    assert '"features"' in text
