import stl
from stl.hypothesis import SignalTemporalLogicStrategy

from hypothesis import given
from pytest import raises

CONTEXT = {
    stl.parse('ap1'): stl.parse('x'),
    stl.parse('ap2'): stl.parse('(y U z)'),
    stl.parse('ap3'): stl.parse('x'),
    stl.parse('ap4'): stl.parse('(x -> y -> z)'),
    stl.parse('ap5'): stl.parse('(ap1 <-> y <-> z)'),
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
    phi = stl.parse('G ap1')
    phi2 = phi.inline_context(CONTEXT)
    assert phi2 == stl.parse('G x')

    phi = stl.parse('G ap5')
    phi2 = phi.inline_context(CONTEXT)
    assert phi2 == stl.parse('G(x <-> y <-> z)')


@given(SignalTemporalLogicStrategy)
def test_inline_context(phi):
    phi2 = phi.inline_context(CONTEXT)
    assert not (APS & phi2.atomic_predicates)


@given(SignalTemporalLogicStrategy, SignalTemporalLogicStrategy)
def test_timed_until_smoke_test(phi1, phi2):
    stl.utils.timed_until(phi1, phi2, lo=2, hi=20)


def test_discretize():
    dt = 0.3

    phi = stl.parse('@ ap1')
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt)
    phi3 = stl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = stl.parse('G[0.3, 1.2] F[0.6, 1.5] ap1')
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt)
    phi3 = stl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = stl.parse('G[0.3, 1.4] F[0.6, 1.5] ap1')
    assert not stl.utils.is_discretizable(phi, dt)

    phi = stl.parse('G[0.3, 1.2] F ap1')
    assert not stl.utils.is_discretizable(phi, dt)

    phi = stl.parse('G[0.3, 1.2] (ap1 U ap2)')
    assert not stl.utils.is_discretizable(phi, dt)

    phi = stl.parse('G[0.3, 0.6] ~F[0, 0.3] a')
    assert stl.utils.is_discretizable(phi, dt)
    phi2 = stl.utils.discretize(phi, dt, distribute=True)
    phi3 = stl.utils.discretize(phi2, dt, distribute=True)
    assert phi2 == phi3
    assert phi2 == stl.parse(
        '(~(@a | @@a) & ~(@@a | @@@a))')

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

    phi = stl.parse('@ap1')
    assert stl.utils.scope(phi, dt) == 0.3

    phi = stl.parse('(@@ap1 | ap2)')
    assert stl.utils.scope(phi, dt) == 0.6

    phi = stl.parse('G[0.3, 1.2] F[0.6, 1.5] ap1')
    assert stl.utils.scope(phi, dt) == 1.2 + 1.5

    phi = stl.parse('G[0.3, 1.2] F ap1')
    assert stl.utils.scope(phi, dt) == float('inf')

    phi = stl.parse('G[0.3, 1.2] (ap1 U ap2)')
    assert stl.utils.scope(phi, dt) == float('inf')
