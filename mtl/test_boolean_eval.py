import hypothesis.strategies as st
from hypothesis import given

import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy

x = {
    "ap1": [(0, True), (0.1, True), (0.2, False)],
    "ap2": [(0, False), (0.2, True), (0.5, False)],
    "ap3": [(0, True), (0.1, True), (0.3, False)],
    "ap4": [(0, False), (0.1, False), (0.3, False)],
    "ap5": [(0, False), (0.1, False), (0.3, True)],
    "ap6": [(0, True), (float('inf'), True)],
}


@given(st.just(mtl.ast.Next(mtl.BOT) | mtl.ast.Next(mtl.TOP)))
def test_eval_smoke_tests(phi):
    assert mtl.parse('~ap4')(x, 0, quantitative=False)
    assert mtl.parse('G[0.1, 0.03] ~ap4')(x, 0, quantitative=False)

    phi6 = mtl.parse('G[0.1, 0.03] ~ap5')
    assert phi6(x, 0, quantitative=False)
    assert phi6(x, 0.2, quantitative=False)

    assert mtl.parse('G ~ap4')(x, 0, quantitative=False)
    assert mtl.parse('F ap5')(x, 0, quantitative=False)
    assert mtl.parse('(ap1 U ap2)')(x, 0, quantitative=False)
    assert not mtl.parse('(ap2 U ap2)')(x, 0, quantitative=False)


@given(MetricTemporalLogicStrategy)
def test_temporal_identity1(phi):
    assert ((~phi) >> 1)(x, 0, quantitative=False) \
        == (~(phi >> 1))(x, 0, quantitative=False)


@given(MetricTemporalLogicStrategy)
def test_temporal_identity2(phi):
    assert phi(x, 0, quantitative=False) \
        == (not (~phi)(x, 0, quantitative=False))


@given(MetricTemporalLogicStrategy)
def test_temporal_identity3(phi):
    assert (phi & phi)(x, 0, quantitative=False) \
        == phi(x, 0, quantitative=False)


@given(MetricTemporalLogicStrategy)
def test_temporal_identity4(phi):
    assert not (phi & ~phi)(x, 0, quantitative=False)
    assert (phi | ~phi)(x, 0, quantitative=False)


@given(MetricTemporalLogicStrategy)
def test_temporal_identity5(phi):
    assert mtl.TOP.until(phi)(x, 0, quantitative=False) \
        == phi.eventually()(x, 0, quantitative=False)
