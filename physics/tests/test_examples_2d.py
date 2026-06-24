from raftsim.examples.generate_river_2d import main as generate_main
from raftsim.examples.generate_scenario2_5d import main as scenario2_5d_main
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


def test_generate_scenario2_5d_example_writes_package(tmp_path):
    exit_code = scenario2_5d_main(
        ["--fixture", "constriction", "--seed", "11", "--nx", "24", "--ny", "12", "--output-dir", str(tmp_path)]
    )

    assert exit_code == 0
    output_dir = tmp_path / "constriction_seed_11"
    assert (output_dir / "scenario.json").exists()
    assert (output_dir / "bed.npy").exists()
    assert (output_dir / "initial_state.npz").exists()
    assert (output_dir / "features.json").exists()
    assert (output_dir / "probes.json").exists()
    assert (output_dir / "validation.txt").exists()
    assert (output_dir / "bed.png").exists()
    assert (output_dir / "depth.png").exists()
    assert (output_dir / "speed.png").exists()


def test_generate_procedural_scenario2_5d_example_writes_package(tmp_path):
    exit_code = scenario2_5d_main(
        [
            "--mode",
            "procedural",
            "--seed",
            "12",
            "--nx",
            "32",
            "--ny",
            "18",
            "--feature-count",
            "9",
            "--no-plots",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    output_dir = tmp_path / "procedural_rapid_seed_12"
    assert (output_dir / "scenario.json").exists()
    assert (output_dir / "bed.npy").exists()
    assert (output_dir / "initial_state.npz").exists()
    assert (output_dir / "features.json").exists()
    assert (output_dir / "probes.json").exists()
    assert (output_dir / "validation.txt").exists()
