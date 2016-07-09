# -*- coding: utf-8 -*-
# TODO: create iso lens between sugar and non-sugar
# TODO: supress + given a + (-b). i.e. want a - b

from collections import namedtuple, deque
from itertools import repeat
from typing import Union
from enum import Enum
from sympy import Symbol

from lenses import lens

VarKind = Enum("VarKind", ["x", "u", "w"])
str_to_varkind = {"x": VarKind.x, "u": VarKind.u, "w": VarKind.w}
dt_sym = Symbol('dt', positive=True)
t_sym = Symbol('t', positive=True)

class LinEq(namedtuple("LinEquality", ["terms", "op", "const"])):
    def __repr__(self):
        rep = "{lhs} {op} {c}"
        lhs = sum(t.id for t in self.terms)
        return rep.format(lhs=lhs, op=self.op, c=self.const)

    def children(self):
        return []


class Var(namedtuple("Var", ["kind", "id", "time"])):
    def __repr__(self):
        time_str = "[{}]".format(self.time)
        return "{i}{t}".format(k=self.kind.name, i=self.id, t=time_str)


class Interval(namedtuple('I', ['lower', 'upper'])):
    def __repr__(self):
        return "[{},{}]".format(self.lower, self.upper)

    def children(self):
        return [self.lower, self.upper]


class NaryOpSTL(namedtuple('NaryOp', ['args'])):
    OP = "?"
    def __repr__(self):
        n = len(self.args)
        if n == 1:
            return "{}".format(self.args[0])
        elif self.args:
            rep = "({})" + " {op} ({})"*(len(self.args) - 1)
            return rep.format(*self.args, op=self.OP)
        else:
            return ""

    def children(self):
        return self.args


class Or(NaryOpSTL):
    OP = "∨"

class And(NaryOpSTL):
    OP = "∧"


class ModalOp(namedtuple('ModalOp', ['interval', 'arg'])):
    def children(self):
        return [self.arg]


class F(ModalOp):
    def __repr__(self):
        return "◇{}({})".format(self.interval, self.arg)


class G(ModalOp):
    def __repr__(self):
        return "□{}({})".format(self.interval, self.arg)


class Neg(namedtuple('Neg', ['arg'])):
    def __repr__(self):
        return "¬({})".format(self.arg)

    def children(self):
        return [self.arg]


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


def time_lens(phi:"STL") -> lens:
    return _time_lens(phi).bind(phi)


def _time_lens(phi):
    if isinstance(phi, LinEq):
        return lens().terms.each_().var.time

    if isinstance(phi, NaryOpSTL):
        child_lens = [lens()[i].add_lens(_time_lens(c)) for i, c
                      in enumerate(phi.children())]
        return lens().args.tuple_(*child_lens).each_()
    else:
        return lens().arg.add_lens(_time_lens(phi.arg))


def set_time(phi, *, t, dt=0.1):
    return time_lens(phi).call("evalf", subs={t_sym: t, dt_sym: dt})
