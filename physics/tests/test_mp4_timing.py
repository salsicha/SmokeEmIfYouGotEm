import runpy
from pathlib import Path
import struct

HELPERS = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/audit_mp4_timing.py'))


def box(kind, payload):
    return struct.pack('>I4s', len(payload)+8, kind)+payload


def test_video_timing_preserves_hitches_instead_of_frame_count_over_30():
    runs = [(9, 100), (1, 700), (10, 100)]
    stts = box(b'stts', bytes(4)+struct.pack('>I', len(runs))+b''.join(struct.pack('>II', *r) for r in runs))
    header = box(b'mdhd', bytes(12)+struct.pack('>II', 1000, 2600)+bytes(4))
    handler = box(b'hdlr', bytes(8)+b'vide'+bytes(12))
    data = box(b'moov', box(b'trak', box(b'mdia', header+handler+box(b'minf', box(b'stbl', stts)))))
    result = HELPERS['parse_video_timing'](data)
    assert result['sample_count'] == 20
    assert result['sample_duration_seconds'] == 2.6
    assert result['maximum_sample_delta_seconds'] == .7
    assert result['container_sample_count_over_30_seconds'] == 20/30


def test_mp4_box_parser_rejects_truncated_or_out_of_bounds_boxes():
    for data in [bytes(4), struct.pack('>I4s', 100, b'moov'), struct.pack('>I4s', 4, b'moov')]:
        try:
            list(HELPERS['boxes'](data))
        except ValueError:
            continue
        raise AssertionError('invalid MP4 bounds accepted')


def test_recorder_uses_payload_time_and_drains_after_shutdown():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimScreenRecorderSubsystem.cpp').read_text(encoding='utf-8')
    assert 'EncodedFrameCount * kRecordingFrameIntervalSeconds' not in source
    assert 'NowSeconds - RecordingStartSeconds' in source
    assert 'FApp::GetCurrentTime()' not in source
    assert 'FPlatformTime::Seconds()' in source
    assert 'Frame.GetPayload<FRecordingFramePayload>()' in source
    assert 'EndSeconds-PendingFrameSeconds' in source
    assert 'DurationSeconds * 10\'000\'000.0' in source
    stop = source.split('void URaftSimScreenRecorderSubsystem::StopRecording()', 1)[1].split('void URaftSimScreenRecorderSubsystem::WritePendingFrame', 1)[0]
    assert stop.index('FrameGrabber->Shutdown()') < stop.index('FrameGrabber->GetCapturedFrames()')
