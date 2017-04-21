# TODO: technically incorrect on 0 robustness since conflates < and >

from functools import singledispatch
from collections import namedtuple

import sympy as sym
from numpy import arange
from funcy import pairwise
from lenses import lens

import stl.ast
from stl.ast import t_sym
from stl.utils import walk, f_neg_or_canonical_form
from stl.robustness import op_lookup

Param = namedtuple("Param", ["L", "h", "B", "eps"])

@singledispatch
def node_base(_, _1, _2):
    return sym.E


@node_base.register(stl.ast.Or)
def _(phi, eps, _1):
    return len(phi.args)**(1/eps)


@node_base.register(stl.ast.F)
def _(phi, eps, L):
    lo, hi = phi.interval
    return sym.ceiling((hi - lo)*L/eps)**(2/eps)


def sample_rate(eps, L):
    return eps / L


def admissible_params(phi, eps, L):
    h = sample_rate(eps, L)
    B = max(node_base(n, eps, L) for n in walk(phi))
    return B, h


def symbolic_params(phi, eps, L):
    L = sym.Dummy("L")
    eps = sym.Dummy("\epsilon")
    return Param(
        L=L,
        h=sample_rate(eps, L),
        B=sym.Dummy("B")(eps, sym.Dummy("\phi")),
        eps=eps,
    )

def smooth_robustness(phi, *, L=None, eps=None):
    phi = f_neg_or_canonical_form(phi)
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
    x = op(eval_terms(phi), phi.const)
    return p.B**x


@alpha.register(stl.Neg)
def _(phi, p):
    return 1/beta(phi.arg, p)


@alpha.register(stl.Or)
def _(phi, p):
    return sum(alpha(psi, p) for psi in phi.args)


def F_params(phi, p, r):
    hi, lo = phi.interval
    N = sym.ceiling((hi - lo) / p.h)
    x = lambda k: r.subs({t_sym: t_sym+k+lo})
    i = sym.Dummy("i")
    return N, i, x


@alpha.register(stl.F)
def _(phi, p):
    N, i, x = F_params(phi, p, alpha(phi.arg, p))
    x_ij = sym.sqrt(p.B**(p.L*p.h)*x(i)*x(i+1))
    return sym.summation(x_ij, (i, 0, N-1))

# Beta implementation

@singledispatch
def beta(phi, p):
    raise NotImplementedError("Call canonicalization function")

beta.register(stl.LinEq)(alpha)

@beta.register(stl.Neg)
def _(phi, p):
    return 1/alpha(phi.arg, p)


@beta.register(stl.Or)
def _(phi, p):
    return alpha(phi, p)/len(phi.args)


@beta.register(stl.F)
def _(phi, p):
    N, i, x = F_params(phi, p, beta(phi.arg, p))
    return sym.summation(x(i), (i, 0, N))
