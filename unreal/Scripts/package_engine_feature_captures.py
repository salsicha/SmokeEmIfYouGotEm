"""Package actual Unreal backbuffer recordings; never synthesize water/boat poses."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image


def digest(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--motion", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--interval", type=float, default=0.25)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 120 or not 0.1 <= args.interval <= 2:
        raise RuntimeError("Use a bounded capture duration and sampling interval")
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "tmp/water-motion-review-deps"))
    import av
    if args.output.exists():
        raise RuntimeError("Preserve previous delivery; choose a fresh output")
    args.output.mkdir(parents=True)
    frames, selected_times, source_hashes = [], [], []
    next_time = 0.0
    total = 0
    with av.open(str(args.video)) as container:
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            total += 1
            t = float(frame.time)
            if t + 1e-6 < next_time or next_time > args.seconds:
                continue
            original = frame.to_image().convert("RGB")
            source_hashes.append(hashlib.sha256(original.tobytes()).hexdigest())
            selected_times.append(t)
            width = 800
            height = round(original.height * width / original.width)
            frames.append(original.resize((width, height), Image.Resampling.LANCZOS))
            if len(frames) == 1:
                original.save(args.output / "first.png")
            next_time += args.interval
    if len(frames) < 8 or total < len(frames):
        raise RuntimeError("Incomplete engine recording")
    frames[len(frames)//2].save(args.output / "middle.png")
    frames[-1].save(args.output / "last.png")
    frames[0].save(args.output / "animation.png", save_all=True,
        append_images=frames[1:], duration=round(args.interval*1000), loop=0, disposal=0, blend=0)
    with Image.open(args.output / "animation.png") as check:
        if check.n_frames != len(frames):
            raise RuntimeError("Playback frame count mismatch")
        for i, expected in enumerate(frames):
            check.seek(i)
            if check.convert("RGB").tobytes() != expected.tobytes():
                raise RuntimeError("Playback frame mismatch")
    shutil.copy2(args.video, args.output / "engine-recording.mp4")
    result = {"schema": "raftsim.engine_capture_delivery.v1",
              "source_video": str(args.video), "video_sha256": digest(args.video),
              "decoded_frames": total, "animation_frames": len(frames),
              "selected_video_seconds": selected_times,
              "selected_original_rgb_sha256": source_hashes,
              "adjacent_duplicate_frames": sum(a == b for a, b in zip(source_hashes, source_hashes[1:])),
              "scope": "Actual Unreal backbuffer frames, reduced-resolution APNG. Repeating playback is not a seamless simulation loop. No offline fluid or scripted boat animation."}
    if args.motion:
        motion = json.loads(args.motion.read_text(encoding="utf-8-sig"))
        if motion["failed"] or motion["simulated_seconds"] < 11.99:
            raise RuntimeError("Incomplete or failed boat-force run")
        rows = motion["motion"]
        times = [r["seconds"] for r in rows]
        gaps = [b-a for a, b in zip(times, times[1:])]
        maximum_gap = 0.25 if motion.get("collision_control", False) else 0.5
        # Receipts are sampled on render frames after fixed-step catch-up.
        # Qualify temporal coverage, not an arbitrary count that rejects a
        # complete 12-second run sampled every 0.10-0.18 seconds.
        if (len(rows) < 8 or times[0] > 0.25
                or motion["simulated_seconds"]-times[-1] > 0.25
                or any(g <= 0 or g > maximum_gap+1e-6 for g in gaps)):
            raise RuntimeError("Incomplete or sparse motion coverage")
        result["maximum_motion_sample_gap_seconds"] = max(gaps)
        result["motion_sampling_limit_seconds"] = maximum_gap
        result["motion_samples"] = len(rows)
        result["first_motion"] = rows[0]
        result["last_motion"] = rows[-1]
        result["boat_u_range_mps"] = [min(r["boat_u_mps"] for r in rows), max(r["boat_u_mps"] for r in rows)]
        result["boat_y_range_m"] = [min(r["y_m"] for r in rows), max(r["y_m"] for r in rows)]
        result["yaw_range_deg"] = [min(r["yaw_deg"] for r in rows), max(r["yaw_deg"] for r in rows)]
        shutil.copy2(args.motion, args.output / "boat-motion.json")
    (args.output / "capture.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("selected_original_rgb_sha256", "selected_video_seconds")}, indent=2))


if __name__ == "__main__":
    main()
