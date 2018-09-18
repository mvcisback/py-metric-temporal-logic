# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

import operator as op
from functools import singledispatch

import funcy as fn
import traces

import mtl
import mtl.ast
from mtl.utils import const_trace, andf, orf

TRUE_TRACE = const_trace(True)
FALSE_TRACE = const_trace(False)


def negate_trace(x):
    return x.operation(TRUE_TRACE, op.xor)


def pointwise_sat(phi, dt=0.1):
    ap_names = [z.id for z in phi.atomic_predicates]

    def _eval_mtl(x, t=0):
        return bool(eval_mtl(phi, dt)(x)[t])

    return _eval_mtl


@singledispatch
def eval_mtl(phi, dt):
    raise NotImplementedError


def or_traces(xs):
    return orf(*xs)


@eval_mtl.register(mtl.Or)
def eval_mtl_or(phi, dt):
    fs = [eval_mtl(arg, dt) for arg in phi.args]

    def _eval(x):
        out = or_traces([f(x) for f in fs])
        out.compact()
        return out

    return _eval


def and_traces(xs):
    return andf(*xs)


@eval_mtl.register(mtl.And)
def eval_mtl_and(phi, dt):
    fs = [eval_mtl(arg, dt) for arg in phi.args]

    def _eval(x):
        out = and_traces([f(x) for f in fs])
        out.compact()
        return out

    return _eval


def apply_until(y):
    if len(y) == 1:
        left, right = y.first_value()
        yield (0, min(left, right))
        return
    periods = list(y.iterperiods())
    phi2_next = False
    for t, _, (phi1, phi2) in periods[::-1]:
        yield (t, phi2 or (phi1 and phi2_next))
        phi2_next = phi2


@eval_mtl.register(mtl.Until)
def eval_mtl_until(phi, dt):
    f1, f2 = eval_mtl(phi.arg1, dt), eval_mtl(phi.arg2, dt)

    def _eval(x):
        y1, y2 = f1(x), f2(x)
        y = y1.operation(y2, lambda a, b: (a, b))
        out = traces.TimeSeries(apply_until(y))
        out.compact()

        return out

    return _eval


@eval_mtl.register(mtl.F)
def eval_mtl_f(phi, dt):
    phi = ~mtl.G(phi.interval, ~phi.arg)
    return eval_mtl(phi, dt)


@eval_mtl.register(mtl.G)
def eval_mtl_g(phi, dt):
    f = eval_mtl(phi.arg, dt)
    a, b = phi.interval
    if b < a:
        return lambda _: TRUE_TRACE

    def process_intervals(x):
        # Need to add last interval
        intervals = fn.chain(x.iterintervals(), [(
            x.first_item(),
            (float('inf'), None),
        )])
        for (start, val), (end, val2) in intervals:
            start2, end2 = start - b, end + a
            if end2 > start2:
                yield (start2, val)

    if b == float('inf'):
        def _eval(x):
            y = f(x).slice(a, b)
            y.compact()
            val = len(y) == 1 and y[a]
            return const_trace(val)
    else:
        def _eval(x):
            y = f(x)
            if len(y) <= 1:
                return y

            out = traces.TimeSeries(process_intervals(y)).slice(
                y.first_key(), float('inf')
            )
            out.compact()
            return out

    return _eval


@eval_mtl.register(mtl.Neg)
def eval_mtl_neg(phi, dt):
    f = eval_mtl(phi.arg, dt)

    def _eval(x):
        out = negate_trace(f(x))
        out.compact()
        return out

    return _eval


@eval_mtl.register(mtl.ast.Next)
def eval_mtl_next(phi, dt):
    f = eval_mtl(phi.arg, dt)

    def _eval(x):
        y = f(x)
        out = traces.TimeSeries(((t - dt, v) for t, v in y))
        out = out.slice(0, float('inf'))
        out.compact()

        return out

    return _eval


@eval_mtl.register(mtl.AtomicPred)
def eval_mtl_ap(phi, _):
    def _eval(x):
        out = x[str(phi.id)]
        out.compact()

        return out

    return _eval


@eval_mtl.register(type(mtl.TOP))
def eval_mtl_top(_, _1):
    return lambda *_: TRUE_TRACE


@eval_mtl.register(type(mtl.BOT))
def eval_mtl_bot(_, _1):
    return lambda *_: FALSE_TRACE
