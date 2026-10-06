"""Observed-rapid catalogue for the 30 km Zambezi reference run (L_Zambezi), Rapids 1-25 (numpy only).

    build_zambezi_run_observed_rapids.py

The reference run placed its 25 rapids by digitising a stylised outfitter map
(victoria-falls-rapids-map.pdf): relative pin spacing scaled to a published
17-mile run. That map is not georeferenced. Observations place most rapids
elsewhere, some by more than a kilometre, and Rapid 25 and Mukuni Beach lie
past the digitised end of the run (27,359 m).

Observations used (batoka_run_observations_2026_09_30.json, researched
2026-09-30, every fact with its source and a confidence):

* Sentinel-2 whitewater on the route at low water (2024-10-08, 203 m3/s and
  2025-10-03, 283 m3/s), projected onto route_stationing.json;
* OpenStreetMap side-stream confluences (Masuwe R 8.79 km at the foot of
  Rapid 9, Songwe L 9.78 km below Rapid 10, ...), the Taita Falcon Lodge GPS
  fix ("above rapids 16 & 17", route 16,959 m), outfitter kilometres (Rapid 11
  at 10 km, Bobo Beach at 25 km, Rapid 25 / Mukuni Beach at 30 km) and the
  Batoka scheme's water-surface profile;
* outfitter, guidebook, trip-report and video descriptions of each rapid's
  features, sides and lines.

Rapids 1-5 come from the upper-gorge catalogue (upper_gorge_observed_rapids.json,
evidence-midline frame), moved onto the route by projecting each evidence
midline point onto the route polyline. That projection also shows that the
persistent Sentinel-2 whitewater at route 2.7-2.8 km, which an earlier audit
took for Stairway to Heaven, is the power-station tailrace cascade (route
2,673 m); Stairway's lip is at route ~3,145 m.

Frame: the run's curved station (river_coordinate_map.json, built from the
route; within ~10 m of route station) and lateral, positive to river left
(Zambia). The procedural channel is ~144 m wide everywhere, wider than the
30-60 m low-water river, so feature laterals are the described side at a
modest offset from the centre, not measurements.

Writes observed_rapids/batoka_run_observed_rapids.json (schema
raftsim.observed_rapid_features.v1, plus rapid_stations, the per-rapid
observed control station the procedural field and scenario use).
"""
import hashlib
import json
from pathlib import Path

import numpy as np

from geo_frames import tm_forward, utm

ROOT = Path(__file__).resolve().parents[2]
Z = ROOT / 'physics/data/real_world/zambezi_batoka_gorge'
OBS = Z / 'observed_rapids'
OUT = OBS / 'batoka_run_observed_rapids.json'
RESEARCH = OBS / 'batoka_run_observations_2026_09_30.json'
UPPER = OBS / 'upper_gorge_observed_rapids.json'

# Lateral offsets in the ~144 m procedural channel (positive river left).
L, LC, C, RC, R = 22.0, 10.0, 0.0, -10.0, -22.0

