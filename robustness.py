from functools import singledispatch
from operator import sub, add

from lenses import lens

import stl.ast


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
    return lambda x, t: max(pointwise_robustness(stl.arg)(x, t + t2) 
                            for t2 in x[lo:hi].index)


@pointwise_robustness.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    return lambda x, t: min(pointwise_robustness(stl.arg)(x, t + t2) 
                            for t2 in x[lo:hi].index)


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


def binsearch(stleval, *, tol=1e-3, lo, hi):
    """Only run search if tightest robustness was positive."""
    # Only check low since hi taken care of by precondition.
    r = stleval(lo)
    if r > 0 or abs(r) < tol: 
        return r, lo

    while abs(r) < tol:
        mid = lo + (hi - lo) / 2
        r = stleval(mid)
        if r < 0:
            lo, hi = mid, hi
        else:
            lo, hi = lo, mid
    return r, mid


def lex_param_project(stl, x, *, order, polarity, ranges, tol=1e-3):
    val = {var: (ranges[0] if polarity[var] else ranges[1]) for var in order}
    # TODO: evaluate top paramater
    for var in order:
        r, param = binsearch() #TODO
        # TODO: update val
    return val
        
