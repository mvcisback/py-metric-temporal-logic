from hypothesis_cfg import ContextFreeGrammarStrategy

import hypothesis.strategies as st
from hypothesis.searchstrategy.strategies import SearchStrategy

import stl


GRAMMAR = {
    'phi': (('Unary', '(', 'phi', ')'),
            ('(', 'phi', ')',  'Binary', '(', 'phi', ')'),
            ('AP',)),
    'Unary': (('~',), ('G',), ('F',), ('X',)),
    'Binary': ((' | ',), (' & ',), (' U ',)),
    'AP': (('AP1',), ('AP2',), ('AP3',), ('AP4',), ('AP5',)),
}

def to_stl(term):
    return stl.parse(''.join(term))

SignalTemporalLogicStrategy = st.builds(
    to_stl, ContextFreeGrammarStrategy(
        GRAMMAR, max_length=25, start='phi'))
