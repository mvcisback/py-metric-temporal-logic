# -*- coding: utf-8 -*-
import stl
from hypothesis import given, event

from stl.hypothesis import SignalTemporalLogicStrategy


@given(SignalTemporalLogicStrategy)
def test_invertable_repr(phi):
    event(str(phi))
    assert str(phi) == str(stl.parse(str(phi)))
