import stl
from stl.hypothesis import SignalTemporalLogicStrategy

from hypothesis import given


@given(SignalTemporalLogicStrategy)
def test_f_neg_or_canonical_form(phi):
    phi2 = stl.utils.f_neg_or_canonical_form(phi)
    phi3 = stl.utils.f_neg_or_canonical_form(phi2)
    assert phi2 == phi3
    assert not any(
        isinstance(x, (stl.ast.G, stl.ast.And)) for x in phi2.walk())
