# -*- coding: utf-8 -*-
# TODO: create iso lens between sugar and non-sugar
# TODO: supress + given a + (-b). i.e. want a - b

from collections import namedtuple, deque
from itertools import repeat
from enum import Enum

import funcy as fn
from sympy import Symbol

dt_sym = Symbol('dt', positive=True)
t_sym = Symbol('t', positive=True)

def flatten_binary(phi, op, dropT, shortT):
    f = lambda x: x.args if isinstance(x, op) else [x]
    args = [arg for arg in phi.args if arg is not dropT]
    if any(arg is shortT for arg in args):
        return shortT
    elif not args:
        return dropT
    else:
        return op(tuple(fn.mapcat(f, phi.args)))
        

class AST(object):
    def __or__(self, other):
        return flatten_binary(Or((self, other)), Or, BOT, TOP)

    def __and__(self, other):
        return flatten_binary(And((self, other)), And, TOP, BOT)

    def __invert__(self):
        return Neg(self)


class _Top(AST):
    def __repr__(self):
        return "⊤"

    def __invert__(self):
        return Bot()


class _Bot(AST):
    def __repr__(self):
        return "⊥"

    def __invert__(self):
        return Top()

TOP = _Top()
BOT = _Bot()


class AtomicPred(namedtuple("AP", ["id", "time"]), AST):
    def __repr__(self):
        return f"{self.id}[{self.time}]"

    def children(self):
        return []


class LinEq(namedtuple("LinEquality", ["terms", "op", "const"]), AST):
    def __repr__(self):
        return " + ".join(map(str, self.terms)) + f" {self.op} {self.const}"

    def children(self):
        return []

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Var(namedtuple("Var", ["coeff", "id", "time"])):
    def __repr__(self):
        return f"{self.coeff}*{self.id}[{self.time}]"


class Interval(namedtuple('I', ['lower', 'upper'])):
    def __repr__(self):
        return f"[{self.lower},{self.upper}]"

    def children(self):
        return [self.lower, self.upper]


class NaryOpSTL(namedtuple('NaryOp', ['args']), AST):
    OP = "?"
    def __repr__(self):
        return f" {self.OP} ".join(f"({x})" for x in self.args)

    def children(self):
        return self.args


class Or(NaryOpSTL):
    OP = "∨"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))

class And(NaryOpSTL):
    OP = "∧"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class ModalOp(namedtuple('ModalOp', ['interval', 'arg']), AST):
    def __repr__(self):
        return f"{self.OP}{self.interval}({self.arg})"
    
    def children(self):
        return [self.arg]


class F(ModalOp):
    OP = "◇"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))

class G(ModalOp):
    OP = "□"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Until(namedtuple('ModalOp', ['interval', 'arg1', 'arg2']), AST):
    def __repr__(self):
        return f"({self.arg1} U{self.interval} ({self.arg2}))"
    
    def children(self):
        return [self.arg1, self.arg2]

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Neg(namedtuple('Neg', ['arg']), AST):
    def __repr__(self):
        return f"¬({self.arg})"

    def children(self):
        return [self.arg]

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))
