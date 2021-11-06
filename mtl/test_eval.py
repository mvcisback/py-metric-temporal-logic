from discrete_signals import signal
from hypothesis import given

import mtl
from mtl import connective
from mtl.evaluator import booleanize_signal, to_signal, eval_mtl_g, eval_mtl_g_legacy
from mtl.hypothesis import MetricTemporalLogicStrategy


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


def test_eval_comparison():
    a = mtl.parse("a")
    b = mtl.parse("b")

    d = {
        "a": [(0,  5.), (1, 10.),           (3,  0.), (4, 10.)],
        "b": [(0, 15.),           (2,  5.),           (4, 10.)],
    }

    i = a < b
    assert i(d, time=0, quantitative=False)
    assert i(d, time=1, quantitative=False)
    assert not i(d, time=2, quantitative=False)
    assert i(d, time=3, quantitative=False)
    assert not i(d, time=4, quantitative=False)

    i = a.eq(b)
    assert not i(d, time=0, quantitative=False)
    assert i(d, time=4, quantitative=False)


@given(MetricTemporalLogicStrategy)
def test_eval_regression_always(phi):
    x = {
        "ap1": [(0, True), (1, True), (2, False)],
        "ap2": [(0, False), (2, True), (5, False)],
        "ap3": [(0, True), (1, True), (3, False)],
        "ap4": [(0, False), (1, False), (3, False)],
        "ap5": [(0, False), (1, False), (3, True)],
        "ap6": [(0, True), (float('inf'), True)],
    }
    s = booleanize_signal(to_signal(x), connective.default)
    f = eval_mtl_g(phi.always(), 0.1, connective.default)(s)
    r = eval_mtl_g_legacy(phi.always(), 0.1, connective.default)(s)
    assert f == r



