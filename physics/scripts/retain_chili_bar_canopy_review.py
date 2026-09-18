"""Retain exact engine/source evidence without implying visual or FPS acceptance."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'docs/reconstruction-review-2026-09-07/chili-bar-canopy'
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/chili_bar/canopy_20260918'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError('Preserve existing review evidence')
    copies = {}
    records = {}
    for role,label in [('before','south-fork-putin-canopy-baseline-v1-20260918'),
                       ('after','south-fork-putin-canopy-after-v1-20260918')]:
        process = ROOT/f'unreal/Saved/RaftSimValidation/{label}-process.json'
        motion = ROOT/f'tmp/chili-bar-canopy-motion-v1-20260918/{label}.json'
        evidence = json.loads(process.read_text()); decode = json.loads(motion.read_text())
        assert evidence['game_exit_code'] == 0 and not evidence['game_timeout']
        assert evidence['suspend_status'] == evidence['resume_status'] == 0
        assert evidence['normal_scenario_start'] and evidence['solver_lane_limit_confirmed']
        assert evidence['solver_lane_limit_requested'] == 4 and len(evidence['startup_frames']) == 24
        assert not any('RaftSimWaterReviewStation' in arg for arg in evidence['game_arguments'])
        video = Path(evidence['startup_motion']['path'])
        assert sha(video) == evidence['startup_motion']['sha256']
        assert decode['source_frames_from_engine'] == evidence['startup_motion']['source_frames']
        assert decode['source_duration_seconds'] == evidence['startup_motion']['duration_seconds']
        assert decode['decoded_frames'] > 1 and decode['last_pts_seconds'] >= decode['source_duration_seconds']-.1
        for frame in evidence['startup_frames']:
            assert sha(Path(frame['path'])) == frame['sha256']
        copies[role+'-process.json'] = process
        copies[role+'-decoded-motion.json'] = motion
        copies[role+'-player-view.png'] = ROOT/f'unreal/Saved/Screenshots/{label}_007.png'
        copies[role+'-motion-13s.png'] = ROOT/f'tmp/chili-bar-canopy-motion-v1-20260918/{label}_13s.png'
        records[role] = dict(video=video.relative_to(ROOT).as_posix(),video_sha256=sha(video),
            source_frames=decode['source_frames_from_engine'],duration_seconds=decode['source_duration_seconds'],
            decoded_frames=decode['decoded_frames'],encoding_rate_is_not_game_fps=True,
            log_sha256=sha(ROOT/f'unreal/Saved/Logs/{label}.log'))
    for role in ('before','after'):
        label = f'south-fork-putin-canopy-fps-{role}-v1-20260918'
        process = ROOT/f'unreal/Saved/RaftSimValidation/{label}-process.json'
        csv = ROOT/f'unreal/Saved/Profiling/CSV/{label}.csv'
        audit = ROOT/f'tmp/chili-bar-canopy-fps-{role}-v1-20260918.json'
        evidence = json.loads(process.read_text()); result = json.loads(audit.read_text())['runs'][0]
        assert evidence['game_exit_code'] == 0 and not evidence['game_timeout']
        assert evidence['suspend_status'] == evidence['resume_status'] == 0
        assert evidence['normal_scenario_start'] and evidence['profile_frames'] == 900
        assert evidence['solver_lane_limit_requested'] == 4 and evidence['solver_lane_limit_confirmed']
        assert evidence['csv_frame_time_mode_confirmed'] and evidence['csv_frame_time_scope_offset'] == 1
        assert sha(csv) == evidence['csv_sha256'] == result['sha256']
        assert result['total_samples'] == 900 and result['sample_indices_inclusive'] == [60,840]
        assert result['metrics']['target_fps'] == 30 and result['metadata']['systemresolution.resx'] == '1280'
        copies[role+'-fps-process.json'] = process
        copies[role+'-fps.csv'] = csv
        copies[role+'-fps-audit.json'] = audit
        records[role]['performance'] = dict(fps=result['metrics']['elapsed_frame_fps'],
            p95_ms=result['metrics']['FrameTime']['p95_ms_nearest_rank'],
            passes_30fps_p95=result['metrics']['frame_p95_within_target_budget'])
    copies['integration.json'] = ROOT/'unreal/Saved/RaftSimValidation/chili-bar-canopy-integration-v1-20260918.json'
    copies['focused-tests.xml'] = ROOT/'tmp/chili-bar-canopy-focused-v1-20260918.xml'
    OUT.mkdir()
    copied = {}
    for name,original in copies.items():
        destination = OUT/name
        shutil.copyfile(original,destination)
        assert sha(destination) == sha(original)
        copied[name] = dict(original=original.relative_to(ROOT).as_posix(),sha256=sha(original))
    report = dict(schema='raftsim.chili_bar.canopy_review.v1',captures=records,retained_files=copied,
        source_manifest_sha256=sha(SOURCE/'source.json'),source_audit_sha256=sha(SOURCE/'source_audit.json'),
        placement_sha256=sha(SOURCE/'placement.json'),fresh_editor_audit_sha256=sha(SOURCE/'integration_audit.json'),
        source_inventory_is_not_measured_tree_inventory=True,
        visible_bank_canopy_integrated=True,tree_art_photoreal_accepted=False,
        terrain_water_and_hydraulic_geometry_unchanged=True,water_breaking_or_froth_improved=False,
        complete_scene_or_release_accepted=False,
        visual_review='Normal put-in bank canopy now visible. Repeated angular crown cards, uniform inferred species, dark understorey, missing finer ground vegetation and structures remain. No full-river canopy or water-realism acceptance.',
        comparison_limits='Same scene entry, camera, source assets and capture settings; elapsed gameplay trajectories are not synchronized pixel tests. Fixed rapid-view ROI names in the decoder are not semantic put-in measurements. Movie encoder repeats frames; use the separate CSVs for game timing.')
    with (OUT/'review.json').open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(records,indent=2))


if __name__ == '__main__':
    main()
