# -*- coding: utf-8 -*-

# TODO: consider using sympy to interpret stuff
# TODO: break out into seperate library
# TODO: allow matrix to be symbolically parsed in STL_GRAMMAR
# TODO: allow multiplication to be distributive
# TODO: support reference specific time points
# TODO: add Implies and Iff syntactic sugar
# TODO: add support for parsing Until
# TODO: support variables on both sides of ineq
# TODO: Allow -x = -1*x
# TODO: change way of parsing dt
# - Allow inside of time index
# - Allow dt*x rather than dt*1*x

from functools import partialmethod
from collections import namedtuple
import operator as op

from parsimonious import Grammar, NodeVisitor
from funcy import flatten
import numpy as np
from lenses import lens

from stl import stl

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
id = ("x" / "u" / "w") ~r"\d+" 
const = ~r"[\+\-]?\d*(\.\d+)?"
op = ">=" / "<=" / "<" / ">" / "="
_ = ~r"\s"+
__ = ~r"\s"*
EOL = "\\n"
''')

MATRIX_GRAMMAR = Grammar(r'''
matrix = "[" __ row+ __ "]"
row = consts ";"? __
consts = (const _ consts) / const

const = ~r"[\+\-]?\d+(\.\d+)?"
_ = ~r"\s"+
__ = ~r"\s"*
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
        return stl.Interval(left[0], right[0])

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

    visit_f = partialmethod(unary_temp_op_visitor, op=stl.F)
    visit_g = partialmethod(unary_temp_op_visitor, op=stl.G)
    visit_or = partialmethod(binop_visitor, op=stl.Or)
    visit_and = partialmethod(binop_visitor, op=stl.And)

    def visit_id(self, name, _):
        var_kind, *iden = name.text
        return stl.str_to_varkind[var_kind] ,int("".join(iden))

    def visit_var(self, _, children):
        (var_kind, iden), time_node = children

        time_node = list(flatten(time_node))
        time = time_node[0] if len(time_node) > 0 else stl.t_sym
            
        return stl.Var(var_kind, iden, time)

    def visit_time_index(self, _, children):
        return children[3]* children[5]

    def visit_prime(self, *_):
        return -stl.dt_sym

    def visit_const(self, const, children):
        return float(const.text)

    def visit_dt(self, *_):
        return stl.dt_sym

    def visit_term(self, _, children):
        coeffs, var = children
        c = coeffs[0] if coeffs else 1
        return stl.Term(c, var)

    def visit_coeff(self, _, children):
        dt, coeff, *_ = children
        dt = dt[0][0] if dt else 1
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
        return stl.LinEq(tuple(terms), op, const[0])

    def visit_pm(self, node, _):
        return 1 if node.text == "+" else -1


class MatrixVisitor(NodeVisitor):
    def generic_visit(self, _, children):
        return children

    def visit_matrix(self, _, children):
        _, _, rows, _, _ = children
        return rows

    def visit_row(self, _, children):
        consts, _, _ = children
        return consts

    def visit_const(self, node, _):
        return float(node.text)

    def visit_consts(self, _, children):
        return list(flatten(children))


def parse_stl(stl_str:str, rule:str="phi") -> "STL":
    return STLVisitor().visit(STL_GRAMMAR[rule].parse(stl_str))


def parse_matrix(mat_str:str) -> np.array:
    return np.array(MatrixVisitor().visit(MATRIX_GRAMMAR.parse(mat_str)))
