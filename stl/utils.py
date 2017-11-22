import operator as op
from functools import reduce, wraps
from math import isfinite

import traces
import numpy as np
from lenses import bind

import stl.ast
from stl.ast import (And, F, G, Interval, LinEq, Neg, Or, Next, Until,
                     AtomicPred, _Top, _Bot)
from stl.types import STL

oo = float('inf')


def f_neg_or_canonical_form(phi: STL) -> STL:
    if isinstance(phi, (LinEq, AtomicPred, _Top, _Bot)):
        return phi

    children = [f_neg_or_canonical_form(s) for s in phi.children]
    if isinstance(phi, (And, G)):
        children = [Neg(s) for s in children]
    children = tuple(sorted(children, key=str))

    if isinstance(phi, Or):
        return Or(children)
    elif isinstance(phi, And):
        return Neg(Or(children))
    elif isinstance(phi, Neg):
        return Neg(*children)
    elif isinstance(phi, Next):
        return Next(*children)
    elif isinstance(phi, Until):
        return Until(*children)
    elif isinstance(phi, F):
        return F(phi.interval, *children)
    elif isinstance(phi, G):
        return Neg(F(phi.interval, *children))
    else:
        raise NotImplementedError


def _lineq_lipschitz(lineq):
    return sum(map(abs, bind(lineq).terms.Each().coeff.collect()))


def linear_stl_lipschitz(phi):
    """Infinity norm lipschitz bound of linear inequality predicate."""
    if any(isinstance(psi, (AtomicPred, _Top, _Bot)) for psi in phi.walk()):
        return float('inf')

    return float(max(map(_lineq_lipschitz, phi.lineqs), default=float('inf')))


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


def const_trace(x, start=0):
    return traces.TimeSeries([(start, x)], domain=traces.Domain(start, oo))


def eval_lineq(lineq, x, domain, compact=True):
    lhs = sum(const_trace(term.coeff) * x[term.id] for term in lineq.terms)
    compare = op_lookup.get(lineq.op)
    output = lhs.operation(const_trace(lineq.const), compare)
    output.domain = domain

    if compact:
        output.compact()
    return output


def eval_lineqs(phi, x):
    lineqs = phi.lineqs
    start = max(y.domain.start() for y in x.values())
    end = min(y.domain.end() for y in x.values())
    domain = traces.Domain(start, end)
    return {lineq: eval_lineq(lineq, x, domain) for lineq in lineqs}


def implicit_validity_domain(phi, trace):
    params = {ap.name for ap in phi.params}
    order = tuple(params)

    def vec_to_dict(theta):
        return {k: v for k, v in zip(order, theta)}

    def oracle(theta):
        return stl.pointwise_sat(phi.set_params(vec_to_dict(theta)))(trace, 0)

    return oracle, order


def require_discretizable(func):
    @wraps(func)
    def _func(phi, dt, *args, **kwargs):
        assert is_discretizable(phi, dt)
        return func(phi, dt, *args, **kwargs)

    return _func


def scope(phi, dt, *, _t=0):
    if isinstance(phi, Next):
        _t += dt
    elif isinstance(phi, (G, F)):
        _t += phi.interval.upper
    elif isinstance(phi, Until):
        _t += float('inf')

    return max((scope(c, dt, _t=_t) for c in phi.children), default=_t)


# Code to discretize a bounded STL formula


@require_discretizable
def discretize(phi, dt):
    return _discretize(phi, dt)


def _discretize(phi, dt):
    if isinstance(phi, (LinEq, AtomicPred)):
        return phi

    children = tuple(_discretize(arg, dt) for arg in phi.children)
    if isinstance(phi, (And, Or)):
        return bind(phi).args.set(children)
    elif isinstance(phi, (Neg, Next)):
        return bind(phi).arg.set(children[0])

    # Only remaining cases are G and F
    psi = children[0]
    l, u = round(phi.interval.lower / dt), round(phi.interval.upper / dt)
    psis = (next(psi, i) for i in range(l, u + 1))
    opf = andf if isinstance(phi, G) else orf
    return opf(*psis)


def _interval_discretizable(itvl, dt):
    l, u = itvl.lower / dt, itvl.upper / dt
    if not (isfinite(l) and isfinite(u)):
        return False
    return np.isclose(l, round(l)) and np.isclose(u, round(u))


def is_discretizable(phi, dt):
    if any(c for c in phi.walk() if isinstance(c, Until)):
        return False

    return all(
        _interval_discretizable(c.interval, dt) for c in phi.walk()
        if isinstance(c, (F, G)))


# EDSL


def alw(phi, *, lo=0, hi=float('inf')):
    return G(Interval(lo, hi), phi)


def env(phi, *, lo=0, hi=float('inf')):
    return F(Interval(lo, hi), phi)


def andf(*args):
    return reduce(op.and_, args) if args else stl.TOP


def orf(*args):
    return reduce(op.or_, args) if args else stl.TOP


def implies(x, y):
    return ~x | y


def xor(x, y):
    return (x | y) & ~(x & y)


def iff(x, y):
    return (x & y) | (~x & ~y)


def next(phi, i=1):
    for _ in range(i):
        phi = Next(phi)
    return phi


def timed_until(phi, psi, lo, hi):
    return env(psi, lo=lo, hi=hi) & alw(stl.ast.Until(phi, psi), lo=0, hi=lo)
