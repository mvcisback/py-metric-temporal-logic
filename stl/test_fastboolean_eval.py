import stl
import stl.fastboolean_eval
import pandas as pd
from nose2.tools import params
import unittest
from sympy import Symbol

ex1 = ("2*A > 3", False)
ex2 = ("F[0, 1](2*A > 3)", True)
ex3 = ("F[1, 0](2*A > 3)", False)
ex4 = ("G[1, 0](2*A > 3)", True)
ex5 = ("(A < 0)", False)
ex6 = ("G[0, 0.1](A < 0)", False)
ex7 = ("G[0, 0.1](C)", True)
ex8 = ("G[0, 0.2](C)", False)
ex9 = ("(F[0, 0.2](C)) and (F[0, 1](2*A > 3))", True)
x = pd.DataFrame([[1,2, True], [1,4, True], [4,2, False]], index=[0,0.1,0.2], 
                 columns=["A", "B", "C"])

class TestSTLRobustness(unittest.TestCase):
    @params(ex1, ex2, ex3, ex4, ex5, ex6, ex7, ex8, ex9)
    def test_stl(self, phi_str, r):
        phi = stl.parse(phi_str)
        stl_eval = stl.fastboolean_eval.pointwise_satf(phi)
        self.assertEqual(stl_eval(x, [0]), r)
