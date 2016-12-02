# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

from functools import singledispatch
import operator as op

import numpy as np
import sympy as smp
from lenses import lens
import gmpy2 as gp

import stl.ast

@singledispatch
def pointwise_sat(stl):
    raise NotImplementedError


@pointwise_sat.register(stl.Or)
def _(stl):
    def sat_comp(x,t):
        val = 0
        for arg in stl.args:
            val = pointwise_sat(arg)(x, t) | val
        return val
    return sat_comp
    #return lambda x, t: any(pointwise_sat(arg)(x, t) for arg in stl.args)


@pointwise_sat.register(stl.And)
def _(stl):
    def sat_comp(x,t):
        val = 2**(len(t))-1
        for arg in stl.args:
            val = pointwise_sat(arg)(x, t) & val
        return val
    return sat_comp
    #return lambda x, t: all(pointwise_sat(arg)(x, t) for arg in stl.args)


@pointwise_sat.register(stl.F)
def _(stl):
    lo, hi = stl.interval
    def sat_comp(x,t):
        val = 0
        for tau in t:
            tau_t = [min(tau + t2, x.index[-1]) for t2 in x[lo:hi].index]
            val = (val << 1) | (pointwise_sat(stl.arg)(x, tau_t) > 0)
        return val
    return sat_comp
    #return lambda x, t, val: [pointwise_sat(stl.arg)(x, [min(deltat + t2, x.index[-1])
    #                         for t2 in x[lo:hi].index], 0) for deltat in t]


@pointwise_sat.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    def sat_comp(x,t):
        val = 0
        for tau in t:
            tau_t = [min(tau + t2, x.index[-1]) for t2 in x[lo:hi].index]
            val = (val << 1) | (gp.popcount(pointwise_sat(stl.arg)(x, tau_t)) == len(tau_t))
        return val
    return sat_comp
    #return lambda x, t: all((pointwise_sat(stl.arg)(x, min(t + t2, x.index[-1])) 
    #                         for t2 in x[lo:hi].index))


@pointwise_sat.register(stl.Neg)
def _(stl):
    def sat_comp(x,t):
        val = pointwise_sat(arg)(x, t) ^ (2**(len(t))-1)
        return val
    return sat_comp
    #return lambda x, t:  pointwise_sat(arg)(x, t, val)


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


@pointwise_sat.register(stl.AtomicPred)
def _(stl):
    def sat_comp(x, t):
        val = 0
        for tau in t:
            val = (val << 1) | (1 if x[stl.id][tau] else 0)
        return val
    return sat_comp
    #return lambda x, t, val: [(val << 1) | (x[stl.id][deltat] == True) for deltat in t] 


@pointwise_sat.register(stl.LinEq)
def _(stl):
    op = op_lookup[stl.op]
    def sat_comp(x, t):
        val = 0
        for tau in t:
            val = (val << 1) | (op(eval_terms(stl, x, tau), stl.const) == True)
        return val
    return sat_comp 
    #return lambda x, t, val: [(val << 1) |(op(eval_terms(stl, x, deltat), stl.const) == True) for deltat in t]


def eval_terms(lineq, x, t):
    psi = lens(lineq).terms.each_().modify(eval_term(x, t))
    return sum(psi.terms)


def eval_term(x, t):
    # TODO(lift interpolation much higher)
    return lambda term: term.coeff*np.interp(t, x.index, x[term.id.name])
