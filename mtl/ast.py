# -*- coding: utf-8 -*-
from collections import deque
from typing import Union, NamedTuple, TypeVar

import attr
import funcy as fn
from lenses import bind

from mtl import sugar


Node = TypeVar("Node")


def flatten_binary(phi, op, dropT, shortT):
    def f(x):
        return x.args if isinstance(x, op) else [x]

    args = [arg for arg in phi.args if arg != dropT]

    if any(arg is shortT for arg in args):
        return shortT
    elif not args:
        return dropT
    elif len(args) == 1:
        return args[0]
    else:
        return op(tuple(fn.mapcat(f, phi.args)))


def _or(exp1, exp2):
    return ~(~exp1 & ~exp2)


def _and(exp1, exp2):
    return flatten_binary(And((exp1, exp2)), And, TOP, BOT)


def _neg(exp):
    if isinstance(exp, Neg):
        return exp.arg
    return Neg(exp)


def _eval(exp, trace, time=False, *, dt=0.1, quantitative=True):
    from mtl import evaluator
    return evaluator.pointwise_sat(exp, dt)(trace, time, quantitative)


def _timeshift(exp, t):
    if exp == BOT:
        return exp

    for _ in range(t):
        exp = Next(exp)
    return exp


def _walk(exp):
    """Walk of the AST."""
    pop = deque.pop
    children = deque([exp])
    while len(children) > 0:
        node = pop(children)
        yield node
        children.extend(node.children)


def _params(exp):
    def get_params(leaf):
        if isinstance(leaf, ModalOp):
            if isinstance(leaf.interval[0], Param):
                yield leaf.interval[0]
            if isinstance(leaf.interval[1], Param):
                yield leaf.interval[1]

    return set(fn.mapcat(get_params, exp.walk()))


def _set_symbols(node, val):
    children = tuple(_set_symbols(c, val) for c in node.children)

    if hasattr(node, 'interval'):
        return node.evolve(
            arg=children[0],
            interval=_update_itvl(node.interval, val),
        )
    elif isinstance(node, AtomicPred):
        return val.get(node.id, node)
    elif hasattr(node, 'args'):
        return node.evolve(args=children)
    elif hasattr(node, 'arg'):
        return node.evolve(arg=children[0])
    return node


def _inline_context(exp, context):
    phi, phi2 = exp, None
    while phi2 != phi:
        phi2, phi = phi, _set_symbols(phi, context)

    return phi


def _atomic_predicates(exp):
    return set(bind(exp).Recur(AtomicPred).collect())


class Param(NamedTuple):
    name: str

    def __repr__(self):
        return self.name


def ast_class(cls):
    cls.__xor__ = sugar.xor
    cls.__or__ = _or
    cls.__and__ = _and
    cls.__invert__ = _neg
    cls.__call__ = _eval
    cls.__rshift__ = _timeshift
    cls.__getitem__ = _inline_context
    cls.walk = _walk
    cls.params = property(_params)
    cls.atomic_predicates = property(_atomic_predicates)
    cls.evolve = attr.evolve
    cls.iff = sugar.iff
    cls.implies = sugar.implies
    # Avoid circular dependence.
    cls.weak_until = lambda a, b: WeakUntil(a, b)
    cls.until = sugar.until
    cls.timed_until = sugar.timed_until
    cls.always = sugar.alw
    cls.eventually = sugar.env

    if not hasattr(cls, "children"):
        cls.children = property(lambda _: ())

    return attr.s(frozen=True, auto_attribs=True, repr=False, slots=True)(cls)


def _update_itvl(itvl, lookup):
    def _update_param(p):
        if not isinstance(p, Param) or p.name not in lookup:
            return p

        val = lookup[p.name]
        return val if isinstance(lookup, Param) else float(val)

    return Interval(*map(_update_param, itvl))


@ast_class
class _Bot:
    def __repr__(self):
        return "FALSE"


@ast_class
class AtomicPred:
    id: str

    def __repr__(self):
        return f"{self.id}"


class Interval(NamedTuple):
    lower: Union[float, Param]
    upper: Union[float, Param]

    def __repr__(self):
        return f"[{self.lower},{self.upper}]"


@ast_class
class NaryOpMTL:
    OP = "?"
    args: Node  # TODO: when 3.7 is more common replace with type union.

    def __repr__(self):
        return "(" + f" {self.OP} ".join(f"{x}" for x in self.args) + ")"

    @property
    def children(self):
        return tuple(self.args)


class And(NaryOpMTL):
    OP = "&"


@ast_class
class ModalOp:
    OP = '?'
    interval: Interval
    arg: Node

    def __repr__(self):
        if self.interval.lower == 0 and self.interval.upper == float('inf'):
            return f"{self.OP}{self.arg}"
        return f"{self.OP}{self.interval}{self.arg}"

    @property
    def children(self):
        return (self.arg,)


class G(ModalOp):
    OP = "G"


@ast_class
class WeakUntil:
    arg1: Node
    arg2: Node

    def __repr__(self):
        return f"({self.arg1} W {self.arg2})"

    @property
    def children(self):
        return (self.arg1, self.arg2)


@ast_class
class Neg:
    arg: Node

    def __repr__(self):
        return f"~{self.arg}"

    @property
    def children(self):
        return (self.arg,)


@ast_class
class Next:
    arg: Node

    def __repr__(self):
        return f"X{self.arg}"

    @property
    def children(self):
        return (self.arg,)


def type_pred(*args):
    ast_types = set(args)
    return lambda x: type(x) in ast_types


BOT = _Bot()
TOP = ~BOT
