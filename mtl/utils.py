import operator as op
from functools import reduce, wraps
from math import isfinite

from discrete_signals import signal
import numpy as np

import mtl.ast
from mtl.ast import (And, G, Interval, Neg, Next, WeakUntil,
                     AtomicPred, _Bot)

oo = float('inf')


def const_trace(x):
    return signal([(0, x)], start=0, end=oo)


def require_discretizable(func):
    @wraps(func)
    def _func(phi, dt, *args, **kwargs):
        if 'horizon' not in kwargs:
            assert is_discretizable(phi, dt)
        return func(phi, dt, *args, **kwargs)

    return _func


def scope(phi, dt, *, _t=0, horizon=oo):
    if isinstance(phi, Next):
        _t += dt
    elif isinstance(phi, G):
        _t += phi.interval.upper
    elif isinstance(phi, WeakUntil):
        _t += float('inf')

    _scope = max((scope(c, dt, _t=_t) for c in phi.children), default=_t)
    return min(_scope, horizon)


# Code to discretize a bounded MTL formula


@require_discretizable
def discretize(phi, dt, distribute=False, *, horizon=None):
    if horizon is None:
        horizon = oo

    phi = _discretize(phi, dt, horizon)
    return _distribute_next(phi) if distribute else phi


def _discretize(phi, dt, horizon):
    if isinstance(phi, (AtomicPred, _Bot)):
        return phi

    if not isinstance(phi, (G, WeakUntil)):
        children = tuple(_discretize(arg, dt, horizon) for arg in phi.children)
        if isinstance(phi, And):
            return phi.evolve(args=children)
        elif isinstance(phi, (Neg, Next)):
            return phi.evolve(arg=children[0])

        raise NotImplementedError

    elif isinstance(phi, WeakUntil):
        raise NotImplementedError

    # Only remaining cases are G and F
    upper = min(phi.interval.upper, horizon)
    l, u = round(phi.interval.lower / dt), round(upper / dt)

    psis = (next(_discretize(phi.arg, dt, horizon - i), i)
            for i in range(l, u + 1))
    opf = andf if isinstance(phi, G) else orf
    return opf(*psis)


def _interval_discretizable(itvl, dt):
    l, u = itvl.lower / dt, itvl.upper / dt
    if not (isfinite(l) and isfinite(u)):
        return False
    return np.isclose(l, round(l)) and np.isclose(u, round(u))


def _distribute_next(phi, i=0):
    if isinstance(phi, AtomicPred):
        return mtl.utils.next(phi, i=i)
    elif isinstance(phi, Next):
        return _distribute_next(phi.arg, i=i+1)

    children = tuple(_distribute_next(c, i) for c in phi.children)

    if isinstance(phi, And):
        return phi.evolve(args=children)
    elif isinstance(phi, (Neg, Next)):
        return phi.evolve(arg=children[0])


def is_discretizable(phi, dt):
    if any(c for c in phi.walk() if isinstance(c, WeakUntil)):
        return False

    return all(
        _interval_discretizable(c.interval, dt) for c in phi.walk()
        if isinstance(c, G))

# EDSL


def alw(phi, *, lo=0, hi=float('inf')):
    return G(Interval(lo, hi), phi)


def env(phi, *, lo=0, hi=float('inf')):
    return ~alw(~phi, lo=lo, hi=hi)


def andf(*args):
    return reduce(op.and_, args) if args else mtl.TOP


def orf(*args):
    return reduce(op.or_, args) if args else mtl.TOP


def implies(x, y):
    return ~x | y


def xor(x, y):
    return (x | y) & ~(x & y)


def iff(x, y):
    return (x & y) | (~x & ~y)


def next(phi, i=1):
    return phi >> i


def until(phi, psi):
    return mtl.ast.WeakUntil(phi, psi) & env(psi)


def timed_until(phi, psi, lo, hi):
    return env(psi, lo=lo, hi=hi) & alw(until(phi, psi), lo=0, hi=lo)
