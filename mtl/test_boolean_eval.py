import hypothesis.strategies as st
import traces
from hypothesis import given
from pytest import raises

import mtl
import mtl.boolean_eval
from mtl.hypothesis import MetricTemporalLogicStrategy, APTraceStrategy
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
    "ap1": traces.TimeSeries([(0, 1), (0.1, 1), (0.2, -1)]),
    "ap2":
    traces.TimeSeries([(0, -1), (0.2, 1), (0.5, -1)]),
    "ap3":
    traces.TimeSeries([(0, 1), (0.1, 1), (0.3, -1)]),
    "ap4":
    traces.TimeSeries([(0, -1), (0.1, -1), (0.3, -1)]),
    "ap5":
    traces.TimeSeries([(0, -1), (0.1, -1), (0.3, 1)]),
    "ap6":
    traces.TimeSeries([(0, 1), (float('inf'), 1)]),
}


def test_apply_weak_since():
    y1 = traces.TimeSeries([(0, -1), (1, 1), (4, -1), (5, 1)])
    y2 = traces.TimeSeries([(0, -1), (2, 1), (3, -1), (6, 1)])
    y3 = traces.TimeSeries(mtl.boolean_eval.apply_weak_since(y1, y2))
    y4 = traces.TimeSeries([(0, 1), (2, 1), (4, -1), (6, 1)])

    y3.compact()
    y4.compact()
    assert y3 == y4



@given(MetricTemporalLogicStrategy)
def test_eval_smoke_tests(phi):
    mtl_eval9 = mtl.boolean_eval.pointwise_sat(phi << 1)
    mtl_eval10 = mtl.boolean_eval.pointwise_sat(~(phi << 1))
    assert mtl_eval9(x) != mtl_eval10(x)

    phi4 = mtl.parse('~ap4')
    mtl_eval11 = mtl.boolean_eval.pointwise_sat(phi4)
    assert mtl_eval11(x) == 1

    phi5 = mtl.parse('H[0.1, 0.03] ~ap4')
    mtl_eval12 = mtl.boolean_eval.pointwise_sat(phi5)
    assert mtl_eval12(x) == 1

    phi6 = mtl.parse('H[0.1, 0.03] ~ap5')
    mtl_eval13 = mtl.boolean_eval.pointwise_sat(phi6)
    assert mtl_eval13(x) == 1
    assert mtl_eval13(x, 0.4) == 1

    phi7 = mtl.parse('H ~ap4')
    mtl_eval14 = mtl.boolean_eval.pointwise_sat(phi7)
    assert mtl_eval14(x) == 1

    phi8 = mtl.parse('P ap5')
    mtl_eval15 = mtl.boolean_eval.pointwise_sat(phi8)
    assert mtl_eval15(x) == 1

    phi9 = mtl.parse('(ap1 M ap2)')
    mtl_eval16 = mtl.boolean_eval.pointwise_sat(phi9)
    assert mtl_eval16(x) == -1

    phi10 = mtl.parse('(ap6 M ap5)')
    mtl_eval17 = mtl.boolean_eval.pointwise_sat(phi10)
    assert mtl_eval17(x) == 1

    with raises(NotImplementedError):
        mtl.boolean_eval.eval_mtl(None, None)


@given(MetricTemporalLogicStrategy, APTraceStrategy)
def test_temporal_identities(phi, x):
    mtl_eval = mtl.boolean_eval.pointwise_sat(phi)
    mtl_eval2 = mtl.boolean_eval.pointwise_sat(~phi)
    assert mtl_eval2(x) == -mtl_eval(x)


    mtl_eval3 = mtl.boolean_eval.pointwise_sat(~~phi)
    assert mtl_eval3(x) == mtl_eval(x)

    mtl_eval4 = mtl.boolean_eval.pointwise_sat(phi & phi)
    assert mtl_eval4(x) == mtl_eval(x)
    mtl_eval5 = mtl.boolean_eval.pointwise_sat(phi & ~phi)
    assert mtl_eval5(x) == -1

    mtl_eval6 = mtl.boolean_eval.pointwise_sat(phi | ~phi)
    assert mtl_eval6(x)

    mtl_eval7 = mtl.boolean_eval.pointwise_sat(phi.weak_since(mtl.BOT))
    assert mtl_eval7(x) == 1

    mtl_eval8 = mtl.boolean_eval.pointwise_sat(phi.hist())
    mtl_eval9 = mtl.boolean_eval.pointwise_sat(~((~phi).once()))
    assert mtl_eval8(x) == mtl_eval9(x)



def test_callable_interface():
    phi = mtl.parse(
        '(((H[0, 4] ap6 & P[2, 1] ap1) | ap2) & H[0,0](ap2))')
    assert not phi(x, 0)
