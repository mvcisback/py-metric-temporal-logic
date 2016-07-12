# -*- coding: utf-8 -*-

# TODO: break out into seperate library
# TODO: allow multiplication to be distributive
# TODO: support reference specific time points
# TODO: add Implies and Iff syntactic sugar
# TODO: add support for parsing Until
# TODO: support variables on both sides of ineq
# TODO: Allow -x = -1*x

from functools import partialmethod
from collections import namedtuple
import operator as op

from parsimonious import Grammar, NodeVisitor
from funcy import flatten
import numpy as np
from lenses import lens

from sympy import Symbol, Number

from stl import ast

STL_GRAMMAR = Grammar(u'''
phi = (g / f / lineq / or / and / paren_phi)

paren_phi = "(" __ phi __ ")"

or = paren_phi _ ("∨" / "or") _ (or / paren_phi)
and = paren_phi _ ("∧" / "and") _ (and / paren_phi)

f = F interval phi
g = G interval phi

F = "F" / "◇"
G = "G" / "□"
interval = "[" __ const_or_unbound __ "," __ const_or_unbound __ "]"

const_or_unbound = unbound / const

lineq = terms _ op _ const_or_unbound
term =  coeff? var
coeff = (dt __ "*" __)? const __ "*" __
terms = (term __ pm __ terms) / term

var = id time?
time = prime / time_index
time_index = "[" "t" __ pm __ const "]"
prime = "'"

pm = "+" / "-"
dt = "dt"
unbound = "?"
id = ("x" / "u" / "w") ~r"[a-zA-z\d]*" 
const = ~r"[\+\-]?\d*(\.\d+)?"
op = ">=" / "<=" / "<" / ">" / "="
_ = ~r"\s"+
__ = ~r"\s"*
EOL = "\\n"
''')


class STLVisitor(NodeVisitor):
    def generic_visit(self, _, children):
        return children

    def children_getter(self, _, children, i):
        return children[i]

    visit_phi = partialmethod(children_getter, i=0)
    visit_paren_phi = partialmethod(children_getter, i=2)

    def visit_interval(self, _, children):
        _, _, left, _, _, _, right, _, _ = children
        return ast.Interval(left[0], right[0])

    def get_text(self, node, _):
        return node.text

    visit_unbound = get_text
    visit_op = get_text

    def unary_temp_op_visitor(self, _, children, op):
        _, interval, phi = children
        return op(interval, phi)

    def binop_visitor(self, _, children, op):
        phi1, _, _, _, (phi2,) = children
        argL = list(phi1.args) if isinstance(phi1, op) else [phi1]
        argR = list(phi2.args) if isinstance(phi2, op) else [phi2]
        return op(tuple(argL + argR))

    visit_f = partialmethod(unary_temp_op_visitor, op=ast.F)
    visit_g = partialmethod(unary_temp_op_visitor, op=ast.G)
    visit_or = partialmethod(binop_visitor, op=ast.Or)
    visit_and = partialmethod(binop_visitor, op=ast.And)

    def visit_id(self, name, _):
        return Symbol(name.text)

    def visit_var(self, _, children):
        iden, time_node = children

        time_node = list(flatten(time_node))
        time = time_node[0] if len(time_node) > 0 else ast.t_sym
            
        return iden, time

    def visit_time_index(self, _, children):
        return children[3]* children[5]

    def visit_prime(self, *_):
        return ast.t_sym - ast.dt_sym

    def visit_const(self, const, children):
        return float(const.text)

    def visit_dt(self, *_):
        return ast.dt_sym

    def visit_term(self, _, children):
        coeffs, (iden, time) = children
        c = coeffs[0] if coeffs else Number(1)
        return ast.Var(coeff=c, id=iden, time=time)
    

    def visit_coeff(self, _, children):
        dt, coeff, *_ = children
        dt = dt[0][0] if dt else Number(1)
        return dt * coeff

    def visit_terms(self, _, children):
        if isinstance(children[0], list):
            term, _1, sgn ,_2, terms = children[0]
            terms = lens(terms)[0].coeff * sgn
            return [term] + terms
        else:
            return children

    def visit_lineq(self, _, children):
        terms, _1, op, _2, const = children
        return ast.LinEq(tuple(terms), op, const[0])

    def visit_pm(self, node, _):
        return Number(1) if node.text == "+" else Number(-1)


def parse(stl_str:str, rule:str="phi") -> "STL":
    return STLVisitor().visit(STL_GRAMMAR[rule].parse(stl_str))
