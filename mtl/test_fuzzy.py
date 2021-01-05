from hypothesis import given, strategies as st

import mtl

from mtl.connective import godel, zadeh, lukasiewicz, product


def prepare_values(a, b, c):
    return {
        "ap1": [(0., a), (0.1, b), (0.2, c)],
        "apa": [(0., a), ],
        "apb": [(0., b), ],
        "apc": [(0., c), ],
    }


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_binop(con, a: float, b: float, c: float):
    x = prepare_values(a, b, c)
    assert mtl.parse("(apa & apb)")(x, 0, logic=con) == con.tnorm([a, b])
    assert mtl.parse("(apa & apb & apc)")(x, 0, logic=con) \
        == con.tnorm([a, b, c])

    assert mtl.parse("(apa | apb)")(x, 0, logic=con) == con.tconorm([a, b])
    assert mtl.parse("(apa | apb | apc)")(x, 0, logic=con) \
        == con.tconorm([a, b, c])


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_until(con, a: float, b: float, c: float):
    pass


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_implies(con, a: float, b: float, c: float):
    x = prepare_values(a, b, c)
    assert mtl.parse("(apa -> apb)")(x, 0, logic=con) == con.implication(a, b)


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_always(con, a: float, b: float, c: float):
    x = prepare_values(a, b, c)
    assert mtl.parse("G ap1")(x, 0, logic=con) == con.tnorm([a, b, c])


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
    st.floats(min_value=0., max_value=1., width=16),
)
def test_fuzzy_neg(con, a: float, b: float, c: float):
    x = prepare_values(a, b, c)
    assert mtl.parse("~ap1")(x, 0, logic=con) == con.negation(a)