# Rapids 6-25: observed control station (the head of the main drop), span,
# class at low water, confidence and the evidence that places it (route m).
RAPIDS = [
    # number, name, aliases, control, start, end, class, confidence, evidence
    ('6', "Devil's Toilet Bowl", [], 4710, 4690, 4850, 'III-IV', 'medium',
     'west end of the 4th Gorge (ERM rapid map); Sentinel-2 whitewater 4.75-4.80 km on both low-water dates'),
    ('7', "Gulliver's Travels", ['Gullivers Travels'], 6140, 5950, 6550, 'V', 'medium',
     '~700 m of class V (outfitters); Sentinel-2 whitewater 6.15-6.40 km on both low-water dates; 7B 6.70-6.85 km'),
    ('8', 'Midnight Diner', ['Star Trek'], 7770, 7750, 7900, 'III-IV', 'medium',
     'Sentinel-2 whitewater 7.80-7.90 km on all three dates up to 904 m3/s; calm pool below'),
    ('9', 'Commercial Suicide', [], 8590, 8550, 8800, 'V-VI', 'medium-high',
     'the most persistent whitewater on the run (8.60-8.80 km on all four dates); Masuwe River (OSM) joins river right '
     'at 8.79 km at its foot'),
    ('10', 'Gnashing Jaws of Death', [], 9310, 9300, 9500, 'III-IV', 'medium',
     'Sentinel-2 whitewater ~9.3-9.45 km; Songwe River joins river left at 9.78 km below the camp beach under Rapid 10'),
    ('11', 'Overland Truck Eater', ['Creamy White Buttocks'], 10560, 10500, 10750, 'IV-V', 'medium',
     'Sentinel-2 whitewater 10.65-10.75 km; "10 km" from the Falls (Shearwater; Sierra Rios km 10); hairpin into the '
     'Songwe Gorge'),
    ('12', 'Three Ugly Sisters', ['Three Sisters', 'Three Little Pigs'], 12040, 12000, 12650, 'III', 'low',
     '"a kilometre of near-continuous action" (12A-12C) in the narrow Songwe Gorge between Rapids 11 and 13'),
    ('13', 'The Mother', [], 12710, 12700, 12900, 'IV', 'low-medium',
     'Sentinel-2 whitewater ~12.70 km; big S-bend pool below'),
    ('14', 'Surprise Surprise', ['Rapid 14'], 13640, 13600, 13900, 'III', 'low-medium',
     'the only S-bend constriction 13.6-13.9 km; Sentinel-2 whitewater ~13.90 km at 203 m3/s'),
    ('15', 'The Washing Machine', ['Washing Machine'], 15820, 15800, 15950, 'IV-V', 'low',
     'Sentinel-2 whitewater ~15.85-15.95 km; Zambian tributary river left at 15.44 km above it'),
    ('16', 'The Terminators', ['Terminator I & II'], 16120, 16100, 16600, 'III', 'low-medium',
     '16A island split and 16B wave train 16.1-16.6 km; Taita Falcon Lodge on the Zambian rim at route 16,959 m sits '
     '"above rapids 16 & 17"'),
    ('17', 'Double Trouble', ['The Bitch'], 17170, 17150, 17350, 'IV-V', 'medium',
     'Sentinel-2 whitewater ~17.25 km at the head of the S-running reach, below Taita Falcon Lodge; deep pool below'),
    ('18', 'Oblivion', [], 18370, 18350, 18500, 'IV-V', 'medium',
     'Sentinel-2 white bar 18.40-18.45 km on both low-water dates'),
    ('19', 'Rapid 19', [], 22470, 22450, 22600, 'II-III', 'low',
     'unnamed in every source ("The Last Straw" is unattested); candidate just below the 11 km Zimbabwe tributary at '
     '22.43 km (alternatives 19.9-21.3 km)'),
    ('20', 'Rapid 20', [], 22950, 22900, 23300, 'II-III', 'low',
     'unnamed; the Zimbabwe take-out is on the right at Rapid 20; Sentinel-2 whitewater ~22.95 km and sand river right '
     '22.9-23.1 km'),
    ('21', 'Rapid 21', [], 23960, 23950, 24150, 'II-III', 'low',
     'unnamed; finishes river left onto Bobo Beach (Zambia take-out, Sierra Rios km 25; sand river left ~24.35 km)'),
    ('22', 'Morning Shave', [], 24470, 24450, 24650, 'II-III', 'low-medium',
     'first rapid below Bobo Beach; Sentinel-2 whitewater 24.40-24.55 km (1-2 pixels)'),
    ('23', 'Morning Shower', [], 25250, 25200, 26000, 'III', 'low',
     'long wave train round a right-hand bend ending in a constricted cauldron; candidate 25.2-26.0 km'),
    ('24', 'Rapid 24', [], 27450, 27400, 27650, 'II-III', 'low',
     'long rapid with many waves and a surf wave; Sentinel-2 whitewater ~27.40-27.60 km (1 pixel)'),
    ('25', 'Rapid 25', ['Closed Season'], 28270, 28250, 28450, 'II-III', 'low',
     'last rapid above Mukuni Beach (the largest sand beach on the route, river left 28.85-29.0 km, with the cable car); '
     'Sierra Rios km 30, whitewaterguidebook mile 17'),
]

