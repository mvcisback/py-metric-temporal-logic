from typing import List, Type, Dict, Mapping, T
from collections import deque
import operator as op
from functools import reduce

from lenses import lens, Lens
import funcy as fn
import sympy

import stl.ast
from stl.ast import (LinEq, And, Or, NaryOpSTL, F, G, Interval, Neg,
                     AtomicPred)
from stl.types import STL, STL_Generator, MTL

def walk(phi:STL) -> STL_Generator:
    """DSF walk of the AST."""
    pop = deque.pop
    children = deque([phi])
    while len(children) > 0:
        node = pop(children)
        yield node
        children.extend(node.children())


def type_pred(*args:List[Type]) -> Mapping[Type, bool]:
    ast_types = set(args)
    return lambda x: type(x) in ast_types


def _child_lens(psi:STL, focus:Lens) -> STL_Generator:
    if psi is None:
        return
    if isinstance(psi, NaryOpSTL):
        for j, _ in enumerate(psi.args):
            yield focus.args[j]
    else:
        yield focus.arg


def ast_lens(phi:STL, bind:bool=True, *,
             pred:Mapping[T, bool], focus_lens:Lens=None) -> Lens:
    if focus_lens is None:
        focus_lens = lambda x: [lens()]
    tls = list(fn.flatten(_ast_lens(phi, pred=pred, focus_lens=focus_lens)))
    tl = lens().tuple_(*tls).each_()
    return tl.bind(phi) if bind else tl


def _ast_lens(phi, *, pred, focus=lens(), focus_lens):
    psi = focus.get(state=phi)
    ret_lens = [focus.add_lens(l) for l in focus_lens(psi)] if pred(psi) else []

    if isinstance(psi, (LinEq, stl.ast.AtomicPred)):
        return ret_lens

    child_lenses = list(_child_lens(psi, focus=focus))
    ret_lens += [_ast_lens(phi, pred=pred, focus=cl, focus_lens=focus_lens) 
                 for cl in child_lenses]
    return ret_lens


lineq_lens = fn.partial(ast_lens, pred=type_pred(LinEq))
AP_lens = fn.partial(ast_lens, pred=type_pred(stl.ast.AtomicPred))
and_or_lens = fn.partial(ast_lens, pred=type_pred(And, Or))

def terms_lens(phi:STL, bind:bool=True) -> Lens:
    return lineq_lens(phi, bind).terms.each_()


def param_lens(phi:STL) -> Lens:
    is_sym = lambda x: isinstance(x, sympy.Symbol)
    def focus_lens(leaf):
        return [lens().const] if isinstance(leaf, LinEq) else [lens().interval[0], lens().interval[1]]

    return ast_lens(phi, pred=type_pred(LinEq, F, G), 
                    focus_lens=focus_lens).filter_(is_sym)


def set_params(stl_or_lens, val) -> STL:
    l = stl_or_lens if isinstance(stl_or_lens, Lens) else param_lens(stl_or_lens)
    return l.modify(lambda x: val.get(x, val.get(str(x), x)))


def f_neg_or_canonical_form(phi:STL) -> STL:
    if isinstance(phi, LinEq):
        return phi

    children = [f_neg_or_canonical_form(s) for s in phi.children()]
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


def get_polarity(phi, traces=None):
    raise NotImplementedError

def canonical_polarity(phi, traces=None):
    raise NotImplementedError


# EDSL

def alw(phi, *, lo, hi):
    return G(Interval(lo, hi), phi)

def env(phi, *, lo, hi):
    return F(Interval(lo, hi), phi)

def until(phi1, phi2, *, lo, hi):
    return stl.ast.Until(Interval(lo, hi), phi1, phi2)

def andf(*args):
    return reduce(op.and_, args, stl.And(tuple()))

def orf(*args):
    return reduce(op.or_, args, stl.Or(tuple()))

def implies(x, y):
    return ~x | y

def xor(x, y):
    return (x | y) & ~(x & y)

def iff(x, y):
    return (x & y) | (~x & ~y)
