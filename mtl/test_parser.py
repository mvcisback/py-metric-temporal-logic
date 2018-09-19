# -*- coding: utf-8 -*-
from hypothesis import given
from traces import TimeSeries

import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy


TS = {
    "ap1": TimeSeries([(0, True), (0.1, True), (0.2, False)]),
    "ap2": TimeSeries([(0, False), (0.2, True), (0.5, False)]),
    "ap3": TimeSeries([(0, True), (0.1, True), (0.3, False)]),
    "ap4": TimeSeries([(0, False), (0.1, False), (0.3, False)]),
    "ap5": TimeSeries([(0, False), (0.1, False), (0.3, True)]),
}


@given(MetricTemporalLogicStrategy)
def test_stablizing_repr(phi):
    for _ in range(10):
        phi, phi2 = mtl.parse(str(phi)), phi

    assert phi == phi2


def test_sugar_smoke():
    mtl.parse('(x <-> x)')
    mtl.parse('(x -> x)')
    mtl.parse('(x ^ x)')
