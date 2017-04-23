# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

from functools import singledispatch
import operator as op

import numpy as np
import funcy as fn
from lenses import lens

import stl.ast

oo = float('inf')

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


def get_times(x, tau, lo=None, hi=None):
    if lo is None or lo is -oo:
        lo = min(v.first()[0] for v in x.values())
    if hi is None or hi is oo:
        hi = max(v.last()[0] for v in x.values())
    if lo > hi:
        return []
    elif hi == lo:
        return [lo]

    all_times = fn.cat(v.slice(lo, hi).items() for v in x.values())
    return sorted(set(fn.pluck(0, all_times)))


@pointwise_sat.register(stl.Until)
def _(stl):
    def _until(x, t):
        f1, f2 = pointwise_sat(stl.arg1), pointwise_sat(stl.arg2)
        for tau in get_times(x, t):
            if not f1(x, tau):
                return f2(x, tau)
        return False
    return _until


def eval_unary_temporal_op(phi, always=True):
    fold = all if always else any
    lo, hi = phi.interval
    if lo > hi:
        retval = True if always else False
        return lambda x, t: retval
    if hi == lo:
        return lambda x, t: f(x, t)
    f = pointwise_sat(phi.arg) 
    return lambda x, t: fold(f(x, tau) for tau in get_times(x, t, lo, hi))


@pointwise_sat.register(stl.F)
def _(phi):
    return eval_unary_temporal_op(phi, always=False)


@pointwise_sat.register(stl.G)
def _(phi):
    return eval_unary_temporal_op(phi, always=True)


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
    return lambda term: term.coeff*x[term.id.name][t]
