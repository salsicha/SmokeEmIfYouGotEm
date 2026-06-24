"""Generate and plot a deterministic 2D river."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..plotting import plot_river2d, plot_river2d_flow
from ..river2d import River2DParameters, generate_river_2d


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/river2d"))
    parser.add_argument("--length", type=float, default=240.0)
    args = parser.parse_args(argv)

    output_dir = args.output_dir / f"seed_{args.seed}"
    river = generate_river_2d(River2DParameters(seed=args.seed, length=args.length))
    validation = river.validate()

    river.write_json(output_dir / "river.json")
    plot_river2d(river, output_path=output_dir / "river.png")
    plot_river2d_flow(river, output_path=output_dir / "flow.png")
    (output_dir / "validation.txt").write_text("\n".join(validation.summary_lines()) + "\n", encoding="utf-8")

    print(f"river={output_dir / 'river.json'}")
    print(f"plot={output_dir / 'river.png'}")
    print(f"flow={output_dir / 'flow.png'}")
    for line in validation.summary_lines():
        print(line)
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
