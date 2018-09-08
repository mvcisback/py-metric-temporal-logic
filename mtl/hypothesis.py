import hypothesis.strategies as st
from hypothesis_cfg import ContextFreeGrammarStrategy

import mtl

GRAMMAR = {
    'phi': (
        ('Unary', 'phi'),
        ('(', 'phi', 'Binary', 'phi', ')'),
        ('AP', ), ('FALSE', ), ('TRUE', )
    ),
    'Unary': (('~', ), ('G', 'Interval'), ('F', 'Interval'), ('X', )),
    'Interval': (('', ), ('[1, 3]', )),
    'Binary': (
        (' | ', ), (' & ', ), (' -> ', ), (' <-> ',), (' ^ ',),
        (' U ',),
    ),
    'AP': (('ap1', ), ('ap2', ), ('ap3', ), ('ap4', ), ('ap5', )),
}

MetricTemporalLogicStrategy = st.builds(
    lambda term: mtl.parse(''.join(term)),
    ContextFreeGrammarStrategy(GRAMMAR, max_length=14, start='phi')
)
