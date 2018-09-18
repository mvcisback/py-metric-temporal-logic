from functools import reduce, singledispatch
from operator import and_, or_

import funcy as fn
from bitarray import bitarray

import mtl.ast

oo = float('inf')


def get_times(x, tau, lo, hi):
    end = min(v.last_key() for v in x.values())

    lo, hi = map(float, (lo, hi))
    hi = hi + tau if hi + tau <= end else end
    lo = lo + tau if lo + tau <= end else end

    if lo > hi:
        return []
    elif hi == lo:
        return [lo]

    all_times = fn.cat(v.slice(lo, hi).items() for v in x.values())
    return sorted(set(fn.pluck(0, all_times)))


def pointwise_sat(mtl):
    f = pointwise_satf(mtl)
    return lambda x, t: bool(int(f(x, [t]).to01()))


@singledispatch
def pointwise_satf(mtl):
    raise NotImplementedError


def bool_op(mtl, conjunction=False):
    binop = and_ if conjunction else or_
    fs = [pointwise_satf(arg) for arg in mtl.args]
    return lambda x, t: reduce(binop, (f(x, t) for f in fs))


@pointwise_satf.register(mtl.Or)
def pointwise_satf_or(mtl):
    return bool_op(mtl, conjunction=False)


@pointwise_satf.register(mtl.And)
def pointwise_satf_and(mtl):
    return bool_op(mtl, conjunction=True)


def temporal_op(mtl, lo, hi, conjunction=False):
    fold = bitarray.all if conjunction else bitarray.any
    f = pointwise_satf(mtl.arg)

    def sat_comp(x, t):
        return bitarray(fold(f(x, get_times(x, tau, lo, hi))) for tau in t)

    return sat_comp


@pointwise_satf.register(mtl.F)
def pointwise_satf_f(mtl):
    lo, hi = mtl.interval
    return temporal_op(mtl, lo, hi, conjunction=False)


@pointwise_satf.register(mtl.G)
def pointwise_satf_g(mtl):
    lo, hi = mtl.interval
    return temporal_op(mtl, lo, hi, conjunction=True)


@pointwise_satf.register(mtl.Neg)
def pointwise_satf_neg(mtl):
    return lambda x, t: ~pointwise_satf(mtl.arg)(x, t)


@pointwise_satf.register(mtl.AtomicPred)
def pointwise_satf_(phi):
    return lambda x, t: bitarray(x[str(phi.id)][tau] for tau in t)


@pointwise_satf.register(mtl.Until)
def pointwise_satf_until(phi):
    raise NotImplementedError


@pointwise_satf.register(type(mtl.TOP))
def pointwise_satf_top(_):
    return lambda _, t: bitarray([True] * len(t))


@pointwise_satf.register(type(mtl.BOT))
def pointwise_satf_bot(_):
    return lambda _, t: bitarray([False] * len(t))
