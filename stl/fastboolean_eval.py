import operator as op
from functools import reduce, singledispatch
from operator import and_, or_

import funcy as fn
from bitarray import bitarray
from lenses import bind

import stl.ast

oo = float('inf')
op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


def eval_terms(lineq, x, t):
    terms = bind(lineq).terms.Each().collect()
    return sum(eval_term(term, x, t) for term in terms)


def eval_term(term, x, t):
    return float(term.coeff) * x[term.id][t]


def get_times(x, tau, lo=None, hi=None):
    end = min(v.domain.end() for v in x.values())
    hi = hi + tau if hi + tau <= end else end
    lo = lo + tau if lo + tau <= end else end

    if lo > hi:
        return []
    elif hi == lo:
        return [lo]

    all_times = fn.cat(v.slice(lo, hi).items() for v in x.values())
    return sorted(set(fn.pluck(0, all_times)))


def pointwise_sat(stl):
    f = pointwise_satf(stl)
    return lambda x, t: bool(int(f(x, [t]).to01()))


@singledispatch
def pointwise_satf(stl):
    raise NotImplementedError


def bool_op(stl, conjunction=False):
    binop = and_ if conjunction else or_
    fs = [pointwise_satf(arg) for arg in stl.args]
    return lambda x, t: reduce(binop, (f(x, t) for f in fs))


@pointwise_satf.register(stl.Or)
def pointwise_satf_or(stl):
    return bool_op(stl, conjunction=False)


@pointwise_satf.register(stl.And)
def pointwise_satf_and(stl):
    return bool_op(stl, conjunction=True)


def temporal_op(stl, lo, hi, conjunction=False):
    fold = bitarray.all if conjunction else bitarray.any
    f = pointwise_satf(stl.arg)

    def sat_comp(x, t):
        return bitarray(fold(f(x, get_times(x, tau, lo, hi))) for tau in t)

    return sat_comp


@pointwise_satf.register(stl.F)
def pointwise_satf_f(stl):
    lo, hi = stl.interval
    return temporal_op(stl, lo, hi, conjunction=False)


@pointwise_satf.register(stl.G)
def pointwise_satf_g(stl):
    lo, hi = stl.interval
    return temporal_op(stl, lo, hi, conjunction=True)


@pointwise_satf.register(stl.Neg)
def pointwise_satf_neg(stl):
    return lambda x, t: ~pointwise_satf(stl.arg)(x, t)


@pointwise_satf.register(stl.AtomicPred)
def pointwise_satf_(phi):
    return lambda x, t: bitarray(x[str(phi.id)][tau] for tau in t)


@pointwise_satf.register(stl.Until)
def pointwise_satf_until(phi):
    raise NotImplementedError


@pointwise_satf.register(type(stl.TOP))
def pointwise_satf_top(_):
    return lambda _, t: bitarray([True] * len(t))


@pointwise_satf.register(type(stl.BOT))
def pointwise_satf_bot(_):
    return lambda _, t: bitarray([False] * len(t))


@pointwise_satf.register(stl.LinEq)
def pointwise_satf_lineq(stl):
    def op(a):
        return op_lookup[stl.op](a, stl.const)
    return lambda x, t: bitarray(op(eval_terms(stl, x, tau)) for tau in t)
