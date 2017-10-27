# TODO: figure out how to deduplicate this with robustness
# - Abstract as working on distributive lattice

import operator as op
from functools import singledispatch

import funcy as fn
import stl
import stl.ast
from lenses import lens

oo = float('inf')


def pointwise_sat(phi):
    ap_names = [z.id.name for z in stl.utils.AP_lens(phi).Each().collect()]

    def _eval_stl(x, t):
        evaluated = stl.utils.eval_lineqs(phi, x)
        evaluated.update(fn.project(x, ap_names))
        return eval_stl(phi)(evaluated, t)

    return _eval_stl


@singledispatch
def eval_stl(stl):
    raise NotImplementedError


@eval_stl.register(stl.Or)
def eval_stl_or(phi):
    fs = [eval_stl(arg) for arg in phi.args]
    return lambda x, t: any(f(x, t) for f in fs)


@eval_stl.register(stl.And)
def eval_stl_and(stl):
    fs = [eval_stl(arg) for arg in stl.args]
    return lambda x, t: all(f(x, t) for f in fs)


def get_times(x, tau, lo=None, hi=None):
    domain = fn.first(x.values()).domain
    if lo is None or lo is -oo:
        lo = domain.start()
    if hi is None or hi is oo:
        hi = domain.end()
    end = min(v.domain.end() for v in x.values())
    hi = hi + tau if hi + tau <= end else end
    lo = lo + tau if lo + tau <= end else end

    if lo > hi:
        return []
    elif hi == lo:
        return [lo]

    all_times = fn.cat(v.slice(lo, hi).items() for v in x.values())
    return sorted(set(fn.pluck(0, all_times)))


@eval_stl.register(stl.Until)
def eval_stl_until(stl):
    def _until(x, t):
        f1, f2 = eval_stl(stl.arg1), eval_stl(stl.arg2)
        for tau in get_times(x, t):
            if not f1(x, tau):
                return f2(x, tau)
        return False

    return _until


def eval_unary_temporal_op(phi, always=True):
    fold = all if always else any
    lo, hi = phi.interval
    if lo > hi:
        retval = True if always else False
        return lambda x, t: retval
    f = eval_stl(phi.arg)
    if hi == lo:
        return lambda x, t: f(x, t)
    return lambda x, t: fold(f(x, tau) for tau in get_times(x, t, lo, hi))


@eval_stl.register(stl.F)
def eval_stl_f(phi):
    return eval_unary_temporal_op(phi, always=False)


@eval_stl.register(stl.G)
def eval_stl_g(phi):
    return eval_unary_temporal_op(phi, always=True)


@eval_stl.register(stl.Neg)
def eval_stl_neg(stl):
    f = eval_stl(stl.arg)
    return lambda x, t: not f(x, t)


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


@eval_stl.register(stl.AtomicPred)
def eval_stl_ap(stl):
    return lambda x, t: x[str(stl.id)][t]


@eval_stl.register(type(stl.TOP))
def eval_stl_top(_):
    return lambda *_: True


@eval_stl.register(type(stl.BOT))
def eval_stl_bot(_):
    return lambda *_: False


@eval_stl.register(stl.LinEq)
def eval_stl_lineq(lineq):
    return lambda x, t: x[lineq][t]


def eval_terms(lineq, x, t):
    terms = lens(lineq).terms.each_().get_all()
    return sum(eval_term(term, x, t) for term in terms)


def eval_term(term, x, t):
    return float(term.coeff) * x[term.id][t]
