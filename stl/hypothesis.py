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
}



def build_lineq(params):
    pass


LinEqStrategy = st.builds(
    lambda x: stl.ast.Lineq(*x),
    st.tuples(
        st.lists(
            st.tuples(
                st.sampled_from(["x", "y", "z","w"]),
                st.integers(min_value=-5, max_value=5)),
            min_size=1, max_size=4, unique=True),
        st.sampled_from([">=", "<=", "<", ">", "="]),
        st.integers(min_value=-5, max_value=5)
))


class SignalTemporalLogicStategy(SearchStrategy):
    def __init__(self, max_length: int):
        super(SearchStrategy, self).__init__()
        self.cfg_gen = ContextFreeGrammarStrategy(
            GRAMMAR, max_length=max_length, start='phi')
        self.ap_gen = st.builds(
            lambda i: stl.ast.AtomicPred(f"AP{i}"),
            st.integers(min_value=0, max_value=max_length))

    def do_draw(self, data):
        # TODO: randomly assign all intervals
        # TODO: randomly decide between linear predicate or boolean predicates
        # TODO: randomly generate boolean predicate
        # TODO: randomly generate linear predicate
        phi =  stl.parse("".join(self.cfg_gen.do_draw(data)))
        ap_lens = stl.utils.AP_lens(phi).Each()
        phi = ap_lens.modify(lambda _: self.ap_gen.do_draw(data))
        return phi