# Expected whitewater features for Rapids 6-25 (station = control + offset).
FEATURES = {
    '6': [dict(id='r6_entry_hole', type='ledge_hole', off=10, lat=C, width_m=14),
          dict(id='r6_surging_waves', type='wave_train', off=30, lat=C, width_m=28, waves=2, wavelength_m=14.0),
          dict(id='r6_left_hole', type='ledge_hole', off=55, lat=L, width_m=8)],
    '7': [dict(id='r7_indicator_rock_garden', type='rock_garden', off=-150, lat=LC, width_m=24, length_m=60),
          dict(id='r7_green_highway', type='wave_train', off=-80, lat=RC, width_m=18, waves=4, wavelength_m=10.0),
          dict(id='r7_directors_wave', type='lateral', off=0, lat=-14.0, width_m=20, angle_deg=35),
          dict(id='r7_the_crease', type='ledge_hole', off=40, lat=L, width_m=14),
          dict(id='r7_the_gap', type='rock_garden', off=120, lat=R, width_m=14, length_m=40),
          dict(id='r7_land_of_the_giants', type='wave_train', off=220, lat=C, width_m=36, waves=6, wavelength_m=16.0),
          dict(id='r7b_waves', type='wave_train', off=570, lat=C, width_m=24, waves=4, wavelength_m=11.0)],
    '8': [dict(id='r8_star_trek_hole', type='ledge_hole', off=20, lat=LC + 4.0, width_m=16),
          dict(id='r8_muncher_waves', type='wave_train', off=10, lat=RC, width_m=14, waves=2, wavelength_m=12.0),
          dict(id='r8_chicken_run', type='rock_garden', off=0, lat=R, width_m=14, length_m=110),
          dict(id='r8_bottom_waves', type='wave_train', off=70, lat=C, width_m=26, waves=3, wavelength_m=11.0)],
    '9': [dict(id='r9_river_wide_pour_over', type='pour_over', off=0, lat=-6.0, width_m=60),
          dict(id='r9_left_diagonal', type='diagonal', off=5, lat=30.0, width_m=16, angle_deg=-40),
          dict(id='r9_bottom_wave_hole', type='ledge_hole', off=70, lat=C, width_m=26),
          dict(id='r9_hero_hole', type='ledge_hole', off=105, lat=26.0, width_m=8),
          dict(id='r9_elbow_rock_garden', type='rock_garden', off=95, lat=-18.0, width_m=14, length_m=30)],
    '10': [dict(id='r10_top_hole', type='ledge_hole', off=5, lat=C, width_m=10),
           dict(id='r10_green_tongue_waves', type='wave_train', off=25, lat=-4.0, width_m=24, waves=5, wavelength_m=12.0),
           dict(id='r10_bottom_left_rocks', type='rock_garden', off=120, lat=L, width_m=14, length_m=50)],
    '11': [dict(id='r11_left_v_tongue', type='wave_train', off=0, lat=26.0, width_m=16, waves=3, wavelength_m=10.0),
           dict(id='r11_top_hole', type='ledge_hole', off=5, lat=-4.0, width_m=34),
           dict(id='r11_left_diagonal', type='diagonal', off=45, lat=16.0, width_m=18, angle_deg=-35),
           dict(id='r11_island_wave', type='wave_train', off=110, lat=C, width_m=22, waves=2, wavelength_m=14.0)],
    '12': [dict(id='r12a_top_left_hole', type='ledge_hole', off=10, lat=LC, width_m=8),
           dict(id='r12a_lower_right_hole', type='ledge_hole', off=60, lat=RC, width_m=8),
           dict(id='r12a_right_wave', type='wave_train', off=80, lat=R, width_m=14, waves=2, wavelength_m=12.0),
           dict(id='r12b_river_wide_wave', type='wave_train', off=280, lat=C, width_m=60, waves=1, wavelength_m=14.0),
           dict(id='r12b_waves', type='wave_train', off=300, lat=C, width_m=24, waves=4, wavelength_m=10.0),
           dict(id='r12c_waves', type='wave_train', off=520, lat=C, width_m=22, waves=4, wavelength_m=9.0)],
    '13': [dict(id='r13_first_wave', type='wave_train', off=0, lat=-4.0, width_m=34, waves=1, wavelength_m=18.0),
           dict(id='r13_left_diagonal', type='diagonal', off=5, lat=24.0, width_m=14, angle_deg=-30),
           dict(id='r13_five_waves', type='wave_train', off=22, lat=C, width_m=30, waves=5, wavelength_m=16.0)],
    '14': [dict(id='r14_left_channel_waves', type='wave_train', off=10, lat=28.0, width_m=16, waves=4, wavelength_m=8.0),
           dict(id='r14_centre_pour_over', type='pour_over', off=60, lat=C, width_m=14),
           dict(id='r14_right_pour_over', type='pour_over', off=60, lat=-26.0, width_m=10)],
    '15': [dict(id='r15_tongue_waves', type='wave_train', off=0, lat=C, width_m=24, waves=4, wavelength_m=12.0),
           dict(id='r15_crossing_diagonal', type='diagonal', off=30, lat=14.0, width_m=14, angle_deg=-35),
           dict(id='r15_washing_machine_hole', type='ledge_hole', off=75, lat=C, width_m=24)],
    '16': [dict(id='r16a_island_split_rocks', type='rock_garden', off=0, lat=C, width_m=20, length_m=40),
           dict(id='r16a_left_hole', type='ledge_hole', off=50, lat=-6.0, width_m=8),
           dict(id='r16b_surf_wave', type='wave_train', off=300, lat=LC, width_m=18, waves=1, wavelength_m=10.0),
           dict(id='r16b_waves', type='wave_train', off=315, lat=LC, width_m=24, waves=5, wavelength_m=12.0),
           dict(id='r16_bottom_hole', type='ledge_hole', off=420, lat=C, width_m=10)],
    '17': [dict(id='r17_tongue', type='wave_train', off=0, lat=C, width_m=18, waves=2, wavelength_m=10.0),
           dict(id='r17_hole_left', type='ledge_hole', off=40, lat=LC + 2.0, width_m=14),
           dict(id='r17_hole_centre', type='ledge_hole', off=40, lat=-4.0, width_m=14),
           dict(id='r17_bottom_rock', type='rock_garden', off=110, lat=6.0, width_m=10, length_m=20)],
    '18': [dict(id='r18_v_waves', type='wave_train', off=0, lat=C, width_m=30, waves=2, wavelength_m=16.0),
           dict(id='r18_oblivion_third_wave_hole', type='ledge_hole', off=38, lat=C, width_m=22),
           dict(id='r18b_loop_hole', type='ledge_hole', off=150, lat=C, width_m=8)],
    '19': [dict(id='r19_surf_wave', type='wave_train', off=10, lat=C, width_m=18, waves=3, wavelength_m=9.0)],
    '20': [dict(id='r20_waves', type='wave_train', off=20, lat=C, width_m=20, waves=4, wavelength_m=9.0)],
    '21': [dict(id='r21_waves', type='wave_train', off=20, lat=C, width_m=20, waves=4, wavelength_m=9.0)],
    '22': [dict(id='r22_splashy_waves', type='wave_train', off=10, lat=LC, width_m=20, waves=6, wavelength_m=9.0)],
    '23': [dict(id='r23_wave_train', type='wave_train', off=10, lat=C, width_m=26, waves=10, wavelength_m=12.0),
           dict(id='r23_left_push_lateral', type='lateral', off=150, lat=-16.0, width_m=16, angle_deg=30),
           dict(id='r23_cauldron_waves', type='wave_train', off=300, lat=C, width_m=22, waves=3, wavelength_m=9.0)],
    '24': [dict(id='r24_waves', type='wave_train', off=10, lat=C, width_m=24, waves=8, wavelength_m=11.0),
           dict(id='r24_surf_wave', type='wave_train', off=110, lat=LC, width_m=16, waves=1, wavelength_m=10.0)],
    '25': [dict(id='r25_left_waves', type='wave_train', off=10, lat=L, width_m=20, waves=5, wavelength_m=9.0),
           dict(id='r25_right_pour_over', type='pour_over', off=60, lat=-24.0, width_m=10)],
}
FEATURE_SOURCE = {'ledge_hole': 'hole', 'pour_over': 'pour-over', 'wave_train': 'waves', 'lateral': 'lateral',
                  'diagonal': 'diagonal', 'rock_garden': 'rocks'}
