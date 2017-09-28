# -*- coding: utf-8 -*-
import stl
from hypothesis import given, note
from hypothesis_cfg import ContextFreeGrammarStrategy

GRAMMAR = {
    'phi': (('Unary', '(', 'phi', ')'),
            ('(', 'phi', ')',  'Binary', '(', 'phi', ')'),
            ('AP',)),
    'Unary': (('~',), ('G',), ('F',), ('X',)),
    'Binary': ((' | ',), (' & ',), (' U ',)),
}


@given(ContextFreeGrammarStrategy(GRAMMAR, length=20, start='phi'))
def test_invertable_repr(foo):
    note(''.join(foo))
    phi = stl.parse(''.join(foo))
    assert str(phi) == str(stl.parse(str(phi)))


