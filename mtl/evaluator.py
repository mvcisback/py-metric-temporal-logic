# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice
import numbers
import operator as op
from collections import defaultdict
from functools import reduce, singledispatch

import funcy as fn
from discrete_signals import signal, DiscreteSignal
from sortedcontainers import SortedDict

from mtl import ast


OO = float('inf')


def to_signal(ts_mapping) -> DiscreteSignal:
    if isinstance(ts_mapping, DiscreteSignal):
        return ts_mapping

    start = min(fn.pluck(0, fn.cat(ts_mapping.values())))
    signals = (signal(v, start, OO, tag=k) for k, v in ts_mapping.items())
    return reduce(op.or_, signals)


def interp(sig, t, tag=None):
    idx = max(sig.data.bisect_right(t) - 1, 0)
    keys = sig.data.keys()
    while idx > 0:
        if tag in sig[keys[idx]]:
            return sig[keys[idx]][tag]
        idx = idx - 1
    key = keys[0]
    return sig[key][tag]


def interp_all(sig, t, end=OO):
    v = fn.map(lambda u: signal([(t, interp(sig, t, u))], t, end, u), sig.tags)
    return reduce(op.__or__, v)


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


def booleanize_signal(sig, logic):
    def _booleanize_value(v):
        if isinstance(v, bool):
            return logic.const_true if v else logic.const_false
        else:
            return v
    return sig.transform(lambda mapping: defaultdict(
        lambda: None, {k: _booleanize_value(v) for k, v in mapping.items()}
    ))


def pointwise_sat(phi, dt=0.1, logic=None):
    if logic is None:
        from mtl import connective
        logic = connective.default
    f = eval_mtl(phi, dt, logic)

    def _eval_mtl(x, t=0, quantitative=False):
        sig = to_signal(x)
        sig = booleanize_signal(sig, logic)

        start_time = sig.items()[0][0]

        if t is None:
            res = [(t, v[phi]) for t, v in f(sig).items() if t >= start_time]
            return res if quantitative else [(t, v >= logic.const_true) for t, v in res]

        if t is False:  # Use original signals starting time.
            t = start_time

        res = interp(f(sig), t, phi)
        return res if quantitative else res > 0

    return _eval_mtl


@singledispatch
def eval_mtl(phi, dt, logic):
    return lambda _: signal([(0, phi)], start=-OO, end=OO, tag=phi)


@eval_mtl.register(numbers.Number)
def eval_mtl_constant_number(phi, dt, logic):
    return lambda _: signal([(0, phi)], start=-OO, end=OO, tag=phi)


@eval_mtl.register(ast.And)
def eval_mtl_and(phi, dt, logic):
    fs = [eval_mtl(arg, dt, logic) for arg in phi.args]

    def _eval(x):
        sigs = [f(x) for f in fs]
        sig = reduce(lambda x, y:
                     dense_compose(x, y, init=logic.const_true), sigs)
        return sig.map(lambda v: logic.tnorm(v.values()), tag=phi)

    return _eval


@eval_mtl.register(ast.Or)
def eval_mtl_or(phi, dt, logic):
    fs = [eval_mtl(arg, dt, logic) for arg in phi.args]

    def _eval(x):
        sigs = [f(x) for f in fs]
        sig = reduce(lambda x, y:
                     dense_compose(x, y, init=logic.const_true), sigs)
        return sig.map(lambda v: logic.tconorm(v.values()), tag=phi)

    return _eval


@eval_mtl.register(ast.Lt)
def eval_mtl_lt(phi, dt, logic):
    f1, f2 = eval_mtl(phi.arg1, dt, logic), eval_mtl(phi.arg2, dt, logic)

    def _eval_lt(v):
        if v[phi.arg1] < v[phi.arg2]:
            return logic.const_true
        elif v[phi.arg2] <= v[phi.arg1] - phi.tolerance:
            return logic.const_false
        else:
            return ((v[phi.arg2] - (v[phi.arg1] - phi.tolerance)) / phi.tolerance) * (logic.const_true - logic.const_false) + logic.const_false

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=logic.const_false)
        return sig.map(_eval_lt, tag=phi)

    return _eval


@eval_mtl.register(ast.Eq)
def eval_mtl_eq(phi, dt, logic):
    f1, f2 = eval_mtl(phi.arg1, dt, logic), eval_mtl(phi.arg2, dt, logic)

    def _eval_eq(v):
        if v[phi.arg1] == v[phi.arg2]:
            return logic.const_true
        elif phi.tolerance != 0. and \
                abs(v[phi.arg1] - v[phi.arg2]) < phi.tolerance:
            return (phi.tolerance - abs(v[phi.arg1] - v[phi.arg2])) \
                   / phi.tolerance \
                   * (logic.const_true - logic.const_false) \
                   + logic.const_false
        else:
            return logic.const_false

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=logic.const_false)
        return sig.map(_eval_eq, tag=phi)

    return _eval


