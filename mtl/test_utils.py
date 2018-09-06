import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy

from hypothesis import given
from pytest import raises

CONTEXT = {
    mtl.parse('ap1'): mtl.parse('x'),
    mtl.parse('ap2'): mtl.parse('(y U z)'),
    mtl.parse('ap3'): mtl.parse('x'),
    mtl.parse('ap4'): mtl.parse('(x -> y -> z)'),
    mtl.parse('ap5'): mtl.parse('(ap1 <-> y <-> z)'),
}
APS = set(CONTEXT.keys())


@given(MetricTemporalLogicStrategy)
def test_f_neg_or_canonical_form(phi):
    phi2 = mtl.utils.f_neg_or_canonical_form(phi)
    phi3 = mtl.utils.f_neg_or_canonical_form(phi2)
    assert phi2 == phi3
    assert not any(
        isinstance(x, (mtl.ast.G, mtl.ast.And)) for x in phi2.walk())


def test_f_neg_or_canonical_form_not_implemented():
    with raises(NotImplementedError):
        mtl.utils.f_neg_or_canonical_form(mtl.ast.AST())


def test_inline_context_rigid():
    phi = mtl.parse('G ap1')
    phi2 = phi.inline_context(CONTEXT)
    assert phi2 == mtl.parse('G x')

    phi = mtl.parse('G ap5')
    phi2 = phi.inline_context(CONTEXT)
    assert phi2 == mtl.parse('G(x <-> y <-> z)')


@given(MetricTemporalLogicStrategy)
def test_inline_context(phi):
    phi2 = phi.inline_context(CONTEXT)
    assert not (APS & phi2.atomic_predicates)


@given(MetricTemporalLogicStrategy, MetricTemporalLogicStrategy)
def test_timed_until_smoke_test(phi1, phi2):
    mtl.utils.timed_until(phi1, phi2, lo=2, hi=20)


def test_discretize():
    dt = 0.3

    phi = mtl.parse('@ ap1')
    assert mtl.utils.is_discretizable(phi, dt)
    phi2 = mtl.utils.discretize(phi, dt)
    phi3 = mtl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = mtl.parse('G[0.3, 1.2] F[0.6, 1.5] ap1')
    assert mtl.utils.is_discretizable(phi, dt)
    phi2 = mtl.utils.discretize(phi, dt)
    phi3 = mtl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = mtl.parse('G[0.3, 1.4] F[0.6, 1.5] ap1')
    assert not mtl.utils.is_discretizable(phi, dt)

    phi = mtl.parse('G[0.3, 1.2] F ap1')
    assert not mtl.utils.is_discretizable(phi, dt)

    phi = mtl.parse('G[0.3, 1.2] (ap1 U ap2)')
    assert not mtl.utils.is_discretizable(phi, dt)

    phi = mtl.parse('G[0.3, 0.6] ~F[0, 0.3] a')
    assert mtl.utils.is_discretizable(phi, dt)
    phi2 = mtl.utils.discretize(phi, dt, distribute=True)
    phi3 = mtl.utils.discretize(phi2, dt, distribute=True)
    assert phi2 == phi3
    assert phi2 == mtl.parse(
        '(~(@a | @@a) & ~(@@a | @@@a))')

    phi = mtl.TOP
    assert mtl.utils.is_discretizable(phi, dt)
    phi2 = mtl.utils.discretize(phi, dt)
    phi3 = mtl.utils.discretize(phi2, dt)
    assert phi2 == phi3

    phi = mtl.BOT
    assert mtl.utils.is_discretizable(phi, dt)
    phi2 = mtl.utils.discretize(phi, dt)
    phi3 = mtl.utils.discretize(phi2, dt)
    assert phi2 == phi3


def test_scope():
    dt = 0.3

    phi = mtl.parse('@ap1')
    assert mtl.utils.scope(phi, dt) == 0.3

    phi = mtl.parse('(@@ap1 | ap2)')
    assert mtl.utils.scope(phi, dt) == 0.6

    phi = mtl.parse('G[0.3, 1.2] F[0.6, 1.5] ap1')
    assert mtl.utils.scope(phi, dt) == 1.2 + 1.5

    phi = mtl.parse('G[0.3, 1.2] F ap1')
    assert mtl.utils.scope(phi, dt) == float('inf')

    phi = mtl.parse('G[0.3, 1.2] (ap1 U ap2)')
    assert mtl.utils.scope(phi, dt) == float('inf')
