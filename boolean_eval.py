# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

from functools import singledispatch
import operator as op

from lenses import lens

import stl.ast

@singledispatch
def pointwise_sat(stl):
    raise NotImplementedError


@pointwise_sat.register(stl.Or)
def _(stl):
    return lambda x, t: any(pointwise_sat(arg)(x, t) for arg in stl.args)


@pointwise_sat.register(stl.And)
def _(stl):
    return lambda x, t: all(pointwise_sat(arg)(x, t) for arg in stl.args)


@pointwise_sat.register(stl.F)
def _(stl):
    lo, hi = stl.interval
    return lambda x, t: any((pointwise_sat(stl.arg)(x, t + t2) 
                             for t2 in x[lo:hi].index))


@pointwise_sat.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    return lambda x, t: all((pointwise_sat(stl.arg)(x, t + t2) 
                             for t2 in x[lo:hi].index))


@pointwise_sat.register(stl.Neg)
def _(stl):
    return lambda x, t: not pointwise_sat(arg)(x, t)


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


@pointwise_sat.register(stl.LinEq)
def _(stl):
    op = op_lookup[stl.op]
    return lambda x, t: op(eval_terms(stl, x, t), stl.const)


def eval_terms(lineq, x, t):
    psi = lens(lineq).terms.each_().modify(eval_term(x, t))
    return sum(psi.terms)


def eval_term(x, t):
    return lambda term: term.coeff*x[term.id.name][t]
