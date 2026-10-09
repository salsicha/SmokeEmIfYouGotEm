"""Every-catalog-entry decision audit and matched native input experiments.

The numerical routes are game hypotheses, not guide instructions. The trial
driver uses normal controls; these gates do not alter water or boat forces.
Unbuilt/evidence-gap entries remain visible and cannot earn a class match.
"""
import argparse
import copy
import json
from pathlib import Path
from build_rapid_calibration import build as reference_plans
from report_rapid_assessment import inventory, ROOT
from rapid_missing_entry_decisions import definitions as missing_definitions

SOURCES = {
 'south-fork':'https://gorafting.com/united-states/california/south-fork-american/',
 'colorado':'https://gorafting.com/united-states/arizona/grand-canyon/hance-rapid/',
 'pacuare':'https://gorafting.com/costa-rica/pacuare-river/',
 'futaleufu':'https://gorafting.com/chile/futaleufu-river/',
 'chilko':'https://www.ukriversguidebook.co.uk/reports/north-america/a-golden-day-on-the-chilko',
 'zambezi':'https://thezambezi.com/zambezi-river-rapid-guide.html',
 'zambezi-upper':'https://thezambezi.com/zambezi-river-rapid-guide.html',
 'futaleufu-continuous':'https://gorafting.com/chile/futaleufu-river/',
}
# Qualitative comparison axes. A rapid can have a broad correct line and still
# require control; a catalog class is never a numerical target flip probability.
AXES = {
 'slalom': ('Successive obstacle gaps, not total wet width', 'Prepare the next gap before clearing the first', 'Hull impact or a blocked line', 'Backstroke, high-side and an available eddy exit'),
 'wall': ('Room between the hazard and opposing bank', 'Set the approach before the lateral or bend', 'Wall contact or lateral broach', 'Reorient before the next hazard; test the runout'),
 'hole': ('Usable routes around or squarely through the hydraulic', 'Establish angle and momentum before its lip', 'Retention, broach or swimmer, not a gate penalty', 'Ordinary strokes or rescue after a real incident'),
 'train': ('Broad lines may be legitimate', 'Square the raft and maintain the chosen line', 'Broadside wave hit rather than arbitrary rock contact', 'Use the documented runout without a reset'),
 'continuous': ('Connected usable lanes across successive hazards', 'Early positioning and repeated maneuvers without a reset', 'An error carries into the next feature', 'Stamina, crew recovery and downstream rescue opportunities'),
 'surf': ('Play feature and an ordinary bypass are both legitimate', 'Choose entry, surf and exit separately', 'Retention is not automatically an involuntary failure', 'Exit to the eddy or downstream using ordinary inputs'),
 'portage': ('No commercial raft route demanded', 'Stop and portage before commitment', 'Do not use a successful driven trial to validate this rapid', 'Portage, not a reset credited as rescue'),
 'unresolved': ('Source/registration insufficient', 'Not assigned without evidence', 'Not inferred from a place name or catalog class', 'Not established'),
}
DECISIONS = {('pacuare','lower_pinball'):2010, ('pacuare','upper_huacas'):640,
             ('pacuare','lower_huacas'):950, ('pacuare','upper_pinball'):1830,
             ('colorado','hance_main'):685, ('colorado','badger_creek'):760,
             ('futaleufu','terminator_core'):1180,
             ('futaleufu','son_of_terminator'):1430, ('futaleufu','khyber_pass'):1700,
             ('chilko','bidwell'):730, ('chilko','white_mile'):3590,
             ('zambezi','rapid_7'):6060, ('zambezi','rapid_15'):15850,
             ('zambezi','rapid_17'):17190, ('zambezi','rapid_18'):18390}
