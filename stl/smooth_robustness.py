# TODO: technically incorrect on 0 robustness since conflates < and >

from functools import singledispatch
from operator import sub, add

import sympy as sym
from lenses import lens

import stl.ast
from stl.ast import t_sym

@singledispatch
def smooth_robustness(stl):
    raise NotImplementedError

def f1(rs):
    return sym.log(sum(sym.exp(r) for r in rs))

def f2(rs):
    return sym.log(sum(sym.exp(r) for r in rs)/(len(rs)))

@smooth_robustness.register(stl.Or)
def _(stl, depth=0):
    rl, rh = list(zip(*[smooth_robustness(arg, depth) for arg in stl.args]))
    return f1(rl), f2(rh)

@smooth_robustness.register(stl.And)
def _(stl, depth=0):
    rh, rl = list(zip(*[-smooth_robustness(arg, depth) for arg in stl.args]))
    return -f2(rh), -f1(rl)


def F1(r, interval, t):
    lo, hi = interval
    bounds = (t, lo, hi)
    return sym.log(sym.Integral(sym.exp(r), bounds))

def F2(r, interval, t):
    lo, hi = interval
    return F1(r, interval, t) - sym.log(hi - lo)

@smooth_robustness.register(stl.F)
def _(stl, depth=0):
    depth += 1
    t = sym.Symbol("t{}".format(depth))
    rl, rh = smooth_robustness(stl.arg)
    r = (rl.subs({t_sym: t}), rh.subs({t_sym: t}))
    return F1(r[0], stl.interval, t), F2(rh[1], stl.interval, t)

@smooth_robustness.register(stl.G)
def _(stl, depth=0):
    depth += 1
    t = sym.Symbol("t{}".format(depth))
    rl, rh = smooth_robustness(stl.arg)
    r = (rl.subs({t_sym: t}), rh.subs({t_sym: t}))
    return -F2(r[1], stl.interval, t), -F1(r[0], stl.interval, t)


@smooth_robustness.register(stl.Neg)
def _(stl, depth=0):
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
def _(stl, depth=0):
    op = op_lookup[stl.op]
    retval = op(eval_terms(stl), stl.const)
    return retval, retval


def eval_terms(lineq):
    return sum(map(eval_term, lineq.terms))


def eval_term(term):
    return term.coeff*sym.Function(term.id.name)(t_sym)
