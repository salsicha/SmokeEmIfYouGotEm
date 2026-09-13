import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_pressure_relaxation import parent_omega


class PressureRelaxationTest(unittest.TestCase):
    def test_estimate_matches_eigenvalues_of_actual_wide_stencil_box(self):
        cells=(8,6,4);h=np.array((50.,50.,800/24));n=np.prod(cells)
        # Independently assemble the zero-Dirichlet wide-stencil Jacobi matrix.
        matrix=np.zeros((n,n));weight=1/(4*h*h);diagonal=2*weight.sum()
        for z in range(cells[2]):
            for y in range(cells[1]):
                for x in range(cells[0]):
                    i=x+cells[0]*(y+cells[1]*z)
                    for axis in range(3):
                        for sign in (-1,1):
                            q=[x,y,z];q[axis]+=2*sign
                            if all(0<=q[a]<cells[a] for a in range(3)):
                                j=q[0]+cells[0]*(q[1]+cells[1]*q[2])
                                matrix[i,j]=weight[axis]/diagonal
        rho=float(np.max(np.abs(np.linalg.eigvalsh(matrix))))
        self.assertAlmostEqual(parent_omega(cells,h),2/(1+np.sqrt(1-rho*rho)),places=12)

    def test_metric_units_do_not_change_relaxation(self):
        cells=(494,166,24)
        self.assertAlmostEqual(parent_omega(cells,(50,50,800/24)),parent_omega(cells,(.5,.5,8/24)))

    def test_invalid_layout_rejected(self):
        for cells,spacing in (((1,4,4),(1,1,1)),((4.5,4,4),(1,1,1)),((4,4,4),(0,1,1)),((4,4,4),(np.nan,1,1))):
            with self.assertRaises(ValueError):parent_omega(cells,spacing)


if __name__=='__main__':unittest.main()
