import stl
import stl.synth
import traces
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
ex6 = ("(A > a?) or (A > b?)", ("a?", "b?",), {"a?": (0, 2), "b?": (0, 2)},
       {"a?": False, "b?": False}, {"a?": 2, "b?": 1})

x = {
    "A": traces.TimeSeries([(0, 1), (0.1, 1), (0.2, 4)]),
    "B": traces.TimeSeries([(0, 2), (0.1, 4), (0.2, 2)]),
    "C": traces.TimeSeries([(0, True), (0.1, True), (0.2, False)]),
}


class TestSTLRobustness(unittest.TestCase):
    @params(ex1, ex2, ex3, ex4, ex5, ex6)
    def test_lex_synth(self, phi_str, order, ranges, polarity, val):
        phi = stl.parse(phi_str)
        val2 = stl.synth.lex_param_project(
            phi, x, order=order, ranges=ranges, polarity=polarity)

        # check that the valuations are almost the same
        for var in order:
            self.assertAlmostEqual(val2[var], val[var], delta=0.01)
