import numpy as np
import pytest
from audit_cap_boundary_lower_bins import lower_bin_witnesses


def test_negative_bins_and_stable_source_ties():
    rows=lower_bin_witnesses(np.array([[-.1,0,3]]),np.array([[-.2,0,1],[-.2,0,1],[.1,0,0]]),np.array([1,2,2]),np.array([.1,.2,0.]))
    assert len(rows)==1 and rows[0]['source_index']==0
    assert rows[0]['excluded_by_clearance']


def test_vegetation_and_missing_residual_not_promoted():
    rows=lower_bin_witnesses(np.array([[0,0,3]]),np.array([[0,0,0],[0,0,1]]),np.array([5,2]),np.array([0,np.nan]))
    assert rows==[]


def test_invalid_bin_rejected():
    with pytest.raises(ValueError):
        lower_bin_witnesses(np.zeros((1,3)),np.zeros((1,3)),np.array([2]),np.array([0]),0)
