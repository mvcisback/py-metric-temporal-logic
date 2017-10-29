# -*- coding: utf-8 -*-
from hypothesis import event, given

import stl
from stl.hypothesis import SignalTemporalLogicStrategy


@given(SignalTemporalLogicStrategy)
def test_invertable_repr(phi):
    event(str(phi))
    assert str(phi) == str(stl.parse(str(phi)))
