from functools import singledispatch, reduce
from operator import and_, or_

from bitarray import bitarray

import stl.ast
from stl.boolean_eval import eval_terms, op_lookup, get_times

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
def _(stl):
    return bool_op(stl, conjunction=False)


@pointwise_satf.register(stl.And)
def _(stl):
    return bool_op(stl, conjunction=True)


def temporal_op(stl, lo, hi, conjunction=False):
    fold = bitarray.all if conjunction else bitarray.any
    f = pointwise_satf(stl.arg)
    def sat_comp(x,t):
        return bitarray(fold(f(x, get_times(x, tau, lo, hi))) for tau in t)
    return sat_comp


@pointwise_satf.register(stl.Until)
def _(stl):
    f1, f2 = pointwise_satf(stl.arg1), pointwise_satf(stl.arg2)
    def __until(x, t):
        f1, f2 = pointwise_satf(stl.arg1), pointwise_satf(stl.arg2)

        state = False
        times = get_times(x, t[0])
        for phi, tau in zip(reversed(f1(x, times)), reversed(times)):
            if not phi:
                state = f2(x, [tau])
                
            if tau in t:
                yield state

    def _until(x, t):
        retval = bitarray(__until(x, t))
        retval.reverse()
        return retval

    return _until


@pointwise_satf.register(stl.F)
def _(stl):
    lo, hi = stl.interval
    return temporal_op(stl, lo, hi, conjunction=False)


@pointwise_satf.register(stl.G)
def _(stl):
    lo, hi = stl.interval
    return temporal_op(stl, lo, hi, conjunction=True)


@pointwise_satf.register(stl.Neg)
def _(stl):
    return lambda x,t: ~pointwise_satf(stl.arg)(x, t) 


@pointwise_satf.register(stl.AtomicPred)
def _(stl):
    return lambda x, t: bitarray(x[str(stl.id)][tau] for tau in t)

@pointwise_satf.register(type(stl.TOP))
def _(_):
    return lambda _, t: bitarray([True]*len(t))


@pointwise_satf.register(type(stl.BOT))
def _(_):
    return lambda _, t: bitarray([False]*len(t))


@pointwise_satf.register(stl.LinEq)
def _(stl):
    op = lambda a: op_lookup[stl.op](a, stl.const)
    return lambda x, t: bitarray(op(eval_terms(stl, x, tau)) for tau in t)
