from mtl import ast


def alw(phi, *, lo=0, hi=float('inf')):
    return ast.G(ast.Interval(lo, hi), phi)


def env(phi, *, lo=0, hi=float('inf')):
    return ~alw(~phi, lo=lo, hi=hi)


def implies(x, y):
    return ast.Implies(x, y)


def xor(x, y):
    return (x | y) & ~(x & y)


def le(x, y, t=0.):
    return (x.lt(y, t) | x.eq(y, t))


def gt(x, y, t=0.):
    return ~(x.le(y, t))


def ge(x, y, t=0.):
    return ~(x.lt(y, t))


def iff(x, y):
    return (x & y) | (~x & ~y)


def until(phi, psi):
    return ast.WeakUntil(phi, psi) & env(psi)


def timed_until(left, right, lo, hi):
    assert 0 <= lo < hi

    expr = env(right, lo=lo, hi=hi)
    expr &= alw(left, lo=0, hi=lo)
    expr &= alw(until(left, right), lo=lo, hi=lo)

    return expr
