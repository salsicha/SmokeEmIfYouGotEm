"""Read MP4 video sample timing without decoding or modifying the recording."""
import argparse
import json
from pathlib import Path
import struct


def boxes(data):
    offset = 0
    while offset < len(data):
        if len(data)-offset < 8:
            raise ValueError('truncated MP4 box header')
        size, kind = struct.unpack_from('>I4s', data, offset)
        header = 8
        if size == 1:
            if len(data)-offset < 16:
                raise ValueError('truncated large MP4 box')
            size = struct.unpack_from('>Q', data, offset+8)[0]
            header = 16
        elif size == 0:
            size = len(data)-offset
        if size < header or offset+size > len(data):
            raise ValueError('invalid MP4 box bounds')
        yield kind, data[offset+header:offset+size]
        offset += size


def child(data, kind):
    found = [payload for name, payload in boxes(data) if name == kind]
    if len(found) != 1:
        raise ValueError(f'expected one {kind!r} box')
    return found[0]


def parse_video_timing(data):
    movie = child(data, b'moov')
    videos = []
    for kind, track in boxes(movie):
        if kind != b'trak':
            continue
        media = child(track, b'mdia')
        handler = child(media, b'hdlr')
        if handler[8:12] != b'vide':
            continue
        header = child(media, b'mdhd')
        if len(header) < 20 or header[0] not in (0, 1):
            raise ValueError('unsupported media header')
        if header[0] == 0:
            scale, duration = struct.unpack_from('>II', header, 12)
        else:
            if len(header) < 32:
                raise ValueError('truncated version-one media header')
            scale, duration = struct.unpack_from('>IQ', header, 20)
        if not scale:
            raise ValueError('zero video timescale')
        table = child(child(child(media, b'minf'), b'stbl'), b'stts')
        if len(table) < 8:
            raise ValueError('truncated sample timing table')
        entries = struct.unpack_from('>I', table, 4)[0]
        if len(table) != 8+8*entries or entries == 0:
            raise ValueError('invalid sample timing table')
        runs = [struct.unpack_from('>II', table, 8+8*i) for i in range(entries)]
        if any(n == 0 or delta == 0 for n, delta in runs):
            raise ValueError('zero sample count or duration')
        count = sum(n for n, _ in runs)
        sample_seconds = sum(n*delta for n, delta in runs)/scale
        videos.append(dict(timescale=scale, media_duration_seconds=duration/scale,
            sample_count=count, sample_duration_seconds=sample_seconds,
            mean_sample_rate_hz=count/sample_seconds,
            minimum_sample_delta_seconds=min(d for _, d in runs)/scale,
            maximum_sample_delta_seconds=max(d for _, d in runs)/scale,
            container_sample_count_over_30_seconds=count/30.,
            sample_timing_runs=[dict(count=n, duration_seconds=d/scale) for n, d in runs]))
    if len(videos) != 1:
        raise ValueError('expected one video track')
    return videos[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-frames', type=int,
        help='Successful source-frame writes from the game log; encoder may duplicate these.')
    args = parser.parse_args()
    if args.source_frames is not None and args.source_frames <= 0:
        parser.error('--source-frames must be positive')
    result = {'video': str(args.video.resolve()), **parse_video_timing(args.video.read_bytes()),
        'limitations': 'Container timing only. The encoder may repeat source frames; container sample rate is not game FPS. No proof of visual realism, image fidelity, correct physics, or performance.'}
    if args.source_frames is not None:
        result['source_frames_from_log'] = args.source_frames
        result['legacy_source_duration_at_30fps_seconds'] = args.source_frames/30.
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'sample_timing_runs'}, indent=2))
