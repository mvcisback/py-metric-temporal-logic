from discrete_signals import signal

import mtl


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
