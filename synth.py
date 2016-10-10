from stl.utils import set_params, param_lens
from stl.robustness import pointwise_robustness

from lenses import lens

def binsearch(stleval, *, tol=1e-3, lo, hi, polarity):
    """Only run search if tightest robustness was positive."""
    # Only check low since hi taken care of by precondition.
    # TODO: allow for different polarities
    rL, rH = stleval(lo), stleval(hi)
    # Early termination via bounds checks
    posL, posH = rL > 0, rH > 0
    if polarity and posL:
        return lo
    elif not polarity and posH:
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
