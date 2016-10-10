import stl
import stl.robustness
import stl.synth
import pandas as pd
from nose2.tools import params
import unittest
from sympy import Symbol

oo = float('inf')

ex1 = ("A > a?", ("a?",), {"a?": (0, 10)}, {"a?": False}, {"a?": 1})
ex2 = ("F[0, b?](A > a?)", ("a?", "b?"), {"a?": (0, 10), "b?": (0, 5)},
       {"a?": False, "b?": True}, {"a?": 4, "b?": 0.2})
ex3 = ("F[0, b?](A < 0)", ("b?",), {"b?": (0, 5)},
       {"b?": True}, {"b?": 5})
ex4 = ("G[0, b?](A < 0)", ("b?",), {"b?": (0.1, 5)},
       {"b?": False}, {"b?": 0.1})
ex5 = ("F[0, b?](A > 0)", ("b?",), {"b?": (0.1, 5)},
       {"b?": True}, {"b?": 0.1})

x = pd.DataFrame([[1,2], [1,4], [4,2]], index=[0,0.1,0.2], 
                 columns=["A", "B"])


class TestSTLRobustness(unittest.TestCase):
    @params(ex1, ex2, ex3, ex4, ex5)
    def test_lex_synth(self, phi_str, order, ranges, polarity, val):
        phi = stl.parse(phi_str)
        val2 = stl.synth.lex_param_project(
            phi, x, order=order, ranges=ranges, polarity=polarity)

        phi2 = stl.utils.set_params(phi, val2)
        phi3 = stl.utils.set_params(phi, val)

        stl_eval = stl.robustness.pointwise_robustness(phi2)
        stl_eval2 = stl.robustness.pointwise_robustness(phi3)

        # check that the robustnesses are almost the same
        self.assertAlmostEqual(stl_eval(x, 0), stl_eval2(x, 0), delta=0.01)

        # check that the valuations are almost the same
        for var in order:
            self.assertAlmostEqual(val2[var], val[var], delta=0.01)
