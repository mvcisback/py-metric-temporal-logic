from discrete_signals import signal
import pytest

import mtl


@pytest.mark.parametrize('left, right, expected', [
    ([-3, -4], [-8, -6], [-4, -4]),
    ([-5, -4], [-1, -2], [-1, -2]),
    ([3, -2], [-8, -6], [-2, -2]),
    ([3, 2], [-8, -6], [2, 2]),
    ([3, -2, -4], [-8, 5, -6], [3, 5, -4]),
    ([-2, 3], [-8, 5], [-2, 5]),
    ([-2, -4], [5, -6], [5, -4]),
    ([0, -2], [-8, -6], [-2, -2]),
    ([3, 0], [-8, -6], [0, 0]),
    ([-3], [-8], [-3]),
])
def test_eval_weak_until_quantitative(left, right, expected):
    trace = {'a': list(enumerate(left)), 'b': list(enumerate(right))}
    weak_until = mtl.parse('(a W b)')
    until = mtl.parse('(a U b)')

    for t, value in enumerate(expected):
        # Quantitative U is the best right witness, limited by preceding lefts.
        expected_until = max(
            min([right[j]] + left[t:j]) for j in range(t, len(left))
        )
        assert value == max(expected_until, min(left[t:]))
        assert weak_until(trace, time=t, quantitative=True, dt=1) == value
        assert until(trace, time=t, quantitative=True, dt=1) \
            == expected_until


def test_eval_regression_smoke1():
    """From issue #215"""
    d2 = {
        'a': [
            (0, True), (1, True), (3, True), (4, True), (5, False), (6, True)
        ],
        'b': [(0, False), (3, True)],
    }
    f2 = mtl.parse('(a U[0,3] b)')
    f2(d2, quantitative=False)


def test_eval_regression_next_neg():
    """From issue #219"""
    d = {"a": [(0, False), (1, True)]}
    f = mtl.parse("(a & (X (~a)))")
    v = f(d, quantitative=False, dt=1, time=None)
    assert not f(d, quantitative=False, dt=1)
    assert min(t for t, _ in v) >= 0


def test_eval_with_signal():
    spec = mtl.parse('F(above_three)')

    raw_data = signal([(0, 1), (1, 2), (2, 3)], start=0, end=10, tag='a')
    processed = raw_data.map(lambda val: val['a'] > 3, tag="above_three")

    assert not spec(processed, quantitative=False)
    assert spec(processed, quantitative=True) == 0


def test_eval_regression_until_start():
    """From issue #221"""
    x = {
        "ap1": [(0, True), (0.1, True), (0.2, False)],
    }

    phi = (mtl.parse("(X TRUE W X TRUE)"))
    phi(x, 0, quantitative=False)


def test_eval_regression_timed_until():
    """From issue #217"""
    x = {
        'start': [(0, True), (200, False)],
        'success': [(0, False), (300, True)]
    }
    phi = mtl.parse('(~start U[0,120] success)')
    assert phi(x, time=200, quantitative=False, dt=1)

    y = {
        'start': [(0, True), (1, False), (5, True), (6, True)],
        'success': [(0, False), (20, True)]
    }
    phi1 = mtl.parse('(start U[0,20] success)')
    assert phi1(y, time=6, quantitative=False, dt=1)

    z = {
        'start': [(0, True), (200, False)],
        'success': [(0, False), (300, True)]
    }
    phi2 = mtl.parse('F[0,120]success')
    assert phi2(z, time=181, quantitative=False, dt=1)
