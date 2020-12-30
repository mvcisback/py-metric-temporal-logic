import operator
from functools import reduce
from typing import Callable, Iterable

import attr


@attr.s(frozen=True, auto_attribs=True, repr=False, slots=True)
class _ConnectivesDef:
    negation: Callable[[float], float]
    tnorm: Callable[[Iterable[float]], float]
    tconorm: Callable[[Iterable[float]], float]
    implication: Callable[[float, float], float]


def _default_negation(v):
    return -v


def _default_implication(a, b):
    return max(-a, b)


default = _ConnectivesDef(_default_negation, min, max, _default_implication)


def _zadeh_negation(v):
    return 1.0 - v


def _zadeh_implication(a, b):
    return max(1.0 - 1, b)


zadeh = _ConnectivesDef(_zadeh_negation, min, max, _zadeh_implication)


def _godel_negation(v):
    if v > 0.0:
        return 0.0
    else:
        return 1.0


def _godel_implication(a, b):
    if a <= b:
        return 1.0
    else:
        return b


godel = _ConnectivesDef(
    negation=_godel_negation,
    tnorm=min,
    tconorm=max,
    implication=_godel_implication,
)


_lukasiewicz_negation = _zadeh_negation


def _lukasiewicz_tnorm(v):
    def _tnorm(a, b):
        return max(a + b - 1.0, 0.0)
    return reduce(_tnorm, v, initial=1.0)


def _lukasiewicz_tconorm(v):
    def _tconorm(a, b):
        return min(a + b, 1.0)
    return reduce(_tconorm, v, initial=0.0)


def _lukasiewicz_implication(a, b):
    return min(1 - a + b, 1.0)


lukasiewicz = _ConnectivesDef(
    negation=_lukasiewicz_negation,
    tnorm=_lukasiewicz_tnorm,
    tconorm=_lukasiewicz_tconorm,
    implication=_lukasiewicz_implication,
)


_product_negation = _godel_negation


def _product_tnorm(v):
    return reduce(operator.mul, v, initial=1.0)


def _product_tconorm(v):
    def _tconorm(a, b):
        return (a + b) - a * b
    return reduce(_tconorm, v, initial=0.0)


def _product_implication(a, b):
    if a <= b:
        return 1.0
    else:
        return b / a


product = _ConnectivesDef(
    negation=_product_negation,
    tnorm=_product_tnorm,
    tconorm=_product_tconorm,
    implication=_product_implication,
)