MUKUNI_BEACH_M = (28850.0, 29000.0)
FINISH_STATION_M = 28950.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def evidence_to_route():
    """Map evidence-midline stations of the upper gorge onto the route by projecting each midline point."""
    c = json.loads((Z / 'scenario_upper_gorge_evidence_2025/evidence/evidence_centreline.json').read_text())
    P = np.array(c['points_xy_station'], float)
    route = json.loads((Z / 'production_corridor/boiling_pot_to_mukuni_beach/hydrography/route_stationing.json').read_text())
    lon = np.array([s['lon'] for s in route['samples']]); lat = np.array([s['lat'] for s in route['samples']])
    sta = np.array([s['station_m'] for s in route['samples']])
    rx, ry = tm_forward(lon, lat, utm(35, south=True))
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(rx), np.diff(ry)))])
    dd = np.arange(0.0, cum[-1], 2.0)
    dx, dy, ds = np.interp(dd, cum, rx), np.interp(dd, cum, ry), np.interp(dd, cum, sta)
    ev, rt = [], []
    for x, y, s in P[::5]:
        i = int(np.argmin((dx - x) ** 2 + (dy - y) ** 2))
        ev.append(s); rt.append(ds[i])
    rt = np.maximum.accumulate(np.array(rt))
    return lambda s: float(np.interp(s, ev, rt))


