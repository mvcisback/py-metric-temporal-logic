import stl
from stl.hypothesis import SignalTemporalLogicStrategy

from hypothesis import given


@given(SignalTemporalLogicStrategy)
def test_identities(phi):
    assert stl.TOP == stl.TOP | phi
    assert stl.BOT == stl.BOT & phi
    assert stl.TOP == phi | stl.TOP
    assert stl.BOT == phi & stl.BOT
    assert phi == phi & stl.TOP
    assert phi == phi | stl.BOT
    assert stl.TOP == stl.TOP & stl.TOP
    assert stl.BOT == stl.BOT | stl.BOT
    assert stl.TOP == stl.TOP | stl.BOT
    assert stl.BOT == stl.TOP & stl.BOT
    assert ~stl.BOT == stl.TOP
    assert ~stl.TOP == stl.BOT
    assert ~~stl.BOT == stl.BOT
    assert ~~stl.TOP == stl.TOP
    assert (phi & phi) & phi == phi & (phi & phi)
    assert (phi | phi) | phi == phi | (phi | phi)
    assert ~~phi == phi


def test_lineqs_unittest():
    phi = stl.parse('(G[0, 1](x + y > a?)) & (F[1,2](z - x > 0))')
    assert len(phi.lineqs) == 2
    assert phi.lineqs == {stl.parse('x + y > a?'), stl.parse('z - x > 0')}

    phi = stl.parse('(G[0, 1](x + y > a?)) U (F[1,2](z - x > 0))')
    assert len(phi.lineqs) == 2
    assert phi.lineqs == {stl.parse('x + y > a?'), stl.parse('z - x > 0')}

    phi = stl.parse('G(⊥)')
    assert phi.lineqs == set()

    phi = stl.parse('F(⊤)')
    assert phi.lineqs == set()


def test_walk():
    phi = stl.parse(
        '((G[0, 1](x + y > a?)) & (F[1,2](z - x > 0))) | ((X(AP1)) U (AP2))')
    assert len(list((~phi).walk())) == 11


def test_var_names():
    phi = stl.parse(
        '((G[0, 1](x + y > a?)) & (F[1,2](z - x > 0))) | ((X(AP1)) U (AP2))')
    assert phi.var_names == {'x', 'y', 'z', 'x', 'AP1', 'AP2'}
