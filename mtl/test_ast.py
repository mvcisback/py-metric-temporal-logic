import mtl
from mtl.hypothesis import MetricTemporalLogicStrategy

from hypothesis import given


@given(MetricTemporalLogicStrategy)
def test_identities(phi):
    assert mtl.TOP == mtl.TOP | phi
    assert mtl.BOT == mtl.BOT & phi
    assert mtl.TOP == phi | mtl.TOP
    assert mtl.BOT == phi & mtl.BOT
    assert phi == phi & mtl.TOP
    assert phi == phi | mtl.BOT
    assert mtl.TOP == mtl.TOP & mtl.TOP
    assert mtl.BOT == mtl.BOT | mtl.BOT
    assert mtl.TOP == mtl.TOP | mtl.BOT
    assert mtl.BOT == mtl.TOP & mtl.BOT
    assert ~mtl.BOT == mtl.TOP
    assert ~mtl.TOP == mtl.BOT
    assert ~~mtl.BOT == mtl.BOT
    assert ~~mtl.TOP == mtl.TOP
    assert (phi & phi) & phi == phi & (phi & phi)
    assert (phi | phi) | phi == phi | (phi | phi)
    assert ~~phi == phi


def test_walk():
    phi = mtl.parse(
        '(([ ][0, 1] ap1 & < >[1,2] ap2) | (@ap1 U ap2))')
    assert len(list((~phi).walk())) == 19
