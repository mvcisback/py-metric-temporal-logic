from itertools import product

import hypothesis.strategies as st
from hypothesis import given
import pytest

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


@pytest.mark.parametrize('left, right, expected', [
    ([False, False], [False, False], [False, False]),
    ([True, False], [False, False], [False, False]),
    ([True, True], [False, False], [True, True]),
    ([True, False, False], [False, True, False], [True, True, False]),
    ([False, True], [False, True], [False, True]),
    ([False, False], [True, False], [True, False]),
    ([False], [False], [False]),
])
def test_eval_weak_until(left, right, expected):
    trace = {'a': list(enumerate(left)), 'b': list(enumerate(right))}
    phi = mtl.parse('(a W b)')

    for t, value in enumerate(expected):
        assert phi(trace, time=t, quantitative=False, dt=1) == value


@pytest.mark.parametrize('length', range(1, 5))
def test_eval_until_exhaustive(length):
    weak_until = mtl.parse('(a W b)')
    until = mtl.parse('(a U b)')

    for values in product((False, True), repeat=2 * length):
        left, right = values[:length], values[length:]
        trace = {'a': list(enumerate(left)), 'b': list(enumerate(right))}

        for t in range(length):
            # A witness for U needs the left operand only before the witness.
            expected_until = any(
                right[j] and all(left[t:j]) for j in range(t, length)
            )
            expected_weak_until = expected_until or all(left[t:])
            assert weak_until(trace, time=t, quantitative=False, dt=1) \
                == expected_weak_until
            assert until(trace, time=t, quantitative=False, dt=1) \
                == expected_until


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
