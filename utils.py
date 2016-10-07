from collections import deque

from lenses import lens
import funcy as fn

from stl.ast import LinEq, And, Or, NaryOpSTL

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


def ast_lens(phi:"STL", bind=True, *, pred) -> lens:
    tls = list(fn.flatten(_ast_lens(phi, pred=pred)))
    tl = lens().tuple_(*tls).each_()
    return tl.bind(phi) if bind else tl


def _ast_lens(phi, *, pred, focus=lens()):
    psi = focus.get(state=phi)
    ret_lens = [focus] if pred(psi) else []

    if isinstance(psi, LinEq):
        return ret_lens

    child_lenses = list(_child_lens(psi, focus=focus))
    ret_lens += [_ast_lens(phi, pred=pred, focus=cl) for cl in child_lenses]
    return ret_lens


lineq_lens = fn.partial(ast_lens, pred=type_pred(LinEq))
and_or_lens = fn.partial(ast_lens, pred=type_pred(And, Or))

def terms_lens(phi:"STL", bind=True) -> lens:
    return lineq_lens(phi, bind).terms.each_()
