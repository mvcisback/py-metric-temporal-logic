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

def test_walk():
    phi = stl.parse(
        '(([ ][0, 1] ap1 & < >[1,2] ap2) | (@ap1 U ap2))')
    assert len(list((~phi).walk())) == 11