# id | documented decision / source feature | comparison family | initial,
# middle, exit lateral hypotheses. Positive is river-left. Exact known routes
# below replace these coarse screening hypotheses before any width sweep.
ROWS = {
'south-fork': '''chili_bar_hole|Surf choice and left eddy|surf|0,0,3
meat_grinder|Offset slots; Death Star and Rhino|slalom|0,-4,3
racehorse_bend|Right-wall lateral at the bend|wall|0,3,0
maya|Ordinary centre run; changes at high water|train|0,0,0
rock_garden|Weave around channel rocks|slalom|0,3,-3
african_queen|Right approach then cut left|slalom|-4,-4,4
triple_threat|Frog Rock followed by three threats|slalom|-4,-4,0
troublemaker|S-turn; diagonal; Gunsight exit|wall|0,-4,4
fowler_s_rock|House Rock and downstream rock/diagonal|slalom|0,3,-3
upper_haystack_canyon|Keep square through the wave train|train|0,0,0
lost_hat|Blind waves feeding Satan's|continuous|0,0,0
satan_s_cesspool|Dogleg and shelf lateral|wall|0,3,0
son_of_satan|Centre rock and right wall|wall|3,3,0
scissors|Diagonal ledges and bottom rock|slalom|0,3,-3
lower_haystack_canyon|Wave train with local rock/hole|train|0,0,0
bouncing_rock|Avoid broadside arrival at right rock|wall|0,4,0
pre_op|Keep between bank holes|hole|0,0,0
hospital_bar|Square diagonal; avoid Catcher's Mitt|wall|0,0,3
recovery_room|Entry hole and reservoir-dependent runout|hole|0,3,0
surprise|Funnel and pourover|hole|0,3,0
bed_and_breakfast|Short class II; boofable rock left of centre|slalom|0,-2,0
the_narrows|Rock-walled outcrop slalom to a rocky-island rest|slalom|0,0,0
mini_gorge|Bedrock narrows with seams and boils after a wave lead-in|continuous|0,0,0
swimmer_s_rapid_chili_bar_run|Easy class II above Indian Creek|train|0,0,0
gremlin_s|Wide left bend; features right of centre; surf wave at the end|train|0,-3,0
old_scary|Island split: left-channel ledge or technical right channel|slalom|3,3,0
blue_house_hole|River-left surf wave; go left of the island|surf|3,4,3
pink_fuzzy_bunny_with_a_fang|Island split: left tongue toward the Fang or right ledges|hole|3,3,0
barking_dog|Funnel into a steep breaking wave; eddy right|surf|0,0,-3
killer_fang_falls|Far-right pourover below Barking Dog|hole|0,2,0
dave_moore|Right-channel wave train or left-channel S-turn|train|-3,-3,0
current_divider|Island split with most flow right, then right-left-right|slalom|-3,3,-3
highway_rapid|Long shallow rocky left bend; exit right of the rock island|continuous|0,3,-3
swimmer_s_c_to_g|Benign wave train above Greenwood Creek|train|0,0,0
cable_car_rapid|Right bend around a bushy island; most flow right|slalom|0,-3,-3
airplane_turn|Three channels; the far left kicks back right|slalom|0,0,0
speed_bump|Surf wave above Fowler's Rock|surf|0,0,0
splat_rock|River-left splat rock above Fowler's Rock|wall|0,-2,0
son_of_fowler|Wave train growing holes at high water below Fowler's|train|0,0,0
salmon_falls|Low-reservoir wave trains, chutes and boofs|continuous|0,0,0''',
'colorado': '''hance_main|Right entry; early left ferry via Duck Pond|continuous|-14,9,5
son_of_hance|Hidden hole and unstable exit water|hole|0,-5,0
badger_creek|Choose the tongue beside the upper-right hydraulic, then square the following waves|hole|0,0,0''',
'pacuare': '''double_drop|Either side of the centre holes|hole|-7,-7,-7
upper_huacas|Low-water right of bottom rock; left alternative at higher water|slalom|0,-14,-14
lower_huacas|Right of drop then avoid left undercut; right sneak exists|wall|0,-8,-14
upper_pinball|Read boulders then turn sharply right|slalom|0,0,-8
lower_pinball|First rock right; second rock left|slalom|-7,-7,12
guatemala|Wave train and optional play hole|surf|0,0,0''',
'futaleufu': '''terminator_wave|Optional surf with eddy service|surf|0,0,0
terminator_entrance|Choose left entrance channel|slalom|4,12,16
terminator_core|Offset holes; crux; Typewriter; exit setup|continuous|16,24,6
son_of_terminator|Work left; prepare right for Khyber|continuous|6,4,-9
khyber_pass|Right-centre; middle; back right of main hole|hole|-10,-3,-10
himalayas|Square centre waves; both edge sneaks are legitimate|train|0,0,0''',
'chilko': '''bidwell|S-bend; punch right lateral; avoid bottom hazard|continuous|-4,-6,-3
white_kilometre|Continuous read-and-run; uncertain exact location|continuous|0,0,0
white_mile|Slab at the turn; sustained waves and holes|continuous|-4,-6,-4''',
'zambezi': '''rapid_1|Ferry away from wall cushion|wall|0,-8,-8
rapid_2|Wave line under bridge|train|0,0,0
rapid_3|Right of left hydraulic|hole|-6,-6,-6
rapid_4|Entry holes then wall diagonal|wall|0,-6,0
rapid_5|Right pourover and Catcher's Mitt|hole|-2,-2,0
rapid_6|Entry hydraulic then surging water|hole|-12,-12,0
rapid_7|Indicator; Director; Crease; Gap; Giants|continuous|-10,0,2
rapid_8|Choose Star Trek or easier Muncher/chicken route|hole|-12,-12,0
rapid_9|Commercial raft portage|portage|0,0,0
rapid_10|Tongue and waves|train|-4,-4,0
rapid_11|Choose either side of main hole; difficult eddy line|hole|24,24,20
rapid_12|Three-part waves; retentive 12B|continuous|0,0,0
rapid_13|Square successive large waves|train|0,0,0
rapid_14|Avoid central shallow hole|hole|18,18,18
rapid_15|Exit wave train before bottom hole|hole|0,-20,-20
rapid_16|Island choices; strong flow dependence|slalom|-12,-12,0
rapid_17|Exit before paired shallow holes|hole|0,-22,-22
rapid_18|Prepare for the third breaking wave|hole|0,0,0
rapid_19|Lower-gorge wave section; exact line evidence limited|unresolved|0,0,0
rapid_20|Lower-gorge wave section; exact line evidence limited|unresolved|0,0,0
rapid_21|Lower-gorge wave section; exact line evidence limited|unresolved|0,0,0
rapid_22|Lower-gorge wave section; exact line evidence limited|unresolved|0,0,0
rapid_23|Bend and cauldron; precise line unverified|unresolved|0,0,0
rapid_24|Flow-dependent play wave|surf|0,0,0
rapid_25|Final wave section; exact line evidence limited|unresolved|0,0,0''',
'futaleufu-continuous': '''school_house|Read-and-run class II-III just below the Rio Azul confluence|train|0,0,0
asleep_at_the_wheel|Avoid the centre-bottom hydraulic using the right passage|hole|0,-4,-4
terminator_wave|Optional surf with eddy service|surf|0,0,0
terminator_entrance|Choose the left entrance channel|slalom|4,12,16
terminator_core|Offset holes; crux; Typewriter; exit setup|continuous|16,24,6
son_of_terminator|Work left; prepare right for Khyber|continuous|6,4,-9
khyber_pass|Right-centre; middle; back right of the main hole|hole|-10,-3,-10
himalayas|Square centre waves; both edge sneaks are legitimate|train|0,0,0''',
'zambezi-upper': '''r1_the_wall|Ferry away from wall cushion|wall|0,-8,-8
r2_the_bridge|Wave line under bridge|train|0,0,0
r3|Right of left hydraulic|hole|-6,-6,-6
r3_5_pocket|Optional left pocket surf|surf|0,0,0
r4_morning_glory|Entry holes then wall diagonal|wall|0,-6,0
r4b|Linked holes below Morning Glory|hole|0,-3,0
stairway_approach|Stage before Stairway|train|0,0,0
r5_stairway_to_heaven|Right pourover and Catcher's Mitt|hole|-2,-2,0
r5_5|Wave section with eddy service|train|0,0,0
reach_end_rapid|Identity and demanding line unverified|unresolved|0,0,0''',
}


