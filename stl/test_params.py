import stl

import hypothesis.strategies as st
from hypothesis import given


@given(st.integers(), st.integers(), st.integers())
def test_params1(a, b, c):
    phi = stl.parse('G[a?, b?](x > c?)')
    assert {x.name for x in phi.params} == {'a?', 'b?', 'c?'}

    phi2 = phi.set_params({'a?': a, 'b?': b, 'c?': c})
    assert phi2.params == set()
    assert phi2 == stl.parse(f'G[{a}, {b}](x > {c})')
