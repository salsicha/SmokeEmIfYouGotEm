"""Validate complete actual-input wet-edge queue/sweep measurements."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def summarize(report):
    rows = report["pairs"]
    if type(report.get("exact")) is not bool or len(rows) != 64:
        raise ValueError("Complete explicit 64-pair native report required")
    for i, row in enumerate(rows):
        if type(row["pair"]) is not int or row["pair"] != i:
            raise ValueError("Original integer pair sequence required")
        if type(row["phase"]) is not int or row["phase"] != i % 2 + 1:
            raise ValueError("Both original production phases required")
        if type(row["sweep_first"]) is not bool or row["sweep_first"] != bool(i // 2 % 2):
            raise ValueError("Both orders within each production phase required")
        if type(row["exact"]) is not bool:
            raise ValueError("Explicit native exactness required")
        for key in ("frame", "nx", "ny", "vertices", "mask_crc32"):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value != int(value) or value < 0:
                raise ValueError("Finite nonnegative integer native counts required")
        if row["nx"] <= 0 or row["ny"] <= 0 or row["vertices"] != row["nx"] * row["ny"]:
            raise ValueError("Complete rectangular grid required")
        if row["mask_crc32"] > 2**32 - 1:
            raise ValueError("Original uint32 mask checksum required")
        if row["frame"] < 120 or (i and row["frame"] < rows[i-1]["frame"]):
            raise ValueError("Original warmed frame order required")
        for key in ("queue_ms", "sweep_ms"):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]) or row[key] <= 0:
                raise ValueError("Finite positive original timings required")
    if rows[-1]["frame"] == rows[0]["frame"]:
        raise ValueError("Multiple actual frames required")
    if len({r["mask_crc32"] for r in rows}) < 2:
        raise ValueError("Changing actual masks required")
    groups = {}
    for phase in (0, 1, 2):
        for order in (None, False, True):
            selected = [r for r in rows if (phase == 0 or r["phase"] == phase)
                        and (order is None or r["sweep_first"] == order)]
            name = f"phase_{phase}_" + ("all" if order is None else "sweep_first" if order else "queue_first")
            groups[name] = dict(pairs=len(selected),
                queue_mean_ms=statistics.mean(r["queue_ms"] for r in selected),
                sweep_mean_ms=statistics.mean(r["sweep_ms"] for r in selected),
                sweep_faster_pairs=sum(r["sweep_ms"] < r["queue_ms"] for r in selected))
    return dict(exact_distances=report["exact"] and all(r["exact"] for r in rows),
        both_orders_and_phases_faster=all(g["sweep_mean_ms"] < g["queue_mean_ms"] for g in groups.values()),
        compared_distances=sum(r["vertices"] for r in rows),
        distinct_masks=len({r["mask_crc32"] for r in rows}),
        first_frame=rows[0]["frame"], last_frame=rows[-1]["frame"], groups=groups,
        scope="Actual two-phase integer distance CPU comparison; not ordinary FPS, motion, physics or release acceptance.",
        release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    payload = args.capture.read_bytes()
    result = summarize(json.loads(payload))
    result.update(capture=str(args.capture.resolve()), sha256=hashlib.sha256(payload).hexdigest())
    with args.report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if result["exact_distances"] and result["both_orders_and_phases_faster"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
