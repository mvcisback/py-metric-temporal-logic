# TODO: technically incorrect on 0 robustness since conflates < and >

from functools import singledispatch
from operator import sub, add

import sympy as sym
from lenses import lens
from numpy import arange
from funcy import pairwise, autocurry

import stl.ast
from stl.ast import t_sym

@singledispatch
def smooth_robustness(stl, L, h):
    raise NotImplementedError

@smooth_robustness.register(stl.And)
@smooth_robustness.register(stl.G)
def _(stl, L, H):
    raise NotImplementedError("Call canonicalization function")

def soft_max(rs):
    return sym.log(sum(sym.exp(r) for r in rs))


def LSE(rs):
    return soft_max(rs) - sym.log(len(rs))


@smooth_robustness.register(stl.Or)
def _(stl, L, h):
    rl, rh = list(zip(
        *[smooth_robustness(arg, depth) for arg in stl.args]))
    return soft_max(rl), LSE(rh)


@autocurry
def x_ij(L, h, x_i, x_j):
    return (L*h + x_i + x_j)/2

@smooth_robustness.register(stl.F)
def _(stl, L, H):
    lo, hi = stl.interval
    times = arange(lo, hi, H)
    rl, rh = smooth_robustness(stl.arg)
    los, his = zip(*[rl.subs({t_sym: t}), rh.subs({t_sym: t}) for t in times])
    return LSE(rl), soft_max(map(x_ij(L, H), his))


@smooth_robustness.register(stl.Neg)
def _(stl, L, H):
    rl, rh = smooth_robustness(arg)
    return -rh, -rl

op_lookup = {
    ">": sub,
    ">=": sub,
    "<": lambda x, y: sub(y, x),
    "<=": lambda x, y: sub(y, x),
    "=": lambda a, b: -abs(a - b),
}


@smooth_robustness.register(stl.LinEq)
def _(stl, L, H):
    op = op_lookup[stl.op]
    retval = op(eval_terms(stl), stl.const)
    return retval, retval


def eval_terms(lineq):
    return sum(map(eval_term, lineq.terms))


def eval_term(term):
    return term.coeff*sym.Function(term.id.name)(t_sym)
