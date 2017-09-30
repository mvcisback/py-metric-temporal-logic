# -*- coding: utf-8 -*-
import stl
from hypothesis import given, event

from stl.hypothesis import SignalTemporalLogicStategy


@given(SignalTemporalLogicStategy(max_length=25))
def test_invertable_repr(phi):
    event(str(phi))
    assert str(phi) == str(stl.parse(str(phi)))


