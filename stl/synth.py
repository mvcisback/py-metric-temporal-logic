import operator as op

from stl.utils import set_params, param_lens
from stl.boolean_eval import pointwise_sat

from lenses import lens
import numpy as np
from copy as deepcopy

var_val_update = lambda val_vec, ind, rep_elem : np.put(val_vec, ind, rep_elem)
# Returns True when lo_i <= hi_i
compute_var_polarity = lambda stleval, lo, hi, ind: stleval(lo) <= stleval(
    var_val_update(lo, ind, hi[ind]))
# Vector of True and False
compute_polarity = lambda stleval, lo, hi: np.array([compute_var_polarity(
                                                                stleval,
                                                                deepcopy(lo),
                                                                hi, i)
                                            for i in range(len(hi))])

# Project from unit cube
project_ub = lambda lo, hi, elem: (np.array(hi) - np.array(lo))*np.array(
    elem) + np.array(lo)

# Update the lo, hi based on polarity
def update_lo_hi(stleval, lo, hi):
    var_polarities = compute_polarity(stleval, lo, hi)
    updated_lo = lo*(var_polarities) + hi*(~var_polarities)*-1
    updated_hi = lo*(~var_polarities)*-1 + hi*(var_polarities)

    return updated_lo, updated_hi, var_polarities

# Monotone threshold function
def thres_func(stleval, lo, hi):
    updated_hi, updated_lo, var_pol = thres_func(stleval, lo, hi)
    # elem is the sample point
    def g(stleval, elem):
        updated_elem = elem*(var_pol) + elem(~var_pol)*-1
        proj_elem = project_ub(updated_lo, updated_hi, updated_elem)
        return stleval(proj_elem)
    return g

def binsearch(stleval, *, tol=1e-3, lo, hi, polarity):
    """Only run search if tightest robustness was positive."""
    # Early termination via bounds checks
    if polarity and stleval(lo):
        return lo
    elif not polarity and stleval(hi):
        return hi

    while hi - lo > tol:
        mid = lo + (hi - lo) / 2
        r = stleval(mid)
        lo, hi = (mid, hi) if r ^ polarity else (lo, mid)

    # Want satisifiable formula
    return hi if polarity else lo


def lex_param_project(stl, x, *, order, polarity, ranges, tol=1e-3):
    val = {var: (ranges[var][0] if not polarity[var] else ranges[var][1]) for var in order}
    p_lens = param_lens(stl)
    def stleval_fact(var, val):
        l = lens(val)[var]
        return lambda p: pointwise_sat(set_params(stl, l.set(p)))(x, 0)
    
    for var in order:
        stleval = stleval_fact(var, val)
        lo, hi = ranges[var]
        param = binsearch(stleval, lo=lo, hi=hi, tol=tol, polarity=polarity[var])
        val[var] = param

    return val








