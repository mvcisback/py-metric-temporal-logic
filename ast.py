# -*- coding: utf-8 -*-
# TODO: create iso lens between sugar and non-sugar
# TODO: supress + given a + (-b). i.e. want a - b

from collections import namedtuple, deque
from itertools import repeat
from typing import Union
from enum import Enum
from sympy import Symbol

VarKind = Enum("VarKind", ["x", "u", "w"])
str_to_varkind = {"x": VarKind.x, "u": VarKind.u, "w": VarKind.w}
dt_sym = Symbol('dt', positive=True)
t_sym = Symbol('t', positive=True)

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


class Var(namedtuple("Var", ["coeff", "id", "time"])):
    def __repr__(self):
        time_str = "[{}]".format(self.time)
        return "{c}*{i}{t}".format(c=self.coeff, i=self.id, t=time_str)


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
            rep = " {op} ".join(["({})"]*(len(self.args) - 1))
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
