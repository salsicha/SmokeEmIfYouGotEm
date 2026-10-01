"""Move L_Zambezi's 25 editor-only rapid markers to the scenario's observed stations.

Run inside the editor:

    RAFTSIM_REPO_ROOT=D:/repos/SmokeEmIfYouGotEm \
    UnrealEditor-Cmd SmokeEmIfYouGotEm.uproject -ExecutePythonScript=unreal/Scripts/place_zambezi_observed_rapid_markers.py

The landscape-candidate builder (AddLandscapeCandidateScenarioMarkers) places
one hidden cone and label per scenario rapid at its station on the corridor
centreline. scenario.json now carries observed stations (Sentinel-2
whitewater, side-stream confluences, outfitter km; digitised_map_station_m keeps
the stylised map's), so the saved markers are moved and relabelled the same way
without regenerating the 30 km map. The Landscape's world offset is recovered
from the existing markers at their digitised stations and checked across all of
them. Marker Z is the Landscape height (line trace) + 6.5 m, as the builder
does. The river water config's observed-whitewater gain is set in the same
save (RAFTSIM_OBSERVED_WHITEWATER_GAIN, default 0.25). A JSON report is written
to RAFTSIM_ZAMBEZI_MARKER_REPORT when set.
"""
import json
import math
import os

import unreal

ROOT = os.environ.get('RAFTSIM_REPO_ROOT', '')
MAP = '/Game/RaftSim/Maps/L_Zambezi'
GAIN = float(os.environ.get('RAFTSIM_OBSERVED_WHITEWATER_GAIN', '0.25'))
REPORT = os.environ.get('RAFTSIM_ZAMBEZI_MARKER_REPORT', '')
SCENARIO = 'physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/scenario.json'
CENTRELINE = ('physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/'
              'hydrography/centerline_local.json')


def load(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return json.load(f)


def local_at(points, station):
    """Centreline local cm and unit tangent at a station (linear between points)."""
    for a, b in zip(points, points[1:]):
        if station <= b['station_m']:
            t = max(0.0, min(1.0, (station - a['station_m']) / max(b['station_m'] - a['station_m'], 1e-6)))
            ax, ay = a['unreal_local_cm']; bx, by = b['unreal_local_cm']
            n = math.hypot(bx - ax, by - ay) or 1.0
            return (ax + t * (bx - ax), ay + t * (by - ay)), ((bx - ax) / n, (by - ay) / n)
    p = points[-1]['unreal_local_cm']
    return (p[0], p[1]), (1.0, 0.0)


def main():
    assert ROOT, 'set RAFTSIM_REPO_ROOT'
    scenario = load(SCENARIO)
    points = load(CENTRELINE)['points']
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    assert world, MAP
    markers = {}
    for actor in unreal.GameplayStatics.get_all_actors_with_tag(world, 'RaftSimScenarioMarker'):
        if actor.actor_has_tag('RaftSimZambeziRun'):
            label = actor.get_actor_label()
            markers[label.split('_')[2]] = actor
    assert len(markers) == 25, len(markers)
    # Landscape world offset from the existing markers at their digitised stations
    offsets = []
    for rapid in scenario['rapids']:
        actor = markers[rapid['rapid_number']]
        (lx, ly), _ = local_at(points, rapid['digitised_map_station_m'])
        loc = actor.get_actor_location()
        offsets.append((loc.x - lx, loc.y - ly))
    ox = sum(o[0] for o in offsets) / len(offsets); oy = sum(o[1] for o in offsets) / len(offsets)
    spread = max(math.hypot(o[0] - ox, o[1] - oy) for o in offsets)
    assert spread < 50.0, f'markers disagree on the Landscape offset by {spread:.1f} cm'
    rows = []
    for rapid in scenario['rapids']:
        actor = markers[rapid['rapid_number']]
        (lx, ly), (tx, ty) = local_at(points, rapid['station_m'])
        x, y = ox + lx, oy + ly
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, 2.0e6), unreal.Vector(x, y, -2.0e6), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, [], unreal.DrawDebugTrace.NONE, True)
        old = actor.get_actor_location()
        z = old.z
        if hit:
            hr = hit.to_tuple()
            if hr[0]:   # blocking hit
                z = hr[4].z + 650.0
        name = rapid['display_name']
        portage = rapid['mandatory_commercial_portage']
        actor.modify()
        actor.set_actor_location(unreal.Vector(x, y, z), False, False)
        actor.set_actor_label('RaftSim_ZambeziRapid_%s_%s' % (rapid['rapid_number'], name.replace(' ', '_')))
        for comp in actor.get_components_by_class(unreal.TextRenderComponent):
            comp.modify()
            comp.set_text('%s  %s%s' % (rapid['rapid_number'], name, '  PORTAGE' if portage else ''))
            comp.set_relative_rotation(unreal.Rotator(-90.0, math.degrees(math.atan2(ty, tx)), 0.0), False, False)
        rows.append(dict(rapid=rapid['rapid_number'], name=name, from_station_m=rapid['digitised_map_station_m'],
                         to_station_m=rapid['station_m'], moved_m=round(math.hypot(x - old.x, y - old.y) / 100.0, 1),
                         z_from_trace=bool(hit and hit.to_tuple()[0])))
    config_class = unreal.load_class(None, '/Script/RaftSimWater.RaftSimRiverWaterConfig')
    configs = unreal.GameplayStatics.get_all_actors_of_class(world, config_class)
    assert len(configs) == 1, len(configs)
    configs[0].modify()
    configs[0].set_editor_property('observed_whitewater_gain', GAIN)
    saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP))
    report = dict(map=MAP, landscape_offset_cm=[ox, oy], offset_spread_cm=spread, markers=rows,
                  observed_whitewater_gain=GAIN, saved=saved)
    unreal.log('RaftSim Zambezi observed markers: ' + json.dumps(report))
    if REPORT:
        with open(REPORT, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=1)


main()
