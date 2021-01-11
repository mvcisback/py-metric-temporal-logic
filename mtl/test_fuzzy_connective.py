import math
from itertools import repeat

import hypothesis.strategies as st
from hypothesis import given

from mtl.connective import default, godel, zadeh, lukasiewicz, product

OO = float('inf')


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_connective_neg(con, a: float, b: float):
    assert con.negation(0.) == 1.
    assert con.negation(1.) == 0.
    assert not (a <= b) or (con.negation(a) >= con.negation(b))


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_connective_norm(con, a: float, b: float, c: float):
    assert con.tnorm([a, b, 0.]) == 0.
    assert con.tnorm([a, 1.]) == a
    assert con.tnorm([a, b]) == con.tnorm([b, a])
    assert (not b >= c) or (con.tnorm([a, b]) >= con.tnorm([a, c]))
    assert con.tnorm([a, b]) <= a


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_connective_conorm(con, a: float, b: float, c: float):
    assert con.tconorm([a, 0.]) == a
    assert con.tconorm([a, b, 1.]) == 1.
    assert con.tconorm([a, b]) == con.tconorm([b, a])
    assert (not b >= c) or (con.tconorm([a, b]) >= con.tconorm([a, c]))
    assert con.tconorm([a, b]) >= a


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_connective_implication(con, a: float, b: float, c: float):
    assert con.implication(1., a) == a
    assert con.implication(0., b) == con.implication(a, 1.) == 1.
    assert con.implication(a, 0.) == con.negation(a)
    assert (not a <= b) or (con.implication(a, c) >= con.implication(b, c))
    assert (not b <= c) or (con.implication(a, b) <= con.implication(a, c))
    assert con.implication(a, b) >= max(con.negation(a), b)


@given(
    st.sampled_from([default, zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.integers(min_value=1, max_value=32),
)
def test_fuzzy_connective_pow(con, a, p):
    assert con.tnorm_pow(a, p) >= con.tnorm_pow(a, OO)
    assert con.tconorm_pow(a, p) <= con.tconorm_pow(a, OO)
    assert con.tnorm_pow(a, p) >= con.tnorm_pow(a, p + 1)
    assert con.tconorm_pow(a, p) <= con.tconorm_pow(a, p + 1)
    assert math.isclose(con.tnorm_pow(a, p), con.tnorm(repeat(a, p)))
    assert math.isclose(con.tconorm_pow(a, p), con.tconorm(repeat(a, p)))
