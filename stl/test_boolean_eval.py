import stl
import stl.boolean_eval
import stl.fastboolean_eval
import traces
import unittest
from sympy import Symbol

import hypothesis.strategies as st
from hypothesis import given, note, assume, example


"""
TODO: property based test that fasteval should be the same as slow
TODO: property based test that x |= phi == ~(x |= ~phi)
TODO: property based test that ~~phi == phi
TODO: property based test that ~~~phi == ~phi
TODO: property based test that ~phi => phi
TODO: property based test that phi => phi
TODO: property based test that phi <=> phi
TODO: property based test that phi & psi => phi
TODO: property based test that psi => phi | psi
TODO: property based test that (True U psi) => F(psi)
TODO: property based test that G(psi) = ~F(~psi)
TODO: Automatically generate input time series.
"""

x = {
    "A": traces.TimeSeries([(0, 1), (0.1, 1), (0.2, 4)]),
    "B": traces.TimeSeries([(0, 2), (0.1, 4), (0.2, 2)]),
    "C": traces.TimeSeries([(0, True), (0.1, True), (0.2, False)]),
    'D': traces.TimeSeries({0.0: 2, 13.8: 3, 19.7: 2}),
}


@given(st.just(stl.BOT))
def test_boolean_identities(phi):
    stl_eval = stl.boolean_eval.pointwise_sat(phi)
    stl_eval2 = stl.boolean_eval.pointwise_sat(~phi)
    assert stl_eval2(x, 0) == (not stl_eval(x, 0))
    stl_eval3 = stl.boolean_eval.pointwise_sat(~~phi)
    assert stl_eval3(x, 0) == stl_eval(x, 0)
    stl_eval4 = stl.boolean_eval.pointwise_sat(phi & phi)
    assert stl_eval4(x, 0) == stl_eval(x, 0)
    stl_eval5 = stl.boolean_eval.pointwise_sat(phi & ~phi)
    assert not stl_eval5(x, 0)
    stl_eval6 = stl.boolean_eval.pointwise_sat(phi | ~phi)
    assert stl_eval6(x, 0)


@given(st.just(stl.BOT))
def test_temporal_identities(phi):
    stl_eval = stl.fastboolean_eval.pointwise_sat(stl.alw(phi, lo=0, hi=4))
    stl_eval2 = stl.fastboolean_eval.pointwise_sat(~stl.env(~phi, lo=0, hi=4))
    assert stl_eval2(x, 0) == stl_eval(x, 0)

    stl_eval3 = stl.fastboolean_eval.pointwise_sat(~stl.alw(~phi, lo=0, hi=4))
    stl_eval4 = stl.fastboolean_eval.pointwise_sat(stl.env(phi, lo=0, hi=4))
    assert stl_eval4(x, 0) == stl_eval3(x, 0)

