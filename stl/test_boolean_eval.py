import stl
import stl.boolean_eval
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

class TestSTLEval(unittest.TestCase):
    @params(ex1, ex2, ex3, ex4, ex5, ex6, ex7, ex8, ex9)
    def test_eval(self, phi_str, r):
        phi = stl.parse(phi_str)
        stl_eval = stl.boolean_eval.pointwise_sat(phi)
        stl_eval2 = stl.boolean_eval.pointwise_sat(~phi)
        self.assertEqual(stl_eval(x, 0), r)
        self.assertEqual(stl_eval2(x, 0), not r)



    @params(ex1, ex2, ex3, ex4, ex5, ex6, ex7, ex8, ex9)
    def test_fasteval(self, phi_str, _):
        phi = stl.parse(phi_str)
        stl_eval = stl.boolean_eval.pointwise_sat(phi)
        stl_evalf = stl.fastboolean_eval.pointwise_sat(phi)
        stl_evalf2 = stl.fastboolean_eval.pointwise_sat(~phi)

        b_slow = stl_eval(x, 0)
        b_fast = stl_evalf(x, 0)
        b_fast2 = stl_evalf2(x, 0)
        self.assertEqual(b_slow, b_fast)
        self.assertEqual(b_fast, not b_fast2)
