from stl.utils import set_params, param_lens
from stl.robustness import pointwise_robustness

from lenses import lens

def binsearch(stleval, *, tol=1e-3, lo, hi, polarity):
    """Only run search if tightest robustness was positive."""
    # Early termination via bounds checks
    if polarity and stleval(lo) > 0:
        return lo
    elif not polarity and stleval(hi) > 0:
        return hi

    while hi - lo > tol:
        mid = lo + (hi - lo) / 2
        r = stleval(mid)
        if not polarity: # swap direction
            r *= -1
        if r < 0:
            lo, hi = mid, hi
        else:
            lo, hi = lo, mid
    
    # Want satisifiable formula
    return hi if polarity else lo


def lex_param_project(stl, x, *, order, polarity, ranges, tol=1e-3):
    val = {var: (ranges[var][0] if not polarity[var] else ranges[var][1]) for var in order}
    p_lens = param_lens(stl)
    def stleval_fact(var, val):
        l = lens(val)[var]
        return lambda p: pointwise_robustness(set_params(stl, l.set(p)))(x, 0)
    
    for var in order:
        stleval = stleval_fact(var, val)
        lo, hi = ranges[var]
        param = binsearch(stleval, lo=lo, hi=hi, tol=tol, polarity=polarity[var])
        val[var] = param

    return val
