# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

import operator as op
from functools import singledispatch, reduce

import funcy as fn
import traces

import mtl
from mtl import ast
from mtl.utils import const_trace, andf, orf

TRUE_TRACE = const_trace(1)
FALSE_TRACE = const_trace(-1)


def negate_trace(x):
    return x.operation(FALSE_TRACE, lambda x, y: x*y)


def pointwise_sat(phi, dt=0.1):
    ap_names = [z.id for z in phi.atomic_predicates]

    def _eval_mtl(x, t=None):
        if t is None:
            t = max(v.last_key() for v in x.values())
        return eval_mtl(phi, dt)(x)[t]

    return _eval_mtl


@singledispatch
def eval_mtl(phi, dt):
    raise NotImplementedError


@eval_mtl.register(ast.And)
def eval_mtl_and(phi, dt):
    fs = [eval_mtl(arg, dt) for arg in phi.args]
    if len(fs) == 0:
        return lambda _: TRUE_TRACE
    elif len(fs) == 1:
        return fs[0]

    def _eval(x):
        return reduce(lambda x, y: x.operation(y, min), [f(x) for f in fs])

    return _eval


def apply_weak_since(y1, y2):
    y = list(y1.operation(y2, lambda a, b: (a, b)))
    prev, max_right = float('inf'), -float('inf')
    for t, (left, right) in y:
        max_right = max(max_right, right)
        prev = max(right, min(left, prev), -max_right)
        yield (t, prev)


@eval_mtl.register(ast.WeakSince)
def eval_mtl_weak_since(phi, dt):
    f1, f2 = eval_mtl(phi.arg1, dt), eval_mtl(phi.arg2, dt)
    
    def _eval(x):
        y1, y2 = f1(x), f2(x)
        return traces.TimeSeries(apply_weak_since(y1, y2))

    return _eval


@eval_mtl.register(ast.Hist)
def eval_mtl_hist(phi, dt):
    f = eval_mtl(phi.arg, dt)

    if phi.interval is not None:
        if phi.interval[0] > phi.interval[1]:
            return lambda _: TRUE_TRACE
        elif phi.interval[0] == phi.interval[1]:
            return lambda x: const_trace(x[phi.interval[0]])    
        else:
            lo, hi = phi.interval
    else:
        lo, hi = 

    def _eval(x):
        y = f(x)
        if len(y) == 1:
            return y

        min_val = min((v for t, v in y.sl), default=1)
        return const_trace(min_val)

    return _eval


@eval_mtl.register(ast.Neg)
def eval_mtl_neg(phi, dt):
    f = eval_mtl(phi.arg, dt)

    def _eval(x):
        return negate_trace(f(x))

    return _eval


@eval_mtl.register(ast.VariantYesterday)
def eval_mtl_next(phi, dt):
    f = eval_mtl(phi.arg, dt)

    def _eval(x):
        y = f(x)
        out = traces.TimeSeries([(0, 1)] + [(t + dt, v) for t, v in y])
        out = out.slice(0, float('inf'))

        return out

    return _eval


@eval_mtl.register(mtl.AtomicPred)
def eval_mtl_ap(phi, _):
    def _eval(x):
        return x[phi.id]

    return _eval


@eval_mtl.register(type(mtl.BOT))
def eval_mtl_bot(_, _1):
    return lambda *_: FALSE_TRACE
