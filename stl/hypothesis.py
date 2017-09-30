from hypothesis_cfg import ContextFreeGrammarStrategy

from hypothesis.searchstrategy.strategies import SearchStrategy
from hypothesis.strategies import integers

import stl


GRAMMAR = {
    'phi': (('Unary', '(', 'phi', ')'),
            ('(', 'phi', ')',  'Binary', '(', 'phi', ')'),
            ('AP',)),
    'Unary': (('~',), ('G',), ('F',), ('X',)),
    'Binary': ((' | ',), (' & ',), (' U ',)),
}


class SignalTemporalLogicStategy(SearchStrategy):
    def __init__(self, max_length: int):
        super(SearchStrategy, self).__init__()
        self.cfg_gen = ContextFreeGrammarStrategy(
            GRAMMAR, max_length=max_length, start='phi')

    def do_draw(self, data):
        # TODO: randomly assign all intervals
        # TODO: randomly decide between linear predicate or boolean predicates
        # TODO: randomly generate boolean predicate
        # TODO: randomly generate linear predicate
        phi =  stl.parse("".join(self.cfg_gen.do_draw(data)))
        return phi
