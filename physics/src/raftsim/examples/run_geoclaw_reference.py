"""Run setup checks for the optional GeoClaw 2.5D reference harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..geoclaw_reference import check_geoclaw_availability, write_geoclaw_setup_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report whether GeoClaw is importable and runnable.")
    parser.add_argument("--allow-unavailable", action="store_true", help="Return 0 even if GeoClaw is not installed.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/geoclaw_reference"))
    args = parser.parse_args(argv)

    availability = check_geoclaw_availability()
    if args.check:
        print(f"available={availability.available}")
        print(f"reason={availability.reason}")
        print(f"missing_modules={','.join(availability.missing_modules)}")
        print(f"missing_executables={','.join(availability.missing_executables)}")
        write_geoclaw_setup_report(args.output_dir, availability)
        return 0 if availability.available or args.allow_unavailable else 1

    report_path = write_geoclaw_setup_report(args.output_dir, availability)
    print(f"GeoClaw setup report={report_path}")
    if not availability.available:
        print(f"GeoClaw unavailable: {availability.reason}")
        return 0 if args.allow_unavailable else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
