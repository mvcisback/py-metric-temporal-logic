import hypothesis.strategies as st
from hypothesis_cfg import ContextFreeGrammarStrategy

import stl

GRAMMAR = {
    'phi': (('Unary', '(', 'phi', ')'), ('(', 'phi', ')', 'Binary', '(', 'phi',
                                         ')'), ('AP', ), ('LINEQ', )),
    'Unary': (('~', ), ('G', 'Interval'), ('F', 'Interval'), ('X', )),
    'Interval': (('',), ('[1, 3]',)),
    'Binary': ((' | ', ), (' & ', ), (' U ',)),
    'AP': (('AP1', ), ('AP2', ), ('AP3', ), ('AP4', ), ('AP5', )),
    'LINEQ': (('x > 4', ), ('y < 2', ), ('y >= 3', ), ('x + y >= 2',)),
}


def to_stl(term):
    return stl.parse(''.join(term))


SignalTemporalLogicStrategy = st.builds(to_stl,
                                        ContextFreeGrammarStrategy(
                                            GRAMMAR,
                                            max_length=27,
                                            start='phi'))
