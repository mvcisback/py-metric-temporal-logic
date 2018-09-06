# -*- coding: utf-8 -*-

# TODO: allow multiplication to be distributive
# TODO: support variables on both sides of ineq
import operator as op
from functools import partialmethod, reduce

from lenses import bind
from parsimonious import Grammar, NodeVisitor
from stl import ast
from stl.utils import iff, implies, xor, timed_until

STL_GRAMMAR = Grammar(u'''
phi = (neg / paren_phi / next / bot / top
     / xor_outer / iff_outer / implies_outer / and_outer / or_outer 
     / timed_until / until / g / f / AP)

paren_phi = "(" __ phi __ ")"
neg = ("~" / "¬") __ phi
next = ("@" / "X") __ phi

and_outer = "(" __ and_inner __ ")"
and_inner = (phi __ ("∧" / "and" / "&") __ and_inner) / phi

or_outer = "(" __ or_inner __ ")"
or_inner = (phi __ ("∨" / "or" / "|") __ or_inner) / phi

implies_outer = "(" __ implies_inner __ ")"
implies_inner = (phi __ ("→" / "->") __ implies_inner) / phi

iff_outer = "(" __ iff_inner __ ")"
iff_inner = (phi __ ("⇔" / "<->" / "iff") __ iff_inner) / phi

xor_outer = "(" __ xor_inner __ ")"
xor_inner = (phi __ ("⊕" / "^" / "xor") __ xor_inner) / phi

f = ("< >" / "F") interval? __ phi
g = ("[ ]" / "G") interval? __ phi
until = "(" __ phi _ "U" _ phi __ ")"
timed_until = "(" __ phi _ "U" interval _ phi __ ")"
interval = "[" __ const_or_unbound __ "," __ const_or_unbound __ "]"

const_or_unbound = const / "inf" / id

AP = ~r"[a-z\d]+"

bot = "0"
top = "1"

id = ~r"[a-z\d]+"
const = ~r"[-+]?(\d*\.\d+|\d+)"
_ = ~r"\s"+
__ = ~r"\s"*
EOL = "\\n"
''')

oo = float('inf')


class STLVisitor(NodeVisitor):
    def __init__(self, H=oo):
        super().__init__()
        self.default_interval = ast.Interval(0.0, H)

    def binop_inner(self, _, children):
        if isinstance(children[0], ast.AST):
            return children

        ((left, _, _, _, right),) = children
        return [left] + right

    def binop_outer(self, _, children, *, binop):
        return reduce(binop, children[2])

    def visit_const_or_unbound(self, node, children):
        child = children[0]
        return ast.Param(child) if isinstance(child, str) else float(node.text)

    visit_and_inner = binop_inner
    visit_iff_inner = binop_inner
    visit_implies_inner = binop_inner
    visit_or_inner = binop_inner
    visit_xor_inner = binop_inner

    visit_and_outer = partialmethod(binop_outer, binop=op.and_)
    visit_iff_outer = partialmethod(binop_outer, binop=iff)
    visit_implies_outer = partialmethod(binop_outer, binop=implies)
    visit_or_outer = partialmethod(binop_outer, binop=op.or_)
    visit_xor_outer = partialmethod(binop_outer, binop=xor)

    def generic_visit(self, _, children):
        return children

    def children_getter(self, _, children, i):
        return children[i]

    visit_phi = partialmethod(children_getter, i=0)
    visit_paren_phi = partialmethod(children_getter, i=2)

    def visit_bot(self, *_):
        return ast.BOT

    def visit_top(self, *_):
        return ast.TOP

    def visit_interval(self, _, children):
        _, _, left, _, _, _, right, _, _ = children
        return ast.Interval(left, right)

    def get_text(self, node, _):
        return node.text

    visit_op = get_text

    def unary_temp_op_visitor(self, _, children, op):
        _, i, _, phi = children
        i = self.default_interval if not i else i[0]
        return op(i, phi)

    visit_f = partialmethod(unary_temp_op_visitor, op=ast.F)
    visit_g = partialmethod(unary_temp_op_visitor, op=ast.G)

    def visit_until(self, _, children):
        _, _, phi1, _, _, _, phi2, _, _ = children
        return ast.Until(phi1, phi2)

    def visit_timed_until(self, _, children):
        _, _, phi1, _, _, itvl, _, phi2, _, _ = children
        return timed_until(phi1, phi2, itvl.lower, itvl.upper)

    def visit_id(self, name, _):
        return name.text

    def visit_AP(self, *args):
        return ast.AtomicPred(self.visit_id(*args))

    def visit_neg(self, _, children):
        return ~children[2]

    def visit_next(self, _, children):
        return ast.Next(children[2])


def parse(stl_str: str, rule: str = "phi", H=oo) -> "STL":
    return STLVisitor(H).visit(STL_GRAMMAR[rule].parse(stl_str))
