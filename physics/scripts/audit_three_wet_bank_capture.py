"""Bind the reference envelope to an unchanged same-call engine contact capture."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from three_wet_bank_envelope import build

def audit(path,expected_sha256):
    source=Path(path).read_bytes()
    digest=hashlib.sha256(source).hexdigest()
    if digest!=expected_sha256:raise ValueError('Contact capture hash changed')
    report=json.loads(source)
    matches=[p for p in report['ground_contact_probes']
             if abs(p['x_cm']-(-542609.86703267507))<1.e-6
             and abs(p['y_cm']-(-360212.23455268872))<1.e-6]
    if len(matches)!=1:raise ValueError('Unique retained raw-dry probe required')
    probe=matches[0];cell=probe['source_cell']
    if len(cell)!=4 or probe['raw_wet'] or probe['raw_depth_m']!=0:
        raise ValueError('Original four-corner dry failure required')
    dry=[i for i,c in enumerate(cell) if not c['clipping_wet']]
    if len(dry)!=1:raise ValueError('Exactly one clipping-dry corner required')
    order=tuple(dry[0]^i for i in range(4))
    B=tuple(F(cell[i]['cached_bed_m']) for i in order)
    H=tuple(F(cell[i]['cached_depth_m']) for i in order)
    for axis in ('field_x_m','field_y_m'):
        if max(c[axis] for c in cell)-min(c[axis] for c in cell)!=1:
            raise ValueError('This retained receipt requires its original one-metre cell')
    proof=build(B,H)
    serialize=lambda x: str(x) if isinstance(x,F) else x
    return json.loads(json.dumps(dict(contact_sha256=digest,
        source_ids=[cell[i]['source_id'] for i in order],canonical_order=order,
        original_bed=B,original_depth=H,proof=proof,
        physical_band_bound_cm=.1,whole_wet_and_dry_triangles_certified=True,
        native_integrated=False,gameplay_delivered=False,river_accepted=False),default=serialize))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contact',required=True);p.add_argument('--sha256',required=True)
    args=p.parse_args();print(json.dumps(audit(args.contact,args.sha256),indent=2))
