import hypothesis.strategies as st
from hypothesis_cfg import ContextFreeGrammarStrategy
from traces import TimeSeries

import mtl

GRAMMAR = {
    'phi': (
        ('Unary', 'phi'),
        ('(', 'phi', 'Binary', 'phi', ')'),
        ('AP', ), ('FALSE', ), ('TRUE', )
    ),
    'Unary': (('~', ), ('H', 'Interval'), ('P', 'Interval'), ('Z', )),
    'Interval': (('', ), ('[1, 3]', )),
    'Binary': (
        (' | ', ), (' & ', ), (' -> ', ), (' <-> ',), (' ^ ',),
        (' M ',),
    ),
    'AP': (('ap1', ), ('ap2', ), ('ap3', ), ('ap4', ), ('ap5', )),
}

MetricTemporalLogicStrategy = st.builds(
    lambda term: mtl.parse(''.join(term)),
    ContextFreeGrammarStrategy(GRAMMAR, max_length=14, start='phi')
)

def _build_boolean_trace(times):
    ts = TimeSeries(times)
    return TimeSeries((t - ts.first_key(), v) for t, v in ts)


BooleanTraceStrategy = st.builds(
    _build_boolean_trace, 
    st.lists(st.tuples(
        st.floats(min_value=0,  allow_nan=False, allow_infinity=False), 
        st.one_of(st.just(-1), st.just(1))), min_size=1
    )
)


APTraceStrategy = st.builds(
    lambda ts: {f'ap{i+1}': v for i, v in enumerate(ts)},
    st.tuples(*(5*[BooleanTraceStrategy]))
)
