# -*- coding: utf-8 -*-
import stl
from nose2.tools import params
import unittest
from sympy import Symbol

ex1 = ('x1 > 2', stl.LinEq(
    (stl.Var(1, Symbol("x1"), stl.t_sym),),
    ">",
    2.0
))
ex1_ = ('x1 > a?', stl.LinEq(
    (stl.Var(1, Symbol("x1"), stl.t_sym),),
    ">",
    Symbol("a?")
))

ex1__ = ('x1', stl.AtomicPred(Symbol('x1'), stl.t_sym))

i1 = stl.Interval(0., 1.)
i1_ = stl.Interval(0., Symbol("b?"))
i2 = stl.Interval(2., 3.)
ex2 = ('◇[0,1](x1 > 2)', stl.F(i1, ex1[1]))
ex3 = ('□[2,3]◇[0,1](x1 > 2)', stl.G(i2, ex2[1]))
ex4 = ('(x1 > 2) or ((x1 > 2) or (x1 > 2))', 
       stl.Or((ex1[1], ex1[1], ex1[1])))
ex5 = ('G[0, b?](x1 > a?)',
       stl.G(i1_, ex1_[1]))
ex6 = ('◇[0,1](x1)', stl.F(i1, ex1__[1]))
ex7 = ('F[0, inf](x)', stl.parse("F(x)"))

'''
class TestSTLParser(unittest.TestCase):
    @params(ex1, ex2, ex3, ex4, ex5, ex6, ex7)
    def test_stl(self, phi_str, phi):
        self.assertEqual(stl.parse(phi_str), phi)

    def test_smoke_test(self):
        """Previously broken parses"""
        stl.parse("◇[0,inf]((1*Lane_ID(t) = 1.0) ∧ (◇[0.0,eps?]((◇[eps?,tau1?](¬(1*Lane_ID(t) = 1.0))) ∧ (□[0,tau1?]((1*Lane_ID(t) = 1.0) U (¬(1*Lane_ID(t) = 1.0)))))))")
'''
