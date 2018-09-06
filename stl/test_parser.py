# -*- coding: utf-8 -*-
from hypothesis import event, given

import stl
from stl.hypothesis import SignalTemporalLogicStrategy


@given(SignalTemporalLogicStrategy)
def test_invertable_repr(phi):
    event(str(phi))
    assert str(phi) == str(stl.parse(str(phi)))


@given(SignalTemporalLogicStrategy)
def test_hash_inheritance(phi):
    assert hash(repr(phi)) == hash(phi)


def test_sugar_smoke():
    stl.parse('(x <-> x)')
    stl.parse('(x -> x)')
    stl.parse('(x ^ x)')
