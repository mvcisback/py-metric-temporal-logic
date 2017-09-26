import stl
import stl.utils
import pandas as pd
import unittest
from sympy import Symbol

ex1 = ("F[b?, 1]G[0, c?](x > a?)", {"a?", "b?", "c?"})
ex2 = ("G[0, c?](x > a?)", {"a?", "c?"})
ex3 = ("F[b?, 1]G[0, c?](x > a?)", {"a?", "b?", "c?"})
ex4 = ("F[b?, 1]G[0, c?](x > a?)", "F[2, 1]G[0, 3](x > 1)")
ex5 = ("G[0, c?](x > a?)", "G[0, 3](x > 1)")

val = {"a?": 1.0, "b?": 2.0, "c?": 3.0}
"""
class TestSTLUtils(unittest.TestCase):
    @params(ex1, ex2, ex3)
    def test_param_lens(self, phi_str, params):
        phi = stl.parse(phi_str)
        self.assertEqual(set(map(str, stl.utils.param_lens(phi).get_all())), params)
        
    @params(ex4, ex5)
    def test_set_params(self, phi_str, phi2_str):
        phi = stl.parse(phi_str)
        phi2 = stl.parse(phi2_str)
        phi = stl.utils.set_params(phi, val)
        
        self.assertEqual(set(map(str, stl.utils.param_lens(phi).get_all())), set())
        self.assertEqual(phi, phi2)

    @params(("x > 5", 1), ("~(x)", 2), ("(F[0,1](x)) & (~(G[0, 2](y)))", 6))
    def test_walk(self, phi_str, l):
        self.assertEqual(l, len(list(stl.walk(stl.parse(phi_str)))))

    @params(([], False, False),([int], True, False), ([int, bool], True, True))
    def test_type_pred(self, types, b1, b2):
        pred = stl.utils.type_pred(*types)
        self.assertFalse(pred(None))
        self.assertEqual(pred(1), b1)
        self.assertEqual(pred(True), b2)

    @params(("(F[0,1]G[0, 4]((x > 3) or (y < 4))) and (x < 3)", 2))
    def test_vars_in_phi(self, phi_str, l):
        phi = stl.parse(phi_str)
        self.assertEqual(len(stl.utils.vars_in_phi(phi)), l)

    @params(("(F[0,1]G[0, 4]((x > 3) or (y < 4))) and (x < 3)", 3))
    def test_terms_lens(self, phi_str, l):
        phi = stl.parse(phi_str)
        l2 = len(stl.terms_lens(phi).get_all())
        self.assertEqual(l, l2)


    @params(("(F[0,1]G[0, 4]((x > 3) | (y < 4))) & (x < 3)", 7, 12))
    def test_f_neg_or_canonical_form(self, phi_str, pre_l, post_l):
        phi = stl.parse(phi_str)
        pre_l2 = len(list(stl.walk(phi)))
        self.assertEqual(pre_l, pre_l2)
        post_l2 = len(list(stl.walk(stl.utils.f_neg_or_canonical_form(phi))))
        self.assertEqual(post_l, post_l2)

    def test_andf(self):
        phi = stl.parse("x")
        self.assertEqual(phi, stl.andf(phi))

    def test_orf(self):
        phi = stl.parse("x")
        self.assertEqual(phi, stl.orf(phi))

    def test_inline_context(self):
        context = {
            stl.parse("x"): stl.parse("(z) & (y)"),
            stl.parse("z"): stl.parse("y - x > 4")
        }
        context2 = {
            stl.parse("x"): stl.parse("x"),
        }
        phi = stl.parse("x")
        self.assertEqual(stl.utils.inline_context(phi, {}), phi)
        self.assertEqual(stl.utils.inline_context(phi, context), 
                         stl.parse("(y - x > 4) & (y)"))

        phi2 = stl.parse("((x) & (z)) | (y)")
        self.assertEqual(stl.utils.inline_context(phi2, context), 
                         stl.parse("((y - x > 4) & (y) & (y - x > 4)) | (y)"))

#    def test_to_from_mtl(self):
#        raise NotImplementedError

#    def test_get_polarity(self):
#        raise NotImplementedError

#    def test_canonical_polarity(self):
#        raise NotImplementedError
"""