def definitions():
    result={}
    for river, lines in ROWS.items():
        for line in lines.splitlines():
            key, decision, family, laterals=line.split('|')
            result[river,key]=dict(decision=decision, family=family,
                successful_route_width=AXES[family][0], steering_timing=AXES[family][1],
                mistake_consequences=AXES[family][2], recoverability=AXES[family][3],
                lateral_hypotheses_m=list(map(float,laterals.split(','))), source=SOURCES[river])
    result['colorado','badger_creek']['source']='https://gorafting.com/united-states/arizona/grand-canyon/badger-creek-rapid/'
    result['colorado','badger_creek']['source_grade']='Grand Canyon 5; not International Class V'
    return result


def build(stage='screen'):
    definitions_by_id=definitions()
    missing_by_name=missing_definitions(AXES)
    base=json.loads((ROOT/'unreal/Tests/Data/rapid_assessment_reaches.json').read_text())
    references={(r['river'],t['rapid_id']):t for r in reference_plans() for t in r['trials']
                if t['variant'] in ('linked','line','early-entry-14')}
    contracts=[]; plans=[]
    for item in inventory():
        t=item['trial']
        contract={k:v for k,v in item.items() if k!='trial'}
        if t:
            contract.update(rapid_id=t['id'], **definitions_by_id[item['river'],t['id']])
            contract['status']='requires_native_comparison'
        else:
            contract.update(status='missing_playable_section', **missing_by_name[item['river'],item['name']])
        contract['catalog_class_match']='not_established'
        contracts.append(contract)
    for reach in base:
        catalog_river=reach.get('catalog_river',reach['river'])
        plan={k:copy.deepcopy(v) for k,v in reach.items() if k!='trials'}
        plan.update(seconds_per_trial=1800, capture_gate_frames=False,trials=[],
                    campaign_scope='Matched normal-input trials, not human skill grades or measured safe widths')
        for original in reach['trials']:
            d=definitions_by_id[catalog_river,original['id']]
            # Reuse tested line geometry where available but NOT its wider
            # continuous bounds under a different rapid's name.
            row=copy.deepcopy(original)
            if reach['river']=='chilko' and original['id']=='bidwell':
                # The old 1015 m finish cut through the bank-contact zone.
                # Include the complete measured exit control, not just crux.
                row['finish_m']=1080
            start,finish=row['start_m'],row['finish_m']; span=finish-start
            route=[[start,d['lateral_hypotheses_m'][0]],
                   [start+.45*span,d['lateral_hypotheses_m'][1]],
                   [finish-1,d['lateral_hypotheses_m'][2]]]
            ref=references.get((reach['river'],original['id']))
            if ref and ref['start_m']<=start and ref['finish_m']>=finish:
                route=copy.deepcopy(ref.get('route_laterals',route))
            if original['id']=='lower_pinball':
                route=copy.deepcopy(references['pacuare','lower_pinball']['route_laterals'])
            if reach['river']=='chilko' and original['id']=='bidwell':
                # Fresh full-production-hull matched control v2: zero contact
                # through 1080 m. Keep the original upstream interpolation;
                # the earlier revision changed it and hit the bank at 850 m.
                route=[[650,-4],[814.25,-6],
                       [930,-6+3*(930-814.25)/(1014-814.25)],[980,1],[1080,1]]
            gates=[dict(id='decision_'+str(i),station_m=start+f*span)
                   for i,f in enumerate((.25,.5,.75,.95))]
            row.update(rapid_id=original['id'],strict_route=True,route_laterals=route,
                       normal_rescue_inputs=False,gates=gates,wall_limit_s=2400,
                       input_interval_s=.85,lane_m=0,decision_contract=d,
                       mistake_trigger_m=DECISIONS.get((catalog_river,original['id']),original['control_m']-12),
                       route_authority='Inferred game route for testing; not measured or guide-approved',
                       width_scope='Offset-input sensitivity. Actual gate tracks are not proof of continuous hull clearance.')
            # An initial yaw alone can be corrected hundreds of metres before
            # the decision. Hold the poor approach with ORDINARY steering
            # inputs through its decision, then release it for recovery. The
            # native receipts record actual headings; this is not a pose edit.
            poor_approach=dict(initial_heading_deg=60.,heading_offset_deg=60.,
                heading_start_m=max(start,row['mistake_trigger_m']-30.),
                heading_end_m=min(finish-1.,row['mistake_trigger_m']+10.))
            variants=[('prepared',{}),('absent',dict(disable_steering=True)),
                      ('late',dict(mistake_seconds=6.)),
                      ('late-recovery',dict(mistake_seconds=6.,normal_rescue_inputs=True)),
                      ('poor-heading',poor_approach),
                      ('poor-heading-recovery',dict(**poor_approach,normal_rescue_inputs=True))]
            # Matched native controls: the 12 m driver stalled in the third
            # wave while a 45 m target and downstream-heading/absent controls
            # cleared. This is a declared input choice, not a water change.
            if reach['river']=='zambezi' and original['id']=='rapid_18':
                row['lookahead_m']=45.
            if reach['river']=='chilko' and original['id']=='bidwell':
                row['lookahead_m']=45.
            if stage=='width':
                variants=[('offset'+str(n),dict(lane_m=n)) for n in (-12,-8,-4,-2,0,2,4,8,12)]
            elif stage=='timing':
                variants=[('delay'+str(n),dict(mistake_seconds=n)) for n in (0,2,4,6,10)]
            if row.get('portage'): variants=[('portage',{})]
            for variant, options in variants:
                trial=copy.deepcopy(row)
                trial.update(id=original['id']+'--'+variant,variant=variant,**options)
                plan['trials'].append(trial)
        plans.append(plan)
    return contracts,plans


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--stage',choices=('screen','width','timing'),default='screen')
    args=parser.parse_args()
    if args.out.exists(): raise SystemExit('Fresh output directory required')
    contracts,plans=build(args.stage)
    args.out.mkdir(parents=True)
    (args.out/'contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
    (args.out/'plans.json').write_text(json.dumps(plans,indent=2)+'\n')
    print(f'{len(contracts)} entries, {sum(len(p["trials"]) for p in plans)} trials')
