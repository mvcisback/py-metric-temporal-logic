# -*- coding: utf-8 -*-
from hypothesis import given

import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy


@given(MetricTemporalLogicStrategy)
def test_stablizing_repr(phi):
    for _ in range(10):
        phi, phi2 = mtl.parse(str(phi)), phi

    assert phi == phi2


def test_sugar_smoke():
    mtl.parse('(x <-> x)')
    mtl.parse('(x -> x)')
    mtl.parse('(x ^ x)')
