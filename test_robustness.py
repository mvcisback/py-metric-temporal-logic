import stl
import stl.robustness
import pandas as pd
from nose2.tools import params
import unittest
from sympy import Symbol

oo = float('inf')

ex1 = ("2*A > 3", -1)
ex2 = ("F[0, 1](2*A > 3)", 5)
ex3 = ("F[1, 0](2*A > 3)", -oo)
ex4 = ("G[1, 0](2*A > 3)", oo)
ex5 = ("(A < 0)", -1)
ex6 = ("G[0, 0.1](A < 0)", -1)
x = pd.DataFrame([[1,2], [1,4], [4,2]], index=[0,0.1,0.2], 
                 columns=["A", "B"])


class TestSTLRobustness(unittest.TestCase):
    @params(ex1, ex2, ex3, ex4, ex5, ex6)
    def test_stl(self, phi_str, r):
        phi = stl.parse(phi_str)
        stl_eval = stl.robustness.pointwise_robustness(phi)
        self.assertEqual(stl_eval(x, 0), r)
