# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

from functools import singledispatch
import operator as op

import numpy as np
from lenses import lens

import stl.ast

@singledispatch
def pointwise_sat(stl):
    raise NotImplementedError


@pointwise_sat.register(stl.Or)
def _(stl):
    fs = [pointwise_sat(arg) for arg in stl.args]
    return lambda x, t: any(f(x, t) for f in fs)


@pointwise_sat.register(stl.And)
def _(stl):
    fs = [pointwise_sat(arg) for arg in stl.args]
    return lambda x, t: all(f(x, t) for f in fs)


@pointwise_sat.register(stl.Until)
def _(stl):
    def _until(x, t):
        phi = (pointwise_sat(phi)(x, t) for t in x.index)
    return lambda x, t: any((pointwise_sat(stl.arg)(x, min(t + t2, x.index[-1]))
                             for t2 in x[lo:hi].index))


@pointwise_sat.register(stl.F)
def _(stl):
    lo, hi = stl.interval
    f = pointwise_sat(stl.arg) 
    return lambda x, t: any((f(x, min(t + t2, x.index[-1]))
                             for t2 in x[lo:hi].index))


@pointwise_sat.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    f = pointwise_sat(stl.arg) 
    return lambda x, t: all((pointwise_sat(stl.arg)(x, min(t + t2, x.index[-1])) 
                             for t2 in x[lo:hi].index))


@pointwise_sat.register(stl.Neg)
def _(stl):
    f = pointwise_sat(stl.arg)
    return lambda x, t: not f(x, t)


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


@pointwise_sat.register(stl.AtomicPred)
def _(stl):
    return lambda x, t: x[str(stl.id)][t]


@pointwise_sat.register(stl.LinEq)
def _(stl):
    op = op_lookup[stl.op]
    return lambda x, t: op(eval_terms(stl, x, t), stl.const)


def eval_terms(lineq, x, t):
    psi = lens(lineq).terms.each_().modify(eval_term(x, t))
    return sum(psi.terms)


def eval_term(x, t):
    # TODO(lift interpolation much higher)
    return lambda term: term.coeff*np.interp(t, x.index, x[term.id.name])