def main():
    research = json.loads(RESEARCH.read_text(encoding='utf-8'))
    by_number = {str(r['number']): r for r in research['rapids']}
    to_route = evidence_to_route()
    upper = json.loads(UPPER.read_text(encoding='utf-8'))
    rapids, features, stations = [], [], []

    # Rapids 1-5 (and the upper gorge's sub-rapids) from the upper-gorge catalogue
    upper_names = {'r1_the_wall': ('1', 'Against the Wall'), 'r2_the_bridge': ('2', 'The Bridge'), 'r3': ('3', 'Rapid 3'),
                   'r4_morning_glory': ('4', 'Morning Glory'), 'r5_stairway_to_heaven': ('5', 'Stairway to Heaven')}
    for r in upper['rapids']:
        a0 = to_route(r['station_m']); a1 = to_route(r['station_m'] + r['length_m'])
        rapids.append(dict(id=r['id'], station_m=round(a0, 1), length_m=round(a1 - a0, 1), rapid_class=r['rapid_class'],
                           source='upper_gorge_observed_rapids.json (evidence station %.0f m, projected onto the route)' % r['station_m']))
        if r['id'] in upper_names:
            num, name = upper_names[r['id']]
            control = 160.0 if num == '1' else round(a0 + 15.0, 1)
            stations.append(dict(rapid_number=num, name=name, aliases=by_number[num]['names'][1:] if num == '2' else [],
                                 control_station_m=control, span_m=[round(a0, 1), round(a1, 1)],
                                 rapid_class=by_number[num]['class_low_water'].split(' (')[0], confidence='medium-high',
                                 evidence='upper-gorge observations (outfitters, WorldView-3 2023-11-26, a 2019 titled video) '
                                          'projected from the evidence midline onto the route'
                                          + ('; the run keeps its procedural control at 160 m behind the calm launch apron' if num == '1' else '')))
    for q in upper['features']:
        if q['type'] == 'sill':
            continue   # bed-only shape of the evidence cook, no appearance of its own
        f = {k: v for k, v in q.items() if k not in ('sources', 'crest_below_ws_m', 'drop_m', 'span_m', 'amplitude_m')}
        f['station_m'] = round(to_route(q['station_m']), 1)
        f['source'] = 'upper_gorge_observed_rapids.json'
        features.append(f)

    # Rapids 6-25
    for num, name, aliases, control, a0, a1, cls, conf, evidence in RAPIDS:
        rec = by_number[num]
        stations.append(dict(rapid_number=num, name=name, aliases=aliases, control_station_m=float(control),
                             span_m=[float(a0), float(a1)], rapid_class=cls, confidence=conf, evidence=evidence))
        rapids.append(dict(id=f'r{num}', station_m=float(a0), length_m=float(a1 - a0), rapid_class=cls,
                           source='batoka_run_observations_2026_09_30.json rapid %s' % num))
        described = {f.get('type') for f in rec.get('features', [])}
        for q in FEATURES[num]:
            f = {k: v for k, v in q.items() if k not in ('off', 'lat')}
            f['station_m'] = float(control + q['off']); f['lateral_m'] = float(q['lat'])
            f['source'] = 'batoka_run_observations_2026_09_30.json rapid %s (%s)' % (num, FEATURE_SOURCE[q['type']])
            features.append(f)
        assert described, num
    order = [int(s['rapid_number']) for s in stations]
    assert order == list(range(1, 26)), order
    ctrl = [s['control_station_m'] for s in stations]
    assert all(b - a >= 150.0 for a, b in zip(ctrl, ctrl[1:])), 'controls must keep their procedural jumps apart'
    cat = dict(
        schema='raftsim.observed_rapid_features.v1',
        reach='zambezi_batoka_gorge reference run (Boiling Pot to Mukuni Beach, low water ~200-300 m3/s)',
        station_frame='scenario',
        frame_note=('run station of scenario_zambezi_run/runtime/river_coordinate_map.json (built from route_stationing.json, '
                    'within ~10 m of route station); lateral positive to river left (Zambia). The procedural channel is '
                    '~144 m wide, so laterals are the described sides at modest offsets, not measurements'),
        observations=RESEARCH.name, observations_sha256=sha(RESEARCH),
        upper_gorge_catalogue=UPPER.name, upper_gorge_catalogue_sha256=sha(UPPER),
        placement_note=('control_station_m is the observed head of each rapid\'s main drop: Rapids 1-5 from the upper-gorge '
                        'observations projected onto the route, 6-25 from Sentinel-2 whitewater on the route, side-stream '
                        'confluences, the Taita Falcon Lodge fix and outfitter kilometres. The stylised-map digitisation '
                        '(reference/user_supplied/rapid_map_digitization.json) is kept as its own record'),
        tailrace_note=('the persistent Sentinel-2 whitewater at route 2.7-2.8 km is the ZESCO power-station tailrace cascade '
                       '(route 2,673 m), not Stairway to Heaven (lip ~3,145 m)'),
        take_out=dict(name='Mukuni Beach', bank='left', span_m=list(MUKUNI_BEACH_M), finish_station_m=FINISH_STATION_M,
                      evidence='the largest sand beach on the route in Sentinel-2 (river left 28.85-29.0 km); Rapid 25 / Mukuni '
                               'Beach at Sierra Rios km 30; cable car on the Zambian side'),
        sizing_note='feature sizes approximate described features (hole widths, wave counts and spacings); not measurements',
        rapid_stations=stations, rapids=rapids, features=features)
    OUT.write_text(json.dumps(cat, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    for s in stations:
        print(s['rapid_number'], s['name'], s['control_station_m'], s['span_m'], s['confidence'])
    print(len(rapids), 'rapid spans,', len(features), 'features')


if __name__ == '__main__':
    main()
