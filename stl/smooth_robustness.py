# TODO: technically incorrect on 0 robustness since conflates < and >

from functools import singledispatch

import sympy as sym
from numpy import arange
from funcy import pairwise, autocurry

import stl.ast
from stl.ast import t_sym
from stl.robustness import op_lookup

@singledispatch
def smooth_robustness(stl, L, h):
    raise NotImplementedError

@smooth_robustness.register(stl.And)
@smooth_robustness.register(stl.G)
def _(stl, L, H):
    raise NotImplementedError("Call canonicalization function")

def soft_max(rs, eps=0.1):
    B = 10
    return sym.log(sum(B**r for r in rs), B)


def LSE(rs, eps=0.1):
    B = 10
    return soft_max(rs) - sym.log(len(rs), B)


@smooth_robustness.register(stl.Or)
def _(stl, L, h):
    rl, rh = list(zip(
        *[smooth_robustness(arg, L, h) for arg in stl.args]))
    return soft_max(rl), LSE(rh)


@autocurry
def x_ij(L, h, xi_xj):
    x_i, x_j = xi_xj
    return (L*h + x_i + x_j)/2


@smooth_robustness.register(stl.F)
def _(stl, L, H):
    lo, hi = stl.interval
    times = arange(lo, hi, H)
    rl, rh = smooth_robustness(stl.arg, L, H)
    los, his = zip(*[(rl.subs({t_sym: t_sym + t}), rh.subs({t_sym: t_sym + t})) for t in times]) 
    return LSE(los), soft_max(map(x_ij(L, H), pairwise(his)))


@smooth_robustness.register(stl.Neg)
def _(stl, L, H):
    rl, rh = smooth_robustness(arg, L, H)
    return -rh, -rl


@smooth_robustness.register(stl.LinEq)
def _(stl, L, H):
    op = op_lookup[stl.op]
    retval = op(eval_terms(stl), stl.const)
    return retval, retval


def eval_terms(lineq):
    return sum(map(eval_term, lineq.terms))


def eval_term(term):
    return term.coeff*sym.Function(term.id.name)(t_sym)
