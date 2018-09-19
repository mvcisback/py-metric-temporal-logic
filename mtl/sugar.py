def implies(x, y):
    return ~x | y


def xor(x, y):
    return (x | y) & ~(x & y)


def iff(x, y):
    return (x & y) | (~x & ~y)


def _or(exp1, exp2):
    return ~(~exp1 & ~exp2)


def _once(exp, itvl=None):
    return ~((~exp).hist(itvl))
