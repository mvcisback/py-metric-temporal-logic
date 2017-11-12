import operator as op
from functools import reduce

import traces
from lenses import bind

import stl.ast
from stl.ast import (And, F, G, Interval, LinEq, Neg, Or, AP_lens)
from stl.types import STL


oo = float('inf')


def f_neg_or_canonical_form(phi: STL) -> STL:
    if isinstance(phi, LinEq):
        return phi

    children = [f_neg_or_canonical_form(s) for s in phi.children]
    if isinstance(phi, (And, G)):
        children = [Neg(s) for s in children]
    children = tuple(children)

    if isinstance(phi, Or):
        return Or(children)
    elif isinstance(phi, And):
        return Neg(Or(children))
    elif isinstance(phi, Neg):
        return Neg(children[0])
    elif isinstance(phi, F):
        return F(phi.interval, children[0])
    elif isinstance(phi, G):
        return Neg(F(phi.interval, children[0]))
    else:
        raise NotImplementedError


def _lineq_lipschitz(lineq):
    return sum(map(abs, bind(lineq).Each().terms.Each().coeff.collect()))


def linear_stl_lipschitz(phi):
    """Infinity norm lipschitz bound of linear inequality predicate."""
    return float(max(map(_lineq_lipschitz, phi.lineqs)))


def inline_context(phi, context):
    phi2 = None

    def update(ap):
        return context.get(ap, ap)

    while phi2 != phi:
        phi2, phi = phi, AP_lens(phi).modify(update)
    # TODO: this is hack to flatten the AST. Fix!
    return stl.parse(str(phi))


op_lookup = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "=": op.eq,
}


def get_times(x):
    times = set.union(*({t for t, _ in v.items()} for v in x.values()))
    return sorted(times)


def const_trace(x, start=0):
    return traces.TimeSeries([(start, x)], domain=traces.Domain(start, oo))


def eval_lineq(lineq, x, domain, compact=True):
    lhs = sum(const_trace(term.coeff)*x[term.id] for term in lineq.terms)
    compare = op_lookup.get(lineq.op)
    output = lhs.operation(const_trace(lineq.const), compare)
    output.domain = domain

    if compact:
        output.compact()
    return output


def eval_lineqs(phi, x):
    lineqs = phi.lineqs
    start = max(y.domain.start() for y in x.values())
    end = min(y.domain.end() for y in x.values())
    domain = traces.Domain(start, end)
    return {lineq: eval_lineq(lineq, x, domain) for lineq in lineqs}


# EDSL


def alw(phi, *, lo=0, hi=float('inf')):
    return G(Interval(lo, hi), phi)


def env(phi, *, lo=0, hi=float('inf')):
    return F(Interval(lo, hi), phi)


def andf(*args):
    return reduce(op.and_, args) if args else stl.TOP


def orf(*args):
    return reduce(op.or_, args) if args else stl.TOP


def implies(x, y):
    return ~x | y


def xor(x, y):
    return (x | y) & ~(x & y)


def iff(x, y):
    return (x & y) | (~x & ~y)


def timed_until(phi, psi, lo, hi):
    return env(psi, lo=lo, hi=hi) & alw(stl.ast.Until(phi, psi), lo=0, hi=lo)
