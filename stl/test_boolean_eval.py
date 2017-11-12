import hypothesis.strategies as st
import traces

from hypothesis import given  # , settings, Verbosity, Phase

import stl
import stl.boolean_eval
import stl.fastboolean_eval
# from stl.hypothesis import SignalTemporalLogicStrategy

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
    "x": traces.TimeSeries([(0, 1), (0.1, 1), (0.2, 4)]),
    "y": traces.TimeSeries([(0, 2), (0.1, 4), (0.2, 2)]),
    "AP1": traces.TimeSeries([(0, True), (0.1, True), (0.2, False)]),
    "AP2": traces.TimeSeries([(0, False), (0.2, True), (0.5, False)]),
    "AP3": traces.TimeSeries([(0, True), (0.1, True), (0.3, False)]),
    "AP4": traces.TimeSeries([(0, False), (0.1, False), (0.3, False)]),
    "AP5": traces.TimeSeries([(0, False), (0.1, False), (0.1, True)]),
}


@given(st.just(stl.ast.Next(stl.BOT) | stl.ast.Next(stl.TOP)))
# @given(SignalTemporalLogicStrategy)
# @settings(max_shrinks=0, verbosity=Verbosity.verbose,
#           perform_health_check=False,
#           phases=[Phase.generate])
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

    # phi2 = stl.alw(stl.ast.Next(phi))
    # phi3 = stl.ast.Next(stl.alw(phi))
    # stl_eval7 = stl.boolean_eval.pointwise_sat(phi2)
    # stl_eval8 = stl.boolean_eval.pointwise_sat(phi3)
    # assert stl_eval7(x, 0) == stl_eval8(x, 0)

    stl_eval9 = stl.boolean_eval.pointwise_sat(stl.ast.Next(phi))
    stl_eval10 = stl.boolean_eval.pointwise_sat(~stl.ast.Next(phi))
    assert stl_eval9(x, 0) != stl_eval10(x, 0)

    phi4 = stl.parse('~(AP4)')
    stl_eval11 = stl.boolean_eval.pointwise_sat(phi4)
    assert stl_eval11(x, 0)

    phi5 = stl.parse('G[0.1, 0.03](~(AP4))')
    stl_eval12 = stl.boolean_eval.pointwise_sat(phi5)
    assert stl_eval12(x, 0)


@given(st.just(stl.BOT))
def test_temporal_identities(phi):
    stl_eval = stl.fastboolean_eval.pointwise_sat(stl.alw(phi, lo=0, hi=4))
    stl_eval2 = stl.fastboolean_eval.pointwise_sat(~stl.env(~phi, lo=0, hi=4))
    assert stl_eval2(x, 0) == stl_eval(x, 0)

    stl_eval3 = stl.fastboolean_eval.pointwise_sat(~stl.alw(~phi, lo=0, hi=4))
    stl_eval4 = stl.fastboolean_eval.pointwise_sat(stl.env(phi, lo=0, hi=4))
    assert stl_eval4(x, 0) == stl_eval3(x, 0)
