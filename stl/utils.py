import operator as op
from collections import deque
from functools import reduce
from typing import List, Mapping, Type, TypeVar

import funcy as fn
import traces

import lenses
import stl.ast
from lenses import lens
from stl.ast import (AST, And, F, G, Interval, LinEq, NaryOpSTL,
                     Neg, Or, Param, ModalOp)
from stl.types import STL, STL_Generator

Lens = TypeVar('Lens')


def walk(phi: STL) -> STL_Generator:
    """Walk of the AST."""
    pop = deque.pop
    children = deque([phi])
    while len(children) > 0:
        node = pop(children)
        yield node
        children.extend(node.children)

def list_params(phi: STL):
    """Walk of the AST."""
    def get_params(leaf):
        if isinstance(leaf, ModalOp):
            if isinstance(leaf.interval[0], Param):
                yield leaf.interval[0]
            if isinstance(leaf.interval[1], Param):
                yield leaf.interval[1]
        elif isinstance(leaf, LinEq):
            if isinstance(leaf.const, Param):
                yield leaf.const
    return set(fn.mapcat(get_params, walk(phi)))


def vars_in_phi(phi):
    focus = stl.terms_lens(phi)
    return set(focus.tuple_(lens.id, lens.time).get_all())


def type_pred(*args: List[Type]) -> Mapping[Type, bool]:
    ast_types = set(args)
    return lambda x: type(x) in ast_types


def ast_lens(phi: STL, bind=True, *, pred=None, focus_lens=None,
             getter=False) -> Lens:
    if focus_lens is None:
        def focus_lens(_):
            return [lens]

    if pred is None:
        def pred(_):
            return False

    child_lenses = _ast_lens(phi, pred=pred, focus_lens=focus_lens)
    phi = lenses.bind(phi) if bind else lens
    return (phi.Tuple if getter else phi.Fork)(*child_lenses)


def _ast_lens(phi: STL, pred, focus_lens) -> Lens:
    if pred(phi):
        yield from focus_lens(phi)

    if phi is None or not phi.children:
        return

    if phi is stl.TOP or phi is stl.BOT:
        child_lenses = [lens]
    elif isinstance(phi, stl.ast.Until):
        child_lenses = [lens.GetAttr('arg1'), lens.GetAttr('arg2')]
    elif isinstance(phi, NaryOpSTL):
        child_lenses = [
            lens.GetAttr('args')[j] for j, _ in enumerate(phi.args)
        ]
    else:
        child_lenses = [lens.GetAttr('arg')]
    for l in child_lenses:
        yield from [l & cl for cl in _ast_lens(l.get()(phi), pred, focus_lens)]


lineq_lens = fn.partial(ast_lens, pred=type_pred(LinEq), getter=True)
AP_lens = fn.partial(ast_lens, pred=type_pred(stl.ast.AtomicPred), getter=True)
and_or_lens = fn.partial(ast_lens, pred=type_pred(And, Or), getter=True)


def terms_lens(phi: STL, bind: bool = True) -> Lens:
    return lineq_lens(phi, bind).Each().terms.Each()


def param_lens(phi: STL, *, getter=False) -> Lens:
    def focus_lens(leaf):
        candidates = [lens.const] if isinstance(leaf, LinEq) else [
            lens.GetAttr('interval')[0],
            lens.GetAttr('interval')[1]
        ]
        return (x for x in candidates if isinstance(x.get()(leaf), Param))

    return ast_lens(phi, pred=type_pred(LinEq, F, G), focus_lens=focus_lens, 
                    getter=getter)


def set_params(phi, val) -> STL:
    phi = param_lens(phi) if isinstance(phi, AST) else phi
    return phi.modify(lambda x: float(val.get(x, val.get(str(x), x))))


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
    return sum(map(abs, lens(lineq).Each().terms.Each().coeff.collect()))


def linear_stl_lipschitz(phi):
    """Infinity norm lipschitz bound of linear inequality predicate."""
    return float(max(map(_lineq_lipschitz, lineq_lens(phi).Each().collect())))


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


def eval_lineq(lineq, x, times=None, compact=True):
    if times is None:
        times = get_times(x)

    def eval_term(term, t):
        return float(term.coeff) * x[term.id.name][t]

    output = traces.TimeSeries(domain=traces.Domain(times[0], times[-1]))
    terms = lens(lineq).Each().terms.Each().collect()
    for t in times:
        lhs = sum(eval_term(term, t) for term in terms)
        output[t] = op_lookup[lineq.op](lhs, lineq.const)

    if compact:
        output.compact()
    return output


def eval_lineqs(phi, x, times=None):
    if times is None:
        times = get_times(x)
    lineqs = set(lineq_lens(phi).Each().collect())
    return {lineq: eval_lineq(lineq, x, times=times) for lineq in lineqs}


# EDSL


def alw(phi, *, lo, hi):
    return G(Interval(lo, hi), phi)


def env(phi, *, lo, hi):
    return F(Interval(lo, hi), phi)


def until(phi1, phi2, *, lo, hi):
    return stl.ast.Until(Interval(lo, hi), phi1, phi2)


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
