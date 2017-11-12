# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

import operator as op
from functools import singledispatch

import funcy as fn
import traces

import stl
import stl.ast
from stl.utils import const_trace, andf, orf


TRUE_TRACE = const_trace(True)
FALSE_TRACE = const_trace(False)


def negate_trace(x):
    return x.operation(TRUE_TRACE, op.xor)


def pointwise_sat(phi, dt=0.1):
    ap_names = [z.id for z in phi.atomic_predicates]

    def _eval_stl(x, t, dt=0.1):
        evaluated = stl.utils.eval_lineqs(phi, x)

        evaluated.update(fn.project(x, ap_names))
        return bool(eval_stl(phi, dt)(evaluated)[t])

    return _eval_stl


@singledispatch
def eval_stl(phi, dt):
    raise NotImplementedError


@eval_stl.register(stl.Or)
def eval_stl_or(phi, dt):
    fs = [eval_stl(arg, dt) for arg in phi.args]

    def _eval(x):
        out = orf(*(f(x) for f in fs))
        out.compact()
        return out

    return _eval


@eval_stl.register(stl.And)
def eval_stl_and(phi, dt):
    fs = [eval_stl(arg, dt) for arg in phi.args]

    def _eval(x):
        out = andf(*(f(x) for f in fs))
        out.compact()
        return out

    return _eval


@eval_stl.register(stl.Until)
def eval_stl_until(phi, dt):
    raise NotImplementedError


@eval_stl.register(stl.F)
def eval_stl_f(phi, dt):
    phi = ~stl.G(phi.interval, ~phi.arg)
    return eval_stl(phi, dt)


@eval_stl.register(stl.G)
def eval_stl_g(phi, dt):
    f = eval_stl(phi.arg, dt)
    a, b = phi.interval

    def process_intervals(x):
        # Need to add last interval
        intervals = fn.chain(x.iterintervals(),
                             [(x.last(), (float('inf'), None),)])
        for (start, val), (end, val2) in intervals:
            start2, end2 = start - b, end + a
            if end2 > start2:
                yield (start2, val)

    def _eval(x):
        y = f(x)
        if len(y) <= 1:
            return y

        out = traces.TimeSeries(process_intervals(y))
        out.compact()
        return out

    return _eval


@eval_stl.register(stl.Neg)
def eval_stl_neg(phi, dt):
    f = eval_stl(phi.arg, dt)

    def _eval(x):
        out = negate_trace(f(x))
        out.compact()
        return out

    return _eval


@eval_stl.register(stl.ast.Next)
def eval_stl_next(phi, dt):
    f = eval_stl(phi.arg, dt)

    def _eval(x):
        out = traces.TimeSeries((t + dt, v) for t, v in f(x))
        out.compact()
        return out

    return _eval


@eval_stl.register(stl.AtomicPred)
def eval_stl_ap(phi, _):
    def _eval(x):
        out = x[str(phi.id)]
        out.compact()
        return out

    return _eval


@eval_stl.register(type(stl.TOP))
def eval_stl_top(_, _1):
    return lambda *_: TRUE_TRACE


@eval_stl.register(type(stl.BOT))
def eval_stl_bot(_, _1):
    return lambda *_: FALSE_TRACE
