# -*- coding: utf-8 -*-
import operator as op
from functools import partialmethod, reduce

from parsimonious import Grammar, NodeVisitor
from mtl import ast
from mtl import sugar

MTL_GRAMMAR = Grammar(u'''
phi = (neg / paren_phi / vyesterday / bot / top
     / xor_outer / iff_outer / implies_outer / and_outer / or_outer
     / weak_since / hist / once / AP)

paren_phi = "(" __ phi __ ")"
neg = ("~" / "¬") __ phi
vyesterday = "Z" __ phi

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

once = "P" interval? __ phi
hist = "H" interval? __ phi
weak_since = "(" __ phi _ "M" _ phi __ ")"
interval = "[" __ const_or_unbound __ "," __ const_or_unbound __ "]"

const_or_unbound = const / "inf" / id

AP = ~r"[a-z][a-z\d]*"

bot = "FALSE"
top = "TRUE"

id = ~r"[a-z\d]+"
const = ~r"[-+]?(\d*\.\d+|\d+)"
_ = ~r"\s"+
__ = ~r"\s"*
EOL = "\\n"
''')

oo = float('inf')


class MTLVisitor(NodeVisitor):
    def __init__(self, H=oo):
        super().__init__()

    def binop_inner(self, _, children):
        if not isinstance(children[0], list):
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
    visit_iff_outer = partialmethod(binop_outer, binop=sugar.iff)
    visit_implies_outer = partialmethod(binop_outer, binop=sugar.implies)
    visit_or_outer = partialmethod(binop_outer, binop=op.or_)
    visit_xor_outer = partialmethod(binop_outer, binop=sugar.xor)

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
        i = None if not i else i[0]
        return getattr(phi, op)(i)

    visit_hist = partialmethod(unary_temp_op_visitor, op='hist')
    visit_once = partialmethod(unary_temp_op_visitor, op='once')

    def visit_weak_since(self, _, children):
        _, _, phi1, _, _, _, phi2, _, _ = children
        return phi1.weak_since(phi2)

    def visit_id(self, name, _):
        return name.text

    def visit_AP(self, *args):
        return ast.AtomicPred(self.visit_id(*args))

    def visit_neg(self, _, children):
        return ~children[2]

    def visit_vyesterday(self, _, children):
        return children[2] << 1


def parse(mtl_str: str, rule: str = "phi", H=oo) -> "MTL":
    return MTLVisitor(H).visit(MTL_GRAMMAR[rule].parse(mtl_str))
