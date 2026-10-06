"""Decode complete local engine clips; measure image changes, not physical FPS."""
from pathlib import Path
import json
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/water-motion-review-deps'))
import av
import numpy as np

OUT = ROOT / 'docs/reconstruction-review-2026-09-07/detail-motion'
ROIS = dict(terrain=(850,110,1150,170), foam_face=(60,380,480,650),
            dark_water=(950,430,1220,680), crest=(500,280,770,420))


def analyze(label, log_dir=None, save_times=(1,8,16,23)):
    log_path = (Path(log_dir) if log_dir is not None else ROOT / 'unreal/Saved/Logs') / (label + '.log')
    log = log_path.read_text(encoding='utf-8', errors='replace')
    match = re.search(r'recording saved: (.+?\.mp4) \((\d+) source_frames, ([\d.]+) s;', log)
    if not match:
        raise RuntimeError('No finalized recording in ' + str(log_path))
    path = Path(match[1]); source_count = int(match[2]); source_duration = float(match[3])
    stats = {name:dict(changes=[], gradients=[]) for name in ROIS}
    frames=[]; previous=None; times=[]; duplicate_count=0; saved=[]
    save_at=iter(save_times); next_save=next(save_at, None)
    with av.open(str(path)) as container:
        for frame in container.decode(video=0):
            t=float(frame.pts*frame.time_base)
            gray=frame.to_ndarray(format='gray').astype(np.float32)
            if gray.shape != (720,1280):
                raise RuntimeError('Unexpected capture resolution')
            if times and t<=times[-1]:
                raise RuntimeError('Non-increasing decoded presentation timestamps')
            entry=dict(t=t, roi={})
            if previous is not None and t>=1:
                duplicate_count+=int(np.array_equal(gray,previous))
                for name,(x0,y0,x1,y1) in ROIS.items():
                    region=gray[y0:y1,x0:x1]
                    change=float(np.mean(np.abs(region-previous[y0:y1,x0:x1])))
                    gradient=float(np.sqrt((np.mean(np.diff(region,axis=0)**2)+np.mean(np.diff(region,axis=1)**2))/2))
                    stats[name]['changes'].append(change);stats[name]['gradients'].append(gradient)
                    entry['roi'][name]=dict(mean_absolute_frame_change=change,spatial_gradient_rms=gradient)
            if next_save is not None and t>=next_save:
                frame_path=OUT / f'{label}_{next_save:02d}s.png'
                # Unmodified decoded source frame, not a generated illustration.
                frame.to_image().save(frame_path);saved.append(str(frame_path))
                next_save=next(save_at, None)
            frames.append(entry);times.append(t);previous=gray
    if len(times)<2:
        raise RuntimeError('Empty motion recording')
    for values in stats.values():
        for key in ('changes','gradients'):
            data=np.array(values.pop(key))
            values[key]=dict(mean=float(data.mean()),median=float(np.median(data)),
                             p95=float(np.quantile(data,0.95)),maximum=float(data.max()))
    report=dict(video=str(path),source_frames_from_engine=source_count,source_duration_seconds=source_duration,
                decoded_frames=len(times),first_pts_seconds=times[0],last_pts_seconds=times[-1],
                maximum_presentation_delta_seconds=float(np.max(np.diff(times))),
                exact_duplicate_decoded_frames_after_first_second=duplicate_count,
                roi_bounds_xyxy=ROIS,roi_statistics=stats,extracted_frames=saved,
                limitations='Luma image-change metrics only. Compression and temporal reconstruction contribute; no world-space velocity, physical amplitude, game FPS or photographic acceptance inferred.')
    (OUT / (label+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    (OUT / (label+'-frames.json')).write_text(json.dumps(frames,separators=(',',':')),encoding='utf-8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('labels', nargs='*', default=['DetailMotionBaseline','DetailMotionSecondOrder'])
    parser.add_argument('--log-dir', type=Path, default=ROOT/'unreal/Saved/Logs')
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--save-times', type=int, nargs='+', default=[1,8,16,23])
    args=parser.parse_args()
    if args.save_times != sorted(set(args.save_times)) or min(args.save_times)<0:
        parser.error('save times must be distinct, increasing, nonnegative seconds')
    OUT=args.output
    OUT.mkdir(parents=True,exist_ok=True)
    for label in args.labels:
        if Path(label).name != label or (OUT/(label+'.json')).exists():
            parser.error('use a simple label and a fresh output path')
    reports=[analyze(label,args.log_dir,args.save_times) for label in args.labels]
    print(json.dumps(reports,indent=2))
