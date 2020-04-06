<figure>
  <img src="assets/logo.png" alt="py-metric-temporal logic logo" width=300px>
  <figcaption>
  A library for manipulating and evaluating metric temporal logic.
  </figcaption>
</figure>



[![Build Status](https://cloud.drone.io/api/badges/mvcisback/py-metric-temporal-logic/status.svg)](https://cloud.drone.io/mvcisback/py-metric-temporal-logic)
[![codecov](https://codecov.io/gh/mvcisback/py-metric-temporal-logic/branch/master/graph/badge.svg)](https://codecov.io/gh/mvcisback/py-metric-temporal-logic)
[![PyPI version](https://badge.fury.io/py/metric-temporal-logic.svg)](https://badge.fury.io/py/metric-temporal-logic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/72686883.svg)](https://zenodo.org/badge/latestdoi/72686883)

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [About](#about)
- [Installation](#installation)
- [Usage](#usage)
    - [Python Operator API](#python-operator-api)
        - [Propositional logic (using python syntax)](#propositional-logic-using-python-syntax)
        - [Modal Logic (using python syntax)](#modal-logic-using-python-syntax)
    - [String based API](#string-based-api)
        - [Propositional logic (parse api)](#propositional-logic-parse-api)
        - [Modal Logic (parser api)](#modal-logic-parser-api)
    - [Boolean Evaluation](#boolean-evaluation)
    - [Quantitative Evaluate (Signal Temporal Logic)](#quantitative-evaluate-signal-temporal-logic)
    - [Utilities](#utilities)
- [Similar Projects](#similar-projects)
- [Citing](#citing)

<!-- markdown-toc end -->

# About

Python library for working with Metric Temporal Logic (MTL). Metric
Temporal Logic is an extension of Linear Temporal Logic (LTL) for
specifying properties over time series (See [Alur][1]). Some practical examples are
given in the usage.

# Installation

If you just need to use `metric-temporal-logic`, you can just run:

`$ pip install metric-temporal-logic`

For developers, note that this project uses the
[poetry](https://poetry.eustace.io/) python package/dependency
management tool. Please familarize yourself with it and then
run:

`$ poetry install`


# Usage

To begin, we import `mtl`.

```python
import mtl
```

There are **two** APIs for interacting with the `mtl` module. Namely, one can specify the MTL expression using:
1. [Python Operators](#python-operator-api).
2. [Strings + The parse API](#string-based-api).

We begin with the Python Operator API:

## Python Operator API

### Propositional logic (using python syntax)
```python
a, b = mtl.parse('a'), mtl.parse('b')
phi0 = ~a
phi1 = a & b
phi2 = a | b
phi3 = a ^ b
phi4 = a.iff(b)
phi5 = a.implies(b)
```


### Modal Logic (using python syntax)

```python
a, b = mtl.parse('a'), mtl.parse('b')

# Eventually `a` will hold.
phi1 = a.eventually()

# `a & b` will always hold.
phi2 = (a & b).always()

# `a` until `b`
phi3 = a.until()

# `a` weak until `b`
phi4 = a.weak_until(b)

# Whenever `a` holds, then `b` holds in the next two time units.
phi5 = (a.implies(b.eventually(lo=0, hi=2))).always()

# We also support timed until.
phi6 = a.timed_until(b, lo=0, hi=2)

# `a` holds in two time steps.
phi7 = a >> 2
```

## String based API

### Propositional logic (parse api)
```python
# - Lowercase strings denote atomic predicates.
phi0 = mtl.parse('atomicpred')

# - infix operators need to be surrounded by parens.
phi1 = mtl.parse('((a & b & c) | d | e)')
phi2 = mtl.parse('(a -> b) & (~a -> c)')
phi3 = mtl.parse('(a -> b -> c)')
phi4 = mtl.parse('(a <-> b <-> c)')
phi5 = mtl.parse('(x ^ y ^ z)')

# - Unary operators (negation)
phi6 = mtl.parse('~a')
phi7 = mtl.parse('~(a)')
```

### Modal Logic (parser api)

```python
# Eventually `x` will hold.
phi1 = mtl.parse('F x')

# `x & y` will always hold.
phi2 = mtl.parse('G(x & y)')

# `x` holds until `y` holds. 
# Note that since `U` is binary, it requires parens.
phi3 = mtl.parse('(x U y)')

# Weak until (`y` never has to hold).
phi4 = mtl.parse('(x W y)')

# Whenever `x` holds, then `y` holds in the next two time units.
phi5 = mtl.parse('G(x -> F[0, 2] y)')

# We also support timed until.
phi6 = mtl.parse('(a U[0, 2] b)')

# Finally, if time is discretized, we also support the next operator.
# Thus, LTL can also be modeled.
# `a` holds in two time steps.
phi7 = mtl.parse('XX a')
```

## Quantitative Evaluate (Signal Temporal Logic)

Given a property `phi`, one can evaluate is a timeseries satisifies
`phi`. Time Series can either be defined using a dictionary mapping
atomic predicate names to lists of (`time`, `val`) pairs **or** using
the [DiscreteSignals](https://github.com/mvcisback/DiscreteSignals)
API (used internally).

There are two types of evaluation. One uses the boolean semantics of
MTL and the other uses Signal Temporal Logic like semantics.


```python
# Assumes piece wise constant interpolation.
data = {
    'a': [(0, 100), (1, -1), (3, -2)],
    'b': [(0, 20), (0.2, 2), (4, -10)]
}

phi = mtl.parse('F(a | b)')
print(phi(data))
# output: 100

# Evaluate at t=3
print(phi(data, time=3))
# output: 2

# Evaluate with discrete time
phi = mtl.parse('X b')
print(phi(data, dt=0.2))
# output: 2
```

## Boolean Evaluation

To Boolean semantics can be thought of as a special case of the
quantitative semantics where `True ↦ 1` and `False ↦ -1`.  This
conversion happens automatically using using the `quantitative=False`
flag.


```python
# Assumes piece wise constant interpolation.
data = {
    'a': [(0, True), (1, False), (3, False)],
    'b': [(0, False), (0.2, True), (4, False)]
}

phi = mtl.parse('F(a | b)')
print(phi(data, quantitative=False))
# output: True

phi = mtl.parse('F(a | b)')
print(phi(data))
# output: True

# Note, quantitative parameter defaults to False

# Evaluate at t=3. 
print(phi(data, time=3, quantitative=False))
# output: False

# Compute sliding satisifaction.
print(phi(data, time=None, quantitative=False))
# output: [(0, True), (0.2, True), (4, False)]

# Evaluate with discrete time
phi = mtl.parse('X b')
print(phi(data, dt=0.2, quantitative=False))
# output: True
```

## Utilities
```python
import mtl
from mtl import utils

print(utils.scope(mtl.parse('XX a'), dt=0.1))
# output: 0.2

print(utils.discretize(mtl.parse('F[0, 0.2] a'), dt=0.1))
# output: (a | X a | XX a)
```

# Similar Projects
Feel free to open up a pull-request to add other similar projects. This library was written to meet some of my unique needs, for example I wanted the AST to be immutable and wanted the library to **just** handle manipulating MTL. Many other similar projects exist with different goals.

1. https://github.com/doganulus/python-monitors
1. https://github.com/STLInspector/STLInspector

# Citing

    @misc{pyMTL,
      author       = {Marcell Vazquez-Chanlatte},
      title        = {mvcisback/py-metric-temporal-logic: v0.1.1},
      month        = jan,
      year         = 2019,
      doi          = {10.5281/zenodo.2548862},
      url          = {https://doi.org/10.5281/zenodo.2548862}
    }

[1]: https://link.springer.com/chapter/10.1007/BFb0031988