def apply_weak_until(left_key, right_key, sig, logic):
    ut = logic.const_false
    ga = logic.const_true

    for t in reversed(sig.times()):
        left, right = interp(sig, t, left_key), interp(sig, t, right_key)

        ga = logic.tnorm([ga, left])
        ut = max(right, logic.tnorm([left, ut]))
        yield (t, logic.tconorm([ut, ga]))


@eval_mtl.register(ast.WeakUntil)
def eval_mtl_until(phi, dt, logic):
    f1, f2 = eval_mtl(phi.arg1, dt, logic), eval_mtl(phi.arg2, dt, logic)

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=logic.const_false)
        sig = sig | interp_all(sig, x.start)
        data = apply_weak_until(phi.arg1, phi.arg2, sig, logic)
        return signal(data, x.start, x.end, tag=phi)

    return _eval


def apply_implies(left_key, right_key, sig, logic):
    for t in sig.times():
        left, right = interp(sig, t, left_key), interp(sig, t, right_key)
        yield (t, logic.implication(left, right))


@eval_mtl.register(ast.Implies)
def eval_mtl_implies(phi, dt, logic):
    f1, f2 = eval_mtl(phi.arg1, dt, logic), eval_mtl(phi.arg2, dt, logic)

    def _eval(x):
        sig = dense_compose(f1(x), f2(x), init=logic.const_false)
        sig = sig | interp_all(sig, x.start)
        data = apply_implies(phi.arg1, phi.arg2, sig, logic)
        return signal(data, x.start, x.end, tag=phi)

    return _eval


@eval_mtl.register(ast.G)
def eval_mtl_g(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)
    a, b = phi.interval
    if b < a:
        return lambda x: logic.TOP.retag({ast.TOP: phi})

    def _min(val):
        return logic.tnorm(val[phi.arg])

    def _rolling_inf(s):
        d = None
        for t in reversed(s.data):
            v = s.data[t]
            if phi.arg in v:
                if d is None:
                    d = v[phi.arg]
                d = logic.tnorm(d, v[phi.arg])
                yield t, d

    def _rolling(s, aa, bb):
        assert aa == 0, f"{aa} -- {phi}"
        # Interpolate the whole signal to include pivot points
        d = SortedDict({t: s[t][phi.arg] for t in s.times() if phi.arg in s[t]})
        for t in set(d.keys()):
            idx = max(d.bisect_right(t) - 1, 0)
            key = d.keys()[idx]
            i = t - bb - aa + dt
            if s.start <= i < s.end:
                d[i] = s[key][phi.arg]
        # Iterate over rolling window
        v = []
        for t in reversed(d):
            v.append((t, d[t]))
            while not (t + aa <= v[0][0] < t + bb):
                del v[0]
            x = [i for j, i in v]
            if len(x) > 0:
                yield t, logic.tnorm(x)
            else:
                yield t, d[t]

    def _eval(x):
        tmp = f(x)
        assert b >= a
        if b > a:
            if a < b < OO:
                if a != 0:
                    return signal(
                        _rolling(tmp, 0, b - a),
                        tmp.start,
                        tmp.end - b if b < tmp.end else tmp.end,
                        tag=phi
                    ) << a
                else:
                    return signal(
                        _rolling(tmp),
                        tmp.start,
                        tmp.end - b if b < tmp.end else tmp.end,
                        tag=phi
                    )
            else:
                return signal(
                    _rolling_inf(tmp),
                    tmp.start,
                    tmp.end - b if b < tmp.end else tmp.end,
                    tag=phi
                )
            return tmp.rolling(a, b).map(_min, tag=phi)

        return tmp.retag({phi.arg: phi})
    return _eval


def eval_mtl_g_legacy(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)
    a, b = phi.interval
    if b < a:
        return lambda x: logic.TOP.retag({ast.TOP: phi})

    def _min(val):
        return logic.tnorm(val[phi.arg])

    def _eval(x):
        tmp = f(x)
        assert b >= a
        if b > a:
            # Force valuation at pivot points
            if a < b < OO:
                ts = fn.map(
                    lambda t: interp_all(tmp, t - b - a + dt, tmp.end),
                    tmp.times())
                tmp = reduce(op.__or__, ts, tmp)[tmp.start:tmp.end]
            return tmp.rolling(a, b).map(_min, tag=phi)

        return tmp.retag({phi.arg: phi})

    return _eval


@eval_mtl.register(ast.Neg)
def eval_mtl_neg(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)

    def _eval(x):
        return f(x).map(lambda v: logic.negation(v[phi.arg]), tag=phi)

    return _eval


@eval_mtl.register(ast.Next)
def eval_mtl_next(phi, dt, logic):
    f = eval_mtl(phi.arg, dt, logic)

    def _eval(x):
        return (f(x) << dt).retag({phi.arg: phi})

    return _eval


@eval_mtl.register(ast.AtomicPred)
def eval_mtl_ap(phi, _, _2):
    def _eval(x):
        return x.project({phi.id}).retag({phi.id: phi})

    return _eval


@eval_mtl.register(type(ast.BOT))
def eval_mtl_bot(_, _1, logic):
    return lambda x: logic.BOT
