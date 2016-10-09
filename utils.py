from collections import deque

from lenses import lens
import funcy as fn
import sympy

from stl.ast import LinEq, And, Or, NaryOpSTL, F, G, Interval

def walk(stl, bfs=False):
    """Walks Ast. Defaults to DFS unless BFS flag is set."""
    pop = deque.popleft if bfs else deque.pop
    children = deque([stl])
    while len(children) != 0:
        node = pop(children)
        yield node
        children.extend(node.children())


def tree(stl):
    return {x:set(x.children()) for x in walk(stl) if x.children()}


def type_pred(*args):
    ast_types = set(args)
    return lambda x: type(x) in ast_types


def _child_lens(psi, focus):
    if psi is None:
        return
    if isinstance(psi, NaryOpSTL):
        for j, _ in enumerate(psi.args):
            yield focus.args[j]
    else:
        yield focus.arg


def ast_lens(phi:"STL", bind=True, *, pred, focus_lens=None) -> lens:
    if focus_lens is None:
        focus_lens = lambda x: [lens()]
    tls = list(fn.flatten(_ast_lens(phi, pred=pred, focus_lens=focus_lens)))
    tl = lens().tuple_(*tls).each_()
    return tl.bind(phi) if bind else tl


def _ast_lens(phi, *, pred, focus=lens(), focus_lens):
    psi = focus.get(state=phi)
    ret_lens = [focus.add_lens(l) for l in focus_lens(psi)] if pred(psi) else []

    if isinstance(psi, LinEq):
        return ret_lens

    child_lenses = list(_child_lens(psi, focus=focus))
    ret_lens += [_ast_lens(phi, pred=pred, focus=cl, focus_lens=focus_lens) 
                 for cl in child_lenses]
    return ret_lens


lineq_lens = fn.partial(ast_lens, pred=type_pred(LinEq))
and_or_lens = fn.partial(ast_lens, pred=type_pred(And, Or))

def terms_lens(phi:"STL", bind=True) -> lens:
    return lineq_lens(phi, bind).terms.each_()


def param_lens(phi):
    is_sym = lambda x: isinstance(x, sympy.Symbol)
    def focus_lens(leaf):
        return [lens().const] if isinstance(leaf, LinEq) else [lens().interval[0], lens().interval[1]]

    return ast_lens(phi, pred=type_pred(LinEq, F, G), focus_lens=focus_lens).filter_(is_sym)
