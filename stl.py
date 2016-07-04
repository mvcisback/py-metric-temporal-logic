# -*- coding: utf-8 -*-
# TODO: create lens convenience functions
#    x.lens().set()
# TODO: create iso lens between sugar and non-sugar
# TODO: supress + given a + (-b). i.e. want a - b

from collections import namedtuple, deque
from itertools import repeat
from typing import Union
from enum import Enum

VarKind = Enum("VarKind", ["x", "u", "w"])
str_to_varkind = {"x": VarKind.x, "u": VarKind.u, "w": VarKind.w}

class LinEq(namedtuple("LinEquality", ["terms", "op", "const"])):
    def __repr__(self):
        n = len(self.terms)
        rep = "{}"
        if n > 1:
            rep += " + {}"*(n - 1)
        rep += " {op} {c}"
        return rep.format(*self.terms, op=self.op, c=self.const)

    def children(self):
        return []


class Var(namedtuple("Var", ["kind", "id", "time"])):
    def __repr__(self):
        time_str = "'" if self.time == -1 else "[t+{}]".format(self.time)
        return "{k}{i}{t}".format(k=self.kind.name, i=self.id, t=time_str)


class Term(namedtuple("Term", ["dt", "coeff", "var"])):
    def __repr__(self):
        dt = "dt*" if self.dt else ""
        coeff = str(self.coeff) + "*" if self.coeff != 1 else ""
        return "{dt}{c}{v}".format(dt=dt, c=coeff, v=self.var)


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
