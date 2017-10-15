# -*- coding: utf-8 -*-
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
    elif len(args) == 1:
        return args[0]
    else:
        return op(tuple(fn.mapcat(f, phi.args)))
        

class AST(object):
    __slots__ = ()

    def __or__(self, other):
        return flatten_binary(Or((self, other)), Or, BOT, TOP)

    def __and__(self, other):
        return flatten_binary(And((self, other)), And, TOP, BOT)

    def __invert__(self):
        return Neg(self)

    @property
    def children(self):
        return set()


class _Top(AST):
    __slots__ = ()
    
    def __repr__(self):
        return "⊤"

    def __invert__(self):
        return BOT


class _Bot(AST):
    __slots__ = ()

    def __repr__(self):
        return "⊥"

    def __invert__(self):
        return TOP

TOP = _Top()
BOT = _Bot()


class AtomicPred(namedtuple("AP", ["id"]), AST):
    __slots__ = ()

    def __repr__(self):
        return f"{self.id}"
    
    @property
    def children(self):
        return set()


class LinEq(namedtuple("LinEquality", ["terms", "op", "const"]), AST):
    __slots__ = ()

    def __repr__(self):
        return " + ".join(map(str, self.terms)) + f" {self.op} {self.const}"
    
    @property
    def children(self):
        return set()

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Var(namedtuple("Var", ["coeff", "id"])):
    __slots__ = ()

    def __repr__(self):
        return f"{self.coeff}*{self.id}"


class Interval(namedtuple('I', ['lower', 'upper'])):
    __slots__ = ()

    def __repr__(self):
        return f"[{self.lower},{self.upper}]"
    
    @property
    def children(self):
        return {self.lower, self.upper}


class NaryOpSTL(namedtuple('NaryOp', ['args']), AST):
    __slots__ = ()

    OP = "?"
    def __repr__(self):
        return f" {self.OP} ".join(f"({x})" for x in self.args)
    
    @property
    def children(self):
        return set(self.args)


class Or(NaryOpSTL):
    __slots__ = ()

    OP = "∨"
    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))

class And(NaryOpSTL):
    __slots__ = ()

    OP = "∧"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class ModalOp(namedtuple('ModalOp', ['interval', 'arg']), AST):
    __slots__ = ()

    def __repr__(self):
        return f"{self.OP}{self.interval}({self.arg})"
    
    @property
    def children(self):
        return {self.arg}


class F(ModalOp):
    __slots__ = ()
    OP = "◇"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))

class G(ModalOp):
    __slots__ = ()
    OP = "□"

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Until(namedtuple('ModalOp', ['arg1', 'arg2']), AST):
    __slots__ = ()

    def __repr__(self):
        return f"({self.arg1}) U ({self.arg2})"
    
    @property
    def children(self):
        return {self.arg1, self.arg2}

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Neg(namedtuple('Neg', ['arg']), AST):
    __slots__ = ()

    def __repr__(self):
        return f"¬({self.arg})"
    
    @property
    def children(self):
        return {self.arg}

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))


class Next(namedtuple('Next', ['arg']), AST):
    __slots__ = ()

    def __repr__(self):
        return f"X({self.arg})"
    
    @property
    def children(self):
        return {self.arg}

    def __hash__(self):
        # TODO: compute hash based on contents
        return hash(repr(self))
