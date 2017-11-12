import hypothesis.strategies as st
from hypothesis_cfg import ContextFreeGrammarStrategy

import stl

GRAMMAR = {
    'phi': (('Unary', '(', 'phi', ')'), ('(', 'phi', ')', 'Binary', '(', 'phi',
                                         ')'), ('AP', ), ('LINEQ', ), ('⊥', ),
            ('⊤', )),
    'Unary': (('~', ), ('G', 'Interval'), ('F', 'Interval'), ('X', )),
    'Interval': (('', ), ('[1, 3]', )),
    'Binary': ((' | ', ), (' & ', ), (' U ', ), (' -> ', ), (' <-> ',),
               (' ^ ',)),
    'AP': (('AP1', ), ('AP2', ), ('AP3', ), ('AP4', ), ('AP5', )),
    'LINEQ': (('x > 4', ), ('y < 2', ), ('y >= 3', ), ('x + 2.0y >= 2', )),
}

SignalTemporalLogicStrategy = st.builds(lambda term: stl.parse(''.join(term)),
                                        ContextFreeGrammarStrategy(
                                            GRAMMAR,
                                            max_length=15,
                                            start='phi'))
