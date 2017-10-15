from typing import List, Type, Dict, Mapping, T, TypeVar
from collections import deque
import operator as op
from functools import reduce

import lenses
from lenses import lens
import funcy as fn
import sympy
import traces

import stl.ast
from stl.ast import (LinEq, And, Or, NaryOpSTL, F, G, Interval, Neg,
                     AtomicPred)
from stl.types import STL, STL_Generator, MTL

Lens = TypeVar('Lens')

def walk(phi:STL) -> STL_Generator:
    """Walk of the AST."""
    pop = deque.pop
    children = deque([phi])
    while len(children) > 0:
        node = pop(children)
        yield node
        children.extend(node.children)

def vars_in_phi(phi):
    focus = stl.terms_lens(phi)
    return set(focus.tuple_(lens.id, lens.time).get_all())

def type_pred(*args:List[Type]) -> Mapping[Type, bool]:
    ast_types = set(args)
    return lambda x: type(x) in ast_types


def ast_lens(phi:STL, bind=True, *, pred=None, focus_lens=None) -> Lens:
    if focus_lens is None:
        focus_lens = lambda _: [lens]
    if pred is None:
        pred = lambda _: False
    l = lenses.bind(phi) if bind else lens
    return l.Tuple(*_ast_lens(phi, pred=pred, focus_lens=focus_lens))

def _ast_lens(phi:STL, pred, focus_lens) -> Lens:
    if pred(phi):
        yield from focus_lens(phi)
    
    if phi is None or not phi.children:
        return

    if phi is stl.TOP or phi is stl.BOT:
        child_lenses = [lens]
    elif isinstance(phi, stl.ast.Until):
        child_lenses = [lens.GetAttr('arg1'), lens.GetAttr('arg2')]
    elif isinstance(phi, NaryOpSTL):
        child_lenses = [lens.GetAttr('args')[j] for j, _ in enumerate(phi.args)]
    else:
        child_lenses = [lens.GetAttr('arg')]
    for l in child_lenses:
        yield from [l & cl for cl in _ast_lens(l.get()(phi), pred, focus_lens)]
    

lineq_lens = fn.partial(ast_lens, pred=type_pred(LinEq))
AP_lens = fn.partial(ast_lens, pred=type_pred(stl.ast.AtomicPred))
and_or_lens = fn.partial(ast_lens, pred=type_pred(And, Or))

def terms_lens(phi:STL, bind:bool=True) -> Lens:
    return lineq_lens(phi, bind).terms.each_()


def param_lens(phi:STL) -> Lens:
    is_sym = lambda x: isinstance(x, sympy.Symbol)
    def focus_lens(leaf):
        return [lens.const] if isinstance(leaf, LinEq) else [lens().interval[0], lens().interval[1]]

    return ast_lens(phi, pred=type_pred(LinEq, F, G), 
                    focus_lens=focus_lens).filter_(is_sym)


def set_params(stl_or_lens, val) -> STL:
    l = stl_or_lens if isinstance(stl_or_lens, Lens) else param_lens(stl_or_lens)
    return l.modify(lambda x: float(val.get(x, val.get(str(x), x))))


def f_neg_or_canonical_form(phi:STL) -> STL:
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


def to_mtl(phi:STL) -> MTL:
    focus = lineq_lens(phi)
    to_ap = lambda i: stl.ast.AtomicPred("AP{}".format(i))
    ap_map = {to_ap(i): leq for i, leq in enumerate(focus.get_all())}
    lineq_map = {v:k for k,v in ap_map.items()}
    return focus.modify(lineq_map.get), ap_map


def from_mtl(phi:MTL, ap_map:Dict[AtomicPred, LinEq]) -> STL:
    focus = AP_lens(phi)
    return focus.modify(ap_map.get)

def _lineq_lipschitz(lineq):
    return sum(map(abs, lens(lineq).terms.each_().coeff.get_all()))

def linear_stl_lipschitz(phi):
    """Infinity norm lipschitz bound of linear inequality predicate."""
    return float(max(map(_lineq_lipschitz, lineq_lens(phi).get_all())))

def inline_context(phi, context):
    phi2 = None
    update = lambda ap: context.get(ap, ap)
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
        return float(term.coeff)*x[term.id.name][t]

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
