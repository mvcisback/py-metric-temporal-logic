import hypothesis.strategies as st
import traces
from hypothesis import given
from pytest import raises

import mtl
import mtl.boolean_eval
import mtl.fastboolean_eval
from mtl.hypothesis import MetricTemporalLogicStrategy
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
    "ap1": traces.TimeSeries([(0, True), (0.1, True), (0.2, False)]),
    "ap2":
    traces.TimeSeries([(0, False), (0.2, True), (0.5, False)]),
    "ap3":
    traces.TimeSeries([(0, True), (0.1, True), (0.3, False)]),
    "ap4":
    traces.TimeSeries([(0, False), (0.1, False), (0.3, False)]),
    "ap5":
    traces.TimeSeries([(0, False), (0.1, False), (0.3, True)]),
    "ap6":
    traces.TimeSeries([(0, True), (float('inf'), True)]),
}


@given(st.just(mtl.ast.Next(mtl.BOT) | mtl.ast.Next(mtl.TOP)))
def test_eval_smoke_tests(phi):
    mtl_eval9 = mtl.boolean_eval.pointwise_sat(mtl.ast.Next(phi))
    mtl_eval10 = mtl.boolean_eval.pointwise_sat(~mtl.ast.Next(phi))
    assert mtl_eval9(x, 0) != mtl_eval10(x, 0)

    phi4 = mtl.parse('~ap4')
    mtl_eval11 = mtl.boolean_eval.pointwise_sat(phi4)
    assert mtl_eval11(x, 0)

    phi5 = mtl.parse('G[0.1, 0.03] ~ap4')
    mtl_eval12 = mtl.boolean_eval.pointwise_sat(phi5)
    assert mtl_eval12(x, 0)

    phi6 = mtl.parse('G[0.1, 0.03] ~ap5')
    mtl_eval13 = mtl.boolean_eval.pointwise_sat(phi6)
    assert mtl_eval13(x, 0)
    assert mtl_eval13(x, 0.4)

    phi7 = mtl.parse('G ~ap4')
    mtl_eval14 = mtl.boolean_eval.pointwise_sat(phi7)
    assert mtl_eval14(x, 0)

    phi8 = mtl.parse('F ap5')
    mtl_eval15 = mtl.boolean_eval.pointwise_sat(phi8)
    assert mtl_eval15(x, 0)

    phi9 = mtl.parse('(ap1 U ap2)')
    mtl_eval16 = mtl.boolean_eval.pointwise_sat(phi9)
    assert mtl_eval16(x, 0)

    phi10 = mtl.parse('(ap2 U ap2)')
    mtl_eval17 = mtl.boolean_eval.pointwise_sat(phi10)
    assert not mtl_eval17(x, 0)

    with raises(NotImplementedError):
        mtl.boolean_eval.eval_mtl(None, None)


@given(MetricTemporalLogicStrategy)
def test_temporal_identities(phi):
    mtl_eval = mtl.boolean_eval.pointwise_sat(phi)
    mtl_eval2 = mtl.boolean_eval.pointwise_sat(~phi)
    assert mtl_eval2(x, 0) == (not mtl_eval(x, 0))
    mtl_eval3 = mtl.boolean_eval.pointwise_sat(~~phi)
    assert mtl_eval3(x, 0) == mtl_eval(x, 0)
    mtl_eval4 = mtl.boolean_eval.pointwise_sat(phi & phi)
    assert mtl_eval4(x, 0) == mtl_eval(x, 0)
    mtl_eval5 = mtl.boolean_eval.pointwise_sat(phi & ~phi)
    assert not mtl_eval5(x, 0)
    mtl_eval6 = mtl.boolean_eval.pointwise_sat(phi | ~phi)
    assert mtl_eval6(x, 0)
    mtl_eval7 = mtl.boolean_eval.pointwise_sat(mtl.ast.Until(mtl.TOP, phi))
    mtl_eval8 = mtl.boolean_eval.pointwise_sat(mtl.env(phi))
    assert mtl_eval7(x, 0) == mtl_eval8(x, 0)


@given(st.just(mtl.BOT))
def test_fastboolean_equiv(phi):
    mtl_eval = mtl.fastboolean_eval.pointwise_sat(mtl.alw(phi, lo=0, hi=4))
    mtl_eval2 = mtl.fastboolean_eval.pointwise_sat(~mtl.env(~phi, lo=0, hi=4))
    assert mtl_eval2(x, 0) == mtl_eval(x, 0)

    mtl_eval3 = mtl.fastboolean_eval.pointwise_sat(~mtl.alw(~phi, lo=0, hi=4))
    mtl_eval4 = mtl.fastboolean_eval.pointwise_sat(mtl.env(phi, lo=0, hi=4))
    assert mtl_eval4(x, 0) == mtl_eval3(x, 0)


def test_fastboolean_smoketest():
    phi = mtl.parse(
        '(((G[0, 4] ap6 & F[2, 1] ap1) | ap2) & G[0,0](ap2))')
    mtl_eval = mtl.fastboolean_eval.pointwise_sat(phi)
    assert not mtl_eval(x, 0)

    with raises(NotImplementedError):
        mtl.fastboolean_eval.pointwise_sat(None)


def test_callable_interface():
    phi = mtl.parse(
        '(((G[0, 4] ap6 & F[2, 1] ap1) | ap2) & G[0,0](ap2))')
    assert not phi(x, 0)
