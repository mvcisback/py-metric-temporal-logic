from mtl import ast


def alw(phi, *, lo=0, hi=float('inf')):
    return ast.G(ast.Interval(lo, hi), phi)


def env(phi, *, lo=0, hi=float('inf')):
    return ~alw(~phi, lo=lo, hi=hi)


def implies(x, y):
    return ~x | y


def xor(x, y):
    return (x | y) & ~(x & y)


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
