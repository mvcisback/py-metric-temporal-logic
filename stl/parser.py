# -*- coding: utf-8 -*-

# TODO: allow multiplication to be distributive
# TODO: support variables on both sides of ineq
# TODO: Allow -x = -1*x

from functools import partialmethod

from lenses import lens
from parsimonious import Grammar, NodeVisitor
from stl import ast
from stl.utils import alw, env, iff, implies, xor

STL_GRAMMAR = Grammar(u'''
phi = (timed_until / until / neg / next / g / f / lineq / AP / or / and
     / implies / xor / iff / paren_phi)

paren_phi = "(" __ phi __ ")"

or = paren_phi _ ("∨" / "or" / "|") _ (or / paren_phi)
and = paren_phi _ ("∧" / "and" / "&") _ (and / paren_phi)
implies = paren_phi _ ("→" / "->") _ (and / paren_phi)
iff = paren_phi _ ("⇔" / "<->" / "iff") _ (and / paren_phi)
xor = paren_phi _ ("⊕" / "^" / "xor") _ (and / paren_phi)

neg = ("~" / "¬") paren_phi
next = "X" paren_phi
f = F interval? phi
g = G interval? phi
until = paren_phi __ U __ paren_phi
timed_until = paren_phi __ U interval __ paren_phi

F = "F" / "◇"
G = "G" / "□"
U = "U"

interval = "[" __ const_or_unbound __ "," __ const_or_unbound __ "]"

const_or_unbound = unbound / "inf" / const

lineq = terms _ op _ const_or_unbound
term =  const? var
terms = (term __ pm __ terms) / term

var = id
AP = ~r"[a-zA-z\d]+"

pm = "+" / "-"
dt = "dt"
unbound = id "?"
id = ~r"[a-zA-z\d]+"
const = ~r"[-+]?\d*\.\d+|\d+"
op = ">=" / "<=" / "<" / ">" / "="
_ = ~r"\s"+
__ = ~r"\s"*
EOL = "\\n"
''')

oo = float('inf')


class STLVisitor(NodeVisitor):
    def __init__(self, H=oo):
        super().__init__()
        self.default_interval = ast.Interval(0.0, H)

    def generic_visit(self, _, children):
        return children

    def children_getter(self, _, children, i):
        return children[i]

    visit_phi = partialmethod(children_getter, i=0)
    visit_paren_phi = partialmethod(children_getter, i=2)

    def visit_interval(self, _, children):
        _, _, (left, ), _, _, _, (right, ), _, _ = children
        left = left if left != [] else float("inf")
        right = right if right != [] else float("inf")
        if isinstance(left, int):
            left = float(left)
        if isinstance(right, int):
            left = float(right)
        return ast.Interval(left, right)

    def get_text(self, node, _):
        return node.text

    def visit_unbound(self, node, _):
        return ast.Param(node.text)

    visit_op = get_text

    def unary_temp_op_visitor(self, _, children, op):
        _, i, phi = children
        i = self.default_interval if not i else i[0]
        return op(i, phi)

    def binop_visitor(self, _, children, op):
        phi1, _, _, _, (phi2, ) = children
        argL = list(phi1.args) if isinstance(phi1, op) else [phi1]
        argR = list(phi2.args) if isinstance(phi2, op) else [phi2]
        return op(tuple(argL + argR))

    def sugar_binop_visitor(self, _, children, op):
        phi1, _, _, _, (phi2, ) = children
        return op(phi1, phi2)

    visit_f = partialmethod(unary_temp_op_visitor, op=ast.F)
    visit_g = partialmethod(unary_temp_op_visitor, op=ast.G)
    visit_or = partialmethod(binop_visitor, op=ast.Or)
    visit_and = partialmethod(binop_visitor, op=ast.And)
    visit_xor = partialmethod(sugar_binop_visitor, op=xor)
    visit_iff = partialmethod(sugar_binop_visitor, op=iff)
    visit_implies = partialmethod(sugar_binop_visitor, op=implies)

    def visit_until(self, _, children):
        phi1, _, _, _, phi2 = children
        return ast.Until(phi1, phi2)

    def visit_timed_until(self, _, children):
        phi, _, _, (lo, hi), _, psi = children
        return env(psi, lo=lo, hi=hi) & alw(ast.Until(phi, psi), lo=0, hi=lo)

    def visit_id(self, name, _):
        return name.text

    def visit_const(self, const, children):
        return float(const.text)

    def visit_term(self, _, children):
        coeffs, iden = children
        c = coeffs[0] if coeffs else 1
        return ast.Var(coeff=c, id=iden)

    def visit_terms(self, _, children):
        if isinstance(children[0], list):
            term, _1, sgn, _2, terms = children[0]
            terms = lens(terms)[0].coeff * sgn
            return [term] + terms
        else:
            return children

    def visit_lineq(self, _, children):
        terms, _1, op, _2, const = children
        return ast.LinEq(tuple(terms), op, const[0])

    def visit_pm(self, node, _):
        return 1 if node.text == "+" else -1

    def visit_AP(self, *args):
        return ast.AtomicPred(self.visit_id(*args))

    def visit_neg(self, _, children):
        return ast.Neg(children[1])

    def visit_next(self, _, children):
        return ast.Next(children[1])


def parse(stl_str: str, rule: str = "phi", H=oo) -> "STL":
    return STLVisitor(H).visit(STL_GRAMMAR[rule].parse(stl_str))
