import stl
from stl.hypothesis import SignalTemporalLogicStrategy

from hypothesis import given


CONTEXT = {
    stl.parse('AP1'): stl.parse('F(x > 4)'),
    stl.parse('AP2'): stl.parse('(AP1) U (AP1)'),
    stl.parse('AP3'): stl.parse('y < 4'),
    stl.parse('AP4'): stl.parse('y < 3'),
    stl.parse('AP5'): stl.parse('y + x > 4'),
}
APS = set(CONTEXT.keys())


@given(SignalTemporalLogicStrategy)
def test_f_neg_or_canonical_form(phi):
    phi2 = stl.utils.f_neg_or_canonical_form(phi)
    phi3 = stl.utils.f_neg_or_canonical_form(phi2)
    assert phi2 == phi3
    assert not any(
        isinstance(x, (stl.ast.G, stl.ast.And)) for x in phi2.walk())


def test_inline_context_rigid():
    phi = stl.parse('G(AP1)')
    phi2 = phi.inline_context(CONTEXT)
    assert phi2 == stl.parse('G(F(x > 4))')

    phi = stl.parse('G(AP2)')
    phi2 = phi.inline_context(CONTEXT)
    assert phi2 == stl.parse('G((F(x > 4)) U (F(x > 4)))')


@given(SignalTemporalLogicStrategy)
def test_inline_context(phi):
    phi2 = phi.inline_context(CONTEXT)
    assert not (APS & phi2.atomic_predicates)
