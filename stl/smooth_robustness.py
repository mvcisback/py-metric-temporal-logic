# TODO: technically incorrect on 0 robustness since conflates < and >

from functools import singledispatch
from collections import namedtuple

import sympy as sym
from numpy import arange
from funcy import pairwise
from lenses import lens

import stl.ast
from stl.ast import t_sym
from stl.utils import walk
from stl.robustness import op_lookup

Param = namedtuple("Param", ["L", "h", "B", "id_map", "eps"])

@singledispatch
def node_base(_, _1, _2):
    return sym.e


@node_base.register(stl.ast.Or)
def node_base(_, eps, _1):
    return len(stl.args)**(1/eps)


@node_base.register(stl.ast.F)
def node_base(_, eps, L):
    lo, hi = stl.interval
    return sym.ceil((hi - lo)*L/eps)**(2/eps)


def sample_rate(eps, L):
    return eps / L


def admissible_params(phi, eps, L):
    h = sample_rate(eps, L),
    B = max(node_base(n, eps, L) for n in walk(phi)),
    return B, h

def symbolic_params(phi, eps, L):
    return Param(
        L=sym.Symbol("L"),
        h=sym.Symbol("h"),
        B="B",
        id_map={n:i for i, n in enumerate(walk(phi))},
        eps=sym.symbol("eps")
    )


def smooth_robustness(phi, *, L=None, eps=None):
    # TODO: Return symbollic formula if flag
    p = symbolic_params(phi, eps, L)
    lo, hi = beta(phi, p), alpha(phi, p)
    subs = {}
    if L is not None:
        subs[p.L] = L
    if eps is not None:
        subs[p.eps] = eps
    if L is not None and eps is not None:
        B, h = admissible_params(phi, eps, L)
        subs[p.B] = B
        subs[p.h] = h
        lo, hi = lo.subs(subs), hi.subs(subs)
    else:
        B = p.B

    return sym.log(lo, B), sym.log(hi, B)


# Alpha implementation

@singledispatch
def alpha(stl, p):
    raise NotImplementedError("Call canonicalization function")

def eval_terms(lineq):
    return sum(map(eval_term, lineq.terms))


def eval_term(term):
    return term.coeff*sym.Function(term.id.name)(t_sym)


@alpha.register(stl.LinEq)
def _(phi, p):
    op = op_lookup[phi.op]
    B = eps_to_base(eps/depth, N)
    x = op(eval_terms(phi), phi.const)
    return B**x


@alpha.register(stl.Neg)
def _(phi, p):
    return 1/beta(phi, p)


@alpha.register(stl.Or)
def _(phi, p):
    return sum(alpha(psi, p) for psi in psi in phi.args)


def F_params(phi, p, r):
    hi, lo = phi.interval
    N = sym.ceiling((hi - lo) / p.h)
    i = sym.Symbol("i_{}".format(p.id_map[phi]))
    x = lambda k: r.subs({t_sym: t_sym+k+lo})
    return N, i, x


@alpha.register(stl.F)
def _(phi, p):
    N, i, x = F_params(phi, p, alpha(phi.arg, p))
    x_ij = sym.sqrt(p.B**(L*h)*x(i)*x(i+1))
    return sym.summation(x_ij, (i, 0, N-1))

# Beta implementation

@singledispatch
def beta(phi, p):
    raise NotImplementedError("Call canonicalization function")

beta.register(stl.LinEq)(alpha)

@beta.register(stl.Neg)
def _(phi, p):
    return 1/alpha(phi, p)


@beta.register(stl.Or)
def _(phi, p):
    return alpha(phi)/len(phi.args)


@beta.register(stl.F)
def _(phi, p):
    N, i, x = F_params(phi, p, beta(phi.arg, p))
    return sym.summation(x(i), (i, 0, N))
