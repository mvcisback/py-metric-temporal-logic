import stl
from stl.hypothesis import SignalTemporalLogicStrategy

from hypothesis import given
from pytest import raises

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


def test_f_neg_or_canonical_form_not_implemented():
    with raises(NotImplementedError):
        stl.utils.f_neg_or_canonical_form(stl.ast.AST())


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


def test_linear_stl_lipschitz_rigid():
    phi = stl.parse('(x + 3y - 4z < 3)')
    assert stl.utils.linear_stl_lipschitz(phi) == (8)


@given(SignalTemporalLogicStrategy, SignalTemporalLogicStrategy)
def test_linear_stl_lipschitz(phi1, phi2):
    lip1 = stl.utils.linear_stl_lipschitz(phi1)
    lip2 = stl.utils.linear_stl_lipschitz(phi2)
    phi3 = phi1 | phi2
    assert stl.utils.linear_stl_lipschitz(phi3) == max(lip1, lip2)


@given(SignalTemporalLogicStrategy, SignalTemporalLogicStrategy)
def test_timed_until_smoke_test(phi1, phi2):
    stl.utils.timed_until(phi1, phi2, lo=2, hi=20)


def test_discretize():
    dt = 0.3

    phi = stl.parse('X(AP1)')
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt)
    phi3 = stl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = stl.parse('G[0.3, 1.2](F[0.6, 1.5](AP1))')
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt)
    phi3 = stl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = stl.parse('G[0.3, 1.4](F[0.6, 1.5](AP1))')
    assert not stl.utils.is_discretizable(phi, dt)

    phi = stl.parse('G[0.3, 1.2](F(AP1))')
    assert not stl.utils.is_discretizable(phi, dt)

    phi = stl.parse('G[0.3, 1.2]((AP1) U (AP2))')
    assert not stl.utils.is_discretizable(phi, dt)

    phi = stl.parse('G[0.3, 0.6](~(F[0, 0.3](A)))')
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt, distribute=True)
    phi3 = stl.utils.discretize(phi2, dt, distribute=True)
    assert phi2 == phi3
    assert phi2 == stl.parse(
        '(~((X(A)) ∨ (X(X(A))))) ∧ (~((X(X(A))) ∨ (X(X(X(A))))))')

    phi = stl.TOP
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt)
    phi3 = stl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = stl.BOT
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt)
    phi3 = stl.utils.discretize(phi2, dt)
    assert phi2 == phi3


def test_scope():
    dt = 0.3

    phi = stl.parse('X(AP1)')
    assert stl.utils.scope(phi, dt) == 0.3

    phi = stl.parse('X((X(AP1)) | (AP2))')
    assert stl.utils.scope(phi, dt) == 0.6

    phi = stl.parse('G[0.3, 1.2](F[0.6, 1.5](AP1))')
    assert stl.utils.scope(phi, dt) == 1.2 + 1.5

    phi = stl.parse('G[0.3, 1.2](F(AP1))')
    assert stl.utils.scope(phi, dt) == float('inf')

    phi = stl.parse('G[0.3, 1.2]((AP1) U (AP2))')
    assert stl.utils.scope(phi, dt) == float('inf')
