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


def timed_until(phi, psi, lo, hi):
    return env(psi, lo=lo, hi=hi) & alw(until(phi, psi), lo=0, hi=lo)
