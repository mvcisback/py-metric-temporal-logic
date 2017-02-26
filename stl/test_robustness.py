import stl
import stl.boolean_eval
import stl.robustness
import stl.smooth_robustness
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
    def test_robustness_sign(self, phi_str, _):
        phi = stl.parse(phi_str)
        stl_eval = stl.boolean_eval.pointwise_sat(phi)
        stl_eval2 = stl.robustness.pointwise_robustness(phi)
        r = stl_eval2(x, 0)
        assert (r == 0 or ((r > 0) == stl_eval(x, 0)))


    @params(ex1, ex2, ex3, ex4, ex5, ex6)
    def test_robustness_value(self, phi_str, r):
        phi = stl.parse(phi_str)
        stl_eval = stl.robustness.pointwise_robustness(phi)
        self.assertEqual(stl_eval(x, 0), r)


    @params(ex1, ex2, ex3, ex4, ex5, ex6)
    def test_eps_robustness(self, phi_str, r):
        phi = stl.parse(phi_str)
        r = stl.robustness.pointwise_robustness(phi)(x, 0)
        lo, hi = stl.smooth_robustness.smooth_robustness(phi, L=1, eps=0.1)
        # hi - lo <= eps
        # lo <= r <= hi
        #raise NotImplementedError


    @params(ex1, ex2, ex3, ex4, ex5, ex6)
    def test_interval_polarity(self, phi_str, r):
        phi = stl.parse(phi_str)
        lo, hi = stl.smooth_robustness.smooth_robustness(phi, L=1, eps=0.1)
        # hi - lo > 0
        #raise NotImplementedError
