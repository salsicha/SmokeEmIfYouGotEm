"""Assemble real UE screenshot frames; no generated/interpolated animation."""
import argparse
import json
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    report = json.loads((args.evidence / "automation/index.json").read_text(encoding="utf-8-sig"))
    tests = report["tests"]
    if not tests or any(test["state"] != "Success" for test in tests):
        raise SystemExit("Refusing to package failed native validation")
    paths = sorted(args.evidence.glob("transfer-*.png"))
    if len(paths) < 20:
        raise SystemExit("Missing transfer/hold/return frames")
    if [path.name for path in paths] != [f"transfer-{i:03d}.png" for i in range(len(paths))]:
        raise SystemExit("Non-contiguous native frame sequence")
    frames = [Image.open(path).convert("RGB") for path in paths]
    if any(frame.size != frames[0].size for frame in frames):
        raise SystemExit("Native frame dimensions changed")
    output = args.evidence / "high-side-animation.png"
    if output.exists():
        raise SystemExit("Preserve existing evidence; use a fresh capture label")
    # Native capture requests are 0.1 simulation seconds apart in the fixed
    # 30 Hz test. This is an animation review, not an FPS benchmark.
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print(f"{len(frames)} native frames: {output}")


if __name__ == "__main__":
    main()
