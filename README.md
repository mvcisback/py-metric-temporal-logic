<figure>
  <img src="assets/logo_text.svg" alt="py-metric-temporal logic logo" width=300px>
  <figcaption>
  A library for manipulating and evaluating metric temporal logic.
  </figcaption>
</figure>


[![Build Status](https://travis-ci.org/mvcisback/py-metric-temporal-logic.svg?branch=master)](https://travis-ci.org/mvcisback/py-metric-temporal-logic)
[![codecov](https://codecov.io/gh/mvcisback/py-metric-temporal-logic/branch/master/graph/badge.svg)](https://codecov.io/gh/mvcisback/py-metric-temporal-logic)

# About

Python library for working with Metric Temporal Logic (MTL). Metric
Temporal Logic is an extension of Linear Temporal Logic (LTL) for
specifying properties over time series (See [Alur][1]). Some practical examples are
given in the usage.

# Installation

`$ pip install metric-temporal-logic`

# Usage

To begin, we import `mtl`.

```python
import mtl
```

## Propositional logic (using parse api)
```python
# - Lowercase strings denote atomic predicates.
phi0 = mtl.parse('atomicpred')

# - Binary operators need to be surrounded by parens.
phi1 = mtl.parse('((a & b & c) | d | e)')
phi2 = mtl.parse('(a -> b) & (~a -> c)')
phi3 = mtl.parse('(a -> b -> c)')
phi4 = mtl.parse('(a <-> b <-> c)')
phi5 = mtl.parse('(x ^ y ^ z)')

# - Unary operators (negation)
phi6 = mtl.parse('~a')
phi7 = mtl.parse('~(a)')
```

## Propositional logic (using python syntax)
```python
a, b = mtl.parse('a'), mtl.parse('b')
phi0 = ~a
phi1 = a & b
phi2 = a | b

# TODO: add
phi3 = a ^ b
phi4 = a.iff(b)
phi5 = a.implies(b)
```

## Modal Logic (parser api)

```python
# Eventually `x` will hold.
phi1 = mtl.parse('F x')

# `x & y` will always hold.
phi2 = mtl.parse('G(x & y)')

# `x` holds until `y` holds. 
# Note that since `U` is binary, it requires parens.
phi3 = mtl.parse('(x U y)')

# Whenever `x` holds, then `y` holds in the next two time units.
phi4 = mtl.parse('G(x -> F[0, 2] y)')

# We also support timed until.
phi5 = mtl.parse('(a U[0, 2] b)')

# Finally, if time is discretized, we also support the next operator.
# Thus, LTL can also be modeled.
# `a` holds in two time steps.
phi6 = mtl.parse('XX a')
```

[1]: https://link.springer.com/chapter/10.1007/BFb0031988
