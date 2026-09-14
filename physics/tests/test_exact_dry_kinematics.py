from fractions import Fraction as F
import numpy as np
from audit_exact_dry_kinematics import limited, ratio_limit, oracle, run


def test_ordered_mc_ties_use_actual_right_direction():
    assert limited((F(0),F(1)),(F(0),F(2)))==(F(0),F(3,2))
    assert limited((F(0),F(-1)),(F(0),F(-2)))==(F(0),F(-3,2))
    assert limited((F(0),F(-1)),(F(0),F(2)))==(F(0),F(0))
    assert ratio_limit((F(0),F(1)),(F(0),F(4)))==F(1,4)


def test_flat_positive_interior_affine_divergence_and_no_mutation():
    y,x=np.indices((7,8),dtype=float)
    h=np.ones_like(x);bed=np.zeros_like(x);ht=np.zeros_like(x)
    u=np.stack((2*x,-3*y),axis=-1)
    copies=[a.copy() for a in (h,bed,ht,u)]
    d,_=oracle(h,bed,ht,u)
    np.testing.assert_array_equal(d[1:-1,1:-1],-np.ones_like(d[1:-1,1:-1]))
    for a,b in zip((h,bed,ht,u),copies):np.testing.assert_array_equal(a,b)


def test_exact_oracle_reproduces_not_waives_original_dry_defect():
    report=run()
    assert max(c['maximum_oracle_discrepancy'] for c in report['cases'])<3e-14
    assert report['cases'][0]['oracle_D_at_target']==1.25
    original_probe=next(c for c in report['cases'] if c['epsilon_power']==24)
    assert original_probe['oracle_D_at_target']==3.75
    assert original_probe['target_D_squared_error']==12.5
    assert report['original_probe_gate_replaced'] is False
    assert report['native_or_full_history_accepted'] is False
