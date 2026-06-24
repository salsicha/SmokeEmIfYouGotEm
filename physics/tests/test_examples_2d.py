from raftsim.examples.generate_river_2d import main as generate_main
from raftsim.examples.run_2d_rapid import main as rapid_main


def test_generate_river_2d_example_writes_outputs(tmp_path):
    exit_code = generate_main(["--seed", "9", "--length", "80", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    output_dir = tmp_path / "seed_9"
    assert (output_dir / "river.json").exists()
    assert (output_dir / "river.png").exists()
    assert (output_dir / "flow.png").exists()
    assert (output_dir / "validation.txt").exists()


def test_run_2d_rapid_example_writes_outputs(tmp_path):
    exit_code = rapid_main(["--seed", "10", "--duration", "1.0", "--backend", "python", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    output_dir = tmp_path / "seed_10_python"
    assert (output_dir / "river.json").exists()
    assert (output_dir / "telemetry.csv").exists()
    assert (output_dir / "trajectory.png").exists()
    assert (output_dir / "forces.png").exists()
