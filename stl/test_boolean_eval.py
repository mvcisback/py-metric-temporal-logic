import hypothesis.strategies as st
import traces
from hypothesis import given
from pytest import raises

import stl
import stl.boolean_eval
import stl.fastboolean_eval
from stl.hypothesis import SignalTemporalLogicStrategy
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
    "x":
    traces.TimeSeries([(0, 1), (0.1, 1), (0.2, 4)], domain=(0, 10)),
    "y":
    traces.TimeSeries([(0, 2), (0.1, 4), (0.2, 2)], domain=(0, 10)),
    "AP1":
    traces.TimeSeries([(0, True), (0.1, True), (0.2, False)], domain=(0, 10)),
    "AP2":
    traces.TimeSeries([(0, False), (0.2, True), (0.5, False)], domain=(0, 10)),
    "AP3":
    traces.TimeSeries([(0, True), (0.1, True), (0.3, False)], domain=(0, 10)),
    "AP4":
    traces.TimeSeries(
        [(0, False), (0.1, False), (0.3, False)], domain=(0, 10)),
    "AP5":
    traces.TimeSeries([(0, False), (0.1, False), (0.3, True)], domain=(0, 10)),
}


@given(st.just(stl.ast.Next(stl.BOT) | stl.ast.Next(stl.TOP)))
def test_eval_smoke_tests(phi):
    stl_eval9 = stl.boolean_eval.pointwise_sat(stl.ast.Next(phi))
    stl_eval10 = stl.boolean_eval.pointwise_sat(~stl.ast.Next(phi))
    assert stl_eval9(x, 0) != stl_eval10(x, 0)

    phi4 = stl.parse('~(AP4)')
    stl_eval11 = stl.boolean_eval.pointwise_sat(phi4)
    assert stl_eval11(x, 0)

    phi5 = stl.parse('G[0.1, 0.03](~(AP4))')
    stl_eval12 = stl.boolean_eval.pointwise_sat(phi5)
    assert stl_eval12(x, 0)

    phi6 = stl.parse('G[0.1, 0.03](~(AP5))')
    stl_eval13 = stl.boolean_eval.pointwise_sat(phi6)
    assert stl_eval13(x, 0)
    assert not stl_eval13(x, 0.4)

    phi7 = stl.parse('G(~(AP4))')
    stl_eval14 = stl.boolean_eval.pointwise_sat(phi7)
    assert stl_eval14(x, 0)

    phi8 = stl.parse('F(AP5)')
    stl_eval15 = stl.boolean_eval.pointwise_sat(phi8)
    assert stl_eval15(x, 0)

    phi9 = stl.parse('(AP1) U (AP2)')
    stl_eval16 = stl.boolean_eval.pointwise_sat(phi9)
    assert stl_eval16(x, 0)

    phi10 = stl.parse('(AP2) U (AP2)')
    stl_eval17 = stl.boolean_eval.pointwise_sat(phi10)
    assert not stl_eval17(x, 0)

    with raises(NotImplementedError):
        stl.boolean_eval.eval_stl(None, None)


@given(SignalTemporalLogicStrategy)
def test_temporal_identities(phi):
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
    stl_eval7 = stl.boolean_eval.pointwise_sat(stl.ast.Until(stl.TOP, phi))
    stl_eval8 = stl.boolean_eval.pointwise_sat(stl.env(phi))
    assert stl_eval7(x, 0) == stl_eval8(x, 0)


@given(st.just(stl.BOT))
def test_fastboolean_equiv(phi):
    stl_eval = stl.fastboolean_eval.pointwise_sat(stl.alw(phi, lo=0, hi=4))
    stl_eval2 = stl.fastboolean_eval.pointwise_sat(~stl.env(~phi, lo=0, hi=4))
    assert stl_eval2(x, 0) == stl_eval(x, 0)

    stl_eval3 = stl.fastboolean_eval.pointwise_sat(~stl.alw(~phi, lo=0, hi=4))
    stl_eval4 = stl.fastboolean_eval.pointwise_sat(stl.env(phi, lo=0, hi=4))
    assert stl_eval4(x, 0) == stl_eval3(x, 0)


def test_fastboolean_smoketest():
    phi = stl.parse(
        '(G[0, 4](x > 0)) & ((F[2, 1](AP1)) | (AP2)) & (G[0,0](AP2))')
    stl_eval = stl.fastboolean_eval.pointwise_sat(phi)
    assert not stl_eval(x, 0)

    with raises(NotImplementedError):
        stl.fastboolean_eval.pointwise_sat(stl.ast.AST())


def test_callable_interface():
    phi = stl.parse(
        '(G[0, 4](x > 0)) & ((F[2, 1](AP1)) | (AP2)) & (G[0,0](AP2))')
    assert not phi(x, 0)


def test_implicit_validity_domain_rigid():
    phi = stl.parse('(G[0, a?](x > b?)) & ((F(AP1)) | (AP2))')
    vals = {'a?': 3, 'b?': 20}
    stl_eval = stl.pointwise_sat(phi.set_params(vals))
    oracle, order = stl.utils.implicit_validity_domain(phi, x)
    assert stl_eval(x, 0) == oracle([vals.get(k) for k in order])
