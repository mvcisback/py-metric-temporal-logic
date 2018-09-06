# -*- coding: utf-8 -*-
from hypothesis import event, given

import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy


@given(MetricTemporalLogicStrategy)
def test_invertable_repr(phi):
    event(str(phi))
    assert str(phi) == str(mtl.parse(str(phi)))


@given(MetricTemporalLogicStrategy)
def test_hash_inheritance(phi):
    assert hash(repr(phi)) == hash(phi)


def test_sugar_smoke():
    mtl.parse('(x <-> x)')
    mtl.parse('(x -> x)')
    mtl.parse('(x ^ x)')
