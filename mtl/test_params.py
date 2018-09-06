import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy

import hypothesis.strategies as st
from hypothesis import given


@given(st.integers(), st.integers(), st.integers())
def test_params1(a, b, c):
    phi = mtl.parse('G[a, b] x')
    assert {x.name for x in phi.params} == {'a', 'b'}

    phi2 = phi.set_params({'a': a, 'b': b})
    assert phi2.params == set()
    assert phi2 == mtl.parse(f'G[{a}, {b}](x)')


@given(MetricTemporalLogicStrategy)
def test_hash_stable(phi):
    assert hash(phi) == hash(mtl.parse(str(phi)))
