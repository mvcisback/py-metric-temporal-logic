from hypothesis import given, strategies as st

import mtl

from mtl.connective import godel, zadeh, lukasiewicz, product
from mtl.hypothesis import MetricTemporalLogicStrategy


VALUES = {
    "ap1": [(0, 1.), (0.1, 1.), (0.2, 0.)],
    "ap2": [(0, 0.), (0.2, 1.), (0.5, 0.)],
    "ap3": [(0, 1.), (0.1, 1.), (0.3, 0.)],
    "ap4": [(0, 0.), (0.1, 0.), (0.3, 0.)],
    "ap5": [(0, 0.), (0.1, 0.), (0.3, 1.)],
    "ap6": [(0, 1.), (float('inf'), 1.)],
}


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


@given(
    st.sampled_from([zadeh, godel, lukasiewicz, product]),
    MetricTemporalLogicStrategy,
    MetricTemporalLogicStrategy,
    MetricTemporalLogicStrategy
)
def test_fuzzy_eval(con, phi1, phi2, phi3):
    v1 = phi1(VALUES, 0, logic=con)
    v2 = phi2(VALUES, 0, logic=con)
    v3 = phi3(VALUES, 0, logic=con)
    nv1 = (~phi1)(VALUES, 0, logic=con)
    nv2 = (~phi2)(VALUES, 0, logic=con)
    assert (not v1 <= v2) or (nv1 >= nv2)
    assert (not v2 >= v3) or con.tnorm([v1, v2]) >= con.tnorm([v1, v3])
    assert (not v2 >= v3) or con.tconorm([v1, v2]) >= con.tconorm([v1, v3])
    assert con.tnorm([v1, v2]) <= v1
    assert con.tconorm([v1, v2]) >= v1
    assert (not v1 <= v2) \
        or (con.implication(v1, v3) >= con.implication(v2, v3))
    assert (not v2 <= v3) \
        or (con.implication(v1, v2) <= con.implication(v1, v3))
    assert con.implication(v1, v2) >= max(con.negation(v1), v2)
