from functools import singledispatch
from operator import sub, add

from lenses import lens

import stl.ast
from stl.utils import set_params, param_lens

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
    "<": add,
    "<=": add,
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
    return lambda term: term.coeff*x[term.id.name][t]


def binsearch(stleval, *, tol=1e-3, lo, hi, polarity):
    """Only run search if tightest robustness was positive."""
    # Only check low since hi taken care of by precondition.
    r = stleval(lo)

    # TODO: early termination by bounds checks
    mid = lo
    if abs(r) < tol: 
        return r, mid

    while abs(r) > tol and hi - lo > tol:
        mid = lo + (hi - lo) / 2
        r = stleval(mid)
        if polarity: # swap direction
            r *= -1
        if r < 0:
            lo, hi = mid, hi
        else:
            lo, hi = lo, mid
    return r, mid


def lex_param_project(stl, x, *, order, polarity, ranges, tol=1e-3):
    val = {var: (ranges[var][0] if polarity[var] else ranges[var][1]) for var in order}
    # TODO: evaluate top paramater
    p_lens = param_lens(stl)
    
    def stleval_fact(var, val):
        l = lens(val)[var]
        return lambda p: pointwise_robustness(set_params(stl, l.set(p)))(x, 0)
    
    for var in order:
        stleval = stleval_fact(var, val)
        lo, hi = ranges[var]
        _, param = binsearch(stleval, lo=lo, hi=hi, tol=tol, polarity=polarity[var])
        val[var] = param

    return val
