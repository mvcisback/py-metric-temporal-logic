# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

import operator as op
from collections import defaultdict
from functools import reduce, singledispatch

import funcy as fn
from discrete_signals import signal

from mtl import ast

OO = float('inf')
CONST_FALSE = signal([(0, -1)], start=-OO, end=OO, tag=ast.BOT)
CONST_TRUE = signal([(0, 1)], start=-OO, end=OO, tag=ast.TOP)


def to_signal(ts_mapping):
    start = min(fn.pluck(0, fn.cat(ts_mapping.values())))
    assert start >= 0
    signals = (signal(v, start, OO, tag=k) for k, v in ts_mapping.items())
    return reduce(op.or_, signals)


def interp(sig, t, tag=None):
    # TODO: return function that interpolates the whole signal.
    sig = sig.project({tag})
    key = sig.data.iloc[sig.data.bisect_right(t) - 1]
    return sig[key][tag]


def dense_compose(sig1, sig2, init=None):
    sig12 = sig1 | sig2
    tags = sig12.tags

    def _dense_compose():
        state = {tag: init for tag in tags}
        for t, val in sig12.items():
            state = {k: val.get(k, state[k]) for k in tags}
            yield t, state

    data = list(_dense_compose())
    return sig12.evolve(data=data)


def booleanize_signal(sig):
    return sig.transform(lambda mapping: defaultdict(
        lambda: None, {k: 2*int(v) - 1 for k, v in mapping.items()}
    ))


def pointwise_sat(phi, dt=0.1):
    f = eval_mtl(phi, dt)

    def _eval_mtl(x, t=0, quantitative=False):
        sig = to_signal(x)
        if not quantitative:
            sig = booleanize_signal(sig)

        res = interp(f(sig), t, phi)
        return res if quantitative else res > 0

    return _eval_mtl


@singledispatch
def eval_mtl(phi, dt):
    raise NotImplementedError


@eval_mtl.register(ast.And)
def eval_mtl_and(phi, dt):
    fs = [eval_mtl(arg, dt) for arg in phi.args]

    def _eval(x):
        sigs = [f(x) for f in fs]
        sig = reduce(lambda x, y: dense_compose(x, y, init=OO), sigs)
        return sig.map(lambda v: min(v.values()), tag=phi)

    return _eval


def apply_weak_until(left_key, right_key, sig):
    prev, max_right = OO, -OO

    for t in reversed(sig.times()):
        left, right = interp(sig, t, left_key), interp(sig, t, right_key)

        max_right = max(max_right, right)
        prev = max(right, min(left, prev), -max_right)
        yield (t, prev)


@eval_mtl.register(ast.WeakUntil)
def eval_mtl_until(phi, dt):
    f1, f2 = eval_mtl(phi.arg1, dt), eval_mtl(phi.arg2, dt)

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=-OO)
        data = apply_weak_until(phi.arg1, phi.arg2, sig)
        return signal(data, x.start, OO, tag=phi)

    return _eval


@eval_mtl.register(ast.G)
def eval_mtl_g(phi, dt):
    f = eval_mtl(phi.arg, dt)
    a, b = phi.interval
    if b < a:
        return lambda x: CONST_TRUE.retag({ast.TOP: phi})

    def _min(val):
        return min(val[phi.arg])

    def _eval(x):
        return f(x).rolling(a, b).map(_min, tag=phi)

    return _eval


@eval_mtl.register(ast.Neg)
def eval_mtl_neg(phi, dt):
    f = eval_mtl(phi.arg, dt)

    def _eval(x):
        return f(x).map(lambda v: -v[phi.arg], tag=phi)

    return _eval


@eval_mtl.register(ast.Next)
def eval_mtl_next(phi, dt):
    f = eval_mtl(phi.arg, dt)

    def _eval(x):
        return (f(x) << dt).retag({phi.arg: phi})

    return _eval


@eval_mtl.register(ast.AtomicPred)
def eval_mtl_ap(phi, _):
    def _eval(x):
        return x.project({phi.id}).retag({phi.id: phi})

    return _eval


@eval_mtl.register(type(ast.BOT))
def eval_mtl_bot(_, _1):
    return lambda x: CONST_FALSE
