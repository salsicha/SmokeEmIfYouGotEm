import numpy as np
import pytest
from extract_troublemaker_pulse_fields import last_return_mask


def test_last_return_is_not_a_ground_classification():
    np.testing.assert_array_equal(last_return_mask(np.array([1,1,2,3]),np.array([1,2,2,3])),[True,False,True,True])


@pytest.mark.parametrize('a,b', [([0],[1]),([2],[1]),([1],[16]),([1.,2.],[1.,2.]),([[1]],[[1]]),([1],[1,2])])
def test_invalid_original_pulses_rejected(a,b):
    with pytest.raises(ValueError): last_return_mask(np.array(a),np.array(b))
