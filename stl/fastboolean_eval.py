# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

from functools import singledispatch
import operator as op

import numpy as np
import sympy as smp
from lenses import lens
import gmpy2 as gp
from bitarray import bitarray

import stl.ast

@singledispatch
def pointwise_satf(stl):
    raise NotImplementedError


@pointwise_satf.register(stl.Or)
def _(stl):
    def sat_comp(x,t):
        sat = bitarray(len(t))
        for arg in stl.args:
            sat = pointwise_satf(arg)(x, t) | sat
        return sat
    return sat_comp


@pointwise_satf.register(stl.And)
def _(stl):
    def sat_comp(x,t):
        sat = bitarray(len(t))
        sat.setall('True')
        for arg in stl.args:
            sat = pointwise_satf(arg)(x, t) & sat
        return sat
    return sat_comp


@pointwise_satf.register(stl.F)
def _(stl):
    lo, hi = stl.interval
    def sat_comp(x,t):
        sat = bitarray()
        for tau in t:
            tau_t = [min(tau + t2, x.index[-1]) for t2 in x[lo:hi].index]
            sat.append((pointwise_satf(stl.arg)(x, tau_t)).count() > 0)
        return sat
    return sat_comp


@pointwise_satf.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    def sat_comp(x,t):
        sat = bitarray()
        for tau in t:
            tau_t = [min(tau + t2, x.index[-1]) for t2 in x[lo:hi].index]
            point_sat = pointwise_satf(stl.arg)(x, tau_t)
            sat.append(point_sat.count() == point_sat.length())
        return sat
    return sat_comp


@pointwise_satf.register(stl.Neg)
def _(stl):
    return lambda x,t: ~pointwise_satf(arg)(x, t) 


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


@pointwise_satf.register(stl.AtomicPred)
def _(stl):
    def sat_comp(x, t):
        sat = bitarray()
        [sat.append(x[stl.id][tau]) for tau in t]
        return sat
    return sat_comp


@pointwise_satf.register(stl.LinEq)
def _(stl):
    op = op_lookup[stl.op]
    def sat_comp(x, t):
        sat = bitarray()
        [sat.append(op(eval_terms(stl, x, tau), stl.const)) for tau in t]
        return sat
    return sat_comp 


def eval_terms(lineq, x, t):
    psi = lens(lineq).terms.each_().modify(eval_term(x, t))
    return sum(psi.terms)


def eval_term(x, t):
    # TODO(lift interpolation much higher)
    return lambda term: term.coeff*np.interp(t, x.index, x[term.id.name])
