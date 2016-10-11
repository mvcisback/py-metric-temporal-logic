# TODO: technically incorrect on 0 robustness since conflates < and >

from functools import singledispatch
from operator import sub, add

import numpy as np
from lenses import lens

import stl.ast

oo = float('inf')

@singledispatch
def pointwise_robustness(stl):
    raise NotImplementedError


@pointwise_robustness.register(stl.Or)
def _(stl):
    return lambda x, t: max(pointwise_robustness(arg)(x, t) for arg in stl.args)


@pointwise_robustness.register(stl.And)
def _(stl):
    return lambda x, t: min(pointwise_robustness(arg)(x, t) for arg in stl.args)


@pointwise_robustness.register(stl.F)
def _(stl):
    lo, hi = stl.interval
    return lambda x, t: max((pointwise_robustness(stl.arg)(x, t + t2) 
                             for t2 in x[lo:hi].index), default=-oo)


@pointwise_robustness.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    return lambda x, t: min((pointwise_robustness(stl.arg)(x, t + t2) 
                             for t2 in x[lo:hi].index), default=oo)


@pointwise_robustness.register(stl.Neg)
def _(stl):
    return lambda x, t: -pointwise_robustness(arg)(x, t)


op_lookup = {
    ">": sub,
    ">=": sub,
    "<": lambda x, y: sub(y, x),
    "<=": lambda x, y: sub(y, x),
    "=": lambda a, b: -abs(a - b),
}



@pointwise_robustness.register(stl.LinEq)
def _(stl):
    op = op_lookup[stl.op]
    return lambda x, t: op(eval_terms(stl, x, t), stl.const)


def eval_terms(lineq, x, t):
    psi = lens(lineq).terms.each_().modify(eval_term(x, t))
    return sum(psi.terms)


def eval_term(x, t):
    # TODO(lift interpolation much higher)
    return lambda term: term.coeff*np.interp(t, x.index, x[term.id.name])
