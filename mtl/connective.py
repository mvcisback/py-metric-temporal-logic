import operator
from functools import reduce
from typing import Callable, Iterable

import attr
from discrete_signals import signal

from mtl import ast

OO = float('inf')


@attr.s(frozen=True, auto_attribs=True, repr=False, slots=True)
class _ConnectivesDef:
    name: str
    negation: Callable[[float], float]
    tnorm: Callable[[Iterable[float]], float]
    tconorm: Callable[[Iterable[float]], float]
    implication: Callable[[float, float], float]
    const_false: float
    const_true: float

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<ConnectivesDef {}>".format(self.name)

    @property
    def BOT(self):
        return signal([(0, self.const_false)], start=-OO, end=OO, tag=ast.BOT)

    @property
    def TOP(self):
        return signal([(0, self.const_true)], start=-OO, end=OO, tag=ast.TOP)


DEFAULT_FALSE = -OO
DEFAULT_TRUE = OO


default = _ConnectivesDef(
    name="default",
    negation=lambda v: -v,
    tnorm=min,
    tconorm=max,
    implication=lambda a, b: max(-a, b),
    const_false=DEFAULT_FALSE,
    const_true=DEFAULT_TRUE,
)


FUZZY_FALSE = 0.0
FUZZY_TRUE = 1.0


zadeh = _ConnectivesDef(
    name="zadeh",
    negation=lambda v: 1. - v,
    tnorm=min,
    tconorm=max,
    implication=lambda a, b: max(1. - a, b),
    const_false=FUZZY_FALSE,
    const_true=FUZZY_TRUE,
)


godel = _ConnectivesDef(
    name="godel",
    negation=lambda v: 0. if v > 0. else 1.,
    tnorm=min,
    tconorm=max,
    implication=lambda a, b: 1. if a <= b else b,
    const_false=FUZZY_FALSE,
    const_true=FUZZY_TRUE,
)


lukasiewicz = _ConnectivesDef(
    name="lukasiewicz",
    negation=lambda v: 1. - v,
    tnorm=lambda v: reduce(lambda a, b: max(a + b - 1., 0.), v, 1.),
    tconorm=lambda v: reduce(lambda a, b: min(a + b, 1.), v, 0.),
    implication=lambda a, b: min(1. - a + b, 1.),
    const_false=FUZZY_FALSE,
    const_true=FUZZY_TRUE,
)


product = _ConnectivesDef(
    name="product",
    negation=lambda v: 0. if v > 0. else 1.,
    tnorm=lambda v: reduce(operator.mul, v, 1.),
    tconorm=lambda v: reduce(lambda a, b: (a + b) - (a * b), v, 0.),
    implication=lambda a, b: 1. if a <= b else b / a,
    const_false=FUZZY_FALSE,
    const_true=FUZZY_TRUE,
)
